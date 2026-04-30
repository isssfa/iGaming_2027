"""
Django management command to consume email tasks from RabbitMQ queue.
Run this command as a background process to process email notifications.

Usage:
    python manage.py consume_emails

For production, run this as a systemd service or supervisor process.
"""
import json
import logging
import signal
import sys
import time
from django.core.management.base import BaseCommand
from django.conf import settings
import pika
from coreconfig.service import email_service
from coreconfig.models import EmailQueue

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Consume email tasks from RabbitMQ queue and send emails'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.should_stop = False
        self.connection = None
        self.channel = None

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-retries',
            type=int,
            default=3,
            help='Maximum number of retries for failed emails (default: 3)',
        )
        parser.add_argument(
            '--prefetch-count',
            type=int,
            default=1,
            help='Number of unacknowledged messages to prefetch (default: 1)',
        )

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.stdout.write(self.style.WARNING('\nShutting down gracefully...'))
        self.should_stop = True
        if self.connection and not self.connection.is_closed:
            self.connection.close()

    def setup_connection(self):
        """Setup RabbitMQ connection and channel"""
        try:
            connection_params = pika.ConnectionParameters(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                virtual_host=settings.RABBITMQ_VHOST,
                credentials=pika.PlainCredentials(
                    settings.RABBITMQ_USER,
                    settings.RABBITMQ_PASSWORD
                ),
                heartbeat=600,
                blocked_connection_timeout=300,
            )
            
            self.connection = pika.BlockingConnection(connection_params)
            self.channel = self.connection.channel()
            
            # Declare queue as durable
            self.channel.queue_declare(queue='email_notifications', durable=True)
            
            # Set prefetch count to process one message at a time
            self.channel.basic_qos(prefetch_count=self.options['prefetch_count'])
            
            self.stdout.write(self.style.SUCCESS('Connected to RabbitMQ'))
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to connect to RabbitMQ: {e}'))
            logger.error(f'RabbitMQ connection error: {e}')
            return False

    def callback(self, ch, method, properties, body):
        """
        Callback function to process each message from the queue
        """
        try:
            # Parse message
            email_data = json.loads(body.decode('utf-8'))
            queue_id = email_data.get('queue_id')
            
            self.stdout.write(f'Processing email task: {email_data.get("email_type", "unknown")} (Queue ID: {queue_id})')
            
            # Process email
            success = email_service.process_email_task(email_data)
            
            if success:
                # Acknowledge message
                ch.basic_ack(delivery_tag=method.delivery_tag)
                
                # Update processed_at timestamp
                if queue_id:
                    try:
                        email_queue = EmailQueue.objects.get(id=queue_id)
                        from django.utils import timezone
                        email_queue.processed_at = timezone.now()
                        email_queue.save()
                    except EmailQueue.DoesNotExist:
                        pass
                
                self.stdout.write(self.style.SUCCESS(f'Email sent successfully (Queue ID: {queue_id})'))
            else:
                # Check retry count
                if queue_id:
                    try:
                        email_queue = EmailQueue.objects.get(id=queue_id)
                        max_retries = self.options['max_retries']
                        
                        if email_queue.retry_count < max_retries:
                            # Reject and requeue for retry
                            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Email failed, requeuing for retry ({email_queue.retry_count + 1}/{max_retries})'
                                )
                            )
                        else:
                            # Max retries reached, acknowledge to remove from queue
                            ch.basic_ack(delivery_tag=method.delivery_tag)
                            self.stdout.write(
                                self.style.ERROR(
                                    f'Email failed after {max_retries} retries, removing from queue'
                                )
                            )
                    except EmailQueue.DoesNotExist:
                        # If queue record doesn't exist, acknowledge to remove from queue
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                else:
                    # No queue_id, acknowledge to remove from queue
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'Invalid JSON in message: {e}'))
            logger.error(f'JSON decode error: {e}')
            # Acknowledge to remove invalid message
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error processing message: {e}'))
            logger.error(f'Error processing email task: {e}', exc_info=True)
            # Reject and requeue on unexpected errors
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def handle(self, *args, **options):
        self.options = options
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.stdout.write(self.style.SUCCESS('Starting email consumer...'))
        
        # Setup connection
        if not self.setup_connection():
            return
        
        try:
            # Set up consumer
            self.channel.basic_consume(
                queue='email_notifications',
                on_message_callback=self.callback,
            )
            
            self.stdout.write(self.style.SUCCESS('Waiting for messages. To exit press CTRL+C'))
            
            # Start consuming
            while not self.should_stop:
                try:
                    self.connection.process_data_events(time_limit=1)
                except KeyboardInterrupt:
                    self.should_stop = True
                    break
                except Exception as e:
                    if not self.should_stop:
                        logger.error(f'Error in process_data_events: {e}')
                        time.sleep(5)  # Wait before retrying
                        # Try to reconnect
                        if not self.setup_connection():
                            self.should_stop = True
                            break
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Consumer error: {e}'))
            logger.error(f'Consumer error: {e}', exc_info=True)
        finally:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            self.stdout.write(self.style.SUCCESS('Email consumer stopped'))

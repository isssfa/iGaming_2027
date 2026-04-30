"""
RabbitMQ Email Service
Common service for sending emails via RabbitMQ queue across all apps.
"""
import json
import logging
from datetime import datetime, date
from decimal import Decimal
import pika
from django.conf import settings
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
from .models import EmailQueue

logger = logging.getLogger(__name__)


class DateTimeJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime, date, and Decimal objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            # Handle both timezone-aware and naive datetime objects
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class RabbitMQEmailService:
    """Service for sending emails via RabbitMQ queue"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue_name = 'email_notifications'
        
    def _get_connection_params(self):
        """Get RabbitMQ connection parameters from settings"""
        return pika.ConnectionParameters(
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
    
    def _ensure_connection(self):
        """Ensure RabbitMQ connection is established"""
        if self.connection is None or self.connection.is_closed:
            try:
                self.connection = pika.BlockingConnection(self._get_connection_params())
                self.channel = self.connection.channel()
                # Declare queue to ensure it exists
                self.channel.queue_declare(queue=self.queue_name, durable=True)
                logger.info("RabbitMQ connection established")
            except Exception as e:
                logger.error(f"Failed to connect to RabbitMQ: {e}")
                raise
    
    def _close_connection(self):
        """Close RabbitMQ connection"""
        try:
            if self.channel and not self.channel.is_closed:
                self.channel.close()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")
    
    def send_email_task(self, email_type, subject, recipients, context=None, 
                        template_path=None, html_body=None, plain_body=None, 
                        attachments=None, source_app=None, related_model_id=None):
        """
        Add email task to RabbitMQ queue
        
        Args:
            email_type: Type of email (e.g., 'inquiry', 'nomination', 'speaker', 'registration')
            subject: Email subject
            recipients: List of recipient email addresses
            context: Template context dictionary (if using template)
            template_path: Path to email template (optional)
            html_body: HTML email body (optional, if not using template)
            plain_body: Plain text email body (optional)
            attachments: List of file paths to attach (optional)
            source_app: Source application name for logging
            related_model_id: ID of related model (e.g., Nomination.id, Inquiry.id)
        
        Returns:
            EmailQueue instance if saved to DB, None otherwise
        """
        try:
            self._ensure_connection()
            
            # Prepare email data
            email_data = {
                'email_type': email_type,
                'subject': subject,
                'recipients': recipients if isinstance(recipients, list) else [recipients],
                'from_email': settings.DEFAULT_FROM_EMAIL,
                'context': context or {},
                'template_path': template_path,
                'html_body': html_body,
                'plain_body': plain_body,
                'attachments': attachments or [],
                'source_app': source_app,
                'related_model_id': related_model_id,
            }

            requeue_snapshot = {
                'template_path': template_path,
                'context': json.loads(json.dumps(context or {}, cls=DateTimeJSONEncoder)),
                'html_body': html_body,
                'plain_body': plain_body,
                'attachments': list(attachments or []),
            }
            
            # Create EmailQueue record
            email_queue = EmailQueue.objects.create(
                email_type=email_type,
                subject=subject,
                recipients=','.join(recipients) if isinstance(recipients, list) else recipients,
                status='pending',
                source_app=source_app or 'unknown',
                related_model_id=related_model_id,
                requeue_snapshot=requeue_snapshot,
            )
            
            # Add queue_id to email_data
            email_data['queue_id'] = email_queue.id
            
            # Publish to RabbitMQ (use custom encoder for datetime objects)
            message = json.dumps(email_data, cls=DateTimeJSONEncoder)
            self.channel.basic_publish(
                exchange='',
                routing_key=self.queue_name,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                )
            )
            
            logger.info(f"Email task queued: {email_type} (Queue ID: {email_queue.id})")
            return email_queue
            
        except Exception as e:
            logger.error(f"Failed to queue email task: {e}")
            # Update EmailQueue status to failed
            if 'email_queue' in locals():
                email_queue.status = 'failed'
                email_queue.error_message = str(e)
                email_queue.save()
            return None
        finally:
            self._close_connection()
    
    def process_email_task(self, email_data):
        """
        Process a single email task from the queue
        
        Args:
            email_data: Dictionary containing email information
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        queue_id = email_data.get('queue_id')
        email_type = email_data.get('email_type', 'unknown')
        
        try:
            # Update status to processing
            if queue_id:
                try:
                    email_queue = EmailQueue.objects.get(id=queue_id)
                    email_queue.status = 'processing'
                    email_queue.save()
                except EmailQueue.DoesNotExist:
                    logger.warning(f"EmailQueue record {queue_id} not found")
            
            # Prepare email
            recipients = email_data.get('recipients', [])
            if not recipients:
                raise ValueError("No recipients specified")
            
            subject = email_data.get('subject', 'Notification')
            template_path = email_data.get('template_path')
            html_body = email_data.get('html_body')
            plain_body = email_data.get('plain_body')
            context = email_data.get('context', {})
            attachments = email_data.get('attachments', [])
            
            # Render template if provided
            if template_path:
                html_body = render_to_string(template_path, context)
            
            # Create email message
            if html_body:
                email = EmailMessage(
                    subject=subject,
                    body=html_body,
                    from_email=email_data.get('from_email', settings.DEFAULT_FROM_EMAIL),
                    to=recipients,
                )
                email.content_subtype = 'html'
            else:
                # Use plain text email
                email = EmailMessage(
                    subject=subject,
                    body=plain_body or '',
                    from_email=email_data.get('from_email', settings.DEFAULT_FROM_EMAIL),
                    to=recipients,
                )
            
            # Attach files if any
            for attachment_path in attachments:
                try:
                    email.attach_file(attachment_path)
                except Exception as e:
                    logger.warning(f"Failed to attach file {attachment_path}: {e}")
            
            # Send email
            email.send()
            
            # Update status to completed
            if queue_id:
                try:
                    email_queue = EmailQueue.objects.get(id=queue_id)
                    email_queue.status = 'completed'
                    email_queue.save()
                except EmailQueue.DoesNotExist:
                    pass
            
            logger.info(f"Email sent successfully: {email_type} (Queue ID: {queue_id})")
            return True
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to send email {email_type} (Queue ID: {queue_id}): {error_msg}")
            
            # Update status to failed
            if queue_id:
                try:
                    email_queue = EmailQueue.objects.get(id=queue_id)
                    email_queue.status = 'failed'
                    email_queue.error_message = error_msg
                    email_queue.retry_count = (email_queue.retry_count or 0) + 1
                    email_queue.save()
                except EmailQueue.DoesNotExist:
                    pass
            
            return False
    
    def _rebuild_email_data_from_awards_vote(self, email_queue, queue_id):
        """Rebuild full RabbitMQ payload for awards vote confirmation when snapshot is missing (legacy rows)."""
        try:
            from awards.models import Vote
            from awards.utils import build_confirmation_url, vote_rows_for_queue_context
        except ImportError:
            return None

        try:
            vote = Vote.objects.select_related('category', 'nominee').get(pk=email_queue.related_model_id)
        except Vote.DoesNotExist:
            return None

        if vote.is_confirmed:
            return None

        pending = list(
            Vote.objects.filter(
                voter_email=vote.voter_email,
                confirmation_token=vote.confirmation_token,
                is_confirmed=False,
            ).select_related('category', 'nominee')
        )
        if not pending:
            return None

        confirm_url = build_confirmation_url(
            token=vote.confirmation_token,
            email=vote.voter_email,
            request=None,
        )
        vote_rows = vote_rows_for_queue_context(pending)
        return {
            'email_type': 'awards_vote',
            'subject': email_queue.subject,
            'recipients': email_queue.get_recipients_list(),
            'from_email': settings.DEFAULT_FROM_EMAIL,
            'queue_id': queue_id,
            'source_app': email_queue.source_app,
            'related_model_id': email_queue.related_model_id,
            'template_path': 'awards/email/vote_confirmation.html',
            'context': {
                'voter_name': vote.voter_name,
                'vote_rows': vote_rows,
                'confirm_url': confirm_url,
            },
            'attachments': [],
        }

    def requeue_failed_email(self, queue_id):
        """
        Requeue a failed email task
        
        Args:
            queue_id: ID of the EmailQueue record to requeue
        
        Returns:
            bool: True if requeued successfully, False otherwise
        """
        try:
            email_queue = EmailQueue.objects.get(id=queue_id)

            snap = email_queue.requeue_snapshot or {}
            if isinstance(snap, dict) and (snap.get('template_path') or snap.get('html_body') or snap.get('plain_body')):
                email_data = {
                    'email_type': email_queue.email_type,
                    'subject': email_queue.subject,
                    'recipients': email_queue.get_recipients_list(),
                    'from_email': settings.DEFAULT_FROM_EMAIL,
                    'queue_id': queue_id,
                    'source_app': email_queue.source_app,
                    'related_model_id': email_queue.related_model_id,
                }
                if snap.get('template_path'):
                    email_data['template_path'] = snap['template_path']
                    email_data['context'] = snap.get('context') or {}
                if snap.get('html_body'):
                    email_data['html_body'] = snap['html_body']
                if snap.get('plain_body'):
                    email_data['plain_body'] = snap['plain_body']
                email_data['attachments'] = snap.get('attachments') or []
            elif email_queue.email_type == 'awards_vote' and email_queue.related_model_id:
                email_data = self._rebuild_email_data_from_awards_vote(email_queue, queue_id)
                if not email_data:
                    email_data = {
                        'email_type': email_queue.email_type,
                        'subject': email_queue.subject,
                        'recipients': email_queue.get_recipients_list(),
                        'from_email': settings.DEFAULT_FROM_EMAIL,
                        'queue_id': queue_id,
                        'source_app': email_queue.source_app,
                        'related_model_id': email_queue.related_model_id,
                        'plain_body': (
                            f"Email subject: {email_queue.subject}\n\n"
                            f"This email was requeued after failure but the original content "
                            f"could not be restored. Use Resend from Awards votes admin instead."
                        ),
                    }
            else:
                email_data = {
                    'email_type': email_queue.email_type,
                    'subject': email_queue.subject,
                    'recipients': email_queue.get_recipients_list(),
                    'from_email': settings.DEFAULT_FROM_EMAIL,
                    'queue_id': queue_id,
                    'source_app': email_queue.source_app,
                    'related_model_id': email_queue.related_model_id,
                    'plain_body': (
                        f"Email subject: {email_queue.subject}\n\n"
                        f"This email was requeued after failure. Original template context was not stored; "
                        f"requeue again after upgrading or resend from the source feature."
                    ),
                }
            
            self._ensure_connection()
            
            message = json.dumps(email_data, cls=DateTimeJSONEncoder)
            self.channel.basic_publish(
                exchange='',
                routing_key=self.queue_name,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                )
            )
            
            # Reset status
            email_queue.status = 'pending'
            email_queue.error_message = None
            email_queue.save()
            
            logger.info(f"Failed email requeued: Queue ID {queue_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to requeue email {queue_id}: {e}")
            return False
        finally:
            self._close_connection()


# Singleton instance
email_service = RabbitMQEmailService()

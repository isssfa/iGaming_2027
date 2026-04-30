# RabbitMQ Email Notification Setup

This document explains how to set up and use RabbitMQ for asynchronous email notifications in the iGaming Forms application.

## Overview

RabbitMQ is used to queue email notifications, preventing delays in API responses when users submit forms. Emails are processed asynchronously by a background worker.

## Why RabbitMQ Instead of Threads?

**Using threads for email service is NOT recommended** because:
- Threads share the same process - if the Django process crashes, all threads die
- No persistence - if the server restarts, queued emails are lost
- Limited error handling and retry mechanisms
- Difficult to scale and monitor

**RabbitMQ provides:**
- Message persistence - emails survive server restarts
- Automatic retry mechanisms
- Better error handling and monitoring
- Easy scaling with multiple workers
- Separation of concerns - email processing is independent of web requests

## Installation

### Windows Development

1. **Install RabbitMQ using Docker (Recommended)**:
   ```bash
   docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
   ```
   - Management UI: http://localhost:15672
   - Default credentials: guest/guest

2. **Or install RabbitMQ directly**:
   - Download from: https://www.rabbitmq.com/download.html
   - Install and start the service

### Linux Deployment

1. **Install RabbitMQ**:
   ```bash
   sudo apt-get update
   sudo apt-get install rabbitmq-server
   sudo systemctl start rabbitmq-server
   sudo systemctl enable rabbitmq-server
   ```

2. **Create a user** (recommended for production):
   ```bash
   sudo rabbitmqctl add_user your_username your_password
   sudo rabbitmqctl set_user_tags your_username administrator
   sudo rabbitmqctl set_permissions -p / your_username ".*" ".*" ".*"
   ```

## Configuration

### Environment Variables

Add these to your `.env` file:

```env
# RabbitMQ Configuration
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_VHOST=/
```

For production, use your actual RabbitMQ server credentials.

## Running the Email Consumer

### Development

Run the consumer in a separate terminal:

```bash
python manage.py consume_emails
```

### Production (Linux)

#### Option 1: Systemd Service

Create `/etc/systemd/system/email-consumer.service`:

```ini
`[Unit]
Description=Django Email Consumer
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/your/project
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python manage.py consume_emails
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target`
```

Enable and start:
```bash
sudo systemctl enable email-consumer
sudo systemctl start email-consumer
sudo systemctl status email-consumer
```

#### Option 2: Supervisor

Create `/etc/supervisor/conf.d/email-consumer.conf`:

```ini
[program:email-consumer]
command=/path/to/venv/bin/python manage.py consume_emails
directory=/path/to/your/project
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/email-consumer.log
```

Then:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start email-consumer
```

## Database Migration

After setting up, run migrations to create the EmailQueue model:

```bash
python manage.py makemigrations coreconfig
python manage.py migrate
```

## Monitoring

### Django Admin

1. Go to Django Admin: `/admin/coreconfig/emailqueue/`
2. View all email queue items:
   - **Pending**: Waiting to be processed
   - **Processing**: Currently being sent
   - **Completed**: Successfully sent
   - **Failed**: Failed after retries

### RabbitMQ Management UI

1. Access: http://localhost:15672 (or your server's IP)
2. Login with your credentials
3. Check the `email_notifications` queue
4. Monitor message rates and consumer status

### Requeue Failed Emails

In Django Admin:
1. Select failed emails
2. Use the "Requeue selected failed emails" action
3. Or click the "Requeue" button on individual failed emails

## Usage in Code

The email service is already integrated into:
- `base/views.py` - Inquiry and Event Registration
- `nomination/views.py` - Award Nominations
- `speakers/views.py` - Speaker Submissions

### Adding to New Views

```python
from coreconfig.service import email_service

# Queue an email
email_queue = email_service.send_email_task(
    email_type='your_type',
    subject='Your Subject',
    recipients=['recipient@example.com'],
    context={'key': 'value'},  # For templates
    template_path='app/template.html',  # Optional
    html_body='<html>...</html>',  # Optional, if not using template
    plain_body='Plain text',  # Optional
    attachments=['/path/to/file.pdf'],  # Optional
    source_app='your_app_name',
    related_model_id=model_instance.id,  # Optional
)
```

## Troubleshooting

### Connection Errors

1. **Check RabbitMQ is running**:
   ```bash
   # Linux
   sudo systemctl status rabbitmq-server
   
   # Docker
   docker ps | grep rabbitmq
   ```

2. **Check credentials** in `.env` file

3. **Check firewall** - port 5672 should be open

### Emails Not Sending

1. Check EmailQueue in Django Admin for error messages
2. Check consumer logs
3. Verify email settings in `.env`
4. Check RabbitMQ queue for stuck messages

### Consumer Not Processing

1. Verify consumer is running: `ps aux | grep consume_emails`
2. Check logs for errors
3. Restart consumer service

## Production Recommendations

1. **Use a dedicated RabbitMQ user** (not guest)
2. **Enable SSL/TLS** for RabbitMQ connections in production
3. **Set up monitoring** (RabbitMQ Management UI, logs, alerts)
4. **Configure multiple consumers** for high volume
5. **Set appropriate retry limits** in `consume_emails` command
6. **Regularly clean up** old EmailQueue records

## Files Created/Modified

### New Files:
- `coreconfig/service.py` - RabbitMQ email service
- `coreconfig/models.py` - EmailQueue model (added)
- `coreconfig/admin.py` - EmailQueue admin interface (updated)
- `coreconfig/management/commands/consume_emails.py` - Email consumer command

### Modified Files:
- `base/views.py` - Updated to use RabbitMQ
- `nomination/views.py` - Updated to use RabbitMQ
- `speakers/views.py` - Updated to use RabbitMQ
- `iGamingForms/settings.py` - Added RabbitMQ configuration
- `requirements.txt` - Added pika library

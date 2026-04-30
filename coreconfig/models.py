from django.db import models


class EnvironmentSetting(models.Model):
    SETTING_TYPE_CHOICES = [
        ('ALLOWED_HOST', 'Allowed Host'),
        ('CORS_ORIGIN', 'CORS Allowed Origin'),
        ('CSRF_TRUSTED_ORIGIN', 'CSRF Trusted Origin'),
    ]

    setting_type = models.CharField(max_length=32, choices=SETTING_TYPE_CHOICES)
    value = models.CharField(max_length=512, unique=True)

    def __str__(self):
        return f"{self.get_setting_type_display()}: {self.value}"


class EmailQueue(models.Model):
    """
    Model to track email notifications in the RabbitMQ queue.
    Stores all pending, processing, completed, and failed email tasks.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    EMAIL_TYPE_CHOICES = [
        ('inquiry', 'Inquiry'),
        ('nomination', 'Nomination'),
        ('speaker', 'Speaker Submission'),
        ('registration', 'Event Registration'),
        ('awards_vote', 'Awards Vote Confirmation'),
        ('other', 'Other'),
    ]
    
    email_type = models.CharField(max_length=50, choices=EMAIL_TYPE_CHOICES, default='other')
    subject = models.CharField(max_length=255)
    recipients = models.TextField(help_text="Comma-separated list of recipient emails")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    source_app = models.CharField(max_length=100, help_text="Source application name")
    related_model_id = models.IntegerField(null=True, blank=True, help_text="ID of related model (e.g., Nomination.id)")
    requeue_snapshot = models.JSONField(
        null=True,
        blank=True,
        help_text="Serialized template/body/context so failed emails can be requeued with the same content.",
    )
    retry_count = models.IntegerField(default=0, help_text="Number of retry attempts")
    error_message = models.TextField(null=True, blank=True, help_text="Error message if failed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True, help_text="When email was successfully sent")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Email Queue Item'
        verbose_name_plural = 'Email Queue Items'
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['email_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.get_email_type_display()} - {self.subject} ({self.get_status_display()})"
    
    def get_recipients_list(self):
        """Return recipients as a list"""
        return [r.strip() for r in self.recipients.split(',') if r.strip()]

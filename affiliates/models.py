from django.conf import settings
from django.db import models


class AffiliateApplication(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'

    class PaymentPreference(models.TextChoices):
        REVSHARE = 'revshare', 'Revshare'
        CPA = 'cpa', 'CPA'
        HYBRID = 'hybrid', 'Hybrid'
        CASH = 'cash_payment', 'Cash payment'
        OTHER = 'other', 'Other'

    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=40)
    is_affiliate = models.BooleanField(
        help_text='Whether the applicant identifies as an affiliate.',
    )
    traffic_sources = models.TextField(
        help_text='Comma-separated traffic source labels (e.g. Web, Facebook).',
    )
    traffic_source_other_label = models.CharField(
        max_length=255,
        blank=True,
        help_text='When "Other" is selected: name/description of that source.',
    )
    traffic_source_details = models.JSONField(
        default=dict,
        help_text='Per-source URL or handle (excluding Offline). Keys: Web, Facebook, …',
    )
    traffic_regions = models.TextField(
        help_text='Which regions does your traffic originate from?',
        default='',
    )
    traffic_volume = models.CharField(
        max_length=255,
        help_text='Traffic volume (free-form).',
        default='',
    )
    payment_preferences = models.TextField(
        help_text='Comma-separated payment preferences (Revshare, CPA, Hybrid, Cash payment, Other).',
        default='',
    )
    payment_other_detail = models.CharField(
        max_length=255,
        blank=True,
        help_text='When payment is Other: specify the preferred means.',
    )
    additional_notes = models.TextField(blank=True)

    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='affiliate_reviews',
    )

    staff_notification_sent = models.BooleanField(default=False)
    decision_email_sent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Affiliate application'
        verbose_name_plural = 'Affiliate applications'

    def __str__(self):
        return f'{self.first_name} {self.last_name} <{self.email}> — {self.get_status_display()}'


class AffiliateProofAttachment(models.Model):
    """One proof URL or one uploaded file, optionally tied to a traffic source or Extra."""

    application = models.ForeignKey(
        AffiliateApplication,
        on_delete=models.CASCADE,
        related_name='proof_attachments',
    )
    label = models.CharField(
        max_length=64,
        help_text='Traffic source name (e.g. Web) or "Extra" for additional proof.',
    )
    url = models.TextField(blank=True)
    file = models.FileField(
        upload_to='affiliate_proofs/%Y/%m/',
        blank=True,
        null=True,
    )
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f'{self.label}: {self.url or (self.file.name if self.file else "")}'

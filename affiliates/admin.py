import logging

from django.contrib import admin, messages
from django.utils import timezone

from coreconfig.service import email_service

from .models import AffiliateApplication, AffiliateProofAttachment

logger = logging.getLogger(__name__)


class AffiliateProofAttachmentInline(admin.TabularInline):
    model = AffiliateProofAttachment
    extra = 0
    readonly_fields = ['sort_order']
    fields = ['label', 'url', 'file', 'sort_order']


@admin.register(AffiliateApplication)
class AffiliateApplicationAdmin(admin.ModelAdmin):
    inlines = [AffiliateProofAttachmentInline]
    list_display = [
        'id',
        'full_name',
        'email',
        'status',
        'is_affiliate',
        'payment_preferences',
        'created_at',
        'staff_notification_sent',
        'decision_email_sent',
    ]
    list_filter = ['status', 'is_affiliate', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    readonly_fields = [
        'created_at',
        'updated_at',
        'staff_notification_sent',
        'decision_email_sent',
        'reviewed_at',
        'reviewed_by',
    ]
    fieldsets = (
        (
            'Applicant',
            {
                'fields': (
                    'first_name',
                    'last_name',
                    'email',
                    'phone',
                    'is_affiliate',
                ),
            },
        ),
        (
            'Program details',
            {
                'fields': (
                    'traffic_sources',
                    'traffic_source_other_label',
                    'traffic_source_details',
                    'traffic_regions',
                    'traffic_volume',
                    'payment_preferences',
                    'payment_other_detail',
                    'additional_notes',
                ),
            },
        ),
        (
            'Decision',
            {
                'fields': (
                    'status',
                    'reviewed_at',
                    'reviewed_by',
                    'decision_email_sent',
                ),
            },
        ),
        (
            'Meta',
            {
                'fields': ('created_at', 'updated_at', 'staff_notification_sent'),
            },
        ),
    )

    @admin.display(description='Name')
    def full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'

    def save_model(self, request, obj, form, change):
        prev_status = None
        if change and obj.pk:
            prev_status = (
                AffiliateApplication.objects.filter(pk=obj.pk)
                .values_list('status', flat=True)
                .first()
            )

        decision_needed = obj.status in (
            AffiliateApplication.Status.ACCEPTED,
            AffiliateApplication.Status.REJECTED,
        ) and (not change or prev_status != obj.status)

        if decision_needed:
            obj.reviewed_at = timezone.now()
            obj.reviewed_by = request.user if request.user.is_authenticated else None

        super().save_model(request, obj, form, change)

        if not decision_needed:
            return

        try:
            if obj.status == AffiliateApplication.Status.ACCEPTED:
                template_path = 'affiliates/email/application_accepted.html'
                subject = 'Your affiliate application has been approved'
            else:
                template_path = 'affiliates/email/application_rejected.html'
                subject = 'Update on your affiliate application'

            queue = email_service.send_email_task(
                email_type='affiliate_decision',
                subject=subject,
                recipients=[obj.email],
                context={
                    'first_name': obj.first_name,
                },
                template_path=template_path,
                source_app='affiliates_admin',
                related_model_id=obj.id,
            )
            if queue is not None:
                AffiliateApplication.objects.filter(pk=obj.pk).update(
                    decision_email_sent=True,
                )
        except Exception as e:
            logger.exception('Affiliate decision email failed: %s', e)
            self.message_user(
                request,
                f'Application saved, but the decision email could not be queued: {e}',
                level=messages.ERROR,
            )

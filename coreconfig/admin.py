from django.contrib import admin
from django.utils.html import format_html
from .models import EnvironmentSetting, EmailQueue
from .service import email_service


@admin.register(EnvironmentSetting)
class EnvironmentSettingAdmin(admin.ModelAdmin):
    list_display = ['setting_type', 'value']
    list_filter = ['setting_type']
    search_fields = ['value']


@admin.register(EmailQueue)
class EmailQueueAdmin(admin.ModelAdmin):
    list_display = ['id', 'email_type', 'subject', 'recipients_short', 'status', 
                    'retry_count', 'created_at', 'processed_at', 'requeue_button']
    list_filter = ['status', 'email_type', 'created_at']
    search_fields = ['subject', 'recipients', 'source_app', 'error_message']
    readonly_fields = ['created_at', 'updated_at', 'processed_at', 'retry_count', 'requeue_snapshot']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Email Information', {
            'fields': ('email_type', 'subject', 'recipients', 'status')
        }),
        ('Tracking', {
            'fields': ('source_app', 'related_model_id', 'retry_count', 'requeue_snapshot')
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'processed_at')
        }),
    )
    
    actions = ['requeue_failed_emails']
    
    def recipients_short(self, obj):
        """Display shortened recipients list"""
        recipients = obj.get_recipients_list()
        if len(recipients) > 2:
            return f"{', '.join(recipients[:2])}... (+{len(recipients) - 2})"
        return ', '.join(recipients)
    recipients_short.short_description = 'Recipients'
    
    def requeue_button(self, obj):
        """Display requeue button for failed emails"""
        if obj.status == 'failed':
            return format_html(
                '<a class="button" href="{}">Requeue</a>',
                f'/admin/coreconfig/emailqueue/{obj.id}/requeue/'
            )
        return '-'
    requeue_button.short_description = 'Actions'
    
    def requeue_failed_emails(self, request, queryset):
        """Admin action to requeue failed emails"""
        requeued = 0
        for email_queue in queryset.filter(status='failed'):
            if email_service.requeue_failed_email(email_queue.id):
                requeued += 1
        self.message_user(request, f'{requeued} failed email(s) requeued successfully.')
    requeue_failed_emails.short_description = 'Requeue selected failed emails'
    
    def get_urls(self):
        """Add custom URL for requeue action"""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:email_id>/requeue/',
                self.admin_site.admin_view(self.requeue_email_view),
                name='coreconfig_emailqueue_requeue',
            ),
        ]
        return custom_urls + urls
    
    def requeue_email_view(self, request, email_id):
        """View to handle requeue action"""
        from django.shortcuts import redirect
        from django.contrib import messages
        
        try:
            email_queue = EmailQueue.objects.get(id=email_id)
            if email_queue.status == 'failed':
                if email_service.requeue_failed_email(email_queue.id):
                    messages.success(request, f'Email {email_queue.id} requeued successfully.')
                else:
                    messages.error(request, f'Failed to requeue email {email_queue.id}.')
            else:
                messages.warning(request, f'Email {email_queue.id} is not in failed status.')
        except EmailQueue.DoesNotExist:
            messages.error(request, 'Email queue item not found.')
        
        return redirect('admin:coreconfig_emailqueue_changelist')

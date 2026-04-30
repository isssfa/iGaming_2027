from django.contrib import admin
from .models import Speaker, BecomeASpeaker
from import_export.admin import ImportExportModelAdmin

@admin.register(Speaker)
class SpeakerAdmin(ImportExportModelAdmin):
    list_display = ('name', 'role', 'company', 'is_featured', 'added_by', 'created_at')
    search_fields = ('name', 'role', 'company')
    list_filter = ('is_featured', 'created_at', 'added_by')
    readonly_fields = ('created_at', 'updated_at', 'added_by')

    def event_list(self, obj):
        return ", ".join(obj.get_event_list())

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.added_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(BecomeASpeaker)
class BecomeASpeakerAdmin(ImportExportModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'company_name', 'type_of_participation', 'email_sent', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'company_name', 'job_title')
    list_filter = ('company_type', 'type_of_participation', 'email_sent', 'created_at')
    readonly_fields = ('created_at', 'email_sent')
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone_number', 'linkedin_profile')
        }),
        ('Professional Information', {
            'fields': ('job_title', 'company_name', 'website_url', 'company_type')
        }),
        ('Speaking Details', {
            'fields': ('type_of_participation', 'talk_title', 'topic_description', 'supporting_files')
        }),
        ('Status', {
            'fields': ('email_sent', 'created_at')
        }),
    )

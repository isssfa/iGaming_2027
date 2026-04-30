from django.contrib import admin
from .models import Nomination
from import_export.admin import ImportExportModelAdmin


@admin.register(Nomination)
class NominationAdmin(ImportExportModelAdmin):
    list_display = (
        'full_name',
        'email',
        'company',
        'nominated_company',
        'email_sent',
        'created_at',
    )
    search_fields = ('full_name', 'email', 'company', 'nominated_company')
    list_filter = ('email_sent', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'email_sent')
    fieldsets = (
        ('Nominator Information', {
            'fields': ('full_name', 'email', 'phone_number', 'linkedin_url', 'company', 'role')
        }),
        ('Nomination Details', {
            'fields': (
                'nominated_company',
                'award_category',
                'background_information',
                'specific_instance_project',
                'impact_on_industry',
            )
        }),
        ('Status', {
            'fields': ('email_sent', 'created_at', 'updated_at')
        }),
    )


from django.contrib import admin
from .models import EventRegistration, Inquiry
from import_export.admin import ImportExportModelAdmin

@admin.register(EventRegistration)
class EventRegistrationAdmin(ImportExportModelAdmin):
    list_display = ('first_name', 'last_name', 'company_name', 'work_email', 'email_sent', 'created_at')
    list_filter = ('email_sent', 'created_at', 'user')
    search_fields = ('first_name', 'last_name', 'company_name', 'work_email', 'user__username')
    readonly_fields = ('first_name', 'last_name', 'company_name', 'work_email', 'email_sent', 'interests', 'user', 'created_at')

@admin.register(Inquiry)
class InquiryAdmin(ImportExportModelAdmin):
    list_display = ('name', 'email', 'topic', 'created_at', 'email_sent')
    search_fields = ('name', 'email', 'topic', 'message')
    list_filter = ('created_at',)
    readonly_fields = ('name', 'email', 'topic', 'message', 'created_at')


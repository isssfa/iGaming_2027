from django.contrib import admin
from .models import EventRegistration, Inquiry, Panel, Ticket
from import_export.admin import ImportExportModelAdmin
from speakers.models import Speaker

@admin.register(EventRegistration)
class EventRegistrationAdmin(ImportExportModelAdmin):
    list_display = ('first_name', 'last_name', 'company_name', 'work_email', 'form_type', 'email_sent', 'created_at')
    list_filter = ('form_type', 'email_sent', 'created_at', 'user')
    search_fields = ('first_name', 'last_name', 'company_name', 'work_email', 'user__username')
    readonly_fields = (
        'first_name',
        'last_name',
        'company_name',
        'work_email',
        'phone_number',
        'nationality',
        'website_url',
        'job_title',
        'job_level',
        'company_operation',
        'form_type',
        'brands',
        'products',
        'interests',
        'email_sent',
        'user',
        'created_at',
        'updated_at',
    )

@admin.register(Inquiry)
class InquiryAdmin(ImportExportModelAdmin):
    list_display = ('name', 'email', 'topic', 'created_at', 'email_sent')
    search_fields = ('name', 'email', 'topic', 'message')
    list_filter = ('created_at',)
    readonly_fields = ('name', 'email', 'topic', 'message', 'created_at')


@admin.register(Panel)
class PanelAdmin(ImportExportModelAdmin):
    list_display = ('name', 'start_time', 'location', 'moderator')
    list_filter = ('start_time',)
    search_fields = ('name', 'description', 'location', 'moderator__name')
    filter_horizontal = ('speakers',)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "speakers":
            kwargs["queryset"] = Speaker.objects.all().order_by("name")
        return super().formfield_for_manytomany(db_field, request, **kwargs)


@admin.register(Ticket)
class TicketAdmin(ImportExportModelAdmin):
    list_display = ('label', 'stripe_price_id', 'price', 'door_price', 'is_popular', 'price_increase_date', 'is_active')
    list_filter = ('is_popular', 'is_active')
    search_fields = ('label', 'stripe_price_id', 'description')


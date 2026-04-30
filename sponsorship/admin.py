from django.contrib import admin
from .models import Sponsorship
from import_export.admin import ImportExportModelAdmin


@admin.register(Sponsorship)
class SponsorshipAdmin(ImportExportModelAdmin):
    list_display = ['title','price', 'status', 'icon', 'created_at', 'added_by']
    readonly_fields = ['created_at', 'updated_at', 'added_by', 'total_sold']

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.added_by = request.user
        super().save_model(request, obj, form, change)
from django.contrib import admin
from .models import Sponsor
from .forms import SponsorAdminForm
from import_export.admin import ImportExportModelAdmin

@admin.register(Sponsor)
class SponsorAdmin(ImportExportModelAdmin):
    form = SponsorAdminForm
    list_display = ('name', 'type', 'added_by', 'created_at', "id")
    list_filter = ('type', 'created_at')
    search_fields = ('name', 'added_by__username')
    readonly_fields = ('created_at', 'updated_at', 'added_by')
    ordering = ('-created_at',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('added_by')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.added_by = request.user
        super().save_model(request, obj, form, change)


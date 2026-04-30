from django.contrib import admin
from .models import ExhibitionTier, ExhibitionOption, ExhibitionImage
from import_export.admin import ImportExportModelAdmin

# Inline for ExhibitionImage (to be nested under ExhibitionOption)
class ExhibitionImageInline(admin.TabularInline):
    model = ExhibitionImage
    extra = 1  # Number of empty forms to display
    fields = ('image',)
    readonly_fields = ('created_at', 'updated_at', 'added_by')
    show_change_link = True

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('added_by')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.added_by = request.user
        super().save_model(request, obj, form, change)

# Admin class for ExhibitionOption, which will have ExhibitionImageInline
@admin.register(ExhibitionOption)
class ExhibitionOptionAdmin(ImportExportModelAdmin):
    list_display = ('tier', 'type', 'stand_size', 'price', 'added_by', 'created_at')
    list_filter = ('tier', 'type')
    search_fields = ('type', 'stand_size', 'description')
    readonly_fields = ('added_by', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('tier', 'type', 'stand_size', 'price', 'description')
        }),
        ('Benefits & Status', {
            'fields': ('stand_benefits', 'exhibitor_benefits', 'sponsorship_status', 'notes'),
        }),
        ('Audit In  formation', {
            'fields': ('added_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    inlines = [ExhibitionImageInline] # <--- ExhibitionImage is inline here



    def save_model(self, request, obj, form, change):
        if not change:
            obj.added_by = request.user
        super().save_model(request, obj, form, change)

# Admin class for ExhibitionTier
@admin.register(ExhibitionTier)
class ExhibitionTierAdmin(ImportExportModelAdmin):
    list_display = ('name', 'added_by', 'created_at', 'updated_at')
    search_fields = ('name',)
    readonly_fields = ('added_by', 'created_at', 'updated_at')
    # No inlines here for ExhibitionOption if you want ExhibitionOption
    # to be a top-level admin item.

    fieldsets = (
        (None, {
            'fields': ('name',)
        }),
        ('Audit Information', {
            'fields': ('added_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.added_by = request.user
        super().save_model(request, obj, form, change)
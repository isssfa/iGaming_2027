from django.contrib import admin
from .models import APICSRFToken


@admin.register(APICSRFToken)
class APICSRFTokenAdmin(admin.ModelAdmin):
    list_display = ['token_short', 'used', 'ip_address', 'created_at']
    list_filter = ['used', 'created_at']
    search_fields = ['token', 'ip_address']
    readonly_fields = ['token', 'created_at']
    ordering = ['-created_at']
    
    def token_short(self, obj):
        return f"{obj.token[:16]}..." if obj.token else "-"
    token_short.short_description = "Token"
    
    def has_add_permission(self, request):
        # Don't allow manual creation of tokens
        return False
    
    def has_change_permission(self, request, obj=None):
        # Don't allow editing tokens
        return False

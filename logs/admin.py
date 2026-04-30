from django.contrib import admin
from .models import LogEntry
from import_export.admin import ImportExportModelAdmin


@admin.register(LogEntry)
class LogEntryAdmin(ImportExportModelAdmin):
    list_display = ('level', 'message', 'source_app', 'user', 'created_at')
    list_filter = ('level', 'source_app', 'created_at')
    search_fields = ('message', 'exception')

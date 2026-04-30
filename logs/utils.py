from .models import LogEntry

def log_message(level, message, user=None, source_app=None, exception=None):
    LogEntry.objects.create(
        level=level,
        message=message,
        user=user,
        source_app=source_app,
        exception=exception
    )

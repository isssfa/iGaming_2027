import traceback
from .models import LogEntry

class ExceptionLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except Exception as e:
            # Log unhandled exceptions
            LogEntry.objects.create(
                level='ERROR',
                message=str(e),
                exception=traceback.format_exc(),
                user=request.user if request.user.is_authenticated else None,
                source_app=request.resolver_match.app_name if request.resolver_match else '',
            )
            raise  # Reraise for default error behavior
        else:
            # Also capture handled HTTP error responses like 401/403/404
            if response.status_code in [401, 403, 404, 500]:
                LogEntry.objects.create(
                    level='ERROR',
                    message=f"{response.status_code} - {response.reason_phrase}",
                    exception=None,
                    user=request.user if request.user.is_authenticated else None,
                    source_app=request.resolver_match.app_name if request.resolver_match else '',
                )
            return response

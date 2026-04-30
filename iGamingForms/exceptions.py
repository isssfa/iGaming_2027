from rest_framework.views import exception_handler
from django.conf import settings


def custom_exception_handler(exc, context):
    """
    Custom exception handler that ensures CORS headers are included
    in all error responses. The CORS middleware should handle this,
    but this ensures it works even if middleware doesn't process the response.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Ensure CORS headers are added to error responses
        # The CORS middleware should handle this, but we add them here as backup
        request = context.get('request')
        if request:
            # Get the origin from the request
            origin = request.META.get('HTTP_ORIGIN') or request.META.get('HTTP_REFERER')
            
            # If origin is in allowed origins, add CORS headers
            if origin:
                from urllib.parse import urlparse
                try:
                    parsed = urlparse(origin)
                    origin_domain = f"{parsed.scheme}://{parsed.netloc}"
                    allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
                    
                    if origin_domain in allowed_origins:
                        # Add CORS headers to the response
                        response['Access-Control-Allow-Origin'] = origin_domain
                        response['Access-Control-Allow-Credentials'] = 'true'
                        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
                        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRF-Token, X-Csrf-Token'
                        response['Access-Control-Expose-Headers'] = 'Content-Type'
                except Exception:
                    # If parsing fails, don't add headers (let CORS middleware handle it)
                    pass
    
    return response


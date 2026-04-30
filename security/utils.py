from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
from ipaddress import ip_address
import hashlib
import hmac


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def validate_origin(request):
    """
    Validate that the request comes from an allowed origin.
    Returns True if origin is valid or if origin checking is disabled.
    """
    # Check if origin validation is disabled - if so, always return True
    enable_validation = getattr(settings, 'ENABLE_ORIGIN_VALIDATION', False)
    if not enable_validation:
        return True
    
    # If validation is enabled, check the origin
    origin = request.META.get('HTTP_ORIGIN') or request.META.get('HTTP_REFERER')
    if not origin:
        # If no origin/referer header, reject if validation is enabled
        return False
    
    # Extract domain from origin/referer
    from urllib.parse import urlparse
    try:
        parsed = urlparse(origin)
        origin_domain = f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        # If parsing fails, reject if validation is enabled
        return False
    
    # Check against allowed origins
    allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
    return origin_domain in allowed_origins


def rate_limit_check(request, identifier=None, rate='5/m', method='POST'):
    """
    Simple rate limiting using cache.
    
    Args:
        request: Django request object
        identifier: Optional custom identifier (defaults to IP)
        rate: Rate limit string like '5/m' (5 per minute), '10/h' (10 per hour)
        method: HTTP method to check
    
    Returns:
        (is_allowed, remaining_requests, reset_time)
    """
    if request.method != method:
        return True, None, None
    
    # Parse rate limit
    try:
        limit, period = rate.split('/')
        limit = int(limit)
        period_map = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        period_seconds = period_map.get(period.lower(), 60)
    except (ValueError, KeyError):
        # Default to 5 per minute
        limit, period_seconds = 5, 60
    
    # Get identifier (IP address by default)
    if identifier is None:
        identifier = get_client_ip(request)
    
    # Create cache key
    cache_key = f'rate_limit_{method}_{identifier}'
    
    # Get current count
    current_count = cache.get(cache_key, 0)
    
    if current_count >= limit:
        # Get reset time
        ttl = cache.ttl(cache_key)
        return False, 0, ttl
    
    # Increment counter
    cache.set(cache_key, current_count + 1, timeout=period_seconds)
    
    remaining = limit - (current_count + 1)
    return True, remaining, period_seconds


def sign_request(data, secret_key=None):
    """
    Sign request data with HMAC for additional security.
    This is optional and can be used for extra protection.
    """
    if secret_key is None:
        secret_key = getattr(settings, 'API_SIGNING_SECRET', settings.SECRET_KEY)
    
    # Create a string representation of the data
    data_str = str(sorted(data.items()))
    
    # Generate HMAC signature
    signature = hmac.new(
        secret_key.encode(),
        data_str.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return signature


def verify_request_signature(data, signature, secret_key=None):
    """Verify request signature."""
    if secret_key is None:
        secret_key = getattr(settings, 'API_SIGNING_SECRET', settings.SECRET_KEY)
    
    expected_signature = sign_request(data, secret_key)
    return hmac.compare_digest(expected_signature, signature)


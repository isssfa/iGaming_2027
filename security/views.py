from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .models import APICSRFToken
from .utils import get_client_ip, rate_limit_check


class CSRFTokenView(APIView):
    """
    Public endpoint to obtain a CSRF token for API protection.
    This endpoint is public and doesn't require authentication.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Rate limit token requests (more lenient than POST endpoints)
        is_allowed, remaining, reset_time = rate_limit_check(
            request,
            rate='20/m',  # Allow 20 token requests per minute
            method='GET'
        )
        
        if not is_allowed:
            return Response(
                {"detail": "Rate limit exceeded. Please try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # Get client IP
        ip_address = get_client_ip(request)
        
        # Generate new token
        raw_token, token_obj = APICSRFToken.generate_token(ip_address)
        
        return Response({
            "csrf_token": raw_token,
            "expires_in": APICSRFToken.EXPIRY_MINUTES * 60,  # seconds
            "message": "Token is single-use and expires after use or 15 minutes."
        }, status=status.HTTP_200_OK)

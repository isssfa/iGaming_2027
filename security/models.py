from django.db import models
from django.utils import timezone
from django.core.cache import cache
import secrets
import hashlib
from datetime import timedelta


class APICSRFToken(models.Model):
    """
    Model to store CSRF tokens for API protection.
    Tokens are single-use and expire after a set time.
    """
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Token expires after 15 minutes by default
    EXPIRY_MINUTES = 15
    
    class Meta:
        verbose_name = "API CSRF Token"
        verbose_name_plural = "API CSRF Tokens"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token', 'used']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.token[:8]}... ({'used' if self.used else 'active'})"
    
    @classmethod
    def generate_token(cls, ip_address=None):
        """Generate a new CSRF token and clean up expired/used tokens."""
        # Clean up expired and used tokens before generating new one
        cls._cleanup_tokens()
        
        # Generate a secure random token
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        # Store in database
        token_obj = cls.objects.create(
            token=token_hash,
            ip_address=ip_address
        )
        
        # Also store in cache for faster lookups (expires in 20 minutes)
        cache.set(f'csrf_token_{token_hash}', True, timeout=20 * 60)
        
        return raw_token, token_obj
    
    @classmethod
    def _cleanup_tokens(cls):
        """
        Bulk delete expired and used tokens.
        This is called automatically when generating new tokens.
        """
        now = timezone.now()
        expiry_cutoff = now - timedelta(minutes=cls.EXPIRY_MINUTES)
        
        # Delete all used tokens and all expired tokens (older than EXPIRY_MINUTES)
        deleted_count = cls.objects.filter(
            models.Q(used=True) | models.Q(created_at__lt=expiry_cutoff)
        ).delete()[0]
        
        return deleted_count
    
    @classmethod
    def validate_token(cls, token, ip_address=None):
        """
        Validate a CSRF token. Returns (is_valid, token_obj).
        Token is marked as used after validation.
        """
        if not token:
            return False, None
        
        # Hash the provided token
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        try:
            token_obj = cls.objects.get(token=token_hash, used=False)
        except cls.DoesNotExist:
            # Check cache first for faster failure
            if not cache.get(f'csrf_token_{token_hash}'):
                return False, None
            return False, None
        
        # Check if token has expired
        expiry_time = token_obj.created_at + timedelta(minutes=cls.EXPIRY_MINUTES)
        if timezone.now() > expiry_time:
            token_obj.used = True
            token_obj.save(update_fields=['used'])
            cache.delete(f'csrf_token_{token_hash}')
            return False, None
        
        # Optional: Verify IP address matches (can be disabled for flexibility)
        # if ip_address and token_obj.ip_address and token_obj.ip_address != ip_address:
        #     return False, None
        
        # Mark token as used (single-use)
        token_obj.used = True
        token_obj.save(update_fields=['used'])
        cache.delete(f'csrf_token_{token_hash}')
        
        return True, token_obj
    
    @classmethod
    def cleanup_expired_tokens(cls):
        """
        Clean up expired and used tokens older than 24 hours.
        This is a more aggressive cleanup for manual/scheduled runs.
        """
        cutoff_time = timezone.now() - timedelta(hours=24)
        deleted_count = cls.objects.filter(
            models.Q(used=True) | models.Q(created_at__lt=cutoff_time)
        ).delete()[0]
        return deleted_count

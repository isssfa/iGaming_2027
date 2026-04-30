# API Security System

This security system provides CSRF token protection and rate limiting for POST endpoints without requiring API token authentication, which prevents token exposure in the browser.

## Features

1. **CSRF Token Protection**: Single-use tokens that expire after 15 minutes
2. **Rate Limiting**: Configurable rate limits per IP address
3. **Origin Validation**: Optional validation of request origin
4. **Public GET Endpoints**: All GET requests are now public (no auth required)
5. **Protected POST Endpoints**: POST requests require CSRF tokens instead of API tokens

## How It Works

### For Frontend Developers

1. **Get a CSRF Token** (before making POST requests):
   ```javascript
   // GET request to obtain token
   const response = await fetch('https://your-api.com/api/security/csrf-token/');
   const data = await response.json();
   const csrfToken = data.csrf_token;
   ```

2. **Use the Token in POST Requests**:
   ```javascript
   // Include token in header or request body
   const postResponse = await fetch('https://your-api.com/api/event-registration/', {
     method: 'POST',
     headers: {
       'Content-Type': 'application/json',
       'X-CSRF-Token': csrfToken,  // Or include in body as 'csrf_token'
     },
     body: JSON.stringify({
       // your data here
       csrf_token: csrfToken,  // Alternative: include in body
     })
   });
   ```

3. **Important Notes**:
   - Tokens are **single-use** - get a new token for each POST request
   - Tokens expire after **15 minutes** if not used
   - Rate limit: **10 POST requests per minute** per IP (configurable per endpoint)

### For Backend Developers

#### Making GET Endpoints Public

GET endpoints are now public by default. No changes needed if you want them public.

If you need to protect a GET endpoint, use:
```python
from rest_framework.permissions import IsAuthenticated

class MyView(APIView):
    permission_classes = [IsAuthenticated]
```

#### Protecting POST Endpoints

Use the `ProtectedPostPermission` class:

```python
from security.permissions import ProtectedPostPermission

class MyPostView(APIView):
    permission_classes = [ProtectedPostPermission]
    rate_limit = '10/m'  # Optional: customize rate limit (default: 10/m)
```

#### Rate Limit Format

- `'5/m'` - 5 requests per minute
- `'10/h'` - 10 requests per hour
- `'100/d'` - 100 requests per day
- `'2/s'` - 2 requests per second

## Configuration

### Settings (settings.py)

```python
# Enable origin validation (recommended for production)
ENABLE_ORIGIN_VALIDATION = True

# Optional: Separate secret for request signing
API_SIGNING_SECRET = 'your-secret-key'

# Cache configuration (required for rate limiting)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        # For production, use Redis or Memcached:
        # 'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        # 'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### Environment Variables (.env)

```env
# Enable origin validation (True/False)
ENABLE_ORIGIN_VALIDATION=True

# Optional: Separate API signing secret
API_SIGNING_SECRET=your-secret-key-here
```

## Maintenance

### Cleanup Expired Tokens

Run periodically (e.g., via cron):

```bash
python manage.py cleanup_csrf_tokens
```

Or set up a cron job:
```bash
# Run every hour
0 * * * * cd /path/to/project && python manage.py cleanup_csrf_tokens
```

## Security Considerations

### Why This Approach?

1. **No Token Exposure**: API tokens are no longer needed in the browser
2. **CSRF Protection**: Single-use tokens prevent CSRF attacks
3. **Rate Limiting**: Prevents abuse and automated attacks
4. **Origin Validation**: Optional but recommended to ensure requests come from your domain

### Limitations

- CSRF tokens are stored in the database (consider Redis for high-traffic sites)
- Rate limiting uses IP addresses (can be bypassed with proxies, but adds friction)
- Origin validation can be bypassed if not properly configured

### Production Recommendations

1. Use **Redis** for caching (better performance and persistence)
2. Enable **origin validation** in production
3. Set up **monitoring** for rate limit violations
4. Consider **CAPTCHA** for sensitive endpoints
5. Use **HTTPS only** in production
6. Set up **logging** for security events

## API Endpoints

### GET /api/security/csrf-token/

Public endpoint to obtain a CSRF token.

**Response:**
```json
{
  "csrf_token": "random-token-string",
  "expires_in": 900,
  "message": "Token is single-use and expires after use or 15 minutes."
}
```

**Rate Limit:** 20 requests per minute

## Migration Guide

### From Token Authentication to CSRF Protection

**Before:**
```javascript
fetch('/api/endpoint/', {
  headers: {
    'Authorization': 'Token your-api-token'
  }
});
```

**After:**
```javascript
// 1. Get CSRF token
const tokenResponse = await fetch('/api/security/csrf-token/');
const { csrf_token } = await tokenResponse.json();

// 2. Use in POST request
fetch('/api/endpoint/', {
  method: 'POST',
  headers: {
    'X-CSRF-Token': csrf_token
  },
  body: JSON.stringify(data)
});
```

## Troubleshooting

### "CSRF token is required"
- Make sure you're getting a token from `/api/security/csrf-token/` before POST requests
- Include the token in the `X-CSRF-Token` header or `csrf_token` in the body

### "Invalid or expired CSRF token"
- Tokens are single-use - get a new token for each request
- Tokens expire after 15 minutes
- Make sure you're using the token immediately after getting it

### "Rate limit exceeded"
- Default limit is 10 requests per minute per IP
- Wait before making another request
- Contact admin if you need higher limits

### "Request origin is not allowed"
- Make sure your domain is in `CORS_ALLOWED_ORIGINS` in settings
- Check that `ENABLE_ORIGIN_VALIDATION` is set correctly


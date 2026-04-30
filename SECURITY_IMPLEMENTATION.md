# API Security Implementation Summary

## ✅ Implementation Complete

A comprehensive security system has been implemented to protect your POST endpoints without exposing API tokens in the browser.

## What Was Implemented

### 1. **CSRF Token System** (`security` app)
   - Single-use tokens that expire after 15 minutes
   - Database-backed token storage with cache optimization
   - Public endpoint to obtain tokens: `/api/security/csrf-token/`

### 2. **Rate Limiting**
   - Configurable per-endpoint rate limits
   - Default: 10 requests per minute per IP
   - Uses Django cache for efficient tracking

### 3. **Origin Validation**
   - Optional validation to ensure requests come from allowed domains
   - Configurable via `ENABLE_ORIGIN_VALIDATION` setting

### 4. **Updated Endpoints**
   - **GET endpoints**: Now public (no authentication required)
     - `/api/sponsorships/`
     - `/api/sponsors/`
     - `/api/exhibition/`
     - `/api/speakers/`
   
   - **POST endpoints**: Protected with CSRF tokens
     - `/api/event-registration/` (10 requests/minute)
     - `/api/inquiry/` (10 requests/minute)

## Next Steps

### 1. Install Dependencies (if needed)
```bash
pip install -r requirements.txt
```

### 2. Run Migrations
```bash
python manage.py makemigrations security
python manage.py migrate
```

### 3. Update Your Frontend

**Before (with API token):**
```javascript
fetch('/api/event-registration/', {
  method: 'POST',
  headers: {
    'Authorization': 'Token your-api-token',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(data)
});
```

**After (with CSRF token):**
```javascript
// Step 1: Get CSRF token
const tokenResponse = await fetch('/api/security/csrf-token/');
const { csrf_token } = await tokenResponse.json();

// Step 2: Use in POST request
fetch('/api/event-registration/', {
  method: 'POST',
  headers: {
    'X-CSRF-Token': csrf_token,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(data)
});
```

### 4. Configure Environment Variables

Add to your `.env` file:
```env
# Enable origin validation (recommended for production)
ENABLE_ORIGIN_VALIDATION=True

# Optional: Separate API signing secret
# API_SIGNING_SECRET=your-secret-key-here
```

### 5. Set Up Maintenance (Optional)

Add a cron job to clean up expired tokens:
```bash
# Run every hour
0 * * * * cd /path/to/project && python manage.py cleanup_csrf_tokens
```

Or use a task scheduler on Windows.

## Production Recommendations

1. **Use Redis for Caching** (better performance):
   ```python
   CACHES = {
       'default': {
           'BACKEND': 'django.core.cache.backends.redis.RedisCache',
           'LOCATION': 'redis://127.0.0.1:6379/1',
       }
   }
   ```

2. **Enable Origin Validation**:
   ```python
   ENABLE_ORIGIN_VALIDATION = True
   ```

3. **Monitor Rate Limits**: Set up logging/alerts for rate limit violations

4. **Use HTTPS**: Always use HTTPS in production

## Files Created/Modified

### New Files:
- `security/models.py` - CSRF token model
- `security/views.py` - Token generation endpoint
- `security/permissions.py` - Custom permission class
- `security/utils.py` - Rate limiting and validation utilities
- `security/urls.py` - Security endpoints
- `security/admin.py` - Admin interface
- `security/management/commands/cleanup_csrf_tokens.py` - Cleanup command
- `security/README.md` - Detailed documentation

### Modified Files:
- `iGamingForms/settings.py` - Added security app, cache config, updated REST framework settings
- `iGamingForms/api_urls.py` - Added security endpoints
- `base/views.py` - Updated to use ProtectedPostPermission
- `sponsorship/views.py` - Made public (AllowAny)
- `sponsor/views.py` - Made public (AllowAny)
- `exhibition/views.py` - Made public (AllowAny)
- `speakers/views.py` - Made public (AllowAny)

## Testing

### Test CSRF Token Endpoint:
```bash
curl http://localhost:8000/api/security/csrf-token/
```

### Test POST Endpoint:
```bash
# 1. Get token
TOKEN=$(curl -s http://localhost:8000/api/security/csrf-token/ | jq -r '.csrf_token')

# 2. Use token
curl -X POST http://localhost:8000/api/event-registration/ \
  -H "X-CSRF-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"first_name": "Test", ...}'
```

## Why This Approach is Better

1. **No Token Exposure**: API tokens never appear in browser code
2. **Simpler than Challenge-Response**: Single request to get token, then use it
3. **Industry Standard**: CSRF protection is a well-established pattern
4. **Rate Limiting**: Built-in protection against abuse
5. **Flexible**: Easy to customize per endpoint

## Support

For detailed documentation, see `security/README.md`

For issues or questions, check:
- Token validation errors → Check token is fresh and single-use
- Rate limit errors → Wait or adjust limits
- Origin validation errors → Check CORS_ALLOWED_ORIGINS setting


# Frontend Integration Guide

## Quick Start

### React/JavaScript Example

```javascript
// Utility function to get and use CSRF token
async function makeProtectedPost(url, data) {
  // Step 1: Get CSRF token
  const tokenResponse = await fetch('/api/security/csrf-token/');
  if (!tokenResponse.ok) {
    throw new Error('Failed to get CSRF token');
  }
  const { csrf_token } = await tokenResponse.json();
  
  // Step 2: Make POST request with token
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'X-CSRF-Token': csrf_token,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  
  return response;
}

// Usage
try {
  const response = await makeProtectedPost('/api/event-registration/', {
    first_name: 'John',
    last_name: 'Doe',
    // ... other fields
  });
  
  if (response.ok) {
    const result = await response.json();
    console.log('Success:', result);
  } else {
    const error = await response.json();
    console.error('Error:', error);
  }
} catch (error) {
  console.error('Request failed:', error);
}
```

### React Hook Example

```javascript
import { useState, useCallback } from 'react';

function useProtectedPost() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const post = useCallback(async (url, data) => {
    setLoading(true);
    setError(null);
    
    try {
      // Get CSRF token
      const tokenResponse = await fetch('/api/security/csrf-token/');
      if (!tokenResponse.ok) {
        throw new Error('Failed to get CSRF token');
      }
      const { csrf_token } = await tokenResponse.json();
      
      // Make POST request
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'X-CSRF-Token': csrf_token,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Request failed');
      }
      
      return await response.json();
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { post, loading, error };
}

// Usage in component
function RegistrationForm() {
  const { post, loading, error } = useProtectedPost();
  
  const handleSubmit = async (formData) => {
    try {
      const result = await post('/api/event-registration/', formData);
      console.log('Registration successful:', result);
    } catch (err) {
      console.error('Registration failed:', err);
    }
  };
  
  return (
    // Your form JSX
  );
}
```

### Axios Example

```javascript
import axios from 'axios';

// Create axios instance
const api = axios.create({
  baseURL: '/api',
});

// Interceptor to add CSRF token to POST requests
api.interceptors.request.use(async (config) => {
  if (config.method === 'post' || config.method === 'put' || config.method === 'patch') {
    // Get CSRF token
    const tokenResponse = await axios.get('/api/security/csrf-token/');
    const csrfToken = tokenResponse.data.csrf_token;
    
    // Add to headers
    config.headers['X-CSRF-Token'] = csrfToken;
  }
  return config;
});

// Usage
api.post('/event-registration/', {
  first_name: 'John',
  last_name: 'Doe',
  // ... other fields
})
.then(response => {
  console.log('Success:', response.data);
})
.catch(error => {
  console.error('Error:', error.response?.data || error.message);
});
```

## Important Notes

1. **Tokens are Single-Use**: Get a new token for each POST request
2. **Tokens Expire**: Tokens expire after 15 minutes if not used
3. **Rate Limits**: Default is 10 requests per minute per IP
4. **Error Handling**: Always handle potential errors:
   - Token fetch failures
   - Invalid/expired tokens
   - Rate limit exceeded
   - Network errors

## Error Handling

```javascript
async function makeProtectedPost(url, data) {
  try {
    // Get token
    const tokenResponse = await fetch('/api/security/csrf-token/');
    
    if (tokenResponse.status === 429) {
      throw new Error('Too many token requests. Please wait.');
    }
    
    if (!tokenResponse.ok) {
      throw new Error('Failed to get CSRF token');
    }
    
    const { csrf_token } = await tokenResponse.json();
    
    // Make POST request
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRF-Token': csrf_token,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (response.status === 403) {
      const error = await response.json();
      if (error.detail?.includes('CSRF token')) {
        throw new Error('Invalid or expired token. Please try again.');
      }
      if (error.detail?.includes('Rate limit')) {
        throw new Error('Too many requests. Please wait a moment.');
      }
      throw new Error(error.detail || 'Request forbidden');
    }
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Request failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Request error:', error);
    throw error;
  }
}
```

## Testing

### Test in Browser Console

```javascript
// Test token endpoint
fetch('/api/security/csrf-token/')
  .then(r => r.json())
  .then(console.log);

// Test POST with token
fetch('/api/security/csrf-token/')
  .then(r => r.json())
  .then(({csrf_token}) => {
    return fetch('/api/event-registration/', {
      method: 'POST',
      headers: {
        'X-CSRF-Token': csrf_token,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({test: 'data'})
    });
  })
  .then(r => r.json())
  .then(console.log)
  .catch(console.error);
```

## Migration Checklist

- [ ] Remove API token from frontend code
- [ ] Update all POST requests to use CSRF tokens
- [ ] Add error handling for token failures
- [ ] Test all POST endpoints
- [ ] Update API documentation
- [ ] Test rate limiting behavior
- [ ] Verify origin validation (if enabled)


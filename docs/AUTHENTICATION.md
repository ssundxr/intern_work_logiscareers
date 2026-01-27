# API Authentication Guide

## Overview

The Logis AI Candidate Engine uses **Bearer Token Authentication** for all API endpoints (service-to-service authentication). This ensures only authorized applications (e.g., the Django REST Framework backend) can access the AI Engine APIs.

## Authentication Method

- **Type:** Static API Token (Bearer Token)
- **Header:** `Authorization: Bearer <token>`
- **Scope:** All API endpoints (except health checks)
- **Protocol:** HTTPS required for production

## Quick Start

### 1. Generate an API Token

Generate a secure random token using Python:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Example output:
```
XyZ9K2mN8pQ4rT6vW1hJ3lF5gD7sA0bC9eR2tY4uI6oP8aS1dF3gH5jK7l
```

### 2. Configure the AI Engine

Add the token to your `.env` file:

```bash
# .env
AI_ENGINE_API_TOKEN=XyZ9K2mN8pQ4rT6vW1hJ3lF5gD7sA0bC9eR2tY4uI6oP8aS1dF3gH5jK7l
```

### 3. Configure the DRF Application

Add the same token to your Django application's settings:

```python
# settings.py or environment variables
AI_ENGINE_API_TOKEN = "XyZ9K2mN8pQ4rT6vW1hJ3lF5gD7sA0bC9eR2tY4uI6oP8aS1dF3gH5jK7l"
AI_ENGINE_BASE_URL = "https://ai-engine.logiscareers.com"
```

### 4. Make Authenticated Requests

#### Python (requests library)

```python
import requests
import os

# Configuration
AI_ENGINE_TOKEN = os.getenv("AI_ENGINE_API_TOKEN")
AI_ENGINE_URL = os.getenv("AI_ENGINE_BASE_URL")

# Prepare headers
headers = {
    "Authorization": f"Bearer {AI_ENGINE_TOKEN}",
    "Content-Type": "application/json"
}

# Example: Evaluate candidate
payload = {
    "job": {...},
    "candidate": {...}
}

response = requests.post(
    f"{AI_ENGINE_URL}/api/v1/compare",
    json=payload,
    headers=headers
)

if response.status_code == 200:
    result = response.json()
    print(f"Overall Score: {result['overall_score']}")
elif response.status_code == 401:
    print("Authentication failed - invalid token")
else:
    print(f"Error: {response.status_code}")
```

#### Django REST Framework Service Class

```python
# services/ai_engine_client.py
import requests
from django.conf import settings
from typing import Dict, Any

class AIEngineClient:
    """Client for AI Engine API"""
    
    def __init__(self):
        self.base_url = settings.AI_ENGINE_BASE_URL
        self.token = settings.AI_ENGINE_API_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def evaluate_candidate(self, job_data: Dict, candidate_data: Dict) -> Dict[str, Any]:
        """Evaluate a candidate against a job"""
        url = f"{self.base_url}/api/v1/compare"
        
        response = requests.post(
            url,
            json={"job": job_data, "candidate": candidate_data},
            headers=self.headers,
            timeout=30
        )
        
        response.raise_for_status()  # Raises exception for 4xx/5xx
        return response.json()
    
    def parse_cv(self, cv_text: str) -> Dict[str, Any]:
        """Parse CV text"""
        url = f"{self.base_url}/api/v1/cv/parse"
        
        response = requests.post(
            url,
            json={"cv_text": cv_text},
            headers=self.headers,
            timeout=30
        )
        
        response.raise_for_status()
        return response.json()
```

#### cURL

```bash
curl -X POST "https://ai-engine.logiscareers.com/api/v1/compare" \
  -H "Authorization: Bearer XyZ9K2mN8pQ4rT6vW1hJ3lF5gD7sA0bC9eR2tY4uI6oP8aS1dF3gH5jK7l" \
  -H "Content-Type: application/json" \
  -d '{
    "job": {...},
    "candidate": {...}
  }'
```

## API Endpoints

### Protected Endpoints (Require Authentication)

All endpoints under `/api/v1/` require Bearer token authentication:

- `POST /api/v1/evaluate` - Evaluate candidate against job
- `POST /api/v1/compare` - Compare candidate to job (DRF-compatible)
- `POST /api/v1/cv/parse` - Parse CV text
- `POST /api/v1/cv/parse-to-candidate` - Parse CV and create Candidate object
- `POST /api/v1/cv/extract-skills` - Extract skills from CV

### Public Endpoints (No Authentication Required)

Health check endpoints are publicly accessible:

- `GET /health` - Liveness probe
- `GET /ready` - Readiness probe

## Response Codes

| Status Code | Description | Example Response |
|-------------|-------------|------------------|
| `200 OK` | Request successful | `{"overall_score": 85, ...}` |
| `401 Unauthorized` | Missing or invalid token | `{"detail": "Unauthorized"}` |
| `422 Unprocessable Entity` | Validation error | `{"error_code": "VALIDATION_ERROR", ...}` |
| `500 Internal Server Error` | Server error | `{"error_code": "SCORING_ERROR", ...}` |

## Error Handling

### Missing Authorization Header

**Request:**
```bash
curl -X POST "https://ai-engine.logiscareers.com/api/v1/compare" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

**Response:**
```json
{
  "detail": "Unauthorized"
}
```
**Status:** `401 Unauthorized`  
**Headers:** `WWW-Authenticate: Bearer`

### Invalid Token Format

**Request:**
```bash
# Missing "Bearer" prefix
curl -X POST "https://ai-engine.logiscareers.com/api/v1/compare" \
  -H "Authorization: XyZ9K2mN..." \
  -d '{...}'
```

**Response:**
```json
{
  "detail": "Unauthorized"
}
```
**Status:** `401 Unauthorized`

### Invalid Token Value

**Request:**
```bash
curl -X POST "https://ai-engine.logiscareers.com/api/v1/compare" \
  -H "Authorization: Bearer INVALID_TOKEN" \
  -d '{...}'
```

**Response:**
```json
{
  "detail": "Unauthorized"
}
```
**Status:** `401 Unauthorized`

## Security Best Practices

### ✅ DO

1. **Use HTTPS in production** - Never send tokens over HTTP
2. **Store tokens in environment variables** - Never hardcode in source code
3. **Use secure token generation** - Use cryptographically secure random generators
4. **Rotate tokens periodically** - Update tokens every 90 days
5. **Limit token exposure** - Only share with authorized services
6. **Monitor authentication failures** - Set up alerts for repeated 401s
7. **Use connection timeouts** - Prevent hanging requests

### ❌ DON'T

1. **Never commit tokens to Git** - Add `.env` to `.gitignore`
2. **Never log tokens** - Redact sensitive data from logs
3. **Never share tokens in plain text** - Use secure channels (e.g., password managers)
4. **Never expose tokens in URLs** - Always use headers
5. **Never reuse tokens across environments** - Use separate tokens for dev/staging/prod
6. **Never disable HTTPS in production** - SSL/TLS is mandatory

## Token Management

### Generating Tokens

```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL
openssl rand -base64 32

# Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('base64url'))"
```

### Rotating Tokens

1. Generate a new token
2. Update AI Engine `.env` file with new token
3. Restart AI Engine service
4. Update DRF application with new token
5. Restart DRF application
6. Monitor logs for authentication errors
7. Invalidate old token

### Environment-Specific Tokens

Use different tokens for each environment:

```bash
# Development
AI_ENGINE_API_TOKEN=dev_XyZ9K2mN8pQ4rT6vW1hJ3lF5...

# Staging
AI_ENGINE_API_TOKEN=stg_A1bC2dE3fG4hI5jK6lM7nO8...

# Production
AI_ENGINE_API_TOKEN=prod_P9oI8uY7tR6eW5qA4sD3f...
```

## Development Mode

If `AI_ENGINE_API_TOKEN` is not set or is empty, authentication is **disabled**. This allows local development without authentication:

```bash
# .env (development)
# AI_ENGINE_API_TOKEN=  # Commented out or empty
```

⚠️ **WARNING:** Never deploy to production without authentication enabled!

## Testing Authentication

### Test Script

Create `test_auth.py`:

```python
import requests
import os
import sys

BASE_URL = os.getenv("AI_ENGINE_BASE_URL", "http://localhost:8000")
TOKEN = os.getenv("AI_ENGINE_API_TOKEN")

def test_no_auth():
    """Test request without Authorization header"""
    print("Test 1: No Authorization header...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200, "Health check should work without auth"
    print("✓ Health check works without auth")
    
    response = requests.post(f"{BASE_URL}/api/v1/compare", json={})
    assert response.status_code == 401, "Protected endpoint should return 401"
    print("✓ Protected endpoint rejects request without auth")

def test_invalid_token():
    """Test request with invalid token"""
    print("\nTest 2: Invalid token...")
    headers = {"Authorization": "Bearer INVALID_TOKEN"}
    response = requests.post(f"{BASE_URL}/api/v1/compare", json={}, headers=headers)
    assert response.status_code == 401, "Should return 401 for invalid token"
    print("✓ Invalid token rejected")

def test_valid_token():
    """Test request with valid token"""
    print("\nTest 3: Valid token...")
    if not TOKEN:
        print("⚠ Skipping - AI_ENGINE_API_TOKEN not set")
        return
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(f"{BASE_URL}/health", headers=headers)
    assert response.status_code == 200, "Should work with valid token"
    print("✓ Valid token accepted")

if __name__ == "__main__":
    test_no_auth()
    test_invalid_token()
    test_valid_token()
    print("\n✓ All authentication tests passed!")
```

Run tests:
```bash
export AI_ENGINE_BASE_URL="http://localhost:8000"
export AI_ENGINE_API_TOKEN="your-token-here"
python test_auth.py
```

## Swagger UI Testing

1. Navigate to `http://localhost:8000/docs`
2. Click the **Authorize** button (lock icon)
3. Enter your token in the value field
4. Click **Authorize**
5. Click **Close**
6. Try any endpoint - the token will be included automatically

## Troubleshooting

### Issue: 401 Unauthorized

**Possible Causes:**
- Token not set in environment variables
- Token mismatch between AI Engine and DRF
- Missing "Bearer" prefix in header
- Token contains extra whitespace or newlines

**Solution:**
```python
# Verify token is loaded correctly
import os
token = os.getenv("AI_ENGINE_API_TOKEN")
print(f"Token length: {len(token) if token else 0}")
print(f"Token value: {token[:10]}..." if token else "Token not set")
```

### Issue: Authentication disabled in production

**Cause:** `AI_ENGINE_API_TOKEN` not set in production environment

**Solution:**
1. Set environment variable in production deployment
2. Restart the service
3. Verify with: `curl http://your-domain/api/v1/compare` (should return 401)

### Issue: Token rotation not working

**Cause:** Services not restarted after token update

**Solution:**
1. Update `.env` file
2. Restart both AI Engine and DRF services
3. Clear any cached configurations
4. Test with new token

## Support

For issues or questions:
- Check logs: `tail -f logs/app.log`
- Review Swagger UI: `http://localhost:8000/docs`
- Contact: DevOps Team

## References

- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [HTTP Bearer Authentication](https://developer.mozilla.org/en-US/docs/Web/HTTP/Authentication)
- [OWASP API Security](https://owasp.org/www-project-api-security/)

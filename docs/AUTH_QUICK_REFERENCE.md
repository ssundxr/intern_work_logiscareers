# Authentication Quick Reference Card

## 🔑 For AI Engine Developers

### Generate Token
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Configure (.env)
```env
AI_ENGINE_API_TOKEN=your-generated-token-here
```

### Start Server
```bash
uvicorn main:app --reload
```

### Test Authentication
```bash
# Without token (should fail - 401)
curl http://localhost:8000/api/v1/compare -d '{}'

# With token (should work)
curl http://localhost:8000/api/v1/compare \
  -H "Authorization: Bearer <token>" \
  -d '{"job":{}, "candidate":{}}'
```

---

## 🔑 For DRF Application Developers

### Configure Django Settings
```python
# settings.py
AI_ENGINE_API_TOKEN = os.environ.get('AI_ENGINE_API_TOKEN')
AI_ENGINE_BASE_URL = 'https://ai-engine.logiscareers.com'
```

### Create Client Service
```python
# services/ai_engine_client.py
import requests
from django.conf import settings

class AIEngineClient:
    def __init__(self):
        self.base_url = settings.AI_ENGINE_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {settings.AI_ENGINE_API_TOKEN}",
            "Content-Type": "application/json"
        }
    
    def compare_candidate(self, job_data, candidate_data):
        """Compare candidate against job"""
        response = requests.post(
            f"{self.base_url}/api/v1/compare",
            json={"job": job_data, "candidate": candidate_data},
            headers=self.headers,
            timeout=30
        )
        response.raise_for_status()  # Raises for 4xx/5xx
        return response.json()
    
    def parse_cv(self, cv_text):
        """Parse CV text"""
        response = requests.post(
            f"{self.base_url}/api/v1/cv/parse",
            json={"cv_text": cv_text},
            headers=self.headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
```

### Use in Views
```python
from services.ai_engine_client import AIEngineClient

def evaluate_candidate_view(request):
    client = AIEngineClient()
    
    try:
        result = client.compare_candidate(
            job_data=get_job_data(),
            candidate_data=get_candidate_data()
        )
        return JsonResponse(result)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            logger.error("AI Engine authentication failed - check token")
            return JsonResponse({"error": "Authentication failed"}, status=500)
        raise
```

---

## 📋 Common Issues

### Issue: 401 Unauthorized
**Cause:** Missing or invalid token  
**Fix:** Verify `AI_ENGINE_API_TOKEN` is set correctly

### Issue: "Unauthorized" with token
**Cause:** Token mismatch or missing "Bearer" prefix  
**Fix:** Ensure header format: `Authorization: Bearer <token>`

### Issue: Works locally, fails in production
**Cause:** Token not set in production environment  
**Fix:** Add token to production environment variables

---

## 🔗 Full Documentation
- **[AUTHENTICATION.md](AUTHENTICATION.md)** - Complete guide
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Implementation details
- **Swagger UI:** http://localhost:8000/docs

---

## 🚨 Security Reminders

✅ **DO:**
- Use HTTPS in production
- Store token in environment variables
- Rotate tokens every 90 days
- Use different tokens per environment

❌ **DON'T:**
- Commit tokens to Git
- Log tokens
- Share tokens in plain text
- Use same token across environments

# API Documentation

## Base URL

```
Development: http://localhost:8000
Production:  https://api.logis-career.com
```

## Authentication

Currently no authentication required. Future versions may implement API key or JWT authentication.

## Endpoints

### Health Check

#### GET `/health`

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2026-01-24T12:00:00.000Z"
}
```

**Status Codes:**
- `200 OK` - Service is healthy

---

### CV Parsing

#### POST `/api/v1/cv/parse`

Parse a CV and extract structured information.

**Request:**
```json
{
  "cv_text": "John Doe\nSoftware Engineer\n..."
}
```

**Response:**
```json
{
  "candidate": {
    "personal_details": {
      "name": "John Doe",
      "email": "john.doe@example.com",
      "phone": "+1234567890",
      "location": "New York, USA"
    },
    "experience": [
      {
        "title": "Software Engineer",
        "company": "Tech Corp",
        "duration_months": 24,
        "description": "..."
      }
    ],
    "education": [
      {
        "degree": "Bachelor of Science",
        "field": "Computer Science",
        "institution": "MIT",
        "graduation_year": 2020
      }
    ],
    "skills": ["Python", "FastAPI", "Machine Learning"],
    "summary": "Experienced software engineer..."
  }
}
```

**Status Codes:**
- `200 OK` - CV parsed successfully
- `422 Unprocessable Entity` - Invalid CV format or content

**Error Response:**
```json
{
  "error": "PARSING_FAILED",
  "message": "Failed to parse CV: Invalid format",
  "details": {
    "cv_length": 1234,
    "error_type": "TextCleanerError"
  }
}
```

---

### Candidate Evaluation

#### POST `/api/v1/evaluate`

Evaluate a candidate against a job description.

**Request:**
```json
{
  "candidate": {
    "personal_details": {...},
    "experience": [...],
    "education": [...],
    "skills": [...],
    "cv_quality": {...}
  },
  "job": {
    "title": "Senior Software Engineer",
    "required_skills": ["Python", "FastAPI", "ML"],
    "required_experience_years": 3,
    "required_education": "Bachelor's degree in Computer Science",
    "salary_range": {
      "min": 80000,
      "max": 120000,
      "currency": "USD"
    }
  }
}
```

**Response:**
```json
{
  "overall_score": 87.5,
  "confidence": 0.92,
  "recommendation": "STRONG_YES",
  "match_level": "EXCELLENT_MATCH",
  "section_scores": {
    "personal_details": {
      "score": 95.0,
      "confidence": 0.95,
      "weight": 0.05,
      "weighted_score": 4.75
    },
    "experience": {
      "score": 88.0,
      "confidence": 0.90,
      "weight": 0.35,
      "weighted_score": 30.8
    },
    "education": {
      "score": 85.0,
      "confidence": 0.88,
      "weight": 0.20,
      "weighted_score": 17.0
    },
    "skills": {
      "score": 92.0,
      "confidence": 0.95,
      "weight": 0.30,
      "weighted_score": 27.6
    },
    "salary": {
      "score": 75.0,
      "confidence": 0.80,
      "weight": 0.05,
      "weighted_score": 3.75
    },
    "cv_analysis": {
      "score": 90.0,
      "confidence": 0.85,
      "weight": 0.05,
      "weighted_score": 4.5
    }
  },
  "strengths": [
    "Strong technical skills match (92%)",
    "Relevant experience in required technologies",
    "High CV quality score"
  ],
  "concerns": [
    "Salary expectations slightly above range"
  ],
  "next_steps": [
    "Schedule technical interview",
    "Verify project experience",
    "Discuss salary expectations"
  ],
  "hard_rejections": [],
  "explanation": {
    "experience": "Candidate has 5 years of relevant experience...",
    "skills": "Strong match on core skills: Python, FastAPI...",
    "education": "Bachelor's degree in Computer Science meets requirements"
  }
}
```

**Status Codes:**
- `200 OK` - Evaluation completed successfully
- `422 Unprocessable Entity` - Invalid candidate or job data
- `500 Internal Server Error` - Scoring error

**Error Response:**
```json
{
  "error": "SCORING_ERROR",
  "message": "Failed to evaluate candidate",
  "details": {
    "section": "skills",
    "error_type": "ConfigurationError"
  }
}
```

---

## Response Fields

### Recommendation Levels

- `STRONG_YES` - Excellent match, proceed immediately
- `YES` - Good match, schedule interview
- `MAYBE` - Acceptable match, requires deeper review
- `NO` - Poor match, not recommended
- `STRONG_NO` - Very poor match or hard rejection

### Match Levels

- `EXCELLENT_MATCH` - Score ≥ 90
- `GOOD_MATCH` - Score 75-89
- `FAIR_MATCH` - Score 60-74
- `POOR_MATCH` - Score 45-59
- `VERY_POOR_MATCH` - Score < 45

### Confidence Levels

- `0.9 - 1.0` - Very High Confidence
- `0.8 - 0.9` - High Confidence
- `0.7 - 0.8` - Medium Confidence
- `0.6 - 0.7` - Low Confidence
- `< 0.6` - Very Low Confidence

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `PARSING_FAILED` | 422 | CV parsing failed |
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `SCORING_ERROR` | 500 | Evaluation failed |
| `CONFIGURATION_ERROR` | 500 | System misconfigured |
| `INTERNAL_SERVER_ERROR` | 500 | Unexpected error |

---

## Rate Limits

Currently no rate limits. Production deployment may implement:
- 100 requests per minute per IP
- 1000 requests per hour per API key

---

## Best Practices

1. **CV Format**: Provide clean, well-formatted text
2. **Job Requirements**: Be specific with required skills
3. **Error Handling**: Always check HTTP status codes
4. **Retries**: Implement exponential backoff for 500 errors
5. **Validation**: Validate data before sending requests

---

## Examples

### Python Client

```python
import requests

# Parse CV
cv_text = "John Doe\nSoftware Engineer\n..."
response = requests.post(
    "http://localhost:8000/api/v1/cv/parse",
    json={"cv_text": cv_text}
)
candidate = response.json()["candidate"]

# Evaluate candidate
job = {
    "title": "Senior Software Engineer",
    "required_skills": ["Python", "FastAPI"],
    "required_experience_years": 3
}
response = requests.post(
    "http://localhost:8000/api/v1/evaluate",
    json={"candidate": candidate, "job": job}
)
result = response.json()
print(f"Score: {result['overall_score']}")
print(f"Recommendation: {result['recommendation']}")
```

### cURL

```bash
# Health check
curl http://localhost:8000/health

# Parse CV
curl -X POST http://localhost:8000/api/v1/cv/parse \
  -H "Content-Type: application/json" \
  -d '{"cv_text": "John Doe\nSoftware Engineer\n..."}'

# Evaluate candidate
curl -X POST http://localhost:8000/api/v1/evaluate \
  -H "Content-Type: application/json" \
  -d @request.json
```

---

## Interactive Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

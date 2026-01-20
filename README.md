# Logis AI Candidate Engine

Enterprise-grade AI-powered candidate ranking system for Logis Career.

## Features

- **Advanced Hybrid Scoring**: Multi-dimensional candidate evaluation
- **Confidence Metrics**: Reliability scoring for each evaluation
- **Contextual Adjustments**: Dynamic score adjustments based on context
- **Feature Interaction Detection**: Identifies synergies between candidate attributes
- **Smart Weight Optimization**: Adaptive weighting based on job requirements

## Architecture

Clean Architecture pattern with strict layer boundaries:

```
api/                 → HTTP controllers (FastAPI)
application/         → Service orchestration
core/                → Business logic & domain rules
ml/                  → ML implementation
config/              → Configuration management
```

## Installation

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Create a `.env` file (see `.env.example`):

```env
API_KEY=your-api-key-here
ENVIRONMENT=production
LOG_LEVEL=INFO
```

## Running the Service

```bash
# Development
uvicorn logis_ai_candidate_engine.api.main:app --reload

# Production
uvicorn logis_ai_candidate_engine.api.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health Checks
- `GET /health` - Liveness probe
- `GET /ready` - Readiness probe

### Evaluation
- `POST /api/v1/evaluate` - Evaluate candidate against job

### CV Parsing
- `POST /api/v1/cv/parse` - Parse CV text
- `POST /api/v1/cv/parse-to-candidate` - Convert CV to Candidate object
- `POST /api/v1/cv/extract-skills` - Extract skills only

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

```bash
pytest tests/ -v
```

## Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "logis_ai_candidate_engine.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_KEY` | No | - | API authentication key |
| `ENVIRONMENT` | No | development | Environment name |
| `LOG_LEVEL` | No | INFO | Logging level |

## License

Proprietary - Logis Career

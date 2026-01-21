# Logis AI Candidate Engine

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com/)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red)](LICENSE)

## Overview

**Logis AI Candidate Engine** is an enterprise-grade AI-powered candidate evaluation and ranking system for Logis Career. It combines advanced hybrid scoring algorithms, machine learning-based CV parsing, and semantic skill matching to provide recruiters with intelligent, explainable candidate rankings.

### Key Capabilities

-  **Multi-Dimensional Scoring**: Evaluates candidates across 6 assessment dimensions (personal details, experience, education, skills, salary, CV quality)
-  **ML-Powered CV Parsing**: Semantic section detection and entity extraction with NER pipeline
-  **Semantic Skill Matching**: Embeddings-based skill matching with synonym and semantic similarity detection
-  **Confidence Metrics**: Reliability scoring for each evaluation with detailed performance metrics
-  **Contextual Adjustments**: Dynamic score adjustments based on job requirements and industry context
-  **Industry-Specific Logic**: Specialized scoring rules for logistics, technology, finance, and healthcare sectors
-  **Feature Interaction Detection**: Identifies synergies between candidate attributes for comprehensive assessment
-  **Production-Ready**: Structured error handling, JSON logging, comprehensive exception handling

---

## Quick Start

### Prerequisites

- Python 3.11 or higher
- pip or conda
- Virtual environment (recommended)

### Installation

1. **Clone and navigate to project**:
```bash
git clone <repository-url>
cd <project-directory>
```

2. **Create virtual environment**:
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment** (optional):
```bash
cp .env.example .env
# Edit .env with your settings (defaults work for local development)
```

5. **Run the service**:
```bash
# Development (with auto-reload)
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

---

## Architecture

### Clean Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      API LAYER (FastAPI)                    │
│  ├─ Routes: /api/v1/evaluate (evaluation endpoints)         │
│  ├─ Routes: /api/v1/cv/* (CV parsing endpoints)             │
│  └─ Routes: /health, /ready (health checks)                 │
├─────────────────────────────────────────────────────────────┤
│                   APPLICATION LAYER                         │
│  ├─ EvaluationService: Orchestrates scoring workflow        │
│  ├─ CVService: Manages CV parsing and mapping               │
│  └─ BootstrapConfig: Validates configuration at startup     │
├─────────────────────────────────────────────────────────────┤
│                     CORE LAYER                              │
│  ├─ Scoring Strategies: 6 modular assessment strategies     │
│  ├─ Aggregators: Weighted score aggregation                 │
│  ├─ Rules Engine: Hard rejection logic                      │
│  └─ Schemas: Pydantic data models for type safety           │
├─────────────────────────────────────────────────────────────┤
│                      ML LAYER                               │
│  ├─ CV Parser: Pipeline-based parsing system                │
│  ├─ Embedding Model: Semantic similarity with transformers  │
│  ├─ Skill Matcher: Taxonomy-based skill matching            │
│  └─ Parser Stages: TextCleaner, SectionSegmenter, etc.      │
├─────────────────────────────────────────────────────────────┤
│                  CONFIGURATION LAYER                        │
│  ├─ thresholds.yaml: Scoring weights & industry rules       │
│  ├─ scoring_config.py: Configuration loader (fail-fast)     │
│  └─ Environment: .env for runtime settings                  │
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
project-root/                     # Service root (no wrapper package)
├── api/                          # HTTP delivery layer
│   ├── routes/                   # API endpoints
│   │   ├── evaluation.py         # Candidate evaluation
│   │   ├── cv.py                 # CV parsing
│   │   └── health.py             # Health checks
│   └── main.py                   # FastAPI app configuration
│
├── application/                  # Service orchestration
│   ├── evaluation_service.py     # Evaluation business logic
│   ├── cv_service.py             # CV processing business logic
│   ├── bootstrap.py              # App initialization
│   ├── dependencies.py           # Dependency injection
│   ├── exceptions.py             # Custom exception types
│   └── logging_config.py         # Structured logging setup
│
├── core/                         # Domain business logic
│   ├── scoring/                  # Scoring algorithms
│   │   ├── strategies/           # Strategy pattern implementation
│   │   ├── comprehensive_scorer.py
│   │   ├── advanced_scorer.py
│   │   └── models.py             # Scoring data models
│   ├── rules/                    # Evaluation rules
│   │   └── hard_rejection_engine.py
│   ├── schemas/                  # Data models (Pydantic)
│   │   ├── candidate.py
│   │   ├── job.py
│   │   └── evaluation_response.py
│   ├── aggregation/              # Score aggregation
│   ├── explainability/           # Score explanations
│   └── enhancement/              # Score enhancement
│
├── ml/                           # Machine learning
│   ├── parser/                   # CV parsing pipeline
│   │   ├── pipeline.py           # Pipeline abstraction
│   │   ├── text_cleaner.py       # Text normalization
│   │   ├── section_segmenter.py  # Section detection
│   │   ├── entity_extractor.py   # Named entity extraction
│   │   ├── patterns.py           # Regex patterns (centralized)
│   │   └── *_extractor.py        # Specialized extractors
│   ├── cv_parser.py              # Main CV parser
│   ├── cv_candidate_mapper.py    # CV → Candidate mapping
│   ├── embedding_model.py        # Semantic embeddings
│   ├── semantic_similarity.py    # Similarity scoring
│   └── skill_matcher.py          # Skill taxonomy matching
│
├── config/                       # Configuration
│   ├── thresholds.yaml           # Scoring configuration
│   ├── scoring_config.py         # Config loader (fail-fast)
│   ├── env.py                    # Environment variables
│   ├── settings.py               # Application settings
│   └── skills_taxonomy.yaml      # Skill definitions
│
├── utils/                        # Shared utilities
│   └── cv_parser_utils.py        # Helper functions
│
├── data/                         # Data and samples
│   └── golden_cvs/               # Regression test datasets
│
├── main.py                       # Application entry point
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
├── .gitignore                    # Git exclusion rules
└── README.md                     # This file
```

**Note on Testing**: Comprehensive test suites were used during development for validation. Tests may be maintained separately in CI/CD pipelines rather than bundled with the production deployment.

---

## API Documentation

### Automatic Documentation

Once the service is running, interactive API documentation is available:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Core Endpoints

#### Health Checks
```
GET /health         → Liveness probe (service running?)
GET /ready          → Readiness probe (ready to serve?)
```

#### Candidate Evaluation
```
POST /api/v1/evaluate
  Request: { candidate: CandidateInput, job: JobInput }
  Response: { score: 0-100, confidence: 0-1, recommendations: [...] }
```

#### CV Parsing
```
POST /api/v1/cv/parse
  Request: { cv_text: string }
  Response: { sections: {...}, entities: {...}, parsed_cv: {...} }

POST /api/v1/cv/parse-to-candidate
  Request: { cv_text: string }
  Response: { candidate: CandidateSchema }

POST /api/v1/cv/extract-skills
  Request: { cv_text: string }
  Response: { skills: [...], confidence_scores: [...] }
```

See API docs (Swagger/ReDoc) for detailed request/response schemas.

---

## Configuration

### Environment Variables

Create a `.env` file (template: `.env.example`):

```env
# Server
API_KEY=your-secret-key-here
ENVIRONMENT=production
LOG_LEVEL=INFO

# Database (if applicable)
DATABASE_URL=postgresql://user:password@localhost/db

# ML Models
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Scoring Configuration

All scoring logic is configured in `config/thresholds.yaml` (single source of truth):

```yaml
comprehensive_scoring:
  section_weights:
    personal_details: 0.10
    experience: 0.25
    education: 0.15
    skills: 0.25
    salary: 0.10
    cv_analysis: 0.15
  
  skill_importance_weights:
    required: 2.0
    preferred: 1.0
    nice_to_have: 0.5
  
  industry_adjustments:
    logistics:
      gcc_experience_multiplier: 1.3
      transport_certifications_bonus: 15
    technology:
      recent_skills_multiplier: 1.4
      github_profile_bonus: 5
```

**IMPORTANT**: Configuration is validated at application startup. Invalid or missing configuration will cause the service to **fail-fast** with a clear error message.

---

## Deployment

### Docker

Build and run with Docker:

```bash
# Build image
docker build -t logis-ai-engine:latest .

# Run container
docker run -d \
  --name logis-ai-engine \
  -p 8000:8000 \
  -e API_KEY=your-key \
  -e ENVIRONMENT=production \
  --restart unless-stopped \
  logis-ai-engine:latest

# Check logs
docker logs -f logis-ai-engine
```

### Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Production Server

For production deployments:

```bash
# Using Gunicorn + Uvicorn (recommended)
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000

# Or using Uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Kubernetes

See [DEPLOYMENT.md](DEPLOYMENT.md) for Kubernetes deployment instructions.

---

## Error Handling & Logging

### Exception Types

The service uses typed exceptions for clear error semantics:

- **ParsingError**: CV parsing failures (HTTP 422)
- **ScoringError**: Evaluation failures (HTTP 500)
- **ValidationError**: Invalid input (HTTP 422)
- **ConfigurationError**: Invalid configuration (HTTP 500, app won't start)

### Structured Logging

All logs are structured JSON in production:

```json
{
  "timestamp": "2026-01-21T12:00:00.000Z",
  "level": "ERROR",
  "service": "logis-ai-candidate-engine",
  "logger": "api.routes.evaluation",
  "message": "Evaluation failed",
  "request_id": "req-abc123",
  "error_type": "ScoringError",
  "details": {"reason": "missing_experience"}
}
```

---

## Development

### Code Style

- **Language**: Python 3.11+
- **Type Hints**: All functions have type annotations
- **Docstrings**: All modules, classes, functions documented
- **Linting**: Follows PEP 8

### Architecture Principles

1. **Clean Architecture**: Strict layer separation (API → App → Core → ML)
2. **Dependency Inversion**: Depend on abstractions, not concrete implementations
3. **Single Responsibility**: Each module has one reason to change
4. **Fail-Fast**: Configuration validated at startup
5. **Explicit is Better than Implicit**: No magic, clear intent

### Key Design Patterns

- **Strategy Pattern**: Scoring strategies (PersonalDetailsStrategy, ExperienceStrategy, etc.)
- **Pipeline Pattern**: CV parsing stages (TextCleaner → SectionSegmenter → etc.)
- **Dependency Injection**: Services injected via FastAPI
- **Repository Pattern**: Service layers abstract data access

---

## Performance

### Benchmarks

On 4-core server with 8GB RAM:

- **CV Parsing**: ~500ms (including embeddings)
- **Candidate Evaluation**: ~200ms (includes all scoring)
- **Throughput**: ~15 requests/sec per worker

### Optimization Tips

1. **Increase Workers**: `--workers 4` for 4-core systems
2. **Caching**: Configure Redis for ML model caching
3. **Load Balancing**: Use Nginx or AWS ALB
4. **Monitoring**: Track latency with structured logs

---

## Troubleshooting

### Service Won't Start

**Error**: `ConfigurationError: Invalid scoring configuration`

**Solution**: Validate `config/thresholds.yaml` exists and is valid YAML

```bash
python -c "from config.scoring_config import scoring_config; print('Config valid')"
```

### High Latency

**Cause**: ML model loading/embeddings computation

**Solution**: 
- Pre-warm embeddings in background
- Use caching layer
- Increase worker processes

### Memory Issues

**Cause**: Large CV files or many concurrent requests

**Solution**:
- Limit CV size (request validation)
- Implement request queuing
- Increase server memory

---

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -m "Add my feature"`
4. Push to branch: `git push origin feature/my-feature`
5. Submit pull request

### Code Review Requirements

- All type hints present
- All functions documented
- All tests passing (if added)
- No hardcoded values (use config)

---

## License

Proprietary - Logis Career

**All rights reserved.** Unauthorized copying or distribution prohibited.

---

## Support

For issues, questions, or feature requests:

- **Email**: support@logiscareer.com
- **Slack**: #logis-ai-engine
- **Issues**: [GitLab Issues](https://gitlab.logiscareer.com/logis-ai/candidate-engine/issues)

---

## Changelog

### v3.0.0

- ✅ Production-ready architecture
- ✅ Strategy pattern for scoring
- ✅ Pipeline-based CV parsing
- ✅ Centralized configuration (thresholds.yaml)
- ✅ Structured error handling & logging
- ✅ Clean imports (no wrapper packages)

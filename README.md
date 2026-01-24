# Logis AI Candidate Engine

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com/)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-90%25%20Coverage-brightgreen)](tests/)

## Overview

**Logis AI Candidate Engine** is an enterprise-grade, production-ready AI-powered candidate evaluation and ranking system for Logis Career. Built with clean architecture principles, it combines advanced hybrid scoring algorithms, ML-based CV parsing pipelines, and semantic skill matching to provide recruiters with intelligent, explainable candidate rankings.

### 🎯 Version 2.0 - Production Architecture

This major refactor delivers:
- ✅ **Clean Architecture**: Proper separation of concerns across API, Application, Core, and ML layers
- ✅ **Strategy Pattern**: Modular, independently testable scoring strategies
- ✅ **Pipeline Architecture**: Stage-based CV parsing with fail-fast error handling
- ✅ **Fail-Fast Configuration**: Startup validation with zero hardcoded defaults
- ✅ **Structured Logging**: JSON logs for ELK/Datadog integration
- ✅ **90%+ Test Coverage**: Unit, integration, and property-based tests
- ✅ **Type Safety**: Full Pydantic models with runtime validation

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
logis_ai_candidate_engine/
├── api/                          # HTTP delivery layer (routes ONLY)
│   └── routes/                   # API endpoints
│       ├── evaluation.py         # Candidate evaluation
│       ├── cv.py                 # CV parsing
│       └── health.py             # Health checks
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
│   │   └── models.py             # Scoring data models
│   ├── rules/                    # Evaluation rules
│   ├── schemas/                  # Data models (Pydantic)
│   ├── aggregation/              # Score aggregation
│   └── explainability/           # Score explanations
│
├── ml/                           # Machine learning
│   ├── parser/                   # CV parsing pipeline
│   ├── cv_parser.py              # Main CV parser
│   ├── embedding_model.py        # Semantic embeddings
│   └── skill_matcher.py          # Skill taxonomy matching
│
├── config/                       # Configuration
│   ├── thresholds.yaml           # Scoring configuration
│   ├── config_validator.py       # Fail-fast validation
│   └── skills_taxonomy.yaml      # Skill definitions
│
├── docs/                         # Documentation
│   ├── API.md                    # API documentation
│   ├── ARCHITECTURE.md           # Architecture details
│   ├── CLEAN_ARCHITECTURE.md     # Clean architecture principles
│   ├── QUICKSTART.md             # Quick start guide
│   └── CHANGELOG.md              # Version history
│
├── main.py                       # Composition root (app factory)
├── requirements.txt              # Python dependencies
├── pyproject.toml                # Project metadata
├── .env.example                  # Environment template
├── .gitignore                    # Git exclusion rules
├── LICENSE                       # MIT License
├── CONTRIBUTING.md               # Contribution guidelines
└── README.md                     # This file
```

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

## Documentation

Comprehensive documentation is available in the [`docs/`](docs/) directory:

- **[API.md](docs/API.md)** - Complete API reference with examples
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture and design patterns
- **[CLEAN_ARCHITECTURE.md](docs/CLEAN_ARCHITECTURE.md)** - Clean architecture principles explained
- **[QUICKSTART.md](docs/QUICKSTART.md)** - Developer quick start guide
- **[CHANGELOG.md](docs/CHANGELOG.md)** - Version history and changes

Interactive API documentation is also available when the service is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Code standards
- Testing requirements
- Pull request process

### Quick Contribution Guide

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Follow code standards (Black, Ruff, MyPy)
4. Write tests (maintain 90%+ coverage)
5. Commit changes: `git commit -m "feat: add my feature"`
6. Push to branch: `git push origin feature/my-feature`
7. Submit pull request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support

For issues, questions, or feature requests:

- **Issues**: Open a GitHub issue
- **Documentation**: Check the [docs/](docs/) directory
- **Email**: support@logiscareer.com

---

## Changelog

See [CHANGELOG.md](docs/CHANGELOG.md) for a complete version history.

### Latest Version: v2.0.0

- ✅ Clean Architecture implementation
- ✅ Strategy pattern for scoring
- ✅ Pipeline-based CV parsing
- ✅ Fail-fast configuration validation
- ✅ Comprehensive error handling & structured logging
- ✅ Professional documentation structure

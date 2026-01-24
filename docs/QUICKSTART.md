# Quick Start Guide - Version 2.0

## Installation

```bash
# 1. Navigate to project directory
cd c:\Users\sdshy\logis_ml_engine\logis_ai_candidate_engine

# 2. Activate virtual environment (if not already active)
.venv\Scripts\activate

# 3. Install project with dev dependencies
pip install -e ".[dev]"

# Or just install without dev tools
pip install -r requirements.txt
```

## Verify Installation

```bash
# Check configuration validation (should print success message)
python -c "from config.config_validator import get_thresholds_config; print('✓ Configuration valid')"

# Check imports work
python -c "from main import app; print('✓ API imports work')"

# Check tests can be discovered
pytest --collect-only
```

## Run Tests

```bash
# Run all tests with coverage
pytest --cov=. --cov-report=term-missing

# Run only fast unit tests
pytest tests/unit/ -v

# Run property-based tests
pytest tests/property/ -v --hypothesis-show-statistics

# Run golden CV regression tests
pytest tests/integration/test_golden_cvs.py -v

# Run specific test
pytest tests/unit/scoring/test_skills_strategy.py::TestSkillsScoringStrategy::test_perfect_required_skills_match -v
```

## Run the API

```bash
# Development mode (auto-reload)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or use the main.py script directly
python main.py

# Production mode (4 workers)
uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000
```

## Access the API

- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Test API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Parse CV
curl -X POST http://localhost:8000/cv/parse \
  -H "Content-Type: application/json" \
  -d '{
    "cv_text": "John Doe\njohn@email.com\n+971 50 123 4567\n\nEXPERIENCE\nSenior Developer at Tech Corp\n2020-Present\n\nSKILLS\nPython, SQL, AWS, Docker"
  }'

# Evaluate candidate
curl -X POST http://localhost:8000/evaluation/evaluate \
  -H "Content-Type: application/json" \
  -d @examples/sample_evaluation_request.json
```

## Code Quality Checks

```bash
# Format code with Black
black .

# Lint with Ruff
ruff check .
ruff check . --fix  # Auto-fix issues

# Type check with MyPy
mypy .
```

## Common Tasks

### Add a New Scoring Strategy

1. Create file: `core/scoring/strategies/my_strategy.py`
```python
from core.scoring.strategies.base import ScoringStrategy, ScoringContext
from core.scoring.models import SectionAssessment

class MyStrategy(ScoringStrategy):
    def score(self, context: ScoringContext) -> SectionAssessment:
        # Implement scoring logic
        pass
```

2. Register in `ComprehensiveScorer`:
```python
self._strategies = {
    # ... existing strategies
    'my_section': MyStrategy(),
}
```

3. Add config to `config/thresholds.yaml`
4. Write unit test in `tests/unit/scoring/test_my_strategy.py`

### Add a New Parser Stage

1. Create file: `ml/parser/my_stage.py`
```python
class MyStageError(Exception):
    pass

class MyStage:
    def process(self, data):
        # Implement stage logic
        pass
```

2. Add to pipeline in `ml/parser/cv_pipeline.py`
3. Write unit test in `tests/unit/parser/test_my_stage.py`

### Update Configuration

1. Edit `config/thresholds.yaml`
2. Restart application (fail-fast validation will catch errors)
3. If app starts successfully, config is valid

## Troubleshooting

### Configuration Error on Startup
```
CRITICAL: CONFIGURATION ERROR
Missing 'comprehensive_scoring' section in thresholds.yaml
```
**Solution**: Check `config/thresholds.yaml` syntax and required keys

### Import Errors
```
ModuleNotFoundError: No module named 'core'
```
**Solution**: Run from project root and ensure virtual environment is activated

### Test Failures
```
AssertionError: Total score 105 is outside valid range [0, 100]
```
**Solution**: Check scoring logic in strategy, verify config values

### API Won't Start
```
ConfigurationError: Application cannot start without thresholds.yaml
```
**Solution**: Ensure `config/thresholds.yaml` exists and is valid

## Environment Variables (Optional)

Create `.env` file:
```bash
# Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Optional
API_KEY=your-secret-key
MODEL_CACHE_DIR=/path/to/cache
```

## Project Structure Quick Reference

```
.
├── api/                    # FastAPI routes (NO business logic)
│   ├── app.py             # FastAPI app factory
│   ├── routes/
│   │   ├── cv.py          # CV parsing endpoints
│   │   ├── evaluation.py  # Evaluation endpoints
│   │   └── health.py      # Health checks
│   └── dependencies.py    # Dependency injection
│
├── application/           # Business services
│   ├── cv_service.py     # CV parsing service
│   ├── evaluation_service.py  # Evaluation service
│   ├── exceptions.py     # Domain exceptions
│   └── logging_config.py # Structured logging
│
├── core/                  # Domain logic
│   ├── scoring/
│   │   ├── strategies/   # Scoring strategies
│   │   ├── comprehensive_scorer.py  # Orchestrator
│   │   └── models.py     # Data models
│   └── ...
│
├── ml/                    # ML components
│   ├── parser/           # CV parser pipeline
│   │   ├── text_cleaner.py
│   │   ├── section_segmenter.py
│   │   └── patterns.py   # Regex patterns
│   └── cv_parser.py      # Main parser
│
├── config/               # Configuration
│   ├── thresholds.yaml  # Scoring config (SINGLE SOURCE OF TRUTH)
│   ├── config_validator.py  # Fail-fast validation
│   └── ...
│
├── tests/                # Test suite
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── property/        # Property-based tests
│
├── main.py              # Entry point (NO business logic)
└── pyproject.toml       # Project metadata + tool config
```

## Getting Help

- **Architecture**: See `ARCHITECTURE.md`
- **Changes**: See `CHANGELOG.md`
- **Summary**: See `REFACTORING_SUMMARY.md`
- **API Docs**: http://localhost:8000/docs (when server running)

## Success Checklist

Before committing/deploying:

- [ ] Tests pass: `pytest --cov=. --cov-fail-under=90`
- [ ] Code formatted: `black .`
- [ ] Linting clean: `ruff k .`
- [ ] Config valid: Configuration loads without errors
- [ ] API starts: `uvicorn api.main:app` runs successfully
- [ ] Health check works: `curl http://localhost:8000/health`

---

**You're all set! 🚀**

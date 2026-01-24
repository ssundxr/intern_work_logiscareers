# Architecture Documentation

## Overview

Logis AI Candidate Engine is a production-grade FastAPI + ML system for CV parsing and candidate scoring. This document describes the clean architecture implementation after the comprehensive refactoring.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│         main.py (Composition Root - Above All Layers)        │
│  - App factory (create_app)                                  │
│  - Exception handlers                                        │
│  - Lifecycle hooks (startup/shutdown)                        │
│  - Route registration                                        │
│  - ASGI server entry point (uvicorn/gunicorn)               │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│               API Layer (api/routes/ ONLY)                   │
│  - REST endpoints (NO business logic, NO app factory)        │
│  - Request/Response serialization                            │
│  - HTTP-specific concerns ONLY                               │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│              Application Layer                               │
│  - Business services (CVService, EvaluationService)          │
│  - Dependency injection                                      │
│  - Bootstrap configuration                                   │
│  - Domain exceptions                                         │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                  Core Domain Layer                           │
│  - Scoring strategies (Strategy Pattern)                     │
│  - Domain models (Pydantic)                                  │
│  - Business rules                                            │
│  - Aggregation logic                                         │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│          ML & Infrastructure Layer                           │
│  - CV Parser (Pipeline Architecture)                         │
│  - Embedding models                                          │
│  - Semantic similarity                                       │
│  - Skill matching                                            │
└─────────────────────────────────────────────────────────────┘
```

## Clean Architecture Principles

### Composition Root (main.py)

**Location**: Project root  
**Responsibility**: Wiring the application together

The composition root sits **above all layers** and is responsible for:
- Creating the FastAPI app instance
- Registering exception handlers
- Attaching lifecycle hooks (startup/shutdown)
- Configuring middleware and CORS
- Registering routes from the api/ layer

**Key Principle**: Composition logic does not belong to any single layer. The api/ folder contains ONLY routes - no app factory, no handlers, no lifecycle events.

### Why Composition Root is at Project Root

1. **Architectural Responsibility**: Composition transcends individual layers
2. **Dependency Direction**: API layer depends inward, should not own application lifecycle
3. **Operational Clarity**: DevOps/CI/CD expects `uvicorn main:app` (standard pattern)
4. **Testability**: Tests import from composition root, not from a delivery mechanism
5. **Future Interfaces**: CLI, workers, gRPC can reuse the same composition root pattern

### API Layer Responsibility

The `api/` folder contains **ONLY routes**:
- HTTP request handlers
- Request/response serialization  
- Delegating to application services

**What should NOT be in api/**:
- App factory (belongs in composition root)
- Exception handlers (belongs in composition root)
- Lifecycle hooks (belongs in composition root)
- Business logic (belongs in application/core layers)

## Key Design Patterns

### 1. Strategy Pattern (Scoring)

**Location**: `core/scoring/strategies/`

Each scoring strategy implements a single responsibility:

```python
class ScoringStrategy(ABC):
    @abstractmethod
    def score(self, context: ScoringContext) -> SectionAssessment:
        pass

# Concrete strategies:
- PersonalDetailsScoringStrategy
- ExperienceScoringStrategy  
- EducationScoringStrategy
- SkillsScoringStrategy
- SalaryScoringStrategy
- CVAnalysisScoringStrategy
```

**Benefits**:
- Single Responsibility Principle
- Open/Closed Principle (add new strategies without modifying existing code)
- Independently testable
- Configuration-driven (all thresholds from YAML)

### 2. Pipeline Pattern (CV Parsing)

**Location**: `ml/parser/`

CV parsing is decomposed into sequential stages:

```
TextCleaner → SectionSegmenter → EntityExtractor → SkillNormalizer
```

Each stage:
- Has a `process()` method
- Raises stage-specific errors
- Is independently testable
- Can be replaced/enhanced without affecting other stages

**Benefits**:
- Separation of concerns
- Easier debugging (know which stage failed)
- Extensible (add new stages easily)
- Testable (mock individual stages)

### 3. Dependency Injection

**Location**: `application/dependencies.py`

Services are injected via FastAPI's dependency system:

```python
@router.post("/evaluate")
def evaluate(
    request: Request,
    service: EvaluationService = Depends(get_evaluation_service)
):
    return service.evaluate(...)
```

**Benefits**:
- Loose coupling
- Easy mocking for tests
- Clear dependencies
- Singleton management

## Configuration Management

### Fail-Fast Validation

**Location**: `config/config_validator.py`

All configuration is validated at startup:

```python
# Application fails immediately if config is invalid
try:
    CONFIG = get_thresholds_config()
except ConfigurationError as e:
    print("CRITICAL: Configuration Error")
    raise
```

**No hardcoded defaults** in scoring logic. All values come from:
- `config/thresholds.yaml` - Scoring weights, thresholds, industry adjustments
- `config/skills_taxonomy.yaml` - Skill normalization rules

### Configuration Models

Type-safe configuration using Pydantic:

```python
class SectionWeightsConfig(BaseModel):
    personal_details: float = Field(..., ge=0.0, le=1.0)
    experience: float = Field(..., ge=0.0, le=1.0)
    # ... must sum to 1.0
```

## Error Handling

### Exception Hierarchy

```
ApplicationError (base)
├── ParsingError (CV parsing failures)
├── ScoringError (Scoring/evaluation failures)  
├── ConfigurationError (Config issues)
└── ValidationError (Input validation)
```

### API Error Mapping

```
ParsingError       → HTTP 422 Unprocessable Entity
ValidationError    → HTTP 422 Unprocessable Entity
ScoringError       → HTTP 500 Internal Server Error
ConfigurationError → HTTP 500 Internal Server Error (startup)
```

### Structured Error Responses

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

## Logging

### Structured JSON Logging

**Location**: `application/logging_config.py`

Production logs are JSON-formatted for ELK/Datadog:

```json
{
  "timestamp": "2026-01-24T12:00:00.000Z",
  "level": "INFO",
  "service": "logis_ai_candidate_engine",
  "logger": "api.routes.evaluation",
  "message": "Evaluating candidate",
  "request_id": "abc123",
  "candidate_id": "12345"
}
```

Development logs are human-readable with colors.

## Testing Strategy

### Test Types

1. **Unit Tests** (`tests/unit/`)
   - Test individual strategies in isolation
   - Mock dependencies
   - Fast execution
   - Target: 90%+ coverage

2. **Integration Tests** (`tests/integration/`)
   - Test full workflows
   - Golden CV regression tests
   - Real dependencies

3. **Property-Based Tests** (`tests/property/`)
   - Use Hypothesis to generate random inputs
   - Verify invariants (e.g., scores always 0-100)
   - Catch edge cases

### Golden CV Dataset

**Location**: `data/golden_cvs/`

Known-good CVs with expected extraction results:
- `golden_cv_1_logistics_manager.txt`
- `golden_cv_2_software_engineer.txt`
- `golden_cv_3_data_scientist.txt`

Tests ensure parser doesn't regress on real-world CVs.

## Running Tests

```bash
# Install test dependencies
pip install -e ".[test]"

# Run all tests with coverage
pytest --cov=. --cov-report=html

# Run only unit tests
pytest tests/unit/ -v

# Run property-based tests
pytest tests/property/ -v --hypothesis-show-statistics

# Run specific test file
pytest tests/unit/scoring/test_skills_strategy.py -v
```

## Deployment

### Production Checklist

- [x] Configuration validated at startup (fail-fast)
- [x] Structured JSON logging enabled
- [x] Exception handlers registered
- [x] No hardcoded scoring values
- [x] 90%+ test coverage
- [x] Property-based tests for invariants
- [x] Golden CV regression tests

### Environment Variables

```bash
# Optional - defaults shown
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false
```

### Running the Server

```bash
# Development
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production (multi-worker)
uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000

# Alternative: Gunicorn with Uvicorn workers
gunicorn main:app -k uvicorn.workers.UvicornWorker --workers 4
```

## Code Quality Tools

Configuration in `pyproject.toml`:

- **Black**: Code formatting (100 char line length)
- **Ruff**: Fast linting (replaces flake8, isort)
- **MyPy**: Static type checking
- **Pytest**: Testing with coverage

```bash
# Format code
black .

# Lint code
ruff check .

# Type check
mypy .
```

## Performance Considerations

### Caching

- Embedding models are loaded once at startup
- Skill taxonomy loaded once from YAML
- Configuration validated once at startup

### Optimization Points

1. **CV Parsing Pipeline**
   - Each stage can be optimized independently
   - Parallelizable for batch processing

2. **Scoring Strategies**
   - Independent strategies can run in parallel
   - Config-driven (no runtime computation)

3. **Skill Matching**
   - Uses pre-computed embeddings
   - Taxonomy-based normalization reduces API calls

## Adding New Features

### Adding a New Scoring Strategy

1. Create strategy class in `core/scoring/strategies/`
2. Implement `ScoringStrategy` interface
3. Add configuration to `thresholds.yaml`
4. Register in `ComprehensiveScorer._strategies`
5. Write unit tests
6. Write property-based tests

### Adding a New CV Parser Stage

1. Create stage class in `ml/parser/`
2. Implement `process()` method
3. Define stage-specific errors
4. Add to pipeline in `cv_parser.py`
5. Write unit tests
6. Add to golden CV regression tests

## Troubleshooting

### Configuration Errors

If application fails at startup with configuration error:
1. Check `config/thresholds.yaml` syntax (valid YAML)
2. Ensure section weights sum to 1.0
3. Verify all required keys are present
4. Check value ranges (e.g., weights 0.0-1.0)

### Test Failures

```bash
# Get detailed output
pytest -vv --tb=long

# Run specific failing test
pytest tests/unit/scoring/test_skills_strategy.py::TestSkillsScoringStrategy::test_perfect_match -vv

# Show print statements
pytest -s
```

### Import Errors

Ensure you're running from project root:
```bash
cd c:\Users\sdshy\logis_ml_engine\logis_ai_candidate_engine
python -m pytest tests/
```

## Maintainer Notes

### Critical Files

- `main.py` - Composition root (app factory, handlers, lifecycle - AT PROJECT ROOT)
- `api/routes/` - HTTP endpoints ONLY (no app factory, no handlers)
- `config/thresholds.yaml` - Single source of truth for scoring
- `config/config_validator.py` - Fail-fast validation
- `core/scoring/comprehensive_scorer.py` - Strategy orchestrator
- `ml/parser/cv_pipeline.py` - Parser pipeline orchestrator

### Architecture Rules

1. **api/ contains ONLY routes** - no app factory, no exception handlers, no lifecycle
2. **Composition root is main.py at project root** - wires all layers together
3. **Dependency direction is always inward** - outer layers depend on inner layers
4. **Business logic belongs in application/core** - never in api/ or main.py

### Before Pushing Changes

```bash
# 1. Format code
black .

# 2. Lint
ruff check . --fix

# 3. Type check
mypy .

# 4. Run tests
pytest --cov=. --cov-report=term --cov-fail-under=90

# 5. Check golden CVs
pytest tests/integration/test_golden_cvs.py -v
```

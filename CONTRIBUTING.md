# Contributing to Logis AI Candidate Engine

Thank you for your interest in contributing to the Logis AI Candidate Engine! This document provides guidelines for contributing to this project.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd logis_ai_candidate_engine
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify setup**
   ```bash
   python -c "from main import app; print('Setup successful!')"
   ```

## Code Standards

### Architecture Principles

This project follows **Clean Architecture** principles:

1. **api/** - Delivery layer (HTTP routes ONLY)
2. **application/** - Application services and use cases
3. **core/** - Domain logic and business rules
4. **ml/** - Infrastructure (ML models, parsers)
5. **main.py** - Composition root (wiring, not business logic)

**Critical Rules:**
- Dependencies flow inward: api → application → core
- No business logic in api/ or main.py
- All configuration in config/ (fail-fast validation)

### Code Style

We use automated formatters and linters:

```bash
# Format code (100 char line length)
black .

# Lint code
ruff check .

# Type check
mypy .

# Run all quality checks
black . && ruff check . && mypy .
```

**Required:**
- All code must pass Black formatting
- All code must pass Ruff linting (no warnings)
- Type hints required for all functions
- Docstrings required for all public APIs

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=term --cov-report=html

# Run specific test file
pytest tests/unit/scoring/test_skills_strategy.py

# Run with verbose output
pytest -vv
```

### Test Requirements

- **Minimum coverage:** 90%
- **Test types required:**
  - Unit tests for all strategies
  - Integration tests for golden CVs
  - Property-based tests for invariants (Hypothesis)

### Writing Tests

```python
# Unit test example
def test_skills_scoring_perfect_match():
    """Test skills scoring with perfect match"""
    strategy = SkillsScoringStrategy()
    context = create_test_context(
        candidate_skills=["Python", "FastAPI", "ML"],
        job_skills=["Python", "FastAPI", "ML"]
    )
    result = strategy.score(context)
    assert result.score >= 95
    assert result.confidence > 0.8

# Property-based test example
@given(st.integers(min_value=0, max_value=100))
def test_score_always_in_range(score):
    """Score must always be between 0 and 100"""
    normalized = normalize_score(score)
    assert 0 <= normalized <= 100
```

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow code standards
   - Write tests (maintain 90%+ coverage)
   - Update documentation

3. **Run quality checks**
   ```bash
   black .
   ruff check .
   mypy .
   pytest --cov=. --cov-fail-under=90
   ```

4. **Commit with clear messages**
   ```bash
   git commit -m "feat: add new scoring strategy for certifications"
   ```

   Commit message format:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation only
   - `refactor:` - Code refactoring
   - `test:` - Adding tests
   - `chore:` - Maintenance tasks

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **PR Requirements**
   - Clear description of changes
   - All tests pass
   - Coverage maintained at 90%+
   - Documentation updated
   - No merge conflicts

## Adding New Features

### Adding a New Scoring Strategy

1. Create strategy class in `core/scoring/strategies/`
   ```python
   from core.scoring.strategies.base import ScoringStrategy
   
   class MyNewStrategy(ScoringStrategy):
       def score(self, context: ScoringContext) -> SectionAssessment:
           # Implementation
           pass
   ```

2. Add configuration to `config/thresholds.yaml`
3. Register in `core/scoring/comprehensive_scorer.py`
4. Write unit tests in `tests/unit/scoring/`
5. Write property-based tests in `tests/property/`
6. Update documentation

### Adding a New API Endpoint

1. Create route in `api/routes/`
   ```python
   from fastapi import APIRouter
   
   router = APIRouter()
   
   @router.post("/endpoint")
   async def my_endpoint():
       # Delegate to application service
       pass
   ```

2. Register in `main.py` (composition root)
3. Write integration tests
4. Update API documentation

### Adding a New Parser Stage

1. Create stage in `ml/parser/`
2. Implement `process()` method
3. Add to pipeline in `ml/parser/cv_pipeline.py`
4. Write unit tests
5. Add to golden CV regression tests

## Documentation

- Update README.md for user-facing changes
- Update ARCHITECTURE.md for architectural changes
- Update QUICKSTART.md for setup/deployment changes
- Add inline docstrings (Google style)

## Code Review

All PRs require:
- At least one approval
- All CI checks passing
- No merge conflicts
- Updated documentation

## Questions?

- Open an issue for bugs
- Open a discussion for feature requests
- Tag maintainers for urgent issues

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

# Unit tests for rule-based rejection engine
 
from logis_ai_candidate_engine.core.rules.hard_rejection_engine import HardRejectionEngine
from logis_ai_candidate_engine.core.schemas.candidate import Candidate
from logis_ai_candidate_engine.core.schemas.job import Job


def _copy_model(model, update: dict):
    model_copy = getattr(model, "model_copy", None)
    if callable(model_copy):
        return model_copy(update=update)
    return model.copy(update=update)


def _base_job() -> Job:
    return Job(
        job_id="job-1",
        country="UAE",
        state=None,
        city=None,
        title="ML Engineer",
        industry="Logistics",
        sub_industry=None,
        functional_area="Engineering",
        designation="Engineer",
        min_experience_years=3,
        max_experience_years=8,
        salary_min=10000,
        salary_max=20000,
        currency="AED",
        required_skills=["python", "ml"],
        keywords=[],
        job_description="python machine learning engineer",
        desired_candidate_profile=None,
    )


def _base_candidate() -> Candidate:
    return Candidate(
        candidate_id="cand-1",
        current_country="UAE",
        availability_to_join_days=None,
        expected_salary=15000,
        currency="AED",
        total_experience_years=5.0,
        education_level="Bachelors",
        skills=["python", "ml"],
        employment_summary="Worked as ML engineer in logistics",
        cv_text="python machine learning engineer",
    )


def test_location_mismatch_rejects() -> None:
    job = _base_job()
    candidate = _copy_model(_base_candidate(), {"current_country": "India"})

    result = HardRejectionEngine.evaluate(job, candidate)

    assert result.is_eligible is False
    assert result.rejection_reason is not None
    assert "LOCATION_MISMATCH" in result.rule_trace


def test_salary_exceeds_max_rejects() -> None:
    job = _base_job()
    candidate = _copy_model(_base_candidate(), {"expected_salary": 999999})

    result = HardRejectionEngine.evaluate(job, candidate)

    assert result.is_eligible is False
    assert "SALARY_EXCEEDS_MAX" in result.rule_trace


def test_insufficient_experience_rejects() -> None:
    job = _copy_model(_base_job(), {"min_experience_years": 6})
    candidate = _copy_model(_base_candidate(), {"total_experience_years": 2.0})

    result = HardRejectionEngine.evaluate(job, candidate)

    assert result.is_eligible is False
    assert "INSUFFICIENT_EXPERIENCE" in result.rule_trace


def test_passes_all_hard_rules() -> None:
    job = _base_job()
    candidate = _base_candidate()

    result = HardRejectionEngine.evaluate(job, candidate)

    assert result.is_eligible is True
    assert result.rejection_reason is None
    assert "PASSED_ALL_HARD_RULES" in result.rule_trace
# API integration tests for candidate evaluation endpoints
 
from fastapi.testclient import TestClient
 
from logis_ai_candidate_engine.api.main import app
from logis_ai_candidate_engine.ml.semantic_similarity import (
    SemanticSimilarityResult,
    SemanticSimilarityScorer,
)
 
client = TestClient(app)
 
 
def _job_payload() -> dict:
    return {
        "job_id": "job-1",
        "country": "UAE",
        "state": None,
        "city": None,
        "title": "ML Engineer",
        "industry": "Logistics",
        "sub_industry": None,
        "functional_area": "Engineering",
        "designation": "Engineer",
        "min_experience_years": 3,
        "max_experience_years": 8,
        "salary_min": 10000,
        "salary_max": 20000,
        "currency": "AED",
        "required_skills": ["python", "ml"],
        "keywords": [],
        "job_description": "python machine learning engineer for logistics",
        "desired_candidate_profile": None,
    }
 
 
def _candidate_payload() -> dict:
    return {
        "candidate_id": "cand-1",
        "current_country": "UAE",
        "availability_to_join_days": None,
        "expected_salary": 15000,
        "currency": "AED",
        "total_experience_years": 5.0,
        "education_level": "Bachelors",
        "skills": ["python", "ml"],
        "employment_summary": "ML engineer in logistics",
        "cv_text": "python machine learning engineer in logistics",
    }
 
 
def test_evaluate_returns_shortlist(monkeypatch) -> None:
    monkeypatch.setattr(
        SemanticSimilarityScorer,
        "score",
        staticmethod(lambda *_: SemanticSimilarityResult(score=100, explanation="stub")),
    )
 
    payload = {"job": _job_payload(), "candidate": _candidate_payload()}
    resp = client.post("/api/v1/evaluate", json=payload)
 
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "SHORTLIST"
    assert isinstance(data.get("total_score"), int)
    assert data.get("section_scores") is not None
    assert data.get("explanations") is not None
 
 
def test_api_key_enforced_only_when_configured(monkeypatch) -> None:
    monkeypatch.setenv("API_KEY", "secret")
    monkeypatch.setattr(
        SemanticSimilarityScorer,
        "score",
        staticmethod(lambda *_: SemanticSimilarityResult(score=100, explanation="stub")),
    )
 
    payload = {"job": _job_payload(), "candidate": _candidate_payload()}
 
    resp = client.post("/api/v1/evaluate", json=payload)
    assert resp.status_code == 401
 
    resp2 = client.post(
        "/api/v1/evaluate",
        json=payload,
        headers={"X-API-Key": "secret"},
    )
    assert resp2.status_code == 200
 
 
def test_evaluate_low_confidence_and_rejected_paths(monkeypatch) -> None:
    low_conf_candidate = _candidate_payload()
    low_conf_candidate["skills"] = ["python"]
    low_conf_candidate["cv_text"] = "unrelated profile text"
 
    monkeypatch.setattr(
        SemanticSimilarityScorer,
        "score",
        staticmethod(lambda *_: SemanticSimilarityResult(score=50, explanation="stub")),
    )
 
    payload = {"job": _job_payload(), "candidate": low_conf_candidate}
    resp = client.post("/api/v1/evaluate", json=payload)
 
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] in {"LOW_CONFIDENCE", "REJECTED"}
 
    very_low_candidate = _candidate_payload()
    very_low_candidate["skills"] = []
    very_low_candidate["cv_text"] = "unrelated profile text"
    very_low_candidate["employment_summary"] = ""
 
    payload2 = {"job": _job_payload(), "candidate": very_low_candidate}
    resp2 = client.post("/api/v1/evaluate", json=payload2)
 
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["decision"] in {"LOW_CONFIDENCE", "REJECTED"}
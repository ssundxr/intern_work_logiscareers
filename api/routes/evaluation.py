"""
Evaluation API Routes

Thin HTTP controller for candidate evaluation endpoints.

LAYER BOUNDARY RULES:
- ✅ Can import: application/ services, core/schemas/, fastapi
- ❌ Cannot import: core/scoring/, core/rules/, ml/
- ❌ No business logic - delegate to EvaluationService

Layer: API
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from logis_ai_candidate_engine.application.dependencies import (
    get_evaluation_service,
    require_api_key,
)
from logis_ai_candidate_engine.application.evaluation_service import EvaluationService
from logis_ai_candidate_engine.core.schemas.candidate import Candidate
from logis_ai_candidate_engine.core.schemas.evaluation_response import EvaluationResponse
from logis_ai_candidate_engine.core.schemas.job import Job


class EvaluationRequest(BaseModel):
    job: Job
    candidate: Candidate


router = APIRouter(tags=["Evaluation"])


@router.post("/evaluate", response_model=EvaluationResponse)
def evaluate(
    payload: EvaluationRequest,
    _: None = Depends(require_api_key),
    service: EvaluationService = Depends(get_evaluation_service),
) -> EvaluationResponse:
    return service.evaluate(job=payload.job, candidate=payload.candidate)

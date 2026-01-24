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

from api.dependencies import (
    get_evaluation_service,
    require_api_key,
)
from application.evaluation_service import EvaluationService
from application.exceptions import ScoringError, ValidationError
from config.logging_config import get_logger
from core.schemas.candidate import Candidate
from core.schemas.evaluation_response import EvaluationResponse
from core.schemas.job import Job


logger = get_logger(__name__)


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
    """
    Evaluate a candidate against a job posting.
    
    Returns detailed scoring breakdown with confidence metrics.
    """
    logger.info(
        f"Evaluating candidate {payload.candidate.id or 'unknown'} for job {payload.job.id or 'unknown'}"
    )
    
    try:
        result = service.evaluate(job=payload.job, candidate=payload.candidate)
        
        logger.info(
            f"Evaluation complete: score={result.overall_score}/100, "
            f"recommendation={result.recommendation}"
        )
        
        return result
    
    except ValueError as e:
        # Validation errors (missing required fields, invalid data)
        raise ValidationError(
            str(e),
            details={
                "candidate_id": payload.candidate.id,
                "job_id": payload.job.id
            }
        )
    
    except Exception as e:
        # Scoring failures
        raise ScoringError(
            f"Failed to evaluate candidate: {str(e)}",
            details={
                "candidate_id": payload.candidate.id,
                "job_id": payload.job.id,
                "error_type": type(e).__name__
            }
        )

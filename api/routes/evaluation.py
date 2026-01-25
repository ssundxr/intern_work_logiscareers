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


@router.post("/compare", response_model=EvaluationResponse)
def compare_candidate_to_job(
    payload: EvaluationRequest,
    _: None = Depends(require_api_key),
    service: EvaluationService = Depends(get_evaluation_service),
) -> EvaluationResponse:
    """
    Compare a candidate against a job posting (DRF-compatible endpoint).
    
    This endpoint implements hybrid scoring logic:
    - Skill Match: Weighted scores for required_skills vs preferred_skills
    - Experience Fit: Validates total years of experience and GCC-area tenure
    - Semantic Analysis: Uses sentence-transformers to compare career summary vs job description
    
    Features:
    - Preserves HTML formatting in job_description field for NLP processing
    - Returns overall match score (0-100)
    - Provides section_scores breakdown for transparency
    - Generates human-readable strengths and concerns
    - Includes confidence_metrics to quantify AI certainty
    - DRF backend compatible schemas
    - Sub-500ms response times with API key validation
    
    Returns:
        EvaluationResponse with:
        - overall_score: Final match score (0-100)
        - section_scores: Breakdown by skills, experience, semantic
        - strengths: Key candidate advantages
        - concerns: Areas of concern or mismatch
        - confidence_metrics: Quantified AI confidence in the match
        - contextual_adjustments: Applied bonuses/penalties
        - feature_interactions: Detected multi-feature patterns
    """
    logger.info(
        f"[COMPARE] Evaluating candidate {payload.candidate.candidate_id} "
        f"for job {payload.job.job_id}"
    )
    
    try:
        # Call the hybrid evaluation service with HTML-preserved job description
        result = service.evaluate(job=payload.job, candidate=payload.candidate)
        
        logger.info(
            f"[COMPARE] Evaluation complete: overall_score={result.overall_score}/100, "
            f"decision={result.decision}, confidence={result.confidence_metrics.confidence_level if result.confidence_metrics else 'N/A'}"
        )
        
        return result
    
    except ValueError as e:
        # Validation errors (missing required fields, invalid data)
        logger.error(f"[COMPARE] Validation error: {str(e)}")
        raise ValidationError(
            str(e),
            details={
                "candidate_id": payload.candidate.candidate_id,
                "job_id": payload.job.job_id
            }
        )
    
    except Exception as e:
        # Scoring failures
        logger.error(f"[COMPARE] Scoring error: {str(e)}", exc_info=True)
        raise ScoringError(
            f"Failed to evaluate candidate: {str(e)}",
            details={
                "candidate_id": payload.candidate.candidate_id,
                "job_id": payload.job.job_id,
                "error_type": type(e).__name__
            }
        )

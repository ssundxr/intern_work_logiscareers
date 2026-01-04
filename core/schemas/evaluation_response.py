# Schema for candidate evaluation API responses
# core/schemas/evaluation_response.py
# 
# Enterprise-grade evaluation response with advanced ML metrics
# Built to Senior SDE/ML Engineer standards (Google/Microsoft level)

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal, Any


DecisionType = Literal["STRONG_MATCH", "POTENTIAL_MATCH", "WEAK_MATCH", "NOT_RECOMMENDED", "REJECTED"]
ConfidenceLevel = Literal["very_high", "high", "medium", "low"]
AdjustmentType = Literal["bonus", "penalty", "neutral"]


class SectionScore(BaseModel):
    """Detailed score breakdown for a single section with ML-grade metrics"""

    score: int = Field(..., ge=0, le=100, description="Section score (0-100)")
    weight: float = Field(..., ge=0, le=1, description="Weight of this section in final score")
    contribution: float = Field(..., description="Actual points contributed to final score")
    explanation: str = Field(..., description="Human-readable explanation")
    details: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional section-specific details (e.g., matched_skills, missing_skills)",
    )
    
    # Advanced ML Engineer metrics
    confidence: Optional[float] = Field(
        None, ge=0, le=1, description="Confidence in this section's score (0-1)"
    )
    data_completeness: Optional[float] = Field(
        None, ge=0, le=1, description="Proportion of required data fields present"
    )
    signal_strength: Optional[float] = Field(
        None, ge=0, le=1, description="How strong/clear the signal is for this section"
    )


class ImprovementTip(BaseModel):
    """Actionable improvement tip for candidates"""

    section: str = Field(..., description="Section this tip relates to")
    tip: str = Field(..., description="Actionable improvement suggestion")
    priority: Literal["critical", "high", "medium", "low"] = Field(
        default="medium", description="Priority of this improvement"
    )
    potential_impact: Optional[int] = Field(
        None, ge=0, le=100, description="Estimated score increase if implemented"
    )


class ContextualAdjustment(BaseModel):
    """Contextual bonus/penalty applied to base score (non-linear effects)"""
    
    rule_code: str = Field(..., description="Unique rule identifier (e.g., 'GCC_EXP_BONUS')")
    rule_name: str = Field(..., description="Human-readable rule name")
    adjustment_type: AdjustmentType = Field(..., description="Type of adjustment")
    impact: float = Field(..., description="Points added/subtracted from total score")
    reason: str = Field(..., description="Why this adjustment was applied")
    confidence: Optional[float] = Field(
        None, ge=0, le=1, description="Confidence in applying this rule"
    )


class FeatureInteraction(BaseModel):
    """Tracks how multiple features interact to affect scoring"""
    
    interaction_type: str = Field(..., description="Type of interaction (e.g., 'SKILLS_COMP_EXP', 'PERFECT_CANDIDATE_AMP')")
    features_involved: List[str] = Field(..., description="Features participating in interaction")
    impact: float = Field(..., description="Net impact on final score")
    description: str = Field(..., description="How these features interacted")
    strength: Optional[float] = Field(
        None, ge=0, le=1, description="Strength of the interaction (0=weak, 1=strong)"
    )


class ConfidenceMetrics(BaseModel):
    """Quantifies uncertainty and confidence in the evaluation"""
    
    confidence_level: ConfidenceLevel = Field(
        ..., description="Categorical confidence level"
    )
    confidence_score: float = Field(
        ..., ge=0, le=1, description="Numerical confidence (0=uncertain, 1=very confident)"
    )
    uncertainty_factors: List[str] = Field(
        default_factory=list,
        description="Factors reducing confidence (e.g., 'incomplete_profile', 'signal_disagreement')"
    )
    data_completeness: Optional[float] = Field(
        None, ge=0, le=1, description="Proportion of required candidate data present"
    )
    signal_agreement: Optional[float] = Field(
        None, ge=0, le=1, description="How well different scoring signals agree (0=conflict, 1=aligned)"
    )


class PerformanceMetrics(BaseModel):
    """Tracks evaluation performance for monitoring and optimization"""
    
    evaluation_time_ms: Optional[float] = Field(
        None, ge=0, description="Total evaluation time in milliseconds"
    )
    rules_evaluated: Optional[int] = Field(
        None, ge=0, description="Number of rules checked"
    )
    adjustments_applied: Optional[int] = Field(
        None, ge=0, description="Number of contextual adjustments applied"
    )
    interactions_detected: Optional[int] = Field(
        None, ge=0, description="Number of feature interactions found"
    )


class ScoringMetadata(BaseModel):
    """Metadata about the scoring process for explainability and debugging"""
    
    weight_profile: str = Field(
        default="mid_level", description="Weight profile used (e.g., 'entry_level', 'mid_level', 'senior_level')"
    )
    weights_used: Optional[Dict[str, float]] = Field(
        None, description="Actual weights applied to each section"
    )
    base_score: Optional[int] = Field(
        None, ge=0, le=100, description="Score before contextual adjustments"
    )
    adjustment_delta: Optional[float] = Field(
        None, description="Total adjustment applied (adjusted_score - base_score)"
    )
    confidence_level: Optional[ConfidenceLevel] = Field(
        None, description="Overall confidence in evaluation"
    )
    timestamp: Optional[str] = Field(
        None, description="When the evaluation occurred (ISO format)"
    )


class EvaluationResponse(BaseModel):
    """
    Enterprise-grade evaluation response for candidate-job matching.
    Built to Senior SDE/ML Engineer standards with advanced metrics.
    
    Features:
    - Multi-signal scoring with contextual adjustments
    - Confidence quantification and uncertainty tracking
    - Feature interaction detection
    - Performance monitoring
    - Full explainability and audit trail
    """

    # ---- Core Decision ----
    decision: DecisionType = Field(..., description="Final evaluation decision")
    total_score: Optional[int] = Field(None, ge=0, le=100, description="Final compatibility score (0-100)")
    base_score: Optional[int] = Field(
        None, ge=0, le=100, description="Base score before contextual adjustments"
    )
    adjusted_score: Optional[int] = Field(
        None, ge=0, le=100, description="Score after applying bonuses/penalties (same as total_score)"
    )

    # ---- Rejection Handling ----
    is_rejected: bool = Field(default=False, description="Whether candidate was hard-rejected")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection (if rejected)")
    rejection_rule_code: Optional[str] = Field(
        None, description="Rule code that triggered rejection (e.g., HR-001)"
    )

    # ---- Detailed Scoring ----
    section_scores: Optional[Dict[str, SectionScore]] = Field(
        default_factory=dict,
        description="Detailed breakdown per scoring section",
    )

    # ---- Legacy Support (for backward compatibility) ----
    explanations: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Simple text explanations per section (deprecated, use section_scores)",
    )

    # ---- Candidate Portal View ----
    matched_skills: Optional[List[str]] = Field(
        default_factory=list, description="All matched skills (required + preferred)"
    )
    missing_skills: Optional[List[str]] = Field(
        default_factory=list, description="All missing skills (required + preferred)"
    )
    
    # Enhanced: Separate required vs preferred for Phase 2
    matched_required_skills: Optional[List[str]] = Field(
        default_factory=list, description="Matched required/must-have skills"
    )
    matched_preferred_skills: Optional[List[str]] = Field(
        default_factory=list, description="Matched preferred/nice-to-have skills"
    )
    missing_required_skills: Optional[List[str]] = Field(
        default_factory=list, description="Missing required skills (critical gaps)"
    )
    missing_preferred_skills: Optional[List[str]] = Field(
        default_factory=list, description="Missing preferred skills (enhancement opportunities)"
    )
    
    # Match type breakdown for transparency
    skill_match_types: Optional[Dict[str, int]] = Field(
        default=None,
        description="Breakdown of match types: exact, synonym, semantic"
    )
    
    improvement_tips: Optional[List[ImprovementTip]] = Field(
        default_factory=list, description="Actionable tips to improve match score"
    )

    # ---- Recruiter Portal View ----
    quick_summary: Optional[str] = Field(
        None, description="One-line summary for recruiters (e.g., 'Great exp, missing 2 skills')"
    )
    strengths: Optional[List[str]] = Field(
        default_factory=list, description="Key strengths of this candidate"
    )
    concerns: Optional[List[str]] = Field(
        default_factory=list, description="Areas of concern or mismatch"
    )
    
    # ---- Advanced ML Metrics (Phase 4: Senior Engineer Level) ----
    confidence_metrics: Optional[ConfidenceMetrics] = Field(
        None, description="Confidence and uncertainty quantification"
    )
    contextual_adjustments: Optional[List[ContextualAdjustment]] = Field(
        default_factory=list, description="Bonuses/penalties applied to base score"
    )
    feature_interactions: Optional[List[FeatureInteraction]] = Field(
        default_factory=list, description="Detected feature interactions"
    )
    performance_metrics: Optional[PerformanceMetrics] = Field(
        None, description="Evaluation performance metrics"
    )
    scoring_metadata: Optional[ScoringMetadata] = Field(
        None, description="Metadata about the scoring process"
    )

    # ---- Audit & Compliance ----
    rule_trace: Optional[List[str]] = Field(
        default_factory=list,
        description="Triggered rules for audit and explainability",
    )
    evaluated_at: Optional[str] = Field(
        None, description="Timestamp of evaluation (ISO format)"
    )
    model_version: Optional[str] = Field(
        default="2.0.0", description="Version of the scoring model used"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "decision": "STRONG_MATCH",
                "total_score": 92,
                "base_score": 85,
                "adjusted_score": 92,
                "is_rejected": False,
                "section_scores": {
                    "skills": {
                        "score": 90,
                        "weight": 0.30,
                        "contribution": 27.0,
                        "explanation": "Matched all required skills with 2 semantic matches",
                        "details": {
                            "matched_required": ["Supply Chain Management", "Logistics Planning"],
                            "missing_required": [],
                            "exact_matches": 3,
                            "semantic_matches": 2,
                        },
                        "confidence": 0.92,
                        "data_completeness": 1.0,
                    }
                },
                "matched_required_skills": ["Supply Chain Management", "Logistics Planning"],
                "matched_preferred_skills": ["SAP", "Six Sigma"],
                "missing_required_skills": [],
                "missing_preferred_skills": [],
                "skill_match_types": {
                    "exact": 3,
                    "synonym": 1,
                    "semantic": 2,
                },
                "quick_summary": "Perfect match with GCC experience",
                "strengths": ["100% required skills match", "8 years GCC experience"],
                "concerns": [],
                "confidence_metrics": {
                    "confidence_level": "very_high",
                    "confidence_score": 0.94,
                    "uncertainty_factors": [],
                    "data_completeness": 0.95,
                    "signal_agreement": 0.92,
                },
                "contextual_adjustments": [
                    {
                        "rule_code": "GCC_EXP_MAJOR_BONUS",
                        "rule_name": "Major GCC Experience Bonus",
                        "adjustment_type": "bonus",
                        "impact": 8,
                        "reason": "8 years of GCC experience for GCC-required role",
                        "confidence": 1.0,
                    },
                    {
                        "rule_code": "SALARY_SWEET_SPOT",
                        "rule_name": "Salary Sweet Spot Bonus",
                        "adjustment_type": "bonus",
                        "impact": 3,
                        "reason": "Expected salary within ideal range",
                        "confidence": 0.85,
                    },
                ],
                "feature_interactions": [
                    {
                        "interaction_type": "PERFECT_CANDIDATE_AMP",
                        "features_involved": ["skills", "experience", "gcc_experience"],
                        "impact": 2.5,
                        "description": "Perfect alignment across all dimensions amplifies final score",
                        "strength": 0.95,
                    }
                ],
                "performance_metrics": {
                    "evaluation_time_ms": 245.3,
                    "rules_evaluated": 18,
                    "adjustments_applied": 2,
                    "interactions_detected": 1,
                },
                "scoring_metadata": {
                    "weight_profile": "mid_level",
                    "weights_used": {
                        "skills": 0.30,
                        "experience": 0.25,
                        "semantic": 0.35,
                    },
                    "base_score": 85,
                    "adjustment_delta": 7,
                    "confidence_level": "very_high",
                    "timestamp": "2024-01-15T10:30:00Z",
                },
                "rule_trace": [
                    "PASSED: HARD_MIN_EXPERIENCE",
                    "PASSED: HARD_SALARY_MISMATCH",
                    "BONUS: GCC_EXP_MAJOR_BONUS (+8)",
                    "BONUS: SALARY_SWEET_SPOT (+3)",
                ],
                "evaluated_at": "2024-01-15T10:30:00Z",
                "model_version": "2.0.0",
            }
        }

from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from logis_ai_candidate_engine.core.aggregation.weighted_score_aggregator import (
    WeightedScoreAggregator,
)
from logis_ai_candidate_engine.core.explainability.section_explanations import (
    SectionExplanationBuilder,
)
from logis_ai_candidate_engine.core.rules.hard_rejection_engine import HardRejectionEngine
from logis_ai_candidate_engine.core.schemas.candidate import Candidate
from logis_ai_candidate_engine.core.schemas.evaluation_response import (
    EvaluationResponse,
    SectionScore,
    ImprovementTip,
    PerformanceMetrics,
    ScoringMetadata,
)
from logis_ai_candidate_engine.core.schemas.job import Job
from logis_ai_candidate_engine.core.scoring.experience_scorer import ExperienceScorer
from logis_ai_candidate_engine.core.scoring.skills_scorer import SkillsScorer
from logis_ai_candidate_engine.ml.semantic_similarity import SemanticSimilarityScorer

# Import CV parsing routes (Phase 3)
from logis_ai_candidate_engine.api.routes.cv import router as cv_router

# Import Phase 4: Advanced Scoring Components
from logis_ai_candidate_engine.core.scoring.contextual_adjuster import ContextualAdjuster
from logis_ai_candidate_engine.core.scoring.confidence_calculator import ConfidenceCalculator
from logis_ai_candidate_engine.core.scoring.advanced_scorer import (
    FeatureInteractionDetector,
    SmartWeightOptimizer,
)


class EvaluationRequest(BaseModel):
    job: Job
    candidate: Candidate


def _require_api_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")) -> None:
    configured = os.getenv("API_KEY")
    if not configured:
        return
    if x_api_key != configured:
        raise HTTPException(status_code=401, detail="Invalid API key")


def _build_semantic_inputs(job: Job, candidate: Candidate) -> tuple[str, str, Optional[str]]:
    job_text = job.job_description
    if job.required_skills:
        job_text = f"{job_text}\nRequired skills: {', '.join(job.required_skills)}"

    candidate_text_parts = [candidate.cv_text or "", candidate.employment_summary or ""]
    candidate_text = "\n".join([p for p in candidate_text_parts if p]).strip()
    return job_text, candidate_text, job.desired_candidate_profile


def _decision_from_score(total_score: int) -> str:
    """Map numeric score to decision category"""
    if total_score >= 85:
        return "STRONG_MATCH"
    if total_score >= 60:
        return "POTENTIAL_MATCH"
    if total_score >= 40:
        return "WEAK_MATCH"
    return "NOT_RECOMMENDED"


app = FastAPI(
    title="Logis AI Candidate Engine",
    version="2.0.0",
    description="Enterprise-grade AI-powered candidate ranking system for Logis Career. "
                "Features: Advanced hybrid scoring, confidence metrics, contextual adjustments, "
                "and feature interaction detection. Built to Senior SDE/ML Engineer standards.",
)

# Include CV parsing routes (Phase 3: NER CV Parsing)
app.include_router(cv_router, prefix="/api/v1", tags=["CV Parsing"])

# Initialize Phase 4 advanced scorers (singletons)
_contextual_adjuster = ContextualAdjuster()
_confidence_calculator = ConfidenceCalculator()
_interaction_detector = FeatureInteractionDetector()
_weight_optimizer = SmartWeightOptimizer()


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring and load balancers"""
    return {
        "status": "healthy",
        "service": "logis-ai-candidate-engine",
        "version": "2.0.0",
        "phase": "4 - Advanced Hybrid Scoring",
        "features": [
            "contextual_adjustments",
            "confidence_scoring",
            "feature_interactions",
            "smart_weight_optimization",
        ],
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/api/v1/evaluate", response_model=EvaluationResponse)
def evaluate(payload: EvaluationRequest, _: None = Depends(_require_api_key)) -> EvaluationResponse:
    """
    Evaluate a candidate against a job with comprehensive scoring.
    
    Features:
    - Hard rejection rules
    - Multi-signal scoring (skills, experience, semantic)
    - Contextual adjustments
    - Confidence scoring
    - Feature interaction detection
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Start performance tracking
    start_time = time.time()
    rules_evaluated = 0
    
    job = payload.job
    candidate = payload.candidate

    # =========================================================================
    # Step 1: Hard Rejection Engine (Eligibility Filter)
    # =========================================================================
    try:
        hard = HardRejectionEngine.evaluate(job=job, candidate=candidate)
        rules_evaluated += len(hard.rule_trace)
    except Exception as e:
        logger.error(f"Hard rejection engine error: {e}", exc_info=True)
        # Continue with evaluation, assuming eligible
        hard = type('obj', (object,), {
            'is_eligible': True,
            'rejection_reason': None,
            'rejection_rule_code': None,
            'rule_trace': []
        })()
    
    if not hard.is_eligible:
        return EvaluationResponse(
            decision="REJECTED",
            total_score=0,
            is_rejected=True,
            rejection_reason=hard.rejection_reason,
            rejection_rule_code=hard.rejection_rule_code,
            section_scores={},
            explanations={},
            rule_trace=hard.rule_trace,
            evaluated_at=datetime.now().isoformat(),
            model_version="2.0.0",
        )

    # =========================================================================
    # Step 2: Soft Scoring (Multi-Signal Evaluation with Advanced Skill Matching)
    # =========================================================================
    
    # Initialize scorers with error handling
    try:
        semantic_scorer = SemanticSimilarityScorer()
        skills_scorer = SkillsScorer(embedding_model=semantic_scorer.model)
    except Exception as e:
        logger.error(f"Scorer initialization error: {e}", exc_info=True)
        semantic_scorer = SemanticSimilarityScorer()
        skills_scorer = SkillsScorer()
    
    # Score skills with advanced matching (required + preferred)
    try:
        skills = skills_scorer.score(
            required_skills=job.required_skills,
            candidate_skills=candidate.skills,
            preferred_skills=getattr(job, 'preferred_skills', [])
        )
    except Exception as e:
        logger.error(f"Skills scoring error: {e}", exc_info=True)
        skills = type('obj', (object,), {'score': 50, 'details': {}})()
    
    # Score experience
    try:
        experience = ExperienceScorer.score(
            job.min_experience_years,
            job.max_experience_years,
            candidate.total_experience_years,
        )
    except Exception as e:
        logger.error(f"Experience scoring error: {e}", exc_info=True)
        experience = type('obj', (object,), {'score': 50, 'details': {}})()

    # Score semantic similarity
    try:
        job_text, candidate_text, job_profile_text = _build_semantic_inputs(job, candidate)
        semantic = semantic_scorer.score(job_text, candidate_text, job_profile_text)
    except Exception as e:
        logger.error(f"Semantic scoring error: {e}", exc_info=True)
        semantic = type('obj', (object,), {'score': 50, 'details': {}})()

    # Build raw section scores for aggregation
    raw_section_scores: Dict[str, int] = {
        "skills": int(skills.score),
        "experience": int(experience.score),
        "semantic": int(semantic.score),
    }

    # =========================================================================
    # Phase 4: Smart Weight Optimization (Job-Level Adaptive Weighting)
    # =========================================================================
    try:
        weights = _weight_optimizer.get_optimized_weights(job)
    except Exception as e:
        logger.error(f"Weight optimization error: {e}", exc_info=True)
        weights = {"skills": 0.4, "experience": 0.35, "semantic": 0.25}
    
    # Aggregate with smart weights
    aggregated = WeightedScoreAggregator.aggregate(
        section_scores=raw_section_scores, weights=weights
    )
    base_score = aggregated.final_score

    # =========================================================================
    # Phase 4: Contextual Adjustments (Intelligence Beyond Linear Scoring)
    # =========================================================================
    try:
        adjusted_score, contextual_adjustments = _contextual_adjuster.apply_adjustments(
            base_score=base_score,
            job=job,
            candidate=candidate,
            skills_result=skills,
            experience_result=experience,
        )
        rules_evaluated += len(contextual_adjustments)
    except Exception as e:
        logger.error(f"Contextual adjustment error: {e}", exc_info=True)
        adjusted_score = base_score
        contextual_adjustments = []
    
    # =========================================================================
    # Phase 4: Feature Interaction Detection
    # =========================================================================
    feature_interactions = _interaction_detector.detect_interactions(
        job=job,
        candidate=candidate,
        skills_result=skills,
        experience_result=experience,
        base_score=base_score,
    )
    
    # =========================================================================
    # Phase 4: Confidence Scoring (Uncertainty Quantification)
    # =========================================================================
    confidence_metrics = _confidence_calculator.calculate_confidence(
        candidate=candidate,
        skills_result=skills,
        experience_result=experience,
        section_scores=raw_section_scores,
        adjusted_score=adjusted_score,
    )
    
    # =========================================================================
    # Phase 4: Performance Metrics Tracking
    # =========================================================================
    evaluation_time_ms = round((time.time() - start_time) * 1000, 2)
    performance_metrics = PerformanceMetrics(
        evaluation_time_ms=evaluation_time_ms,
        rules_evaluated=rules_evaluated,
        adjustments_applied=len(contextual_adjustments),
        interactions_detected=len(feature_interactions),
    )
    
    # =========================================================================
    # Phase 4: Scoring Metadata (Audit Trail)
    # =========================================================================
    scoring_metadata = ScoringMetadata(
        weight_profile=_weight_optimizer._determine_job_level(job),
        weights_used=weights,
        base_score=base_score,
        adjustment_delta=adjusted_score - base_score,
        confidence_level=confidence_metrics.confidence_level,
        timestamp=datetime.now().isoformat(),
    )

    # =========================================================================
    # Step 3: Build Detailed Response
    # =========================================================================
    
    # Create SectionScore objects with detailed information
    detailed_section_scores: Dict[str, SectionScore] = {
        "skills": SectionScore(
            score=int(skills.score),
            weight=weights["skills"],
            contribution=aggregated.contributions["skills"],
            explanation=skills.explanation,
            details={
                "matched_skills": skills.matched_skills,
                "missing_skills": skills.missing_skills,
                "matched_required": skills.matched_required,
                "matched_preferred": skills.matched_preferred,
                "missing_required": skills.missing_required,
                "missing_preferred": skills.missing_preferred,
                "match_breakdown": {
                    "exact_matches": skills.exact_matches,
                    "synonym_matches": skills.synonym_matches,
                    "semantic_matches": skills.semantic_matches,
                },
                "detailed_matches": skills.match_details,
            },
        ),
        "experience": SectionScore(
            score=int(experience.score),
            weight=weights["experience"],
            contribution=aggregated.contributions["experience"],
            explanation=experience.explanation,
            details={},
        ),
        "semantic": SectionScore(
            score=int(semantic.score),
            weight=weights["semantic"],
            contribution=aggregated.contributions["semantic"],
            explanation=semantic.explanation,
            details={},
        ),
    }

    # Legacy explanations for backward compatibility
    raw_explanations: Dict[str, str] = {
        "skills": skills.explanation,
        "experience": experience.explanation,
        "semantic": semantic.explanation,
    }
    explanations = SectionExplanationBuilder.build(
        section_explanations=raw_explanations,
        contributions=aggregated.contributions,
    )

    # Generate improvement tips for candidates (Phase 2 enhanced)
    improvement_tips: List[ImprovementTip] = []
    
    # Critical: Missing required skills
    if skills.missing_required:
        improvement_tips.append(
            ImprovementTip(
                section="skills",
                tip=f"Critical: Add these required skills: {', '.join(skills.missing_required[:3])}",
                priority="critical",
            )
        )
    
    # High: Missing preferred skills
    if skills.missing_preferred:
        improvement_tips.append(
            ImprovementTip(
                section="skills",
                tip=f"Consider adding these preferred skills: {', '.join(skills.missing_preferred[:3])}",
                priority="high",
            )
        )
    
    if int(experience.score) < 80:
        improvement_tips.append(
            ImprovementTip(
                section="experience",
                tip="Gain more relevant experience to better match the job requirements",
                priority="medium",
            )
        )

    # Generate quick summary for recruiters (Phase 2 enhanced)
    strengths: List[str] = []
    concerns: List[str] = []
    
    # Enhanced skill strength/concern detection
    total_required = len(job.required_skills) if job.required_skills else 0
    if total_required > 0:
        required_match_pct = (len(skills.matched_required) / total_required) * 100
        if required_match_pct >= 80:
            match_type_desc = ""
            if skills.exact_matches > 0:
                match_type_desc = f", {skills.exact_matches} exact"
            strengths.append(f"Strong required skills match ({len(skills.matched_required)}/{total_required}{match_type_desc})")
        elif required_match_pct < 60:
            concerns.append(f"Missing {len(skills.missing_required)} required skills")
    
    if skills.matched_preferred:
        strengths.append(f"Bonus: {len(skills.matched_preferred)} preferred skills matched")
    
    if int(experience.score) >= 80:
        strengths.append(f"Excellent experience fit ({candidate.total_experience_years} years)")
    
    if candidate.gcc_experience_years and candidate.gcc_experience_years > 0:
        strengths.append(f"GCC experience ({candidate.gcc_experience_years} years)")
    
    if int(semantic.score) >= 80:
        strengths.append("High profile relevance")
    
    # Build quick summary
    if len(strengths) >= 2:
        quick_summary = "Strong: " + ", ".join(strengths[:2])
    elif len(concerns) > 0:
        quick_summary = "Note: " + concerns[0]
    else:
        quick_summary = "Average match"

    # Determine final decision (using adjusted score)
    decision = _decision_from_score(adjusted_score)

    # =========================================================================
    # Return Comprehensive Response (Phase 4: Enterprise-Grade Hybrid Scoring)
    # =========================================================================
    return EvaluationResponse(
        decision=decision,
        total_score=adjusted_score,  # Use adjusted score as primary
        base_score=base_score,  # Phase 4: Include base score
        adjusted_score=adjusted_score,  # Phase 4: Explicit adjusted score
        is_rejected=False,
        rejection_reason=None,
        rejection_rule_code=None,
        section_scores=detailed_section_scores,
        explanations=explanations,  # Legacy support
        
        # Enhanced skill matching fields
        matched_skills=skills.matched_skills,
        missing_skills=skills.missing_skills,
        matched_required_skills=skills.matched_required,
        matched_preferred_skills=skills.matched_preferred,
        missing_required_skills=skills.missing_required,
        missing_preferred_skills=skills.missing_preferred,
        skill_match_types={
            "exact": skills.exact_matches,
            "synonym": skills.synonym_matches,
            "semantic": skills.semantic_matches,
        },
        
        improvement_tips=improvement_tips,
        quick_summary=quick_summary,
        strengths=strengths,
        concerns=concerns,
        rule_trace=list(hard.rule_trace),
        evaluated_at=datetime.now().isoformat(),
        model_version="2.0.0",  # Phase 4 version
        
        # Phase 4: Advanced Hybrid Scoring Fields
        confidence_metrics=confidence_metrics,
        contextual_adjustments=contextual_adjustments,
        feature_interactions=feature_interactions,
        performance_metrics=performance_metrics,
        scoring_metadata=scoring_metadata,
    )

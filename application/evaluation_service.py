from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from core.aggregation.weighted_score_aggregator import (
    WeightedScoreAggregator,
)
from core.explainability.section_explanations import (
    SectionExplanationBuilder,
)
from core.rules.hard_rejection_engine import HardRejectionEngine
from core.schemas.candidate import Candidate
from core.schemas.evaluation_response import (
    ContextualAdjustment,
    EvaluationResponse,
    FeatureInteraction,
    ImprovementTip,
    PerformanceMetrics,
    ScoringMetadata,
    SectionScore,
)
from core.schemas.job import Job
from core.scoring.advanced_scorer import (
    FeatureInteractionDetector,
    SmartWeightOptimizer,
)
from core.scoring.confidence_calculator import ConfidenceCalculator
from core.scoring.contextual_adjuster import ContextualAdjuster
from core.scoring.experience_scorer import ExperienceScorer
from core.scoring.skills_scorer import SkillsScorer
from ml.semantic_similarity import SemanticSimilarityScorer


logger = logging.getLogger(__name__)


class EvaluationService:
    
    _instance: Optional[EvaluationService] = None
    
    def __init__(self) -> None:
        self._contextual_adjuster = ContextualAdjuster()
        self._confidence_calculator = ConfidenceCalculator()
        self._interaction_detector = FeatureInteractionDetector()
        self._weight_optimizer = SmartWeightOptimizer()
    
    @classmethod
    def get_instance(cls) -> EvaluationService:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def evaluate(self, job: Job, candidate: Candidate) -> EvaluationResponse:
        start_time = time.time()
        rules_evaluated = 0
        
        rejection_result = self._check_hard_rejection(job, candidate)
        if rejection_result is not None:
            return rejection_result
        
        rules_evaluated += self._get_rejection_rules_count(job, candidate)
        
        skills_result, experience_result, semantic_result = self._compute_section_scores(
            job, candidate
        )
        
        raw_section_scores = self._build_raw_section_scores(
            skills_result, experience_result, semantic_result
        )
        
        weights = self._get_optimized_weights(job)
        
        aggregated = WeightedScoreAggregator.aggregate(
            section_scores=raw_section_scores, weights=weights
        )
        base_score = aggregated.final_score
        
        adjusted_score, contextual_adjustments = self._apply_contextual_adjustments(
            base_score, job, candidate, raw_section_scores
        )
        rules_evaluated += len(contextual_adjustments)
        
        feature_interactions = self._detect_feature_interactions(
            job, candidate, raw_section_scores
        )
        
        confidence_metrics = self._calculate_confidence(
            candidate, raw_section_scores, adjusted_score, job
        )
        
        evaluation_time_ms = round((time.time() - start_time) * 1000, 2)
        performance_metrics = PerformanceMetrics(
            evaluation_time_ms=evaluation_time_ms,
            rules_evaluated=rules_evaluated,
            adjustments_applied=len(contextual_adjustments),
            interactions_detected=len(feature_interactions),
        )
        
        scoring_metadata = ScoringMetadata(
            weight_profile=self._weight_optimizer.determine_job_level(job),
            weights_used=weights,
            base_score=base_score,
            adjustment_delta=adjusted_score - base_score,
            confidence_level=confidence_metrics.confidence_level,
            timestamp=datetime.now().isoformat(),
        )
        
        detailed_section_scores = self._build_detailed_section_scores(
            skills_result, experience_result, semantic_result, weights, aggregated
        )
        
        explanations = self._build_legacy_explanations(
            skills_result, experience_result, semantic_result, aggregated
        )
        
        improvement_tips = self._generate_improvement_tips(job, skills_result, experience_result)
        
        strengths, concerns = self._analyze_strengths_and_concerns(
            job, candidate, skills_result, experience_result, semantic_result
        )
        
        quick_summary = self._generate_quick_summary(strengths, concerns)
        
        decision = self._decision_from_score(adjusted_score)
        
        rule_trace = self._get_rule_trace(job, candidate)
        
        return EvaluationResponse(
            decision=decision,
            total_score=adjusted_score,
            base_score=base_score,
            adjusted_score=adjusted_score,
            is_rejected=False,
            rejection_reason=None,
            rejection_rule_code=None,
            section_scores=detailed_section_scores,
            explanations=explanations,
            matched_skills=skills_result.matched_skills,
            missing_skills=skills_result.missing_skills,
            matched_required_skills=skills_result.matched_required,
            matched_preferred_skills=skills_result.matched_preferred,
            missing_required_skills=skills_result.missing_required,
            missing_preferred_skills=skills_result.missing_preferred,
            skill_match_types={
                "exact": skills_result.exact_matches,
                "synonym": skills_result.synonym_matches,
                "semantic": skills_result.semantic_matches,
            },
            improvement_tips=improvement_tips,
            quick_summary=quick_summary,
            strengths=strengths,
            concerns=concerns,
            rule_trace=rule_trace,
            evaluated_at=datetime.now().isoformat(),
            model_version="2.0.0",
            confidence_metrics=confidence_metrics,
            contextual_adjustments=contextual_adjustments,
            feature_interactions=feature_interactions,
            performance_metrics=performance_metrics,
            scoring_metadata=scoring_metadata,
        )
    
    def _check_hard_rejection(
        self, job: Job, candidate: Candidate
    ) -> Optional[EvaluationResponse]:
        try:
            hard = HardRejectionEngine.evaluate(job=job, candidate=candidate)
        except Exception as e:
            logger.error(f"Hard rejection engine error: {e}", exc_info=True)
            return None
        
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
        return None
    
    def _get_rejection_rules_count(self, job: Job, candidate: Candidate) -> int:
        try:
            hard = HardRejectionEngine.evaluate(job=job, candidate=candidate)
            return len(hard.rule_trace)
        except Exception:
            return 0
    
    def _get_rule_trace(self, job: Job, candidate: Candidate) -> List[str]:
        try:
            hard = HardRejectionEngine.evaluate(job=job, candidate=candidate)
            return list(hard.rule_trace)
        except Exception:
            return []
    
    def _compute_section_scores(self, job: Job, candidate: Candidate) -> Tuple:
        semantic_scorer = SemanticSimilarityScorer()
        skills_scorer = SkillsScorer()
        
        skills_result = self._score_skills(job, candidate, skills_scorer)
        experience_result = self._score_experience(job, candidate)
        semantic_result = self._score_semantic(job, candidate, semantic_scorer)
        
        return skills_result, experience_result, semantic_result
    
    def _score_skills(self, job: Job, candidate: Candidate, skills_scorer: SkillsScorer):
        try:
            return skills_scorer.score(
                required_skills=job.required_skills,
                candidate_skills=candidate.skills,
                preferred_skills=getattr(job, 'preferred_skills', [])
            )
        except Exception as e:
            logger.error(f"Skills scoring error: {e}", exc_info=True)
            return self._create_fallback_skills_result()
    
    def _score_experience(self, job: Job, candidate: Candidate):
        try:
            return ExperienceScorer.score(
                job.min_experience_years,
                job.max_experience_years,
                candidate.total_experience_years,
            )
        except Exception as e:
            logger.error(f"Experience scoring error: {e}", exc_info=True)
            return self._create_fallback_score_result()
    
    def _score_semantic(
        self, job: Job, candidate: Candidate, semantic_scorer: SemanticSimilarityScorer
    ):
        try:
            job_text, candidate_text, job_profile_text = self._build_semantic_inputs(
                job, candidate
            )
            return semantic_scorer.score(job_text, candidate_text, job_profile_text)
        except Exception as e:
            logger.error(f"Semantic scoring error: {e}", exc_info=True)
            return self._create_fallback_score_result()
    
    @staticmethod
    def _build_semantic_inputs(
        job: Job, candidate: Candidate
    ) -> Tuple[str, str, Optional[str]]:
        job_text = job.job_description
        if job.required_skills:
            job_text = f"{job_text}\nRequired skills: {', '.join(job.required_skills)}"
        
        candidate_text_parts = [candidate.cv_text or "", candidate.employment_summary or ""]
        candidate_text = "\n".join([p for p in candidate_text_parts if p]).strip()
        return job_text, candidate_text, job.desired_candidate_profile
    
    def _build_raw_section_scores(
        self, skills_result, experience_result, semantic_result
    ) -> Dict[str, int]:
        return {
            "skills": int(skills_result.score),
            "experience": int(experience_result.score),
            "semantic": int(semantic_result.score),
        }
    
    def _get_optimized_weights(self, job: Job) -> Dict[str, float]:
        try:
            weights, _profile_name = self._weight_optimizer.get_optimized_weights(job)
            return weights
        except Exception as e:
            logger.error(f"Weight optimization error: {e}", exc_info=True)
            return {"skills": 0.4, "experience": 0.35, "semantic": 0.25}
    
    def _apply_contextual_adjustments(
        self,
        base_score: int,
        job: Job,
        candidate: Candidate,
        section_scores: Dict[str, int],
    ) -> Tuple[int, List[ContextualAdjustment]]:
        try:
            adjusted_score, adjustments = self._contextual_adjuster.apply_adjustments(
                base_score=base_score,
                job=job,
                candidate=candidate,
                section_scores=section_scores,
            )
            return int(adjusted_score), adjustments
        except Exception as e:
            logger.error(f"Contextual adjustment error: {e}", exc_info=True)
            return base_score, []
    
    def _detect_feature_interactions(
        self,
        job: Job,
        candidate: Candidate,
        section_scores: Dict[str, int],
    ) -> List[FeatureInteraction]:
        return self._interaction_detector.detect_interactions(
            candidate=candidate,
            job=job,
            section_scores=section_scores,
        )
    
    def _calculate_confidence(
        self,
        candidate: Candidate,
        section_scores: Dict[str, int],
        adjusted_score: int,
        job: Job,
    ):
        return self._confidence_calculator.calculate_confidence(
            total_score=adjusted_score,
            section_scores=section_scores,
            candidate=candidate,
            job=job,
        )
    
    def _build_detailed_section_scores(
        self,
        skills_result,
        experience_result,
        semantic_result,
        weights: Dict[str, float],
        aggregated,
    ) -> Dict[str, SectionScore]:
        return {
            "skills": SectionScore(
                score=int(skills_result.score),
                weight=weights["skills"],
                contribution=aggregated.contributions["skills"],
                explanation=skills_result.explanation,
                details={
                    "matched_skills": skills_result.matched_skills,
                    "missing_skills": skills_result.missing_skills,
                    "matched_required": skills_result.matched_required,
                    "matched_preferred": skills_result.matched_preferred,
                    "missing_required": skills_result.missing_required,
                    "missing_preferred": skills_result.missing_preferred,
                    "match_breakdown": {
                        "exact_matches": skills_result.exact_matches,
                        "synonym_matches": skills_result.synonym_matches,
                        "semantic_matches": skills_result.semantic_matches,
                    },
                    "detailed_matches": skills_result.match_details,
                },
            ),
            "experience": SectionScore(
                score=int(experience_result.score),
                weight=weights["experience"],
                contribution=aggregated.contributions["experience"],
                explanation=experience_result.explanation,
                details={},
            ),
            "semantic": SectionScore(
                score=int(semantic_result.score),
                weight=weights["semantic"],
                contribution=aggregated.contributions["semantic"],
                explanation=semantic_result.explanation,
                details={},
            ),
        }
    
    def _build_legacy_explanations(
        self, skills_result, experience_result, semantic_result, aggregated
    ) -> Dict[str, str]:
        raw_explanations = {
            "skills": skills_result.explanation,
            "experience": experience_result.explanation,
            "semantic": semantic_result.explanation,
        }
        return SectionExplanationBuilder.build(
            section_explanations=raw_explanations,
            contributions=aggregated.contributions,
        )
    
    def _generate_improvement_tips(
        self, job: Job, skills_result, experience_result
    ) -> List[ImprovementTip]:
        tips: List[ImprovementTip] = []
        
        if skills_result.missing_required:
            tips.append(
                ImprovementTip(
                    section="skills",
                    tip=f"Critical: Add these required skills: {', '.join(skills_result.missing_required[:3])}",
                    priority="critical",
                )
            )
        
        if skills_result.missing_preferred:
            tips.append(
                ImprovementTip(
                    section="skills",
                    tip=f"Consider adding these preferred skills: {', '.join(skills_result.missing_preferred[:3])}",
                    priority="high",
                )
            )
        
        if int(experience_result.score) < 80:
            tips.append(
                ImprovementTip(
                    section="experience",
                    tip="Gain more relevant experience to better match the job requirements",
                    priority="medium",
                )
            )
        
        return tips
    
    def _analyze_strengths_and_concerns(
        self,
        job: Job,
        candidate: Candidate,
        skills_result,
        experience_result,
        semantic_result,
    ) -> Tuple[List[str], List[str]]:
        strengths: List[str] = []
        concerns: List[str] = []
        
        total_required = len(job.required_skills) if job.required_skills else 0
        if total_required > 0:
            required_match_pct = (len(skills_result.matched_required) / total_required) * 100
            if required_match_pct >= 80:
                match_type_desc = ""
                if skills_result.exact_matches > 0:
                    match_type_desc = f", {skills_result.exact_matches} exact"
                strengths.append(
                    f"Strong required skills match ({len(skills_result.matched_required)}/{total_required}{match_type_desc})"
                )
            elif required_match_pct < 60:
                concerns.append(f"Missing {len(skills_result.missing_required)} required skills")
        
        if skills_result.matched_preferred:
            strengths.append(f"Bonus: {len(skills_result.matched_preferred)} preferred skills matched")
        
        if int(experience_result.score) >= 80:
            strengths.append(
                f"Excellent experience fit ({candidate.total_experience_years} years)"
            )
        
        if candidate.gcc_experience_years and candidate.gcc_experience_years > 0:
            strengths.append(f"GCC experience ({candidate.gcc_experience_years} years)")
        
        if int(semantic_result.score) >= 80:
            strengths.append("High profile relevance")
        
        return strengths, concerns
    
    def _generate_quick_summary(
        self, strengths: List[str], concerns: List[str]
    ) -> str:
        if len(strengths) >= 2:
            return "Strong: " + ", ".join(strengths[:2])
        elif len(concerns) > 0:
            return "Note: " + concerns[0]
        return "Average match"
    
    @staticmethod
    def _decision_from_score(total_score: int) -> str:
        if total_score >= 85:
            return "STRONG_MATCH"
        if total_score >= 60:
            return "POTENTIAL_MATCH"
        if total_score >= 40:
            return "WEAK_MATCH"
        return "NOT_RECOMMENDED"
    
    @staticmethod
    def _create_fallback_score_result():
        return type('FallbackResult', (), {'score': 50, 'details': {}, 'explanation': 'Fallback score used'})()
    
    @staticmethod
    def _create_fallback_skills_result():
        return type('FallbackSkillsResult', (), {
            'score': 50,
            'details': {},
            'explanation': 'Fallback score used',
            'matched_skills': [],
            'missing_skills': [],
            'matched_required': [],
            'matched_preferred': [],
            'missing_required': [],
            'missing_preferred': [],
            'exact_matches': 0,
            'synonym_matches': 0,
            'semantic_matches': 0,
            'match_details': [],
        })()

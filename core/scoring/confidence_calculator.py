# Confidence Scoring Engine
# core/scoring/confidence_calculator.py
#
# Quantifies uncertainty in evaluation scores
# Built to Senior ML Engineer standards for production ML systems

from typing import Dict, List, Optional
from dataclasses import dataclass

from logis_ai_candidate_engine.core.schemas.candidate import Candidate
from logis_ai_candidate_engine.core.schemas.job import Job
from logis_ai_candidate_engine.core.schemas.evaluation_response import (
    ConfidenceMetrics,
    ConfidenceLevel,
)


@dataclass
class DataQualityMetrics:
    """Tracks completeness of input data"""
    total_fields: int
    populated_fields: int
    critical_missing: List[str]
    optional_missing: List[str]
    
    @property
    def completeness_score(self) -> float:
        """Calculate data completeness score"""
        return self.populated_fields / self.total_fields if self.total_fields > 0 else 0.0


class ConfidenceCalculator:
    """
    Calculates confidence scores for candidate evaluations.
    
    Confidence reflects:
    - Data completeness (do we have enough information?)
    - Signal agreement (do different scoring sections agree?)
    - Score proximity to decision boundaries
    - Presence of edge cases or unusual patterns
    
    Philosophy:
    - Be honest about uncertainty
    - Flag cases that need human review
    - Provide actionable uncertainty factors
    - Support A/B testing and continuous improvement
    """
    
    # Critical fields that significantly impact confidence
    CRITICAL_CANDIDATE_FIELDS = [
        'total_experience_years',
        'skills',
        'expected_salary',
        'nationality',
        'current_country',
    ]
    
    CRITICAL_JOB_FIELDS = [
        'required_skills',
        'min_experience_years',
        'min_salary',
        'max_salary',
    ]
    
    # Decision boundary thresholds
    DECISION_BOUNDARIES = {
        'STRONG_MATCH': 85,
        'POTENTIAL_MATCH': 60,
        'WEAK_MATCH': 40,
    }
    
    def calculate_confidence(
        self,
        total_score: float,
        section_scores: Dict[str, int],
        candidate: Candidate,
        job: Job,
    ) -> ConfidenceMetrics:
        """
        Calculate comprehensive confidence metrics.
        
        Args:
            total_score: Final aggregated score
            section_scores: Individual section scores
            candidate: Candidate profile
            job: Job posting
        
        Returns:
            ConfidenceMetrics object with detailed confidence breakdown
        """
        
        # 1. Data Quality Assessment
        data_quality = self._assess_data_quality(candidate, job)
        
        # 2. Signal Agreement
        signal_agreement = self._calculate_signal_agreement(section_scores)
        
        # 3. Boundary Distance
        boundary_confidence = self._assess_boundary_distance(total_score)
        
        # 4. Uncertainty Factors
        uncertainty_factors = self._identify_uncertainty_factors(
            data_quality, signal_agreement, boundary_confidence, candidate, job
        )
        
        # 5. Overall Confidence Score (weighted combination)
        confidence_score = self._compute_overall_confidence(
            data_quality.completeness_score,
            signal_agreement,
            boundary_confidence,
        )
        
        # 6. Categorical Confidence Level
        confidence_level = self._score_to_level(confidence_score)
        
        return ConfidenceMetrics(
            overall_confidence=confidence_level,
            confidence_score=confidence_score,
            uncertainty_factors=uncertainty_factors,
            signal_agreement=signal_agreement,
            data_quality_score=data_quality.completeness_score,
        )
    
    def _assess_data_quality(
        self, 
        candidate: Candidate, 
        job: Job
    ) -> DataQualityMetrics:
        """
        Assess quality and completeness of input data.
        
        Returns metrics about missing critical vs optional fields.
        """
        
        critical_missing = []
        total_critical = len(self.CRITICAL_CANDIDATE_FIELDS) + len(self.CRITICAL_JOB_FIELDS)
        populated_critical = 0
        
        # Check candidate critical fields
        for field in self.CRITICAL_CANDIDATE_FIELDS:
            value = getattr(candidate, field, None)
            if value is not None and value != [] and value != 0:
                populated_critical += 1
            else:
                critical_missing.append(f"candidate.{field}")
        
        # Check job critical fields
        for field in self.CRITICAL_JOB_FIELDS:
            value = getattr(job, field, None)
            if value is not None and value != [] and value != 0:
                populated_critical += 1
            else:
                critical_missing.append(f"job.{field}")
        
        # Optional fields that improve accuracy
        optional_missing = []
        
        if not candidate.cv_text:
            optional_missing.append("candidate.cv_text")
        if not candidate.gcc_experience_years:
            optional_missing.append("candidate.gcc_experience_years")
        if not candidate.education_details:
            optional_missing.append("candidate.education_details")
        if not job.desired_candidate_profile:
            optional_missing.append("job.desired_candidate_profile")
        
        return DataQualityMetrics(
            total_fields=total_critical,
            populated_fields=populated_critical,
            critical_missing=critical_missing,
            optional_missing=optional_missing,
        )
    
    def _calculate_signal_agreement(
        self, 
        section_scores: Dict[str, int]
    ) -> float:
        """
        Calculate how well different scoring signals agree.
        
        High agreement = all sections give similar scores
        Low agreement = conflicting signals (e.g., great skills but poor experience)
        
        Returns value from 0 (total conflict) to 1 (perfect agreement)
        """
        
        if not section_scores or len(section_scores) < 2:
            return 0.5  # Neutral when not enough signals
        
        scores = list(section_scores.values())
        
        # Calculate coefficient of variation (normalized std dev)
        mean_score = sum(scores) / len(scores)
        
        if mean_score == 0:
            return 1.0  # All zeros = perfect agreement
        
        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5
        
        # Coefficient of variation
        cv = std_dev / mean_score if mean_score > 0 else 0
        
        # Convert to agreement score (0 = high variance, 1 = low variance)
        # CV of 0.3 or more indicates significant disagreement
        agreement = max(0, 1 - (cv / 0.5))
        
        return min(1.0, agreement)
    
    def _assess_boundary_distance(self, score: float) -> float:
        """
        Calculate confidence based on distance from decision boundaries.
        
        Scores near boundaries (e.g., 59 vs 60 for POTENTIAL_MATCH threshold)
        are less confident than scores far from boundaries (e.g., 90).
        
        Returns confidence from 0 (on boundary) to 1 (far from any boundary)
        """
        
        boundaries = sorted(self.DECISION_BOUNDARIES.values())
        
        # Find minimum distance to any boundary
        min_distance = min(abs(score - b) for b in boundaries)
        
        # Normalize: distance of 10+ points = high confidence
        # distance of 0 points = low confidence
        confidence = min(1.0, min_distance / 10.0)
        
        return confidence
    
    def _identify_uncertainty_factors(
        self,
        data_quality: DataQualityMetrics,
        signal_agreement: float,
        boundary_confidence: float,
        candidate: Candidate,
        job: Job,
    ) -> List[str]:
        """
        Identify specific factors contributing to uncertainty.
        
        These are actionable items that explain WHY confidence is low.
        """
        
        factors = []
        
        # Data quality issues
        if data_quality.completeness_score < 0.8:
            factors.append(f"incomplete_data ({int(data_quality.completeness_score * 100)}% complete)")
        
        for missing in data_quality.critical_missing[:3]:  # Top 3
            factors.append(f"missing_{missing.replace('.', '_')}")
        
        # Signal disagreement
        if signal_agreement < 0.6:
            factors.append(f"conflicting_signals (agreement={signal_agreement:.2f})")
        
        # Boundary proximity
        if boundary_confidence < 0.3:
            factors.append("score_near_decision_boundary")
        
        # Edge cases
        if candidate.total_experience_years == 0:
            factors.append("no_work_experience")
        
        if not candidate.skills or len(candidate.skills) == 0:
            factors.append("no_skills_listed")
        
        if job.max_experience_years and candidate.total_experience_years > job.max_experience_years * 1.5:
            factors.append("significant_overqualification")
        
        if candidate.expected_salary > job.max_salary * 1.2:
            factors.append("salary_expectation_very_high")
        
        return factors[:5]  # Return top 5 factors
    
    def _compute_overall_confidence(
        self,
        data_completeness: float,
        signal_agreement: float,
        boundary_confidence: float,
    ) -> float:
        """
        Compute overall confidence score as weighted combination.
        
        Weights reflect relative importance:
        - Data completeness: 40% (can't be confident with missing data)
        - Signal agreement: 35% (conflicting signals = uncertainty)
        - Boundary distance: 25% (marginal cases = lower confidence)
        """
        
        confidence = (
            data_completeness * 0.40 +
            signal_agreement * 0.35 +
            boundary_confidence * 0.25
        )
        
        return min(1.0, max(0.0, confidence))
    
    def _score_to_level(self, confidence_score: float) -> ConfidenceLevel:
        """Convert numerical confidence to categorical level"""
        
        if confidence_score >= 0.85:
            return "very_high"
        elif confidence_score >= 0.70:
            return "high"
        elif confidence_score >= 0.50:
            return "medium"
        else:
            return "low"

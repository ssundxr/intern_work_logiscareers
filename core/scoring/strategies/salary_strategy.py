"""
Salary Scoring Strategy

Extracted from ComprehensiveScorer._assess_salary()
Assesses salary expectations alignment.

This strategy is responsible ONLY for salary assessment.

Configuration: All scoring constants loaded from config.scoring_config.
"""

from typing import List
from config.scoring_config import scoring_config
from core.scoring.strategies.base import ScoringStrategy, ScoringContext
from core.scoring.models import (
    SectionAssessment,
    FieldAssessment,
    MatchLevel
)


class SalaryScoringStrategy(ScoringStrategy):
    """
    Strategy for assessing salary expectations alignment.
    
    Evaluates:
    - Expected salary vs budget
    - Current vs expected (career progression indicator)
    """
    
    def score(self, context: ScoringContext) -> SectionAssessment:
        """
        Assess salary expectations alignment.
        
        This is the EXACT logic from ComprehensiveScorer._assess_salary()
        with NO modifications to preserve bit-for-bit identical scoring.
        """
        candidate_data = context.candidate_data
        job_data = context.job_data
        fields = []
        
        expected_salary = candidate_data.get('expected_salary', 0) or 0
        current_salary = candidate_data.get('current_salary', 0) or 0
        salary_min = job_data.get('salary_min', 0) or 0
        salary_max = job_data.get('salary_max', 0) or 0
        
        # Salary alignment score
        if salary_max == 0:
            salary_score = 100
            salary_explanation = "No salary range specified for this job"
        elif expected_salary == 0:
            salary_score = 80
            salary_explanation = "Candidate salary expectation not specified"
        elif expected_salary <= salary_max:
            if expected_salary >= salary_min:
                salary_score = 100
                salary_explanation = f"Expected salary {expected_salary:,} fits perfectly within budget ({salary_min:,}-{salary_max:,})"
            else:
                salary_score = 95
                salary_explanation = f"Expected salary {expected_salary:,} is below budget range - potential savings"
        elif expected_salary <= salary_max * 1.1:
            salary_score = 80
            salary_explanation = f"Expected salary {expected_salary:,} is slightly above budget ({salary_max:,}) but negotiable"
        elif expected_salary <= salary_max * 1.25:
            salary_score = 60
            salary_explanation = f"Expected salary {expected_salary:,} exceeds budget ({salary_max:,}) by 10-25%"
        else:
            salary_score = 40
            salary_explanation = f"Significant salary gap: expects {expected_salary:,}, budget max is {salary_max:,}"
        
        fields.append(FieldAssessment(
            field_name='expected_salary',
            field_label='Expected Salary',
            candidate_value=f"{expected_salary:,}" if expected_salary else 'Not specified',
            job_requirement=f"{salary_min:,} - {salary_max:,}" if salary_max else 'Not specified',
            score=salary_score,
            explanation=salary_explanation,
            match_level=self._get_match_level(salary_score),
            weight=2.0
        ))
        
        # Current vs Expected (career progression indicator)
        if current_salary and expected_salary:
            increase_pct = ((expected_salary - current_salary) / current_salary) * 100 if current_salary > 0 else 0
            
            if increase_pct <= 20:
                prog_score = 100
                prog_explanation = f"Reasonable salary expectation ({increase_pct:.0f}% increase from current)"
            elif increase_pct <= 35:
                prog_score = 85
                prog_explanation = f"Moderate salary increase expected ({increase_pct:.0f}%)"
            elif increase_pct <= 50:
                prog_score = 70
                prog_explanation = f"Significant salary increase expected ({increase_pct:.0f}%)"
            else:
                prog_score = 50
                prog_explanation = f"Very high salary expectation ({increase_pct:.0f}% increase)"
            
            fields.append(FieldAssessment(
                field_name='salary_progression',
                field_label='Salary Progression',
                candidate_value=f"Current: {current_salary:,} → Expected: {expected_salary:,}",
                job_requirement='Reasonable expectations preferred',
                score=prog_score,
                explanation=prog_explanation,
                match_level=self._get_match_level(prog_score)
            ))
        
        section_score = self._calculate_section_score(fields)
        
        section_weight = scoring_config.section_weights.salary
        return SectionAssessment(
            section_name='salary',
            section_label='Salary',
            fields=fields,
            total_score=section_score,
            weighted_score=section_score * section_weight,
            explanation=self._generate_section_explanation('salary', section_score, fields),
            match_level=self._get_match_level(section_score),
            weight=section_weight
        )
    
    def _calculate_section_score(self, fields: List[FieldAssessment]) -> int:
        """Calculate weighted average score for a section."""
        total_weighted = 0
        total_weight = 0
        
        for field in fields:
            total_weighted += field.score * field.weight
            total_weight += field.weight
        
        return int(round(total_weighted / total_weight)) if total_weight > 0 else 0
    
    def _get_match_level(self, score: int) -> MatchLevel:
        """Determine match level from score."""
        if score >= 85:
            return MatchLevel.EXCELLENT
        elif score >= 70:
            return MatchLevel.GOOD
        elif score >= 50:
            return MatchLevel.PARTIAL
        else:
            return MatchLevel.POOR
    
    def _generate_section_explanation(
        self,
        section_name: str,
        score: int,
        fields: List[FieldAssessment]
    ) -> str:
        """Generate human-readable section explanation."""
        
        high_scoring = [f for f in fields if f.score >= 80]
        low_scoring = [f for f in fields if f.score < 60]
        
        parts = []
        
        if score >= 85:
            parts.append(f"Excellent match on {section_name.replace('_', ' ')}")
        elif score >= 70:
            parts.append(f"Good match on {section_name.replace('_', ' ')}")
        elif score >= 50:
            parts.append(f"Partial match on {section_name.replace('_', ' ')}")
        else:
            parts.append(f"Weak match on {section_name.replace('_', ' ')}")
        
        if high_scoring:
            parts.append(f"Strong in: {', '.join(f.field_label for f in high_scoring[:2])}")
        
        if low_scoring:
            parts.append(f"Gaps in: {', '.join(f.field_label for f in low_scoring[:2])}")
        
        return '. '.join(parts)

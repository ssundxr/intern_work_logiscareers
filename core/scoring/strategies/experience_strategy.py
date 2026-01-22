"""
Experience Scoring Strategy

Extracted from ComprehensiveScorer._assess_experience()
Assesses work experience with recency weighting.

This strategy is responsible ONLY for experience assessment.

Configuration: All scoring constants loaded from config.scoring_config.
"""

from typing import List
from datetime import datetime
from config.scoring_config import scoring_config
from core.scoring.strategies.base import ScoringStrategy, ScoringContext
from core.scoring.models import (
    SectionAssessment,
    FieldAssessment,
    MatchLevel
)


class ExperienceScoringStrategy(ScoringStrategy):
    """
    Strategy for assessing work experience with recency weighting.
    
    Evaluates:
    - Total experience years
    - GCC experience
    - Industry match
    - Functional area match
    - Work level/designation
    """
    
    def score(self, context: ScoringContext) -> SectionAssessment:
        """
        Assess work experience with recency weighting.
        
        This is the EXACT logic from ComprehensiveScorer._assess_experience()
        with NO modifications to preserve bit-for-bit identical scoring.
        """
        candidate_data = context.candidate_data
        job_data = context.job_data
        fields = []
        
        # Get current year for recency calculations
        current_year = datetime.now().year
        
        # Total Experience with recency weighting
        candidate_exp = candidate_data.get('total_experience_years', 0)
        min_exp = job_data.get('min_experience_years', 0)
        max_exp = job_data.get('max_experience_years')
        
        if max_exp is None:
            max_exp = min_exp + 10  # Reasonable range if not specified
        
        # Apply recency weight based on most recent work
        # Check if candidate has recent employment history
        employment_summary = candidate_data.get('employment_summary', '')
        recency_weight = 1.0  # Default
        recency_note = ""
        
        # Simple heuristic: if mentions recent years or "current", higher weight
        recency_weights = scoring_config.experience_recency_weights
        if any(str(year) in employment_summary for year in range(current_year - 2, current_year + 1)):
            recency_weight = recency_weights.current_or_recent
            recency_note = " (recent/current)"
        elif any(str(year) in employment_summary for year in range(current_year - 5, current_year - 2)):
            recency_weight = recency_weights.moderately_recent
            recency_note = " (moderately recent)"
        else:
            recency_weight = recency_weights.older
            recency_note = " (needs verification)"
        
        # Calculate experience score with recency adjustment
        if candidate_exp >= min_exp and candidate_exp <= max_exp:
            base_exp_score = 100
            exp_explanation = f"{candidate_exp:.1f} years perfectly matches required range ({min_exp}-{max_exp} years){recency_note}"
        elif candidate_exp >= min_exp:
            if candidate_exp <= max_exp + 5:
                base_exp_score = 85
                exp_explanation = f"{candidate_exp:.1f} years experience exceeds maximum ({max_exp}), but within acceptable range{recency_note}"
            else:
                base_exp_score = 70
                exp_explanation = f"{candidate_exp:.1f} years may be overqualified for this role (requires {min_exp}-{max_exp} years){recency_note}"
        elif candidate_exp >= min_exp - 1:
            base_exp_score = 75
            exp_explanation = f"{candidate_exp:.1f} years is slightly below minimum ({min_exp} years), but close{recency_note}"
        elif candidate_exp >= min_exp * 0.5:
            base_exp_score = 50
            exp_explanation = f"{candidate_exp:.1f} years experience is below minimum requirement of {min_exp} years{recency_note}"
        else:
            base_exp_score = 25
            exp_explanation = f"Insufficient experience: {candidate_exp:.1f} years vs required {min_exp} years{recency_note}"
        
        # Apply recency weight
        exp_score = int(base_exp_score * recency_weight)
        if recency_weight < 1.0:
            exp_explanation += f". Score adjusted for recency ({recency_weight:.0%})"
        
        fields.append(FieldAssessment(
            field_name='total_experience',
            field_label='Total Experience',
            candidate_value=f"{candidate_exp:.1f} years",
            job_requirement=f"{min_exp}-{max_exp} years",
            score=exp_score,
            explanation=exp_explanation,
            match_level=self._get_match_level(exp_score),
            weight=1.5
        ))
        
        # GCC Experience
        gcc_exp = candidate_data.get('gcc_experience_years', 0)
        min_gcc = job_data.get('min_gcc_experience_years', 0) if job_data.get('require_gcc_experience') else 0
        
        if min_gcc == 0:
            gcc_score = 100 if gcc_exp > 0 else 80
            gcc_explanation = f"GCC experience: {gcc_exp:.1f} years" if gcc_exp > 0 else "No GCC experience, not required"
        elif gcc_exp >= min_gcc:
            gcc_score = 100
            gcc_explanation = f"{gcc_exp:.1f} years GCC experience meets requirement ({min_gcc} years minimum)"
        elif gcc_exp > 0:
            gcc_score = 60
            gcc_explanation = f"{gcc_exp:.1f} years GCC experience is below required {min_gcc} years"
        else:
            gcc_score = 30
            gcc_explanation = f"No GCC experience, but {min_gcc} years required"
        
        fields.append(FieldAssessment(
            field_name='gcc_experience',
            field_label='GCC Experience',
            candidate_value=f"{gcc_exp:.1f} years",
            job_requirement=f"{min_gcc} years minimum" if min_gcc > 0 else 'Not required',
            score=gcc_score,
            explanation=gcc_explanation,
            match_level=self._get_match_level(gcc_score),
            weight=1.2
        ))
        
        # Industry Match
        candidate_industry = candidate_data.get('preferred_industry', '')
        employment_summary = candidate_data.get('employment_summary', '')
        job_industry = job_data.get('industry', '')
        job_sub_industry = job_data.get('sub_industry', '')
        
        industry_keywords = [job_industry.lower(), job_sub_industry.lower()] if job_sub_industry else [job_industry.lower()]
        summary_lower = (employment_summary + ' ' + candidate_industry).lower()
        
        matched_industries = [ind for ind in industry_keywords if ind and ind in summary_lower]
        
        if len(matched_industries) >= 2:
            ind_score = 100
            ind_explanation = f"Strong industry match: experience in {', '.join(matched_industries)}"
        elif len(matched_industries) == 1:
            ind_score = 85
            ind_explanation = f"Industry match found: {matched_industries[0]}"
        elif any(keyword in summary_lower for keyword in ['logistics', 'supply chain', 'warehouse', 'freight', 'shipping', 'transport']):
            ind_score = 75
            ind_explanation = "Related logistics/supply chain experience detected"
        else:
            ind_score = 50
            ind_explanation = f"No direct industry match found for {job_industry}"
        
        fields.append(FieldAssessment(
            field_name='industry',
            field_label='Industry Experience',
            candidate_value=candidate_industry or 'From work history',
            job_requirement=f"{job_industry}" + (f" / {job_sub_industry}" if job_sub_industry else ''),
            score=ind_score,
            explanation=ind_explanation,
            match_level=self._get_match_level(ind_score)
        ))
        
        # Functional Area Match
        candidate_func = candidate_data.get('preferred_functional_area', '')
        job_func = job_data.get('functional_area', '')
        
        if not job_func:
            func_score = 100
            func_explanation = "No specific functional area requirement"
        elif job_func.lower() in (candidate_func + ' ' + employment_summary).lower():
            func_score = 95
            func_explanation = f"Functional area '{job_func}' matches candidate experience"
        elif candidate_func:
            func_score = 70
            func_explanation = f"Candidate functional area '{candidate_func}' differs from job requirement '{job_func}'"
        else:
            func_score = 60
            func_explanation = f"Functional area experience not clearly defined"
        
        fields.append(FieldAssessment(
            field_name='functional_area',
            field_label='Functional Area',
            candidate_value=candidate_func or 'Not specified',
            job_requirement=job_func or 'Not specified',
            score=func_score,
            explanation=func_explanation,
            match_level=self._get_match_level(func_score)
        ))
        
        # Work Level/Designation
        candidate_designation = candidate_data.get('preferred_designation', '')
        job_designation = job_data.get('designation', '')
        
        if not job_designation:
            desig_score = 100
            desig_explanation = "No specific designation requirement"
        elif self._match_designation_level(candidate_designation, job_designation):
            desig_score = 95
            desig_explanation = f"Designation level matches: seeking {job_designation}"
        else:
            desig_score = 70
            desig_explanation = f"Designation: candidate seeking '{candidate_designation}', job offers '{job_designation}'"
        
        fields.append(FieldAssessment(
            field_name='designation',
            field_label='Designation/Role Level',
            candidate_value=candidate_designation or 'Open',
            job_requirement=job_designation or 'Not specified',
            score=desig_score,
            explanation=desig_explanation,
            match_level=self._get_match_level(desig_score)
        ))
        
        # Calculate section score (weighted)
        section_score = self._calculate_section_score(fields)
        
        section_weight = scoring_config.section_weights.experience
        return SectionAssessment(
            section_name='experience',
            section_label='Experience',
            fields=fields,
            total_score=section_score,
            weighted_score=section_score * section_weight,
            explanation=self._generate_section_explanation('experience', section_score, fields),
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
    
    def _match_designation_level(self, candidate: str, job: str) -> bool:
        """Check if designation levels match."""
        levels = {
            'junior': 1, 'entry': 1,
            'mid': 2, 'intermediate': 2,
            'senior': 3, 'lead': 3,
            'manager': 4, 'head': 4,
            'director': 5, 'executive': 5, 'vp': 5, 'cxo': 6
        }
        
        candidate_level = 0
        job_level = 0
        
        for key, level in levels.items():
            if candidate and key in candidate.lower():
                candidate_level = max(candidate_level, level)
            if job and key in job.lower():
                job_level = max(job_level, level)
        
        return abs(candidate_level - job_level) <= 1
    
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

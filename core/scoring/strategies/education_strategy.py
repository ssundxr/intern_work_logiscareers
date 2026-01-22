"""
Education Scoring Strategy

Extracted from ComprehensiveScorer._assess_education()
Assesses education qualifications.

This strategy is responsible ONLY for education assessment.

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


class EducationScoringStrategy(ScoringStrategy):
    """
    Strategy for assessing education qualifications.
    
    Evaluates:
    - Education level
    - Field of study relevance
    - Professional certifications
    """
    
    def score(self, context: ScoringContext) -> SectionAssessment:
        """
        Assess education qualifications.
        
        This is the EXACT logic from ComprehensiveScorer._assess_education()
        with NO modifications to preserve bit-for-bit identical scoring.
        """
        candidate_data = context.candidate_data
        job_data = context.job_data
        fields = []
        
        # Education Level
        candidate_edu = candidate_data.get('education_level', '')
        required_edu = job_data.get('required_education', '')
        
        education_hierarchy = {
            'phd': 5, 'doctorate': 5,
            'masters': 4, 'master': 4, 'mba': 4, 'msc': 4,
            'bachelors': 3, 'bachelor': 3, 'bsc': 3, 'btech': 3,
            'diploma': 2, 'associate': 2,
            'high school': 1, 'secondary': 1
        }
        
        candidate_level = 0
        required_level = 0
        
        for key, level in education_hierarchy.items():
            if candidate_edu and key in candidate_edu.lower():
                candidate_level = max(candidate_level, level)
            if required_edu and key in required_edu.lower():
                required_level = max(required_level, level)
        
        if required_level == 0:
            edu_score = 100
            edu_explanation = "No specific education requirement"
        elif candidate_level >= required_level:
            edu_score = 100
            edu_explanation = f"Education '{candidate_edu}' meets or exceeds requirement '{required_edu}'"
        elif candidate_level == required_level - 1:
            edu_score = 75
            edu_explanation = f"Education '{candidate_edu}' is one level below required '{required_edu}'"
        else:
            edu_score = 50
            edu_explanation = f"Education gap: '{candidate_edu}' vs required '{required_edu}'"
        
        fields.append(FieldAssessment(
            field_name='education_level',
            field_label='Education Level',
            candidate_value=candidate_edu or 'Not specified',
            job_requirement=required_edu or 'Not specified',
            score=edu_score,
            explanation=edu_explanation,
            match_level=self._get_match_level(edu_score),
            weight=1.5
        ))
        
        # Field of Study (if available)
        education_details = candidate_data.get('education_details', [])
        if education_details:
            fields_of_study = [e.get('field_of_study', '') for e in education_details if e.get('field_of_study')]
            study_text = ', '.join(fields_of_study) if fields_of_study else 'Not specified'
            
            job_keywords = (job_data.get('job_description', '') + ' ' + job_data.get('title', '')).lower()
            
            relevance_score = 75
            if any(field.lower() in job_keywords for field in fields_of_study):
                relevance_score = 95
                relevance_explanation = f"Field of study relevant to job requirements"
            else:
                relevance_explanation = "Field of study may not directly relate to job"
            
            fields.append(FieldAssessment(
                field_name='field_of_study',
                field_label='Field of Study',
                candidate_value=study_text,
                job_requirement='Relevant field preferred',
                score=relevance_score,
                explanation=relevance_explanation,
                match_level=self._get_match_level(relevance_score)
            ))
        
        # Certifications (if available)
        certifications = candidate_data.get('it_skills_certifications', [])
        if isinstance(certifications, list) and certifications:
            cert_score = min(100, 70 + len(certifications) * 10)
            cert_explanation = f"Has {len(certifications)} relevant certifications"
        else:
            cert_score = 60
            cert_explanation = "No certifications listed"
        
        fields.append(FieldAssessment(
            field_name='certifications',
            field_label='Professional Certifications',
            candidate_value=f"{len(certifications) if isinstance(certifications, list) else 0} certifications",
            job_requirement='Preferred',
            score=cert_score,
            explanation=cert_explanation,
            match_level=self._get_match_level(cert_score)
        ))
        
        section_score = self._calculate_section_score(fields)
        
        section_weight = scoring_config.section_weights.education
        return SectionAssessment(
            section_name='education',
            section_label='Education & Qualifications',
            fields=fields,
            total_score=section_score,
            weighted_score=section_score * section_weight,
            explanation=self._generate_section_explanation('education', section_score, fields),
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

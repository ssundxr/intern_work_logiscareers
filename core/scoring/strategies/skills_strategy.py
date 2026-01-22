"""
Skills Scoring Strategy

Extracted from ComprehensiveScorer._assess_skills()
Assesses skills matching with weighted importance and industry adjustments.

This strategy is responsible ONLY for skills assessment.

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


class SkillsScoringStrategy(ScoringStrategy):
    """
    Strategy for assessing skills matching with weighted importance and industry adjustments.
    
    Evaluates:
    - Required skills match
    - Preferred skills match
    - IT/Technical skills
    - Industry-specific adjustments
    """
    
    def score(self, context: ScoringContext) -> SectionAssessment:
        """
        Assess skills matching with weighted importance and industry adjustments.
        
        This is the EXACT logic from ComprehensiveScorer._assess_skills()
        with NO modifications to preserve bit-for-bit identical scoring.
        """
        candidate_data = context.candidate_data
        job_data = context.job_data
        fields = []
        
        # Get all candidate skills
        candidate_skills = set()
        professional_skills = candidate_data.get('professional_skills', []) or []
        it_skills = candidate_data.get('it_skills', []) or []
        all_skills = candidate_data.get('skills', []) or []
        
        for skill_list in [professional_skills, it_skills, all_skills]:
            if isinstance(skill_list, list):
                candidate_skills.update(s.lower().strip() for s in skill_list if s)
        
        # Get required and preferred skills
        required_skills = job_data.get('required_skills', []) or []
        preferred_skills = job_data.get('preferred_skills', []) or []
        
        # Get industry for adjustments
        industry = job_data.get('industry', '').lower()
        industry_adjustments = scoring_config.get_industry_adjustment(industry)
        
        # Match required skills with weighted scoring
        matched_required = []
        missing_required = []
        required_weighted_score = 0
        max_required_weight = 0
        
        skill_weights = scoring_config.skill_importance_weights
        for skill in required_skills:
            skill_lower = skill.lower().strip()
            weight = skill_weights.required
            max_required_weight += weight
            
            # Direct match or partial match
            if skill_lower in candidate_skills or any(skill_lower in cs or cs in skill_lower for cs in candidate_skills):
                matched_required.append(skill)
                required_weighted_score += weight
            else:
                missing_required.append(skill)
        
        if required_skills:
            req_match_pct = (required_weighted_score / max_required_weight) * 100 if max_required_weight > 0 else 0
            req_score = int(req_match_pct)
            req_explanation = f"Matched {len(matched_required)}/{len(required_skills)} required skills ({req_match_pct:.0f}% weighted)"
            if missing_required:
                critical_missing = missing_required[:3]
                req_explanation += f". Critical gaps: {', '.join(critical_missing)}"
                if len(missing_required) > 3:
                    req_explanation += f" (+{len(missing_required) - 3} more)"
        else:
            req_score = 100
            req_explanation = "No required skills specified"
        
        fields.append(FieldAssessment(
            field_name='required_skills',
            field_label='Required Skills',
            candidate_value=matched_required or ['None matched'],
            job_requirement=required_skills or ['None specified'],
            score=req_score,
            explanation=req_explanation,
            match_level=self._get_match_level(req_score),
            weight=2.0
        ))
        
        # Match preferred skills with weighted scoring
        matched_preferred = []
        preferred_weighted_score = 0
        max_preferred_weight = 0
        
        for skill in preferred_skills:
            skill_lower = skill.lower().strip()
            weight = skill_weights.preferred
            max_preferred_weight += weight
            
            if skill_lower in candidate_skills or any(skill_lower in cs or cs in skill_lower for cs in candidate_skills):
                matched_preferred.append(skill)
                preferred_weighted_score += weight
        
        if preferred_skills:
            pref_match_pct = (preferred_weighted_score / max_preferred_weight) * 100 if max_preferred_weight > 0 else 0
            pref_score = int(pref_match_pct)
            pref_explanation = f"Matched {len(matched_preferred)}/{len(preferred_skills)} preferred skills ({pref_match_pct:.0f}% weighted)"
        else:
            pref_score = 100
            pref_explanation = "No preferred skills specified"
        
        fields.append(FieldAssessment(
            field_name='preferred_skills',
            field_label='Preferred Skills',
            candidate_value=matched_preferred or ['None matched'],
            job_requirement=preferred_skills or ['None specified'],
            score=pref_score,
            explanation=pref_explanation,
            match_level=self._get_match_level(pref_score)
        ))
        
        # IT/Technical Skills
        it_skill_list = list(it_skills) if isinstance(it_skills, list) else []
        it_score = min(100, 60 + len(it_skill_list) * 5) if it_skill_list else 50
        
        fields.append(FieldAssessment(
            field_name='it_skills',
            field_label='IT/Technical Skills',
            candidate_value=it_skill_list[:5] if it_skill_list else ['None listed'],
            job_requirement='Technical proficiency preferred',
            score=it_score,
            explanation=f"Has {len(it_skill_list)} IT/technical skills" if it_skill_list else "No IT skills listed",
            match_level=self._get_match_level(it_score)
        ))
        
        # Calculate weighted section score (required skills have more weight)
        base_section_score = self._calculate_section_score(fields)
        
        # Apply industry-specific adjustments
        section_score = base_section_score
        industry_bonus = 0
        adjustment_details = []
        
        if industry_adjustments:
            # Check for industry-specific skill bonuses
            if 'skill_multipliers' in industry_adjustments:
                for skill_key, multiplier in industry_adjustments['skill_multipliers'].items():
                    if skill_key in candidate_data or any(skill_key.lower() in str(v).lower() for v in candidate_skills):
                        bonus = int((multiplier - 1.0) * base_section_score)
                        industry_bonus += bonus
                        adjustment_details.append(f"{skill_key.replace('_', ' ').title()} (+{bonus})")
            
            # Check for certification bonuses
            if 'certifications' in industry_adjustments:
                candidate_certs = set(str(c).lower() for c in candidate_data.get('certifications', []) or [])
                for cert_key, bonus_points in industry_adjustments['certifications'].items():
                    if any(cert_key.lower() in cert for cert in candidate_certs):
                        industry_bonus += bonus_points
                        adjustment_details.append(f"{cert_key} cert (+{bonus_points})")
            
            # Check for language bonuses
            if 'languages' in industry_adjustments:
                candidate_langs = set(str(l).lower() for l in candidate_data.get('languages', []) or [])
                for lang_key, bonus_points in industry_adjustments['languages'].items():
                    if any(lang_key.lower() in lang for lang in candidate_langs):
                        industry_bonus += bonus_points
                        adjustment_details.append(f"{lang_key.title()} language (+{bonus_points})")
        
        section_score = min(100, base_section_score + industry_bonus)
        
        # Update explanation if adjustments applied
        base_explanation = self._generate_section_explanation('skills', base_section_score, fields)
        if adjustment_details:
            final_explanation = f"{base_explanation}. Industry bonuses: {', '.join(adjustment_details)}"
        else:
            final_explanation = base_explanation
        
        section_weight = scoring_config.section_weights.skills
        return SectionAssessment(
            section_name='skills',
            section_label='Skills',
            fields=fields,
            total_score=section_score,
            weighted_score=section_score * section_weight,
            explanation=final_explanation,
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

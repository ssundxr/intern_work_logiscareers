"""
Personal Details Scoring Strategy

Extracted from ComprehensiveScorer._assess_personal_details()
Assesses personal details and eligibility criteria.

This strategy is responsible ONLY for personal details assessment.

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


class PersonalDetailsScoringStrategy(ScoringStrategy):
    """
    Strategy for assessing personal details and eligibility criteria.
    
    Evaluates:
    - Nationality match
    - Location alignment
    - Visa status
    - Availability to join
    - Gender preference (if applicable)
    - Driving license
    """
    
    def score(self, context: ScoringContext) -> SectionAssessment:
        """
        Assess personal details and eligibility criteria.
        
        This is the EXACT logic from ComprehensiveScorer._assess_personal_details()
        with NO modifications to preserve bit-for-bit identical scoring.
        """
        candidate_data = context.candidate_data
        job_data = context.job_data
        fields = []
        
        # Nationality check
        nationality = candidate_data.get('nationality', '')
        preferred_nationalities = job_data.get('preferred_nationality', [])
        
        if not preferred_nationalities or not nationality:
            nat_score = 100
            nat_explanation = "No nationality requirement specified"
        elif nationality in preferred_nationalities:
            nat_score = 100
            nat_explanation = f"Nationality '{nationality}' matches preference"
        else:
            nat_score = 70
            nat_explanation = f"Nationality '{nationality}' not in preferred list: {preferred_nationalities}"
        
        fields.append(FieldAssessment(
            field_name='nationality',
            field_label='Nationality',
            candidate_value=nationality or 'Not specified',
            job_requirement=preferred_nationalities or 'No preference',
            score=nat_score,
            explanation=nat_explanation,
            match_level=self._get_match_level(nat_score)
        ))
        
        # Location check
        candidate_location = candidate_data.get('current_country') or candidate_data.get('current_city', '')
        job_location = job_data.get('country') or job_data.get('city', '')
        preferred_locations = job_data.get('preferred_locations', [])
        
        location_match = False
        if not job_location and not preferred_locations:
            loc_score = 100
            loc_explanation = "No location requirement"
        elif candidate_location.lower() in job_location.lower() or job_location.lower() in candidate_location.lower():
            loc_score = 100
            loc_explanation = f"Candidate location '{candidate_location}' matches job location '{job_location}'"
            location_match = True
        elif any(loc.lower() in candidate_location.lower() for loc in preferred_locations):
            loc_score = 90
            loc_explanation = f"Candidate in preferred location: {candidate_location}"
            location_match = True
        else:
            loc_score = 60
            loc_explanation = f"Candidate location '{candidate_location}' differs from job location '{job_location}'"
        
        fields.append(FieldAssessment(
            field_name='location',
            field_label='Location',
            candidate_value=candidate_location or 'Not specified',
            job_requirement=job_location or preferred_locations or 'Flexible',
            score=loc_score,
            explanation=loc_explanation,
            match_level=self._get_match_level(loc_score)
        ))
        
        # Visa Status check
        visa_status = candidate_data.get('visa_status', '')
        visa_requirement = job_data.get('visa_requirement')
        
        if not visa_requirement:
            visa_score = 100
            visa_explanation = "No specific visa requirement"
        elif visa_status and 'valid' in visa_status.lower():
            visa_score = 100
            visa_explanation = f"Valid visa status: {visa_status}"
        elif visa_status:
            visa_score = 80
            visa_explanation = f"Visa status: {visa_status}"
        else:
            visa_score = 60
            visa_explanation = "Visa status not specified"
        
        fields.append(FieldAssessment(
            field_name='visa_status',
            field_label='Visa Status',
            candidate_value=visa_status or 'Not specified',
            job_requirement=visa_requirement or 'Not specified',
            score=visa_score,
            explanation=visa_explanation,
            match_level=self._get_match_level(visa_score)
        ))
        
        # Availability to Join
        availability_days = candidate_data.get('availability_to_join_days', 30)
        required_joining = job_data.get('required_date_of_joining', '')
        
        if availability_days <= 7:
            avail_score = 100
            avail_explanation = f"Immediately available (within {availability_days} days)"
        elif availability_days <= 30:
            avail_score = 90
            avail_explanation = f"Available within {availability_days} days (1 month notice)"
        elif availability_days <= 60:
            avail_score = 75
            avail_explanation = f"Available within {availability_days} days (2 months notice)"
        elif availability_days <= 90:
            avail_score = 60
            avail_explanation = f"Available within {availability_days} days (3 months notice)"
        else:
            avail_score = 40
            avail_explanation = f"Long notice period: {availability_days} days"
        
        fields.append(FieldAssessment(
            field_name='availability',
            field_label='Availability to Join',
            candidate_value=f"{availability_days} days",
            job_requirement=required_joining or 'ASAP preferred',
            score=avail_score,
            explanation=avail_explanation,
            match_level=self._get_match_level(avail_score)
        ))
        
        # Gender preference (if applicable)
        candidate_gender = candidate_data.get('gender', '')
        gender_pref = job_data.get('gender_preference', 'No Preference')
        
        if gender_pref == 'No Preference' or not gender_pref:
            gender_score = 100
            gender_explanation = "No gender preference"
        elif candidate_gender and candidate_gender.lower() == gender_pref.lower():
            gender_score = 100
            gender_explanation = f"Gender matches preference: {gender_pref}"
        elif not candidate_gender:
            gender_score = 80
            gender_explanation = "Candidate gender not specified"
        else:
            gender_score = 50
            gender_explanation = f"Gender '{candidate_gender}' does not match preference '{gender_pref}'"
        
        fields.append(FieldAssessment(
            field_name='gender',
            field_label='Gender Preference',
            candidate_value=candidate_gender or 'Not specified',
            job_requirement=gender_pref,
            score=gender_score,
            explanation=gender_explanation,
            match_level=self._get_match_level(gender_score)
        ))
        
        # Driving License
        has_license = candidate_data.get('driving_license') == 'Yes'
        license_country = candidate_data.get('driving_license_country', '')
        
        if has_license:
            license_score = 100
            license_explanation = f"Valid driving license from {license_country or 'unspecified country'}"
        else:
            license_score = 70
            license_explanation = "No driving license"
        
        fields.append(FieldAssessment(
            field_name='driving_license',
            field_label='Driving License',
            candidate_value='Yes' if has_license else 'No',
            job_requirement='Preferred',
            score=license_score,
            explanation=license_explanation,
            match_level=self._get_match_level(license_score)
        ))
        
        # Calculate section score
        section_score = self._calculate_section_score(fields)
        
        section_weight = scoring_config.section_weights.personal_details
        return SectionAssessment(
            section_name='personal_details',
            section_label='Personal Details & Eligibility',
            fields=fields,
            total_score=section_score,
            weighted_score=section_score * section_weight,
            explanation=self._generate_section_explanation('personal_details', section_score, fields),
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

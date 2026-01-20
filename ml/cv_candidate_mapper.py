# CV to Candidate Mapper
# ml/cv_candidate_mapper.py
#
# Maps parsed CV data to the Candidate schema for evaluation.
# Handles data transformation, normalization, and enrichment.

from typing import Optional, List, Dict, Any
from datetime import datetime

from logis_ai_candidate_engine.ml.cv_parser import (
    ParsedCV, 
    ParsedExperience, 
    ParsedEducation,
    SkillExtraction,
)
from logis_ai_candidate_engine.core.schemas.candidate import (
    Candidate,
    EmploymentHistory,
    EducationDetails,
)


class CVToCandidateMapper:
    """
    Maps parsed CV data to the Candidate schema.
    
    This mapper handles:
    - Data transformation from CV format to Candidate format
    - Default value population for missing required fields
    - Skills normalization and deduplication
    - Experience and education structure mapping
    
    Usage:
        mapper = CVToCandidateMapper()
        candidate = mapper.map(parsed_cv, candidate_id="cand_123")
    """
    
    # Default values for required fields
    DEFAULT_NATIONALITY = "Not Specified"
    DEFAULT_COUNTRY = "Not Specified"
    DEFAULT_CURRENCY = "AED"
    DEFAULT_EXPECTED_SALARY = 0
    
    # Education level mapping
    EDUCATION_LEVEL_MAP = {
        'phd': 'PhD',
        'doctorate': 'PhD',
        'masters': 'Masters',
        'mba': 'Masters',
        'bachelors': 'Bachelors',
        'undergraduate': 'Bachelors',
        'diploma': 'Diploma',
        'associate': 'Diploma',
        'certificate': 'Certificate',
        'high_school': 'High School',
    }
    
    def __init__(
        self,
        default_nationality: str = None,
        default_country: str = None,
        default_currency: str = None,
    ):
        """
        Initialize the mapper with optional default values.
        
        Args:
            default_nationality: Default nationality if not found in CV
            default_country: Default country if not found in CV  
            default_currency: Default currency for salary
        """
        self.default_nationality = default_nationality or self.DEFAULT_NATIONALITY
        self.default_country = default_country or self.DEFAULT_COUNTRY
        self.default_currency = default_currency or self.DEFAULT_CURRENCY
    
    def map(
        self,
        parsed_cv: ParsedCV,
        candidate_id: str,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> Candidate:
        """
        Map a ParsedCV to a Candidate object.
        
        Args:
            parsed_cv: The parsed CV data
            candidate_id: Unique identifier for the candidate
            additional_data: Optional dict with additional candidate data
                           (can override extracted values)
        
        Returns:
            Candidate object ready for evaluation
        """
        additional = additional_data or {}
        
        # Normalize LinkedIn URL to include https:// prefix
        linkedin_url = self._normalize_linkedin_url(parsed_cv.contact.linkedin_url)
        
        # Build candidate with required fields
        candidate_data = {
            # Required fields
            "candidate_id": candidate_id,
            "nationality": additional.get("nationality", self.default_nationality),
            "current_country": additional.get("current_country", self.default_country),
            "expected_salary": additional.get("expected_salary", self.DEFAULT_EXPECTED_SALARY),
            "currency": additional.get("currency", self.default_currency),
            "total_experience_years": self._get_experience_years(parsed_cv, additional),
            "skills": self._extract_skills_list(parsed_cv),
            
            # Optional but commonly available
            "full_name": parsed_cv.name,
            "email": parsed_cv.contact.email,
            "mobile_number": parsed_cv.contact.phone,
            "alternative_mobile": parsed_cv.contact.alternative_phone,
            "linkedin_url": linkedin_url,
            "cv_text": parsed_cv.raw_text,
            
            # Structured data
            "employment_summary": parsed_cv.summary,
            "employment_history": self._map_employment_history(parsed_cv.experience),
            "education_details": self._map_education_details(parsed_cv.education),
            "education_level": self._get_highest_education(parsed_cv.education),
            
            # Additional extracted data
            "languages_known": parsed_cv.languages if parsed_cv.languages else None,
            "professional_skills": self._extract_professional_skills(parsed_cv),
            "it_skills_certifications": self._extract_it_skills(parsed_cv),
        }
        
        # Merge with additional data (additional takes precedence)
        for key, value in additional.items():
            if key in candidate_data and value is not None:
                candidate_data[key] = value
        
        # Remove None values for optional fields to use defaults
        candidate_data = {k: v for k, v in candidate_data.items() if v is not None}
        
        return Candidate(**candidate_data)
    
    def _normalize_linkedin_url(self, url: Optional[str]) -> Optional[str]:
        """Normalize LinkedIn URL to include https:// prefix"""
        if not url:
            return None
        
        # Already has protocol
        if url.startswith('http://') or url.startswith('https://'):
            return url
        
        # Add https:// prefix
        return f"https://{url}"
    
    def _get_experience_years(
        self, 
        parsed_cv: ParsedCV, 
        additional: Dict
    ) -> float:
        """Get total experience years from parsed CV or additional data"""
        if "total_experience_years" in additional:
            return float(additional["total_experience_years"])
        
        if parsed_cv.total_experience_years is not None:
            return parsed_cv.total_experience_years
        
        # Calculate from employment history
        if parsed_cv.experience:
            total_months = sum(
                exp.duration_months or 0 for exp in parsed_cv.experience
            )
            if total_months > 0:
                return round(total_months / 12, 1)
        
        return 0.0
    
    def _extract_skills_list(self, parsed_cv: ParsedCV) -> List[str]:
        """Extract unique normalized skills from parsed CV"""
        if not parsed_cv.skills:
            return []
        
        # Use normalized skills, deduplicated
        seen = set()
        skills = []
        
        for skill_ext in parsed_cv.skills:
            normalized = skill_ext.normalized_skill
            if normalized not in seen:
                skills.append(normalized.replace('_', ' ').title())
                seen.add(normalized)
        
        return skills
    
    def _extract_professional_skills(self, parsed_cv: ParsedCV) -> List[str]:
        """Extract domain/professional skills (logistics, supply chain, etc.)"""
        professional_keywords = [
            'logistics', 'supply_chain', 'warehouse', 'transportation',
            'procurement', 'inventory', 'erp', 'demand_planning', 'freight',
            'customs', 'distribution', 'operations', 'six_sigma',
        ]
        
        professional_skills = []
        
        for skill_ext in parsed_cv.skills:
            normalized = skill_ext.normalized_skill.lower()
            if any(kw in normalized for kw in professional_keywords):
                skill_name = normalized.replace('_', ' ').title()
                if skill_name not in professional_skills:
                    professional_skills.append(skill_name)
        
        return professional_skills if professional_skills else None
    
    def _extract_it_skills(self, parsed_cv: ParsedCV) -> List[str]:
        """Extract IT/technical skills"""
        it_keywords = [
            'python', 'java', 'sql', 'javascript', 'react', 'angular',
            'aws', 'azure', 'docker', 'kubernetes', 'machine_learning',
            'data_analysis', 'tensorflow', 'pytorch', 'tableau', 'power_bi',
        ]
        
        it_skills = []
        
        for skill_ext in parsed_cv.skills:
            normalized = skill_ext.normalized_skill.lower()
            if any(kw in normalized for kw in it_keywords):
                skill_name = normalized.replace('_', ' ').title()
                if skill_name not in it_skills:
                    it_skills.append(skill_name)
        
        return it_skills if it_skills else None
    
    def _map_employment_history(
        self, 
        experiences: List[ParsedExperience]
    ) -> List[EmploymentHistory]:
        """Map parsed experiences to EmploymentHistory schema"""
        history = []
        
        for exp in experiences:
            history.append(EmploymentHistory(
                company_name=exp.company_name or "Unknown Company",
                job_title=exp.job_title or "Unknown Position",
                start_date=exp.start_date,
                end_date=exp.end_date,
                duration_months=exp.duration_months,
                is_current=exp.is_current,
                responsibilities=exp.responsibilities,
                location=exp.location,
            ))
        
        return history if history else None
    
    def _map_education_details(
        self, 
        education: List[ParsedEducation]
    ) -> List[EducationDetails]:
        """Map parsed education to EducationDetails schema"""
        details = []
        
        for edu in education:
            # Normalize degree level
            degree_normalized = edu.degree
            if degree_normalized:
                degree_normalized = self.EDUCATION_LEVEL_MAP.get(
                    degree_normalized.lower(), 
                    degree_normalized.title()
                )
            
            details.append(EducationDetails(
                education_level=degree_normalized or "Unknown",
                field_of_study=edu.field_of_study,
                university=edu.institution,
                graduation_year=edu.graduation_year,
                country=edu.location,
            ))
        
        return details if details else None
    
    def _get_highest_education(
        self, 
        education: List[ParsedEducation]
    ) -> Optional[str]:
        """Get the highest education level from parsed education"""
        if not education:
            return None
        
        # Education level priority (higher is better)
        priority = {
            'phd': 5,
            'doctorate': 5,
            'masters': 4,
            'mba': 4,
            'bachelors': 3,
            'undergraduate': 3,
            'diploma': 2,
            'associate': 2,
            'certificate': 1,
            'high_school': 0,
        }
        
        highest_priority = -1
        highest_level = None
        
        for edu in education:
            if edu.degree:
                degree_lower = edu.degree.lower()
                edu_priority = priority.get(degree_lower, 0)
                
                if edu_priority > highest_priority:
                    highest_priority = edu_priority
                    highest_level = self.EDUCATION_LEVEL_MAP.get(
                        degree_lower, 
                        edu.degree.title()
                    )
        
        return highest_level


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def map_cv_to_candidate(
    parsed_cv: ParsedCV,
    candidate_id: str,
    additional_data: Optional[Dict[str, Any]] = None,
) -> Candidate:
    """
    Convenience function to map a parsed CV to a Candidate.
    
    Args:
        parsed_cv: The parsed CV data
        candidate_id: Unique identifier for the candidate
        additional_data: Optional dict with additional candidate data
        
    Returns:
        Candidate object ready for evaluation
    """
    mapper = CVToCandidateMapper()
    return mapper.map(parsed_cv, candidate_id, additional_data)

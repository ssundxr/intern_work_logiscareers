"""
CV Parsing Service

Application layer service that orchestrates CV parsing operations.
Coordinates between ML parsers and domain schemas without exposing
implementation details to the API layer.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any

from logis_ai_candidate_engine.ml.cv_parser import CVParser
from logis_ai_candidate_engine.ml.cv_candidate_mapper import CVToCandidateMapper


class CVService:
    """
    Service layer for CV parsing operations.
    
    Responsibilities:
    - Orchestrate CV parsing workflow
    - Transform ML outputs to application responses
    - Manage parser and mapper lifecycle
    - Handle error scenarios gracefully
    """
    
    _instance: Optional['CVService'] = None
    
    def __init__(self) -> None:
        self._parser = CVParser()
        self._mapper = CVToCandidateMapper()
    
    @classmethod
    def get_instance(cls) -> 'CVService':
        """Get singleton instance of CVService"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def parse_cv(self, cv_text: str) -> Dict[str, Any]:
        """
        Parse raw CV text and extract structured information.
        
        Args:
            cv_text: Raw CV text to parse
        
        Returns:
            Dictionary with parsed CV data including:
            - Contact information (email, phone, LinkedIn)
            - Professional summary
            - Skills with confidence scores
            - Work experience
            - Education
            - Languages
            - Extraction confidence and warnings
        
        Raises:
            Exception: If CV parsing fails
        """
        result = self._parser.parse(cv_text)
        
        return {
            "success": True,
            "name": result.name,
            "email": result.contact.email,
            "phone": result.contact.phone,
            "linkedin_url": result.contact.linkedin_url,
            "summary": result.summary,
            "skills": [s.to_dict() for s in result.skills],
            "experience": [e.to_dict() for e in result.experience],
            "education": [e.to_dict() for e in result.education],
            "total_experience_years": result.total_experience_years,
            "languages": result.languages,
            "extraction_confidence": result.extraction_confidence,
            "parsing_warnings": result.parsing_warnings,
            "parsed_at": datetime.now().isoformat(),
        }
    
    def parse_cv_to_candidate(
        self,
        cv_text: str,
        candidate_id: Optional[str] = None,
        nationality: Optional[str] = None,
        current_country: Optional[str] = None,
        expected_salary: Optional[int] = None,
        currency: Optional[str] = None,
        total_experience_years: Optional[float] = None,
        visa_status: Optional[str] = None,
        gcc_experience_years: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Parse CV text and create a fully-formed Candidate object.
        
        Args:
            cv_text: Raw CV text to parse
            candidate_id: Optional candidate ID (auto-generated if not provided)
            nationality: Candidate nationality (required for evaluation)
            current_country: Current country (required for evaluation)
            expected_salary: Expected salary
            currency: Salary currency (e.g., AED, USD)
            total_experience_years: Override extracted experience years
            visa_status: Visa status
            gcc_experience_years: GCC-specific experience
        
        Returns:
            Dictionary with:
            - success: Whether operation succeeded
            - candidate: Generated Candidate object
            - parsing_confidence: Confidence score
            - parsing_warnings: Any warnings
            - created_at: Timestamp
        
        Raises:
            Exception: If parsing or mapping fails
        """
        # Parse CV
        parsed_cv = self._parser.parse(cv_text)
        
        # Map to Candidate
        candidate = self._mapper.map_to_candidate(
            parsed_cv=parsed_cv,
            candidate_id=candidate_id,
            nationality=nationality,
            current_country=current_country,
            expected_salary=expected_salary,
            currency=currency,
            total_experience_years=total_experience_years,
            visa_status=visa_status,
            gcc_experience_years=gcc_experience_years,
        )
        
        return {
            "success": True,
            "candidate": candidate.model_dump(),
            "parsing_confidence": parsed_cv.extraction_confidence,
            "parsing_warnings": parsed_cv.parsing_warnings,
            "created_at": datetime.now().isoformat(),
        }
    
    def extract_skills(
        self, 
        cv_text: str, 
        normalize: bool = True
    ) -> Dict[str, Any]:
        """
        Extract only skills from CV text.
        
        Args:
            cv_text: CV text to extract skills from
            normalize: Whether to normalize skills to canonical forms
        
        Returns:
            Dictionary with:
            - success: Whether operation succeeded
            - skills: List of skill names
            - skill_details: Detailed extraction with confidence
            - total_skills_found: Count of skills
        
        Raises:
            Exception: If skill extraction fails
        """
        parsed_cv = self._parser.parse(cv_text)
        
        skill_names = [s.skill_name for s in parsed_cv.skills]
        skill_details = [s.to_dict() for s in parsed_cv.skills]
        
        if normalize:
            # Skills are already normalized by the parser
            pass
        
        return {
            "success": True,
            "skills": skill_names,
            "skill_details": skill_details,
            "total_skills_found": len(skill_names),
        }
    
    def check_health(self) -> Dict[str, Any]:
        """
        Check health of CV parsing service.
        
        Returns:
            Health status information
        """
        return {
            "status": "healthy",
            "parser_ready": self._parser is not None,
            "mapper_ready": self._mapper is not None,
            "timestamp": datetime.now().isoformat(),
        }


# - Parse CV text and extract structured data
# - Map Cv data to Candidate objects
# - Extract skills from Cv text

from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

from logis_ai_candidate_engine.ml.cv_parser import CVParser, ParsedCV
from logis_ai_candidate_engine.ml.cv_candidate_mapper import CVToCandidateMapper
from logis_ai_candidate_engine.core.schemas.candidate import Candidate



_parser: Optional[CVParser] = None
_mapper: Optional[CVToCandidateMapper] = None


def get_parser() -> CVParser:
    """Get or create the CV parser singleton"""
    global _parser
    if _parser is None:
        _parser = CVParser()
    return _parser


def get_mapper() -> CVToCandidateMapper:
    """Get or create the CV mapper singleton"""
    global _mapper
    if _mapper is None:
        _mapper = CVToCandidateMapper()
    return _mapper




def parse_cv(cv_text: str) -> Dict[str, Any]:
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
    parser = get_parser()
    result = parser.parse(cv_text)
    
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
        - Generated Candidate object
        - Parsing confidence score
        - Parsing warnings
        - Creation timestamp
    
    Raises:
        Exception: If CV to Candidate conversion fails
    """
    parser = get_parser()
    mapper = get_mapper()
    
    # Parse the CV
    parsed = parser.parse(cv_text)
    
    # Generate candidate ID if not provided
    candidate_id = candidate_id or f"cv_parsed_{uuid.uuid4().hex[:8]}"
    
    # Prepare additional data from parameters
    additional_data = {}
    if nationality:
        additional_data["nationality"] = nationality
    if current_country:
        additional_data["current_country"] = current_country
    if expected_salary is not None:
        additional_data["expected_salary"] = expected_salary
    if currency:
        additional_data["currency"] = currency
    if total_experience_years is not None:
        additional_data["total_experience_years"] = total_experience_years
    if visa_status:
        additional_data["visa_status"] = visa_status
    if gcc_experience_years is not None:
        additional_data["gcc_experience_years"] = gcc_experience_years
    
    # Map to Candidate
    candidate = mapper.map(
        parsed_cv=parsed,
        candidate_id=candidate_id,
        additional_data=additional_data if additional_data else None,
    )
    
    return {
        "success": True,
        "candidate": candidate.model_dump(),
        "parsing_confidence": parsed.extraction_confidence,
        "parsing_warnings": parsed.parsing_warnings,
        "created_at": datetime.now().isoformat(),
    }


def extract_skills_from_cv(cv_text: str, normalize: bool = True) -> Dict[str, Any]:
    """
    Extract only skills from CV text.
    
    Args:
        cv_text: CV text to extract skills from
        normalize: Whether to normalize skills to canonical forms
    
    Returns:
        Dictionary with:
        - List of extracted skill names
        - Detailed skill extraction with confidence scores
        - Total skills found
    
    Raises:
        Exception: If skill extraction fails
    """
    parser = get_parser()
    result = parser.parse(cv_text)
    
    if normalize:
        skills = list(set(s.normalized_skill.replace('_', ' ').title() for s in result.skills))
    else:
        skills = list(set(s.skill for s in result.skills))
    
    return {
        "success": True,
        "skills": skills,
        "skill_details": [s.to_dict() for s in result.skills],
        "total_skills_found": len(result.skills),
    }


def check_cv_parser_health() -> Dict[str, Any]:
    """
    Health check for CV parsing service
    
    Returns:
        Dictionary with service health status
    """
    try:
        parser = get_parser()
        return {
            "status": "healthy",
            "service": "cv-parser",
            "parser_ready": parser is not None,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "cv-parser",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }

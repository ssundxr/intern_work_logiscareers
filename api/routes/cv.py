# CV Parsing API Routes
# api/routes/cv.py
#
# Provides REST API endpoints for CV parsing operations:
# - Parse CV text and return structured data
# - Parse CV and auto-create a Candidate object
# - Parse CV and directly evaluate against a job

from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from logis_ai_candidate_engine.ml.cv_parser import CVParser, ParsedCV
from logis_ai_candidate_engine.ml.cv_candidate_mapper import CVToCandidateMapper
from logis_ai_candidate_engine.core.schemas.candidate import Candidate


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class ParseCVRequest(BaseModel):
    """Request model for CV parsing"""
    cv_text: str = Field(..., description="Raw CV text to parse", min_length=50)
    
    class Config:
        json_schema_extra = {
            "example": {
                "cv_text": """John Doe
john.doe@email.com
+971 50 123 4567

SUMMARY
Experienced logistics professional with 8+ years in supply chain management.

EXPERIENCE
Supply Chain Manager at XYZ Logistics
Jan 2020 - Present
- Managed end-to-end supply chain operations
- Reduced costs by 15% through optimization

EDUCATION
MBA in Supply Chain Management
University of Dubai, 2015

SKILLS
Python, SQL, SAP, WMS, TMS, Excel, Tableau
"""
            }
        }


class ParsedCVResponse(BaseModel):
    """Response model for parsed CV data"""
    success: bool = Field(..., description="Whether parsing was successful")
    name: Optional[str] = Field(None, description="Extracted candidate name")
    email: Optional[str] = Field(None, description="Extracted email address")
    phone: Optional[str] = Field(None, description="Extracted phone number")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL")
    summary: Optional[str] = Field(None, description="Professional summary")
    skills: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted skills with confidence")
    experience: List[Dict[str, Any]] = Field(default_factory=list, description="Parsed work experience")
    education: List[Dict[str, Any]] = Field(default_factory=list, description="Parsed education")
    total_experience_years: Optional[float] = Field(None, description="Calculated total experience")
    languages: List[str] = Field(default_factory=list, description="Detected languages")
    extraction_confidence: float = Field(..., description="Overall extraction confidence (0-1)")
    parsing_warnings: List[str] = Field(default_factory=list, description="Any warnings during parsing")
    parsed_at: str = Field(..., description="Timestamp of parsing")


class CVToCandidateRequest(BaseModel):
    """Request to parse CV and create a Candidate object"""
    cv_text: str = Field(..., description="Raw CV text to parse", min_length=50)
    candidate_id: Optional[str] = Field(None, description="Optional candidate ID (auto-generated if not provided)")
    
    # Optional overrides for required fields
    nationality: Optional[str] = Field(None, description="Candidate nationality (required for evaluation)")
    current_country: Optional[str] = Field(None, description="Current country (required for evaluation)")
    expected_salary: Optional[int] = Field(None, ge=0, description="Expected salary")
    currency: Optional[str] = Field(None, description="Salary currency (e.g., AED, USD)")
    total_experience_years: Optional[float] = Field(None, ge=0, description="Override extracted experience years")
    
    # Additional optional data
    visa_status: Optional[str] = Field(None, description="Visa status")
    gcc_experience_years: Optional[float] = Field(None, ge=0, description="GCC-specific experience")
    
    class Config:
        json_schema_extra = {
            "example": {
                "cv_text": "John Doe\njohn@email.com\n\nExperienced Python Developer...",
                "nationality": "Indian",
                "current_country": "UAE",
                "expected_salary": 15000,
                "currency": "AED"
            }
        }


class CVToCandidateResponse(BaseModel):
    """Response with parsed CV and generated Candidate"""
    success: bool
    candidate: Optional[Dict[str, Any]] = Field(None, description="Generated Candidate object")
    parsing_confidence: float = Field(..., description="CV parsing confidence score")
    parsing_warnings: List[str] = Field(default_factory=list)
    created_at: str


class CVSkillsExtractionRequest(BaseModel):
    """Request to extract only skills from CV text"""
    cv_text: str = Field(..., description="CV text to extract skills from")
    normalize: bool = Field(True, description="Whether to normalize skills to canonical forms")


class CVSkillsExtractionResponse(BaseModel):
    """Response with extracted skills"""
    success: bool
    skills: List[str] = Field(default_factory=list, description="List of extracted skill names")
    skill_details: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Detailed skill extraction with confidence scores"
    )
    total_skills_found: int


# =============================================================================
# ROUTER DEFINITION
# =============================================================================

router = APIRouter(prefix="/cv", tags=["CV Parsing"])

# Singleton parser instance
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


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/parse", response_model=ParsedCVResponse)
def parse_cv(request: ParseCVRequest) -> ParsedCVResponse:
    """
    Parse raw CV text and extract structured information.
    
    This endpoint uses NER-based extraction to identify:
    - Contact information (email, phone, LinkedIn)
    - Professional summary
    - Skills (with confidence scores and taxonomy matching)
    - Work experience (job titles, companies, durations)
    - Education (degrees, institutions, years)
    - Languages
    
    The extraction uses a multi-strategy approach:
    1. Pattern matching for structured data (emails, phones, dates)
    2. Section detection using keyword and semantic matching
    3. Skill extraction using the Logis Career skill taxonomy
    """
    try:
        parser = get_parser()
        result = parser.parse(request.cv_text)
        
        return ParsedCVResponse(
            success=True,
            name=result.name,
            email=result.contact.email,
            phone=result.contact.phone,
            linkedin_url=result.contact.linkedin_url,
            summary=result.summary,
            skills=[s.to_dict() for s in result.skills],
            experience=[e.to_dict() for e in result.experience],
            education=[e.to_dict() for e in result.education],
            total_experience_years=result.total_experience_years,
            languages=result.languages,
            extraction_confidence=result.extraction_confidence,
            parsing_warnings=result.parsing_warnings,
            parsed_at=datetime.now().isoformat(),
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"CV parsing failed: {str(e)}"
        )


@router.post("/parse-to-candidate", response_model=CVToCandidateResponse)
def parse_cv_to_candidate(request: CVToCandidateRequest) -> CVToCandidateResponse:
    """
    Parse CV text and create a fully-formed Candidate object.
    
    This endpoint:
    1. Parses the CV using NER extraction
    2. Maps extracted data to the Candidate schema
    3. Merges with any provided override values
    4. Returns a Candidate object ready for job evaluation
    
    Use this when you want to:
    - Auto-populate candidate profiles from CVs
    - Reduce manual data entry
    - Standardize candidate data extraction
    """
    try:
        parser = get_parser()
        mapper = get_mapper()
        
        # Parse the CV
        parsed = parser.parse(request.cv_text)
        
        # Generate candidate ID if not provided
        candidate_id = request.candidate_id or f"cv_parsed_{uuid.uuid4().hex[:8]}"
        
        # Prepare additional data from request
        additional_data = {}
        if request.nationality:
            additional_data["nationality"] = request.nationality
        if request.current_country:
            additional_data["current_country"] = request.current_country
        if request.expected_salary is not None:
            additional_data["expected_salary"] = request.expected_salary
        if request.currency:
            additional_data["currency"] = request.currency
        if request.total_experience_years is not None:
            additional_data["total_experience_years"] = request.total_experience_years
        if request.visa_status:
            additional_data["visa_status"] = request.visa_status
        if request.gcc_experience_years is not None:
            additional_data["gcc_experience_years"] = request.gcc_experience_years
        
        # Map to Candidate
        candidate = mapper.map(
            parsed_cv=parsed,
            candidate_id=candidate_id,
            additional_data=additional_data if additional_data else None,
        )
        
        return CVToCandidateResponse(
            success=True,
            candidate=candidate.model_dump(),
            parsing_confidence=parsed.extraction_confidence,
            parsing_warnings=parsed.parsing_warnings,
            created_at=datetime.now().isoformat(),
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"CV to Candidate conversion failed: {str(e)}"
        )


@router.post("/extract-skills", response_model=CVSkillsExtractionResponse)
def extract_skills_from_cv(request: CVSkillsExtractionRequest) -> CVSkillsExtractionResponse:
    """
    Extract only skills from CV text.
    
    This lightweight endpoint is optimized for:
    - Quick skill extraction without full CV parsing
    - Skill validation against the Logis Career taxonomy
    - Skills gap analysis preparation
    
    Returns both simple skill names and detailed extraction info
    including confidence scores and which CV section each skill
    was found in.
    """
    try:
        parser = get_parser()
        result = parser.parse(request.cv_text)
        
        if request.normalize:
            skills = list(set(s.normalized_skill.replace('_', ' ').title() for s in result.skills))
        else:
            skills = list(set(s.skill for s in result.skills))
        
        return CVSkillsExtractionResponse(
            success=True,
            skills=skills,
            skill_details=[s.to_dict() for s in result.skills],
            total_skills_found=len(result.skills),
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Skill extraction failed: {str(e)}"
        )


@router.get("/health")
def cv_parser_health():
    """Health check for CV parsing service"""
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

# Candidate schema definitions for ATS candidate profiles
# core/schemas/candidate.py

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import date


class EmploymentHistory(BaseModel):
    """Structured employment history entry"""

    company_name: str = Field(..., description="Name of the company")
    job_title: str = Field(..., description="Job title/designation")
    industry: Optional[str] = Field(None, description="Company industry")
    functional_area: Optional[str] = Field(None, description="Functional area")
    location: Optional[str] = Field(None, description="Job location")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM format)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM format, 'Present' for current)")
    duration_months: Optional[int] = Field(None, ge=0, description="Duration in months")
    responsibilities: Optional[str] = Field(None, description="Key responsibilities and achievements")
    is_current: bool = Field(default=False, description="Whether this is the current job")


class EducationDetails(BaseModel):
    """Structured education entry"""

    education_level: str = Field(..., description="Degree level (e.g., Bachelors, Masters, PhD)")
    field_of_study: Optional[str] = Field(None, description="Major/specialization (e.g., Computer Science)")
    university: Optional[str] = Field(None, description="Name of university/institution")
    country: Optional[str] = Field(None, description="Country where degree was obtained")
    graduation_year: Optional[int] = Field(None, ge=1950, le=2030, description="Year of graduation")


class Candidate(BaseModel):
    # ---- Identity ----
    candidate_id: str = Field(..., description="Unique candidate identifier")
    registration_number: Optional[str] = Field(None, description="Logis Career registration number (e.g., CAN1001771)")

    # ---- Personal Information ----
    full_name: Optional[str] = Field(None, description="Candidate full name")
    date_of_birth: Optional[str] = Field(None, description="Date of birth (ISO format)")
    gender: Optional[str] = Field(None, description="Gender (Male/Female)")
    nationality: str = Field(..., description="Candidate nationality")
    marital_status: Optional[str] = Field(None, description="Marital status")

    # ---- Location & Contact ----
    current_country: str = Field(..., description="Candidate current country (eligibility check)")
    current_state: Optional[str] = Field(None, description="Current state/emirate")
    current_city: Optional[str] = Field(None, description="Current city")
    mobile_number: Optional[str] = Field(None, description="Primary mobile number")
    alternative_mobile: Optional[str] = Field(None, description="Alternative mobile number")
    email: Optional[str] = Field(None, description="Email address")

    # ---- Visa & Work Authorization ----
    visa_status: Optional[str] = Field(
        None,
        description="Visa status (e.g., Work Visa, Visit Visa, Citizen, Permanent Resident)",
    )
    visa_expiry: Optional[str] = Field(None, description="Visa expiry date (ISO format)")
    driving_license: Optional[str] = Field(None, description="Driving license number or status")
    driving_license_country: Optional[str] = Field(
        None, description="Country that issued the driving license"
    )

    # ---- Language Skills ----
    languages_known: Optional[List[str]] = Field(
        default_factory=list,
        description="Languages known (e.g., English, Hindi, Malayalam, Tamil, French)",
    )

    # ---- Availability ----
    availability_to_join_days: Optional[int] = Field(
        None, ge=0, description="Days required to join (e.g., 14, 30)"
    )

    # ---- Compensation ----
    current_salary: Optional[int] = Field(None, ge=0, description="Current/last drawn salary")
    expected_salary: int = Field(..., ge=0, description="Candidate expected salary")
    currency: str = Field(..., description="Salary currency (e.g., AED, USD)")

    # ---- Professional Profile ----
    total_experience_years: float = Field(..., ge=0, description="Total professional experience in years")
    gcc_experience_years: Optional[float] = Field(
        None, ge=0, description="GCC-specific work experience in years"
    )
    work_level: Optional[str] = Field(
        None, description="Work level/seniority (Entry, Mid, Managerial, Executive)"
    )

    # ---- Skills & Certifications ----
    skills: List[str] = Field(..., description="List of candidate skills (general)")
    professional_skills: Optional[List[str]] = Field(
        default_factory=list, description="Professional/domain skills (e.g., 3PL, Air Freight)"
    )
    it_skills_certifications: Optional[List[str]] = Field(
        default_factory=list, description="IT skills and certifications"
    )

    # ---- Education ----
    education_level: Optional[str] = Field(None, description="Highest education level achieved")
    education_details: Optional[List[EducationDetails]] = Field(
        default_factory=list, description="Structured education history"
    )

    # ---- Employment History ----
    employment_summary: Optional[str] = Field(None, description="Short professional summary")
    employment_history: Optional[List[EmploymentHistory]] = Field(
        default_factory=list, description="Structured employment history"
    )

    # ---- Achievements & Portfolio ----
    achievements: Optional[str] = Field(None, description="Major achievements and projects")
    honors_awards: Optional[str] = Field(None, description="Honors and awards received")

    # ---- Preferences ----
    preferred_industry: Optional[str] = Field(None, description="Preferred industry to work in")
    preferred_sub_industry: Optional[str] = Field(None, description="Preferred sub-industry")
    preferred_functional_area: Optional[str] = Field(None, description="Preferred functional area")
    preferred_designation: Optional[str] = Field(None, description="Preferred job designation/role")
    preferred_job_location: Optional[str] = Field(None, description="Preferred job location")
    job_search_status: Optional[str] = Field(None, description="Job search status (Active, Passive, etc.)")

    # ---- Social & External Links ----
    linkedin_url: Optional[HttpUrl] = Field(None, description="LinkedIn profile URL")

    # ---- CV Content (ML Input) ----
    cv_text: Optional[str] = Field(None, description="Extracted resume/CV text for semantic analysis")
    cv_file_path: Optional[str] = Field(None, description="Path to original CV file (PDF/DOCX)")

    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": "cand_1001",
                "registration_number": "CAN1001771",
                "nationality": "Indian",
                "current_country": "UAE",
                "visa_status": "Work Visa",
                "total_experience_years": 9.8,
                "gcc_experience_years": 9.8,
                "expected_salary": 24000,
                "currency": "AED",
                "skills": ["Sales", "Business Development", "Logistics"],
                "education_level": "Bachelors",
            }
        }

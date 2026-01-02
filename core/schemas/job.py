# Job schema definitions for ATS job postings
# core/schemas/job.py

from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class Job(BaseModel):
    # ---- Identity ----
    job_id: str = Field(..., description="Unique identifier for the job")

    # ---- Employer Information ----
    company_name: Optional[str] = Field(None, description="Name of the hiring company")
    company_type: Optional[str] = Field(
        None, description="Type of company (Employer, Consultancy, etc.)"
    )

    # ---- Location & Compliance ----
    country: str = Field(..., description="Job country (used for eligibility rules)")
    state: Optional[str] = Field(None, description="Job state or region")
    city: Optional[str] = Field(None, description="Job city")
    preferred_locations: Optional[List[str]] = Field(
        default_factory=list,
        description="Preferred candidate locations (for remote/hybrid roles)",
    )

    # ---- Role Metadata ----
    title: str = Field(..., description="Job title")
    job_type: Optional[str] = Field(
        None, description="Employment type (Full-time, Part-time, Contract, etc.)"
    )
    industry: str = Field(..., description="Primary industry")
    sub_industry: Optional[str] = Field(None, description="Sub-industry classification")
    functional_area: str = Field(..., description="Functional area of the role")
    designation: str = Field(..., description="Role seniority or designation")
    job_status: Optional[str] = Field(None, description="Job posting status (Active, Closed, etc.)")

    # ---- Experience Requirements ----
    min_experience_years: int = Field(
        ..., ge=0, description="Minimum required experience in years"
    )
    max_experience_years: Optional[int] = Field(
        None, ge=0, description="Maximum experience (optional)"
    )
    require_gcc_experience: bool = Field(
        default=False, description="Whether GCC work experience is mandatory"
    )

    # ---- Compensation ----
    salary_min: int = Field(..., ge=0, description="Minimum salary offered")
    salary_max: int = Field(..., ge=0, description="Maximum salary offered")
    currency: str = Field(..., description="Salary currency (e.g., AED)")
    hide_salary: bool = Field(
        default=False,
        description="Hide salary from job seekers (reduces applications)",
    )
    other_benefits: Optional[str] = Field(
        None, description="Additional benefits apart from salary"
    )

    # ---- Skills & Keywords ----
    required_skills: List[str] = Field(
        default_factory=list, 
        description="List of mandatory/must-have skills for the job"
    )
    preferred_skills: List[str] = Field(
        default_factory=list,
        description="List of nice-to-have/preferred skills (not mandatory but beneficial)"
    )
    keywords: Optional[List[str]] = Field(
        default_factory=list,
        description="Optional keywords to boost relevance scoring",
    )

    # ---- Eligibility Criteria ----
    required_education: Optional[str] = Field(
        None, description="Required education level (e.g., Bachelors, Masters)"
    )
    preferred_nationality: Optional[List[str]] = Field(
        default_factory=list,
        description="Preferred candidate nationalities (if specified)",
    )
    gender_preference: Optional[Literal["Male", "Female", "No Preference"]] = Field(
        default="No Preference", description="Gender preference (use cautiously for compliance)"
    )
    visa_requirement: Optional[str] = Field(
        None,
        description="Visa requirement (e.g., 'Must have valid work visa', 'Visa provided')",
    )

    # ---- Text Fields (ML Input) ----
    job_description: str = Field(
        ..., description="Full job description text (roles and responsibilities)"
    )
    desired_candidate_profile: Optional[str] = Field(
        None, description="Preferred candidate profile description"
    )
    recruiter_instructions: Optional[str] = Field(
        None, description="Internal instructions for recruiters (not published)"
    )

    # ---- Additional Metadata ----
    no_of_vacancies: int = Field(default=1, ge=1, description="Number of open positions")
    job_expiry_date: Optional[str] = Field(
        None, description="Date when job posting expires (ISO format)"
    )
    mode_of_application: Optional[str] = Field(
        None, description="Application mode (e.g., Direct, Through Consultant)"
    )
    custom_questions: Optional[List[str]] = Field(
        default_factory=list,
        description="Up to 6 custom screening questions for candidates",
    )

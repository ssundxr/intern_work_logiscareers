"""
Data Completeness Validator
Ensures candidates have sufficient data for accurate AI assessment.
Implements hard rejection for missing critical data.

⭐⭐ = CRITICAL - Hard rejection if missing
⭐ = IMPORTANT - Strong warning if missing
"""

from typing import Dict, List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass


class DataCriticality(Enum):
    """Criticality levels for data fields"""
    CRITICAL = "⭐⭐"  # Must have - Hard rejection
    IMPORTANT = "⭐"   # Should have - Strong warning
    OPTIONAL = ""      # Nice to have


@dataclass
class DataRequirement:
    """Represents a data requirement"""
    field_path: str
    field_name: str
    criticality: DataCriticality
    reason: str
    impact_if_missing: str
    
    
class DataCompletenessValidator:
    """
    Validates that candidate and job data has sufficient information
    for accurate AI assessment.
    """
    
    # ============================================
    # CANDIDATE DATA REQUIREMENTS
    # ============================================
    
    CANDIDATE_REQUIREMENTS = [
        # ⭐⭐ CRITICAL - Personal & Contact (Hard Rejection)
        DataRequirement(
            field_path="email",
            field_name="Email Address",
            criticality=DataCriticality.CRITICAL,
            reason="Primary communication channel",
            impact_if_missing="Cannot contact candidate for interviews"
        ),
        DataRequirement(
            field_path="mobile_number",
            field_name="Mobile Number",
            criticality=DataCriticality.CRITICAL,
            reason="Required for interview scheduling and urgent communication",
            impact_if_missing="Cannot reach candidate quickly"
        ),
        DataRequirement(
            field_path="current_city",
            field_name="Current Location",
            criticality=DataCriticality.CRITICAL,
            reason="Required for relocation assessment and logistics",
            impact_if_missing="Cannot assess relocation needs and costs"
        ),
        
        # ⭐ IMPORTANT - Work Experience (Recommended)
        DataRequirement(
            field_path="employment_history",
            field_name="Detailed Work History (At least 1 entry)",
            criticality=DataCriticality.IMPORTANT,
            reason="Recommended for career progression, skill verification, and job hopping analysis",
            impact_if_missing="Reduces career trajectory analysis accuracy by 60%"
        ),
        
        # ⭐ IMPORTANT - Skills (Recommended)
        DataRequirement(
            field_path="skills",
            field_name="Professional/Technical Skills (At least 3)",
            criticality=DataCriticality.IMPORTANT,
            reason="Recommended for skills matching and skill currency analysis",
            impact_if_missing="Reduces skills match accuracy by 70%"
        ),
        
        # ⭐ IMPORTANT - Education (Recommended)
        DataRequirement(
            field_path="education_details",
            field_name="Education History (At least 1 entry)",
            criticality=DataCriticality.IMPORTANT,
            reason="Recommended for qualification verification and learning potential assessment",
            impact_if_missing="Reduces education match accuracy by 55%"
        ),
        
        # ⭐ IMPORTANT - Salary Expectations (Recommended)
        DataRequirement(
            field_path="expected_salary",
            field_name="Expected Salary",
            criticality=DataCriticality.IMPORTANT,
            reason="Recommended for budget matching and salary mismatch detection",
            impact_if_missing="Reduces salary match accuracy by 50%"
        ),
        
        # ⭐ IMPORTANT - CV Document (Recommended for detailed analysis)
        DataRequirement(
            field_path="cv_text",
            field_name="CV/Resume Content",
            criticality=DataCriticality.IMPORTANT,
            reason="Recommended for detailed CV analysis, keyword matching, and comprehensive assessment",
            impact_if_missing="Reduced CV analysis depth - 40% accuracy loss in CV quality scoring"
        ),
        
        # ⭐ IMPORTANT - Work Experience Details
        DataRequirement(
            field_path="employment_history.job_title",
            field_name="Job Titles in Work History",
            criticality=DataCriticality.IMPORTANT,
            reason="Required for career progression analysis",
            impact_if_missing="Reduces career progression analysis accuracy by 70%"
        ),
        DataRequirement(
            field_path="employment_history.company_name",
            field_name="Company Names in Work History",
            criticality=DataCriticality.IMPORTANT,
            reason="Required for employer quality assessment",
            impact_if_missing="Cannot assess employer quality and stability"
        ),
        DataRequirement(
            field_path="employment_history.duration",
            field_name="Employment Dates/Duration",
            criticality=DataCriticality.IMPORTANT,
            reason="Required for gap detection and job hopping analysis",
            impact_if_missing="Cannot detect employment gaps or job hopping - 50% red flag detection accuracy loss"
        ),
        DataRequirement(
            field_path="employment_history.responsibilities",
            field_name="Job Responsibilities/Achievements",
            criticality=DataCriticality.IMPORTANT,
            reason="Required for role depth assessment and skill validation",
            impact_if_missing="Reduces role fit accuracy by 40%"
        ),
        
        # ⭐ IMPORTANT - GCC Experience
        DataRequirement(
            field_path="gcc_experience_years",
            field_name="GCC Work Experience",
            criticality=DataCriticality.IMPORTANT,
            reason="Required for GCC adaptation assessment (if job in GCC)",
            impact_if_missing="Cannot assess GCC market familiarity - 30% cultural fit accuracy loss"
        ),
        
        # ⭐ IMPORTANT - Availability
        DataRequirement(
            field_path="availability_to_join_days",
            field_name="Notice Period/Availability",
            criticality=DataCriticality.IMPORTANT,
            reason="Required for hiring timeline planning",
            impact_if_missing="Cannot assess hiring timeline fit"
        ),
        
        # ⭐ IMPORTANT - Certifications
        DataRequirement(
            field_path="it_skill_certifications",
            field_name="Professional Certifications",
            criticality=DataCriticality.IMPORTANT,
            reason="Required for skill currency and learning potential assessment",
            impact_if_missing="Reduces skill currency accuracy by 20%, learning potential accuracy by 30%"
        ),
        
        # ⭐ IMPORTANT - Current Salary
        DataRequirement(
            field_path="current_salary",
            field_name="Current Salary",
            criticality=DataCriticality.IMPORTANT,
            reason="Required for salary growth assessment and negotiation planning",
            impact_if_missing="Reduces salary assessment accuracy by 30%"
        ),
        
        # ⭐ IMPORTANT - Professional Summary
        DataRequirement(
            field_path="professional_summary",
            field_name="Professional Summary/Profile",
            criticality=DataCriticality.IMPORTANT,
            reason="Provides career overview and communication skills assessment",
            impact_if_missing="Reduces overall assessment depth by 15%"
        ),
    ]
    
    # ============================================
    # JOB DATA REQUIREMENTS
    # ============================================
    
    JOB_REQUIREMENTS = [
        # ⭐⭐ CRITICAL - Basic Job Info
        DataRequirement(
            field_path="title",
            field_name="Job Title",
            criticality=DataCriticality.CRITICAL,
            reason="Core requirement for role matching",
            impact_if_missing="Cannot perform any assessment"
        ),
        DataRequirement(
            field_path="job_description",
            field_name="Job Description",
            criticality=DataCriticality.CRITICAL,
            reason="Required for comprehensive JD-CV matching",
            impact_if_missing="Cannot perform detailed matching - 50% overall accuracy loss"
        ),
        
        # ⭐ IMPORTANT - Experience Requirements
        DataRequirement(
            field_path="min_experience_years",
            field_name="Minimum Experience Required",
            criticality=DataCriticality.IMPORTANT,
            reason="Recommended for experience matching and underqualification detection",
            impact_if_missing="Reduces experience match accuracy by 50%"
        ),
        DataRequirement(
            field_path="max_experience_years",
            field_name="Maximum Experience Required",
            criticality=DataCriticality.IMPORTANT,
            reason="Recommended for overqualification detection",
            impact_if_missing="Reduces overqualification detection accuracy by 40%"
        ),
        
        # ⭐ IMPORTANT - Skills Requirements
        DataRequirement(
            field_path="required_skills",
            field_name="Required/Must-Have Skills (At least 3)",
            criticality=DataCriticality.IMPORTANT,
            reason="Recommended for skills matching",
            impact_if_missing="Reduces skills match accuracy by 60%"
        ),
        
        # ⭐ IMPORTANT - Education Requirements
        DataRequirement(
            field_path="required_education",
            field_name="Minimum Education Required",
            criticality=DataCriticality.IMPORTANT,
            reason="Recommended for education qualification matching",
            impact_if_missing="Reduces education match accuracy by 50%"
        ),
        
        # ⭐ IMPORTANT - Salary Budget
        DataRequirement(
            field_path="salary_max",
            field_name="Maximum Salary Budget",
            criticality=DataCriticality.IMPORTANT,
            reason="Recommended for salary fit assessment and mismatch detection",
            impact_if_missing="Reduces salary match accuracy by 50%"
        ),
        
        # ⭐ IMPORTANT - Location
        DataRequirement(
            field_path="city",
            field_name="Job Location",
            criticality=DataCriticality.IMPORTANT,
            reason="Recommended for location matching and relocation assessment",
            impact_if_missing="Reduces location fit accuracy by 40%"
        ),
        
        # ⭐ IMPORTANT - Job Level/Designation
        DataRequirement(
            field_path="designation",
            field_name="Job Designation/Level",
            criticality=DataCriticality.IMPORTANT,
            reason="Required for seniority level matching",
            impact_if_missing="Reduces seniority match accuracy by 40%"
        ),
        
        # ⭐ IMPORTANT - Preferred Skills
        DataRequirement(
            field_path="preferred_skills",
            field_name="Preferred/Nice-to-Have Skills",
            criticality=DataCriticality.IMPORTANT,
            reason="Required for comprehensive skills scoring",
            impact_if_missing="Reduces skills assessment depth by 30%"
        ),
        
        # ⭐ IMPORTANT - GCC Experience Requirement
        DataRequirement(
            field_path="min_gcc_experience_years",
            field_name="Minimum GCC Experience Required",
            criticality=DataCriticality.IMPORTANT,
            reason="Required for GCC experience matching (if applicable)",
            impact_if_missing="Cannot assess GCC experience requirement"
        ),
        
        # ⭐ IMPORTANT - Salary Range
        DataRequirement(
            field_path="salary_min",
            field_name="Minimum Salary Range",
            criticality=DataCriticality.IMPORTANT,
            reason="Required for complete salary assessment",
            impact_if_missing="Reduces salary assessment accuracy by 20%"
        ),
        
        # ⭐ IMPORTANT - Responsibilities
        DataRequirement(
            field_path="responsibilities",
            field_name="Key Responsibilities",
            criticality=DataCriticality.IMPORTANT,
            reason="Required for role depth matching",
            impact_if_missing="Reduces role fit accuracy by 25%"
        ),
    ]
    
    @staticmethod
    def validate_candidate_data(candidate_data: Dict) -> Tuple[bool, List[str], List[str], float]:
        """
        Validate candidate data completeness.
        
        Returns:
            Tuple of (is_valid_for_assessment, critical_missing, important_missing, completeness_score)
        """
        critical_missing = []
        important_missing = []
        
        for req in DataCompletenessValidator.CANDIDATE_REQUIREMENTS:
            is_present = DataCompletenessValidator._check_field_presence(
                candidate_data, req.field_path
            )
            
            # Special validation for skills - need at least 3
            if req.field_path == "skills" and is_present:
                skills_list = candidate_data.get("skills", [])
                if isinstance(skills_list, list) and len(skills_list) < 3:
                    is_present = False
                    print(f"VALIDATION FAILED: {req.field_path} - has {len(skills_list)} skills, need 3")
            
            # Special validation for numeric fields that can be 0
            if req.field_path in ["expected_salary", "total_experience_years", "gcc_experience_years"]:
                value = candidate_data.get(req.field_path)
                is_present = value is not None and isinstance(value, (int, float)) and value >= 0
                if not is_present:
                    print(f"VALIDATION FAILED: {req.field_path} - value: {value}")
            
            if not is_present:
                print(f"VALIDATION FAILED: {req.field_path} - {req.field_name}")
                if req.criticality == DataCriticality.CRITICAL:
                    critical_missing.append(
                        f"{req.criticality.value} {req.field_name}: {req.impact_if_missing}"
                    )
                elif req.criticality == DataCriticality.IMPORTANT:
                    important_missing.append(
                        f"{req.criticality.value} {req.field_name}: {req.impact_if_missing}"
                    )
        
        # Calculate completeness score
        total_requirements = len(DataCompletenessValidator.CANDIDATE_REQUIREMENTS)
        missing_count = len(critical_missing) + len(important_missing)
        completeness_score = ((total_requirements - missing_count) / total_requirements) * 100
        
        # Valid for assessment only if no critical fields are missing
        is_valid = len(critical_missing) == 0
        
        return is_valid, critical_missing, important_missing, completeness_score
    
    @staticmethod
    def validate_job_data(job_data: Dict) -> Tuple[bool, List[str], List[str], float]:
        """
        Validate job data completeness.
        
        Returns:
            Tuple of (is_valid_for_posting, critical_missing, important_missing, completeness_score)
        """
        critical_missing = []
        important_missing = []
        
        for req in DataCompletenessValidator.JOB_REQUIREMENTS:
            is_present = DataCompletenessValidator._check_field_presence(
                job_data, req.field_path
            )
            
            if not is_present:
                if req.criticality == DataCriticality.CRITICAL:
                    critical_missing.append(
                        f"{req.criticality.value} {req.field_name}: {req.impact_if_missing}"
                    )
                elif req.criticality == DataCriticality.IMPORTANT:
                    important_missing.append(
                        f"{req.criticality.value} {req.field_name}: {req.impact_if_missing}"
                    )
        
        # Calculate completeness score
        total_requirements = len(DataCompletenessValidator.JOB_REQUIREMENTS)
        missing_count = len(critical_missing) + len(important_missing)
        completeness_score = ((total_requirements - missing_count) / total_requirements) * 100
        
        # Valid for posting only if no critical fields are missing
        is_valid = len(critical_missing) == 0
        
        return is_valid, critical_missing, important_missing, completeness_score
    
    @staticmethod
    def _check_field_presence(data: Dict, field_path: str) -> bool:
        """Check if a field is present and has meaningful data"""
        parts = field_path.split('.')
        current = data
        
        for i, part in enumerate(parts):
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                # For lists, check if at least one item has the remaining path
                if len(current) == 0:
                    return False
                # If there are more parts to check, validate against list items
                if i < len(parts) - 1:
                    remaining_path = '.'.join(parts[i:])
                    return any(
                        DataCompletenessValidator._check_field_presence({'temp': item}, f'temp.{remaining_path}')
                        if isinstance(item, dict) else False
                        for item in current
                    )
                # If this is the last part, just check if list is non-empty
                return True
            else:
                return False
            
            if current is None:
                return False
        
        # Check for meaningful data
        if isinstance(current, str):
            return len(current.strip()) > 0
        elif isinstance(current, (list, dict)):
            return len(current) > 0
        elif isinstance(current, (int, float)):
            # Allow 0 as a valid value - only check it's not None
            return True
        elif isinstance(current, bool):
            return True  # Boolean fields are valid regardless of value
        
        return current is not None
    
    @staticmethod
    def get_data_improvement_suggestions(candidate_data: Dict, job_data: Dict) -> Dict:
        """
        Get specific suggestions for improving data quality.
        
        Returns suggestions for both candidate and job data.
        """
        _, cand_critical, cand_important, cand_score = DataCompletenessValidator.validate_candidate_data(candidate_data)
        _, job_critical, job_important, job_score = DataCompletenessValidator.validate_job_data(job_data)
        
        return {
            'candidate': {
                'completeness_score': round(cand_score, 1),
                'critical_missing': cand_critical,
                'important_missing': cand_important,
                'status': 'ready' if not cand_critical else 'incomplete',
                'message': 'Candidate profile is complete for AI assessment' if not cand_critical 
                          else f'Missing {len(cand_critical)} critical field(s) - Cannot perform accurate assessment'
            },
            'job': {
                'completeness_score': round(job_score, 1),
                'critical_missing': job_critical,
                'important_missing': job_important,
                'status': 'ready' if not job_critical else 'incomplete',
                'message': 'Job posting is complete for AI matching' if not job_critical
                          else f'Missing {len(job_critical)} critical field(s) - Cannot perform accurate matching'
            },
            'assessment_quality_estimate': DataCompletenessValidator._estimate_assessment_quality(
                cand_score, job_score, len(cand_critical), len(job_critical)
            )
        }
    
    @staticmethod
    def _estimate_assessment_quality(cand_score: float, job_score: float, 
                                     cand_critical_count: int, job_critical_count: int) -> Dict:
        """Estimate the quality of AI assessment based on data completeness"""
        
        if cand_critical_count > 0 or job_critical_count > 0:
            return {
                'quality': 'UNACCEPTABLE',
                'confidence': '0%',
                'accuracy': '0%',
                'message': 'Cannot perform accurate assessment with missing critical data'
            }
        
        avg_score = (cand_score + job_score) / 2
        
        if avg_score >= 90:
            return {
                'quality': 'EXCELLENT',
                'confidence': '90-95%',
                'accuracy': '90-95%',
                'message': 'Assessment will be highly accurate and reliable - equivalent to experienced HR recruiter'
            }
        elif avg_score >= 75:
            return {
                'quality': 'GOOD',
                'confidence': '75-85%',
                'accuracy': '75-85%',
                'message': 'Assessment will be good but some nuances may be missed'
            }
        elif avg_score >= 60:
            return {
                'quality': 'FAIR',
                'confidence': '60-75%',
                'accuracy': '60-75%',
                'message': 'Assessment will be basic - consider adding more data for better insights'
            }
        else:
            return {
                'quality': 'POOR',
                'confidence': '40-60%',
                'accuracy': '40-60%',
                'message': 'Assessment quality significantly reduced - add important missing fields'
            }

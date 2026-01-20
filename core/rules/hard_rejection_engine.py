# Implements rule-based hard rejection logic for candidates
# core/rules/hard_rejection_engine.py

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from logis_ai_candidate_engine.core.schemas.job import Job
from logis_ai_candidate_engine.core.schemas.candidate import Candidate


class HardRejectionResult:
    """
    Immutable result object for hard rejection evaluation.
    
    Attributes:
        is_eligible: Whether candidate passes all hard rejection rules
        rejection_reason: Human-readable rejection reason (if rejected)
        rejection_rule_code: Machine-readable rule code (e.g., HR-001)
        rule_trace: List of all rules evaluated
    """

    def __init__(
        self,
        is_eligible: bool,
        rejection_reason: Optional[str] = None,
        rejection_rule_code: Optional[str] = None,
        rule_trace: Optional[List[str]] = None,
    ):
        self.is_eligible = is_eligible
        self.rejection_reason = rejection_reason
        self.rejection_rule_code = rejection_rule_code
        self.rule_trace = rule_trace or []


class HardRejectionEngine:
    """
    Applies deterministic, non-negotiable business rules to determine candidate eligibility.
    
    Each rule follows the pattern:
    1. Check condition
    2. If failed: Return immediately with rejection reason and rule code
    3. If passed: Add to rule trace and continue
    
    Rules are evaluated in order of strictness (most restrictive first).
    """

    # Rule configuration constants
    SALARY_TOLERANCE_PERCENT = 10  # Allow 10% over max salary
    MAX_EXPERIENCE_TOLERANCE_YEARS = 3  # Allow 3 years over max
    VISA_EXPIRY_WARNING_DAYS = 90  # Warn if visa expires within 90 days

    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO date string to datetime object"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _normalize_string(s: Optional[str]) -> str:
        """Normalize string for comparison (lowercase, trimmed)"""
        return (s or "").strip().lower()

    @staticmethod
    def evaluate(job: Job, candidate: Candidate) -> HardRejectionResult:
        """
        Evaluate candidate against job using hard rejection rules.
        
        Rules are evaluated in order:
        HR-001: Location + Visa eligibility
        HR-002: Visa expiry check
        HR-003: Salary mismatch
        HR-004: Minimum experience
        HR-005: Maximum experience (overqualified)
        HR-006: Nationality restriction
        HR-007: Education requirement
        HR-008: GCC experience requirement
        
        Returns:
            HardRejectionResult with eligibility status and trace
        """
        rule_trace: List[str] = []

        # =====================================================================
        # HR-001: Location + Work Authorization Eligibility
        # =====================================================================
        rule_trace.append("HR-001:CHECKING_LOCATION_AND_VISA")
        
        candidate_country = HardRejectionEngine._normalize_string(candidate.current_country)
        job_country = HardRejectionEngine._normalize_string(job.country)
        
        if candidate_country != job_country:
            # Candidate is in different country - check if they have work authorization
            visa_status = HardRejectionEngine._normalize_string(candidate.visa_status)
            
            # Valid work authorization statuses
            valid_visa_statuses = [
                "work visa", "work permit", "citizen", "permanent resident", 
                "pr", "nationality", "national"
            ]
            
            has_work_auth = any(status in visa_status for status in valid_visa_statuses)
            
            if not has_work_auth:
                rule_trace.append("HR-001:FAILED")
                return HardRejectionResult(
                    is_eligible=False,
                    rejection_reason=f"Candidate does not have work authorization for {job.country}. Current location: {candidate.current_country}, Visa status: {candidate.visa_status or 'Not specified'}",
                    rejection_rule_code="HR-001",
                    rule_trace=rule_trace,
                )
        
        rule_trace.append("HR-001:PASSED")

        # =====================================================================
        # HR-002: Visa Expiry Check
        # =====================================================================
        rule_trace.append("HR-002:CHECKING_VISA_EXPIRY")
        
        if candidate.visa_expiry:
            expiry_date = HardRejectionEngine._parse_date(candidate.visa_expiry)
            
            if expiry_date:
                today = datetime.now()
                days_until_expiry = (expiry_date - today).days
                
                if days_until_expiry < HardRejectionEngine.VISA_EXPIRY_WARNING_DAYS:
                    rule_trace.append("HR-002:FAILED")
                    return HardRejectionResult(
                        is_eligible=False,
                        rejection_reason=f"Candidate's visa expires within {HardRejectionEngine.VISA_EXPIRY_WARNING_DAYS} days (Expiry: {candidate.visa_expiry})",
                        rejection_rule_code="HR-002",
                        rule_trace=rule_trace,
                    )
        
        rule_trace.append("HR-002:PASSED")

        # =====================================================================
        # HR-003: Salary Expectation
        # =====================================================================
        rule_trace.append("HR-003:CHECKING_SALARY")
        
        # Allow 10% tolerance over max salary
        salary_threshold = job.salary_max * (1 + HardRejectionEngine.SALARY_TOLERANCE_PERCENT / 100)
        
        if candidate.expected_salary > salary_threshold:
            rule_trace.append("HR-003:FAILED")
            return HardRejectionResult(
                is_eligible=False,
                rejection_reason=f"Candidate expected salary ({candidate.expected_salary} {candidate.currency}) exceeds job maximum ({job.salary_max} {job.currency}) by more than {HardRejectionEngine.SALARY_TOLERANCE_PERCENT}%",
                rejection_rule_code="HR-003",
                rule_trace=rule_trace,
            )
        
        rule_trace.append("HR-003:PASSED")

        # =====================================================================
        # HR-004: Minimum Experience
        # =====================================================================
        rule_trace.append("HR-004:CHECKING_MIN_EXPERIENCE")
        
        if candidate.total_experience_years < job.min_experience_years:
            rule_trace.append("HR-004:FAILED")
            return HardRejectionResult(
                is_eligible=False,
                rejection_reason=f"Candidate experience ({candidate.total_experience_years} years) is below minimum requirement ({job.min_experience_years} years)",
                rejection_rule_code="HR-004",
                rule_trace=rule_trace,
            )
        
        rule_trace.append("HR-004:PASSED")

        # =====================================================================
        # HR-005: Maximum Experience (Overqualified Check)
        # =====================================================================
        rule_trace.append("HR-005:CHECKING_MAX_EXPERIENCE")
        
        if job.max_experience_years is not None:
            # Allow some tolerance for overqualification
            max_allowed = job.max_experience_years + HardRejectionEngine.MAX_EXPERIENCE_TOLERANCE_YEARS
            
            if candidate.total_experience_years > max_allowed:
                rule_trace.append("HR-005:FAILED")
                return HardRejectionResult(
                    is_eligible=False,
                    rejection_reason=f"Candidate is overqualified ({candidate.total_experience_years} years exceeds maximum of {job.max_experience_years} years by more than {HardRejectionEngine.MAX_EXPERIENCE_TOLERANCE_YEARS} years)",
                    rejection_rule_code="HR-005",
                    rule_trace=rule_trace,
                )
        
        rule_trace.append("HR-005:PASSED")

        # =====================================================================
        # HR-006: Nationality Restriction
        # =====================================================================
        rule_trace.append("HR-006:CHECKING_NATIONALITY")
        
        if job.preferred_nationality and len(job.preferred_nationality) > 0:
            candidate_nationality = HardRejectionEngine._normalize_string(candidate.nationality)
            allowed_nationalities = [
                HardRejectionEngine._normalize_string(n) for n in job.preferred_nationality
            ]
            
            if candidate_nationality not in allowed_nationalities:
                rule_trace.append("HR-006:FAILED")
                return HardRejectionResult(
                    is_eligible=False,
                    rejection_reason=f"Job requires specific nationality. Candidate nationality: {candidate.nationality}, Required: {', '.join(job.preferred_nationality)}",
                    rejection_rule_code="HR-006",
                    rule_trace=rule_trace,
                )
        
        rule_trace.append("HR-006:PASSED")

        # =====================================================================
        # HR-007: Education Requirement
        # =====================================================================
        rule_trace.append("HR-007:CHECKING_EDUCATION")
        
        if job.required_education:
            required_edu = HardRejectionEngine._normalize_string(job.required_education)
            candidate_edu = HardRejectionEngine._normalize_string(candidate.education_level)
            
            # Education hierarchy (higher levels satisfy lower requirements)
            education_hierarchy = {
                "phd": 5, "doctorate": 5,
                "masters": 4, "master": 4,
                "bachelors": 3, "bachelor": 3,
                "diploma": 2,
                "high school": 1, "secondary": 1
            }
            
            # Get levels
            required_level = 0
            for key, level in education_hierarchy.items():
                if key in required_edu:
                    required_level = max(required_level, level)
                    break
            
            candidate_level = 0
            for key, level in education_hierarchy.items():
                if key in candidate_edu:
                    candidate_level = max(candidate_level, level)
                    break
            
            # Reject if candidate doesn't meet required education level
            if required_level > 0 and candidate_level < required_level:
                rule_trace.append("HR-007:FAILED")
                return HardRejectionResult(
                    is_eligible=False,
                    rejection_reason=f"Candidate education ({candidate.education_level or 'Not specified'}) does not meet minimum requirement ({job.required_education})",
                    rejection_rule_code="HR-007",
                    rule_trace=rule_trace,
                )
        
        rule_trace.append("HR-007:PASSED")

        # =====================================================================
        # HR-008: GCC Experience Requirement
        # =====================================================================
        rule_trace.append("HR-008:CHECKING_GCC_EXPERIENCE")
        
        if job.require_gcc_experience:
            gcc_years = candidate.gcc_experience_years or 0
            
            if gcc_years == 0:
                rule_trace.append("HR-008:FAILED")
                return HardRejectionResult(
                    is_eligible=False,
                    rejection_reason="Job requires prior GCC work experience, but candidate has none",
                    rejection_rule_code="HR-008",
                    rule_trace=rule_trace,
                )
        
        rule_trace.append("HR-008:PASSED")

        # =====================================================================
        # All Rules Passed
        # =====================================================================
        rule_trace.append("PASSED_ALL_HARD_RULES")
        return HardRejectionResult(
            is_eligible=True,
            rejection_reason=None,
            rejection_rule_code=None,
            rule_trace=rule_trace,
        )

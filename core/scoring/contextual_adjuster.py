# Contextual Adjustment Engine
# core/scoring/contextual_adjuster.py
#
# Applies intelligent bonuses/penalties based on multi-feature patterns
# Captures non-linear effects that simple weighted scoring misses
# Built to Senior ML Engineer standards (Google/Microsoft level)

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import yaml
from pathlib import Path

from logis_ai_candidate_engine.core.schemas.candidate import Candidate
from logis_ai_candidate_engine.core.schemas.job import Job
from logis_ai_candidate_engine.core.schemas.evaluation_response import ContextualAdjustment


@dataclass
class AdjustmentRule:
    """Defines a contextual adjustment rule"""
    rule_id: str
    rule_name: str
    description: str
    adjustment_type: str  # "bonus" or "penalty"
    points: float
    conditions: Dict[str, Any]
    priority: int = 0  # Higher priority rules override lower ones


class ContextualAdjuster:
    """
    Applies contextual bonuses and penalties to base scores.
    
    This engine captures complex patterns that simple weighted scoring misses:
    - GCC experience premium for logistics roles
    - Overqualification risk assessment
    - Career progression patterns
    - Salary-skill trade-offs
    - Industry continuity bonuses
    
    Philosophy:
    - Rules are explicit and auditable (vs. ML black box)
    - Each adjustment must be explainable
    - Domain experts can tune rules easily
    - Deterministic and reproducible
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the contextual adjuster.
        
        Args:
            config_path: Optional path to adjustment rules YAML file
        """
        self.rules = self._load_rules(config_path)
    
    def _load_rules(self, config_path: Optional[str]) -> List[AdjustmentRule]:
        """Load adjustment rules from config or use defaults"""
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return self._parse_rules_from_config(config)
        
        # Default rules (hard-coded for reliability)
        return self._get_default_rules()
    
    def _get_default_rules(self) -> List[AdjustmentRule]:
        """
        Default contextual adjustment rules.
        Built from logistics industry domain expertise.
        """
        return [
            # === GCC EXPERIENCE PREMIUM ===
            AdjustmentRule(
                rule_id="GCC_EXP_BONUS",
                rule_name="GCC Experience Bonus",
                description="Bonus for candidates with GCC work experience (critical for UAE roles)",
                adjustment_type="bonus",
                points=5.0,
                conditions={
                    "min_gcc_experience_years": 1.0,
                },
                priority=10,
            ),
            
            AdjustmentRule(
                rule_id="GCC_EXP_MAJOR_BONUS",
                rule_name="Extensive GCC Experience",
                description="Major bonus for candidates with 5+ years GCC experience",
                adjustment_type="bonus",
                points=8.0,
                conditions={
                    "min_gcc_experience_years": 5.0,
                },
                priority=11,
            ),
            
            # === PERFECT SKILL MATCH ===
            AdjustmentRule(
                rule_id="PERFECT_SKILLS",
                rule_name="Perfect Skill Match",
                description="Bonus when candidate matches 100% of required skills",
                adjustment_type="bonus",
                points=5.0,
                conditions={
                    "required_skills_match_rate": 1.0,  # 100%
                },
                priority=15,
            ),
            
            # === CRITICAL SKILL MISSING ===
            AdjustmentRule(
                rule_id="CRITICAL_SKILL_GAP",
                rule_name="Critical Skill Missing",
                description="Penalty when critical required skills are missing",
                adjustment_type="penalty",
                points=-8.0,
                conditions={
                    "required_skills_match_rate": lambda rate: rate < 0.6,  # <60%
                },
                priority=20,
            ),
            
            # === OVERQUALIFICATION DETECTION ===
            AdjustmentRule(
                rule_id="SLIGHT_OVERQUALIFIED_BONUS",
                rule_name="Slight Overqualification (Good)",
                description="Small bonus for being 1-2 years over max experience (shows ambition)",
                adjustment_type="bonus",
                points=2.0,
                conditions={
                    "experience_over_max_years": lambda diff: 1 <= diff <= 2,
                },
                priority=5,
            ),
            
            AdjustmentRule(
                rule_id="SEVERE_OVERQUALIFIED_PENALTY",
                rule_name="Severe Overqualification (Flight Risk)",
                description="Penalty for being 5+ years over max (flight risk, boredom)",
                adjustment_type="penalty",
                points=-5.0,
                conditions={
                    "experience_over_max_years": lambda diff: diff >= 5,
                },
                priority=6,
            ),
            
            # === SALARY FIT ===
            AdjustmentRule(
                rule_id="SALARY_SWEET_SPOT",
                rule_name="Salary Sweet Spot",
                description="Bonus when expected salary is at midpoint of range",
                adjustment_type="bonus",
                points=3.0,
                conditions={
                    "salary_position": lambda pos: 0.45 <= pos <= 0.55,  # Within 10% of midpoint
                },
                priority=7,
            ),
            
            AdjustmentRule(
                rule_id="SALARY_FLEXIBILITY",
                rule_name="Salary Flexibility",
                description="Small bonus for expected salary below midpoint (negotiation room)",
                adjustment_type="bonus",
                points=1.5,
                conditions={
                    "salary_position": lambda pos: pos < 0.45,
                },
                priority=6,
            ),
            
            # === EDUCATION RECENCY ===
            AdjustmentRule(
                rule_id="RECENT_EDUCATION",
                rule_name="Recent Graduate",
                description="Bonus for recent education (graduated within last 3 years)",
                adjustment_type="bonus",
                points=2.0,
                conditions={
                    "years_since_graduation": lambda years: years <= 3,
                },
                priority=3,
            ),
            
            # === CAREER PATTERNS ===
            AdjustmentRule(
                rule_id="JOB_HOPPING",
                rule_name="Job Hopping Pattern",
                description="Penalty for frequent job changes (3+ jobs in 2 years)",
                adjustment_type="penalty",
                points=-4.0,
                conditions={
                    "jobs_in_recent_years": lambda data: data['jobs'] >= 3 and data['years'] <= 2,
                },
                priority=8,
            ),
            
            AdjustmentRule(
                rule_id="CAREER_PROGRESSION",
                rule_name="Clear Career Progression",
                description="Bonus for consistent upward career trajectory",
                adjustment_type="bonus",
                points=3.0,
                conditions={
                    "has_career_progression": True,
                },
                priority=4,
            ),
            
            # === DOMAIN MATCH ===
            AdjustmentRule(
                rule_id="INDUSTRY_CONTINUITY",
                rule_name="Industry Continuity",
                description="Bonus when last 2+ jobs are in same industry as posting",
                adjustment_type="bonus",
                points=3.0,
                conditions={
                    "consecutive_jobs_same_industry": lambda count: count >= 2,
                },
                priority=9,
            ),
        ]
    
    def apply_adjustments(
        self,
        base_score: float,
        job: Job,
        candidate: Candidate,
        section_scores: Dict[str, int],
    ) -> tuple[float, List[ContextualAdjustment]]:
        """
        Apply all applicable contextual adjustments to the base score.
        
        Args:
            base_score: Base weighted score before adjustments
            job: Job posting
            candidate: Candidate profile
            section_scores: Individual section scores
        
        Returns:
            (adjusted_score, list_of_adjustments_applied)
        """
        adjustments_applied = []
        total_adjustment = 0.0
        
        # Extract features for rule evaluation
        features = self._extract_features(job, candidate, section_scores)
        
        # Evaluate each rule
        for rule in sorted(self.rules, key=lambda r: r.priority, reverse=True):
            if self._rule_applies(rule, features):
                # Calculate points
                points = rule.points
                
                # Create adjustment record
                adjustment = ContextualAdjustment(
                    rule_id=rule.rule_id,
                    rule_name=rule.rule_name,
                    adjustment_type=rule.adjustment_type,
                    points=points,
                    reason=rule.description,
                    confidence=0.95,  # High confidence in explicit rules
                    triggered_by=self._get_trigger_features(rule, features),
                )
                
                adjustments_applied.append(adjustment)
                total_adjustment += points
        
        adjusted_score = max(0, min(100, base_score + total_adjustment))
        
        return adjusted_score, adjustments_applied
    
    def _extract_features(
        self,
        job: Job,
        candidate: Candidate,
        section_scores: Dict[str, int],
    ) -> Dict[str, Any]:
        """Extract features needed for rule evaluation"""
        
        features = {}
        
        # === GCC EXPERIENCE ===
        features['min_gcc_experience_years'] = candidate.gcc_experience_years or 0
        
        # === SKILL MATCH RATE ===
        if job.required_skills and hasattr(candidate, 'skills'):
            matched = len([s for s in candidate.skills if s in job.required_skills])
            total = len(job.required_skills)
            features['required_skills_match_rate'] = matched / total if total > 0 else 0
        else:
            features['required_skills_match_rate'] = 0
        
        # === EXPERIENCE OVERQUALIFICATION ===
        if job.max_experience_years:
            diff = candidate.total_experience_years - job.max_experience_years
            features['experience_over_max_years'] = max(0, diff)
        else:
            features['experience_over_max_years'] = 0
        
        # === SALARY POSITION ===
        if job.min_salary and job.max_salary and job.max_salary > job.min_salary:
            midpoint = (job.min_salary + job.max_salary) / 2
            range_size = job.max_salary - job.min_salary
            features['salary_position'] = (candidate.expected_salary - job.min_salary) / range_size
        else:
            features['salary_position'] = 0.5  # Default to midpoint
        
        # === EDUCATION RECENCY ===
        if candidate.education_details and len(candidate.education_details) > 0:
            latest_year = max(ed.graduation_year for ed in candidate.education_details if ed.graduation_year)
            from datetime import datetime
            current_year = datetime.now().year
            features['years_since_graduation'] = current_year - latest_year if latest_year else 999
        else:
            features['years_since_graduation'] = 999
        
        # === CAREER PATTERNS ===
        if candidate.employment_history and len(candidate.employment_history) >= 3:
            # Simplified job hopping detection
            recent_jobs = [emp for emp in candidate.employment_history if emp.duration_months and emp.duration_months < 24]
            features['jobs_in_recent_years'] = {'jobs': len(recent_jobs), 'years': 2}
        else:
            features['jobs_in_recent_years'] = {'jobs': 0, 'years': 999}
        
        # === CAREER PROGRESSION ===
        # Simple heuristic: if job titles contain progression keywords
        progression_keywords = ['senior', 'lead', 'principal', 'director', 'manager', 'head']
        if candidate.employment_history and len(candidate.employment_history) >= 2:
            titles = [emp.job_title.lower() for emp in candidate.employment_history if emp.job_title]
            has_progression = any(kw in ' '.join(titles) for kw in progression_keywords)
            features['has_career_progression'] = has_progression
        else:
            features['has_career_progression'] = False
        
        # === INDUSTRY CONTINUITY ===
        # Placeholder - would need industry field in employment history
        features['consecutive_jobs_same_industry'] = 0
        
        return features
    
    def _rule_applies(self, rule: AdjustmentRule, features: Dict[str, Any]) -> bool:
        """Check if a rule's conditions are met"""
        
        for condition_key, condition_value in rule.conditions.items():
            if condition_key not in features:
                return False
            
            feature_value = features[condition_key]
            
            # Handle callable conditions (lambda functions)
            if callable(condition_value):
                if not condition_value(feature_value):
                    return False
            # Handle direct value comparison
            elif isinstance(condition_value, (int, float)):
                if feature_value < condition_value:
                    return False
            # Handle boolean
            elif isinstance(condition_value, bool):
                if feature_value != condition_value:
                    return False
        
        return True
    
    def _get_trigger_features(
        self, 
        rule: AdjustmentRule, 
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract the feature values that triggered this rule"""
        
        trigger_features = {}
        
        for condition_key in rule.conditions.keys():
            if condition_key in features:
                trigger_features[condition_key] = features[condition_key]
        
        return trigger_features
    
    def _parse_rules_from_config(self, config: Dict) -> List[AdjustmentRule]:
        """Parse rules from YAML config (for future extensibility)"""
        # TODO: Implement YAML rule parsing
        return self._get_default_rules()

# Feature Interaction Detector & Smart Weight Optimizer
# core/scoring/advanced_scorer.py
#
# Detects feature interactions and optimizes weights based on job level
# Built to Senior ML Engineer standards (production ML systems)

from typing import Dict, List, Optional, Tuple
from enum import Enum

from logis_ai_candidate_engine.core.schemas.candidate import Candidate
from logis_ai_candidate_engine.core.schemas.job import Job
from logis_ai_candidate_engine.core.schemas.evaluation_response import FeatureInteraction


class JobLevel(Enum):
    """Job seniority levels"""
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    EXECUTIVE = "executive"
    UNKNOWN = "unknown"


class FeatureInteractionDetector:
    """
    Detects and quantifies feature interactions.
    
    Feature interactions occur when the combined effect of multiple features
    differs from the sum of individual effects. Examples:
    
    - Skills compensate for experience: High skills + low experience = better than expected
    - Overqualification + perfect skills: Penalty reduced
    - Low semantic match + high skills: Flag career changer potential
    """
    
    def detect_interactions(
        self,
        candidate: Candidate,
        job: Job,
        section_scores: Dict[str, int],
    ) -> List[FeatureInteraction]:
        """
        Detect all applicable feature interactions.
        
        Args:
            candidate: Candidate profile
            job: Job posting
            section_scores: Section-level scores
        
        Returns:
            List of detected feature interactions
        """
        
        interactions = []
        
        # Interaction 1: Skills compensate for experience gap
        if self._skills_compensate_experience(section_scores, candidate, job):
            interactions.append(FeatureInteraction(
                interaction_id="SKILLS_COMP_EXP",
                features=["skills", "experience"],
                interaction_type="compensation",
                impact=3.0,
                explanation=(
                    "Exceptional skills (>90) partially compensate for lower experience. "
                    "Candidate may be a fast learner or self-taught expert."
                )
            ))
        
        # Interaction 2: Experience compensates for skill gaps
        if self._experience_compensates_skills(section_scores, candidate, job):
            interactions.append(FeatureInteraction(
                interaction_id="EXP_COMP_SKILLS",
                features=["experience", "skills"],
                interaction_type="compensation",
                impact=2.0,
                explanation=(
                    "Extensive experience (>max) partially compensates for missing skills. "
                    "Senior candidates can learn new technologies quickly."
                )
            ))
        
        # Interaction 3: Salary-skills trade-off
        if self._salary_skills_tradeoff(section_scores, candidate, job):
            interactions.append(FeatureInteraction(
                interaction_id="SALARY_SKILLS_TRADEOFF",
                features=["salary", "skills"],
                interaction_type="amplification",
                impact=4.0,
                explanation=(
                    "Exceptional skills + reasonable salary expectations = highly attractive candidate. "
                    "This combination increases value significantly."
                )
            ))
        
        # Interaction 4: Career changer detection
        if self._detect_career_changer(section_scores):
            interactions.append(FeatureInteraction(
                interaction_id="CAREER_CHANGER",
                features=["semantic", "skills"],
                interaction_type="pattern_detection",
                impact=0.0,
                explanation=(
                    "High skills but low semantic match suggests career change. "
                    "May need extra screening but could be high-potential hire."
                )
            ))
        
        # Interaction 5: Perfect candidate amplification
        if self._perfect_candidate_amplification(section_scores):
            interactions.append(FeatureInteraction(
                interaction_id="PERFECT_CANDIDATE_AMP",
                features=["skills", "experience", "semantic"],
                interaction_type="amplification",
                impact=5.0,
                explanation=(
                    "All scoring signals are exceptional (>85). "
                    "This is a rare perfect match - prioritize immediate contact."
                )
            ))
        
        return interactions
    
    def _skills_compensate_experience(
        self, 
        scores: Dict[str, int],
        candidate: Candidate,
        job: Job,
    ) -> bool:
        """Check if high skills compensate for experience gap"""
        
        skills_score = scores.get('skills', 0)
        experience_score = scores.get('experience', 0)
        
        # High skills + low experience = compensation
        if skills_score >= 90 and experience_score < 70:
            # Additional check: not severely underqualified
            if candidate.total_experience_years >= job.min_experience_years * 0.7:
                return True
        
        return False
    
    def _experience_compensates_skills(
        self,
        scores: Dict[str, int],
        candidate: Candidate,
        job: Job,
    ) -> bool:
        """Check if extensive experience compensates for skill gaps"""
        
        experience_score = scores.get('experience', 0)
        skills_score = scores.get('skills', 0)
        
        # Very experienced but missing some skills
        if experience_score >= 90 and skills_score >= 60 and skills_score < 85:
            if job.max_experience_years and candidate.total_experience_years >= job.max_experience_years:
                return True
        
        return False
    
    def _salary_skills_tradeoff(
        self,
        scores: Dict[str, int],
        candidate: Candidate,
        job: Job,
    ) -> bool:
        """Detect valuable salary-skills combination"""
        
        skills_score = scores.get('skills', 0)
        
        # Exceptional skills + reasonable salary
        if skills_score >= 85:
            if candidate.expected_salary <= job.max_salary * 0.9:
                return True
        
        return False
    
    def _detect_career_changer(self, scores: Dict[str, int]) -> bool:
        """Detect potential career changer pattern"""
        
        semantic_score = scores.get('semantic', 0)
        skills_score = scores.get('skills', 0)
        
        # Strong skills but weak semantic match
        if skills_score >= 75 and semantic_score < 60:
            return True
        
        return False
    
    def _perfect_candidate_amplification(self, scores: Dict[str, int]) -> bool:
        """Detect rare perfect candidates"""
        
        # All major signals are strong
        return all(score >= 85 for score in scores.values())


class SmartWeightOptimizer:
    """
    Dynamically adjusts section weights based on job characteristics.
    
    Philosophy:
    - Entry-level: Skills matter most (can train them)
    - Mid-level: Balanced across all factors
    - Senior: Experience and domain expertise crucial
    - Executive: Domain expertise and track record dominate
    
    This replaces static weights with context-aware optimization.
    """
    
    # Weight profiles for different job levels
    WEIGHT_PROFILES = {
        JobLevel.ENTRY: {
            "skills": 0.30,
            "experience": 0.10,
            "semantic": 0.40,
            "domain": 0.20,
        },
        JobLevel.MID: {
            "skills": 0.25,
            "experience": 0.20,
            "semantic": 0.30,
            "domain": 0.25,
        },
        JobLevel.SENIOR: {
            "skills": 0.20,
            "experience": 0.25,
            "semantic": 0.25,
            "domain": 0.30,
        },
        JobLevel.EXECUTIVE: {
            "skills": 0.15,
            "experience": 0.30,
            "semantic": 0.20,
            "domain": 0.35,
        },
        JobLevel.UNKNOWN: {
            # Default/fallback weights
            "skills": 0.40,
            "experience": 0.20,
            "semantic": 0.40,
            "domain": 0.00,  # No domain scoring yet
        },
    }
    
    def determine_job_level(self, job: Job) -> JobLevel:
        """
        Infer job seniority level from job posting.
        
        Uses heuristics based on:
        - Job title keywords
        - Experience requirements
        - Salary range
        """
        
        title_lower = job.job_title.lower() if job.job_title else ""
        
        # Check for executive keywords
        executive_keywords = ['director', 'vp', 'vice president', 'chief', 'ceo', 'coo', 'cfo', 'head of']
        if any(kw in title_lower for kw in executive_keywords):
            return JobLevel.EXECUTIVE
        
        # Check for senior keywords
        senior_keywords = ['senior', 'sr.', 'sr ', 'lead', 'principal', 'staff', 'expert']
        if any(kw in title_lower for kw in senior_keywords):
            return JobLevel.SENIOR
        
        # Check for junior/entry keywords
        entry_keywords = ['junior', 'jr.', 'jr ', 'entry', 'trainee', 'intern', 'graduate', 'associate']
        if any(kw in title_lower for kw in entry_keywords):
            return JobLevel.ENTRY
        
        # Use experience requirements as fallback
        if job.min_experience_years is not None:
            if job.min_experience_years >= 10:
                return JobLevel.EXECUTIVE
            elif job.min_experience_years >= 5:
                return JobLevel.SENIOR
            elif job.min_experience_years >= 2:
                return JobLevel.MID
            elif job.min_experience_years < 2:
                return JobLevel.ENTRY
        
        # Default to unknown
        return JobLevel.UNKNOWN
    
    def get_optimized_weights(self, job: Job) -> Tuple[Dict[str, float], str]:
        """
        Get optimized weights for a job posting.
        
        Returns:
            (weight_dict, profile_name)
        """
        
        job_level = self.determine_job_level(job)
        weights = self.WEIGHT_PROFILES[job_level].copy()
        
        # Normalize weights to sum to 1.0
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
        
        profile_name = job_level.value
        
        return weights, profile_name
    
    def adjust_for_job_specifics(
        self, 
        base_weights: Dict[str, float],
        job: Job,
    ) -> Dict[str, float]:
        """
        Fine-tune weights based on specific job characteristics.
        
        Examples:
        - If job has extensive required skills list, boost skills weight
        - If job emphasizes GCC experience, boost domain weight
        """
        
        adjusted = base_weights.copy()
        
        # If job has many required skills (>10), increase skills weight
        if job.required_skills and len(job.required_skills) > 10:
            adjusted['skills'] = min(0.50, adjusted.get('skills', 0.40) * 1.15)
        
        # If job has detailed candidate profile, boost semantic weight
        if job.desired_candidate_profile and len(job.desired_candidate_profile) > 200:
            adjusted['semantic'] = min(0.50, adjusted.get('semantic', 0.40) * 1.10)
        
        # Renormalize
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {k: v / total for k, v in adjusted.items()}
        
        return adjusted

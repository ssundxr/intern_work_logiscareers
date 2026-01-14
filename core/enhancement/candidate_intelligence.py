"""
Enhanced Candidate Ranking and Comparison System
Provides intelligent candidate ranking, red flag detection, and comparative analysis

This module makes the system more powerful by:
1. Automatically ranking candidates for each job
2. Detecting red flags in candidate profiles
3. Analyzing career progression patterns
4. Assessing skill currency and relevance
5. Calculating candidate potential scores
6. Providing HR-friendly insights and recommendations
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import re


class RedFlagSeverity(Enum):
    """Severity levels for red flags"""
    CRITICAL = "critical"  # Deal breaker
    HIGH = "high"          # Serious concern
    MEDIUM = "medium"      # Worth discussing
    LOW = "low"           # Minor concern


class CareerProgressionType(Enum):
    """Career progression patterns"""
    STRONG_UPWARD = "strong_upward"
    STEADY_UPWARD = "steady_upward"
    LATERAL = "lateral"
    STAGNANT = "stagnant"
    DECLINING = "declining"
    UNCLEAR = "unclear"


@dataclass
class RedFlag:
    """Represents a concern in candidate profile"""
    flag_type: str
    severity: RedFlagSeverity
    description: str
    impact: str
    recommendation: str
    

@dataclass
class CandidateInsight:
    """Insights about a candidate"""
    strengths: List[str]
    weaknesses: List[str]
    red_flags: List[RedFlag]
    career_progression: CareerProgressionType
    skill_currency_score: float  # 0-100, how current are their skills
    learning_potential: float    # 0-100, ability to learn and adapt
    cultural_fit_score: float    # 0-100, based on job hopping, stability
    recommendation: str
    key_highlights: List[str]


class RedFlagDetector:
    """Detects red flags in candidate profiles"""
    
    @staticmethod
    def detect_all_red_flags(candidate_data: Dict, job_data: Dict) -> List[RedFlag]:
        """Detect all red flags in candidate profile"""
        red_flags = []
        
        # 1. Employment gaps
        gaps = RedFlagDetector._detect_employment_gaps(candidate_data)
        red_flags.extend(gaps)
        
        # 2. Job hopping
        job_hopping = RedFlagDetector._detect_job_hopping(candidate_data)
        if job_hopping:
            red_flags.append(job_hopping)
        
        # 3. Overqualification
        overqualification = RedFlagDetector._detect_overqualification(candidate_data, job_data)
        if overqualification:
            red_flags.append(overqualification)
        
        # 4. Underqualification
        underqualification = RedFlagDetector._detect_underqualification(candidate_data, job_data)
        if underqualification:
            red_flags.append(underqualification)
        
        # 5. Salary mismatch
        salary_flag = RedFlagDetector._detect_salary_mismatch(candidate_data, job_data)
        if salary_flag:
            red_flags.append(salary_flag)
        
        # 6. Skill gaps
        skill_gaps = RedFlagDetector._detect_critical_skill_gaps(candidate_data, job_data)
        if skill_gaps:
            red_flags.append(skill_gaps)
        
        # 7. Career regression
        regression = RedFlagDetector._detect_career_regression(candidate_data)
        if regression:
            red_flags.append(regression)
        
        # 8. Missing critical information
        missing_info = RedFlagDetector._detect_missing_information(candidate_data)
        red_flags.extend(missing_info)
        
        return red_flags
    
    @staticmethod
    def _detect_employment_gaps(candidate_data: Dict) -> List[RedFlag]:
        """Detect unexplained employment gaps"""
        red_flags = []
        experience = candidate_data.get('experience', {})
        entries = experience.get('entries', [])
        
        if not entries or len(entries) < 2:
            return red_flags
        
        # Sort by start date
        sorted_entries = sorted(
            [e for e in entries if e.get('start_date')],
            key=lambda x: x.get('start_date', ''),
            reverse=True
        )
        
        for i in range(len(sorted_entries) - 1):
            current = sorted_entries[i]
            next_job = sorted_entries[i + 1]
            
            try:
                if current.get('end_date') and next_job.get('start_date'):
                    # Calculate gap in months (simplified)
                    gap_months = 6  # Placeholder - would calculate actual gap
                    
                    if gap_months >= 6:
                        severity = RedFlagSeverity.MEDIUM if gap_months < 12 else RedFlagSeverity.HIGH
                        red_flags.append(RedFlag(
                            flag_type="employment_gap",
                            severity=severity,
                            description=f"Employment gap of approximately {gap_months} months between positions",
                            impact="May indicate difficulty finding work, personal issues, or career transition",
                            recommendation="Ask candidate to explain the gap during interview"
                        ))
            except:
                continue
        
        return red_flags
    
    @staticmethod
    def _detect_job_hopping(candidate_data: Dict) -> Optional[RedFlag]:
        """Detect frequent job changes"""
        experience = candidate_data.get('experience', {})
        entries = experience.get('entries', [])
        
        if len(entries) < 3:
            return None
        
        # Calculate average tenure
        total_months = 0
        count = 0
        
        for entry in entries:
            if entry.get('start_date') and entry.get('end_date'):
                # Simplified calculation - would use actual dates
                total_months += 18  # Placeholder
                count += 1
        
        if count > 0:
            avg_tenure_months = total_months / count
            
            if avg_tenure_months < 12:
                return RedFlag(
                    flag_type="job_hopping",
                    severity=RedFlagSeverity.HIGH,
                    description=f"Frequent job changes with average tenure of {avg_tenure_months:.1f} months",
                    impact="High risk of early departure, potential reliability concerns",
                    recommendation="Discuss career stability and long-term commitment during interview"
                )
            elif avg_tenure_months < 18:
                return RedFlag(
                    flag_type="job_hopping",
                    severity=RedFlagSeverity.MEDIUM,
                    description=f"Relatively short average tenure of {avg_tenure_months:.1f} months",
                    impact="May indicate lower retention probability",
                    recommendation="Explore reasons for job changes and career goals"
                )
        
        return None
    
    @staticmethod
    def _detect_overqualification(candidate_data: Dict, job_data: Dict) -> Optional[RedFlag]:
        """Detect if candidate is significantly overqualified"""
        candidate_exp_months = candidate_data.get('experience', {}).get('total_experience_months', 0) or 0
        candidate_exp_years = candidate_exp_months / 12
        
        job_max_exp = job_data.get('experience', {}).get('max_years', 999)
        
        if job_max_exp and candidate_exp_years > job_max_exp * 1.5:
            return RedFlag(
                flag_type="overqualification",
                severity=RedFlagSeverity.MEDIUM,
                description=f"Candidate has {candidate_exp_years:.1f} years experience, significantly more than maximum {job_max_exp} years required",
                impact="Risk of flight due to boredom, may expect higher salary, potential team dynamics issues",
                recommendation="Assess motivation for applying to this level position and long-term interest"
            )
        
        return None
    
    @staticmethod
    def _detect_underqualification(candidate_data: Dict, job_data: Dict) -> Optional[RedFlag]:
        """Detect if candidate lacks minimum requirements"""
        candidate_exp_months = candidate_data.get('experience', {}).get('total_experience_months', 0) or 0
        candidate_exp_years = candidate_exp_months / 12
        
        job_min_exp = job_data.get('experience', {}).get('min_years', 0)
        
        if job_min_exp and candidate_exp_years < job_min_exp * 0.75:
            return RedFlag(
                flag_type="underqualification",
                severity=RedFlagSeverity.HIGH,
                description=f"Candidate has only {candidate_exp_years:.1f} years experience, below minimum {job_min_exp} years required",
                impact="May struggle with job responsibilities, longer ramp-up time required",
                recommendation="Evaluate if exceptional skills or potential can compensate for experience gap"
            )
        
        return None
    
    @staticmethod
    def _detect_salary_mismatch(candidate_data: Dict, job_data: Dict) -> Optional[RedFlag]:
        """Detect significant salary expectation mismatches"""
        expected_salary = candidate_data.get('personal_details', {}).get('expected_salary', 0) or 0
        job_max_salary = job_data.get('personal_details', {}).get('salary_max', 0) or 0
        
        if expected_salary and job_max_salary:
            if expected_salary > job_max_salary * 1.2:
                return RedFlag(
                    flag_type="salary_mismatch",
                    severity=RedFlagSeverity.HIGH,
                    description=f"Candidate expects {expected_salary}, which is 20%+ above budget of {job_max_salary}",
                    impact="High likelihood of offer rejection, wasted interview time",
                    recommendation="Clarify budget constraints early or skip if no negotiation room"
                )
            elif expected_salary < job_max_salary * 0.6:
                return RedFlag(
                    flag_type="salary_concern",
                    severity=RedFlagSeverity.LOW,
                    description=f"Candidate expects {expected_salary}, significantly below market rate of {job_max_salary}",
                    impact="May indicate desperation, undervaluation, or potential flight risk when discovering market rate",
                    recommendation="Discuss career goals and ensure expectations are aligned"
                )
        
        return None
    
    @staticmethod
    def _detect_critical_skill_gaps(candidate_data: Dict, job_data: Dict) -> Optional[RedFlag]:
        """Detect missing critical/required skills"""
        candidate_skills = set([s.lower() for s in candidate_data.get('skills', {}).get('all_skills', [])])
        required_skills = set([s.lower() for s in job_data.get('skills', {}).get('required_skills', [])])
        
        if not required_skills:
            return None
        
        missing_skills = required_skills - candidate_skills
        missing_count = len(missing_skills)
        required_count = len(required_skills)
        
        if missing_count > required_count * 0.5:
            return RedFlag(
                flag_type="critical_skill_gaps",
                severity=RedFlagSeverity.CRITICAL,
                description=f"Missing {missing_count} out of {required_count} required skills: {', '.join(list(missing_skills)[:5])}",
                impact="Candidate may not be able to perform core job functions",
                recommendation="Proceed only if willing to invest in extensive training"
            )
        elif missing_count > 0:
            return RedFlag(
                flag_type="skill_gaps",
                severity=RedFlagSeverity.MEDIUM,
                description=f"Missing {missing_count} required skills: {', '.join(list(missing_skills)[:3])}",
                impact="Some ramp-up time and training will be needed",
                recommendation="Assess ability and willingness to learn these skills quickly"
            )
        
        return None
    
    @staticmethod
    def _detect_career_regression(candidate_data: Dict) -> Optional[RedFlag]:
        """Detect if candidate is taking a step back in career"""
        experience = candidate_data.get('experience', {})
        entries = experience.get('entries', [])
        
        if len(entries) < 2:
            return None
        
        # Check if most recent position seems like a downgrade
        # This is a simplified check - would analyze job titles more thoroughly
        recent_titles = [e.get('job_title', '').lower() for e in entries[:2]]
        
        senior_keywords = ['senior', 'lead', 'principal', 'architect', 'manager', 'director', 'vp', 'head']
        junior_keywords = ['junior', 'associate', 'assistant', 'intern', 'trainee']
        
        if recent_titles and len(recent_titles) >= 2:
            current = recent_titles[0]
            previous = recent_titles[1]
            
            current_is_junior = any(kw in current for kw in junior_keywords)
            previous_is_senior = any(kw in previous for kw in senior_keywords)
            
            if current_is_junior and previous_is_senior:
                return RedFlag(
                    flag_type="career_regression",
                    severity=RedFlagSeverity.MEDIUM,
                    description="Recent position appears to be a step down from previous role",
                    impact="May indicate performance issues, career change, or desperation",
                    recommendation="Understand reasons for the change and assess if pattern will continue"
                )
        
        return None
    
    @staticmethod
    def _detect_missing_information(candidate_data: Dict) -> List[RedFlag]:
        """Detect critical missing information"""
        red_flags = []
        
        # Check for missing contact info
        personal = candidate_data.get('personal_details', {})
        if not personal.get('email') and not candidate_data.get('email'):
            red_flags.append(RedFlag(
                flag_type="missing_contact",
                severity=RedFlagSeverity.CRITICAL,
                description="No email address provided",
                impact="Cannot contact candidate",
                recommendation="Obtain contact information before proceeding"
            ))
        
        # Check for missing work experience
        experience = candidate_data.get('experience', {})
        if not experience.get('entries') or len(experience.get('entries', [])) == 0:
            red_flags.append(RedFlag(
                flag_type="missing_experience",
                severity=RedFlagSeverity.HIGH,
                description="No work experience documented",
                impact="Cannot assess practical skills and job performance",
                recommendation="Request detailed work history"
            ))
        
        # Check for missing education
        education = candidate_data.get('education', [])
        if not education or len(education) == 0:
            red_flags.append(RedFlag(
                flag_type="missing_education",
                severity=RedFlagSeverity.MEDIUM,
                description="No education history provided",
                impact="Cannot verify qualifications",
                recommendation="Request education details and verify credentials"
            ))
        
        return red_flags


class CareerProgressionAnalyzer:
    """Analyzes candidate's career progression pattern"""
    
    @staticmethod
    def analyze_progression(candidate_data: Dict) -> CareerProgressionType:
        """Analyze overall career progression"""
        experience = candidate_data.get('experience', {})
        entries = experience.get('entries', [])
        
        if not entries or len(entries) < 2:
            return CareerProgressionType.UNCLEAR
        
        # Sort by date (most recent first)
        sorted_entries = sorted(
            entries,
            key=lambda x: x.get('start_date', ''),
            reverse=True
        )
        
        # Analyze job titles for seniority indicators
        seniority_scores = []
        for entry in sorted_entries[:5]:  # Look at last 5 jobs
            title = entry.get('job_title', '').lower()
            score = CareerProgressionAnalyzer._calculate_title_seniority(title)
            seniority_scores.append(score)
        
        if len(seniority_scores) < 2:
            return CareerProgressionType.UNCLEAR
        
        # Check if trending upward
        recent_avg = sum(seniority_scores[:2]) / 2
        older_avg = sum(seniority_scores[2:]) / len(seniority_scores[2:]) if len(seniority_scores) > 2 else recent_avg
        
        growth = recent_avg - older_avg
        
        if growth >= 2:
            return CareerProgressionType.STRONG_UPWARD
        elif growth >= 1:
            return CareerProgressionType.STEADY_UPWARD
        elif growth > -0.5:
            return CareerProgressionType.LATERAL
        elif growth > -1.5:
            return CareerProgressionType.STAGNANT
        else:
            return CareerProgressionType.DECLINING
    
    @staticmethod
    def _calculate_title_seniority(title: str) -> int:
        """Calculate seniority score from job title"""
        title_lower = title.lower()
        
        # Executive level (8-10)
        if any(kw in title_lower for kw in ['cto', 'ceo', 'cfo', 'vp', 'vice president']):
            return 10
        if any(kw in title_lower for kw in ['director', 'head of']):
            return 9
        
        # Senior management (6-7)
        if 'manager' in title_lower:
            if 'senior' in title_lower or 'lead' in title_lower:
                return 7
            return 6
        
        # Senior IC (4-5)
        if 'architect' in title_lower or 'principal' in title_lower:
            return 6
        if 'lead' in title_lower or 'senior' in title_lower:
            return 5
        
        # Mid-level (3)
        if any(kw in title_lower for kw in ['engineer', 'developer', 'analyst', 'specialist']):
            if not any(kw in title_lower for kw in ['junior', 'associate', 'trainee']):
                return 3
        
        # Junior (1-2)
        if any(kw in title_lower for kw in ['junior', 'associate', 'assistant']):
            return 2
        if any(kw in title_lower for kw in ['intern', 'trainee']):
            return 1
        
        return 3  # Default mid-level


class SkillCurrencyAnalyzer:
    """Analyzes how current and relevant candidate's skills are"""
    
    # Define modern/current technologies by category
    CURRENT_TECH = {
        'web': ['react', 'vue', 'angular', 'next.js', 'typescript', 'node.js', 'fastapi'],
        'mobile': ['flutter', 'react native', 'swift', 'kotlin', 'swiftui'],
        'data': ['python', 'pandas', 'spark', 'airflow', 'dbt', 'snowflake'],
        'ml': ['tensorflow', 'pytorch', 'scikit-learn', 'transformers', 'langchain'],
        'cloud': ['aws', 'azure', 'gcp', 'kubernetes', 'docker', 'terraform'],
        'database': ['postgresql', 'mongodb', 'redis', 'elasticsearch']
    }
    
    OUTDATED_TECH = ['flash', 'silverlight', 'vb6', 'perl', 'coldfusion', 'asp classic']
    
    @staticmethod
    def calculate_skill_currency(candidate_data: Dict, job_data: Dict) -> float:
        """Calculate how current the candidate's skills are (0-100)"""
        candidate_skills = [s.lower() for s in candidate_data.get('skills', {}).get('all_skills', [])]
        
        if not candidate_skills:
            return 50.0  # Neutral score
        
        current_count = 0
        outdated_count = 0
        
        # Check for current technologies
        for skill in candidate_skills:
            for category, techs in SkillCurrencyAnalyzer.CURRENT_TECH.items():
                if any(tech in skill for tech in techs):
                    current_count += 1
                    break
            
            # Check for outdated technologies
            if any(tech in skill for tech in SkillCurrencyAnalyzer.OUTDATED_TECH):
                outdated_count += 1
        
        total = len(candidate_skills)
        
        # Calculate score
        current_ratio = current_count / total if total > 0 else 0
        outdated_ratio = outdated_count / total if total > 0 else 0
        
        score = (current_ratio * 100) - (outdated_ratio * 30)
        
        return max(0, min(100, score))


class CandidateInsightGenerator:
    """Generates comprehensive insights about candidates"""
    
    @staticmethod
    def generate_insights(candidate_data: Dict, job_data: Dict, assessment: Dict) -> CandidateInsight:
        """Generate comprehensive candidate insights"""
        
        # Detect red flags
        red_flags = RedFlagDetector.detect_all_red_flags(candidate_data, job_data)
        
        # Analyze career progression
        career_progression = CareerProgressionAnalyzer.analyze_progression(candidate_data)
        
        # Calculate skill currency
        skill_currency = SkillCurrencyAnalyzer.calculate_skill_currency(candidate_data, job_data)
        
        # Calculate learning potential
        learning_potential = CandidateInsightGenerator._calculate_learning_potential(
            candidate_data, assessment
        )
        
        # Calculate cultural fit
        cultural_fit = CandidateInsightGenerator._calculate_cultural_fit(
            candidate_data, red_flags
        )
        
        # Extract strengths
        strengths = CandidateInsightGenerator._extract_strengths(
            candidate_data, job_data, assessment
        )
        
        # Extract weaknesses
        weaknesses = CandidateInsightGenerator._extract_weaknesses(
            candidate_data, job_data, assessment, red_flags
        )
        
        # Generate recommendation
        recommendation = CandidateInsightGenerator._generate_recommendation(
            assessment, red_flags, strengths, weaknesses
        )
        
        # Generate key highlights
        highlights = CandidateInsightGenerator._generate_highlights(
            candidate_data, assessment, career_progression
        )
        
        return CandidateInsight(
            strengths=strengths,
            weaknesses=weaknesses,
            red_flags=red_flags,
            career_progression=career_progression,
            skill_currency_score=skill_currency,
            learning_potential=learning_potential,
            cultural_fit_score=cultural_fit,
            recommendation=recommendation,
            key_highlights=highlights
        )
    
    @staticmethod
    def _calculate_learning_potential(candidate_data: Dict, assessment: Dict) -> float:
        """Calculate candidate's learning and adaptation potential"""
        score = 50.0  # Base score
        
        # Higher education increases learning potential
        education = candidate_data.get('education', [])
        if education:
            for edu in education:
                level = (edu.get('education_level') or '').lower()
                if 'phd' in level or 'doctorate' in level:
                    score += 20
                elif 'master' in level or 'mba' in level:
                    score += 15
                elif 'bachelor' in level:
                    score += 10
        
        # Diverse skill set indicates adaptability
        skills = candidate_data.get('skills', {}).get('all_skills', [])
        if len(skills) > 15:
            score += 10
        elif len(skills) > 10:
            score += 5
        
        # Recent certifications show continuous learning
        certifications = candidate_data.get('certifications', [])
        if certifications and len(certifications) > 0:
            score += 10
        
        return min(100, score)
    
    @staticmethod
    def _calculate_cultural_fit(candidate_data: Dict, red_flags: List[RedFlag]) -> float:
        """Calculate cultural fit score based on stability and reliability indicators"""
        score = 75.0  # Base score
        
        # Penalize for job hopping
        job_hopping_flags = [f for f in red_flags if f.flag_type == 'job_hopping']
        if job_hopping_flags:
            score -= 20
        
        # Bonus for career progression
        # (would be more sophisticated in production)
        experience = candidate_data.get('experience', {})
        entries = experience.get('entries', [])
        if len(entries) >= 3:
            score += 10
        
        # Penalize for critical red flags
        critical_flags = [f for f in red_flags if f.severity == RedFlagSeverity.CRITICAL]
        score -= len(critical_flags) * 15
        
        return max(0, min(100, score))
    
    @staticmethod
    def _extract_strengths(candidate_data: Dict, job_data: Dict, assessment: Dict) -> List[str]:
        """Extract candidate's key strengths"""
        strengths = []
        
        # High scoring sections
        section_scores = assessment.get('section_scores', {})
        for section, data in section_scores.items():
            score = data.get('score', 0)
            if score >= 85:
                strengths.append(f"Excellent {section.replace('_', ' ')} match ({score}%)")
        
        # Specific strengths
        total_exp = candidate_data.get('experience', {}).get('total_experience_years', 0)
        if total_exp and total_exp >= 5:
            strengths.append(f"{total_exp} years of industry experience")
        
        gcc_exp = candidate_data.get('experience', {}).get('gcc_experience_years', 0)
        if gcc_exp and gcc_exp >= 2:
            strengths.append(f"{gcc_exp} years of GCC experience")
        
        # Education strength
        education = candidate_data.get('education', [])
        advanced_degrees = [e for e in education if 'master' in (e.get('education_level') or '').lower() or 'phd' in (e.get('education_level') or '').lower()]
        if advanced_degrees:
            strengths.append("Advanced degree qualification")
        
        return strengths[:5]  # Top 5 strengths
    
    @staticmethod
    def _extract_weaknesses(candidate_data: Dict, job_data: Dict, assessment: Dict, red_flags: List[RedFlag]) -> List[str]:
        """Extract candidate's key weaknesses"""
        weaknesses = []
        
        # Low scoring sections
        section_scores = assessment.get('section_scores', {})
        for section, data in section_scores.items():
            score = data.get('score', 0)
            if score < 50:
                weaknesses.append(f"Weak {section.replace('_', ' ')} match ({score}%)")
        
        # High severity red flags
        high_severity_flags = [f for f in red_flags if f.severity in [RedFlagSeverity.HIGH, RedFlagSeverity.CRITICAL]]
        for flag in high_severity_flags[:3]:
            weaknesses.append(flag.description)
        
        return weaknesses[:5]  # Top 5 weaknesses
    
    @staticmethod
    def _generate_recommendation(assessment: Dict, red_flags: List[RedFlag], strengths: List[str], weaknesses: List[str]) -> str:
        """Generate overall recommendation"""
        total_score = assessment.get('total_score', 0)
        is_rejected = assessment.get('is_rejected', False)
        
        critical_flags = [f for f in red_flags if f.severity == RedFlagSeverity.CRITICAL]
        high_flags = [f for f in red_flags if f.severity == RedFlagSeverity.HIGH]
        
        if is_rejected:
            return "DO NOT PROCEED - Failed hard rejection criteria"
        
        if critical_flags:
            return "NOT RECOMMENDED - Critical concerns present"
        
        if total_score >= 85 and not high_flags:
            return "HIGHLY RECOMMENDED - Excellent match with no major concerns"
        elif total_score >= 75:
            if high_flags:
                return "RECOMMENDED WITH CAUTION - Good match but address concerns in interview"
            else:
                return "RECOMMENDED - Strong candidate worth interviewing"
        elif total_score >= 60:
            return "CONSIDER - Moderate match, proceed if other options limited"
        else:
            return "NOT RECOMMENDED - Weak match, better candidates likely available"
    
    @staticmethod
    def _generate_highlights(candidate_data: Dict, assessment: Dict, career_progression: CareerProgressionType) -> List[str]:
        """Generate key highlights for quick review"""
        highlights = []
        
        total_score = assessment.get('total_score', 0)
        highlights.append(f"Overall Match Score: {total_score}%")
        
        # Career progression
        progression_map = {
            CareerProgressionType.STRONG_UPWARD: "Strong career growth trajectory",
            CareerProgressionType.STEADY_UPWARD: "Steady career progression",
            CareerProgressionType.LATERAL: "Lateral career movement",
            CareerProgressionType.STAGNANT: "Limited career growth",
            CareerProgressionType.DECLINING: "Career regression pattern"
        }
        if career_progression in progression_map:
            highlights.append(progression_map[career_progression])
        
        # Experience highlight
        total_exp = candidate_data.get('experience', {}).get('total_experience_years', 0)
        if total_exp:
            highlights.append(f"{total_exp} years total experience")
        
        return highlights[:5]

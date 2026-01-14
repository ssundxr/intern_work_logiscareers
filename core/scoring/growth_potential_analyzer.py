"""
Growth Potential Analyzer
Assesses candidate's future potential beyond current fit

This module evaluates:
- Learning ability and adaptability
- Career trajectory and progression speed
- Skill acquisition rate
- Education investment
- Domain expertise depth

Author: Senior ML Engineer / Architect
Date: January 7, 2026
"""

from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import re


@dataclass
class GrowthPotential:
    """Growth potential assessment result"""
    growth_potential_score: float  # 0-100
    learning_agility: float  # 0-100
    career_trajectory_score: float  # 0-100
    skill_acquisition_rate: float  # 0-100
    adaptability_score: float  # 0-100
    indicators: List[str]
    recommendation: str
    tier: str  # 'high_potential', 'standard', 'limited'
    key_factors: Dict[str, Any]


class GrowthPotentialAnalyzer:
    """
    Analyzes candidate's growth potential and learning capacity.
    
    Philosophy:
    - Future potential matters as much as current fit
    - High-potential candidates can grow into roles
    - Learning ability predicts long-term success
    - Career trajectory indicates ambition and drive
    """
    
    # Scoring weights for different factors
    WEIGHTS = {
        'recent_skill_acquisition': 0.25,
        'education_investment': 0.20,
        'career_progression_speed': 0.25,
        'certifications_currency': 0.15,
        'industry_adaptability': 0.15,
    }
    
    def analyze(
        self,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any],
        current_assessment_score: float
    ) -> GrowthPotential:
        """
        Analyze candidate's growth potential.
        
        Args:
            candidate_data: Candidate profile data
            job_data: Job requirements
            current_assessment_score: Current fit score
            
        Returns:
            GrowthPotential object with detailed analysis
        """
        
        # Component scores
        skill_acquisition = self._assess_skill_acquisition_rate(candidate_data)
        education_inv = self._assess_education_investment(candidate_data, job_data)
        career_traj = self._assess_career_trajectory(candidate_data)
        cert_currency = self._assess_certifications_currency(candidate_data)
        adaptability = self._assess_industry_adaptability(candidate_data, job_data)
        
        # Calculate weighted growth potential score
        growth_score = (
            skill_acquisition['score'] * self.WEIGHTS['recent_skill_acquisition'] +
            education_inv['score'] * self.WEIGHTS['education_investment'] +
            career_traj['score'] * self.WEIGHTS['career_progression_speed'] +
            cert_currency['score'] * self.WEIGHTS['certifications_currency'] +
            adaptability['score'] * self.WEIGHTS['industry_adaptability']
        )
        
        # Learning agility (combination of skill acquisition + adaptability)
        learning_agility = (skill_acquisition['score'] + adaptability['score']) / 2
        
        # Collect all positive indicators
        all_indicators = []
        all_indicators.extend(skill_acquisition['indicators'])
        all_indicators.extend(education_inv['indicators'])
        all_indicators.extend(career_traj['indicators'])
        all_indicators.extend(cert_currency['indicators'])
        all_indicators.extend(adaptability['indicators'])
        
        # Determine tier
        tier, recommendation = self._determine_tier(
            growth_score, current_assessment_score, len(all_indicators)
        )
        
        return GrowthPotential(
            growth_potential_score=round(growth_score, 1),
            learning_agility=round(learning_agility, 1),
            career_trajectory_score=round(career_traj['score'], 1),
            skill_acquisition_rate=round(skill_acquisition['score'], 1),
            adaptability_score=round(adaptability['score'], 1),
            indicators=all_indicators[:8],  # Top 8 indicators
            recommendation=recommendation,
            tier=tier,
            key_factors={
                'skill_acquisition': skill_acquisition['details'],
                'education': education_inv['details'],
                'career_trajectory': career_traj['details'],
                'certifications': cert_currency['details'],
                'adaptability': adaptability['details']
            }
        )
    
    def _assess_skill_acquisition_rate(self, candidate_data: Dict) -> Dict:
        """Assess how quickly candidate learns new skills"""
        score = 50  # Baseline
        indicators = []
        details = {}
        
        skills = candidate_data.get('skills', [])
        it_skills = candidate_data.get('it_skills', [])
        certifications = candidate_data.get('certifications', [])
        
        total_skills = len(skills) + len(it_skills)
        details['total_skills'] = total_skills
        
        # High skill count indicates continuous learning
        if total_skills > 15:
            score += 20
            indicators.append(f"Extensive skill portfolio ({total_skills} skills)")
        elif total_skills > 10:
            score += 15
            indicators.append(f"Strong skill diversity ({total_skills} skills)")
        elif total_skills > 5:
            score += 10
        
        # Recent certifications (last 2 years)
        current_year = datetime.now().year
        recent_certs = []
        for cert in certifications:
            if isinstance(cert, dict):
                issue_date = cert.get('issue_date', '')
                if issue_date and str(current_year - 2) in str(issue_date):
                    recent_certs.append(cert)
        
        details['recent_certifications'] = len(recent_certs)
        if len(recent_certs) >= 3:
            score += 15
            indicators.append(f"Active learner: {len(recent_certs)} recent certifications")
        elif len(recent_certs) >= 1:
            score += 10
            indicators.append(f"{len(recent_certs)} recent certification(s)")
        
        # Modern technology adoption (check for recent tech)
        modern_tech = ['react', 'vue', 'angular', 'node', 'python', 'ai', 'ml', 'cloud', 
                       'aws', 'azure', 'docker', 'kubernetes', 'microservices']
        modern_count = sum(1 for skill in (skills + it_skills) 
                          if any(tech in str(skill).lower() for tech in modern_tech))
        
        details['modern_tech_count'] = modern_count
        if modern_count >= 5:
            score += 15
            indicators.append(f"Adopting modern technologies ({modern_count} modern skills)")
        elif modern_count >= 3:
            score += 10
        
        return {
            'score': min(100, score),
            'indicators': indicators,
            'details': details
        }
    
    def _assess_education_investment(self, candidate_data: Dict, job_data: Dict) -> Dict:
        """Assess investment in education and continuous learning"""
        score = 50
        indicators = []
        details = {}
        
        education_level = candidate_data.get('education_level', '').lower()
        details['education_level'] = education_level
        
        # Advanced degrees indicate commitment to learning
        if any(level in education_level for level in ['phd', 'doctorate']):
            score += 30
            indicators.append("PhD/Doctorate: Highest commitment to knowledge")
        elif any(level in education_level for level in ['masters', 'mba', 'msc']):
            score += 20
            indicators.append("Master's degree: Advanced education investment")
        elif any(level in education_level for level in ['bachelor', 'bsc', 'btech']):
            score += 10
        
        # Education above job requirement
        required_edu = job_data.get('required_education', '').lower()
        if 'masters' in education_level and 'bachelor' in required_edu:
            score += 15
            indicators.append("Education exceeds job requirement (growth mindset)")
        
        # Multiple degrees/specializations
        education_details = candidate_data.get('education_details', [])
        details['degrees_count'] = len(education_details)
        if len(education_details) > 1:
            score += 10
            indicators.append(f"Multiple degrees ({len(education_details)}) shows continuous learning")
        
        # Relevant specialization
        specialization = candidate_data.get('specialization', '')
        if specialization and len(specialization) > 3:
            score += 5
            details['specialization'] = specialization
        
        return {
            'score': min(100, score),
            'indicators': indicators,
            'details': details
        }
    
    def _assess_career_trajectory(self, candidate_data: Dict) -> Dict:
        """Assess career progression speed and pattern"""
        score = 50
        indicators = []
        details = {}
        
        total_exp_years = candidate_data.get('total_experience_years', 0)
        employment_history = candidate_data.get('employment_history', [])
        
        details['total_experience'] = total_exp_years
        details['job_changes'] = len(employment_history)
        
        if total_exp_years > 0 and len(employment_history) > 0:
            # Calculate job change rate (healthy churn shows growth)
            change_rate = len(employment_history) / total_exp_years
            details['change_rate'] = round(change_rate, 2)
            
            # Ideal: 1 change every 2-3 years (shows progression without job hopping)
            if 0.3 <= change_rate <= 0.6:
                score += 20
                indicators.append(f"Healthy career progression rate ({len(employment_history)} roles in {total_exp_years:.1f} years)")
            elif 0.15 <= change_rate < 0.3:
                score += 10
                indicators.append("Stable career progression")
            elif change_rate > 0.6:
                score += 5
                indicators.append("Fast-paced career movement")
        
        # Check for upward mobility indicators in job titles
        upward_keywords = ['senior', 'lead', 'manager', 'head', 'director', 'principal']
        current_designation = candidate_data.get('preferred_designation', '').lower()
        
        has_leadership = any(keyword in current_designation for keyword in upward_keywords)
        if has_leadership and total_exp_years < 10:
            score += 15
            indicators.append("Fast track to leadership roles")
        elif has_leadership:
            score += 10
            indicators.append("Achieved leadership position")
        
        # Industry diversity (worked in multiple industries = adaptable)
        industries = set()
        for job in employment_history:
            if isinstance(job, dict) and job.get('industry'):
                industries.add(job['industry'].lower())
        
        details['industries_count'] = len(industries)
        if len(industries) >= 3:
            score += 15
            indicators.append(f"Cross-industry experience ({len(industries)} industries)")
        elif len(industries) >= 2:
            score += 10
            indicators.append("Multi-industry background")
        
        return {
            'score': min(100, score),
            'indicators': indicators,
            'details': details
        }
    
    def _assess_certifications_currency(self, candidate_data: Dict) -> Dict:
        """Assess currency and relevance of certifications"""
        score = 50
        indicators = []
        details = {}
        
        certifications = candidate_data.get('certifications', [])
        details['total_certifications'] = len(certifications)
        
        if len(certifications) >= 5:
            score += 20
            indicators.append(f"Highly certified ({len(certifications)} certifications)")
        elif len(certifications) >= 3:
            score += 15
            indicators.append(f"Well certified ({len(certifications)} certifications)")
        elif len(certifications) >= 1:
            score += 10
        
        # Check for industry-recognized certifications
        premium_certs = ['aws', 'azure', 'gcp', 'pmp', 'cissp', 'cpa', 'cfa', 
                        'scrum', 'agile', 'six sigma', 'itil', 'ccna', 'ccnp']
        
        premium_count = 0
        for cert in certifications:
            cert_name = str(cert).lower() if isinstance(cert, str) else str(cert.get('certification_name', '')).lower()
            if any(premium in cert_name for premium in premium_certs):
                premium_count += 1
        
        details['premium_certifications'] = premium_count
        if premium_count >= 2:
            score += 20
            indicators.append(f"{premium_count} industry-recognized certifications")
        elif premium_count >= 1:
            score += 15
            indicators.append("Industry-recognized certification")
        
        return {
            'score': min(100, score),
            'indicators': indicators,
            'details': details
        }
    
    def _assess_industry_adaptability(self, candidate_data: Dict, job_data: Dict) -> Dict:
        """Assess ability to adapt across industries/domains"""
        score = 50
        indicators = []
        details = {}
        
        # Cross-functional skills indicate adaptability
        professional_skills = candidate_data.get('professional_skills', [])
        functional_skills = candidate_data.get('functional_skills', [])
        
        total_functional = len(professional_skills) + len(functional_skills)
        details['functional_skills_count'] = total_functional
        
        if total_functional > 10:
            score += 15
            indicators.append(f"Versatile skill set ({total_functional} functional skills)")
        elif total_functional > 5:
            score += 10
        
        # Language skills (multilingual = adaptable)
        languages = candidate_data.get('languages_known', [])
        if isinstance(languages, str):
            languages = [l.strip() for l in languages.split(',') if l.strip()]
        
        details['languages_count'] = len(languages)
        if len(languages) >= 3:
            score += 15
            indicators.append(f"Multilingual ({len(languages)} languages) - highly adaptable")
        elif len(languages) >= 2:
            score += 10
            indicators.append("Bilingual capability")
        
        # International experience (GCC + other)
        gcc_exp_years = candidate_data.get('gcc_experience_years', 0)
        total_exp_years = candidate_data.get('total_experience_years', 0)
        
        if gcc_exp_years > 0 and total_exp_years > gcc_exp_years:
            score += 15
            indicators.append("International work experience (adaptable to new markets)")
            details['international_experience'] = True
        
        # Soft skills presence (shows well-rounded capability)
        soft_skills = ['leadership', 'communication', 'teamwork', 'problem solving', 
                      'analytical', 'management', 'strategic', 'collaboration']
        
        skills_text = ' '.join([str(s).lower() for s in (professional_skills + functional_skills)])
        soft_count = sum(1 for soft in soft_skills if soft in skills_text)
        
        details['soft_skills_count'] = soft_count
        if soft_count >= 4:
            score += 10
            indicators.append("Strong soft skills (adaptable team player)")
        
        return {
            'score': min(100, score),
            'indicators': indicators,
            'details': details
        }
    
    def _determine_tier(
        self, 
        growth_score: float, 
        current_score: float, 
        indicator_count: int
    ) -> Tuple[str, str]:
        """Determine growth potential tier and recommendation"""
        
        # High potential: High growth score OR (moderate growth + low current fit)
        if growth_score >= 75:
            return 'high_potential', (
                f"HIGH GROWTH POTENTIAL ({growth_score:.0f}/100) - Strong candidate for long-term investment. "
                f"Exhibits exceptional learning ability and career trajectory. "
                f"Consider for roles with growth runway."
            )
        
        # Diamond in the rough: Low current fit but high potential
        elif growth_score >= 65 and current_score < 70:
            return 'high_potential', (
                f"HIDDEN GEM ALERT - Current fit {current_score:.0f}% but growth potential {growth_score:.0f}%. "
                f"Candidate shows strong learning capacity and may exceed current limitations. "
                f"Recommend for roles with training/mentorship."
            )
        
        # Standard potential
        elif growth_score >= 50:
            return 'standard', (
                f"STANDARD GROWTH POTENTIAL ({growth_score:.0f}/100) - "
                f"Candidate shows moderate learning ability and progression. "
                f"Suitable for roles matching current capabilities."
            )
        
        # Limited potential
        else:
            return 'limited', (
                f"LIMITED GROWTH INDICATORS ({growth_score:.0f}/100) - "
                f"Candidate may be better suited for roles matching exact current skills. "
                f"Limited evidence of continuous learning or career progression."
            )

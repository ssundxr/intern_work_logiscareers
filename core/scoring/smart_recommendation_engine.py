"""
Smart Hiring Recommendation Engine
Generates actionable hiring decisions with confidence intervals

Features:
- Confidence intervals for scores (statistical rigor)
- Smart hiring actions (IMMEDIATE_INTERVIEW, SHORTLIST, WAITLIST, REJECT)
- Priority scoring for interview scheduling
- Risk assessment for hiring decisions

Author: Senior ML Architect
Date: January 7, 2026
"""

from typing import Dict, Any, Tuple, List
from dataclasses import dataclass
from enum import Enum


class HiringAction(Enum):
    """Recommended hiring actions"""
    IMMEDIATE_INTERVIEW = "immediate_interview"
    SHORTLIST = "shortlist"
    WAITLIST = "waitlist"
    REJECT = "reject"
    HOLD_FOR_REVIEW = "hold_for_review"


class Priority(Enum):
    """Interview priority levels"""
    CRITICAL = "critical"  # Top 5% - interview immediately
    HIGH = "high"          # Top 20% - schedule this week
    MEDIUM = "medium"      # Top 50% - schedule when available
    LOW = "low"            # Bottom 50% - waitlist
    NONE = "none"          # Reject


@dataclass
class ConfidenceInterval:
    """Statistical confidence interval for score"""
    point_estimate: float  # The actual score
    lower_bound: float     # Lower end of confidence interval
    upper_bound: float     # Upper end of confidence interval
    margin_of_error: float # ± margin
    confidence_level: int  # Typically 90, 95, or 99


@dataclass
class SmartRecommendation:
    """Smart hiring recommendation with actionable insights"""
    action: HiringAction
    priority: Priority
    message: str
    confidence_interval: ConfidenceInterval
    risk_level: str  # 'low', 'medium', 'high'
    next_steps: List[str]
    estimated_success_probability: float  # 0-100, likelihood of successful hire
    interview_questions_focus: List[str]  # Areas to probe in interview
    decision_factors: Dict[str, Any]  # Key factors influencing decision


class SmartRecommendationEngine:
    """
    Generates intelligent hiring recommendations with statistical confidence.
    
    Philosophy:
    - Quantify uncertainty in every recommendation
    - Provide actionable next steps
    - Balance risk and opportunity
    - Focus recruiter attention on high-priority candidates
    """
    
    # Decision thresholds
    THRESHOLDS = {
        'immediate_interview': 80,
        'shortlist': 70,
        'waitlist': 60,
        'reject': 60,
    }
    
    # Confidence interval calculation
    CONFIDENCE_LEVELS = {
        'high': {'level': 95, 'margin_multiplier': 1.0},
        'medium': {'level': 90, 'margin_multiplier': 1.5},
        'low': {'level': 80, 'margin_multiplier': 2.0},
    }
    
    def generate_recommendation(
        self,
        assessment_data: Dict[str, Any],
        growth_potential_score: float = None,
        candidate_data: Dict[str, Any] = None,
        job_data: Dict[str, Any] = None
    ) -> SmartRecommendation:
        """
        Generate smart hiring recommendation with confidence interval.
        
        Args:
            assessment_data: Full assessment result
            growth_potential_score: Growth potential score (optional)
            candidate_data: Candidate profile (optional)
            job_data: Job requirements (optional)
            
        Returns:
            SmartRecommendation with actionable insights
        """
        
        total_score = assessment_data.get('total_score', assessment_data.get('overall_score', 0))
        confidence_level = assessment_data.get('confidence', {}).get('level', 'medium')
        confidence_score = assessment_data.get('confidence', {}).get('score', assessment_data.get('confidence_score', 70)) / 100.0
        is_rejected = assessment_data.get('is_rejected', False)
        # Handle both nested and flat data structures
        insights = assessment_data.get('insights', {})
        if isinstance(insights, dict):
            red_flags = insights.get('red_flags', [])
        else:
            red_flags = assessment_data.get('red_flags', [])
        
        # Calculate confidence interval
        confidence_interval = self._calculate_confidence_interval(
            total_score, confidence_level, confidence_score
        )
        
        # Determine action and priority
        action, priority = self._determine_action_and_priority(
            total_score,
            confidence_interval,
            is_rejected,
            len(red_flags),
            growth_potential_score
        )
        
        # Assess hiring risk
        risk_level = self._assess_hiring_risk(
            total_score,
            confidence_interval,
            red_flags,
            confidence_score
        )
        
        # Generate next steps
        next_steps = self._generate_next_steps(
            action, 
            total_score, 
            red_flags,
            assessment_data
        )
        
        # Estimate success probability
        success_probability = self._estimate_success_probability(
            total_score,
            confidence_score,
            growth_potential_score,
            len(red_flags)
        )
        
        # Generate interview focus areas
        interview_focus = self._generate_interview_focus(
            assessment_data,
            red_flags
        )
        
        # Build decision factors
        decision_factors = self._build_decision_factors(
            assessment_data,
            growth_potential_score,
            confidence_interval,
            risk_level
        )
        
        # Generate recommendation message
        message = self._generate_recommendation_message(
            action,
            total_score,
            confidence_interval,
            growth_potential_score,
            risk_level,
            red_flags
        )
        
        return SmartRecommendation(
            action=action,
            priority=priority,
            message=message,
            confidence_interval=confidence_interval,
            risk_level=risk_level,
            next_steps=next_steps,
            estimated_success_probability=round(success_probability, 1),
            interview_questions_focus=interview_focus,
            decision_factors=decision_factors
        )
    
    def _calculate_confidence_interval(
        self,
        score: float,
        confidence_level: str,
        confidence_score: float
    ) -> ConfidenceInterval:
        """
        Calculate statistical confidence interval for the score.
        
        Lower confidence = wider interval (more uncertainty)
        """
        
        config = self.CONFIDENCE_LEVELS.get(confidence_level, self.CONFIDENCE_LEVELS['medium'])
        
        # Base margin of error depends on confidence
        # High confidence score = narrow interval, low = wide interval
        base_margin = 5  # Base ± 5 points
        
        # Adjust margin based on confidence score (0-1)
        # confidence_score of 1.0 = no adjustment, 0.5 = 2x margin
        adjustment_factor = config['margin_multiplier'] * (1.5 - confidence_score)
        margin = base_margin * adjustment_factor
        
        # Ensure bounds stay within 0-100
        lower = max(0, score - margin)
        upper = min(100, score + margin)
        
        return ConfidenceInterval(
            point_estimate=round(score, 1),
            lower_bound=round(lower, 1),
            upper_bound=round(upper, 1),
            margin_of_error=round(margin, 1),
            confidence_level=config['level']
        )
    
    def _determine_action_and_priority(
        self,
        score: float,
        ci: ConfidenceInterval,
        is_rejected: bool,
        red_flag_count: int,
        growth_score: float = None
    ) -> Tuple[HiringAction, Priority]:
        """Determine hiring action and priority"""
        
        # Hard reject
        if is_rejected or score < 40:
            return HiringAction.REJECT, Priority.NONE
        
        # Critical red flags
        if red_flag_count >= 3:
            return HiringAction.HOLD_FOR_REVIEW, Priority.LOW
        
        # Use lower bound of CI for conservative decision making
        # This accounts for uncertainty
        conservative_score = ci.lower_bound
        
        # Factor in growth potential for borderline cases
        if growth_score and growth_score >= 75 and score >= 65:
            # High potential candidate, even if current fit is borderline
            return HiringAction.SHORTLIST, Priority.HIGH
        
        # Standard decision tree based on score
        if score >= self.THRESHOLDS['immediate_interview'] and conservative_score >= 75:
            # Excellent match with high confidence
            return HiringAction.IMMEDIATE_INTERVIEW, Priority.CRITICAL
        
        elif score >= self.THRESHOLDS['immediate_interview'] and red_flag_count == 0:
            # Excellent match but some uncertainty
            return HiringAction.IMMEDIATE_INTERVIEW, Priority.HIGH
        
        elif score >= self.THRESHOLDS['shortlist'] and conservative_score >= 65:
            # Good match with decent confidence
            return HiringAction.SHORTLIST, Priority.HIGH
        
        elif score >= self.THRESHOLDS['shortlist'] and red_flag_count <= 1:
            # Good match with minor concerns
            return HiringAction.SHORTLIST, Priority.MEDIUM
        
        elif score >= self.THRESHOLDS['waitlist'] and conservative_score >= 55:
            # Borderline candidate worth keeping
            return HiringAction.WAITLIST, Priority.MEDIUM
        
        elif score >= self.THRESHOLDS['waitlist']:
            # Borderline with uncertainty
            return HiringAction.WAITLIST, Priority.LOW
        
        else:
            # Below threshold
            return HiringAction.REJECT, Priority.NONE
    
    def _assess_hiring_risk(
        self,
        score: float,
        ci: ConfidenceInterval,
        red_flags: List,
        confidence_score: float
    ) -> str:
        """Assess risk level of hiring this candidate"""
        
        # Wide confidence interval = higher risk
        interval_width = ci.upper_bound - ci.lower_bound
        
        # Multiple factors contribute to risk
        risk_factors = 0
        
        if interval_width > 15:
            risk_factors += 2  # High uncertainty
        elif interval_width > 10:
            risk_factors += 1
        
        if len(red_flags) >= 2:
            risk_factors += 2
        elif len(red_flags) >= 1:
            risk_factors += 1
        
        if confidence_score < 0.6:
            risk_factors += 2
        elif confidence_score < 0.75:
            risk_factors += 1
        
        if score < 70 and len(red_flags) > 0:
            risk_factors += 1
        
        # Determine risk level
        if risk_factors >= 4:
            return 'high'
        elif risk_factors >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _generate_next_steps(
        self,
        action: HiringAction,
        score: float,
        red_flags: List,
        assessment_data: Dict
    ) -> List[str]:
        """Generate actionable next steps for recruiters"""
        
        steps = []
        
        if action == HiringAction.IMMEDIATE_INTERVIEW:
            steps.append("Schedule interview within 24-48 hours")
            steps.append("Prepare job offer parameters")
            if score < 90:
                steps.append(f"Address minor gaps during interview: {', '.join([rf.get('type', 'unknown') for rf in red_flags[:2]])}")
        
        elif action == HiringAction.SHORTLIST:
            steps.append("Add to shortlist for interview scheduling")
            steps.append("Request additional information if needed")
            if red_flags:
                steps.append(f"Verify concerns: {red_flags[0].get('description', 'Unknown concern')}")
            steps.append("Compare with other shortlisted candidates")
        
        elif action == HiringAction.WAITLIST:
            steps.append("Add to waitlist - review if shortlist exhausted")
            steps.append("Monitor for better candidates")
            if score >= 65:
                steps.append("Consider if requirements can be adjusted")
        
        elif action == HiringAction.HOLD_FOR_REVIEW:
            steps.append("Senior recruiter review required")
            steps.append(f"Investigate red flags: {', '.join([rf.get('type', 'unknown') for rf in red_flags[:3]])}")
            steps.append("Request additional documentation")
        
        elif action == HiringAction.REJECT:
            steps.append("Send polite rejection email")
            steps.append("Keep in database for future opportunities")
        
        return steps
    
    def _estimate_success_probability(
        self,
        score: float,
        confidence: float,
        growth_score: float = None,
        red_flag_count: int = 0
    ) -> float:
        """
        Estimate probability of successful hire.
        
        Based on:
        - Current fit score
        - Confidence in assessment
        - Growth potential
        - Red flags
        """
        
        # Start with score as base probability
        base_probability = score
        
        # Adjust for confidence (low confidence = lower probability)
        confidence_adjustment = (confidence - 0.5) * 20  # ± 10 points max
        
        # Adjust for growth potential
        growth_adjustment = 0
        if growth_score:
            if growth_score >= 75:
                growth_adjustment = 10
            elif growth_score >= 65:
                growth_adjustment = 5
        
        # Penalize for red flags
        red_flag_penalty = min(red_flag_count * 5, 20)
        
        # Calculate final probability
        probability = base_probability + confidence_adjustment + growth_adjustment - red_flag_penalty
        
        return max(0, min(100, probability))
    
    def _generate_interview_focus(
        self,
        assessment_data: Dict,
        red_flags: List
    ) -> List[str]:
        """Generate interview focus areas"""
        
        focus_areas = []
        
        # Focus on weak sections
        section_scores = assessment_data.get('section_scores', {})
        weak_sections = [
            name for name, data in section_scores.items()
            if isinstance(data, dict) and data.get('score', 100) < 70
        ]
        
        for section in weak_sections[:3]:
            focus_areas.append(f"Probe {section.replace('_', ' ')} capabilities in depth")
        
        # Focus on red flags
        for flag in red_flags[:2]:
            if isinstance(flag, dict):
                focus_areas.append(f"Clarify: {flag.get('description', 'Concern area')}")
        
        # Focus on critical skills gaps
        insights = assessment_data.get('insights', {})
        if isinstance(insights, dict):
            weaknesses = insights.get('weaknesses', [])
            for weakness in weaknesses[:2]:
                focus_areas.append(f"Assess: {weakness}")
        elif isinstance(insights, list):
            # If insights is a list of strings, use them as weaknesses
            for weakness in insights[:2]:
                if weakness and isinstance(weakness, str):
                    focus_areas.append(f"Assess: {weakness}")
        
        return focus_areas[:5]  # Top 5
    
    def _build_decision_factors(
        self,
        assessment_data: Dict,
        growth_score: float,
        ci: ConfidenceInterval,
        risk_level: str
    ) -> Dict[str, Any]:
        """Build key decision factors"""
        
        # Handle both dict and list insights structures
        insights = assessment_data.get('insights', {})
        if isinstance(insights, dict):
            red_flag_count = len(insights.get('red_flags', assessment_data.get('red_flags', [])))
            top_strength = insights.get('strengths', ['Unknown'])[0] if insights.get('strengths') else 'Not identified'
            top_weakness = insights.get('weaknesses', ['Unknown'])[0] if insights.get('weaknesses') else 'Not identified'
        else:
            red_flag_count = len(assessment_data.get('red_flags', []))
            top_strength = assessment_data.get('strong_sections', ['Unknown'])[0] if assessment_data.get('strong_sections') else 'Not identified'
            top_weakness = assessment_data.get('weak_sections', ['Unknown'])[0] if assessment_data.get('weak_sections') else 'Not identified'
        
        return {
            'current_fit_score': assessment_data.get('total_score', assessment_data.get('overall_score', 0)),
            'score_range': f"{ci.lower_bound:.0f}-{ci.upper_bound:.0f}",
            'confidence_level': assessment_data.get('confidence', {}).get('level', 'unknown'),
            'growth_potential': growth_score if growth_score else 'not_assessed',
            'risk_level': risk_level,
            'red_flag_count': red_flag_count,
            'top_strength': top_strength,
            'top_weakness': top_weakness,
        }
    
    def _generate_recommendation_message(
        self,
        action: HiringAction,
        score: float,
        ci: ConfidenceInterval,
        growth_score: float,
        risk_level: str,
        red_flags: List
    ) -> str:
        """Generate human-readable recommendation message"""
        
        messages = {
            HiringAction.IMMEDIATE_INTERVIEW: (
                f"🎯 IMMEDIATE INTERVIEW RECOMMENDED - "
                f"Score: {score:.0f} (range: {ci.lower_bound:.0f}-{ci.upper_bound:.0f}, {ci.confidence_level}% confidence). "
                f"Excellent match with {risk_level} hiring risk. "
                f"Top-tier candidate - prioritize scheduling."
            ),
            
            HiringAction.SHORTLIST: (
                f"✅ SHORTLIST FOR INTERVIEW - "
                f"Score: {score:.0f} (range: {ci.lower_bound:.0f}-{ci.upper_bound:.0f}, {ci.confidence_level}% confidence). "
                f"Strong candidate with {risk_level} risk. "
                + (f"Growth potential: {growth_score:.0f}. " if growth_score and growth_score >= 70 else "")
                + f"Schedule when available."
            ),
            
            HiringAction.WAITLIST: (
                f"⏸️ WAITLIST - "
                f"Score: {score:.0f} (range: {ci.lower_bound:.0f}-{ci.upper_bound:.0f}, {ci.confidence_level}% confidence). "
                f"Borderline candidate with {risk_level} risk. "
                f"Consider if shortlist candidates decline."
            ),
            
            HiringAction.HOLD_FOR_REVIEW: (
                f"⚠️ HOLD FOR SENIOR REVIEW - "
                f"Score: {score:.0f} but {len(red_flags)} red flags detected. "
                f"Risk level: {risk_level}. "
                f"Requires additional verification before proceeding."
            ),
            
            HiringAction.REJECT: (
                f"❌ NOT RECOMMENDED - "
                f"Score: {score:.0f} (range: {ci.lower_bound:.0f}-{ci.upper_bound:.0f}). "
                f"Significant gaps exist. Send polite rejection."
            ),
        }
        
        return messages.get(action, "Unknown recommendation")

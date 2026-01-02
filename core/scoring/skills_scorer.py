"""
Advanced Skills Scoring Engine with Multi-Strategy Matching

This module provides enterprise-grade skill matching using:
- Synonym matching (JS → JavaScript)
- Semantic similarity (TensorFlow ≈ PyTorch)
- Required vs Preferred skill differentiation
- Weighted scoring based on match confidence

Author: Senior SDE
Date: January 2, 2026
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer

from logis_ai_candidate_engine.ml.skill_matcher import get_skill_matcher, SkillMatchResult, SkillMatch


@dataclass
class SkillsScoringResult:
    """
    Enhanced result object for skills scoring with detailed breakdown.
    """
    score: int  # 0-100
    explanation: str
    matched_skills: List[str]  # All matched skills (required + preferred)
    missing_skills: List[str]  # All missing skills
    
    # Enhanced fields for Phase 2
    matched_required: List[str]
    matched_preferred: List[str]
    missing_required: List[str]
    missing_preferred: List[str]
    
    required_match_score: float  # 0-100
    preferred_match_score: float  # 0-100
    
    # Match type breakdown
    exact_matches: int
    synonym_matches: int
    semantic_matches: int
    
    # Match details for UI
    match_details: Dict[str, any]


class SkillsScorer:
    """
    Enterprise-grade skills scoring using advanced matching strategies.
    
    Features:
    - Multi-strategy matching (exact, synonym, semantic)
    - Required vs Preferred skill differentiation (70/30 split)
    - Confidence-weighted scoring
    - Detailed match explanations
    - Integration with SkillMatcher and embedding model
    
    Scoring Formula:
    - Overall Score = (Required Match * 0.7) + (Preferred Match * 0.3)
    - Each match weighted by confidence (exact=1.0, synonym=0.95, semantic=0.85)
    """

    def __init__(self, embedding_model: Optional[SentenceTransformer] = None):
        """
        Initialize SkillsScorer with optional embedding model.
        
        Args:
            embedding_model: Pre-loaded sentence transformer for semantic matching
        """
        self.skill_matcher = get_skill_matcher(embedding_model)
    
    def score(
        self,
        required_skills: List[str],
        candidate_skills: List[str],
        preferred_skills: Optional[List[str]] = None
    ) -> SkillsScoringResult:
        """
        Score candidate skills against job requirements (required + preferred).
        
        Args:
            required_skills: Must-have skills for the job
            candidate_skills: Skills from candidate's profile
            preferred_skills: Nice-to-have skills (optional)
        
        Returns:
            SkillsScoringResult with comprehensive matching details
        """
        # Handle legacy API (backward compatibility)
        if preferred_skills is None:
            preferred_skills = []
        
        # Edge case: No skills required
        if not required_skills and not preferred_skills:
            return SkillsScoringResult(
                score=100,
                explanation="No skills specified for this job",
                matched_skills=[],
                missing_skills=[],
                matched_required=[],
                matched_preferred=[],
                missing_required=[],
                missing_preferred=[],
                required_match_score=100.0,
                preferred_match_score=100.0,
                exact_matches=0,
                synonym_matches=0,
                semantic_matches=0,
                match_details={}
            )
        
        # Perform advanced skill matching
        match_result: SkillMatchResult = self.skill_matcher.match_skills(
            required_job_skills=required_skills,
            preferred_job_skills=preferred_skills,
            candidate_skills=candidate_skills
        )
        
        # Extract matched/missing skills for response
        matched_required = [m.candidate_skill for m in match_result.matched_required]
        matched_preferred = [m.candidate_skill for m in match_result.matched_preferred]
        missing_required = match_result.missing_required
        missing_preferred = match_result.missing_preferred
        
        all_matched = matched_required + matched_preferred
        all_missing = missing_required + missing_preferred
        
        # Round overall score to integer
        overall_score = int(round(match_result.overall_skill_score))
        
        # Build human-readable explanation
        explanation_parts = []
        
        if required_skills:
            req_match_pct = (len(matched_required) / len(required_skills)) * 100
            explanation_parts.append(
                f"Required skills: {len(matched_required)}/{len(required_skills)} matched ({req_match_pct:.0f}%)"
            )
        
        if preferred_skills:
            pref_match_pct = (len(matched_preferred) / len(preferred_skills)) * 100
            explanation_parts.append(
                f"Preferred skills: {len(matched_preferred)}/{len(preferred_skills)} matched ({pref_match_pct:.0f}%)"
            )
        
        # Add match type breakdown
        match_type_parts = []
        if match_result.match_details['exact_matches'] > 0:
            match_type_parts.append(f"{match_result.match_details['exact_matches']} exact")
        if match_result.match_details['synonym_matches'] > 0:
            match_type_parts.append(f"{match_result.match_details['synonym_matches']} synonym")
        if match_result.match_details['semantic_matches'] > 0:
            match_type_parts.append(f"{match_result.match_details['semantic_matches']} semantic")
        
        if match_type_parts:
            explanation_parts.append(f"Match types: {', '.join(match_type_parts)}")
        
        explanation = " | ".join(explanation_parts)
        
        # Build detailed match info for UI
        detailed_matches = {
            'required_matches': [
                {
                    'job_skill': m.job_skill,
                    'candidate_skill': m.candidate_skill,
                    'match_type': m.match_type,
                    'confidence': f"{m.confidence:.0%}",
                    'explanation': self.skill_matcher.explain_match(m)
                }
                for m in match_result.matched_required
            ],
            'preferred_matches': [
                {
                    'job_skill': m.job_skill,
                    'candidate_skill': m.candidate_skill,
                    'match_type': m.match_type,
                    'confidence': f"{m.confidence:.0%}",
                    'explanation': self.skill_matcher.explain_match(m)
                }
                for m in match_result.matched_preferred
            ]
        }
        
        return SkillsScoringResult(
            score=overall_score,
            explanation=explanation,
            matched_skills=all_matched,
            missing_skills=all_missing,
            matched_required=matched_required,
            matched_preferred=matched_preferred,
            missing_required=missing_required,
            missing_preferred=missing_preferred,
            required_match_score=match_result.required_match_score,
            preferred_match_score=match_result.preferred_match_score,
            exact_matches=match_result.match_details['exact_matches'],
            synonym_matches=match_result.match_details['synonym_matches'],
            semantic_matches=match_result.match_details['semantic_matches'],
            match_details=detailed_matches
        )

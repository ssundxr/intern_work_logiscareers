"""
Intelligent Candidate Ranking System
Ranks and compares candidates for jobs using multiple criteria

Features:
- Multi-dimensional ranking algorithm
- Comparative candidate analysis
- Interview priority suggestions
- Batch processing for multiple candidates
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class RankingCriteria(Enum):
    """Criteria for ranking candidates"""
    OVERALL_SCORE = "overall_score"
    SKILLS_MATCH = "skills_match"
    EXPERIENCE_FIT = "experience_fit"
    SALARY_FIT = "salary_fit"
    CULTURAL_FIT = "cultural_fit"
    LEARNING_POTENTIAL = "learning_potential"


@dataclass
class RankedCandidate:
    """Candidate with ranking information"""
    candidate_id: int
    candidate_name: str
    overall_rank: int
    total_score: float
    skills_score: float
    experience_score: float
    cultural_fit: float
    red_flag_count: int
    critical_red_flags: int
    recommendation: str
    rank_tier: str  # "S", "A", "B", "C", "D"
    interview_priority: str  # "urgent", "high", "medium", "low"
    key_strengths: List[str]
    key_concerns: List[str]


class CandidateRanker:
    """Ranks candidates for a specific job"""
    
    @staticmethod
    def rank_candidates(
        candidates: List[Dict[str, Any]],
        ranking_criteria: RankingCriteria = RankingCriteria.OVERALL_SCORE
    ) -> List[RankedCandidate]:
        """
        Rank candidates based on specified criteria
        
        Args:
            candidates: List of candidate assessment results
            ranking_criteria: Primary criteria for ranking
        
        Returns:
            List of ranked candidates with detailed information
        """
        
        # Calculate composite scores for each candidate
        scored_candidates = []
        
        for candidate in candidates:
            composite_score = CandidateRanker._calculate_composite_score(
                candidate, ranking_criteria
            )
            
            scored_candidates.append({
                'candidate': candidate,
                'composite_score': composite_score
            })
        
        # Sort by composite score
        scored_candidates.sort(key=lambda x: x['composite_score'], reverse=True)
        
        # Build ranked candidate objects
        ranked = []
        for idx, item in enumerate(scored_candidates):
            candidate = item['candidate']
            rank = idx + 1
            
            ranked_candidate = RankedCandidate(
                candidate_id=candidate.get('candidate_id') or candidate.get('id', 0),
                candidate_name=candidate.get('candidate_name', 'Unknown'),
                overall_rank=rank,
                total_score=candidate.get('assessment', {}).get('total_score', 0),
                skills_score=candidate.get('assessment', {}).get('section_scores', {}).get('skills', {}).get('score', 0),
                experience_score=candidate.get('assessment', {}).get('section_scores', {}).get('experience', {}).get('score', 0),
                cultural_fit=candidate.get('insights', {}).get('cultural_fit_score', 0),
                red_flag_count=len(candidate.get('insights', {}).get('red_flags', [])),
                critical_red_flags=len([
                    f for f in candidate.get('insights', {}).get('red_flags', [])
                    if f.get('severity') == 'critical'
                ]),
                recommendation=candidate.get('insights', {}).get('recommendation', ''),
                rank_tier=CandidateRanker._calculate_tier(rank, len(scored_candidates)),
                interview_priority=CandidateRanker._calculate_interview_priority(
                    candidate, rank
                ),
                key_strengths=candidate.get('insights', {}).get('strengths', [])[:3],
                key_concerns=[
                    f.get('description', '') for f in 
                    candidate.get('insights', {}).get('red_flags', [])[:2]
                ]
            )
            
            ranked.append(ranked_candidate)
        
        return ranked
    
    @staticmethod
    def _calculate_composite_score(
        candidate: Dict[str, Any],
        criteria: RankingCriteria
    ) -> float:
        """Calculate composite score based on ranking criteria"""
        
        assessment = candidate.get('assessment', {})
        insights = candidate.get('insights', {})
        
        if criteria == RankingCriteria.OVERALL_SCORE:
            # Balanced score considering all factors
            base_score = assessment.get('total_score', 0)
            
            # Adjust for red flags
            red_flags = insights.get('red_flags', [])
            critical_flags = [f for f in red_flags if f.get('severity') == 'critical']
            high_flags = [f for f in red_flags if f.get('severity') == 'high']
            
            red_flag_penalty = len(critical_flags) * 15 + len(high_flags) * 5
            
            # Bonus for high cultural fit and learning potential
            cultural_bonus = (insights.get('cultural_fit_score', 0) - 70) * 0.1
            learning_bonus = (insights.get('learning_potential', 0) - 70) * 0.1
            
            return base_score - red_flag_penalty + cultural_bonus + learning_bonus
        
        elif criteria == RankingCriteria.SKILLS_MATCH:
            skills_score = assessment.get('section_scores', {}).get('skills', {}).get('score', 0)
            skill_currency = insights.get('skill_currency_score', 0)
            return (skills_score * 0.7) + (skill_currency * 0.3)
        
        elif criteria == RankingCriteria.EXPERIENCE_FIT:
            exp_score = assessment.get('section_scores', {}).get('experience', {}).get('score', 0)
            return exp_score
        
        elif criteria == RankingCriteria.SALARY_FIT:
            salary_score = assessment.get('section_scores', {}).get('salary', {}).get('score', 0)
            return salary_score
        
        elif criteria == RankingCriteria.CULTURAL_FIT:
            return insights.get('cultural_fit_score', 0)
        
        elif criteria == RankingCriteria.LEARNING_POTENTIAL:
            return insights.get('learning_potential', 0)
        
        return assessment.get('total_score', 0)
    
    @staticmethod
    def _calculate_tier(rank: int, total: int) -> str:
        """Calculate rank tier (S, A, B, C, D)"""
        percentile = (rank - 1) / total if total > 0 else 0
        
        if percentile <= 0.1:
            return "S"  # Top 10%
        elif percentile <= 0.3:
            return "A"  # Top 30%
        elif percentile <= 0.6:
            return "B"  # Top 60%
        elif percentile <= 0.85:
            return "C"  # Top 85%
        else:
            return "D"  # Bottom 15%
    
    @staticmethod
    def _calculate_interview_priority(candidate: Dict[str, Any], rank: int) -> str:
        """Calculate interview priority"""
        assessment = candidate.get('assessment', {})
        insights = candidate.get('insights', {})
        
        total_score = assessment.get('total_score', 0)
        critical_flags = len([
            f for f in insights.get('red_flags', [])
            if f.get('severity') == 'critical'
        ])
        
        # Don't interview if rejected or has critical flags
        if assessment.get('is_rejected') or critical_flags > 0:
            return "do_not_interview"
        
        # Urgent for top candidates
        if rank <= 3 and total_score >= 85:
            return "urgent"
        
        # High priority for good candidates
        if rank <= 10 and total_score >= 75:
            return "high"
        
        # Medium priority for acceptable candidates
        if total_score >= 60:
            return "medium"
        
        # Low priority for weak candidates
        return "low"
    
    @staticmethod
    def generate_comparison_matrix(
        ranked_candidates: List[RankedCandidate]
    ) -> Dict[str, Any]:
        """Generate a comparison matrix for top candidates"""
        
        if not ranked_candidates:
            return {}
        
        # Take top 10 candidates for comparison
        top_candidates = ranked_candidates[:10]
        
        comparison = {
            'total_candidates': len(ranked_candidates),
            'compared_count': len(top_candidates),
            'tier_distribution': {
                'S': len([c for c in ranked_candidates if c.rank_tier == 'S']),
                'A': len([c for c in ranked_candidates if c.rank_tier == 'A']),
                'B': len([c for c in ranked_candidates if c.rank_tier == 'B']),
                'C': len([c for c in ranked_candidates if c.rank_tier == 'C']),
                'D': len([c for c in ranked_candidates if c.rank_tier == 'D']),
            },
            'interview_priorities': {
                'urgent': len([c for c in ranked_candidates if c.interview_priority == 'urgent']),
                'high': len([c for c in ranked_candidates if c.interview_priority == 'high']),
                'medium': len([c for c in ranked_candidates if c.interview_priority == 'medium']),
                'low': len([c for c in ranked_candidates if c.interview_priority == 'low']),
            },
            'top_candidates': [
                {
                    'rank': c.overall_rank,
                    'name': c.candidate_name,
                    'tier': c.rank_tier,
                    'score': c.total_score,
                    'priority': c.interview_priority,
                    'strengths': c.key_strengths,
                    'concerns': c.key_concerns
                }
                for c in top_candidates
            ],
            'average_score': sum(c.total_score for c in ranked_candidates) / len(ranked_candidates),
            'top_10_average': sum(c.total_score for c in top_candidates) / len(top_candidates) if top_candidates else 0,
        }
        
        return comparison

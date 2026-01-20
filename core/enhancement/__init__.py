"""
Enhancement Package - Advanced Candidate Intelligence
Provides red flag detection, ranking, and comprehensive insights
"""

from .candidate_intelligence import (
    RedFlag,
    RedFlagSeverity,
    RedFlagDetector,
    CandidateInsight,
    CandidateInsightGenerator,
    CareerProgressionType,
    CareerProgressionAnalyzer,
    SkillCurrencyAnalyzer
)

from .ranking_system import (
    RankedCandidate,
    RankingCriteria,
    CandidateRanker
)

__all__ = [
    'RedFlag',
    'RedFlagSeverity',
    'RedFlagDetector',
    'CandidateInsight',
    'CandidateInsightGenerator',
    'CareerProgressionType',
    'CareerProgressionAnalyzer',
    'SkillCurrencyAnalyzer',
    'RankedCandidate',
    'RankingCriteria',
    'CandidateRanker',
]

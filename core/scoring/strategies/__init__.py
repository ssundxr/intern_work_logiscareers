"""
Scoring Strategy Implementations

This module exports all concrete scoring strategy classes for the Strategy Pattern
implementation in ComprehensiveScorer.

Each strategy is responsible for ONE specific assessment area:
- PersonalDetailsScoringStrategy: Personal details and eligibility
- ExperienceScoringStrategy: Work experience and recency
- EducationScoringStrategy: Education qualifications
- SkillsScoringStrategy: Skills matching with weighted importance
- SalaryScoringStrategy: Salary expectations alignment
- CVAnalysisScoringStrategy: CV/Resume content analysis
"""

from core.scoring.strategies.base import ScoringStrategy, ScoringContext
from core.scoring.strategies.personal_details_strategy import PersonalDetailsScoringStrategy
from core.scoring.strategies.experience_strategy import ExperienceScoringStrategy
from core.scoring.strategies.education_strategy import EducationScoringStrategy
from core.scoring.strategies.skills_strategy import SkillsScoringStrategy
from core.scoring.strategies.salary_strategy import SalaryScoringStrategy
from core.scoring.strategies.cv_analysis_strategy import CVAnalysisScoringStrategy

__all__ = [
    'ScoringStrategy',
    'ScoringContext',
    'PersonalDetailsScoringStrategy',
    'ExperienceScoringStrategy',
    'EducationScoringStrategy',
    'SkillsScoringStrategy',
    'SalaryScoringStrategy',
    'CVAnalysisScoringStrategy',
]


# Scores candidate's education section
# core/scoring/education_scorer.py

from typing import Optional


class EducationScoringResult:
    """
    Immutable result object for education scoring.
    """

    def __init__(self, score: int, explanation: str):
        self.score = score
        self.explanation = explanation


class EducationScorer:
    """
    Computes education alignment score.
    Education is treated as a supporting signal, not a gate.
    """

    EDUCATION_RANKING = {
        "phd": 100,
        "doctorate": 100,
        "masters": 90,
        "master": 90,
        "bachelors": 80,
        "bachelor": 80,
        "diploma": 70,
        "high school": 65,
    }

    DEFAULT_SCORE = 75  # Neutral score for missing/unknown education

    @staticmethod
    def score(education_level: Optional[str]) -> EducationScoringResult:
        if not education_level:
            return EducationScoringResult(
                score=EducationScorer.DEFAULT_SCORE,
                explanation="Education information not provided; neutral impact applied",
            )

        normalized = education_level.strip().lower()

        for key, value in EducationScorer.EDUCATION_RANKING.items():
            if key in normalized:
                return EducationScoringResult(
                    score=value,
                    explanation=f"Education level identified as '{education_level}'",
                )

        # Unknown or non-standard education
        return EducationScoringResult(
            score=EducationScorer.DEFAULT_SCORE,
            explanation=f"Education level '{education_level}' treated as neutral",
        )

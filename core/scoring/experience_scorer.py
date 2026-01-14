# Scores candidate's experience section
# core/scoring/experience_scorer.py

from typing import Optional


class ExperienceScoringResult:
    """
    Immutable result object for experience scoring.
    """

    def __init__(self, score: int, explanation: str):
        self.score = score
        self.explanation = explanation


class ExperienceScorer:
    """
    Computes experience alignment score between
    job requirements and candidate experience.
    """

    @staticmethod
    def score(
        min_experience_years: int,
        max_experience_years: Optional[int],
        candidate_experience_years: float,
    ) -> ExperienceScoringResult:
        # Defensive: ensure non-negative experience
        candidate_experience_years = max(candidate_experience_years, 0)

        # Case 1: No max experience defined (common case)
        if max_experience_years is None:
            # Candidate at or above minimum gets full score
            explanation = (
                f"{candidate_experience_years:.1f} years experience "
                f"against minimum requirement of {min_experience_years} years"
            )
            return ExperienceScoringResult(score=100, explanation=explanation)

        # Case 2: Experience within defined range
        if candidate_experience_years <= max_experience_years:
            range_span = max_experience_years - min_experience_years
            if range_span == 0:
                # Edge case: min == max
                return ExperienceScoringResult(
                    score=100,
                    explanation=(
                        f"{candidate_experience_years:.1f} years experience "
                        f"matches exact requirement of {min_experience_years} years"
                    ),
                )

            normalized = (
                (candidate_experience_years - min_experience_years) / range_span
            )
            score = int(round(70 + (normalized * 30)))  # 70 → 100 range

            explanation = (
                f"{candidate_experience_years:.1f} years experience "
                f"within required range ({min_experience_years}–{max_experience_years} years)"
            )

            return ExperienceScoringResult(score=score, explanation=explanation)

        # Case 3: Overqualified candidate (above max)
        explanation = (
            f"{candidate_experience_years:.1f} years experience "
            f"exceeds preferred maximum of {max_experience_years} years"
        )

        # Mild penalty, not rejection
        return ExperienceScoringResult(score=85, explanation=explanation)

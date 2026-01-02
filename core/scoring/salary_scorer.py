# Scores candidate's salary expectations
# core/scoring/salary_scorer.py

class SalaryScoringResult:
    """
    Immutable result object for salary alignment scoring.
    """

    def __init__(self, score: int, explanation: str):
        self.score = score
        self.explanation = explanation


class SalaryScorer:
    """
    Computes soft salary alignment score.
    Hard salary rejection is handled upstream.
    """

    MIN_SCORE = 75
    MAX_SCORE = 100

    @staticmethod
    def score(
        salary_min: int,
        salary_max: int,
        expected_salary: int,
    ) -> SalaryScoringResult:
        # Defensive: handle degenerate range
        if salary_max <= salary_min:
            return SalaryScoringResult(
                score=SalaryScorer.MAX_SCORE,
                explanation="Salary range is narrow or undefined; neutral score applied",
            )

        # Expected salary is within range (hard rejection already applied)
        midpoint = (salary_min + salary_max) / 2

        if expected_salary <= salary_min:
            return SalaryScoringResult(
                score=SalaryScorer.MAX_SCORE,
                explanation="Expected salary is at or below minimum range; excellent alignment",
            )

        if expected_salary <= midpoint:
            # Linear decay from 100 → 90
            ratio = (expected_salary - salary_min) / (midpoint - salary_min)
            score = int(round(SalaryScorer.MAX_SCORE - (ratio * 10)))

            return SalaryScoringResult(
                score=score,
                explanation="Expected salary is comfortably within job range",
            )

        # expected_salary between midpoint and salary_max
        ratio = (expected_salary - midpoint) / (salary_max - midpoint)
        score = int(round(90 - (ratio * 15)))  # 90 → 75

        return SalaryScoringResult(
            score=max(score, SalaryScorer.MIN_SCORE),
            explanation="Expected salary is near the upper limit of job range",
        )

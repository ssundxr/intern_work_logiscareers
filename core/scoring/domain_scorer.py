# Scores candidate's domain expertise
# core/scoring/domain_scorer.py

from typing import List, Optional


class DomainScoringResult:
    """
    Immutable result object for domain / industry alignment scoring.
    """

    def __init__(self, score: int, explanation: str, matched_domains: List[str]):
        self.score = score
        self.explanation = explanation
        self.matched_domains = matched_domains


class DomainScorer:
    """
    Computes industry / domain alignment score between
    job and candidate background.
    """

    DEFAULT_SCORE = 75  # Neutral baseline
    STRONG_MATCH_SCORE = 95
    PARTIAL_MATCH_SCORE = 85

    @staticmethod
    def score(
        job_industry: str,
        job_sub_industry: Optional[str],
        employment_summary: Optional[str],
    ) -> DomainScoringResult:
        if not employment_summary:
            return DomainScoringResult(
                score=DomainScorer.DEFAULT_SCORE,
                explanation="No employment summary provided; neutral domain score applied",
                matched_domains=[],
            )

        summary_normalized = employment_summary.lower()

        matched_domains: List[str] = []

        # Primary industry match
        if job_industry.lower() in summary_normalized:
            matched_domains.append(job_industry.lower())

        # Sub-industry match (if provided)
        if job_sub_industry and job_sub_industry.lower() in summary_normalized:
            matched_domains.append(job_sub_industry.lower())

        if len(matched_domains) >= 2:
            return DomainScoringResult(
                score=DomainScorer.STRONG_MATCH_SCORE,
                explanation="Strong alignment with job industry and sub-industry",
                matched_domains=matched_domains,
            )

        if len(matched_domains) == 1:
            return DomainScoringResult(
                score=DomainScorer.PARTIAL_MATCH_SCORE,
                explanation="Partial alignment with job industry",
                matched_domains=matched_domains,
            )

        # No explicit domain signal found
        return DomainScoringResult(
            score=DomainScorer.DEFAULT_SCORE,
            explanation="No direct industry alignment detected; neutral score applied",
            matched_domains=[],
        )

# Aggregates section scores using weighted logic
# core/aggregation/weighted_score_aggregator.py

from typing import Dict


class WeightedScoreAggregationResult:
    """
    Immutable result object for weighted score aggregation.
    """

    def __init__(self, final_score: int, contributions: Dict[str, float]):
        self.final_score = final_score
        self.contributions = contributions


class WeightedScoreAggregator:
    """
    Aggregates section-wise scores into a final compatibility score
    using configurable weights.
    """

    @staticmethod
    def aggregate(
        section_scores: Dict[str, int],
        weights: Dict[str, float],
    ) -> WeightedScoreAggregationResult:
        if not section_scores:
            raise ValueError("Section scores cannot be empty")

        # Filter weights to only those sections that actually exist
        active_weights = {
            section: weight
            for section, weight in weights.items()
            if section in section_scores
        }

        if not active_weights:
            raise ValueError("No matching weights for provided section scores")

        # Normalize weights to sum to 1.0
        total_weight = sum(active_weights.values())
        normalized_weights = {
            section: weight / total_weight
            for section, weight in active_weights.items()
        }

        weighted_sum = 0.0
        contributions: Dict[str, float] = {}

        for section, score in section_scores.items():
            weight = normalized_weights.get(section, 0.0)
            contribution = score * weight
            contributions[section] = round(contribution, 2)
            weighted_sum += contribution

        final_score = int(round(weighted_sum))

        return WeightedScoreAggregationResult(
            final_score=final_score,
            contributions=contributions,
        )

# Logs rule-based decision traces for explainability
# core/explainability/rule_trace_logger.py

from typing import List


class RuleTraceLogger:
    """
    Collects and formats rule execution traces
    for auditability and explainability.
    """

    @staticmethod
    def format(rule_trace: List[str]) -> List[str]:
        """
        Converts internal rule identifiers into
        human-readable explanations.
        """
        readable_mapping = {
            "LOCATION_MISMATCH": "Candidate location does not match job location",
            "SALARY_EXCEEDS_MAX": "Candidate salary expectation exceeds job budget",
            "INSUFFICIENT_EXPERIENCE": "Candidate does not meet minimum experience requirement",
            "PASSED_ALL_HARD_RULES": "Candidate passed all mandatory eligibility checks",
        }

        formatted_trace = []

        for rule in rule_trace:
            formatted_trace.append(
                readable_mapping.get(rule, f"Rule executed: {rule}")
            )

        return formatted_trace

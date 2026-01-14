# Generates section-wise explanations for candidate evaluation
# core/explainability/section_explanations.py

from typing import Dict


class SectionExplanationBuilder:
    """
    Builds recruiter-friendly explanations for
    each scoring section.
    """

    @staticmethod
    def build(
        section_explanations: Dict[str, str],
        contributions: Dict[str, float],
    ) -> Dict[str, str]:
        """
        Merges raw section explanations with contribution context.
        """

        final_explanations: Dict[str, str] = {}

        for section, explanation in section_explanations.items():
            contribution = contributions.get(section)

            if contribution is not None:
                final_explanations[section] = (
                    f"{explanation} (contributed {round(contribution)} points)"
                )
            else:
                final_explanations[section] = explanation

        return final_explanations

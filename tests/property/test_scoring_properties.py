"""
Property-Based Tests for Scoring Strategies

Uses Hypothesis to test scoring strategies with random but valid inputs.
Ensures scoring functions never produce invalid outputs (scores outside 0-100, etc.)

Author: Production Testing
Date: January 24, 2026
"""

import pytest
from hypothesis import given, strategies as st, assume
from core.scoring.strategies.skills_strategy import SkillsScoringStrategy
from core.scoring.strategies.experience_strategy import ExperienceScoringStrategy
from core.scoring.strategies.base import ScoringContext


# =============================================================================
# HYPOTHESIS STRATEGIES (Data Generators)
# =============================================================================

@st.composite
def skill_list_strategy(draw):
    """Generate realistic skill lists"""
    common_skills = [
        "Python", "Java", "JavaScript", "SQL", "AWS", "Docker", "Kubernetes",
        "React", "Angular", "Node.js", "Machine Learning", "Data Science",
        "Project Management", "Agile", "Scrum", "Communication", "Leadership"
    ]
    num_skills = draw(st.integers(min_value=0, max_value=15))
    return draw(st.lists(st.sampled_from(common_skills), min_size=num_skills, max_size=num_skills, unique=True))


@st.composite
def years_of_experience_strategy(draw):
    """Generate realistic years of experience"""
    return draw(st.floats(min_value=0.0, max_value=50.0, allow_nan=False, allow_infinity=False))


@st.composite
def scoring_context_strategy(draw):
    """Generate valid ScoringContext objects"""
    candidate_skills = draw(skill_list_strategy())
    required_skills = draw(skill_list_strategy())
    preferred_skills = draw(skill_list_strategy())
    
    candidate_years = draw(years_of_experience_strategy())
    required_years = draw(years_of_experience_strategy())
    
    return ScoringContext(
        candidate_data={
            "skills": candidate_skills,
            "total_experience_years": candidate_years,
            "gcc_experience_years": draw(st.floats(min_value=0.0, max_value=candidate_years, allow_nan=False)),
            "current_salary": draw(st.integers(min_value=1000, max_value=500000)),
        },
        job_data={
            "required_skills": required_skills,
            "preferred_skills": preferred_skills,
            "it_skills": draw(skill_list_strategy()),
            "years_experience_min": required_years,
            "years_experience_max": required_years + draw(st.floats(min_value=0.0, max_value=10.0)),
            "salary_min": draw(st.integers(min_value=1000, max_value=200000)),
            "salary_max": draw(st.integers(min_value=10000, max_value=500000)),
        },
        cv_text=""
    )


# =============================================================================
# PROPERTY-BASED TESTS
# =============================================================================

class TestScoringStrategyProperties:
    """Property-based tests ensuring scoring strategies never violate invariants"""
    
    @pytest.mark.property
    @given(context=scoring_context_strategy())
    def test_skills_score_always_in_valid_range(self, context):
        """Property: Skills scores must always be between 0 and 100"""
        strategy = SkillsScoringStrategy()
        result = strategy.score(context)
        
        # Total score must be in range
        assert 0 <= result.total_score <= 100, \
            f"Total score {result.total_score} is outside valid range [0, 100]"
        
        # All individual field scores must be in range
        for field in result.fields:
            assert 0 <= field.score <= 100, \
                f"Field {field.field_name} score {field.score} is outside valid range [0, 100]"
    
    @pytest.mark.property
    @given(context=scoring_context_strategy())
    def test_experience_score_always_in_valid_range(self, context):
        """Property: Experience scores must always be between 0 and 100"""
        strategy = ExperienceScoringStrategy()
        result = strategy.score(context)
        
        # Total score must be in range
        assert 0 <= result.total_score <= 100, \
            f"Total score {result.total_score} is outside valid range [0, 100]"
        
        # All individual field scores must be in range
        for field in result.fields:
            assert 0 <= field.score <= 100, \
                f"Field {field.field_name} score {field.score} is outside valid range [0, 100]"
    
    @pytest.mark.property
    @given(
        candidate_skills=skill_list_strategy(),
        required_skills=skill_list_strategy()
    )
    def test_more_skills_never_decreases_score(self, candidate_skills, required_skills):
        """Property: Adding more candidate skills should never decrease the score"""
        assume(len(required_skills) > 0)  # Only test when there are requirements
        
        strategy = SkillsScoringStrategy()
        
        # Score with original skills
        context1 = ScoringContext(
            candidate_data={"skills": candidate_skills},
            job_data={"required_skills": required_skills, "preferred_skills": [], "it_skills": []},
            cv_text=""
        )
        score1 = strategy.score(context1).total_score
        
        # Score with additional skill (that matches a requirement)
        if required_skills and required_skills[0] not in candidate_skills:
            enhanced_skills = candidate_skills + [required_skills[0]]
            context2 = ScoringContext(
                candidate_data={"skills": enhanced_skills},
                job_data={"required_skills": required_skills, "preferred_skills": [], "it_skills": []},
                cv_text=""
            )
            score2 = strategy.score(context2).total_score
            
            # Adding a matching skill should not decrease score
            assert score2 >= score1, \
                f"Adding matching skill decreased score from {score1} to {score2}"
    
    @pytest.mark.property
    @given(context=scoring_context_strategy())
    def test_section_name_is_always_set(self, context):
        """Property: Section name must always be set in result"""
        strategy = SkillsScoringStrategy()
        result = strategy.score(context)
        
        assert result.section_name is not None
        assert isinstance(result.section_name, str)
        assert len(result.section_name) > 0
    
    @pytest.mark.property
    @given(context=scoring_context_strategy())
    def test_match_level_is_consistent_with_score(self, context):
        """Property: Match level should be consistent with score ranges"""
        strategy = SkillsScoringStrategy()
        result = strategy.score(context)
        
        from core.scoring.models import MatchLevel
        
        if result.total_score >= 85:
            assert result.match_level == MatchLevel.EXCELLENT
        elif result.total_score >= 70:
            assert result.match_level == MatchLevel.GOOD
        elif result.total_score >= 50:
            assert result.match_level == MatchLevel.PARTIAL
        else:
            assert result.match_level == MatchLevel.POOR


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])

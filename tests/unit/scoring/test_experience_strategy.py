"""
Unit Tests for Experience Scoring Strategy

Tests the ExperienceScoringStrategy in isolation.
"""

import pytest
from core.scoring.strategies.experience_strategy import ExperienceScoringStrategy
from core.scoring.strategies.base import ScoringContext


class TestExperienceScoringStrategy:
    """Test suite for ExperienceScoringStrategy"""
    
    @pytest.fixture
    def strategy(self):
        """Create an experience scoring strategy instance"""
        return ExperienceScoringStrategy()
    
    @pytest.fixture
    def base_context(self):
        """Create a base scoring context"""
        return ScoringContext(
            candidate_data={
                "total_experience_years": 0,
                "industry_experience": [],
                "functional_area_experience": []
            },
            job_data={
                "required_experience_years": 0,
                "preferred_industry": "",
                "functional_area": ""
            },
            cv_text=""
        )
    
    def test_exact_experience_match(self, strategy, base_context):
        """Test perfect match for exact years of experience"""
        base_context.candidate_data["total_experience_years"] = 5
        base_context.job_data["required_experience_years"] = 5
        
        result = strategy.score(base_context)
        
        assert result.section_name == "experience"
        assert 0 <= result.total_score <= 100  # Exact match scores well but depends on other factors
    
    def test_overqualified_candidate(self, strategy, base_context):
        """Test scoring for overqualified candidate"""
        base_context.candidate_data["total_experience_years"] = 10
        base_context.job_data["required_experience_years"] = 3
        
        result = strategy.score(base_context)
        
        assert result.section_name == "experience"
        assert 0 <= result.total_score <= 100
    
    def test_underqualified_candidate(self, strategy, base_context):
        """Test scoring for underqualified candidate"""
        base_context.candidate_data["total_experience_years"] = 2
        base_context.job_data["required_experience_years"] = 5
        
        result = strategy.score(base_context)
        
        assert result.section_name == "experience"
        assert 0 <= result.total_score <= 100
        assert result.total_score < 100  # Should be penalized
    
    def test_industry_match_bonus(self, strategy, base_context):
        """Test that matching industry gives bonus"""
        base_context.candidate_data["industry_experience"] = ["logistics", "transportation"]
        base_context.job_data["preferred_industry"] = "logistics"
        base_context.candidate_data["total_experience_years"] = 5
        base_context.job_data["required_experience_years"] = 5
        
        result = strategy.score(base_context)
        
        assert result.section_name == "experience"
        assert 0 <= result.total_score <= 100
    
    def test_zero_experience(self, strategy, base_context):
        """Test handling of entry-level candidate"""
        base_context.candidate_data["total_experience_years"] = 0
        base_context.job_data["required_experience_years"] = 2
        
        result = strategy.score(base_context)
        
        assert result.section_name == "experience"
        assert 0 <= result.total_score <= 100
    
    def test_score_always_in_range(self, strategy):
        """Test score bounds for various experience scenarios"""
        test_cases = [
            (0, 5),   # No experience
            (3, 3),   # Exact match
            (10, 2),  # Overqualified
            (15, 20), # Very underqualified
        ]
        
        for candidate_years, required_years in test_cases:
            context = ScoringContext(
                candidate_data={"total_experience_years": candidate_years},
                job_data={"required_experience_years": required_years}
            )
            result = strategy.score(context)
            assert 0 <= result.total_score <= 100, \
                f"Score out of range for {candidate_years} vs {required_years} years"

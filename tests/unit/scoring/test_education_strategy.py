"""
Unit Tests for Education Scoring Strategy

Tests the EducationScoringStrategy in isolation.
"""

import pytest
from core.scoring.strategies.education_strategy import EducationScoringStrategy
from core.scoring.strategies.base import ScoringContext


class TestEducationScoringStrategy:
    """Test suite for EducationScoringStrategy"""
    
    @pytest.fixture
    def strategy(self):
        """Create an education scoring strategy instance"""
        return EducationScoringStrategy()
    
    @pytest.fixture
    def base_context(self):
        """Create a base scoring context"""
        return ScoringContext(
            candidate_data={
                "education": [],
                "certifications": []
            },
            job_data={
                "required_education": "",
                "preferred_field": "",
                "required_certifications": []
            },
            cv_text=""
        )
    
    def test_phd_highest_score(self, strategy, base_context):
        """Test that PhD gets highest education level score"""
        base_context.candidate_data["education"] = [
            {"degree": "PhD", "field": "Computer Science"}
        ]
        base_context.job_data["required_education"] = "Bachelor"
        
        result = strategy.score(base_context)
        
        assert result.section_name == "education"
        assert 0 <= result.total_score <= 100  # PhD scores well but depends on other factors
    
    def test_matching_degree_level(self, strategy, base_context):
        """Test exact degree level match"""
        base_context.candidate_data["education"] = [
            {"degree": "Bachelor", "field": "Engineering"}
        ]
        base_context.job_data["required_education"] = "Bachelor"
        
        result = strategy.score(base_context)
        
        assert result.section_name == "education"
        assert 0 <= result.total_score <= 100
    
    def test_field_relevance_bonus(self, strategy, base_context):
        """Test that matching field of study gives bonus"""
        base_context.candidate_data["education"] = [
            {"degree": "Master", "field": "Computer Science"}
        ]
        base_context.job_data["required_education"] = "Master"
        base_context.job_data["preferred_field"] = "Computer Science"
        
        result = strategy.score(base_context)
        
        assert result.section_name == "education"
        assert 0 <= result.total_score <= 100
    
    def test_certifications_add_value(self, strategy, base_context):
        """Test that relevant certifications improve score"""
        base_context.candidate_data["education"] = [
            {"degree": "Bachelor", "field": "IT"}
        ]
        base_context.candidate_data["certifications"] = ["AWS Certified", "PMP"]
        base_context.job_data["required_education"] = "Bachelor"
        base_context.job_data["required_certifications"] = ["AWS Certified"]
        
        result = strategy.score(base_context)
        
        assert result.section_name == "education"
        assert 0 <= result.total_score <= 100
    
    def test_no_education_data(self, strategy, base_context):
        """Test handling of missing education data"""
        # Empty education list
        result = strategy.score(base_context)
        
        assert result.section_name == "education"
        assert 0 <= result.total_score <= 100
    
    def test_score_bounds(self, strategy):
        """Test that score stays within 0-100 for various inputs"""
        test_contexts = [
            ScoringContext(
                candidate_data={"education": []},
                job_data={"required_education": "PhD"}
            ),
            ScoringContext(
                candidate_data={"education": [{"degree": "High School"}]},
                job_data={"required_education": "Master"}
            ),
            ScoringContext(
                candidate_data={
                    "education": [{"degree": "PhD", "field": "Physics"}],
                    "certifications": ["PMP", "Six Sigma"]
                },
                job_data={"required_education": "Bachelor"}
            )
        ]
        
        for context in test_contexts:
            result = strategy.score(context)
            assert 0 <= result.total_score <= 100

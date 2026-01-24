"""
Unit Tests for Personal Details Scoring Strategy

Tests the PersonalDetailsScoringStrategy in isolation.
"""

import pytest
from core.scoring.strategies.personal_details_strategy import PersonalDetailsScoringStrategy
from core.scoring.strategies.base import ScoringContext


class TestPersonalDetailsScoringStrategy:
    """Test suite for PersonalDetailsScoringStrategy"""
    
    @pytest.fixture
    def strategy(self):
        """Create a personal details scoring strategy instance"""
        return PersonalDetailsScoringStrategy()
    
    @pytest.fixture
    def base_context(self):
        """Create a base scoring context"""
        return ScoringContext(
            candidate_data={
                "nationality": "",
                "current_location": "",
                "visa_status": "",
                "availability": "",
                "gender": ""
            },
            job_data={
                "location": "",
                "gender_requirement": None
            },
            cv_text=""
        )
    
    def test_gcc_national_perfect_score(self, strategy, base_context):
        """Test that GCC nationals get perfect score"""
        base_context.candidate_data["nationality"] = "Saudi"
        
        result = strategy.score(base_context)
        
        assert result.section_name == "personal_details"
        assert 0 <= result.total_score <= 100
        assert result.total_score >= 80  # Should be high for GCC national
    
    def test_location_exact_match(self, strategy, base_context):
        """Test perfect score for exact location match"""
        base_context.candidate_data["current_location"] = "Riyadh"
        base_context.job_data["location"] = "Riyadh"
        
        result = strategy.score(base_context)
        
        assert result.section_name == "personal_details"
        assert 0 <= result.total_score <= 100
    
    def test_immediate_availability_high_score(self, strategy, base_context):
        """Test high score for immediate availability"""
        base_context.candidate_data["availability"] = "immediate"
        
        result = strategy.score(base_context)
        
        assert result.section_name == "personal_details"
        assert 0 <= result.total_score <= 100
    
    def test_missing_data_handles_gracefully(self, strategy, base_context):
        """Test that missing data doesn't crash"""
        # All fields empty/None
        result = strategy.score(base_context)
        
        assert result.section_name == "personal_details"
        assert 0 <= result.total_score <= 100
    
    def test_score_always_in_valid_range(self, strategy):
        """Test that score is always between 0-100 regardless of input"""
        contexts = [
            ScoringContext(
                candidate_data={"nationality": "Unknown"},
                job_data={}
            ),
            ScoringContext(
                candidate_data={},
                job_data={"location": "Tokyo"}
            ),
            ScoringContext(
                candidate_data={"nationality": "American", "current_location": "New York"},
                job_data={"location": "Dubai", "gender_requirement": "male"}
            )
        ]
        
        for context in contexts:
            result = strategy.score(context)
            assert 0 <= result.total_score <= 100, f"Score {result.total_score} out of range"

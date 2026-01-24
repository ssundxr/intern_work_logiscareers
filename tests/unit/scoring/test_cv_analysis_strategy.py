"""
Unit Tests for CV Analysis Scoring Strategy

Tests the CVAnalysisScoringStrategy in isolation.
"""

import pytest
from core.scoring.strategies.cv_analysis_strategy import CVAnalysisScoringStrategy
from core.scoring.strategies.base import ScoringContext


class TestCVAnalysisScoringStrategy:
    """Test suite for CVAnalysisScoringStrategy"""
    
    @pytest.fixture
    def strategy(self):
        """Create a CV analysis scoring strategy instance"""
        return CVAnalysisScoringStrategy()
    
    @pytest.fixture
    def base_context(self):
        """Create a base scoring context with minimal CV"""
        return ScoringContext(
            candidate_data={
                "cv_quality": {}
            },
            job_data={},
            cv_text="Sample CV text"
        )
    
    def test_well_formatted_cv_high_score(self, strategy, base_context):
        """Test that well-formatted CV gets high score"""
        base_context.candidate_data["cv_quality"] = {
            "format_score": 95,
            "completeness": 90,
            "keyword_density": 85
        }
        base_context.cv_text = "Detailed professional CV with relevant keywords and experience."
        
        result = strategy.score(base_context)
        
        assert hasattr(result, 'cv_score')
        assert 0 <= result.cv_score <= 100
    
    def test_poorly_formatted_cv_lower_score(self, strategy, base_context):
        """Test that poorly formatted CV gets lower score"""
        base_context.candidate_data["cv_quality"] = {
            "format_score": 40,
            "completeness": 50,
            "keyword_density": 30
        }
        base_context.cv_text = "Brief CV"
        
        result = strategy.score(base_context)
        
        assert hasattr(result, 'cv_score')
        assert 0 <= result.cv_score <= 100
    
    def test_empty_cv_handles_gracefully(self, strategy, base_context):
        """Test handling of empty or minimal CV"""
        base_context.cv_text = ""
        base_context.candidate_data["cv_quality"] = {}
        
        result = strategy.score(base_context)
        
        assert hasattr(result, 'cv_score')
        assert 0 <= result.cv_score <= 100
    
    def test_cv_with_keywords_bonus(self, strategy, base_context):
        """Test that keyword-rich CV gets bonus"""
        base_context.cv_text = """
        Senior Software Engineer with expertise in Python, FastAPI, Machine Learning.
        Led multiple projects using AWS, Docker, Kubernetes. Strong communication skills.
        """
        base_context.candidate_data["cv_quality"] = {
            "keyword_density": 90
        }
        
        result = strategy.score(base_context)
        
        assert hasattr(result, 'cv_score')
        assert 0 <= result.cv_score <= 100
    
    def test_score_always_in_range(self, strategy):
        """Test score bounds for various CV quality scenarios"""
        test_contexts = [
            ScoringContext(
                candidate_data={"cv_quality": {"format_score": 100}},
                job_data={},
                cv_text="Excellent detailed professional CV"
            ),
            ScoringContext(
                candidate_data={"cv_quality": {}},
                job_data={},
                cv_text=""
            ),
            ScoringContext(
                candidate_data={},
                job_data={},
                cv_text="Minimal CV text"
            )
        ]
        
        for context in test_contexts:
            result = strategy.score(context)
            assert 0 <= result.cv_score <= 100

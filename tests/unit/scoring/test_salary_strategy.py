"""
Unit Tests for Salary Scoring Strategy

Tests the SalaryScoringStrategy in isolation.
"""

import pytest
from core.scoring.strategies.salary_strategy import SalaryScoringStrategy
from core.scoring.strategies.base import ScoringContext


class TestSalaryScoringStrategy:
    """Test suite for SalaryScoringStrategy"""
    
    @pytest.fixture
    def strategy(self):
        """Create a salary scoring strategy instance"""
        return SalaryScoringStrategy()
    
    @pytest.fixture
    def base_context(self):
        """Create a base scoring context"""
        return ScoringContext(
            candidate_data={
                "salary_expectation": 0
            },
            job_data={
                "salary_min": 0,
                "salary_max": 0
            },
            cv_text=""
        )
    
    def test_salary_within_range_perfect_score(self, strategy, base_context):
        """Test perfect score when salary is within budget"""
        base_context.candidate_data["salary_expectation"] = 80000
        base_context.job_data["salary_min"] = 70000
        base_context.job_data["salary_max"] = 90000
        
        result = strategy.score(base_context)
        
        assert result.section_name == "salary"
        assert 0 <= result.total_score <= 100
        assert result.total_score >= 80  # Within range should score high
    
    def test_salary_at_lower_bound(self, strategy, base_context):
        """Test scoring when candidate expects minimum salary"""
        base_context.candidate_data["salary_expectation"] = 70000
        base_context.job_data["salary_min"] = 70000
        base_context.job_data["salary_max"] = 100000
        
        result = strategy.score(base_context)
        
        assert result.section_name == "salary"
        assert 0 <= result.total_score <= 100
    
    def test_salary_at_upper_bound(self, strategy, base_context):
        """Test scoring when candidate expects maximum salary"""
        base_context.candidate_data["salary_expectation"] = 100000
        base_context.job_data["salary_min"] = 70000
        base_context.job_data["salary_max"] = 100000
        
        result = strategy.score(base_context)
        
        assert result.section_name == "salary"
        assert 0 <= result.total_score <= 100
    
    def test_salary_above_budget(self, strategy, base_context):
        """Test penalty when candidate expects above budget"""
        base_context.candidate_data["salary_expectation"] = 120000
        base_context.job_data["salary_min"] = 70000
        base_context.job_data["salary_max"] = 90000
        
        result = strategy.score(base_context)
        
        assert result.section_name == "salary"
        assert 0 <= result.total_score <= 100
        assert result.total_score < 100  # Should be penalized
    
    def test_salary_below_budget(self, strategy, base_context):
        """Test scoring when candidate expects below budget"""
        base_context.candidate_data["salary_expectation"] = 50000
        base_context.job_data["salary_min"] = 70000
        base_context.job_data["salary_max"] = 90000
        
        result = strategy.score(base_context)
        
        assert result.section_name == "salary"
        assert 0 <= result.total_score <= 100
    
    def test_no_salary_data(self, strategy, base_context):
        """Test handling when salary data is missing"""
        # Zero or None values
        result = strategy.score(base_context)
        
        assert result.section_name == "salary"
        assert 0 <= result.total_score <= 100
    
    def test_score_bounds_various_ranges(self, strategy):
        """Test score stays in bounds for various salary scenarios"""
        test_cases = [
            (50000, 100000, 120000),   # Way below
            (100000, 80000, 120000),   # In range
            (150000, 80000, 120000),   # Way above
            (0, 50000, 100000),        # No expectation
        ]
        
        for expectation, min_sal, max_sal in test_cases:
            context = ScoringContext(
                candidate_data={"salary_expectation": expectation},
                job_data={"salary_min": min_sal, "salary_max": max_sal}
            )
            result = strategy.score(context)
            assert 0 <= result.total_score <= 100, \
                f"Score out of range for expectation={expectation}, range=[{min_sal}, {max_sal}]"

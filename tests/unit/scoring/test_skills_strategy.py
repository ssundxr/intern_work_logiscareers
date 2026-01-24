"""
Unit Tests for Skills Scoring Strategy

Tests the SkillsScoringStrategy in isolation using mock data.

Author: Production Testing
Date: January 24, 2026
"""

import pytest
from core.scoring.strategies.skills_strategy import SkillsScoringStrategy
from core.scoring.strategies.base import ScoringContext
from core.scoring.models import MatchLevel


class TestSkillsScoringStrategy:
    """Test suite for SkillsScoringStrategy"""
    
    @pytest.fixture
    def strategy(self):
        """Create a skills scoring strategy instance"""
        return SkillsScoringStrategy()
    
    @pytest.fixture
    def base_context(self):
        """Create a base scoring context"""
        return ScoringContext(
            candidate_data={
                "skills": []
            },
            job_data={
                "required_skills": [],
                "preferred_skills": [],
                "it_skills": []
            },
            cv_text=""
        )
    
    def test_perfect_required_skills_match(self, strategy, base_context):
        """Test scoring when all required skills are matched"""
        base_context.candidate_data["skills"] = ["Python", "SQL", "AWS"]
        base_context.job_data["required_skills"] = ["Python", "SQL", "AWS"]
        
        result = strategy.score(base_context)
        
        # Should have perfect match
        assert result.section_name == "skills"
        assert 0 <= result.total_score <= 100
        assert result.match_level == MatchLevel.EXCELLENT
        
        # Check required skills field
        required_field = next(f for f in result.fields if f.field_name == "required_skills")
        assert required_field.score == 100
    
    def test_partial_required_skills_match(self, strategy, base_context):
        """Test scoring when only some required skills are matched"""
        base_context.candidate_data["skills"] = ["Python", "SQL"]
        base_context.job_data["required_skills"] = ["Python", "SQL", "AWS", "Docker"]
        
        result = strategy.score(base_context)
        
        # Should have 50% match (2 out of 4)
        required_field = next(f for f in result.fields if f.field_name == "required_skills")
        assert required_field.score == 50
        assert result.match_level in [MatchLevel.PARTIAL, MatchLevel.GOOD]
    
    def test_no_required_skills_match(self, strategy, base_context):
        """Test scoring when no required skills are matched"""
        base_context.candidate_data["skills"] = ["Java", "Kotlin"]
        base_context.job_data["required_skills"] = ["Python", "SQL", "AWS"]
        
        result = strategy.score(base_context)
        
        # Should have 0% match
        required_field = next(f for f in result.fields if f.field_name == "required_skills")
        assert required_field.score == 0
        assert result.match_level == MatchLevel.POOR
    
    def test_preferred_skills_bonus(self, strategy, base_context):
        """Test that preferred skills contribute to overall score"""
        base_context.candidate_data["skills"] = ["Python", "SQL", "Machine Learning", "Deep Learning"]
        base_context.job_data["required_skills"] = ["Python", "SQL"]
        base_context.job_data["preferred_skills"] = ["Machine Learning", "Deep Learning"]
        
        result = strategy.score(base_context)
        
        # Should have both required and preferred matches
        required_field = next(f for f in result.fields if f.field_name == "required_skills")
        preferred_field = next(f for f in result.fields if f.field_name == "preferred_skills")
        
        assert required_field.score == 100  # All required skills matched
        assert preferred_field.score == 100  # All preferred skills matched
        assert 0 <= result.total_score <= 100  # Combined should be in valid range
    
    def test_case_insensitive_skill_matching(self, strategy, base_context):
        """Test that skill matching is case-insensitive"""
        base_context.candidate_data["skills"] = ["python", "sql", "aws"]
        base_context.job_data["required_skills"] = ["Python", "SQL", "AWS"]
        
        result = strategy.score(base_context)
        
        required_field = next(f for f in result.fields if f.field_name == "required_skills")
        assert required_field.score == 100
    
    def test_empty_required_skills(self, strategy, base_context):
        """Test handling when job has no required skills"""
        base_context.candidate_data["skills"] = ["Python", "SQL"]
        base_context.job_data["required_skills"] = []
        
        result = strategy.score(base_context)
        
        # Should not fail, should give decent score
        assert result.total_score >= 50
        assert result.section_name == "skills"
    
    def test_empty_candidate_skills(self, strategy, base_context):
        """Test handling when candidate has no skills listed"""
        base_context.candidate_data["skills"] = []
        base_context.job_data["required_skills"] = ["Python", "SQL", "AWS"]
        
        result = strategy.score(base_context)
        
        # Should have low score but not crash
        assert 0 <= result.total_score <= 100
        assert result.match_level == MatchLevel.POOR


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

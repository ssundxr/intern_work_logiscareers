"""
Phase 4: Smoke Tests (No TensorFlow dependencies)
Quick validation of Phase 4 components without ML dependencies.
"""

import pytest
from logis_ai_candidate_engine.core.schemas.job import Job
from logis_ai_candidate_engine.core.schemas.candidate import Candidate
from logis_ai_candidate_engine.core.scoring.contextual_adjuster import ContextualAdjuster
from logis_ai_candidate_engine.core.scoring.confidence_calculator import (
    ConfidenceCalculator,
    ConfidenceLevel,
)
from logis_ai_candidate_engine.core.scoring.advanced_scorer import (
    FeatureInteractionDetector,
    SmartWeightOptimizer,
)


def test_contextual_adjuster_imports():
    """Test that ContextualAdjuster can be imported and instantiated."""
    adjuster = ContextualAdjuster()
    assert adjuster is not None


def test_confidence_calculator_imports():
    """Test that ConfidenceCalculator can be imported and instantiated."""
    calculator = ConfidenceCalculator()
    assert calculator is not None


def test_feature_interaction_detector_imports():
    """Test that FeatureInteractionDetector can be imported and instantiated."""
    detector = FeatureInteractionDetector()
    assert detector is not None


def test_smart_weight_optimizer_imports():
    """Test that SmartWeightOptimizer can be imported and instantiated."""
    optimizer = SmartWeightOptimizer()
    assert optimizer is not None


def test_smart_weights_entry_level():
    """Test entry-level job gets skills-heavy weights."""
    optimizer = SmartWeightOptimizer()
    
    entry_job = Job(
        id="job-entry",
        title="Logistics Coordinator",
        min_experience_years=0,
        max_experience_years=2,
        required_skills=["Excel", "Communication"],
        preferred_skills=[],
        min_salary=40000,
        max_salary=60000,
        location="Dubai",
        gcc_required=False,
        description="Entry level position",
    )
    
    weights = optimizer.get_optimized_weights(entry_job)
    
    # Entry level should prioritize skills
    assert weights["skills"] >= 0.30
    assert weights["experience"] <= 0.25
    assert abs(sum(weights.values()) - 1.0) < 0.01


def test_smart_weights_senior_level():
    """Test senior-level job gets experience-heavy weights."""
    optimizer = SmartWeightOptimizer()
    
    senior_job = Job(
        id="job-senior",
        title="Director of Logistics",
        min_experience_years=12,
        max_experience_years=20,
        required_skills=["Strategic Planning", "Leadership"],
        preferred_skills=[],
        min_salary=200000,
        max_salary=300000,
        location="Dubai",
        gcc_required=True,
        description="Senior leadership role",
    )
    
    weights = optimizer.get_optimized_weights(senior_job)
    
    # Senior should emphasize experience and domain
    assert weights["experience"] >= 0.25
    assert weights["semantic"] >= 0.30
    assert abs(sum(weights.values()) - 1.0) < 0.01


def test_contextual_adjuster_gcc_bonus():
    """Test GCC experience bonus rule (without full scoring)."""
    adjuster = ContextualAdjuster()
    
    gcc_job = Job(
        id="job-gcc",
        title="Supply Chain Manager",
        min_experience_years=5,
        max_experience_years=10,
        required_skills=["Supply Chain"],
        preferred_skills=[],
        min_salary=100000,
        max_salary=150000,
        location="Dubai",
        gcc_required=True,
        description="GCC role",
    )
    
    gcc_candidate = Candidate(
        id="cand-gcc",
        name="Ahmed",
        total_experience_years=8,
        gcc_experience_years=8,
        skills=["Supply Chain"],
        current_salary=120000,
        expected_salary=130000,
        location="Dubai",
        job_history=[{"title": "Manager", "company": "Co1", "years": 8, "location": "Dubai"}],
    )
    
    # Create mock results
    from logis_ai_candidate_engine.core.scoring.skills_scorer import SkillsResult
    from logis_ai_candidate_engine.core.scoring.experience_scorer import ExperienceResult
    
    mock_skills = SkillsResult(
        score=85,
        matched_skills=["Supply Chain"],
        missing_skills=[],
        matched_required=["Supply Chain"],
        matched_preferred=[],
        missing_required=[],
        missing_preferred=[],
        exact_matches=1,
        synonym_matches=0,
        semantic_matches=0,
        match_details=[],
        explanation="Good match",
    )
    
    mock_experience = ExperienceResult(
        score=90,
        explanation="Perfect experience fit",
    )
    
    base_score = 80
    adjusted, adjustments = adjuster.apply_adjustments(
        base_score, gcc_job, gcc_candidate, mock_skills, mock_experience
    )
    
    # Should get GCC bonus
    assert adjusted > base_score
    gcc_adjustments = [a for a in adjustments if "GCC" in a.rule_code]
    assert len(gcc_adjustments) > 0


def test_confidence_calculator_basic():
    """Test basic confidence calculation."""
    calculator = ConfidenceCalculator()
    
    complete_candidate = Candidate(
        id="cand-complete",
        name="Complete Profile",
        total_experience_years=7,
        gcc_experience_years=5,
        skills=["Skill1", "Skill2", "Skill3"],
        current_salary=120000,
        expected_salary=130000,
        location="Dubai",
        job_history=[{"title": "Manager", "company": "Co1", "years": 7, "location": "Dubai"}],
    )
    
    from logis_ai_candidate_engine.core.scoring.skills_scorer import SkillsResult
    from logis_ai_candidate_engine.core.scoring.experience_scorer import ExperienceResult
    
    mock_skills = SkillsResult(
        score=85,
        matched_skills=["Skill1", "Skill2"],
        missing_skills=["Skill3"],
        matched_required=["Skill1"],
        matched_preferred=["Skill2"],
        missing_required=[],
        missing_preferred=["Skill3"],
        exact_matches=2,
        synonym_matches=0,
        semantic_matches=0,
        match_details=[],
        explanation="Good match",
    )
    
    mock_experience = ExperienceResult(
        score=90,
        explanation="Perfect fit",
    )
    
    section_scores = {"skills": 85, "experience": 90, "semantic": 88}
    adjusted_score = 87
    
    confidence = calculator.calculate_confidence(
        complete_candidate, mock_skills, mock_experience, section_scores, adjusted_score
    )
    
    # Complete profile should have high confidence
    assert confidence.confidence_level in [ConfidenceLevel.HIGH, ConfidenceLevel.VERY_HIGH]
    assert confidence.confidence_score >= 0.70


def test_feature_interaction_detector_basic():
    """Test basic feature interaction detection."""
    detector = FeatureInteractionDetector()
    
    job = Job(
        id="job-test",
        title="Test Job",
        min_experience_years=5,
        max_experience_years=10,
        required_skills=["Skill1", "Skill2"],
        preferred_skills=[],
        min_salary=100000,
        max_salary=150000,
        location="Dubai",
        gcc_required=False,
        description="Test",
    )
    
    candidate = Candidate(
        id="cand-test",
        name="Test",
        total_experience_years=7,
        gcc_experience_years=0,
        skills=["Skill1", "Skill2", "Skill3"],
        current_salary=120000,
        expected_salary=130000,
        location="Dubai",
        job_history=[{"title": "Manager", "company": "Co1", "years": 7, "location": "Dubai"}],
    )
    
    from logis_ai_candidate_engine.core.scoring.skills_scorer import SkillsResult
    from logis_ai_candidate_engine.core.scoring.experience_scorer import ExperienceResult
    
    mock_skills = SkillsResult(
        score=90,
        matched_skills=["Skill1", "Skill2"],
        missing_skills=[],
        matched_required=["Skill1", "Skill2"],
        matched_preferred=[],
        missing_required=[],
        missing_preferred=[],
        exact_matches=2,
        synonym_matches=0,
        semantic_matches=0,
        match_details=[],
        explanation="Perfect match",
    )
    
    mock_experience = ExperienceResult(
        score=85,
        explanation="Good fit",
    )
    
    interactions = detector.detect_interactions(job, candidate, mock_skills, mock_experience, 88)
    
    # Should detect at least no errors
    assert isinstance(interactions, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

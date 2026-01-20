"""
Phase 4: Advanced Hybrid Scoring Integration Tests
Enterprise-grade test suite for contextual adjustments, confidence scoring,
feature interactions, and smart weight optimization.
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
from logis_ai_candidate_engine.core.scoring.skills_scorer import SkillsScorer
from logis_ai_candidate_engine.core.scoring.experience_scorer import ExperienceScorer
from logis_ai_candidate_engine.ml.embedding_model import EmbeddingModel


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def embedding_model():
    """Shared embedding model for skill scoring."""
    return EmbeddingModel()


@pytest.fixture
def gcc_job():
    """Sample GCC logistics job for testing."""
    return Job(
        id="job-001",
        title="Supply Chain Manager - GCC",
        min_experience_years=5,
        max_experience_years=10,
        required_skills=[
            "Supply Chain Management",
            "Logistics Planning",
            "Inventory Management",
            "Transportation Management",
        ],
        preferred_skills=["SAP", "Power BI", "Six Sigma"],
        min_salary=100000,
        max_salary=150000,
        location="Dubai, UAE",
        gcc_required=True,
        description="Lead supply chain operations for GCC region",
    )


@pytest.fixture
def entry_level_job():
    """Entry-level logistics coordinator job."""
    return Job(
        id="job-002",
        title="Logistics Coordinator",
        min_experience_years=0,
        max_experience_years=2,
        required_skills=["MS Excel", "Communication", "Data Entry"],
        preferred_skills=["SAP Basics"],
        min_salary=40000,
        max_salary=60000,
        location="Dubai, UAE",
        gcc_required=False,
        description="Support logistics operations team",
    )


@pytest.fixture
def senior_level_job():
    """Senior director logistics job."""
    return Job(
        id="job-003",
        title="Director of Logistics & Operations",
        min_experience_years=12,
        max_experience_years=20,
        required_skills=[
            "Strategic Planning",
            "Supply Chain Strategy",
            "Team Leadership",
            "Budget Management",
            "Vendor Management",
        ],
        preferred_skills=["MBA", "Six Sigma Black Belt", "SAP EWM"],
        min_salary=200000,
        max_salary=300000,
        location="Riyadh, Saudi Arabia",
        gcc_required=True,
        description="Strategic leadership for regional logistics",
    )


@pytest.fixture
def gcc_veteran_candidate():
    """Perfect GCC veteran candidate."""
    return Candidate(
        id="cand-001",
        name="Ahmed Al-Mansouri",
        total_experience_years=8,
        gcc_experience_years=8,
        skills=[
            "Supply Chain Management",
            "Logistics Planning",
            "Inventory Management",
            "Transportation Management",
            "SAP",
            "Power BI",
            "Six Sigma Green Belt",
        ],
        current_salary=135000,
        expected_salary=145000,
        location="Dubai, UAE",
        job_history=[
            {
                "title": "Supply Chain Manager",
                "company": "Aramex",
                "years": 4,
                "location": "Dubai, UAE",
            },
            {
                "title": "Logistics Supervisor",
                "company": "DP World",
                "years": 4,
                "location": "Jebel Ali, UAE",
            },
        ],
    )


@pytest.fixture
def overqualified_candidate():
    """Severely overqualified candidate."""
    return Candidate(
        id="cand-002",
        name="John Smith",
        total_experience_years=18,
        gcc_experience_years=2,
        skills=[
            "Supply Chain Management",
            "Logistics Planning",
            "Strategic Planning",
            "SAP EWM",
            "Six Sigma Black Belt",
        ],
        current_salary=180000,
        expected_salary=220000,
        location="Dubai, UAE",
        job_history=[
            {
                "title": "VP Supply Chain",
                "company": "Global Corp",
                "years": 8,
                "location": "Singapore",
            },
            {
                "title": "Director Logistics",
                "company": "MegaCorp",
                "years": 10,
                "location": "Hong Kong",
            },
        ],
    )


@pytest.fixture
def job_hopper_candidate():
    """Candidate with frequent job changes."""
    return Candidate(
        id="cand-003",
        name="Frequent Changer",
        total_experience_years=6,
        gcc_experience_years=3,
        skills=["Supply Chain Management", "Logistics Planning", "SAP"],
        current_salary=110000,
        expected_salary=130000,
        location="Dubai, UAE",
        job_history=[
            {"title": "Supply Chain Analyst", "company": "Co1", "years": 1, "location": "Dubai"},
            {"title": "Logistics Coordinator", "company": "Co2", "years": 1, "location": "Dubai"},
            {"title": "SC Manager", "company": "Co3", "years": 1.5, "location": "Abu Dhabi"},
            {"title": "Operations Manager", "company": "Co4", "years": 1, "location": "Dubai"},
            {"title": "Supply Chain Lead", "company": "Co5", "years": 1.5, "location": "Dubai"},
        ],
    )


@pytest.fixture
def perfect_match_candidate():
    """100% perfect match candidate."""
    return Candidate(
        id="cand-004",
        name="Perfect Match",
        total_experience_years=7,
        gcc_experience_years=7,
        skills=[
            "Supply Chain Management",
            "Logistics Planning",
            "Inventory Management",
            "Transportation Management",
            "SAP",
            "Power BI",
            "Six Sigma",
        ],
        current_salary=120000,
        expected_salary=130000,
        location="Dubai, UAE",
        job_history=[
            {
                "title": "Supply Chain Manager",
                "company": "Top Logistics Co",
                "years": 7,
                "location": "Dubai, UAE",
            }
        ],
    )


# ============================================================================
# Contextual Adjustment Tests
# ============================================================================


def test_gcc_experience_major_bonus(gcc_job, gcc_veteran_candidate, embedding_model):
    """Test GCC experience major bonus for 8 years GCC experience."""
    adjuster = ContextualAdjuster()
    skills_scorer = SkillsScorer(embedding_model=embedding_model)
    exp_scorer = ExperienceScorer()

    skills_result = skills_scorer.score(
        gcc_job.required_skills, gcc_veteran_candidate.skills, gcc_job.preferred_skills
    )
    exp_result = exp_scorer.score(
        gcc_job.min_experience_years,
        gcc_job.max_experience_years,
        gcc_veteran_candidate.total_experience_years,
    )

    base_score = 75
    adjusted, adjustments = adjuster.apply_adjustments(
        base_score, gcc_job, gcc_veteran_candidate, skills_result, exp_result
    )

    # Should get GCC_EXP_MAJOR_BONUS (+8)
    gcc_bonus = [a for a in adjustments if a.rule_code == "GCC_EXP_MAJOR_BONUS"]
    assert len(gcc_bonus) == 1
    assert gcc_bonus[0].impact == 8
    assert adjusted == 83


def test_perfect_skills_bonus(gcc_job, perfect_match_candidate, embedding_model):
    """Test perfect skills match bonus."""
    adjuster = ContextualAdjuster()
    skills_scorer = SkillsScorer(embedding_model=embedding_model)
    exp_scorer = ExperienceScorer()

    skills_result = skills_scorer.score(
        gcc_job.required_skills, perfect_match_candidate.skills, gcc_job.preferred_skills
    )
    exp_result = exp_scorer.score(
        gcc_job.min_experience_years,
        gcc_job.max_experience_years,
        perfect_match_candidate.total_experience_years,
    )

    # Perfect match should have 100% required + 100% preferred
    assert len(skills_result.missing_required) == 0
    assert len(skills_result.missing_preferred) == 0

    base_score = 85
    adjusted, adjustments = adjuster.apply_adjustments(
        base_score, gcc_job, perfect_match_candidate, skills_result, exp_result
    )

    # Should get PERFECT_SKILLS bonus (+5)
    perfect_bonus = [a for a in adjustments if a.rule_code == "PERFECT_SKILLS"]
    assert len(perfect_bonus) == 1
    assert perfect_bonus[0].impact == 5


def test_severe_overqualified_penalty(gcc_job, overqualified_candidate, embedding_model):
    """Test penalty for severely overqualified candidate."""
    adjuster = ContextualAdjuster()
    skills_scorer = SkillsScorer(embedding_model=embedding_model)
    exp_scorer = ExperienceScorer()

    skills_result = skills_scorer.score(
        gcc_job.required_skills, overqualified_candidate.skills, gcc_job.preferred_skills
    )
    exp_result = exp_scorer.score(
        gcc_job.min_experience_years,
        gcc_job.max_experience_years,
        overqualified_candidate.total_experience_years,
    )

    base_score = 78
    adjusted, adjustments = adjuster.apply_adjustments(
        base_score, gcc_job, overqualified_candidate, skills_result, exp_result
    )

    # Should get SEVERE_OVERQUALIFIED penalty (-5)
    overqualified_penalty = [a for a in adjustments if a.rule_code == "SEVERE_OVERQUALIFIED"]
    assert len(overqualified_penalty) == 1
    assert overqualified_penalty[0].impact == -5
    assert adjusted < base_score


def test_job_hopping_penalty(gcc_job, job_hopper_candidate, embedding_model):
    """Test penalty for job hopping (5 jobs in 6 years)."""
    adjuster = ContextualAdjuster()
    skills_scorer = SkillsScorer(embedding_model=embedding_model)
    exp_scorer = ExperienceScorer()

    skills_result = skills_scorer.score(
        gcc_job.required_skills, job_hopper_candidate.skills, gcc_job.preferred_skills
    )
    exp_result = exp_scorer.score(
        gcc_job.min_experience_years,
        gcc_job.max_experience_years,
        job_hopper_candidate.total_experience_years,
    )

    base_score = 70
    adjusted, adjustments = adjuster.apply_adjustments(
        base_score, gcc_job, job_hopper_candidate, skills_result, exp_result
    )

    # Should get JOB_HOPPING penalty (-4)
    hopping_penalty = [a for a in adjustments if a.rule_code == "JOB_HOPPING"]
    assert len(hopping_penalty) == 1
    assert hopping_penalty[0].impact == -4
    assert "5 jobs in 6.0 years" in hopping_penalty[0].reason


def test_salary_sweet_spot_bonus(gcc_job, gcc_veteran_candidate, embedding_model):
    """Test salary sweet spot bonus."""
    adjuster = ContextualAdjuster()
    skills_scorer = SkillsScorer(embedding_model=embedding_model)
    exp_scorer = ExperienceScorer()

    skills_result = skills_scorer.score(
        gcc_job.required_skills, gcc_veteran_candidate.skills, gcc_job.preferred_skills
    )
    exp_result = exp_scorer.score(
        gcc_job.min_experience_years,
        gcc_job.max_experience_years,
        gcc_veteran_candidate.total_experience_years,
    )

    base_score = 80
    adjusted, adjustments = adjuster.apply_adjustments(
        base_score, gcc_job, gcc_veteran_candidate, skills_result, exp_result
    )

    # Expected salary (145k) is within sweet spot (125k-150k for 100k-150k range)
    sweet_spot = [a for a in adjustments if a.rule_code == "SALARY_SWEET_SPOT"]
    assert len(sweet_spot) == 1
    assert sweet_spot[0].impact == 3


def test_cumulative_adjustments(gcc_job, perfect_match_candidate, embedding_model):
    """Test multiple adjustments applied cumulatively."""
    adjuster = ContextualAdjuster()
    skills_scorer = SkillsScorer(embedding_model=embedding_model)
    exp_scorer = ExperienceScorer()

    skills_result = skills_scorer.score(
        gcc_job.required_skills, perfect_match_candidate.skills, gcc_job.preferred_skills
    )
    exp_result = exp_scorer.score(
        gcc_job.min_experience_years,
        gcc_job.max_experience_years,
        perfect_match_candidate.total_experience_years,
    )

    base_score = 85
    adjusted, adjustments = adjuster.apply_adjustments(
        base_score, gcc_job, perfect_match_candidate, skills_result, exp_result
    )

    # Perfect candidate should get multiple bonuses
    assert len(adjustments) >= 3  # GCC bonus, perfect skills, salary sweet spot
    assert adjusted > base_score
    
    # Calculate total delta
    total_delta = sum(a.impact for a in adjustments)
    assert adjusted == min(100, base_score + total_delta)  # Capped at 100


# ============================================================================
# Confidence Scoring Tests
# ============================================================================


def test_confidence_very_high_complete_data(gcc_job, gcc_veteran_candidate, embedding_model):
    """Test very high confidence for complete, consistent data."""
    calculator = ConfidenceCalculator()
    skills_scorer = SkillsScorer(embedding_model=embedding_model)
    exp_scorer = ExperienceScorer()

    skills_result = skills_scorer.score(
        gcc_job.required_skills, gcc_veteran_candidate.skills, gcc_job.preferred_skills
    )
    exp_result = exp_scorer.score(
        gcc_job.min_experience_years,
        gcc_job.max_experience_years,
        gcc_veteran_candidate.total_experience_years,
    )

    section_scores = {"skills": 90, "experience": 85, "semantic": 88}
    adjusted_score = 88

    confidence = calculator.calculate_confidence(
        gcc_veteran_candidate, skills_result, exp_result, section_scores, adjusted_score
    )

    # Complete data, high scores, consistent signals
    assert confidence.confidence_level in [ConfidenceLevel.VERY_HIGH, ConfidenceLevel.HIGH]
    assert confidence.confidence_score >= 0.75
    assert len(confidence.uncertainty_factors) <= 2


def test_confidence_low_incomplete_data(gcc_job, embedding_model):
    """Test low confidence for incomplete candidate data."""
    calculator = ConfidenceCalculator()
    skills_scorer = SkillsScorer(embedding_model=embedding_model)
    exp_scorer = ExperienceScorer()

    # Incomplete candidate (missing salary, location, job history)
    incomplete_candidate = Candidate(
        id="cand-incomplete",
        name="Incomplete Profile",
        total_experience_years=5,
        gcc_experience_years=0,
        skills=["Supply Chain Management"],
        current_salary=None,
        expected_salary=None,
        location=None,
        job_history=None,
    )

    skills_result = skills_scorer.score(
        gcc_job.required_skills, incomplete_candidate.skills, gcc_job.preferred_skills
    )
    exp_result = exp_scorer.score(
        gcc_job.min_experience_years, gcc_job.max_experience_years, incomplete_candidate.total_experience_years
    )

    section_scores = {"skills": 45, "experience": 70, "semantic": 50}
    adjusted_score = 55

    confidence = calculator.calculate_confidence(
        incomplete_candidate, skills_result, exp_result, section_scores, adjusted_score
    )

    # Incomplete data should reduce confidence
    assert confidence.confidence_level in [ConfidenceLevel.LOW, ConfidenceLevel.MEDIUM]
    assert "incomplete_profile" in confidence.uncertainty_factors or "weak_signals" in confidence.uncertainty_factors


def test_confidence_signal_disagreement(gcc_job, embedding_model):
    """Test lower confidence when signals disagree."""
    calculator = ConfidenceCalculator()
    skills_scorer = SkillsScorer(embedding_model=embedding_model)
    exp_scorer = ExperienceScorer()

    # Candidate with conflicting signals (high exp, low skills)
    conflicting_candidate = Candidate(
        id="cand-conflict",
        name="Conflicting Signals",
        total_experience_years=8,
        gcc_experience_years=5,
        skills=["MS Excel"],  # Very few skills for senior role
        current_salary=120000,
        expected_salary=140000,
        location="Dubai, UAE",
        job_history=[{"title": "Manager", "company": "Co1", "years": 8, "location": "Dubai"}],
    )

    skills_result = skills_scorer.score(
        gcc_job.required_skills, conflicting_candidate.skills, gcc_job.preferred_skills
    )
    exp_result = exp_scorer.score(
        gcc_job.min_experience_years, gcc_job.max_experience_years, conflicting_candidate.total_experience_years
    )

    # Highly divergent section scores
    section_scores = {"skills": 30, "experience": 90, "semantic": 45}
    adjusted_score = 55

    confidence = calculator.calculate_confidence(
        conflicting_candidate, skills_result, exp_result, section_scores, adjusted_score
    )

    # Signal disagreement should reduce confidence
    assert "signal_disagreement" in confidence.uncertainty_factors
    assert confidence.confidence_score < 0.75


# ============================================================================
# Feature Interaction Tests
# ============================================================================


def test_interaction_skills_comp_exp(gcc_job, embedding_model):
    """Test SKILLS_COMP_EXP interaction (high skills compensate for low exp)."""
    detector = FeatureInteractionDetector()
    skills_scorer = SkillsScorer(embedding_model=embedding_model)
    exp_scorer = ExperienceScorer()

    # Junior candidate with excellent skills
    junior_expert = Candidate(
        id="cand-junior-expert",
        name="Junior Expert",
        total_experience_years=3,  # Below min (5)
        gcc_experience_years=2,
        skills=[
            "Supply Chain Management",
            "Logistics Planning",
            "Inventory Management",
            "Transportation Management",
            "SAP",
            "Power BI",
            "Six Sigma",
        ],
        current_salary=80000,
        expected_salary=100000,
        location="Dubai, UAE",
        job_history=[{"title": "SC Analyst", "company": "Co1", "years": 3, "location": "Dubai"}],
    )

    skills_result = skills_scorer.score(
        gcc_job.required_skills, junior_expert.skills, gcc_job.preferred_skills
    )
    exp_result = exp_scorer.score(
        gcc_job.min_experience_years, gcc_job.max_experience_years, junior_expert.total_experience_years
    )

    interactions = detector.detect_interactions(gcc_job, junior_expert, skills_result, exp_result, 75)

    # Should detect SKILLS_COMP_EXP
    skills_comp = [i for i in interactions if i.interaction_type == "SKILLS_COMP_EXP"]
    assert len(skills_comp) == 1
    assert skills_comp[0].impact > 0
    assert "high skills" in skills_comp[0].description.lower()


def test_interaction_exp_comp_skills(gcc_job, embedding_model):
    """Test EXP_COMP_SKILLS interaction (high exp compensates for skill gaps)."""
    detector = FeatureInteractionDetector()
    skills_scorer = SkillsScorer(embedding_model=embedding_model)
    exp_scorer = ExperienceScorer()

    # Senior candidate with fewer listed skills
    senior_basic = Candidate(
        id="cand-senior-basic",
        name="Senior Basic",
        total_experience_years=12,
        gcc_experience_years=8,
        skills=["Supply Chain Management", "Logistics Planning"],  # Missing some required
        current_salary=140000,
        expected_salary=160000,
        location="Dubai, UAE",
        job_history=[{"title": "SC Director", "company": "Co1", "years": 12, "location": "Dubai"}],
    )

    skills_result = skills_scorer.score(
        gcc_job.required_skills, senior_basic.skills, gcc_job.preferred_skills
    )
    exp_result = exp_scorer.score(
        gcc_job.min_experience_years, gcc_job.max_experience_years, senior_basic.total_experience_years
    )

    interactions = detector.detect_interactions(gcc_job, senior_basic, skills_result, exp_result, 72)

    # Should detect EXP_COMP_SKILLS
    exp_comp = [i for i in interactions if i.interaction_type == "EXP_COMP_SKILLS"]
    assert len(exp_comp) == 1
    assert exp_comp[0].impact > 0


def test_interaction_perfect_candidate_amp(gcc_job, perfect_match_candidate, embedding_model):
    """Test PERFECT_CANDIDATE_AMP interaction (amplification of perfect match)."""
    detector = FeatureInteractionDetector()
    skills_scorer = SkillsScorer(embedding_model=embedding_model)
    exp_scorer = ExperienceScorer()

    skills_result = skills_scorer.score(
        gcc_job.required_skills, perfect_match_candidate.skills, gcc_job.preferred_skills
    )
    exp_result = exp_scorer.score(
        gcc_job.min_experience_years, gcc_job.max_experience_years, perfect_match_candidate.total_experience_years
    )

    interactions = detector.detect_interactions(gcc_job, perfect_match_candidate, skills_result, exp_result, 95)

    # Should detect PERFECT_CANDIDATE_AMP
    perfect_amp = [i for i in interactions if i.interaction_type == "PERFECT_CANDIDATE_AMP"]
    assert len(perfect_amp) == 1
    assert perfect_amp[0].impact > 0
    assert perfect_amp[0].impact >= 3  # Strong amplification


def test_interaction_career_changer(embedding_model):
    """Test CAREER_CHANGER interaction detection."""
    detector = FeatureInteractionDetector()
    skills_scorer = SkillsScorer(embedding_model=embedding_model)
    exp_scorer = ExperienceScorer()

    # Non-GCC job for career changer test
    tech_job = Job(
        id="job-tech",
        title="Supply Chain Analyst",
        min_experience_years=2,
        max_experience_years=5,
        required_skills=["Supply Chain Management", "Data Analysis", "Excel"],
        preferred_skills=["SQL", "Python"],
        min_salary=60000,
        max_salary=80000,
        location="Dubai, UAE",
        gcc_required=False,
        description="Analyze supply chain data",
    )

    # Career changer: lots of experience, low skills match
    career_changer = Candidate(
        id="cand-changer",
        name="Career Changer",
        total_experience_years=10,
        gcc_experience_years=0,
        skills=["Project Management", "Excel"],  # Few matching skills
        current_salary=70000,
        expected_salary=75000,
        location="Dubai, UAE",
        job_history=[{"title": "IT Manager", "company": "Co1", "years": 10, "location": "Dubai"}],
    )

    skills_result = skills_scorer.score(tech_job.required_skills, career_changer.skills, tech_job.preferred_skills)
    exp_result = exp_scorer.score(
        tech_job.min_experience_years, tech_job.max_experience_years, career_changer.total_experience_years
    )

    interactions = detector.detect_interactions(tech_job, career_changer, skills_result, exp_result, 55)

    # Should detect CAREER_CHANGER
    career_change = [i for i in interactions if i.interaction_type == "CAREER_CHANGER"]
    assert len(career_change) == 1
    assert career_change[0].impact < 0  # Negative impact


# ============================================================================
# Smart Weight Optimization Tests
# ============================================================================


def test_smart_weights_entry_level(entry_level_job):
    """Test entry-level job gets skills-heavy weights."""
    optimizer = SmartWeightOptimizer()
    weights = optimizer.get_optimized_weights(entry_level_job)

    # Entry level should prioritize skills
    assert weights["skills"] >= 0.3
    assert weights["experience"] <= 0.25
    assert "skills" in weights and "experience" in weights and "semantic" in weights


def test_smart_weights_mid_level(gcc_job):
    """Test mid-level job gets balanced weights."""
    optimizer = SmartWeightOptimizer()
    weights = optimizer.get_optimized_weights(gcc_job)

    # Mid-level should be balanced
    assert 0.25 <= weights["skills"] <= 0.35
    assert 0.20 <= weights["experience"] <= 0.30
    assert 0.30 <= weights["semantic"] <= 0.40


def test_smart_weights_senior_level(senior_level_job):
    """Test senior-level job gets experience/domain-heavy weights."""
    optimizer = SmartWeightOptimizer()
    weights = optimizer.get_optimized_weights(senior_level_job)

    # Senior should emphasize experience and domain fit
    assert weights["experience"] >= 0.25
    assert weights["semantic"] >= 0.30  # Domain fit important
    assert weights["skills"] <= 0.30  # Skills less critical


def test_smart_weights_sum_to_one(gcc_job):
    """Test that optimized weights always sum to 1.0."""
    optimizer = SmartWeightOptimizer()
    weights = optimizer.get_optimized_weights(gcc_job)

    total = sum(weights.values())
    assert abs(total - 1.0) < 0.01  # Allow small floating point error


# ============================================================================
# End-to-End Integration Tests
# ============================================================================


def test_e2e_gcc_veteran_high_score(gcc_job, gcc_veteran_candidate, embedding_model):
    """End-to-end test: GCC veteran should score very high with bonuses."""
    adjuster = ContextualAdjuster()
    confidence_calc = ConfidenceCalculator()
    interaction_detector = FeatureInteractionDetector()
    weight_optimizer = SmartWeightOptimizer()

    skills_scorer = SkillsScorer(embedding_model=embedding_model)
    exp_scorer = ExperienceScorer()

    # Get optimized weights
    weights = weight_optimizer.get_optimized_weights(gcc_job)

    # Score sections
    skills_result = skills_scorer.score(
        gcc_job.required_skills, gcc_veteran_candidate.skills, gcc_job.preferred_skills
    )
    exp_result = exp_scorer.score(
        gcc_job.min_experience_years, gcc_job.max_experience_years, gcc_veteran_candidate.total_experience_years
    )

    # Simulate aggregated base score
    base_score = 80

    # Apply contextual adjustments
    adjusted_score, adjustments = adjuster.apply_adjustments(
        base_score, gcc_job, gcc_veteran_candidate, skills_result, exp_result
    )

    # Calculate confidence
    section_scores = {"skills": 85, "experience": 85, "semantic": 80}
    confidence = confidence_calc.calculate_confidence(
        gcc_veteran_candidate, skills_result, exp_result, section_scores, adjusted_score
    )

    # Detect interactions
    interactions = interaction_detector.detect_interactions(
        gcc_job, gcc_veteran_candidate, skills_result, exp_result, base_score
    )

    # Assertions
    assert adjusted_score > base_score  # Should get bonuses
    assert adjusted_score >= 85  # High final score
    assert len(adjustments) >= 2  # Multiple bonuses applied
    assert confidence.confidence_level in [ConfidenceLevel.HIGH, ConfidenceLevel.VERY_HIGH]
    assert len(interactions) >= 0  # May or may not have interactions


def test_e2e_overqualified_penalty(gcc_job, overqualified_candidate, embedding_model):
    """End-to-end test: Overqualified candidate should get penalty."""
    adjuster = ContextualAdjuster()
    skills_scorer = SkillsScorer(embedding_model=embedding_model)
    exp_scorer = ExperienceScorer()

    skills_result = skills_scorer.score(
        gcc_job.required_skills, overqualified_candidate.skills, gcc_job.preferred_skills
    )
    exp_result = exp_scorer.score(
        gcc_job.min_experience_years, gcc_job.max_experience_years, overqualified_candidate.total_experience_years
    )

    base_score = 78
    adjusted_score, adjustments = adjuster.apply_adjustments(
        base_score, gcc_job, overqualified_candidate, skills_result, exp_result
    )

    # Should get overqualified penalty
    assert any(a.rule_code == "SEVERE_OVERQUALIFIED" for a in adjustments)
    assert adjusted_score < base_score


def test_e2e_perfect_candidate_max_score(gcc_job, perfect_match_candidate, embedding_model):
    """End-to-end test: Perfect candidate should approach or hit 100."""
    adjuster = ContextualAdjuster()
    confidence_calc = ConfidenceCalculator()
    skills_scorer = SkillsScorer(embedding_model=embedding_model)
    exp_scorer = ExperienceScorer()

    skills_result = skills_scorer.score(
        gcc_job.required_skills, perfect_match_candidate.skills, gcc_job.preferred_skills
    )
    exp_result = exp_scorer.score(
        gcc_job.min_experience_years, gcc_job.max_experience_years, perfect_match_candidate.total_experience_years
    )

    base_score = 90  # Already high base
    adjusted_score, adjustments = adjuster.apply_adjustments(
        base_score, gcc_job, perfect_match_candidate, skills_result, exp_result
    )

    # Should get multiple bonuses, approach 100
    assert adjusted_score >= 95
    assert adjusted_score <= 100  # Capped at 100
    assert len(adjustments) >= 3  # Multiple bonuses

    # Confidence should be very high
    section_scores = {"skills": 95, "experience": 90, "semantic": 92}
    confidence = confidence_calc.calculate_confidence(
        perfect_match_candidate, skills_result, exp_result, section_scores, adjusted_score
    )
    assert confidence.confidence_level == ConfidenceLevel.VERY_HIGH


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

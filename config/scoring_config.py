"""
Scoring Configuration Loader

This module is the SINGLE SOURCE OF TRUTH for all scoring configuration.
It loads and validates thresholds.yaml at module import time with fail-fast behavior.

⚠️  CRITICAL: If configuration is missing or invalid, this module will raise
             ConfigurationError and ABORT APPLICATION STARTUP.

NO DEFAULT VALUES are provided in code - all configuration must come from YAML.

Usage:
    from config.scoring_config import scoring_config
    
    # Access comprehensive scoring weights
    section_weights = scoring_config.section_weights
    skill_weights = scoring_config.skill_importance_weights
    
    # Access field scoring thresholds
    nat_scores = scoring_config.field_scoring['personal_details']['nationality']

Layer: Config
Dependencies: config.config_validator (Pydantic validation)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# Import Pydantic-validated config
from config.config_validator import get_thresholds_config, ConfigurationError


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SectionWeights:
    """Section weights for comprehensive scoring. Must sum to 1.0."""
    personal_details: float
    experience: float
    education: float
    skills: float
    salary: float
    cv_analysis: float
    
    def __post_init__(self) -> None:
        """Validate that section weights sum to 1.0."""
        total = (
            self.personal_details + 
            self.experience + 
            self.education + 
            self.skills + 
            self.salary + 
            self.cv_analysis
        )
        if not (0.99 <= total <= 1.01):  # Allow tiny floating point error
            raise ConfigurationError(
                f"Section weights must sum to 1.0, got {total:.4f}. "
                f"Check comprehensive_scoring.section_weights in thresholds.yaml"
            )


@dataclass(frozen=True)
class SkillImportanceWeights:
    """Multipliers for skill importance levels."""
    required: float
    preferred: float
    nice_to_have: float


@dataclass(frozen=True)
class ExperienceRecencyWeights:
    """Decay factors for experience recency."""
    current_or_recent: float
    moderately_recent: float
    older: float


@dataclass(frozen=True)
class IndustryAdjustment:
    """Industry-specific scoring adjustments."""
    gcc_experience_multiplier: float | None = None
    arabic_language_bonus: int | None = None
    transport_certifications_bonus: int | None = None
    warehouse_experience_bonus: int | None = None
    recent_skills_multiplier: float | None = None
    github_profile_bonus: int | None = None
    modern_tech_stack_bonus: int | None = None
    certifications_multiplier: float | None = None
    compliance_experience_bonus: int | None = None
    patient_care_experience_bonus: int | None = None


@dataclass(frozen=True)
class DecisionThresholds:
    """Classification thresholds for candidate scoring."""
    strong_match: int
    potential_match: int
    weak_match: int
    
    def __post_init__(self) -> None:
        """Validate threshold ordering."""
        if not (self.weak_match < self.potential_match < self.strong_match):
            raise ConfigurationError(
                f"Thresholds must be ordered: weak < potential < strong. "
                f"Got: weak={self.weak_match}, potential={self.potential_match}, "
                f"strong={self.strong_match}"
            )


@dataclass(frozen=True)
class ScoringConfig:
    """
    Complete scoring configuration loaded from thresholds.yaml.
    
    This is the single source of truth for all scoring behavior.
    All fields are REQUIRED - no defaults are provided in code.
    """
    
    # Comprehensive scoring configuration
    section_weights: SectionWeights
    skill_importance_weights: SkillImportanceWeights
    experience_recency_weights: ExperienceRecencyWeights
    industry_adjustments: dict[str, dict[str, Any]]
    
    # Field-level scoring thresholds
    field_scoring: dict[str, dict[str, dict[str, Any]]]
    
    # Decision thresholds
    decision_thresholds: DecisionThresholds
    
    # Legacy and other configuration
    scoring_weights: dict[str, float]
    hard_rejection_rules: dict[str, Any]
    features: dict[str, bool]
    
    def get_industry_adjustment(self, industry: str) -> dict[str, Any]:
        """
        Get industry-specific adjustments for a given industry.
        
        Args:
            industry: Industry name (lowercase)
            
        Returns:
            Dictionary of adjustments for the industry, or empty dict if not found
        """
        return self.industry_adjustments.get(industry.lower(), {})
    
    def get_field_score_config(self, section: str, field: str) -> dict[str, Any]:
        """
        Get scoring configuration for a specific field.
        
        Args:
            section: Section name (e.g., 'personal_details', 'experience')
            field: Field name within section (e.g., 'nationality', 'years_of_experience')
            
        Returns:
            Dictionary of scoring thresholds for the field
            
        Raises:
            ConfigurationError: If section or field not found
        """
        if section not in self.field_scoring:
            raise ConfigurationError(
                f"Field scoring configuration missing for section '{section}'. "
                f"Check field_scoring in thresholds.yaml"
            )
        
        if field not in self.field_scoring[section]:
            raise ConfigurationError(
                f"Field scoring configuration missing for field '{field}' in section '{section}'. "
                f"Check field_scoring.{section} in thresholds.yaml"
            )
        
        return self.field_scoring[section][field]


def _find_config_file() -> Path:
    """
    Locate thresholds.yaml configuration file.
    
    Returns:
        Path to thresholds.yaml
        
    Raises:
        ConfigurationError: If file not found
    """
    # Try relative to this module
    config_dir = Path(__file__).parent
    config_file = config_dir / "thresholds.yaml"
    
    if config_file.exists():
        return config_file
    
    # Try from workspace root
    workspace_root = config_dir.parent
    config_file = workspace_root / "config" / "thresholds.yaml"
    
    if config_file.exists():
        return config_file
    
    raise ConfigurationError(
        f"Configuration file 'thresholds.yaml' not found. "
        f"Searched in: {config_dir}, {workspace_root / 'config'}"
    )


def _load_yaml(config_file: Path) -> dict[str, Any]:
    """
    Load and parse YAML configuration file.
    
    Args:
        config_file: Path to thresholds.yaml
        
    Returns:
        Parsed YAML as dictionary
        
    Raises:
        ConfigurationError: If file cannot be read or parsed
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        if not isinstance(data, dict):
            raise ConfigurationError(
                f"Invalid YAML format: expected dictionary, got {type(data).__name__}"
            )
            
        return data
        
    except FileNotFoundError as e:
        raise ConfigurationError(f"Configuration file not found: {config_file}") from e
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML syntax in {config_file}: {e}") from e
    except Exception as e:
        raise ConfigurationError(f"Failed to load configuration from {config_file}: {e}") from e


def _validate_required_keys(data: dict[str, Any], required_keys: list[str], context: str) -> None:
    """
    Validate that all required keys are present in configuration.
    
    Args:
        data: Configuration dictionary
        required_keys: List of required key names
        context: Context string for error messages
        
    Raises:
        ConfigurationError: If any required key is missing
    """
    missing = [key for key in required_keys if key not in data]
    if missing:
        raise ConfigurationError(
            f"Missing required configuration keys in {context}: {', '.join(missing)}. "
            f"Check thresholds.yaml"
        )


def _load_section_weights(data: dict[str, Any]) -> SectionWeights:
    """Load and validate section weights."""
    _validate_required_keys(
        data,
        ['comprehensive_scoring'],
        'root level'
    )
    
    comp_scoring = data['comprehensive_scoring']
    _validate_required_keys(
        comp_scoring,
        ['section_weights'],
        'comprehensive_scoring'
    )
    
    weights = comp_scoring['section_weights']
    _validate_required_keys(
        weights,
        ['personal_details', 'experience', 'education', 'skills', 'salary', 'cv_analysis'],
        'comprehensive_scoring.section_weights'
    )
    
    return SectionWeights(
        personal_details=float(weights['personal_details']),
        experience=float(weights['experience']),
        education=float(weights['education']),
        skills=float(weights['skills']),
        salary=float(weights['salary']),
        cv_analysis=float(weights['cv_analysis']),
    )


def _load_skill_importance_weights(data: dict[str, Any]) -> SkillImportanceWeights:
    """Load and validate skill importance weights."""
    comp_scoring = data['comprehensive_scoring']
    _validate_required_keys(
        comp_scoring,
        ['skill_importance_weights'],
        'comprehensive_scoring'
    )
    
    weights = comp_scoring['skill_importance_weights']
    _validate_required_keys(
        weights,
        ['required', 'preferred', 'nice_to_have'],
        'comprehensive_scoring.skill_importance_weights'
    )
    
    return SkillImportanceWeights(
        required=float(weights['required']),
        preferred=float(weights['preferred']),
        nice_to_have=float(weights['nice_to_have']),
    )


def _load_experience_recency_weights(data: dict[str, Any]) -> ExperienceRecencyWeights:
    """Load and validate experience recency weights."""
    comp_scoring = data['comprehensive_scoring']
    _validate_required_keys(
        comp_scoring,
        ['experience_recency_weights'],
        'comprehensive_scoring'
    )
    
    weights = comp_scoring['experience_recency_weights']
    _validate_required_keys(
        weights,
        ['current_or_recent', 'moderately_recent', 'older'],
        'comprehensive_scoring.experience_recency_weights'
    )
    
    return ExperienceRecencyWeights(
        current_or_recent=float(weights['current_or_recent']),
        moderately_recent=float(weights['moderately_recent']),
        older=float(weights['older']),
    )


def _load_decision_thresholds(data: dict[str, Any]) -> DecisionThresholds:
    """Load and validate decision thresholds."""
    _validate_required_keys(
        data,
        ['decision_thresholds'],
        'root level'
    )
    
    thresholds = data['decision_thresholds']
    _validate_required_keys(
        thresholds,
        ['strong_match', 'potential_match', 'weak_match'],
        'decision_thresholds'
    )
    
    return DecisionThresholds(
        strong_match=int(thresholds['strong_match']),
        potential_match=int(thresholds['potential_match']),
        weak_match=int(thresholds['weak_match']),
    )


def _load_config() -> ScoringConfig:
    """
    Load complete scoring configuration from thresholds.yaml.
    
    This function is called ONCE at module import time.
    If configuration is invalid, it raises ConfigurationError and aborts startup.
    
    Returns:
        Validated ScoringConfig instance
        
    Raises:
        ConfigurationError: If configuration is missing or invalid
    """
    logger.info("Loading scoring configuration from thresholds.yaml...")
    
    # Locate and load YAML file
    config_file = _find_config_file()
    data = _load_yaml(config_file)
    
    # Validate root-level keys
    _validate_required_keys(
        data,
        ['comprehensive_scoring', 'field_scoring', 'decision_thresholds', 
         'scoring_weights', 'hard_rejection_rules', 'features'],
        'root level'
    )
    
    # Load and validate comprehensive scoring
    section_weights = _load_section_weights(data)
    skill_importance_weights = _load_skill_importance_weights(data)
    experience_recency_weights = _load_experience_recency_weights(data)
    
    # Load industry adjustments (optional per industry)
    industry_adjustments = data['comprehensive_scoring'].get('industry_adjustments', {})
    
    # Load field scoring (required)
    field_scoring = data.get('field_scoring', {})
    
    # Load decision thresholds
    decision_thresholds = _load_decision_thresholds(data)
    
    # Load legacy/other configuration
    scoring_weights = data.get('scoring_weights', {})
    hard_rejection_rules = data.get('hard_rejection_rules', {})
    features = data.get('features', {})
    
    logger.info(f"✓ Configuration loaded successfully from {config_file}")
    logger.info(f"  - Section weights sum: {sum([section_weights.personal_details, section_weights.experience, section_weights.education, section_weights.skills, section_weights.salary, section_weights.cv_analysis]):.2f}")
    logger.info(f"  - Decision thresholds: strong={decision_thresholds.strong_match}, potential={decision_thresholds.potential_match}, weak={decision_thresholds.weak_match}")
    logger.info(f"  - Industry adjustments: {len(industry_adjustments)} industries configured")
    
    return ScoringConfig(
        section_weights=section_weights,
        skill_importance_weights=skill_importance_weights,
        experience_recency_weights=experience_recency_weights,
        industry_adjustments=industry_adjustments,
        field_scoring=field_scoring,
        decision_thresholds=decision_thresholds,
        scoring_weights=scoring_weights,
        hard_rejection_rules=hard_rejection_rules,
        features=features,
    )


# ==============================================================================
# MODULE-LEVEL SINGLETON
# ==============================================================================
# Load configuration ONCE at module import time.
# If this fails, the entire application ABORTS with ConfigurationError.
#
# This ensures FAIL-FAST behavior: you cannot start the app with bad config.
# ==============================================================================

try:
    scoring_config: ScoringConfig = _load_config()
except ConfigurationError as e:
    logger.critical(f"❌ FATAL: Scoring configuration failed to load: {e}")
    logger.critical("Application cannot start without valid configuration.")
    logger.critical("Fix thresholds.yaml and restart the application.")
    raise
except Exception as e:
    logger.critical(f"❌ FATAL: Unexpected error loading configuration: {e}")
    raise ConfigurationError(f"Unexpected error loading configuration: {e}") from e


# Export configuration singleton
__all__ = ['scoring_config', 'ConfigurationError', 'ScoringConfig']

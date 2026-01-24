"""
Configuration Loader with Fail-Fast Validation

This module loads and validates all configuration from YAML files.
The application MUST fail at startup if configuration is invalid or incomplete.

NO hardcoded defaults are allowed in scoring logic - all must come from config files.

Design Principles:
- Fail-fast: Invalid config = immediate failure at startup
- Type-safe: Pydantic models for all config structures
- Single source of truth: thresholds.yaml
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator, ValidationError as PydanticValidationError


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing required values."""
    pass


# =============================================================================
# CONFIGURATION MODELS - Type-safe configuration structures
# =============================================================================

class SectionWeightsConfig(BaseModel):
    """Section weights for comprehensive scoring - must sum to 1.0"""
    personal_details: float = Field(..., ge=0.0, le=1.0)
    experience: float = Field(..., ge=0.0, le=1.0)
    education: float = Field(..., ge=0.0, le=1.0)
    skills: float = Field(..., ge=0.0, le=1.0)
    salary: float = Field(..., ge=0.0, le=1.0)
    cv_analysis: float = Field(..., ge=0.0, le=1.0)
    
    def validate_sum(self):
        """Ensure weights sum to 1.0 (with tolerance for floating point)"""
        total = sum([
            self.personal_details,
            self.experience,
            self.education,
            self.skills,
            self.salary,
            self.cv_analysis
        ])
        if not (0.99 <= total <= 1.01):
            raise ConfigurationError(
                f"Section weights must sum to 1.0, got {total:.4f}. "
                f"Check config/thresholds.yaml comprehensive_scoring.section_weights"
            )


class SkillImportanceWeightsConfig(BaseModel):
    """Skill importance multipliers"""
    required: float = Field(..., gt=0)
    preferred: float = Field(..., gt=0)
    nice_to_have: float = Field(..., gt=0)


class ExperienceRecencyWeightsConfig(BaseModel):
    """Experience recency decay factors"""
    current_or_recent: float = Field(..., ge=0, le=1)
    moderately_recent: float = Field(..., ge=0, le=1)
    older: float = Field(..., ge=0, le=1)


class IndustryAdjustmentConfig(BaseModel):
    """Industry-specific scoring adjustments"""
    gcc_experience_multiplier: Optional[float] = Field(default=1.0, gt=0)
    arabic_language_bonus: Optional[float] = Field(default=0, ge=0)
    transport_certifications_bonus: Optional[float] = Field(default=0, ge=0)
    warehouse_experience_bonus: Optional[float] = Field(default=0, ge=0)
    recent_skills_multiplier: Optional[float] = Field(default=1.0, gt=0)
    github_profile_bonus: Optional[float] = Field(default=0, ge=0)
    modern_tech_stack_bonus: Optional[float] = Field(default=0, ge=0)
    certifications_multiplier: Optional[float] = Field(default=1.0, gt=0)
    compliance_experience_bonus: Optional[float] = Field(default=0, ge=0)
    patient_care_experience_bonus: Optional[float] = Field(default=0, ge=0)


class ComprehensiveScoringConfig(BaseModel):
    """Comprehensive scoring configuration"""
    section_weights: SectionWeightsConfig
    skill_importance_weights: SkillImportanceWeightsConfig
    experience_recency_weights: ExperienceRecencyWeightsConfig
    industry_adjustments: Dict[str, IndustryAdjustmentConfig]


class FieldThresholdsConfig(BaseModel):
    """Field-level scoring thresholds (0-100 scores)"""
    # Store as raw dict - will be validated at access time
    raw_config: Dict[str, Any]
    
    class Config:
        arbitrary_types_allowed = True
    
    def get_score(self, section: str, field: str, criterion: str, default: Optional[int] = None) -> int:
        """
        Get a field score with fail-fast behavior.
        
        Args:
            section: Section name (e.g., 'personal_details', 'experience')
            field: Field name (e.g., 'nationality', 'years_of_experience')
            criterion: Score criterion (e.g., 'gcc_national', 'exact_match')
            default: Optional default value (if None, raises error when missing)
        
        Returns:
            int: Score value
        
        Raises:
            ConfigurationError: If score not found and no default provided
        """
        try:
            score = self.raw_config[section][field][criterion]
            if not isinstance(score, (int, float)):
                raise ConfigurationError(
                    f"Invalid score type at field_scoring.{section}.{field}.{criterion}: "
                    f"expected number, got {type(score).__name__}"
                )
            return int(score)
        except KeyError:
            if default is not None:
                return default
            raise ConfigurationError(
                f"Missing required configuration: field_scoring.{section}.{field}.{criterion} "
                f"in config/thresholds.yaml"
            )


class ThresholdsConfig(BaseModel):
    """Complete thresholds configuration from YAML"""
    comprehensive_scoring: ComprehensiveScoringConfig
    field_scoring: FieldThresholdsConfig
    
    class Config:
        arbitrary_types_allowed = True


# =============================================================================
# CONFIGURATION LOADER
# =============================================================================

class ConfigLoader:
    """
    Loads and validates configuration from YAML files.
    Implements fail-fast behavior - invalid config causes immediate failure.
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize config loader.
        
        Args:
            config_dir: Path to config directory (defaults to ./config)
        """
        if config_dir is None:
            # Assume config/ is relative to this file's parent
            config_dir = Path(__file__).parent
        
        self.config_dir = Path(config_dir)
        self.thresholds_path = self.config_dir / "thresholds.yaml"
        
        if not self.thresholds_path.exists():
            raise ConfigurationError(
                f"Critical configuration file not found: {self.thresholds_path}\n"
                f"Application cannot start without thresholds.yaml"
            )
    
    def load_thresholds(self) -> ThresholdsConfig:
        """
        Load and validate thresholds configuration.
        
        Returns:
            ThresholdsConfig: Validated configuration
        
        Raises:
            ConfigurationError: If configuration is invalid or incomplete
        """
        try:
            with open(self.thresholds_path, 'r', encoding='utf-8') as f:
                raw_config = yaml.safe_load(f)
            
            if not raw_config:
                raise ConfigurationError(
                    f"Empty configuration file: {self.thresholds_path}"
                )
            
            # Validate required top-level keys
            if 'comprehensive_scoring' not in raw_config:
                raise ConfigurationError(
                    "Missing 'comprehensive_scoring' section in thresholds.yaml"
                )
            
            if 'field_scoring' not in raw_config:
                raise ConfigurationError(
                    "Missing 'field_scoring' section in thresholds.yaml"
                )
            
            # Parse comprehensive scoring config
            comp_scoring = ComprehensiveScoringConfig(
                section_weights=SectionWeightsConfig(**raw_config['comprehensive_scoring']['section_weights']),
                skill_importance_weights=SkillImportanceWeightsConfig(
                    **raw_config['comprehensive_scoring']['skill_importance_weights']
                ),
                experience_recency_weights=ExperienceRecencyWeightsConfig(
                    **raw_config['comprehensive_scoring']['experience_recency_weights']
                ),
                industry_adjustments={
                    industry: IndustryAdjustmentConfig(**adjustments)
                    for industry, adjustments in raw_config['comprehensive_scoring']['industry_adjustments'].items()
                }
            )
            
            # Validate section weights sum to 1.0
            comp_scoring.section_weights.validate_sum()
            
            # Create field scoring config (raw dict for flexible access)
            field_scoring = FieldThresholdsConfig(raw_config=raw_config['field_scoring'])
            
            return ThresholdsConfig(
                comprehensive_scoring=comp_scoring,
                field_scoring=field_scoring
            )
            
        except PydanticValidationError as e:
            raise ConfigurationError(
                f"Invalid configuration in {self.thresholds_path}:\n{e}"
            ) from e
        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Invalid YAML syntax in {self.thresholds_path}:\n{e}"
            ) from e
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load configuration from {self.thresholds_path}: {e}"
            ) from e


# =============================================================================
# GLOBAL CONFIG SINGLETON (loaded at module import = fail-fast)
# =============================================================================

_config_loader = ConfigLoader()
_thresholds_config: Optional[ThresholdsConfig] = None


def get_thresholds_config() -> ThresholdsConfig:
    """
    Get validated thresholds configuration (singleton).
    
    This function is called at module import time by scoring_config.py,
    ensuring fail-fast behavior - the application will not start if config is invalid.
    
    Returns:
        ThresholdsConfig: Validated configuration
    
    Raises:
        ConfigurationError: If configuration is invalid
    """
    global _thresholds_config
    if _thresholds_config is None:
        _thresholds_config = _config_loader.load_thresholds()
    return _thresholds_config


# Validate configuration at import time (fail-fast)
try:
    CONFIG = get_thresholds_config()
    print(f"[OK] Configuration validated successfully: {_config_loader.thresholds_path}")
except ConfigurationError as e:
    print(f"\n{'='*80}")
    print("CRITICAL: CONFIGURATION ERROR")
    print('='*80)
    print(str(e))
    print('='*80)
    print("\nThe application will not start until configuration is fixed.")
    print(f"Please check: {_config_loader.thresholds_path}\n")
    raise

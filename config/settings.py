"""
Application Settings

Centralized, typed configuration management for the AI Engine.
Eliminates scattered os.getenv() calls and provides validation.

Layer: Configuration
Dependencies: None (pure configuration)
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """
    Application configuration settings.
    
    All settings are loaded from environment variables.
    Provides typed access and validation.
    """
    
    # API Configuration
    api_key: Optional[str] = None  # Legacy support
    ai_engine_api_token: Optional[str] = None  # Bearer token for service-to-service auth
    
    # Application Metadata
    app_name: str = "Logis AI Candidate Engine"
    app_version: str = "2.0.0"
    app_phase: str = "4 - Advanced Hybrid Scoring"
    
    # Environment
    environment: str = "development"  # development, staging, production
    debug: bool = False
    
    # Logging
    log_level: str = "INFO"
    
    # ML Model Paths (if needed in future)
    model_cache_dir: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "Settings":
        """
        Load settings from environment variables.
        
        Returns:
            Settings: Configured instance
        """
        return cls(
            api_key=os.getenv("API_KEY"),
            ai_engine_api_token=os.getenv("AI_ENGINE_API_TOKEN"),
            app_name=os.getenv("APP_NAME", "Logis AI Candidate Engine"),
            app_version=os.getenv("APP_VERSION", "2.0.0"),
            app_phase=os.getenv("APP_PHASE", "4 - Advanced Hybrid Scoring"),
            environment=os.getenv("ENVIRONMENT", "development"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            model_cache_dir=os.getenv("MODEL_CACHE_DIR"),
        )
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"
    
    def requires_api_key(self) -> bool:
        """Check if API key authentication is required."""
        return self.api_key is not None and len(self.api_key) > 0
    
    def requires_authentication(self) -> bool:
        """Check if Bearer token authentication is required."""
        return self.ai_engine_api_token is not None and len(self.ai_engine_api_token) > 0


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get application settings singleton.
    
    Returns:
        Settings: Application configuration
    """
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from environment.
    Useful for testing.
    
    Returns:
        Settings: Reloaded configuration
    """
    global _settings
    _settings = Settings.from_env()
    return _settings

"""
Configuration Module

Centralized configuration management for the AI Candidate Engine.

Usage:
    from config import get_settings
    
    settings = get_settings()
    if settings.requires_api_key():
        # API key validation required
"""

from config.env import load_env_file
from config.settings import Settings, get_settings, reload_settings


__all__ = [
    "Settings",
    "get_settings",
    "reload_settings",
    "load_env_file",
]

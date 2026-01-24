"""
FastAPI Dependency Injection

This module provides FastAPI-specific dependency injection functions.
It delegates to the application bootstrap for service construction.

Layer: API/Application boundary
Dependencies: Application Bootstrap, FastAPI
"""

from __future__ import annotations

from typing import Optional

from fastapi import Header, HTTPException

from application.bootstrap import get_application
from application.evaluation_service import EvaluationService
from application.cv_service import CVService
from config import get_settings


def get_evaluation_service() -> EvaluationService:
    """
    Get EvaluationService instance via application bootstrap.
    
    This is a FastAPI dependency injection factory.
    
    Returns:
        EvaluationService: Initialized service from bootstrap
        
    Raises:
        HTTPException: If application not bootstrapped
    """
    app = get_application()
    
    if not app.is_ready():
        raise HTTPException(
            status_code=503,
            detail="Application not ready. Bootstrap incomplete."
        )
    
    return app.get_evaluation_service()


def get_cv_service() -> CVService:
    """
    Get CVService instance via application bootstrap.
    
    This is a FastAPI dependency injection factory.
    
    Returns:
        CVService: Initialized service from bootstrap
        
    Raises:
        HTTPException: If application not bootstrapped
    """
    app = get_application()
    
    if not app.is_ready():
        raise HTTPException(
            status_code=503,
            detail="Application not ready. Bootstrap incomplete."
        )
    
    return app.get_cv_service()


def require_api_key(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
) -> None:
    """
    Validate API key if configured.
    
    Checks X-API-Key header against configured API_KEY from settings.
    If no API_KEY is configured, allows all requests.
    
    Args:
        x_api_key: API key from request header
    
    Raises:
        HTTPException: If API key is invalid
    """
    settings = get_settings()
    
    if not settings.requires_api_key():
        # No API key required
        return
    
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

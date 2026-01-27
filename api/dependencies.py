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


def verify_bearer_token(
    authorization: Optional[str] = Header(default=None, alias="Authorization")
) -> None:
    """
    Validate Bearer token for service-to-service authentication.
    
    Checks Authorization header for Bearer token format and validates against
    configured AI_ENGINE_API_TOKEN from settings.
    
    Expected header format: "Authorization: Bearer <token>"
    
    Args:
        authorization: Authorization header from request
    
    Raises:
        HTTPException: If token is missing, malformed, or invalid (401 Unauthorized)
    
    Example:
        >>> # In DRF application:
        >>> headers = {"Authorization": f"Bearer {settings.AI_ENGINE_API_TOKEN}"}
        >>> response = requests.post(url, json=data, headers=headers)
    """
    from config.logging_config import get_logger
    logger = get_logger(__name__)
    
    settings = get_settings()
    
    # If authentication is not configured, allow all requests (development mode)
    if not settings.requires_authentication():
        logger.debug("Authentication disabled - no AI_ENGINE_API_TOKEN configured")
        return
    
    # Check if Authorization header is present
    if not authorization:
        logger.warning("Authentication failed: Missing Authorization header")
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Parse Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning(
            f"Authentication failed: Malformed Authorization header (expected 'Bearer <token>')"
        )
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    
    # Validate token
    if token != settings.ai_engine_api_token:
        logger.warning("Authentication failed: Invalid token")
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.debug("Authentication successful")


# Legacy API key support (deprecated)
def require_api_key(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
) -> None:
    """
    Validate API key if configured (DEPRECATED).
    
    Use verify_bearer_token() instead for Bearer token authentication.
    This function is kept for backward compatibility.
    
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

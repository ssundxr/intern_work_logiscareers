"""
Health and Readiness Endpoints

Production-grade health checking for the AI Engine.

- /health  → Liveness check (always returns 200 if API is running)
- /ready   → Readiness check (validates bootstrap and services)

Layer: API
Dependencies: Application Bootstrap, Config
"""

from datetime import datetime

from fastapi import APIRouter, Response, status

from logis_ai_candidate_engine.application.bootstrap import get_application
from logis_ai_candidate_engine.config import get_settings


router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """
    Liveness probe endpoint.
    
    Returns basic service information. Always returns 200 if the API is running.
    Does NOT trigger any ML inference or heavy operations.
    
    Use this for:
    - Kubernetes liveness probes
    - Load balancer health checks
    - Uptime monitoring
    """
    settings = get_settings()
    
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "phase": settings.app_phase,
        "features": [
            "contextual_adjustments",
            "confidence_scoring",
            "feature_interactions",
            "smart_weight_optimization",
        ],
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/ready")
def readiness_check(response: Response):
    """
    Readiness probe endpoint.
    
    Validates that the application is fully bootstrapped and ready to serve requests.
    Returns 200 if ready, 503 if not ready.
    
    Checks:
    - Application bootstrap completed
    - All services initialized
    - No bootstrap errors
    
    Use this for:
    - Kubernetes readiness probes
    - Pre-deployment validation
    - Service mesh integration
    """
    app = get_application()
    settings = get_settings()
    
    if not app.is_ready():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "service": settings.app_name,
            "version": settings.app_version,
            "errors": app.get_bootstrap_errors(),
            "timestamp": datetime.now().isoformat(),
        }
    
    return {
        "status": "ready",
        "service": settings.app_name,
        "version": settings.app_version,
        "bootstrapped": True,
        "timestamp": datetime.now().isoformat(),
    }

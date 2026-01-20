"""
FastAPI Application Entry Point

Main application configuration and startup.
Bootstraps the application and registers routers.

Layer: API
"""

import logging

from fastapi import FastAPI

from logis_ai_candidate_engine.api.routes.cv import router as cv_router
from logis_ai_candidate_engine.api.routes.evaluation import router as evaluation_router
from logis_ai_candidate_engine.api.routes.health import router as health_router
from logis_ai_candidate_engine.application.bootstrap import get_application
from logis_ai_candidate_engine.config import get_settings


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Get settings
settings = get_settings()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Enterprise-grade AI-powered candidate ranking system for Logis Career. "
                "Features: Advanced hybrid scoring, confidence metrics, contextual adjustments, "
                "and feature interaction detection.",
)


@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler.
    
    Bootstraps the application services before accepting requests.
    """
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    
    # Bootstrap application
    bootstrap = get_application()
    success = bootstrap.bootstrap()
    
    if not success:
        errors = bootstrap.get_bootstrap_errors()
        logger.error("❌ Application bootstrap failed:")
        for error in errors:
            logger.error(f"  - {error}")
        raise RuntimeError("Application bootstrap failed")
    
    logger.info("✅ Application ready to serve requests")


# Register routers
app.include_router(health_router)
app.include_router(cv_router, prefix="/api/v1", tags=["CV Parsing"])
app.include_router(evaluation_router, prefix="/api/v1", tags=["Evaluation"])

"""
FastAPI Application Entry Point

Main application configuration and startup.
Bootstraps the application and registers routers.

Layer: API
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from api.routes.cv import router as cv_router
from api.routes.evaluation import router as evaluation_router
from api.routes.health import router as health_router
from application.bootstrap import get_application
from application.exceptions import (
    ApplicationError,
    ParsingError,
    ScoringError,
    ConfigurationError,
    ValidationError,
)
from application.logging_config import configure_logging, get_logger
from config import get_settings


# Configure structured logging
configure_logging()
logger = get_logger(__name__)


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


# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================

@app.exception_handler(ParsingError)
async def parsing_error_handler(request: Request, exc: ParsingError):
    """
    Handle CV parsing errors.
    
    Maps to HTTP 422 Unprocessable Entity - indicates that the CV format
    or content is invalid/unsupported.
    """
    logger.error(
        f"Parsing error: {exc.message}",
        exc_info=exc,
        extra={"error_code": exc.error_code, "details": exc.details}
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=exc.to_dict()
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """
    Handle input validation errors.
    
    Maps to HTTP 422 Unprocessable Entity - indicates that the request
    data is invalid or missing required fields.
    """
    logger.warning(
        f"Validation error: {exc.message}",
        extra={"error_code": exc.error_code, "details": exc.details}
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=exc.to_dict()
    )


@app.exception_handler(ScoringError)
async def scoring_error_handler(request: Request, exc: ScoringError):
    """
    Handle scoring/evaluation errors.
    
    Maps to HTTP 500 Internal Server Error - indicates an internal
    failure during candidate evaluation.
    """
    logger.error(
        f"Scoring error: {exc.message}",
        exc_info=exc,
        extra={"error_code": exc.error_code, "details": exc.details}
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=exc.to_dict()
    )


@app.exception_handler(ConfigurationError)
async def configuration_error_handler(request: Request, exc: ConfigurationError):
    """
    Handle configuration errors.
    
    Maps to HTTP 500 Internal Server Error - indicates that the service
    is misconfigured and cannot process requests.
    """
    logger.critical(
        f"Configuration error: {exc.message}",
        exc_info=exc,
        extra={"error_code": exc.error_code, "details": exc.details}
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=exc.to_dict()
    )


@app.exception_handler(ApplicationError)
async def application_error_handler(request: Request, exc: ApplicationError):
    """
    Handle generic application errors (catch-all for custom exceptions).
    
    Maps to HTTP 500 Internal Server Error.
    """
    logger.error(
        f"Application error: {exc.message}",
        exc_info=exc,
        extra={"error_code": exc.error_code, "details": exc.details}
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=exc.to_dict()
    )


@app.exception_handler(RequestValidationError)
async def fastapi_validation_error_handler(request: Request, exc: RequestValidationError):
    """
    Handle FastAPI/Pydantic validation errors.
    
    Maps to HTTP 422 Unprocessable Entity - indicates that the request
    body/params don't match the expected schema.
    """
    logger.warning(
        f"Request validation error: {str(exc)}",
        extra={"errors": exc.errors()}
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions (last resort).
    
    Maps to HTTP 500 Internal Server Error.
    Logs full stack trace but returns generic error to client.
    """
    logger.exception(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        exc_info=exc
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred"
        }
    )


# =============================================================================
# LIFECYCLE EVENTS
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler.
    
    Bootstraps the application services before accepting requests.
    """
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    
    try:
        # Bootstrap application
        bootstrap = get_application()
        success = bootstrap.bootstrap()
        
        if not success:
            errors = bootstrap.get_bootstrap_errors()
            logger.error("❌ Application bootstrap failed:")
            for error in errors:
                logger.error(f"  - {error}")
            
            raise ConfigurationError(
                "Application bootstrap failed",
                details={"errors": errors}
            )
        
        logger.info("✅ Application ready to serve requests")
    
    except ConfigurationError:
        # Re-raise to fail fast
        raise
    except Exception as e:
        logger.exception("Unexpected error during startup")
        raise ConfigurationError(
            f"Startup failed: {str(e)}",
            details={"original_error": str(e)}
        )


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    logger.info("Shutting down application")


# Register routers
app.include_router(health_router)
app.include_router(cv_router, prefix="/api/v1", tags=["CV Parsing"])
app.include_router(evaluation_router, prefix="/api/v1", tags=["Evaluation"])

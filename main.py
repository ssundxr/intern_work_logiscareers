"""
Application Entry Point & Composition Root

This is the composition root for the Logis AI Candidate Engine.
Responsibilities:
    - Wiring dependencies (dependency injection)
    - Registering exception handlers
    - Attaching lifecycle hooks
    - Bootstrapping the application
    - Creating the FastAPI app instance

Layer: Composition Root (above all layers)

The api/ folder contains ONLY routes - no app factory, no handlers, no lifecycle.

Usage:
    Development: uvicorn main:app --reload
    Production:  uvicorn main:app --workers 4
    
    Or run directly: python main.py
"""

import sys
from pathlib import Path

# Ensure project root is in path for imports
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

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
from config.logging_config import configure_logging, get_logger
from config import get_settings


def create_app() -> FastAPI:
    """
    Application factory - creates and configures FastAPI app.
    
    This is the composition root that wires all layers together.
    
    Returns:
        FastAPI: Configured application instance
    """
    # Configure structured logging
    configure_logging()
    logger = get_logger(__name__)

    # Get settings
    settings = get_settings()

    # Create FastAPI app with security scheme for Swagger/OpenAPI
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Enterprise-grade AI-powered candidate ranking system for Logis Career. "
                    "Features: Advanced hybrid scoring, confidence metrics, contextual adjustments, "
                    "and feature interaction detection.\n\n"
                    "**Authentication:** All endpoints require Bearer token authentication. "
                    "Include the token in the Authorization header: `Authorization: Bearer <token>`",
        swagger_ui_parameters={
            "persistAuthorization": True,
        },
    )
    
    # Add security scheme for Bearer token authentication
    # This updates the OpenAPI schema for Swagger UI
    from fastapi.openapi.utils import get_openapi
    
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title=settings.app_name,
            version=settings.app_version,
            description=app.description,
            routes=app.routes,
        )
        
        # Add Bearer token security scheme
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Enter the API token provided by your administrator. "
                              "The token should be set in the AI_ENGINE_API_TOKEN environment variable."
            }
        }
        
        # Apply security globally to all endpoints (except health)
        if settings.requires_authentication():
            for path in openapi_schema["paths"]:
                # Don't require auth for health endpoints
                if "/health" not in path and "/ready" not in path:
                    for method in openapi_schema["paths"][path]:
                        if method in ["get", "post", "put", "delete", "patch"]:
                            openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi

    # =============================================================================
    # EXCEPTION HANDLERS
    # =============================================================================

    @app.exception_handler(ParsingError)
    async def parsing_error_handler(request: Request, exc: ParsingError):
        """Handle CV parsing errors - maps to HTTP 422"""
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
        """Handle input validation errors - maps to HTTP 422"""
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
        """Handle scoring/evaluation errors - maps to HTTP 500"""
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
        """Handle configuration errors - maps to HTTP 500"""
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
        """Handle generic application errors - maps to HTTP 500"""
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
        """Handle FastAPI/Pydantic validation errors - maps to HTTP 422"""
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
        """Handle unexpected exceptions - maps to HTTP 500"""
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
        """Bootstrap application services before accepting requests"""
        logger.info(f"Starting {settings.app_name} v{settings.app_version}")
        logger.info(f"Environment: {settings.environment}")
        
        try:
            # Bootstrap application
            bootstrap = get_application()
            success = bootstrap.bootstrap()
            
            if not success:
                errors = bootstrap.get_bootstrap_errors()
                logger.error("Application bootstrap failed:")
                for error in errors:
                    logger.error(f"  - {error}")
                
                raise ConfigurationError(
                    "Application bootstrap failed",
                    details={"errors": errors}
                )
            
            logger.info("Application ready to serve requests")
        
        except ConfigurationError:
            raise
        except Exception as e:
            logger.exception("Unexpected error during startup")
            raise ConfigurationError(
                f"Startup failed: {str(e)}",
                details={"original_error": str(e)}
            )

    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on application shutdown"""
        logger.info("Shutting down application")

    # =============================================================================
    # ROUTE REGISTRATION
    # =============================================================================
    
    # Register routes from api/ layer (delivery layer contains ONLY routes)
    app.include_router(health_router)
    app.include_router(cv_router, prefix="/api/v1", tags=["CV Parsing"])
    app.include_router(evaluation_router, prefix="/api/v1", tags=["Evaluation"])
    
    return app


# Create app instance (composition happens here, not in api/ layer)
app = create_app()

# Export for uvicorn/gunicorn
__all__ = ["app", "create_app"]


if __name__ == "__main__":
    """
    Direct execution mode for development.
    In production, use uvicorn/gunicorn directly.
    """
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

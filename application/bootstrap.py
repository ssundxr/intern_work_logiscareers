"""
Application Bootstrap

Centralized initialization and dependency construction for the AI Engine.
This module is the single source of truth for application service lifecycle.

Responsibilities:
- Initialize application services
- Construct dependency graph
- Validate bootstrap completion
- Provide service factories

Layer: Application
Dependencies: Core, ML (NO FastAPI)
"""

from __future__ import annotations

import logging
from typing import Optional

from logis_ai_candidate_engine.application.cv_service import CVService
from logis_ai_candidate_engine.application.evaluation_service import EvaluationService


logger = logging.getLogger(__name__)


class ApplicationBootstrap:
    """
    Application bootstrap and dependency container.
    
    This class orchestrates the initialization of all application services
    and ensures they are properly constructed before the application starts.
    """
    
    _instance: Optional[ApplicationBootstrap] = None
    _is_bootstrapped: bool = False
    
    def __init__(self) -> None:
        """
        Private constructor. Use get_instance() instead.
        """
        self._evaluation_service: Optional[EvaluationService] = None
        self._cv_service: Optional[CVService] = None
        self._bootstrap_errors: list[str] = []
    
    @classmethod
    def get_instance(cls) -> ApplicationBootstrap:
        """
        Get singleton instance of ApplicationBootstrap.
        
        Returns:
            ApplicationBootstrap instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def bootstrap(self) -> bool:
        """
        Initialize all application services.
        
        This method should be called once during application startup.
        It constructs all services and validates the dependency graph.
        
        Returns:
            bool: True if bootstrap succeeded, False otherwise
        """
        if self._is_bootstrapped:
            logger.info("Application already bootstrapped")
            return True
        
        try:
            logger.info("Starting application bootstrap...")
            
            # Initialize services
            self._bootstrap_evaluation_service()
            self._bootstrap_cv_service()
            
            # Mark as bootstrapped
            ApplicationBootstrap._is_bootstrapped = True
            
            logger.info("✅ Application bootstrap completed successfully")
            return True
            
        except Exception as e:
            error_msg = f"Bootstrap failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self._bootstrap_errors.append(error_msg)
            return False
    
    def _bootstrap_evaluation_service(self) -> None:
        """
        Initialize EvaluationService.
        
        Raises:
            Exception: If service initialization fails
        """
        try:
            logger.debug("Initializing EvaluationService...")
            self._evaluation_service = EvaluationService()
            logger.debug("✅ EvaluationService initialized")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize EvaluationService: {e}") from e
    
    def _bootstrap_cv_service(self) -> None:
        """
        Initialize CVService.
        
        Raises:
            Exception: If service initialization fails
        """
        try:
            logger.debug("Initializing CVService...")
            self._cv_service = CVService()
            logger.debug("✅ CVService initialized")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize CVService: {e}") from e
    
    def get_evaluation_service(self) -> EvaluationService:
        """
        Get EvaluationService instance.
        
        Returns:
            EvaluationService: Initialized service
            
        Raises:
            RuntimeError: If application not bootstrapped
        """
        if not self._is_bootstrapped:
            raise RuntimeError(
                "Application not bootstrapped. Call bootstrap() first."
            )
        
        if self._evaluation_service is None:
            raise RuntimeError("EvaluationService not initialized")
        
        return self._evaluation_service
    
    def get_cv_service(self) -> CVService:
        """
        Get CVService instance.
        
        Returns:
            CVService: Initialized service
            
        Raises:
            RuntimeError: If application not bootstrapped
        """
        if not self._is_bootstrapped:
            raise RuntimeError(
                "Application not bootstrapped. Call bootstrap() first."
            )
        
        if self._cv_service is None:
            raise RuntimeError("CVService not initialized")
        
        return self._cv_service
    
    def is_ready(self) -> bool:
        """
        Check if application is ready to serve requests.
        
        Returns:
            bool: True if all services are initialized and ready
        """
        return (
            self._is_bootstrapped
            and self._evaluation_service is not None
            and self._cv_service is not None
            and len(self._bootstrap_errors) == 0
        )
    
    def get_bootstrap_errors(self) -> list[str]:
        """
        Get list of bootstrap errors if any.
        
        Returns:
            list[str]: Bootstrap errors
        """
        return self._bootstrap_errors.copy()
    
    @classmethod
    def reset(cls) -> None:
        """
        Reset bootstrap state. Used for testing only.
        
        WARNING: This should only be called in test environments.
        """
        cls._instance = None
        cls._is_bootstrapped = False


# Convenience function for global access
def get_application() -> ApplicationBootstrap:
    """
    Get the application bootstrap instance.
    
    Returns:
        ApplicationBootstrap: Singleton instance
    """
    return ApplicationBootstrap.get_instance()

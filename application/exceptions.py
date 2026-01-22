"""
Application-Level Custom Exceptions

This module defines domain-specific exceptions that provide clear error semantics
and enable structured error handling at the API layer.

Exception Hierarchy:
    ApplicationError (base)
    ├── ParsingError - CV parsing failures
    ├── ScoringError - Scoring/evaluation failures
    └── ConfigurationError - Bootstrap/config failures

Design Principles:
1. Exceptions originate from domain/application layers
2. API layer translates to HTTP status codes
3. Messages are user-safe (no internal details)
4. Context preserved for logging
"""

from typing import Optional, Dict, Any


class ApplicationError(Exception):
    """
    Base class for all application-level errors.
    
    This provides a common interface for error handling and logging.
    All custom exceptions should inherit from this.
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize application error.
        
        Args:
            message: Human-readable error message (user-safe)
            error_code: Machine-readable error code (e.g., "PARSING_FAILED")
            details: Additional context for logging (not exposed to users)
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__.upper()
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to structured dict for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
        }


class ParsingError(ApplicationError):
    """
    Raised when CV parsing fails.
    
    Examples:
    - Invalid CV format
    - Empty/malformed input
    - Unsupported file type
    - Critical parsing stage failure
    
    HTTP Mapping: 400 Bad Request or 422 Unprocessable Entity
    """
    
    def __init__(
        self,
        message: str = "Failed to parse CV",
        error_code: str = "PARSING_FAILED",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)


class ScoringError(ApplicationError):
    """
    Raised when candidate scoring/evaluation fails.
    
    Examples:
    - Missing required scoring data
    - Invalid score calculation
    - Aggregation failure
    - Scoring strategy error
    
    HTTP Mapping: 500 Internal Server Error
    """
    
    def __init__(
        self,
        message: str = "Failed to score candidate",
        error_code: str = "SCORING_FAILED",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)


class ConfigurationError(ApplicationError):
    """
    Raised when configuration is invalid or missing.
    
    Examples:
    - Missing config file
    - Invalid YAML syntax
    - Missing required environment variables
    - Bootstrap failure
    
    HTTP Mapping: 500 Internal Server Error (startup failure)
    
    Note: This should typically cause application to fail-fast on startup.
    """
    
    def __init__(
        self,
        message: str = "Configuration error",
        error_code: str = "CONFIGURATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)


class ValidationError(ApplicationError):
    """
    Raised when input validation fails.
    
    Examples:
    - Missing required fields
    - Invalid data types
    - Business rule violations
    
    HTTP Mapping: 422 Unprocessable Entity
    """
    
    def __init__(
        self,
        message: str = "Validation failed",
        error_code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)

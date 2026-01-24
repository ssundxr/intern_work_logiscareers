"""
Structured Logging Configuration

Production-grade logging with:
- JSON format for production (machine-readable)
- Human-readable format for development
- Request ID tracking
- Contextual error logging
- Performance monitoring

Usage:
    from config.logging_config import get_logger
    
    logger = get_logger(__name__)
    logger.info("Processing request", extra={"request_id": req_id, "cv_length": len(text)})
"""

import logging
import sys
import json
from typing import Dict, Any, Optional
from datetime import datetime
from config.env import get_env


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging in production.
    
    Produces machine-readable logs with consistent schema:
    {
        "timestamp": "2026-01-21T12:00:00.000Z",
        "level": "INFO",
        "service": "logis_ai_candidate_engine",
        "logger": "api.routes.evaluation",
        "message": "Evaluating candidate",
        "request_id": "abc123",
        "error_type": "ParsingError",  # if exception
        "extra": {...}
    }
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": "logis_ai_candidate_engine",
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add request_id if available
        if hasattr(record, 'request_id'):
            log_data["request_id"] = record.request_id
        
        # Add exception info if present
        if record.exc_info:
            log_data["error_type"] = record.exc_info[0].__name__
            log_data["error_message"] = str(record.exc_info[1])
        
        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_data["extra"] = record.extra_data
        
        return json.dumps(log_data)


class DevelopmentFormatter(logging.Formatter):
    """
    Human-readable formatter for development.
    
    Example output:
    2026-01-21 12:00:00 [INFO] api.routes.evaluation: Evaluating candidate (request_id=abc123)
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as human-readable string."""
        # Base format
        base = f"{self.formatTime(record)} [{record.levelname}] {record.name}: {record.getMessage()}"
        
        # Add request_id if available
        if hasattr(record, 'request_id'):
            base += f" (request_id={record.request_id})"
        
        # Add exception info if present
        if record.exc_info:
            base += f"\n{self.formatException(record.exc_info)}"
        
        return base


def configure_logging() -> None:
    """
    Configure application logging based on environment.
    
    Production: JSON structured logs to stdout
    Development: Human-readable logs to stdout
    """
    env = get_env()
    
    # Determine log level
    log_level_str = env.log_level.upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    # Remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Choose formatter based on environment
    if env.environment == "production":
        formatter = JSONFormatter()
    else:
        formatter = DevelopmentFormatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("tensorflow").setLevel(logging.ERROR)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with structured logging support.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
        
    Usage:
        logger = get_logger(__name__)
        logger.info("Processing", extra={"request_id": "123", "extra_data": {"cv_length": 1000}})
    """
    return logging.getLogger(name)


class RequestContextLogger:
    """
    Context manager for adding request ID to all logs within a request.
    
    Usage:
        with RequestContextLogger(request_id="abc123"):
            logger.info("Processing request")  # Will include request_id
    """
    
    def __init__(self, request_id: str):
        self.request_id = request_id
        self.old_factory = None
    
    def __enter__(self):
        # Store old factory
        self.old_factory = logging.getLogRecordFactory()
        
        # Create new factory that adds request_id
        request_id = self.request_id
        
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            record.request_id = request_id
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore old factory
        if self.old_factory:
            logging.setLogRecordFactory(self.old_factory)


def log_with_context(logger: logging.Logger, level: str, message: str, **context):
    """
    Log with additional context data.
    
    Args:
        logger: Logger instance
        level: Log level ('info', 'error', etc.)
        message: Log message
        **context: Additional context fields
        
    Usage:
        log_with_context(logger, 'info', 'Processing CV', cv_length=1000, candidate_id=123)
    """
    log_func = getattr(logger, level.lower())
    
    # Create a custom log record with extra_data
    class ContextAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            kwargs['extra'] = {'extra_data': context}
            return msg, kwargs
    
    adapter = ContextAdapter(logger, {})
    log_func = getattr(adapter, level.lower())
    log_func(message)

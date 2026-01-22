"""
Main Application Entry Point

This is the entry point for running the FastAPI application.
Use with: uvicorn main:app --reload

Production-grade FastAPI application for AI-powered candidate evaluation.
"""

from api.main import app

# Re-export app for uvicorn
__all__ = ["app"]


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

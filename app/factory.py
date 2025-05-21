"""
Factory module for creating and configuring FastAPI applications.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.config import AppSettings

def create_app(settings: AppSettings = None) -> FastAPI:
    """
    Create and configure a FastAPI application.
    
    Args:
        settings: Application settings, if not provided defaults will be used
        
    Returns:
        Configured FastAPI application
    """
    if settings is None:
        settings = AppSettings()
    
    app = FastAPI(
        title="HermitBench API",
        description="API for running and evaluating autonomous LLM interactions",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    app.include_router(router)
    
    # Add application state
    app.state.settings = settings
    
    @app.get("/health")
    async def health_check():
        """Simple health check endpoint"""
        return {"status": "healthy"}
    
    @app.get("/")
    async def index():
        """API home page with info"""
        return {
            "name": "HermitBench API",
            "version": "1.0.0",
            "description": "API for running and evaluating autonomous LLM interactions",
            "documentation": "/docs",
            "endpoints": [
                {"path": "/api/models", "description": "Get available models"},
                {"path": "/api/run", "description": "Run a single interaction"},
                {"path": "/api/run-batch", "description": "Run a batch of interactions"},
                {"path": "/api/test-run", "description": "Run a standard test"},
                {"path": "/health", "description": "Health check endpoint"}
            ]
        }
    
    return app

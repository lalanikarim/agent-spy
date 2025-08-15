"""Main FastAPI application for Agent Spy."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api import health, runs
from src.core.config import get_settings
from src.core.database import close_database, init_database
from src.core.logging import setup_logging

# Get settings
settings = get_settings()

# Setup logging
logger = setup_logging(settings)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Initialize database connection
    await init_database()
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    # Close database connections
    await close_database()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_credentials,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )
    
    # Add custom middleware
    @app.middleware("http")
    async def add_request_id(request, call_next):
        """Add request ID to all requests."""
        import uuid
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    
    # Add exception handlers
    @app.exception_handler(ValueError)
    async def value_error_handler(request, exc):
        """Handle ValueError exceptions."""
        logger.error(f"ValueError: {exc}", exc_info=True)
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)},
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        """Handle general exceptions."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        if settings.debug:
            return JSONResponse(
                status_code=500,
                content={"detail": str(exc), "type": type(exc).__name__},
            )
        else:
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )
    
    # Include routers
    app.include_router(health.router, tags=["health"])
    app.include_router(
        runs.router,
        prefix=settings.langsmith_endpoint_base,
        tags=["runs"]
    )
    
    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    """Run the application directly."""
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )

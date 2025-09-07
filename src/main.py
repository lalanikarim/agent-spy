"""Main FastAPI application for Agent Spy."""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api import debug, health, runs, websocket
from src.core.config import get_settings
from src.core.database import close_database, init_database
from src.core.logging import setup_logging
from src.core.otlp_forwarder import set_otlp_forwarder
from src.otel.otlp_receiver import OtlpReceiver

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

    # Initialize OTLP receiver
    otlp_receiver = None
    if settings.otlp_grpc_enabled or settings.otlp_http_enabled:
        try:
            otlp_receiver = OtlpReceiver(
                http_path=settings.otlp_http_path, grpc_host=settings.otlp_grpc_host, grpc_port=settings.otlp_grpc_port
            )
            # Start gRPC server in background if enabled
            if settings.otlp_grpc_enabled:
                asyncio.create_task(otlp_receiver.start_grpc_server())
                logger.info(f"OTLP gRPC server configured on {settings.otlp_grpc_host}:{settings.otlp_grpc_port}")
            logger.info(f"OTLP receiver configured with HTTP path: {settings.otlp_http_path}")
        except Exception as e:
            logger.error(f"Failed to start OTLP receiver: {e}")

    # Initialize OTLP forwarder
    if settings.otlp_forwarder_enabled:
        try:
            from src.otel.forwarder import OtlpForwarderConfig, OtlpForwarderService

            forwarder_config = OtlpForwarderConfig(
                enabled=settings.otlp_forwarder_enabled,
                endpoint=settings.otlp_forwarder_endpoint,
                protocol=settings.otlp_forwarder_protocol,
                service_name=settings.otlp_forwarder_service_name,
                timeout=settings.otlp_forwarder_timeout,
                retry_count=settings.otlp_forwarder_retry_count,
                insecure=settings.otlp_forwarder_insecure,
                debounce_seconds=settings.forwarder_debounce_seconds,
                forward_run_timeout_seconds=settings.forward_run_timeout_seconds,
                max_synthetic_spans=settings.forwarder_max_synthetic_spans,
                attr_max_str=settings.forwarder_attr_max_str,
                attr_max_kv_str=settings.forwarder_attr_max_kv_str,
                attr_max_list_items=settings.forwarder_attr_max_list_items,
            )
            otlp_forwarder = OtlpForwarderService(forwarder_config)
            set_otlp_forwarder(otlp_forwarder)
            logger.info(f"OTLP forwarder initialized: {settings.otlp_forwarder_protocol}://{settings.otlp_forwarder_endpoint}")
        except Exception as e:
            logger.error(f"Failed to initialize OTLP forwarder: {e}")
            set_otlp_forwarder(None)
    else:
        logger.info("OTLP forwarder disabled")

    yield

    # Shutdown
    logger.info("Shutting down application")

    # Stop OTLP receiver
    if otlp_receiver:
        try:
            await otlp_receiver.stop_grpc_server()
        except Exception as e:
            logger.error(f"Error stopping OTLP receiver: {e}")

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

    # Note: No default project injection; clients must send project via headers or payload

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
    app.include_router(runs.router, prefix=settings.langsmith_endpoint_base, tags=["runs"])
    app.include_router(websocket.router, tags=["websocket"])
    app.include_router(debug.router, tags=["debug"])

    # Include OTLP receiver router
    if settings.otlp_http_enabled:
        try:
            # Create OTLP receiver for HTTP routing
            otlp_receiver = OtlpReceiver(
                http_path=settings.otlp_http_path, grpc_host=settings.otlp_grpc_host, grpc_port=settings.otlp_grpc_port
            )
            app.include_router(otlp_receiver.router)
            logger.info(f"OTLP HTTP receiver configured at {settings.otlp_http_path}")
        except Exception as e:
            logger.error(f"Failed to configure OTLP HTTP receiver: {e}")

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    """Run the application directly."""
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser(description="Agent Spy server")
    parser.add_argument(
        "command",
        nargs="?",
        choices=["serve", "export-env"],
        default="serve",
        help="Command to run: serve (default) or export-env",
    )
    parser.add_argument(
        "--out",
        dest="out",
        default=".env.generated",
        help="Output path for export-env",
    )
    args = parser.parse_args()

    if args.command == "export-env":
        path = settings.export_env_file(args.out)
        logger.info(f"Exported environment to {path}")
    else:
        uvicorn.run(
            "src.main:app",
            host=settings.host,
            port=settings.port,
            reload=settings.reload,
            log_level=settings.log_level.lower(),
        )

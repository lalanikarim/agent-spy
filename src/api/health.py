"""Health check endpoints."""

import time
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from src.core.config import get_settings
from src.core.database import get_db_session
from src.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: str
    version: str
    environment: str
    uptime_seconds: float
    database_status: str = "not_configured"
    database_type: str = "unknown"
    dependencies: dict[str, str] = {}


class ReadinessResponse(BaseModel):
    """Readiness check response model."""

    ready: bool
    checks: dict[str, bool]
    timestamp: str


# Store application start time
_start_time = time.time()


@router.get("/health", response_model=HealthResponse, summary="Health Check")
async def health_check() -> HealthResponse:
    """
    Health check endpoint that returns the current status of the application.

    This endpoint is used by load balancers and monitoring systems to determine
    if the application is running and healthy.
    """
    logger.debug("Health check requested")

    # Get fresh settings to ensure we have the latest environment variables
    settings = get_settings()

    current_time = time.time()
    uptime = current_time - _start_time

    # Check database connectivity
    database_status = "unknown"
    try:
        async with get_db_session() as session:
            # Execute a simple query to test connectivity
            result = await session.execute(select(1))
            result.scalar()
            database_status = "connected"
    except Exception as e:
        logger.warning(f"Database connectivity check failed: {e}")
        database_status = "disconnected"

    # TODO: Add dependency checks (Redis, external APIs, etc.) in later phases
    dependencies = {
        "database": database_status,
    }

    response = HealthResponse(
        status="healthy" if database_status == "connected" else "degraded",
        timestamp=datetime.now(UTC).isoformat(),
        version=settings.app_version,
        environment=settings.environment,
        uptime_seconds=round(uptime, 2),
        database_status=database_status,
        database_type=settings.database_type,
        dependencies=dependencies,
    )

    logger.info(f"Health check completed: {response.status} (database: {database_status})")
    return response


@router.get("/health/ready", response_model=ReadinessResponse, summary="Readiness Check")
async def readiness_check() -> ReadinessResponse:
    """
    Readiness check endpoint for determining if app is ready to serve requests.

    This endpoint performs deeper checks than the health endpoint and is used by
    Kubernetes and other orchestration systems to determine if the application
    should receive traffic.
    """
    logger.debug("Readiness check requested")

    # Check database connectivity
    database_ready = False
    try:
        async with get_db_session() as session:
            # Execute a simple query to test connectivity
            result = await session.execute(select(1))
            result.scalar()
            database_ready = True
    except Exception as e:
        logger.warning(f"Database readiness check failed: {e}")

    checks = {
        "application": True,  # Application is running if we reach this point
        "database": database_ready,  # Database connectivity check
        "configuration": True,  # Configuration loaded successfully
    }

    # Application is ready if all critical checks pass
    ready = checks["application"] and checks["configuration"] and checks["database"]

    response = ReadinessResponse(ready=ready, checks=checks, timestamp=datetime.now(UTC).isoformat())

    logger.info(f"Readiness check completed: ready={ready} (database: {database_ready})")
    return response


@router.get("/health/live", summary="Liveness Check")
async def liveness_check() -> dict[str, Any]:
    """
    Liveness check endpoint that returns whether the application is alive.

    This is the simplest health check that just confirms the application
    process is running and can respond to requests.
    """
    logger.debug("Liveness check requested")

    response = {"alive": True, "timestamp": datetime.now(UTC).isoformat()}

    return response

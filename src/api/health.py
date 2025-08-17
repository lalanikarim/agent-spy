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
from src.core.redis import manager as redis_manager

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

    # Check Redis connectivity (optional)
    redis_health = await redis_manager.health_check()
    redis_status = redis_health["status"]

    dependencies = {
        "database": database_status,
        "redis": redis_status,
    }

    # Determine overall status - Redis is optional, so don't fail if Redis is disabled
    overall_status = "healthy"
    if database_status != "connected" or redis_status == "error":
        overall_status = "degraded"

    response = HealthResponse(
        status=overall_status,
        timestamp=datetime.now(UTC).isoformat(),
        version=settings.app_version,
        environment=settings.environment,
        uptime_seconds=round(uptime, 2),
        database_status=database_status,
        database_type=settings.database_type,
        dependencies=dependencies,
    )

    logger.info(f"Health check completed: {response.status} (database: {database_status}, redis: {redis_status})")
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

    # Check Redis readiness (optional)
    redis_health = await redis_manager.health_check()
    redis_ready = redis_health["status"] in ["connected", "disabled"]  # Ready if connected or disabled

    checks = {
        "application": True,  # Application is running if we reach this point
        "database": database_ready,  # Database connectivity check
        "configuration": True,  # Configuration loaded successfully
        "redis": redis_ready,  # Redis readiness (optional)
    }

    # Application is ready if all critical checks pass (Redis is optional)
    ready = checks["application"] and checks["configuration"] and checks["database"]
    # Don't fail readiness if Redis is just disabled, only if it's enabled but failing
    if redis_health["status"] == "error":
        ready = False

    response = ReadinessResponse(ready=ready, checks=checks, timestamp=datetime.now(UTC).isoformat())

    logger.info(f"Readiness check completed: ready={ready} (database: {database_ready}, redis: {redis_health['status']})")
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

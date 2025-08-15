"""Health check endpoints."""

import time
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.core.config import Settings, get_settings
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
    dependencies: dict[str, str] = {}


class ReadinessResponse(BaseModel):
    """Readiness check response model."""
    ready: bool
    checks: dict[str, bool]
    timestamp: str


# Store application start time
_start_time = time.time()


@router.get("/health", response_model=HealthResponse, summary="Health Check")
async def health_check(
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> HealthResponse:
    """
    Health check endpoint that returns the current status of the application.
    
    This endpoint is used by load balancers and monitoring systems to determine
    if the application is running and healthy.
    """
    logger.debug("Health check requested")
    
    current_time = time.time()
    uptime = current_time - _start_time
    
    # TODO: Add database connectivity check in Phase 3
    database_status = "not_implemented"
    
    # TODO: Add dependency checks (Redis, external APIs, etc.) in later phases
    dependencies = {
        "database": database_status,
    }
    
    response = HealthResponse(
        status="healthy",
        timestamp=datetime.now(UTC).isoformat(),
        version=settings.app_version,
        environment=settings.environment,
        uptime_seconds=round(uptime, 2),
        database_status=database_status,
        dependencies=dependencies
    )
    
    logger.info(f"Health check completed: {response.status}")
    return response


@router.get(
    "/health/ready", response_model=ReadinessResponse, summary="Readiness Check"
)
async def readiness_check(
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> ReadinessResponse:
    """
    Readiness check endpoint for determining if app is ready to serve requests.
    
    This endpoint performs deeper checks than the health endpoint and is used by
    Kubernetes and other orchestration systems to determine if the application
    should receive traffic.
    """
    logger.debug("Readiness check requested")
    
    checks = {
        "application": True,  # Application is running if we reach this point
        "database": False,    # TODO: Implement database connectivity check in Phase 3
        "configuration": True,  # Configuration loaded successfully
    }
    
    # Application is ready if all critical checks pass
    ready = checks["application"] and checks["configuration"]
    # Note: Database check will be required in Phase 3
    
    response = ReadinessResponse(
        ready=ready,
        checks=checks,
        timestamp=datetime.now(UTC).isoformat()
    )
    
    logger.info(f"Readiness check completed: ready={ready}")
    return response


@router.get("/health/live", summary="Liveness Check")
async def liveness_check() -> dict[str, Any]:
    """
    Liveness check endpoint that returns whether the application is alive.
    
    This is the simplest health check that just confirms the application
    process is running and can respond to requests.
    """
    logger.debug("Liveness check requested")
    
    response = {
        "alive": True,
        "timestamp": datetime.now(UTC).isoformat()
    }
    
    return response

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
from src.repositories.runs import RunRepository

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
    otlp_config: dict[str, Any] = {}


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

    # Initialize dependencies
    dependencies = {
        "database": database_status,
    }

    # Gather OTLP configuration and status
    otlp_config = {}
    try:
        # OTLP Receiver Configuration
        otlp_config["receiver"] = {
            "http_enabled": settings.otlp_http_enabled,
            "http_path": settings.otlp_http_path,
            "grpc_enabled": settings.otlp_grpc_enabled,
            "grpc_host": settings.otlp_grpc_host,
            "grpc_port": settings.otlp_grpc_port,
        }

        # OTLP Forwarder Configuration
        otlp_config["forwarder"] = {
            "enabled": settings.otlp_forwarder_enabled,
            "endpoint": settings.otlp_forwarder_endpoint,
            "protocol": settings.otlp_forwarder_protocol,
            "service_name": settings.otlp_forwarder_service_name,
            "timeout": settings.otlp_forwarder_timeout,
            "retry_count": settings.otlp_forwarder_retry_count,
            "status": "configured"
            if settings.otlp_forwarder_enabled and settings.otlp_forwarder_endpoint
            else "not_configured",
        }

        # Add OTLP status to dependencies
        if settings.otlp_http_enabled or settings.otlp_grpc_enabled:
            dependencies["otlp_receiver"] = "enabled"
        else:
            dependencies["otlp_receiver"] = "disabled"

        if settings.otlp_forwarder_enabled and settings.otlp_forwarder_endpoint:
            dependencies["otlp_forwarder"] = "enabled"
            # Add forwarder endpoint info to dependencies for easier debugging
            dependencies["otlp_forwarder_endpoint"] = (
                f"{settings.otlp_forwarder_protocol}://{settings.otlp_forwarder_endpoint}"
            )
        else:
            dependencies["otlp_forwarder"] = "disabled"

    except Exception as e:
        logger.warning(f"Failed to gather OTLP configuration: {e}")
        otlp_config["error"] = str(e)
        dependencies["otlp_config"] = "error"

    response = HealthResponse(
        status="healthy" if database_status == "connected" else "degraded",
        timestamp=datetime.now(UTC).isoformat(),
        version=settings.app_version,
        environment=settings.environment,
        uptime_seconds=round(uptime, 2),
        database_status=database_status,
        database_type=settings.database_type,
        dependencies=dependencies,
        otlp_config=otlp_config,
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


@router.get("/health/traces", summary="Trace Completeness Health Check")
async def trace_completeness_check() -> dict[str, Any]:
    """
    Trace completeness health check endpoint.

    This endpoint checks for incomplete traces that may be missing outputs,
    which is the core issue we're addressing. It provides proactive monitoring
    to detect trace completeness issues before they become problems.
    """
    logger.info("🔍 Trace completeness health check requested")

    try:
        async with get_db_session() as session:
            run_repo = RunRepository(session)

            # Check trace completeness across all projects for the last 24 hours
            completeness_stats = await run_repo.check_trace_completeness(hours_back=24)

            # Determine overall health status
            if completeness_stats["completeness_score"] >= 0.95:
                health_status = "healthy"
            elif completeness_stats["completeness_score"] >= 0.90:
                health_status = "degraded"
            else:
                health_status = "unhealthy"

            # Check for critical issues
            critical_issues = []
            if completeness_stats["completed_missing_outputs"] > 0:
                critical_issues.append(
                    f"{completeness_stats['completed_missing_outputs']} traces marked completed but missing outputs"
                )

            if completeness_stats["long_running_potential_orphans"] > 0:
                critical_issues.append(f"{completeness_stats['long_running_potential_orphans']} potentially orphaned traces")

            if completeness_stats["incomplete_completion"] > 0:
                critical_issues.append(f"{completeness_stats['incomplete_completion']} traces with incomplete completion")

            response = {
                "status": health_status,
                "completeness_score": completeness_stats["completeness_score"],
                "total_traces_checked": completeness_stats["total_traces_checked"],
                "critical_issues": critical_issues,
                "problematic_traces_count": len(completeness_stats["problematic_traces"]),
                "timestamp": datetime.now(UTC).isoformat(),
                "details": {
                    "completed_missing_outputs": completeness_stats["completed_missing_outputs"],
                    "long_running_potential_orphans": completeness_stats["long_running_potential_orphans"],
                    "incomplete_completion": completeness_stats["incomplete_completion"],
                },
            }

            if critical_issues:
                logger.warning(
                    f"⚠️ Trace completeness health check: {health_status} - {len(critical_issues)} critical issues found"
                )
                for issue in critical_issues:
                    logger.warning(f"  - {issue}")
            else:
                logger.info(f"✅ Trace completeness health check: {health_status} - No critical issues found")

            return response

    except Exception as e:
        logger.error(f"❌ Trace completeness health check failed: {e}")
        return {"status": "error", "error": str(e), "timestamp": datetime.now(UTC).isoformat()}

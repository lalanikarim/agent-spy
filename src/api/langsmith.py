"""LangSmith compatibility endpoints for runs/traces."""

from fastapi import APIRouter

from src.core.logging import get_logger
from src.schemas.runs import LangSmithInfo

logger = get_logger(__name__)
router = APIRouter()


@router.get("/info", response_model=LangSmithInfo, summary="Service Information")
async def get_service_info() -> LangSmithInfo:
    """
    Get service information endpoint that LangSmith clients expect.

    This endpoint provides information about the service capabilities
    and configuration that LangSmith clients use for compatibility.
    """
    logger.debug("Service info requested")

    info = LangSmithInfo(
        version="0.1.0",
        license_expiration_time=None,  # No license expiration for local service
        tenant_handle="agent-spy-local",
    )

    logger.info("Service info provided")
    return info

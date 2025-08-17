"""Cache management API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.core.logging import get_logger
from src.core.redis import manager as redis_manager
from src.services.cache_service import cache_service
from src.services.dashboard_cache_service import dashboard_cache
from src.services.rate_limit_service import rate_limit_service

logger = get_logger(__name__)
router = APIRouter()


class CacheStatusResponse(BaseModel):
    """Cache status response model."""

    redis_status: dict[str, Any]
    cache_service_status: dict[str, Any]
    rate_limit_status: dict[str, Any]
    dashboard_cache_status: dict[str, Any]


class CacheOperationResponse(BaseModel):
    """Cache operation response model."""

    success: bool
    message: str
    details: dict[str, Any]


@router.get("/cache/status", response_model=CacheStatusResponse, summary="Get Cache Status")
async def get_cache_status() -> CacheStatusResponse:
    """Get comprehensive cache system status."""
    try:
        # Get Redis status
        redis_status = await redis_manager.health_check()

        # Get cache service status
        cache_service_status = await cache_service.get_backend_status()

        # Get rate limit service status
        rate_limit_status = await rate_limit_service.get_backend_status()

        # Get dashboard cache status
        dashboard_cache_status = {
            "enabled": True,
            "stats_ttl": dashboard_cache.stats_ttl,
            "project_stats_ttl": dashboard_cache.project_stats_ttl,
        }

        return CacheStatusResponse(
            redis_status=redis_status,
            cache_service_status=cache_service_status,
            rate_limit_status=rate_limit_status,
            dashboard_cache_status=dashboard_cache_status,
        )

    except Exception as e:
        logger.error(f"Failed to get cache status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache status: {str(e)}")


@router.post("/cache/clear", response_model=CacheOperationResponse, summary="Clear All Cache")
async def clear_all_cache() -> CacheOperationResponse:
    """Clear all cached data."""
    try:
        # Clear cache service
        cache_cleared = await cache_service.invalidate_pattern("*")

        # Clear dashboard cache
        await dashboard_cache.invalidate_dashboard_cache()

        return CacheOperationResponse(
            success=True,
            message="Cache cleared successfully",
            details={
                "cache_keys_cleared": cache_cleared,
                "dashboard_cache_cleared": True,
            },
        )

    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.post("/cache/clear/pattern", response_model=CacheOperationResponse, summary="Clear Cache Pattern")
async def clear_cache_pattern(
    pattern: str = Query(..., description="Cache key pattern to clear (supports wildcards)"),
) -> CacheOperationResponse:
    """Clear cache entries matching a pattern."""
    try:
        keys_cleared = await cache_service.invalidate_pattern(pattern)

        return CacheOperationResponse(
            success=True,
            message=f"Cache pattern '{pattern}' cleared successfully",
            details={
                "pattern": pattern,
                "keys_cleared": keys_cleared,
            },
        )

    except Exception as e:
        logger.error(f"Failed to clear cache pattern '{pattern}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache pattern: {str(e)}")


@router.post("/cache/dashboard/warm", response_model=CacheOperationResponse, summary="Warm Dashboard Cache")
async def warm_dashboard_cache() -> CacheOperationResponse:
    """Pre-warm dashboard cache with common queries."""
    try:
        await dashboard_cache.warm_dashboard_cache()

        return CacheOperationResponse(
            success=True,
            message="Dashboard cache warmed successfully",
            details={
                "cache_type": "dashboard",
                "warmed": True,
            },
        )

    except Exception as e:
        logger.error(f"Failed to warm dashboard cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to warm dashboard cache: {str(e)}")


@router.post("/cache/dashboard/clear", response_model=CacheOperationResponse, summary="Clear Dashboard Cache")
async def clear_dashboard_cache() -> CacheOperationResponse:
    """Clear dashboard-specific cache."""
    try:
        await dashboard_cache.invalidate_dashboard_cache()

        return CacheOperationResponse(
            success=True,
            message="Dashboard cache cleared successfully",
            details={
                "cache_type": "dashboard",
                "cleared": True,
            },
        )

    except Exception as e:
        logger.error(f"Failed to clear dashboard cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear dashboard cache: {str(e)}")


@router.get("/cache/keys", summary="List Cache Keys")
async def list_cache_keys(
    pattern: str = Query("*", description="Pattern to match cache keys"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of keys to return"),
) -> dict[str, Any]:
    """List cache keys matching a pattern."""
    try:
        # This would require Redis to be available
        if not redis_manager.enabled:
            return {"keys": [], "pattern": pattern, "total": 0, "message": "Redis not available for key listing"}

            # Get keys matching pattern
        if redis_manager.client is None:
            return {"keys": [], "pattern": pattern, "total": 0, "message": "Redis client not available"}

        keys = await redis_manager.client.keys(pattern)

        # Get TTL for each key
        ttls = []
        for key in keys[:limit]:
            ttl = await redis_manager.client.ttl(key)
            ttls.append({"key": key, "ttl": ttl})

        return {
            "keys": ttls,
            "pattern": pattern,
            "total": len(keys),
            "returned": len(ttls),
        }

    except Exception as e:
        logger.error(f"Failed to list cache keys: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list cache keys: {str(e)}")


@router.delete("/cache/keys/{key:path}", response_model=CacheOperationResponse, summary="Delete Cache Key")
async def delete_cache_key(key: str) -> CacheOperationResponse:
    """Delete a specific cache key."""
    try:
        success = await cache_service.delete(key)

        if success:
            return CacheOperationResponse(
                success=True, message=f"Cache key '{key}' deleted successfully", details={"key": key, "deleted": True}
            )
        else:
            return CacheOperationResponse(
                success=False,
                message=f"Cache key '{key}' not found or already deleted",
                details={"key": key, "deleted": False},
            )

    except Exception as e:
        logger.error(f"Failed to delete cache key '{key}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete cache key: {str(e)}")


@router.get("/cache/stats", summary="Get Cache Statistics")
async def get_cache_stats() -> dict[str, Any]:
    """Get cache performance statistics."""
    try:
        # Get Redis info if available
        redis_info = {}
        if redis_manager.enabled:
            try:
                if redis_manager.client is None:
                    redis_info = {"error": "Redis client not available"}
                else:
                    info = await redis_manager.client.info()
                    redis_info = {
                        "memory_used": info.get("used_memory_human"),
                        "memory_peak": info.get("used_memory_peak_human"),
                        "connected_clients": info.get("connected_clients"),
                        "total_commands_processed": info.get("total_commands_processed"),
                        "keyspace_hits": info.get("keyspace_hits"),
                        "keyspace_misses": info.get("keyspace_misses"),
                    }
            except Exception as e:
                logger.warning(f"Failed to get Redis info: {e}")

        # Get cache service status
        cache_status = await cache_service.get_backend_status()

        # Get rate limit status
        rate_limit_status = await rate_limit_service.get_backend_status()

        return {
            "redis": redis_info,
            "cache_service": cache_status,
            "rate_limit": rate_limit_status,
            "timestamp": "2024-01-01T00:00:00Z",  # TODO: Add actual timestamp
        }

    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

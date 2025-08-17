"""Optional Redis connection and service management with fallbacks."""

import json
from contextlib import asynccontextmanager
from typing import Any

from src.core.config import get_settings
from src.core.logging import get_logger

# Redis imports with optional handling
_redis_available = False
redis = None  # type: ignore
ConnectionPool = None  # type: ignore
ConnectionError = Exception
TimeoutError = Exception
RedisError = Exception

try:
    import redis.asyncio as redis
    from redis.asyncio.connection import ConnectionPool

    _redis_available = True
except ImportError:
    pass

REDIS_AVAILABLE = _redis_available

logger = get_logger(__name__)

# Global Redis client and pool
redis_client: Any | None = None if REDIS_AVAILABLE else None
redis_pool: Any | None = None if REDIS_AVAILABLE else None
redis_enabled: bool = False


class RedisManager:
    """Optional Redis connection and service manager with fallbacks."""

    def __init__(self):
        self.client: Any | None = None
        self.pool: Any | None = None
        self.settings = get_settings()
        self.enabled = False

    async def initialize(self) -> None:
        """Initialize Redis connection if enabled and available."""
        global redis_client, redis_pool, redis_enabled

        # Check if Redis is enabled in configuration
        if not self.settings.redis_enabled:
            logger.info("Redis is disabled in configuration")
            redis_enabled = False
            return

        # Check if Redis dependencies are available
        if not REDIS_AVAILABLE:
            logger.warning("Redis dependencies not installed, falling back to in-memory alternatives")
            redis_enabled = False
            return

        try:
            # Create connection pool
            if ConnectionPool is not None:
                self.pool = ConnectionPool.from_url(
                    self.settings.get_redis_url(),
                    max_connections=self.settings.redis_max_connections,
                    retry_on_timeout=self.settings.redis_retry_on_timeout,
                    socket_timeout=self.settings.redis_socket_timeout,
                    socket_connect_timeout=self.settings.redis_socket_connect_timeout,
                    health_check_interval=30,
                )

                # Create Redis client
                if redis is not None:
                    self.client = redis.Redis(connection_pool=self.pool)
                else:
                    raise RuntimeError("Redis module not available")
            else:
                raise RuntimeError("ConnectionPool not available")

            # Test connection
            await self.client.ping()

            # Set global references
            redis_client = self.client
            redis_pool = self.pool
            redis_enabled = True
            self.enabled = True

            logger.info(f"Redis connection initialized: {self.settings.redis_host}:{self.settings.redis_port}")

        except Exception as e:
            logger.warning(f"Failed to initialize Redis connection, falling back to alternatives: {e}")
            redis_enabled = False
            self.enabled = False
            # Don't raise - graceful fallback

    async def close(self) -> None:
        """Close Redis connections."""
        global redis_client, redis_pool, redis_enabled

        if self.client:
            try:
                await self.client.aclose()
            except Exception as e:
                logger.warning(f"Error closing Redis client: {e}")
            finally:
                self.client = None
                redis_client = None

        if self.pool:
            try:
                await self.pool.aclose()
            except Exception as e:
                logger.warning(f"Error closing Redis pool: {e}")
            finally:
                self.pool = None
                redis_pool = None

        redis_enabled = False
        self.enabled = False
        logger.info("Redis connections closed")

    async def health_check(self) -> dict[str, Any]:
        """Perform Redis health check."""
        if not self.enabled or not self.client:
            return {
                "status": "disabled" if not self.settings.redis_enabled else "disconnected",
                "enabled": self.settings.redis_enabled,
                "available": REDIS_AVAILABLE,
                "error": "Redis not enabled" if not self.settings.redis_enabled else "Redis not connected",
            }

        try:
            # Test basic connectivity
            pong = await self.client.ping()

            # Get Redis info
            info = await self.client.info()

            return {
                "status": "connected",
                "enabled": True,
                "available": True,
                "ping": pong,
                "version": info.get("redis_version"),
                "memory_used": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "uptime_seconds": info.get("uptime_in_seconds"),
            }

        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {"status": "error", "enabled": True, "available": True, "error": str(e)}


# Global Redis manager instance
manager = RedisManager()


async def init_redis() -> None:
    """Initialize Redis connection."""
    await manager.initialize()


async def close_redis() -> None:
    """Close Redis connection."""
    await manager.close()


def get_redis_client() -> Any:
    """Get Redis client instance."""
    if not redis_enabled or not redis_client:
        raise RuntimeError("Redis not available. Check redis_enabled setting and Redis connectivity.")
    return redis_client


def is_redis_available() -> bool:
    """Check if Redis is available for use."""
    return redis_enabled and redis_client is not None


@asynccontextmanager
async def get_redis():
    """Get Redis client context manager."""
    if not is_redis_available():
        raise RuntimeError("Redis not available. Check redis_enabled setting and Redis connectivity.")

    client = get_redis_client()
    try:
        yield client
    except Exception as e:
        logger.error(f"Redis operation error: {e}")
        raise


# Utility functions for common Redis operations
async def redis_get(key: str, default: Any = None) -> Any:
    """Get value from Redis with JSON deserialization."""
    if not is_redis_available():
        return default

    try:
        async with get_redis() as client:
            value = await client.get(key)
            if value is None:
                return default
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value.decode() if isinstance(value, bytes) else value
    except Exception as e:
        logger.warning(f"Redis get error for key {key}: {e}")
        return default


async def redis_set(key: str, value: Any, ttl: int | None = None) -> bool:
    """Set value in Redis with JSON serialization."""
    if not is_redis_available():
        return False

    try:
        async with get_redis() as client:
            if isinstance(value, dict | list):
                value = json.dumps(value, default=str)
            return await client.set(key, value, ex=ttl)
    except Exception as e:
        logger.warning(f"Redis set error for key {key}: {e}")
        return False


async def redis_delete(key: str) -> int:
    """Delete key from Redis."""
    if not is_redis_available():
        return 0

    try:
        async with get_redis() as client:
            return await client.delete(key)
    except Exception as e:
        logger.warning(f"Redis delete error for key {key}: {e}")
        return 0


async def redis_exists(key: str) -> bool:
    """Check if key exists in Redis."""
    if not is_redis_available():
        return False

    try:
        async with get_redis() as client:
            return bool(await client.exists(key))
    except Exception as e:
        logger.warning(f"Redis exists error for key {key}: {e}")
        return False


async def redis_expire(key: str, ttl: int) -> bool:
    """Set TTL for Redis key."""
    if not is_redis_available():
        return False

    try:
        async with get_redis() as client:
            return await client.expire(key, ttl)
    except Exception as e:
        logger.warning(f"Redis expire error for key {key}: {e}")
        return False


# Key generation utilities
def make_cache_key(*parts: str) -> str:
    """Generate cache key with consistent naming."""
    settings = get_settings()
    return f"agentspy:{settings.environment}:cache:{':'.join(parts)}"


def make_session_key(session_id: str) -> str:
    """Generate session key."""
    settings = get_settings()
    return f"agentspy:{settings.environment}:session:{session_id}"


def make_pubsub_channel(*parts: str) -> str:
    """Generate pub/sub channel name."""
    settings = get_settings()
    return f"agentspy:{settings.environment}:pubsub:{':'.join(parts)}"


def make_rate_limit_key(identifier: str, window: str) -> str:
    """Generate rate limit key."""
    settings = get_settings()
    return f"agentspy:{settings.environment}:ratelimit:{identifier}:{window}"

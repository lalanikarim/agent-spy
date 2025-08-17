"""Dual-backend rate limiting service with Redis and in-memory fallback."""

import time
from collections import defaultdict
from threading import Lock

from src.core.config import get_settings
from src.core.logging import get_logger
from src.core.redis import get_redis, is_redis_available, make_rate_limit_key

logger = get_logger(__name__)


class InMemoryRateLimiter:
    """In-memory rate limiter fallback."""

    def __init__(self):
        self.counters: dict[str, list[float]] = defaultdict(list)
        self.lock = Lock()

    def _cleanup_old_entries(self, key: str, window_seconds: int):
        """Remove old entries outside the sliding window."""
        current_time = time.time()
        cutoff_time = current_time - window_seconds

        with self.lock:
            self.counters[key] = [timestamp for timestamp in self.counters[key] if timestamp > cutoff_time]

    def is_allowed(self, key: str, limit: int, window_seconds: int) -> tuple[bool, dict]:
        """Check if request is allowed within rate limit."""
        self._cleanup_old_entries(key, window_seconds)

        with self.lock:
            current_count = len(self.counters[key])
            is_allowed = current_count < limit

            if is_allowed:
                self.counters[key].append(time.time())

            return is_allowed, {
                "limit": limit,
                "remaining": max(0, limit - current_count - (1 if is_allowed else 0)),
                "reset_time": time.time() + window_seconds,
                "current_count": current_count + (1 if is_allowed else 0),
            }


class RateLimitService:
    """Dual-backend rate limiting service with Redis and in-memory fallback."""

    def __init__(self):
        self.settings = get_settings()
        self.memory_limiter = InMemoryRateLimiter()
        self._redis_available = False
        self._check_redis_availability()

    def _check_redis_availability(self):
        """Check if Redis is available for use."""
        self._redis_available = is_redis_available()

    async def is_allowed(
        self, identifier: str, limit: int, window_seconds: int = 3600, window_type: str = "sliding"
    ) -> tuple[bool, dict]:
        """
        Check if request is allowed within rate limit.

        Args:
            identifier: Unique identifier for rate limiting (e.g., IP, user ID, API key)
            limit: Maximum number of requests allowed in the window
            window_seconds: Time window in seconds
            window_type: Type of window ("sliding" or "fixed")

        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        self._check_redis_availability()

        if self._redis_available and window_type == "sliding":
            return await self._redis_sliding_window(identifier, limit, window_seconds)
        else:
            return self._memory_rate_limit(identifier, limit, window_seconds)

    async def _redis_sliding_window(self, identifier: str, limit: int, window_seconds: int) -> tuple[bool, dict]:
        """Redis-based sliding window rate limiting."""
        current_time = time.time()
        window_start = current_time - window_seconds

        try:
            async with get_redis() as client:
                # Use Redis sorted set for sliding window
                key = make_rate_limit_key(identifier, f"sliding_{window_seconds}")

                # Remove old entries outside the window
                await client.zremrangebyscore(key, 0, window_start)

                # Get current count
                current_count = await client.zcard(key)

                # Check if request is allowed
                is_allowed = current_count < limit

                if is_allowed:
                    # Add current request timestamp
                    await client.zadd(key, {str(current_time): current_time})
                    await client.expire(key, window_seconds)

                # Get remaining requests
                remaining = max(0, limit - current_count - (1 if is_allowed else 0))

                # Calculate reset time
                reset_time = current_time + window_seconds

                return is_allowed, {
                    "limit": limit,
                    "remaining": remaining,
                    "reset_time": reset_time,
                    "current_count": current_count + (1 if is_allowed else 0),
                    "backend": "redis",
                }

        except Exception as e:
            logger.warning(f"Redis rate limiting failed, falling back to memory: {e}")
            self._redis_available = False
            return self._memory_rate_limit(identifier, limit, window_seconds)

    def _memory_rate_limit(self, identifier: str, limit: int, window_seconds: int) -> tuple[bool, dict]:
        """In-memory rate limiting fallback."""
        is_allowed, info = self.memory_limiter.is_allowed(identifier, limit, window_seconds)
        info["backend"] = "memory"
        return is_allowed, info

    async def get_rate_limit_info(self, identifier: str, window_seconds: int = 3600) -> dict:
        """Get current rate limit information without consuming a request."""
        self._check_redis_availability()

        if self._redis_available:
            try:
                async with get_redis() as client:
                    key = make_rate_limit_key(identifier, f"sliding_{window_seconds}")
                    current_time = time.time()
                    window_start = current_time - window_seconds

                    # Remove old entries
                    await client.zremrangebyscore(key, 0, window_start)

                    # Get current count
                    current_count = await client.zcard(key)

                    return {"current_count": current_count, "reset_time": current_time + window_seconds, "backend": "redis"}

            except Exception as e:
                logger.warning(f"Redis rate limit info failed: {e}")
                self._redis_available = False

        # Fallback to memory
        return {
            "current_count": len(self.memory_limiter.counters[identifier]),
            "reset_time": time.time() + window_seconds,
            "backend": "memory",
        }

    async def reset_rate_limit(self, identifier: str, window_seconds: int = 3600) -> bool:
        """Reset rate limit for an identifier."""
        self._check_redis_availability()

        success = False

        if self._redis_available:
            try:
                async with get_redis() as client:
                    key = make_rate_limit_key(identifier, f"sliding_{window_seconds}")
                    await client.delete(key)
                    success = True
                    logger.debug(f"Redis rate limit reset for: {identifier}")
            except Exception as e:
                logger.warning(f"Redis rate limit reset failed: {e}")
                self._redis_available = False

        # Also reset memory limiter
        with self.memory_limiter.lock:
            self.memory_limiter.counters[identifier].clear()
            success = True

        return success

    async def get_backend_status(self) -> dict:
        """Get status of rate limiting backends."""
        self._check_redis_availability()

        return {
            "redis_available": self._redis_available,
            "memory_counters": len(self.memory_limiter.counters),
            "active_backend": "redis" if self._redis_available else "memory",
        }


# Global rate limit service instance
rate_limit_service = RateLimitService()


# Rate limiting decorator
def rate_limit(limit: int, window_seconds: int = 3600, identifier_func=None):
    """
    Decorator for rate limiting endpoints.

    Args:
        limit: Maximum number of requests allowed in the window
        window_seconds: Time window in seconds
        identifier_func: Function to extract identifier from request (defaults to IP)
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract request from args (assuming FastAPI endpoint)
            request = None
            for arg in args:
                if hasattr(arg, "client") and hasattr(arg, "headers"):
                    request = arg
                    break

            if not request:
                # Fallback: use function name as identifier
                identifier = f"func:{func.__name__}"
            else:
                # Use provided function or default to IP
                if identifier_func:
                    identifier = identifier_func(request)
                else:
                    identifier = request.client.host if request.client else "unknown"

            # Check rate limit
            is_allowed, info = await rate_limit_service.is_allowed(identifier, limit, window_seconds)

            if not is_allowed:
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Rate limit exceeded",
                        "limit": info["limit"],
                        "remaining": info["remaining"],
                        "reset_time": info["reset_time"],
                    },
                )

            # Add rate limit headers to response
            response = await func(*args, **kwargs)
            if hasattr(response, "headers"):
                response.headers["X-RateLimit-Limit"] = str(info["limit"])
                response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
                response.headers["X-RateLimit-Reset"] = str(int(info["reset_time"]))

            return response

        return wrapper

    return decorator

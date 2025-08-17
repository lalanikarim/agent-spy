"""Dual-backend caching service with Redis and in-memory fallback."""

import hashlib
import json
import time
from collections import OrderedDict
from collections.abc import Callable
from functools import wraps
from threading import Lock
from typing import Any, TypeVar

from src.core.config import get_settings
from src.core.logging import get_logger
from src.core.redis import get_redis, is_redis_available, make_cache_key, redis_enabled

logger = get_logger(__name__)

T = TypeVar("T")


class InMemoryCache:
    """LRU in-memory cache fallback."""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
        self.expiry: dict[str, float] = {}
        self.lock = Lock()

    def get(self, key: str) -> Any:
        """Get value from in-memory cache."""
        with self.lock:
            # Check expiry
            if key in self.expiry and time.time() > self.expiry[key]:
                self.cache.pop(key, None)
                self.expiry.pop(key, None)
                return None

            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                return self.cache[key]

            return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set value in in-memory cache."""
        with self.lock:
            # Remove oldest items if at capacity
            while len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                self.cache.pop(oldest_key)
                self.expiry.pop(oldest_key, None)

            self.cache[key] = value
            if ttl:
                self.expiry[key] = time.time() + ttl

            return True

    def delete(self, key: str) -> bool:
        """Delete key from in-memory cache."""
        with self.lock:
            deleted = key in self.cache
            self.cache.pop(key, None)
            self.expiry.pop(key, None)
            return deleted

    def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern (simple prefix matching)."""
        with self.lock:
            keys_to_delete = [k for k in self.cache if pattern.replace("*", "") in k]
            for key in keys_to_delete:
                self.cache.pop(key, None)
                self.expiry.pop(key, None)
            return len(keys_to_delete)


class CacheService:
    """Dual-backend caching service with Redis and in-memory fallback."""

    def __init__(self):
        self.settings = get_settings()
        self.default_ttl = self.settings.cache_default_ttl
        self.key_prefix = "cache"
        self.memory_cache = InMemoryCache(max_size=self.settings.cache_memory_size)
        self._redis_available = False
        self._check_redis_availability()

    def _check_redis_availability(self):
        """Check if Redis is available for use."""
        self._redis_available = is_redis_available()

    async def get(self, key: str, default: Any = None) -> Any:
        """Get cached value from Redis or in-memory fallback."""
        self._check_redis_availability()

        if self._redis_available:
            # Try Redis first
            cache_key = make_cache_key(self.key_prefix, key)
            try:
                async with get_redis() as client:
                    value = await client.get(cache_key)
                    if value is not None:
                        logger.debug(f"Redis cache hit: {cache_key}")
                        return json.loads(value)
            except Exception as e:
                logger.warning(f"Redis cache error, falling back to memory: {e}")
                self._redis_available = False

        # Fallback to in-memory cache
        memory_value = self.memory_cache.get(key)
        if memory_value is not None:
            logger.debug(f"Memory cache hit: {key}")
            return memory_value

        logger.debug(f"Cache miss: {key}")
        return default

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set cached value in Redis and/or in-memory cache."""
        ttl = ttl or self.default_ttl
        success = False

        self._check_redis_availability()

        if self._redis_available:
            # Try Redis first
            cache_key = make_cache_key(self.key_prefix, key)
            try:
                async with get_redis() as client:
                    serialized = json.dumps(value, default=str)
                    result = await client.setex(cache_key, ttl, serialized)
                    if result:
                        logger.debug(f"Redis cache set: {cache_key} (TTL: {ttl}s)")
                        success = True
            except Exception as e:
                logger.warning(f"Redis cache set error, using memory fallback: {e}")
                self._redis_available = False

        # Always set in memory cache as backup
        memory_success = self.memory_cache.set(key, value, ttl)
        if not success and memory_success:
            logger.debug(f"Memory cache set: {key} (TTL: {ttl}s)")
            success = True

        return success

    async def delete(self, key: str) -> bool:
        """Delete cached value from both Redis and memory."""
        redis_success = False
        memory_success = False

        self._check_redis_availability()

        if self._redis_available:
            cache_key = make_cache_key(self.key_prefix, key)
            try:
                async with get_redis() as client:
                    redis_success = bool(await client.delete(cache_key))
                    logger.debug(f"Redis cache delete: {cache_key}")
            except Exception as e:
                logger.warning(f"Redis cache delete error: {e}")
                self._redis_available = False

        memory_success = self.memory_cache.delete(key)

        return redis_success or memory_success

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern in both backends."""
        total_deleted = 0

        self._check_redis_availability()

        if self._redis_available:
            cache_pattern = make_cache_key(self.key_prefix, pattern)
            try:
                async with get_redis() as client:
                    keys = await client.keys(cache_pattern)
                    if keys:
                        redis_deleted = await client.delete(*keys)
                        total_deleted += redis_deleted
                        logger.info(f"Redis cache invalidated {redis_deleted} keys matching: {cache_pattern}")
            except Exception as e:
                logger.warning(f"Redis cache invalidate error: {e}")
                self._redis_available = False

        # Also clear from memory cache
        memory_deleted = self.memory_cache.clear_pattern(pattern)
        total_deleted += memory_deleted

        return total_deleted

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        self._check_redis_availability()

        if self._redis_available:
            cache_key = make_cache_key(self.key_prefix, key)
            try:
                async with get_redis() as client:
                    return bool(await client.exists(cache_key))
            except Exception as e:
                logger.warning(f"Redis cache exists error: {e}")
                self._redis_available = False

        # Fallback to memory cache
        return self.memory_cache.get(key) is not None

    async def get_ttl(self, key: str) -> int:
        """Get TTL for cached key."""
        self._check_redis_availability()

        if self._redis_available:
            cache_key = make_cache_key(self.key_prefix, key)
            try:
                async with get_redis() as client:
                    return await client.ttl(cache_key)
            except Exception as e:
                logger.warning(f"Redis cache TTL error: {e}")
                self._redis_available = False

        # Fallback to memory cache TTL calculation
        if key in self.memory_cache.expiry:
            remaining = self.memory_cache.expiry[key] - time.time()
            return max(0, int(remaining))

        return -1

    async def get_backend_status(self) -> dict[str, Any]:
        """Get status of cache backends."""
        self._check_redis_availability()

        return {
            "redis_available": self._redis_available,
            "redis_enabled": redis_enabled,
            "memory_cache_size": len(self.memory_cache.cache),
            "memory_cache_max_size": self.memory_cache.max_size,
            "active_backend": "redis" if self._redis_available else "memory",
        }

    def cache_key_for_function(self, func_name: str, *args, **kwargs) -> str:
        """Generate cache key for function call."""
        # Create deterministic key from function name and arguments
        key_data = {"function": func_name, "args": args, "kwargs": sorted(kwargs.items()) if kwargs else {}}
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_string.encode(), usedforsecurity=False).hexdigest()
        return f"func:{func_name}:{key_hash}"


# Global cache service instance
cache_service = CacheService()


# Caching decorators
def cached(ttl: int | None = None, key_prefix: str = ""):
    """Decorator for caching function results."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Generate cache key
            cache_key = cache_service.cache_key_for_function(
                f"{key_prefix}{func.__name__}" if key_prefix else func.__name__, *args, **kwargs
            )

            # Try to get from cache
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_service.set(cache_key, result, ttl)

            return result

        # Add cache management methods to function
        def cache_invalidate(*args: Any, **kwargs: Any) -> Any:
            return cache_service.delete(
                cache_service.cache_key_for_function(
                    f"{key_prefix}{func.__name__}" if key_prefix else func.__name__, *args, **kwargs
                )
            )

        wrapper.cache_invalidate = cache_invalidate

        return wrapper

    return decorator


def cache_invalidate_on_change(patterns: list[str]):
    """Decorator to invalidate cache patterns when function executes."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            result = await func(*args, **kwargs)

            # Invalidate cache patterns after successful execution
            for pattern in patterns:
                await cache_service.invalidate_pattern(pattern)

            return result

        return wrapper

    return decorator


# Add decorators to cache service for convenience
cache_service.cached = cached
cache_service.cache_invalidate_on_change = cache_invalidate_on_change

"""Tests for Redis integration."""

import pytest

from src.core.redis import RedisManager, is_redis_available
from src.services.cache_service import cache_service
from src.services.rate_limit_service import rate_limit_service
from src.services.session_service import session_service


@pytest.mark.asyncio
async def test_redis_manager_initialization():
    """Test Redis manager initialization."""
    manager = RedisManager()

    # Test initialization without Redis enabled
    await manager.initialize()
    assert not manager.enabled

    # Test health check when disabled
    health = await manager.health_check()
    assert health["status"] in ["disabled", "disconnected"]


@pytest.mark.asyncio
async def test_cache_service_without_redis():
    """Test cache service works without Redis."""
    # Test basic cache operations
    await cache_service.set("test_key", "test_value", ttl=60)

    # Get value
    value = await cache_service.get("test_key")
    assert value == "test_value"

    # Test exists
    exists = await cache_service.exists("test_key")
    assert exists is True

    # Test delete
    deleted = await cache_service.delete("test_key")
    assert deleted is True

    # Test get after delete
    value = await cache_service.get("test_key")
    assert value is None


@pytest.mark.asyncio
async def test_cache_service_complex_data():
    """Test cache service with complex data types."""
    test_data = {"string": "test", "number": 42, "list": [1, 2, 3], "dict": {"nested": "value"}, "boolean": True}

    await cache_service.set("complex_key", test_data, ttl=60)
    retrieved = await cache_service.get("complex_key")

    assert retrieved == test_data


@pytest.mark.asyncio
async def test_session_service_without_redis():
    """Test session service works without Redis."""
    # Test session creation (should return None when Redis unavailable)
    session = await session_service.create_session({"user_id": "123"})
    assert session is None

    # Test session retrieval
    retrieved = await session_service.get_session("test_session_id")
    assert retrieved is None


@pytest.mark.asyncio
async def test_rate_limit_service_without_redis():
    """Test rate limit service works without Redis."""
    # Test rate limiting
    is_allowed, info = await rate_limit_service.is_allowed("test_user", 10, 3600)
    assert is_allowed is True
    assert info["limit"] == 10
    assert info["remaining"] == 9
    assert info["backend"] == "memory"


@pytest.mark.asyncio
async def test_rate_limit_service_multiple_requests():
    """Test rate limiting with multiple requests."""
    identifier = "test_user_2"
    limit = 3
    window = 3600

    # Make requests up to limit
    for i in range(limit):
        is_allowed, info = await rate_limit_service.is_allowed(identifier, limit, window)
        assert is_allowed is True
        assert info["remaining"] == limit - i - 1

    # Next request should be blocked
    is_allowed, info = await rate_limit_service.is_allowed(identifier, limit, window)
    assert is_allowed is False
    assert info["remaining"] == 0


@pytest.mark.asyncio
async def test_cache_service_pattern_invalidation():
    """Test cache pattern invalidation."""
    # Set multiple keys with pattern
    await cache_service.set("user:123:profile", {"name": "John"}, ttl=60)
    await cache_service.set("user:123:settings", {"theme": "dark"}, ttl=60)
    await cache_service.set("user:456:profile", {"name": "Jane"}, ttl=60)

    # Invalidate pattern
    deleted = await cache_service.invalidate_pattern("user:123:*")
    assert deleted >= 2

    # Check that user:123 keys are gone
    assert await cache_service.get("user:123:profile") is None
    assert await cache_service.get("user:123:settings") is None

    # Check that user:456 key still exists
    assert await cache_service.get("user:456:profile") is not None


@pytest.mark.asyncio
async def test_cache_service_ttl():
    """Test cache TTL functionality."""
    await cache_service.set("ttl_test", "value", ttl=60)  # Use longer TTL for testing

    # Check TTL
    ttl = await cache_service.get_ttl("ttl_test")
    assert ttl > 0 or ttl == -1  # Allow -1 for keys without TTL

    # Check that key exists
    value = await cache_service.get("ttl_test")
    assert value == "value"


@pytest.mark.asyncio
async def test_cache_service_backend_status():
    """Test cache service backend status."""
    status = await cache_service.get_backend_status()

    assert "redis_available" in status
    assert "memory_cache_size" in status
    assert "active_backend" in status
    assert status["active_backend"] in ["redis", "memory"]


@pytest.mark.asyncio
async def test_rate_limit_service_reset():
    """Test rate limit reset functionality."""
    identifier = "reset_test_user"
    limit = 5

    # Make some requests
    for _i in range(3):
        await rate_limit_service.is_allowed(identifier, limit, 3600)

    # Reset rate limit
    reset_success = await rate_limit_service.reset_rate_limit(identifier, 3600)
    assert reset_success is True

    # Should be able to make full limit of requests again
    for _i in range(limit):
        is_allowed, info = await rate_limit_service.is_allowed(identifier, limit, 3600)
        assert is_allowed is True


@pytest.mark.asyncio
async def test_rate_limit_service_info():
    """Test rate limit info retrieval."""
    identifier = "info_test_user"
    limit = 10

    # Get initial info
    info = await rate_limit_service.get_rate_limit_info(identifier, 3600)
    assert "current_count" in info
    assert "reset_time" in info
    assert "backend" in info

    # Make a request
    await rate_limit_service.is_allowed(identifier, limit, 3600)

    # Get updated info
    updated_info = await rate_limit_service.get_rate_limit_info(identifier, 3600)
    assert updated_info["current_count"] == 1


@pytest.mark.asyncio
async def test_redis_availability_check():
    """Test Redis availability checking."""
    # Test when Redis is not available
    available = is_redis_available()
    assert isinstance(available, bool)


@pytest.mark.asyncio
async def test_cache_decorator():
    """Test cache decorator functionality."""
    call_count = 0

    @cache_service.cached(ttl=60)
    async def expensive_function(param: str):
        nonlocal call_count
        call_count += 1
        return f"result_{param}_{call_count}"

    # First call should execute function
    result1 = await expensive_function("test")
    assert result1 == "result_test_1"
    assert call_count == 1

    # Second call should use cache
    result2 = await expensive_function("test")
    assert result2 == "result_test_1"  # Same result
    assert call_count == 1  # Function not called again

    # Different parameter should execute function
    result3 = await expensive_function("different")
    assert result3 == "result_different_2"
    assert call_count == 2


@pytest.mark.asyncio
async def test_cache_invalidate_decorator():
    """Test cache invalidate decorator."""

    @cache_service.cache_invalidate_on_change(["test_pattern:*"])
    async def update_function():
        return "updated"

    # Set some test data
    await cache_service.set("test_pattern:1", "value1")
    await cache_service.set("test_pattern:2", "value2")
    await cache_service.set("other:1", "value3")

    # Execute function
    result = await update_function()
    assert result == "updated"

    # Check that pattern keys are invalidated
    assert await cache_service.get("test_pattern:1") is None
    assert await cache_service.get("test_pattern:2") is None
    assert await cache_service.get("other:1") is not None  # Should still exist

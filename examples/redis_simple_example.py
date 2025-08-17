#!/usr/bin/env python3
"""
Simple Redis Integration Example for Agent Spy

This example demonstrates the Redis integration features without database dependencies.
"""

import asyncio
import json
from datetime import datetime

from src.core.redis import close_redis, init_redis
from src.core.redis import manager as redis_manager
from src.services.cache_service import cache_service
from src.services.rate_limit_service import rate_limit_service
from src.services.session_service import session_service


async def demonstrate_cache_service():
    """Demonstrate cache service functionality."""
    print("\n=== Cache Service Demo ===")

    # Test basic caching
    print("Setting cache value...")
    await cache_service.set("demo:user:123", {"name": "John Doe", "email": "john@example.com"}, ttl=300)

    print("Retrieving cache value...")
    user_data = await cache_service.get("demo:user:123")
    print(f"Retrieved: {json.dumps(user_data, indent=2)}")

    # Test cache decorator
    @cache_service.cached(ttl=60)
    async def expensive_calculation(n: int):
        print(f"  Computing expensive calculation for {n}...")
        await asyncio.sleep(0.1)  # Simulate expensive operation
        return n * n

    print("\nTesting cache decorator...")
    result1 = await expensive_calculation(5)
    print(f"First call result: {result1}")

    result2 = await expensive_calculation(5)  # Should use cache
    print(f"Second call result: {result2} (should be cached)")

    # Test pattern invalidation
    print("\nTesting pattern invalidation...")
    await cache_service.set("demo:users:1:profile", {"name": "Alice"})
    await cache_service.set("demo:users:2:profile", {"name": "Bob"})
    await cache_service.set("demo:config:theme", {"color": "blue"})

    print("Before invalidation:")
    print(f"  User 1: {await cache_service.get('demo:users:1:profile')}")
    print(f"  User 2: {await cache_service.get('demo:users:2:profile')}")
    print(f"  Config: {await cache_service.get('demo:config:theme')}")

    deleted = await cache_service.invalidate_pattern("demo:users:*")
    print(f"Invalidated {deleted} user keys")

    print("After invalidation:")
    print(f"  User 1: {await cache_service.get('demo:users:1:profile')}")
    print(f"  User 2: {await cache_service.get('demo:users:2:profile')}")
    print(f"  Config: {await cache_service.get('demo:config:theme')}")


async def demonstrate_session_service():
    """Demonstrate session service functionality."""
    print("\n=== Session Service Demo ===")

    # Create a session
    session_data = {"user_id": "12345", "username": "demo_user", "login_time": datetime.now().isoformat()}

    session = await session_service.create_session(session_data)
    if session:
        print(f"Created session: {session.session_id}")
        print(f"Session data: {json.dumps(session.data, indent=2)}")

        # Retrieve session
        retrieved = await session_service.get_session(session.session_id)
        if retrieved:
            print(f"Retrieved session: {retrieved.session_id}")
            print(f"Last accessed: {retrieved.last_accessed}")

        # Update session
        await session_service.update_session(session.session_id, {"last_action": "demo_completed"})

        # Get updated session
        updated = await session_service.get_session(session.session_id)
        if updated:
            print(f"Updated session data: {json.dumps(updated.data, indent=2)}")

        # Clean up
        await session_service.delete_session(session.session_id)
        print("Session deleted")
    else:
        print("Session service not available (Redis disabled)")


async def demonstrate_rate_limiting():
    """Demonstrate rate limiting functionality."""
    print("\n=== Rate Limiting Demo ===")

    identifier = "demo_user"
    limit = 5
    window = 3600  # 1 hour

    print(f"Testing rate limiting for '{identifier}' (limit: {limit} requests per hour)")

    # Make requests up to limit
    for i in range(limit + 2):  # Try to exceed limit
        is_allowed, info = await rate_limit_service.is_allowed(identifier, limit, window)

        if is_allowed:
            print(f"  Request {i + 1}: ALLOWED (remaining: {info['remaining']})")
        else:
            print(f"  Request {i + 1}: BLOCKED (limit exceeded)")
            break

    # Get rate limit info
    info = await rate_limit_service.get_rate_limit_info(identifier, window)
    print(f"\nRate limit info: {json.dumps(info, indent=2)}")

    # Reset rate limit
    await rate_limit_service.reset_rate_limit(identifier, window)
    print("Rate limit reset")

    # Test again after reset
    is_allowed, info = await rate_limit_service.is_allowed(identifier, limit, window)
    print(f"After reset: {'ALLOWED' if is_allowed else 'BLOCKED'}")


async def demonstrate_cache_management():
    """Demonstrate cache management functionality."""
    print("\n=== Cache Management Demo ===")

    # Get cache status
    status = await cache_service.get_backend_status()
    print(f"Cache backend status: {json.dumps(status, indent=2)}")

    # Get Redis status
    redis_status = await redis_manager.health_check()
    print(f"Redis status: {json.dumps(redis_status, indent=2)}")

    # Set some test data
    await cache_service.set("demo:test:1", "value1")
    await cache_service.set("demo:test:2", "value2")
    await cache_service.set("demo:test:3", "value3")

    # Check if keys exist
    for i in range(1, 4):
        exists = await cache_service.exists(f"demo:test:{i}")
        print(f"Key demo:test:{i} exists: {exists}")

    # Get TTL for a key
    ttl = await cache_service.get_ttl("demo:test:1")
    print(f"TTL for demo:test:1: {ttl} seconds")


async def demonstrate_graceful_fallbacks():
    """Demonstrate graceful fallbacks when Redis is unavailable."""
    print("\n=== Graceful Fallbacks Demo ===")

    # Check Redis availability
    redis_available = redis_manager.enabled
    print(f"Redis available: {redis_available}")

    if not redis_available:
        print("Redis is not available - all operations will use in-memory fallbacks")
        print("This demonstrates the graceful degradation feature")

    # All operations should work regardless of Redis availability
    print("\nTesting operations with fallbacks:")

    # Cache operations
    await cache_service.set("fallback:test", "works without Redis")
    value = await cache_service.get("fallback:test")
    print(f"Cache get/set: {value}")

    # Rate limiting
    is_allowed, info = await rate_limit_service.is_allowed("fallback_user", 10, 3600)
    print(f"Rate limiting: {'ALLOWED' if is_allowed else 'BLOCKED'} (backend: {info['backend']})")

    # Session operations (will return None when Redis unavailable)
    session = await session_service.create_session({"test": "data"})
    print(f"Session creation: {'SUCCESS' if session else 'FALLBACK (no Redis)'}")


async def main():
    """Main demonstration function."""
    print("Agent Spy Redis Integration Demo (Simple)")
    print("=" * 50)

    # Initialize Redis
    print("Initializing Redis...")
    await init_redis()

    try:
        # Run demonstrations
        await demonstrate_cache_service()
        await demonstrate_session_service()
        await demonstrate_rate_limiting()
        await demonstrate_cache_management()
        await demonstrate_graceful_fallbacks()

        print("\n" + "=" * 50)
        print("Demo completed successfully!")
        print("\nKey Features Demonstrated:")
        print("- Optional Redis integration with graceful fallbacks")
        print("- Dual-backend caching (Redis + in-memory)")
        print("- Session management with Redis")
        print("- Rate limiting with sliding windows")
        print("- Cache management and monitoring")
        print("- Automatic fallback to in-memory alternatives")

    finally:
        # Clean up
        print("\nCleaning up...")
        await close_redis()


if __name__ == "__main__":
    asyncio.run(main())

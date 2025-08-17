"""Redis-backed session management service."""

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from src.core.config import get_settings
from src.core.logging import get_logger
from src.core.redis import get_redis, is_redis_available, make_session_key

logger = get_logger(__name__)


class SessionData:
    """Session data container."""

    def __init__(self, session_id: str, data: dict[str, Any] = None):
        self.session_id = session_id
        self.data = data or {}
        self.created_at = datetime.now(UTC)
        self.last_accessed = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionData":
        """Create session from dictionary."""
        session = cls(data["session_id"], data.get("data", {}))
        session.created_at = datetime.fromisoformat(data["created_at"])
        session.last_accessed = datetime.fromisoformat(data["last_accessed"])
        return session


class RedisSessionService:
    """Redis-backed session management service."""

    def __init__(self):
        self.settings = get_settings()
        self.default_ttl = 86400  # 24 hours
        self.session_prefix = "session"

    async def create_session(self, data: dict[str, Any] = None) -> SessionData | None:
        """Create new session."""
        if not is_redis_available():
            logger.warning("Redis not available for session storage")
            return None

        session_id = str(uuid.uuid4())
        session = SessionData(session_id, data)

        await self._store_session(session)
        logger.debug(f"Session created: {session_id}")

        return session

    async def get_session(self, session_id: str) -> SessionData | None:
        """Get session by ID."""
        if not is_redis_available():
            logger.warning("Redis not available for session storage")
            return None

        session_key = make_session_key(session_id)

        try:
            async with get_redis() as client:
                session_data = await client.get(session_key)
                if not session_data:
                    return None

                session_dict = json.loads(session_data)
                session = SessionData.from_dict(session_dict)

                # Update last accessed time
                session.last_accessed = datetime.now(UTC)
                await self._store_session(session)

                logger.debug(f"Session retrieved: {session_id}")
                return session

        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None

    async def update_session(self, session_id: str, data: dict[str, Any]) -> bool:
        """Update session data."""
        session = await self.get_session(session_id)
        if not session:
            return False

        session.data.update(data)
        session.last_accessed = datetime.now(UTC)

        return await self._store_session(session)

    async def delete_session(self, session_id: str) -> bool:
        """Delete session."""
        if not is_redis_available():
            logger.warning("Redis not available for session storage")
            return False

        session_key = make_session_key(session_id)

        try:
            async with get_redis() as client:
                result = await client.delete(session_key)
                logger.debug(f"Session deleted: {session_id}")
                return bool(result)

        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    async def extend_session(self, session_id: str, ttl: int | None = None) -> bool:
        """Extend session TTL."""
        if not is_redis_available():
            logger.warning("Redis not available for session storage")
            return False

        session_key = make_session_key(session_id)
        ttl = ttl or self.default_ttl

        try:
            async with get_redis() as client:
                result = await client.expire(session_key, ttl)
                logger.debug(f"Session TTL extended: {session_id} ({ttl}s)")
                return result

        except Exception as e:
            logger.error(f"Failed to extend session {session_id}: {e}")
            return False

    async def _store_session(self, session: SessionData) -> bool:
        """Store session in Redis."""
        if not is_redis_available():
            logger.warning("Redis not available for session storage")
            return False

        session_key = make_session_key(session.session_id)

        try:
            async with get_redis() as client:
                session_data = json.dumps(session.to_dict())
                result = await client.setex(session_key, self.default_ttl, session_data)
                return result

        except Exception as e:
            logger.error(f"Failed to store session {session.session_id}: {e}")
            return False

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions (Redis handles this automatically)."""
        # Redis TTL handles automatic cleanup
        # This method could implement additional cleanup logic if needed
        logger.debug("Session cleanup completed (handled by Redis TTL)")
        return 0

    async def get_session_count(self) -> int:
        """Get total number of active sessions."""
        if not is_redis_available():
            return 0

        try:
            async with get_redis() as client:
                pattern = make_session_key("*")
                keys = await client.keys(pattern)
                return len(keys)

        except Exception as e:
            logger.error(f"Failed to get session count: {e}")
            return 0


# Global session service instance
session_service = RedisSessionService()

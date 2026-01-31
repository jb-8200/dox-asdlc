"""Redis implementation of ISessionRepository.

This module provides the Redis-backed implementation for session
persistence operations using JSON serialization.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

from src.core.models.ideation import (
    DataSource,
    IdeationSession,
    ProjectStatus,
)
from src.orchestrator.repositories.interfaces import ISessionRepository

if TYPE_CHECKING:
    import redis.asyncio as redis


# Redis key prefixes
SESSION_KEY_PREFIX = "ideation:session:"
USER_SESSIONS_KEY_PREFIX = "ideation:user_sessions:"


def _session_to_dict(session: IdeationSession) -> dict[str, Any]:
    """Convert IdeationSession to JSON-serializable dict."""
    return {
        "id": session.id,
        "project_name": session.project_name,
        "user_id": session.user_id,
        "status": session.status.value,
        "data_source": session.data_source.value,
        "version": session.version,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }


def _dict_to_session(data: dict[str, Any]) -> IdeationSession:
    """Convert dict to IdeationSession."""
    return IdeationSession(
        id=data["id"],
        project_name=data["project_name"],
        user_id=data["user_id"],
        status=ProjectStatus(data["status"]),
        data_source=DataSource(data["data_source"]),
        version=data["version"],
        created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=datetime.fromisoformat(data["updated_at"]),
    )


class RedisSessionRepository(ISessionRepository):
    """Redis implementation of session repository.

    Stores sessions as JSON in Redis keys with the pattern:
    - `ideation:session:{session_id}` - Session JSON data
    - `ideation:user_sessions:{user_id}` - Set of session IDs for user

    Args:
        redis_client: Async Redis client instance.
    """

    def __init__(self, redis_client: redis.Redis) -> None:
        """Initialize repository with Redis client.

        Args:
            redis_client: Async Redis client for storage operations.
        """
        self._redis = redis_client

    async def create(self, session: IdeationSession) -> IdeationSession:
        """Create a new session in Redis.

        Args:
            session: The session to create.

        Returns:
            The created session.
        """
        key = f"{SESSION_KEY_PREFIX}{session.id}"
        data = _session_to_dict(session)
        await self._redis.set(key, json.dumps(data))

        # Add to user's session index
        user_key = f"{USER_SESSIONS_KEY_PREFIX}{session.user_id}"
        await self._redis.sadd(user_key, session.id)

        return session

    async def get_by_id(self, session_id: str) -> IdeationSession | None:
        """Get session by ID from Redis.

        Args:
            session_id: The session ID to look up.

        Returns:
            The session if found, None otherwise.
        """
        key = f"{SESSION_KEY_PREFIX}{session_id}"
        data = await self._redis.get(key)

        if data is None:
            return None

        return _dict_to_session(json.loads(data))

    async def update(self, session: IdeationSession) -> None:
        """Update an existing session in Redis.

        Args:
            session: The session with updated values.
        """
        key = f"{SESSION_KEY_PREFIX}{session.id}"
        data = _session_to_dict(session)
        await self._redis.set(key, json.dumps(data))

    async def delete(self, session_id: str) -> None:
        """Delete session from Redis.

        Also removes from user index and related data.

        Args:
            session_id: The ID of the session to delete.
        """
        # Get session to find user_id for index cleanup
        session = await self.get_by_id(session_id)
        if session:
            user_key = f"{USER_SESSIONS_KEY_PREFIX}{session.user_id}"
            await self._redis.srem(user_key, session_id)

        # Delete session data
        key = f"{SESSION_KEY_PREFIX}{session_id}"
        await self._redis.delete(key)

        # Delete related data (messages, requirements, maturity, prd, stories)
        await self._redis.delete(f"ideation:messages:{session_id}")
        await self._redis.delete(f"ideation:requirements:{session_id}")
        await self._redis.delete(f"ideation:maturity:{session_id}")
        await self._redis.delete(f"ideation:prd:{session_id}")
        await self._redis.delete(f"ideation:stories:{session_id}")

    async def list_by_user(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> list[IdeationSession]:
        """List sessions for a user from Redis.

        Args:
            user_id: The user ID to filter by.
            limit: Maximum number of sessions to return.
            offset: Number of sessions to skip.

        Returns:
            List of sessions for the user, ordered by updated_at desc.
        """
        user_key = f"{USER_SESSIONS_KEY_PREFIX}{user_id}"
        session_ids = await self._redis.smembers(user_key)

        if not session_ids:
            return []

        # Fetch all sessions
        sessions = []
        for sid in session_ids:
            session = await self.get_by_id(sid.decode() if isinstance(sid, bytes) else sid)
            if session:
                sessions.append(session)

        # Sort by updated_at descending
        sessions.sort(key=lambda s: s.updated_at, reverse=True)

        # Apply pagination
        return sessions[offset : offset + limit]

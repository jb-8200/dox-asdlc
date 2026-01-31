"""Redis implementation of IMessageRepository.

This module provides the Redis-backed implementation for message
persistence operations using JSON serialization.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

from src.core.models.ideation import (
    ChatMessage,
    MessageRole,
)
from src.orchestrator.repositories.interfaces import IMessageRepository

if TYPE_CHECKING:
    import redis.asyncio as redis


# Redis key prefix
MESSAGES_KEY_PREFIX = "ideation:messages:"


def _message_to_dict(message: ChatMessage) -> dict[str, Any]:
    """Convert ChatMessage to JSON-serializable dict."""
    return {
        "id": message.id,
        "session_id": message.session_id,
        "role": message.role.value,
        "content": message.content,
        "timestamp": message.timestamp.isoformat(),
        "maturity_delta": message.maturity_delta,
        "metadata": message.metadata,
    }


def _dict_to_message(data: dict[str, Any]) -> ChatMessage:
    """Convert dict to ChatMessage."""
    return ChatMessage(
        id=data["id"],
        session_id=data["session_id"],
        role=MessageRole(data["role"]),
        content=data["content"],
        timestamp=datetime.fromisoformat(data["timestamp"]),
        maturity_delta=data.get("maturity_delta", 0),
        metadata=data.get("metadata"),
    )


class RedisMessageRepository(IMessageRepository):
    """Redis implementation of message repository.

    Stores messages as a JSON list in Redis with the key pattern:
    - `ideation:messages:{session_id}` - List of message JSONs

    Args:
        redis_client: Async Redis client instance.
    """

    def __init__(self, redis_client: redis.Redis) -> None:
        """Initialize repository with Redis client.

        Args:
            redis_client: Async Redis client for storage operations.
        """
        self._redis = redis_client

    async def create(self, message: ChatMessage) -> ChatMessage:
        """Create a new message in Redis list.

        Args:
            message: The message to create.

        Returns:
            The created message.
        """
        key = f"{MESSAGES_KEY_PREFIX}{message.session_id}"
        data = _message_to_dict(message)
        await self._redis.rpush(key, json.dumps(data))
        return message

    async def get_by_session(
        self, session_id: str, limit: int = 100, offset: int = 0
    ) -> list[ChatMessage]:
        """Get messages for session from Redis.

        Args:
            session_id: The session ID to filter by.
            limit: Maximum number of messages to return.
            offset: Number of messages to skip.

        Returns:
            List of messages for the session, ordered by timestamp asc.
        """
        key = f"{MESSAGES_KEY_PREFIX}{session_id}"

        # Get all messages (Redis LRANGE is 0-indexed, -1 means all)
        start = offset
        end = offset + limit - 1 if limit > 0 else -1

        raw_messages = await self._redis.lrange(key, start, end)

        messages = []
        for raw in raw_messages:
            data = json.loads(raw.decode() if isinstance(raw, bytes) else raw)
            messages.append(_dict_to_message(data))

        # Messages are already in order (appended chronologically)
        return messages

    async def delete_by_session(self, session_id: str) -> None:
        """Delete all messages for a session.

        Args:
            session_id: The session ID whose messages to delete.
        """
        key = f"{MESSAGES_KEY_PREFIX}{session_id}"
        await self._redis.delete(key)

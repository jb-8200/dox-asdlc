"""Redis implementation of IMaturityRepository.

This module provides the Redis-backed implementation for maturity state
persistence operations using JSON serialization.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

from src.core.models.ideation import (
    MaturityCategory,
    MaturityState,
)
from src.orchestrator.repositories.interfaces import IMaturityRepository

if TYPE_CHECKING:
    import redis.asyncio as redis


# Redis key prefix
MATURITY_KEY_PREFIX = "ideation:maturity:"


def _maturity_to_dict(maturity: MaturityState) -> dict[str, Any]:
    """Convert MaturityState to JSON-serializable dict."""
    return {
        "session_id": maturity.session_id,
        "score": maturity.score,
        "level": maturity.level,
        "categories": [
            {
                "id": cat.id,
                "name": cat.name,
                "score": cat.score,
                "required_for_submit": cat.required_for_submit,
            }
            for cat in maturity.categories
        ],
        "can_submit": maturity.can_submit,
        "gaps": maturity.gaps,
        "updated_at": maturity.updated_at.isoformat(),
    }


def _dict_to_maturity(data: dict[str, Any]) -> MaturityState:
    """Convert dict to MaturityState."""
    categories = [
        MaturityCategory(
            id=cat["id"],
            name=cat["name"],
            score=cat["score"],
            required_for_submit=cat["required_for_submit"],
        )
        for cat in data.get("categories", [])
    ]

    return MaturityState(
        session_id=data["session_id"],
        score=data["score"],
        level=data["level"],
        categories=categories,
        can_submit=data.get("can_submit", False),
        gaps=data.get("gaps", []),
        updated_at=datetime.fromisoformat(data["updated_at"]),
    )


class RedisMaturityRepository(IMaturityRepository):
    """Redis implementation of maturity repository.

    Stores maturity state as JSON in Redis with the key pattern:
    - `ideation:maturity:{session_id}` - Maturity state JSON

    Args:
        redis_client: Async Redis client instance.
    """

    def __init__(self, redis_client: redis.Redis) -> None:
        """Initialize repository with Redis client.

        Args:
            redis_client: Async Redis client for storage operations.
        """
        self._redis = redis_client

    async def save(self, maturity: MaturityState) -> None:
        """Save or update maturity state (upsert).

        Args:
            maturity: The maturity state to save.
        """
        key = f"{MATURITY_KEY_PREFIX}{maturity.session_id}"
        data = _maturity_to_dict(maturity)
        await self._redis.set(key, json.dumps(data))

    async def get_by_session(self, session_id: str) -> MaturityState | None:
        """Get maturity state for session.

        Args:
            session_id: The session ID to look up.

        Returns:
            The maturity state if found, None otherwise.
        """
        key = f"{MATURITY_KEY_PREFIX}{session_id}"
        raw_data = await self._redis.get(key)

        if raw_data is None:
            return None

        data = json.loads(raw_data.decode() if isinstance(raw_data, bytes) else raw_data)
        return _dict_to_maturity(data)

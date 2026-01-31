"""Redis implementation of IRequirementRepository.

This module provides the Redis-backed implementation for requirement
persistence operations using JSON serialization.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

from src.core.models.ideation import (
    ExtractedRequirement,
    RequirementPriority,
    RequirementType,
)
from src.orchestrator.repositories.interfaces import IRequirementRepository

if TYPE_CHECKING:
    import redis.asyncio as redis


# Redis key prefix
REQUIREMENTS_KEY_PREFIX = "ideation:requirements:"


def _requirement_to_dict(requirement: ExtractedRequirement) -> dict[str, Any]:
    """Convert ExtractedRequirement to JSON-serializable dict."""
    return {
        "id": requirement.id,
        "session_id": requirement.session_id,
        "description": requirement.description,
        "type": requirement.type.value,
        "priority": requirement.priority.value,
        "category_id": requirement.category_id,
        "created_at": requirement.created_at.isoformat(),
    }


def _dict_to_requirement(data: dict[str, Any]) -> ExtractedRequirement:
    """Convert dict to ExtractedRequirement."""
    return ExtractedRequirement(
        id=data["id"],
        session_id=data["session_id"],
        description=data["description"],
        type=RequirementType(data["type"]),
        priority=RequirementPriority(data["priority"]),
        category_id=data.get("category_id"),
        created_at=datetime.fromisoformat(data["created_at"]),
    )


class RedisRequirementRepository(IRequirementRepository):
    """Redis implementation of requirement repository.

    Stores requirements as a hash in Redis with the key pattern:
    - `ideation:requirements:{session_id}` - Hash of requirement_id -> JSON

    Args:
        redis_client: Async Redis client instance.
    """

    def __init__(self, redis_client: redis.Redis) -> None:
        """Initialize repository with Redis client.

        Args:
            redis_client: Async Redis client for storage operations.
        """
        self._redis = redis_client

    async def create(self, requirement: ExtractedRequirement) -> ExtractedRequirement:
        """Create a new requirement in Redis.

        Args:
            requirement: The requirement to create.

        Returns:
            The created requirement.
        """
        key = f"{REQUIREMENTS_KEY_PREFIX}{requirement.session_id}"
        data = _requirement_to_dict(requirement)
        await self._redis.hset(key, requirement.id, json.dumps(data))
        return requirement

    async def get_by_session(self, session_id: str) -> list[ExtractedRequirement]:
        """Get all requirements for a session.

        Args:
            session_id: The session ID to filter by.

        Returns:
            List of requirements for the session.
        """
        key = f"{REQUIREMENTS_KEY_PREFIX}{session_id}"
        raw_data = await self._redis.hgetall(key)

        if not raw_data:
            return []

        requirements = []
        for _req_id, raw_json in raw_data.items():
            json_str = raw_json.decode() if isinstance(raw_json, bytes) else raw_json
            data = json.loads(json_str)
            requirements.append(_dict_to_requirement(data))

        # Sort by created_at for consistent ordering
        requirements.sort(key=lambda r: r.created_at)
        return requirements

    async def update(self, requirement: ExtractedRequirement) -> None:
        """Update an existing requirement.

        Args:
            requirement: The requirement with updated values.
        """
        key = f"{REQUIREMENTS_KEY_PREFIX}{requirement.session_id}"
        data = _requirement_to_dict(requirement)
        await self._redis.hset(key, requirement.id, json.dumps(data))

    async def delete(self, requirement_id: str) -> None:
        """Delete a requirement by ID.

        Note: This requires scanning all session keys to find the requirement.
        For better performance, consider storing a reverse index.

        Args:
            requirement_id: The ID of the requirement to delete.
        """
        # Scan all requirement keys to find which session this belongs to
        # In practice, the service layer should know the session_id
        cursor = 0
        while True:
            cursor, keys = await self._redis.scan(
                cursor, match=f"{REQUIREMENTS_KEY_PREFIX}*"
            )
            for key in keys:
                key_str = key.decode() if isinstance(key, bytes) else key
                # Check if this requirement exists in this hash
                exists = await self._redis.hexists(key_str, requirement_id)
                if exists:
                    await self._redis.hdel(key_str, requirement_id)
                    return
            if cursor == 0:
                break

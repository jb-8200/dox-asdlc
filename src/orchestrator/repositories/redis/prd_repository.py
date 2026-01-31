"""Redis implementation of IPRDRepository.

This module provides the Redis-backed implementation for PRD draft
and user story persistence operations using JSON serialization.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

from src.core.models.ideation import (
    PRDDraft,
    PRDSection,
    RequirementPriority,
    UserStory,
)
from src.orchestrator.repositories.interfaces import IPRDRepository

if TYPE_CHECKING:
    import redis.asyncio as redis


# Redis key prefixes
PRD_KEY_PREFIX = "ideation:prd:"
STORIES_KEY_PREFIX = "ideation:stories:"


def _prd_to_dict(draft: PRDDraft) -> dict[str, Any]:
    """Convert PRDDraft to JSON-serializable dict."""
    return {
        "id": draft.id,
        "session_id": draft.session_id,
        "title": draft.title,
        "version": draft.version,
        "sections": [
            {
                "id": section.id,
                "heading": section.heading,
                "content": section.content,
                "order": section.order,
            }
            for section in draft.sections
        ],
        "status": draft.status,
        "created_at": draft.created_at.isoformat(),
    }


def _dict_to_prd(data: dict[str, Any]) -> PRDDraft:
    """Convert dict to PRDDraft."""
    sections = [
        PRDSection(
            id=s["id"],
            heading=s["heading"],
            content=s["content"],
            order=s["order"],
        )
        for s in data.get("sections", [])
    ]

    return PRDDraft(
        id=data["id"],
        session_id=data["session_id"],
        title=data["title"],
        version=data["version"],
        sections=sections,
        status=data.get("status", "draft"),
        created_at=datetime.fromisoformat(data["created_at"]),
    )


def _story_to_dict(story: UserStory) -> dict[str, Any]:
    """Convert UserStory to JSON-serializable dict."""
    return {
        "id": story.id,
        "session_id": story.session_id,
        "title": story.title,
        "as_a": story.as_a,
        "i_want": story.i_want,
        "so_that": story.so_that,
        "acceptance_criteria": story.acceptance_criteria,
        "linked_requirements": story.linked_requirements,
        "priority": story.priority.value,
        "created_at": story.created_at.isoformat(),
    }


def _dict_to_story(data: dict[str, Any]) -> UserStory:
    """Convert dict to UserStory."""
    return UserStory(
        id=data["id"],
        session_id=data["session_id"],
        title=data["title"],
        as_a=data["as_a"],
        i_want=data["i_want"],
        so_that=data["so_that"],
        acceptance_criteria=data.get("acceptance_criteria", []),
        linked_requirements=data.get("linked_requirements", []),
        priority=RequirementPriority(data.get("priority", "should_have")),
        created_at=datetime.fromisoformat(data["created_at"]),
    )


class RedisPRDRepository(IPRDRepository):
    """Redis implementation of PRD repository.

    Stores PRD drafts and user stories in Redis with the key patterns:
    - `ideation:prd:{session_id}` - PRD draft JSON
    - `ideation:stories:{session_id}` - List of user story JSONs

    Args:
        redis_client: Async Redis client instance.
    """

    def __init__(self, redis_client: redis.Redis) -> None:
        """Initialize repository with Redis client.

        Args:
            redis_client: Async Redis client for storage operations.
        """
        self._redis = redis_client

    async def save_draft(self, draft: PRDDraft) -> PRDDraft:
        """Save a PRD draft to Redis.

        Args:
            draft: The PRD draft to save.

        Returns:
            The saved PRD draft.
        """
        key = f"{PRD_KEY_PREFIX}{draft.session_id}"
        data = _prd_to_dict(draft)
        await self._redis.set(key, json.dumps(data))
        return draft

    async def get_draft(self, session_id: str) -> PRDDraft | None:
        """Get latest PRD draft for session.

        Args:
            session_id: The session ID to look up.

        Returns:
            The PRD draft if found, None otherwise.
        """
        key = f"{PRD_KEY_PREFIX}{session_id}"
        raw_data = await self._redis.get(key)

        if raw_data is None:
            return None

        data = json.loads(raw_data.decode() if isinstance(raw_data, bytes) else raw_data)
        return _dict_to_prd(data)

    async def save_user_stories(
        self, session_id: str, stories: list[UserStory]
    ) -> None:
        """Save user stories for session.

        Replaces any existing stories for the session.

        Args:
            session_id: The session ID to associate stories with.
            stories: List of user stories to save.
        """
        key = f"{STORIES_KEY_PREFIX}{session_id}"

        # Delete existing stories
        await self._redis.delete(key)

        # Add new stories
        if stories:
            story_jsons = [json.dumps(_story_to_dict(s)) for s in stories]
            await self._redis.rpush(key, *story_jsons)

    async def get_user_stories(self, session_id: str) -> list[UserStory]:
        """Get user stories for session.

        Args:
            session_id: The session ID to look up.

        Returns:
            List of user stories for the session.
        """
        key = f"{STORIES_KEY_PREFIX}{session_id}"
        raw_stories = await self._redis.lrange(key, 0, -1)

        if not raw_stories:
            return []

        stories = []
        for raw in raw_stories:
            data = json.loads(raw.decode() if isinstance(raw, bytes) else raw)
            stories.append(_dict_to_story(data))

        return stories

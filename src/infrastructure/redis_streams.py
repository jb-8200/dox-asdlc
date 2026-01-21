"""Redis Streams management for aSDLC event coordination.

Provides consumer group initialization and stream operations
as defined in System_Design.md Section 6.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import redis.asyncio as redis

from src.core.config import RedisConfig, get_redis_config
from src.core.exceptions import ConsumerGroupError, StreamError
from src.core.redis_client import get_redis_client

logger = logging.getLogger(__name__)


@dataclass
class StreamEvent:
    """Represents an event from the aSDLC event stream."""

    event_id: str
    event_type: str
    session_id: str
    epic_id: str | None
    task_id: str | None
    git_sha: str | None
    artifact_paths: list[str]
    mode: str
    timestamp: str
    raw_data: dict[str, Any]

    @classmethod
    def from_stream_entry(
        cls, event_id: str, data: dict[str, Any]
    ) -> StreamEvent:
        """Create StreamEvent from Redis stream entry."""
        artifact_paths = data.get("artifact_paths", "")
        if isinstance(artifact_paths, str):
            artifact_paths = (
                artifact_paths.split(",") if artifact_paths else []
            )

        return cls(
            event_id=event_id,
            event_type=data.get("event_type", "unknown"),
            session_id=data.get("session_id", ""),
            epic_id=data.get("epic_id"),
            task_id=data.get("task_id"),
            git_sha=data.get("git_sha"),
            artifact_paths=artifact_paths,
            mode=data.get("mode", "normal"),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            raw_data=data,
        )


async def ensure_stream_exists(
    client: redis.Redis | None = None,
    stream_name: str | None = None,
) -> bool:
    """Ensure the event stream exists.

    Creates the stream if it doesn't exist by adding a placeholder message.

    Args:
        client: Redis client. Creates one if not provided.
        stream_name: Stream name. Uses config default if not provided.

    Returns:
        bool: True if stream exists or was created.

    Raises:
        StreamError: If stream creation fails.
    """
    if client is None:
        client = await get_redis_client()

    if stream_name is None:
        config = get_redis_config()
        stream_name = config.stream_name

    try:
        # Check if stream exists
        exists = await client.exists(stream_name)
        if exists:
            logger.debug(f"Stream {stream_name} already exists")
            return True

        # Create stream with initial placeholder
        # This will be trimmed when real events are added
        await client.xadd(
            stream_name,
            {"_init": "true", "timestamp": datetime.utcnow().isoformat()},
            maxlen=1000,
        )
        logger.info(f"Created stream: {stream_name}")
        return True
    except redis.RedisError as e:
        raise StreamError(
            f"Failed to ensure stream exists: {e}",
            details={"stream": stream_name},
        ) from e


async def create_consumer_group(
    client: redis.Redis,
    stream_name: str,
    group_name: str,
    start_id: str = "0",
) -> bool:
    """Create a consumer group for the stream.

    Args:
        client: Redis client.
        stream_name: Name of the stream.
        group_name: Name of the consumer group.
        start_id: ID to start reading from. "0" for beginning, "$" for new only.

    Returns:
        bool: True if group was created, False if it already exists.

    Raises:
        ConsumerGroupError: If group creation fails.
    """
    try:
        await client.xgroup_create(
            stream_name, group_name, id=start_id, mkstream=True
        )
        logger.info(f"Created consumer group: {group_name} for {stream_name}")
        return True
    except redis.ResponseError as e:
        if "BUSYGROUP" in str(e):
            # Group already exists
            logger.debug(
                f"Consumer group {group_name} already exists for {stream_name}"
            )
            return False
        raise ConsumerGroupError(
            f"Failed to create consumer group: {e}",
            details={"stream": stream_name, "group": group_name},
        ) from e
    except redis.RedisError as e:
        raise ConsumerGroupError(
            f"Redis error creating consumer group: {e}",
            details={"stream": stream_name, "group": group_name},
        ) from e


async def initialize_consumer_groups(
    client: redis.Redis | None = None,
    config: RedisConfig | None = None,
) -> dict[str, bool]:
    """Initialize all consumer groups defined in configuration.

    Creates the event stream and all consumer groups from config.
    Idempotent - safe to call multiple times.

    Args:
        client: Redis client. Creates one if not provided.
        config: Redis configuration. Uses environment config if not provided.

    Returns:
        dict: Mapping of group names to creation status (True=created, False=existed).

    Raises:
        ConsumerGroupError: If initialization fails.
    """
    if client is None:
        client = await get_redis_client()

    if config is None:
        config = get_redis_config()

    # Ensure stream exists first
    await ensure_stream_exists(client, config.stream_name)

    results = {}
    for group_name in config.consumer_groups:
        try:
            created = await create_consumer_group(
                client, config.stream_name, group_name
            )
            results[group_name] = created
        except ConsumerGroupError:
            logger.error(f"Failed to create consumer group: {group_name}")
            raise

    return results


async def get_stream_info(
    client: redis.Redis | None = None,
    stream_name: str | None = None,
) -> dict[str, Any]:
    """Get information about the event stream.

    Args:
        client: Redis client. Creates one if not provided.
        stream_name: Stream name. Uses config default if not provided.

    Returns:
        dict: Stream information including length, groups, and consumers.
    """
    if client is None:
        client = await get_redis_client()

    if stream_name is None:
        config = get_redis_config()
        stream_name = config.stream_name

    try:
        info = await client.xinfo_stream(stream_name)
        groups_info = await client.xinfo_groups(stream_name)

        return {
            "stream": stream_name,
            "length": info.get("length", 0),
            "first_entry": info.get("first-entry"),
            "last_entry": info.get("last-entry"),
            "groups": [
                {
                    "name": g.get("name"),
                    "consumers": g.get("consumers", 0),
                    "pending": g.get("pending", 0),
                    "last_delivered": g.get("last-delivered-id"),
                }
                for g in groups_info
            ],
        }
    except redis.ResponseError as e:
        if "no such key" in str(e).lower():
            return {
                "stream": stream_name,
                "length": 0,
                "exists": False,
                "groups": [],
            }
        raise StreamError(
            f"Failed to get stream info: {e}",
            details={"stream": stream_name},
        ) from e


async def publish_event(
    client: redis.Redis | None = None,
    event_type: str = "",
    session_id: str = "",
    epic_id: str | None = None,
    task_id: str | None = None,
    git_sha: str | None = None,
    artifact_paths: list[str] | None = None,
    mode: str = "normal",
    stream_name: str | None = None,
    **extra_fields,
) -> str:
    """Publish an event to the event stream.

    Args:
        client: Redis client. Creates one if not provided.
        event_type: Type of event (e.g., "task_created", "gate_requested").
        session_id: Session identifier.
        epic_id: Optional epic identifier.
        task_id: Optional task identifier.
        git_sha: Optional Git SHA reference.
        artifact_paths: Optional list of artifact paths.
        mode: Event mode ("normal" or "rlm").
        stream_name: Stream name. Uses config default if not provided.
        **extra_fields: Additional fields to include in the event.

    Returns:
        str: The event ID assigned by Redis.

    Raises:
        StreamError: If publishing fails.
    """
    if client is None:
        client = await get_redis_client()

    if stream_name is None:
        config = get_redis_config()
        stream_name = config.stream_name

    event_data = {
        "event_type": event_type,
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "mode": mode,
    }

    if epic_id:
        event_data["epic_id"] = epic_id
    if task_id:
        event_data["task_id"] = task_id
    if git_sha:
        event_data["git_sha"] = git_sha
    if artifact_paths:
        event_data["artifact_paths"] = ",".join(artifact_paths)

    # Add any extra fields
    event_data.update(extra_fields)

    try:
        event_id = await client.xadd(stream_name, event_data, maxlen=10000)
        logger.debug(f"Published event {event_id}: {event_type}")
        return event_id
    except redis.RedisError as e:
        raise StreamError(
            f"Failed to publish event: {e}",
            details={"event_type": event_type, "stream": stream_name},
        ) from e

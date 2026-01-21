"""Integration tests for Redis streams module.

Tests stream operations with mocked Redis client.
Full integration tests with real Redis require Docker.
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestStreamEvent:
    """Tests for StreamEvent dataclass."""

    def test_from_stream_entry(self) -> None:
        """Test creating StreamEvent from stream entry."""
        from src.infrastructure.redis_streams import StreamEvent

        event_id = "1234567890-0"
        data = {
            "event_type": "task_created",
            "session_id": "session-123",
            "epic_id": "epic-1",
            "task_id": "task-1",
            "git_sha": "abc123",
            "artifact_paths": "path/1,path/2",
            "mode": "normal",
            "timestamp": "2026-01-21T00:00:00",
        }

        event = StreamEvent.from_stream_entry(event_id, data)

        assert event.event_id == event_id
        assert event.event_type == "task_created"
        assert event.session_id == "session-123"
        assert event.epic_id == "epic-1"
        assert event.task_id == "task-1"
        assert event.git_sha == "abc123"
        assert event.artifact_paths == ["path/1", "path/2"]
        assert event.mode == "normal"

    def test_from_stream_entry_with_defaults(self) -> None:
        """Test creating StreamEvent with missing fields."""
        from src.infrastructure.redis_streams import StreamEvent

        event = StreamEvent.from_stream_entry("1234-0", {})

        assert event.event_type == "unknown"
        assert event.session_id == ""
        assert event.epic_id is None
        assert event.artifact_paths == []
        assert event.mode == "normal"


class TestEnsureStreamExists:
    """Tests for ensure_stream_exists function."""

    @pytest.mark.asyncio
    async def test_stream_exists(self) -> None:
        """Test when stream already exists."""
        from src.infrastructure.redis_streams import ensure_stream_exists

        mock_client = AsyncMock()
        mock_client.exists.return_value = True

        result = await ensure_stream_exists(
            mock_client, "test:stream"
        )

        assert result is True
        mock_client.exists.assert_called_once_with("test:stream")
        mock_client.xadd.assert_not_called()

    @pytest.mark.asyncio
    async def test_stream_created(self) -> None:
        """Test when stream needs to be created."""
        from src.infrastructure.redis_streams import ensure_stream_exists

        mock_client = AsyncMock()
        mock_client.exists.return_value = False

        result = await ensure_stream_exists(
            mock_client, "test:stream"
        )

        assert result is True
        mock_client.xadd.assert_called_once()


class TestCreateConsumerGroup:
    """Tests for create_consumer_group function."""

    @pytest.mark.asyncio
    async def test_group_created(self) -> None:
        """Test creating a new consumer group."""
        from src.infrastructure.redis_streams import create_consumer_group

        mock_client = AsyncMock()

        result = await create_consumer_group(
            mock_client, "test:stream", "test-group"
        )

        assert result is True
        mock_client.xgroup_create.assert_called_once_with(
            "test:stream", "test-group", id="0", mkstream=True
        )

    @pytest.mark.asyncio
    async def test_group_already_exists(self) -> None:
        """Test when consumer group already exists."""
        import redis.asyncio as redis

        from src.infrastructure.redis_streams import create_consumer_group

        mock_client = AsyncMock()
        mock_client.xgroup_create.side_effect = redis.ResponseError(
            "BUSYGROUP Consumer Group name already exists"
        )

        result = await create_consumer_group(
            mock_client, "test:stream", "test-group"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_group_creation_error(self) -> None:
        """Test when consumer group creation fails."""
        import redis.asyncio as redis

        from src.core.exceptions import ConsumerGroupError
        from src.infrastructure.redis_streams import create_consumer_group

        mock_client = AsyncMock()
        mock_client.xgroup_create.side_effect = redis.ResponseError(
            "Some other error"
        )

        with pytest.raises(ConsumerGroupError):
            await create_consumer_group(
                mock_client, "test:stream", "test-group"
            )


class TestInitializeConsumerGroups:
    """Tests for initialize_consumer_groups function."""

    @pytest.mark.asyncio
    async def test_all_groups_initialized(self) -> None:
        """Test initializing all consumer groups."""
        from src.core.config import RedisConfig
        from src.infrastructure.redis_streams import initialize_consumer_groups

        mock_client = AsyncMock()
        mock_client.exists.return_value = True

        config = RedisConfig(
            stream_name="test:events",
            consumer_groups=("group-a", "group-b"),
        )

        with patch(
            "src.infrastructure.redis_streams.get_redis_client",
            return_value=mock_client,
        ):
            results = await initialize_consumer_groups(mock_client, config)

        assert len(results) == 2
        assert "group-a" in results
        assert "group-b" in results


class TestGetStreamInfo:
    """Tests for get_stream_info function."""

    @pytest.mark.asyncio
    async def test_stream_info_returned(self) -> None:
        """Test getting stream information."""
        from src.infrastructure.redis_streams import get_stream_info

        mock_client = AsyncMock()
        mock_client.xinfo_stream.return_value = {
            "length": 100,
            "first-entry": ("1234-0", {}),
            "last-entry": ("5678-0", {}),
        }
        mock_client.xinfo_groups.return_value = [
            {
                "name": "test-group",
                "consumers": 2,
                "pending": 5,
                "last-delivered-id": "5000-0",
            }
        ]

        info = await get_stream_info(mock_client, "test:stream")

        assert info["stream"] == "test:stream"
        assert info["length"] == 100
        assert len(info["groups"]) == 1
        assert info["groups"][0]["name"] == "test-group"

    @pytest.mark.asyncio
    async def test_stream_not_exists(self) -> None:
        """Test when stream does not exist."""
        import redis.asyncio as redis

        from src.infrastructure.redis_streams import get_stream_info

        mock_client = AsyncMock()
        mock_client.xinfo_stream.side_effect = redis.ResponseError(
            "no such key"
        )

        info = await get_stream_info(mock_client, "test:stream")

        assert info["stream"] == "test:stream"
        assert info["length"] == 0
        assert info["exists"] is False


class TestPublishEvent:
    """Tests for publish_event function."""

    @pytest.mark.asyncio
    async def test_publish_event_success(self) -> None:
        """Test publishing an event to the stream."""
        from src.infrastructure.redis_streams import publish_event

        mock_client = AsyncMock()
        mock_client.xadd.return_value = "1234567890-0"

        with patch.dict(os.environ, {"REDIS_HOST": "localhost"}):
            from src.core.config import clear_config_cache

            clear_config_cache()

            event_id = await publish_event(
                client=mock_client,
                event_type="task_created",
                session_id="session-123",
                epic_id="epic-1",
                task_id="task-1",
                stream_name="test:events",
            )

        assert event_id == "1234567890-0"
        mock_client.xadd.assert_called_once()

        # Verify event data
        call_args = mock_client.xadd.call_args
        event_data = call_args.args[1]
        assert event_data["event_type"] == "task_created"
        assert event_data["session_id"] == "session-123"
        assert event_data["epic_id"] == "epic-1"
        assert event_data["task_id"] == "task-1"
        assert "timestamp" in event_data

    @pytest.mark.asyncio
    async def test_publish_event_with_artifacts(self) -> None:
        """Test publishing event with artifact paths."""
        from src.infrastructure.redis_streams import publish_event

        mock_client = AsyncMock()
        mock_client.xadd.return_value = "1234-0"

        await publish_event(
            client=mock_client,
            event_type="test",
            session_id="test",
            artifact_paths=["path/1", "path/2"],
            stream_name="test:events",
        )

        call_args = mock_client.xadd.call_args
        event_data = call_args.args[1]
        assert event_data["artifact_paths"] == "path/1,path/2"

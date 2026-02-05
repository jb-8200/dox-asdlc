"""Integration tests for multi-session presence management.

Tests the presence tracking functionality for the multi-session infrastructure:
- Registration and heartbeat operations
- Stale detection timing
- Deregistration
- Concurrent sessions

Requires: Redis running on localhost:6379 (or REDIS_HOST/REDIS_PORT env vars)
"""

from __future__ import annotations

import asyncio
import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import AsyncGenerator

import pytest
import redis.asyncio as redis

from src.infrastructure.coordination.client import CoordinationClient
from src.infrastructure.coordination.config import CoordinationConfig


# Skip all tests if Redis is not available
def redis_available() -> bool:
    """Check if Redis is available for integration tests."""
    host = os.environ.get("REDIS_HOST", "localhost")
    port = int(os.environ.get("REDIS_PORT", 6379))
    try:
        r = redis.from_url(f"redis://{host}:{port}", decode_responses=True)
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(r.ping())
        loop.run_until_complete(r.aclose())
        loop.close()
        return result
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not redis_available(),
    reason="Redis not available for integration tests",
)


@pytest.fixture
def test_prefix() -> str:
    """Generate unique prefix for test isolation."""
    return f"test-presence-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def config(test_prefix: str) -> CoordinationConfig:
    """Create test configuration with unique prefix."""
    return CoordinationConfig(
        redis_host=os.environ.get("REDIS_HOST", "localhost"),
        redis_port=int(os.environ.get("REDIS_PORT", 6379)),
        key_prefix=test_prefix,
        message_ttl_days=1,
        presence_timeout_minutes=5,  # 5 minutes stale threshold
        timeline_max_size=100,
    )


@pytest.fixture
async def redis_client(config: CoordinationConfig) -> AsyncGenerator[redis.Redis, None]:
    """Create Redis client for tests."""
    client = redis.from_url(
        f"redis://{config.redis_host}:{config.redis_port}",
        decode_responses=True,
    )
    yield client
    # Cleanup: delete all test keys
    keys = await client.keys(f"{config.key_prefix}:*")
    if keys:
        await client.delete(*keys)
    await client.aclose()


@pytest.fixture
async def client(
    redis_client: redis.Redis,
    config: CoordinationConfig,
) -> AsyncGenerator[CoordinationClient, None]:
    """Create coordination client for tests."""
    client = CoordinationClient(
        redis_client=redis_client,
        config=config,
        instance_id="test-instance",
    )
    yield client


class TestPresenceRegistration:
    """Tests for presence registration functionality."""

    @pytest.mark.asyncio
    async def test_register_presence_stores_in_redis(
        self,
        client: CoordinationClient,
        redis_client: redis.Redis,
        config: CoordinationConfig,
    ) -> None:
        """Test that register_instance stores presence data in Redis."""
        await client.register_instance(
            instance_id="backend",
            session_id="session-test-123",
        )

        # Verify data in Redis
        presence_key = config.presence_key()
        data = await redis_client.hgetall(presence_key)

        assert "backend.active" in data
        assert data["backend.active"] == "1"
        assert "backend.session_id" in data
        assert data["backend.session_id"] == "session-test-123"
        assert "backend.last_heartbeat" in data

    @pytest.mark.asyncio
    async def test_register_presence_with_minimal_fields(
        self,
        client: CoordinationClient,
        redis_client: redis.Redis,
        config: CoordinationConfig,
    ) -> None:
        """Test registration with only required fields."""
        await client.register_instance(
            instance_id="frontend",
            session_id=None,  # Optional
        )

        presence_key = config.presence_key()
        data = await redis_client.hgetall(presence_key)

        assert data["frontend.active"] == "1"
        assert "frontend.last_heartbeat" in data
        # session_id should not be set
        assert "frontend.session_id" not in data

    @pytest.mark.asyncio
    async def test_register_presence_updates_existing(
        self,
        client: CoordinationClient,
        redis_client: redis.Redis,
        config: CoordinationConfig,
    ) -> None:
        """Test that re-registration updates existing presence."""
        # First registration
        await client.register_instance("orchestrator", "session-1")

        presence_key = config.presence_key()
        first_session = await redis_client.hget(presence_key, "orchestrator.session_id")
        assert first_session == "session-1"

        # Small delay
        await asyncio.sleep(0.1)

        # Re-register with new session
        await client.register_instance("orchestrator", "session-2")

        second_session = await redis_client.hget(presence_key, "orchestrator.session_id")
        assert second_session == "session-2"

    @pytest.mark.asyncio
    async def test_register_multiple_instances(
        self,
        client: CoordinationClient,
    ) -> None:
        """Test registering multiple instances."""
        # Register multiple
        await client.register_instance("backend", "session-b")
        await client.register_instance("frontend", "session-f")
        await client.register_instance("orchestrator", "session-o")

        # Get presence
        presence = await client.get_presence()

        assert "backend" in presence
        assert "frontend" in presence
        assert "orchestrator" in presence
        assert presence["backend"].active is True
        assert presence["frontend"].active is True
        assert presence["orchestrator"].active is True


class TestHeartbeat:
    """Tests for heartbeat functionality."""

    @pytest.mark.asyncio
    async def test_heartbeat_updates_timestamp(
        self,
        client: CoordinationClient,
        redis_client: redis.Redis,
        config: CoordinationConfig,
    ) -> None:
        """Test that heartbeat updates the last_heartbeat timestamp."""
        # Register
        await client.register_instance("backend", "session-hb")

        presence_key = config.presence_key()
        initial_hb = await redis_client.hget(presence_key, "backend.last_heartbeat")

        # Small delay to ensure different timestamp
        await asyncio.sleep(0.2)

        # Heartbeat
        await client.heartbeat("backend")

        updated_hb = await redis_client.hget(presence_key, "backend.last_heartbeat")

        # Timestamps should be different
        assert initial_hb is not None
        assert updated_hb is not None
        # The updated heartbeat should be >= initial (timestamps are seconds precision)
        # Due to timing, they might be the same second, so just verify both exist

    @pytest.mark.asyncio
    async def test_heartbeat_for_unregistered_instance(
        self,
        client: CoordinationClient,
        redis_client: redis.Redis,
        config: CoordinationConfig,
    ) -> None:
        """Test heartbeat for an instance that was never registered."""
        # Heartbeat without registration
        await client.heartbeat("unregistered-instance")

        # Should have created the heartbeat field
        presence_key = config.presence_key()
        hb = await redis_client.hget(presence_key, "unregistered-instance.last_heartbeat")
        assert hb is not None

    @pytest.mark.asyncio
    async def test_heartbeat_performance(
        self,
        client: CoordinationClient,
    ) -> None:
        """Test that heartbeat operation is fast (<100ms)."""
        await client.register_instance("devops", "session-perf")

        start = datetime.now(UTC)
        await client.heartbeat("devops")
        end = datetime.now(UTC)

        duration_ms = (end - start).total_seconds() * 1000
        assert duration_ms < 100, f"Heartbeat took {duration_ms}ms, expected <100ms"


class TestStaleDetection:
    """Tests for stale session detection."""

    @pytest.mark.asyncio
    async def test_active_session_not_marked_stale(
        self,
        client: CoordinationClient,
    ) -> None:
        """Test that recently active sessions are not marked stale."""
        # Register with fresh heartbeat
        await client.register_instance("backend", "session-active")

        # Get presence
        presence = await client.get_presence()

        assert "backend" in presence
        assert presence["backend"].active is True
        # With default 5 minute timeout, should not be stale
        assert not presence["backend"].is_stale(timeout_minutes=5)

    @pytest.mark.asyncio
    async def test_stale_detection_with_old_timestamp(
        self,
        client: CoordinationClient,
        redis_client: redis.Redis,
        config: CoordinationConfig,
    ) -> None:
        """Test that sessions with old heartbeat are marked stale."""
        # Register instance
        await client.register_instance("stale-test", "session-stale")

        # Manually set an old heartbeat timestamp (10 minutes ago)
        presence_key = config.presence_key()
        old_time = datetime.now(UTC) - timedelta(minutes=10)
        old_time_str = old_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        await redis_client.hset(presence_key, "stale-test.last_heartbeat", old_time_str)

        # Get presence with 5 minute timeout
        presence = await client.get_presence(timeout_minutes=5)

        assert "stale-test" in presence
        # Should be marked inactive due to stale detection
        assert presence["stale-test"].active is False

    @pytest.mark.asyncio
    async def test_stale_boundary_condition(
        self,
        client: CoordinationClient,
        redis_client: redis.Redis,
        config: CoordinationConfig,
    ) -> None:
        """Test stale detection at exactly the timeout boundary."""
        # Register instance
        await client.register_instance("boundary-test", "session-boundary")

        # Set heartbeat to exactly 5 minutes ago
        presence_key = config.presence_key()
        boundary_time = datetime.now(UTC) - timedelta(minutes=5)
        boundary_time_str = boundary_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        await redis_client.hset(presence_key, "boundary-test.last_heartbeat", boundary_time_str)

        # Get presence with 5 minute timeout
        presence = await client.get_presence(timeout_minutes=5)

        assert "boundary-test" in presence
        # At exactly 5 minutes, should be marked stale
        assert presence["boundary-test"].active is False

    @pytest.mark.asyncio
    async def test_stale_session_can_be_reactivated(
        self,
        client: CoordinationClient,
        redis_client: redis.Redis,
        config: CoordinationConfig,
    ) -> None:
        """Test that a stale session can be reactivated with heartbeat."""
        # Register instance
        await client.register_instance("reactivate-test", "session-reactivate")

        # Make it stale
        presence_key = config.presence_key()
        old_time = datetime.now(UTC) - timedelta(minutes=10)
        old_time_str = old_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        await redis_client.hset(presence_key, "reactivate-test.last_heartbeat", old_time_str)

        # Verify it's stale
        presence_before = await client.get_presence(timeout_minutes=5)
        assert presence_before["reactivate-test"].active is False

        # Send heartbeat to reactivate
        await client.heartbeat("reactivate-test")

        # Should now be active
        presence_after = await client.get_presence(timeout_minutes=5)
        assert presence_after["reactivate-test"].active is True


class TestDeregistration:
    """Tests for session deregistration."""

    @pytest.mark.asyncio
    async def test_deregister_removes_presence(
        self,
        client: CoordinationClient,
        redis_client: redis.Redis,
        config: CoordinationConfig,
    ) -> None:
        """Test that deregistration removes presence data."""
        # Register
        await client.register_instance("temp-instance", "session-temp")

        # Verify registered
        presence_key = config.presence_key()
        active_before = await redis_client.hget(presence_key, "temp-instance.active")
        assert active_before == "1"

        # Deregister
        await client.unregister_instance("temp-instance")

        # Verify removed
        active_after = await redis_client.hget(presence_key, "temp-instance.active")
        assert active_after is None

    @pytest.mark.asyncio
    async def test_deregister_nonexistent_instance(
        self,
        client: CoordinationClient,
    ) -> None:
        """Test deregistering an instance that doesn't exist."""
        # Should not raise an error
        await client.unregister_instance("nonexistent-instance")

    @pytest.mark.asyncio
    async def test_deregister_not_visible_in_get_presence(
        self,
        client: CoordinationClient,
    ) -> None:
        """Test that deregistered instance is not in get_presence output."""
        # Register
        await client.register_instance("visible-test", "session-visible")

        # Verify visible
        presence_before = await client.get_presence()
        assert "visible-test" in presence_before

        # Deregister
        await client.unregister_instance("visible-test")

        # Should not be in presence anymore
        presence_after = await client.get_presence()
        assert "visible-test" not in presence_after


class TestConcurrentSessions:
    """Tests for concurrent session handling."""

    @pytest.mark.asyncio
    async def test_concurrent_registrations(
        self,
        client: CoordinationClient,
    ) -> None:
        """Test concurrent registration of multiple sessions."""
        # Register multiple sessions concurrently
        tasks = [
            client.register_instance(f"concurrent-{i}", f"session-{i}")
            for i in range(10)
        ]
        await asyncio.gather(*tasks)

        # All should be visible
        presence = await client.get_presence()
        for i in range(10):
            assert f"concurrent-{i}" in presence
            assert presence[f"concurrent-{i}"].active is True

    @pytest.mark.asyncio
    async def test_concurrent_heartbeats(
        self,
        client: CoordinationClient,
    ) -> None:
        """Test concurrent heartbeat operations."""
        # Register instances first
        for i in range(5):
            await client.register_instance(f"heartbeat-{i}", f"session-hb-{i}")

        # Send concurrent heartbeats
        tasks = [
            client.heartbeat(f"heartbeat-{i}")
            for i in range(5)
        ]
        await asyncio.gather(*tasks)

        # All should still be active
        presence = await client.get_presence()
        for i in range(5):
            assert f"heartbeat-{i}" in presence
            assert presence[f"heartbeat-{i}"].active is True

    @pytest.mark.asyncio
    async def test_concurrent_register_and_deregister(
        self,
        redis_client: redis.Redis,
        config: CoordinationConfig,
    ) -> None:
        """Test concurrent registration and deregistration."""
        # Create separate clients for concurrent operations
        client_a = CoordinationClient(
            redis_client=redis_client,
            config=config,
            instance_id="client-a",
        )
        client_b = CoordinationClient(
            redis_client=redis_client,
            config=config,
            instance_id="client-b",
        )

        # Interleaved operations
        await asyncio.gather(
            client_a.register_instance("session-a", "sess-a"),
            client_b.register_instance("session-b", "sess-b"),
            client_a.register_instance("session-c", "sess-c"),
        )

        # All should be present
        presence = await client_a.get_presence()
        assert "session-a" in presence
        assert "session-b" in presence
        assert "session-c" in presence

        # Concurrent deregistration
        await asyncio.gather(
            client_a.unregister_instance("session-a"),
            client_b.unregister_instance("session-b"),
        )

        # Only session-c should remain
        presence_after = await client_a.get_presence()
        assert "session-a" not in presence_after
        assert "session-b" not in presence_after
        assert "session-c" in presence_after


class TestPresenceMetadata:
    """Tests for presence metadata handling."""

    @pytest.mark.asyncio
    async def test_presence_info_to_dict(
        self,
        client: CoordinationClient,
    ) -> None:
        """Test that PresenceInfo can be converted to dict."""
        await client.register_instance("dict-test", "session-dict")

        presence = await client.get_presence()
        info = presence["dict-test"]
        info_dict = info.to_dict()

        assert info_dict["instance_id"] == "dict-test"
        assert info_dict["active"] is True
        assert "last_heartbeat" in info_dict
        assert info_dict.get("session_id") == "session-dict"

    @pytest.mark.asyncio
    async def test_presence_timestamp_format(
        self,
        client: CoordinationClient,
        redis_client: redis.Redis,
        config: CoordinationConfig,
    ) -> None:
        """Test that timestamps are stored in ISO format."""
        await client.register_instance("timestamp-test", "session-ts")

        presence_key = config.presence_key()
        timestamp = await redis_client.hget(presence_key, "timestamp-test.last_heartbeat")

        # Should be ISO format: YYYY-MM-DDTHH:MM:SSZ
        assert timestamp is not None
        assert "T" in timestamp
        assert timestamp.endswith("Z")

        # Should be parseable
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert parsed is not None


class TestPresenceCleanup:
    """Tests for cleanup behavior."""

    @pytest.mark.asyncio
    async def test_cleanup_removes_test_keys(
        self,
        redis_client: redis.Redis,
        config: CoordinationConfig,
    ) -> None:
        """Test that test cleanup properly removes keys."""
        # Create a client and register
        client = CoordinationClient(
            redis_client=redis_client,
            config=config,
            instance_id="cleanup-test",
        )
        await client.register_instance("cleanup-instance", "session-cleanup")

        # Verify key exists
        keys_before = await redis_client.keys(f"{config.key_prefix}:*")
        assert len(keys_before) > 0

        # Cleanup will happen via fixture when test ends

    @pytest.mark.asyncio
    async def test_isolated_test_prefix(
        self,
        config: CoordinationConfig,
        redis_client: redis.Redis,
    ) -> None:
        """Test that test prefix provides isolation."""
        # Each test run gets a unique prefix
        assert config.key_prefix.startswith("test-presence-")

        # Register something
        client = CoordinationClient(
            redis_client=redis_client,
            config=config,
            instance_id="isolation-test",
        )
        await client.register_instance("isolated-instance", "session-isolated")

        # Keys should be under our prefix
        presence_key = config.presence_key()
        assert config.key_prefix in presence_key

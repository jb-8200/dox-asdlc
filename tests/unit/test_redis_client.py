"""Unit tests for Redis client factory.

Tests configuration loading and client creation.
Integration tests with real Redis are in tests/integration/.
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.config import RedisConfig, clear_config_cache
from src.core.exceptions import RedisConnectionError


class TestRedisConfig:
    """Tests for RedisConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = RedisConfig()
        assert config.host == "localhost"
        assert config.port == 6379
        assert config.db == 0
        assert config.password is None
        assert config.max_connections == 10
        assert config.stream_name == "asdlc:events"
        assert len(config.consumer_groups) == 6

    def test_from_env(self) -> None:
        """Test configuration from environment variables."""
        clear_config_cache()
        with patch.dict(
            os.environ,
            {
                "REDIS_HOST": "redis.example.com",
                "REDIS_PORT": "6380",
                "REDIS_DB": "1",
                "REDIS_PASSWORD": "secret",
                "REDIS_MAX_CONNECTIONS": "20",
            },
        ):
            config = RedisConfig.from_env()
            assert config.host == "redis.example.com"
            assert config.port == 6380
            assert config.db == 1
            assert config.password == "secret"
            assert config.max_connections == 20

    def test_consumer_groups_defined(self) -> None:
        """Test all required consumer groups are defined."""
        config = RedisConfig()
        expected_groups = {
            "discovery-handlers",
            "design-handlers",
            "development-handlers",
            "validation-handlers",
            "deployment-handlers",
            "hitl-handlers",
        }
        assert set(config.consumer_groups) == expected_groups

    def test_key_prefixes(self) -> None:
        """Test key prefix configuration."""
        config = RedisConfig()
        assert config.task_prefix == "asdlc:task:"
        assert config.session_prefix == "asdlc:session:"


class TestRedisClientModule:
    """Tests for redis_client module functions."""

    @pytest.fixture(autouse=True)
    def reset_globals(self) -> None:
        """Reset global state before each test."""
        import src.core.redis_client as redis_client_module

        redis_client_module._pool = None
        redis_client_module._client = None
        clear_config_cache()

    @pytest.mark.asyncio
    async def test_get_connection_pool_creates_pool(self) -> None:
        """Test connection pool creation."""
        with patch(
            "src.core.redis_client.ConnectionPool"
        ) as mock_pool_class:
            from src.core.redis_client import get_connection_pool

            mock_pool = MagicMock()
            mock_pool_class.return_value = mock_pool

            config = RedisConfig(host="testhost", port=6380)
            pool = await get_connection_pool(config)

            assert pool == mock_pool
            mock_pool_class.assert_called_once()
            call_kwargs = mock_pool_class.call_args.kwargs
            assert call_kwargs["host"] == "testhost"
            assert call_kwargs["port"] == 6380

    @pytest.mark.asyncio
    async def test_get_connection_pool_returns_singleton(self) -> None:
        """Test that connection pool is a singleton."""
        with patch(
            "src.core.redis_client.ConnectionPool"
        ) as mock_pool_class:
            from src.core.redis_client import get_connection_pool
            import src.core.redis_client as module

            mock_pool = MagicMock()
            mock_pool_class.return_value = mock_pool

            config = RedisConfig()
            pool1 = await get_connection_pool(config)
            pool2 = await get_connection_pool(config)

            assert pool1 is pool2
            assert mock_pool_class.call_count == 1

    @pytest.mark.asyncio
    async def test_ping_redis_returns_false_on_error(self) -> None:
        """Test ping_redis handles errors gracefully."""
        from src.core.redis_client import ping_redis

        mock_client = AsyncMock()
        mock_client.ping.side_effect = Exception("Connection refused")

        result = await ping_redis(mock_client)
        assert result is False

    @pytest.mark.asyncio
    async def test_ping_redis_returns_true_on_success(self) -> None:
        """Test ping_redis returns True on successful ping."""
        from src.core.redis_client import ping_redis

        mock_client = AsyncMock()
        mock_client.ping.return_value = True

        result = await ping_redis(mock_client)
        assert result is True

    @pytest.mark.asyncio
    async def test_check_redis_health_returns_healthy(self) -> None:
        """Test check_redis_health returns healthy status."""
        from src.core.redis_client import check_redis_health

        mock_client = AsyncMock()
        mock_client.ping.return_value = True
        mock_client.info.return_value = {"redis_version": "7.0.0"}

        with patch.dict(
            os.environ,
            {"REDIS_HOST": "testhost", "REDIS_PORT": "6379"},
        ):
            clear_config_cache()
            health = await check_redis_health(mock_client)

        assert health["status"] == "healthy"
        assert health["connected"] is True
        assert health["server_version"] == "7.0.0"

    @pytest.mark.asyncio
    async def test_check_redis_health_returns_unhealthy_on_error(
        self,
    ) -> None:
        """Test check_redis_health returns unhealthy on error."""
        from src.core.redis_client import check_redis_health

        mock_client = AsyncMock()
        mock_client.ping.side_effect = Exception("Connection failed")

        with patch.dict(
            os.environ,
            {"REDIS_HOST": "testhost", "REDIS_PORT": "6379"},
        ):
            clear_config_cache()
            health = await check_redis_health(mock_client)

        assert health["status"] == "unhealthy"
        assert health["connected"] is False
        assert "error" in health


class TestExecuteWithRetry:
    """Tests for execute_with_retry function."""

    @pytest.mark.asyncio
    async def test_execute_with_retry_success_first_try(self) -> None:
        """Test successful execution on first try."""
        from src.core.redis_client import execute_with_retry

        async def success_func():
            return "success"

        result = await execute_with_retry(
            "test_op", success_func, max_retries=3
        )
        assert result == "success"

    @pytest.mark.asyncio
    async def test_execute_with_retry_success_after_retries(self) -> None:
        """Test successful execution after retries."""
        import redis.asyncio as redis

        from src.core.redis_client import execute_with_retry

        call_count = 0

        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise redis.ConnectionError("Connection failed")
            return "success"

        result = await execute_with_retry(
            "test_op", flaky_func, max_retries=3, retry_delay=0.01
        )
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_execute_with_retry_raises_after_max_retries(self) -> None:
        """Test that error is raised after max retries."""
        import redis.asyncio as redis

        from src.core.exceptions import RedisOperationError
        from src.core.redis_client import execute_with_retry

        async def always_fail():
            raise redis.ConnectionError("Connection failed")

        with pytest.raises(RedisOperationError) as exc_info:
            await execute_with_retry(
                "test_op", always_fail, max_retries=2, retry_delay=0.01
            )

        assert "test_op" in str(exc_info.value)
        assert "2 retries" in str(exc_info.value)

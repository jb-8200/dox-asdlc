"""Unit tests for Agent Telemetry Service.

Tests the AgentTelemetryService class methods for retrieving agent status,
logs, and metrics from Redis.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.orchestrator.services.agent_telemetry import (
    AgentTelemetryService,
    get_agent_telemetry_service,
)
from src.orchestrator.api.models.agent_telemetry import (
    AgentLog,
    AgentLogLevel,
    AgentMetrics,
    AgentStatus,
    AgentStatusEnum,
    AgentType,
)


class TestAgentTelemetryServiceInit:
    """Tests for AgentTelemetryService initialization."""

    def test_init_with_default_redis_client(self) -> None:
        """Test service can be instantiated with default Redis client."""
        service = AgentTelemetryService()
        assert service is not None

    def test_init_with_custom_redis_client(self) -> None:
        """Test service can be instantiated with custom Redis client."""
        mock_client = AsyncMock()
        service = AgentTelemetryService(redis_client=mock_client)
        assert service._redis_client is mock_client


class TestGetAllAgentStatus:
    """Tests for get_all_agent_status method."""

    @pytest.fixture
    def service(self) -> AgentTelemetryService:
        """Create a service instance with mocked Redis."""
        mock_client = AsyncMock()
        return AgentTelemetryService(redis_client=mock_client)

    @pytest.mark.asyncio
    async def test_get_all_agent_status_returns_list(
        self, service: AgentTelemetryService
    ) -> None:
        """Test that get_all_agent_status returns a list of AgentStatus."""
        # Mock Redis data
        service._redis_client.smembers.return_value = {"agent-1", "agent-2"}
        service._redis_client.get.side_effect = [
            json.dumps({
                "agent_id": "agent-1",
                "agent_type": "backend",
                "status": "running",
                "current_task": "task-1",
                "progress": 50,
            }),
            json.dumps({
                "agent_id": "agent-2",
                "agent_type": "frontend",
                "status": "idle",
                "current_task": None,
                "progress": 0,
            }),
        ]

        result = await service.get_all_agent_status()

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(s, AgentStatus) for s in result)

    @pytest.mark.asyncio
    async def test_get_all_agent_status_empty(
        self, service: AgentTelemetryService
    ) -> None:
        """Test get_all_agent_status when no agents are active."""
        service._redis_client.smembers.return_value = set()

        result = await service.get_all_agent_status()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_all_agent_status_parses_agent_data(
        self, service: AgentTelemetryService
    ) -> None:
        """Test that agent data is correctly parsed."""
        service._redis_client.smembers.return_value = {"agent-1"}
        service._redis_client.get.return_value = json.dumps({
            "agent_id": "agent-1",
            "agent_type": "backend",
            "status": "running",
            "current_task": "task-xyz",
            "progress": 75,
        })

        result = await service.get_all_agent_status()

        assert len(result) == 1
        agent = result[0]
        assert agent.agent_id == "agent-1"
        assert agent.agent_type == AgentType.BACKEND
        assert agent.status == AgentStatusEnum.RUNNING
        assert agent.current_task == "task-xyz"
        assert agent.progress == 75

    @pytest.mark.asyncio
    async def test_get_all_agent_status_handles_missing_data(
        self, service: AgentTelemetryService
    ) -> None:
        """Test handling when agent status data is missing."""
        service._redis_client.smembers.return_value = {"agent-1"}
        service._redis_client.get.return_value = None

        result = await service.get_all_agent_status()

        # Should skip agents with missing data
        assert result == []

    @pytest.mark.asyncio
    async def test_get_all_agent_status_redis_error(
        self, service: AgentTelemetryService
    ) -> None:
        """Test handling Redis errors gracefully."""
        service._redis_client.smembers.side_effect = Exception("Redis connection error")

        # Should return empty list on error
        result = await service.get_all_agent_status()
        assert result == []


class TestGetAgentLogs:
    """Tests for get_agent_logs method."""

    @pytest.fixture
    def service(self) -> AgentTelemetryService:
        """Create a service instance with mocked Redis."""
        mock_client = AsyncMock()
        return AgentTelemetryService(redis_client=mock_client)

    @pytest.mark.asyncio
    async def test_get_agent_logs_returns_list(
        self, service: AgentTelemetryService
    ) -> None:
        """Test that get_agent_logs returns a list of AgentLog."""
        timestamp = datetime.now(timezone.utc).isoformat()
        service._redis_client.lrange.return_value = [
            json.dumps({
                "timestamp": timestamp,
                "level": "info",
                "message": "Task started",
                "agent_id": "agent-1",
            }),
            json.dumps({
                "timestamp": timestamp,
                "level": "debug",
                "message": "Processing step 1",
                "agent_id": "agent-1",
            }),
        ]

        result = await service.get_agent_logs("agent-1")

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(log, AgentLog) for log in result)

    @pytest.mark.asyncio
    async def test_get_agent_logs_with_limit(
        self, service: AgentTelemetryService
    ) -> None:
        """Test that get_agent_logs respects the limit parameter."""
        timestamp = datetime.now(timezone.utc).isoformat()
        service._redis_client.lrange.return_value = [
            json.dumps({
                "timestamp": timestamp,
                "level": "info",
                "message": "Log 1",
                "agent_id": "agent-1",
            }),
        ]

        await service.get_agent_logs("agent-1", limit=50)

        # Verify lrange was called with correct range (0 to limit-1)
        service._redis_client.lrange.assert_called_once()
        call_args = service._redis_client.lrange.call_args
        assert call_args[0][1] == 0  # start
        assert call_args[0][2] == 49  # end (limit - 1)

    @pytest.mark.asyncio
    async def test_get_agent_logs_with_level_filter(
        self, service: AgentTelemetryService
    ) -> None:
        """Test that get_agent_logs filters by log level."""
        timestamp = datetime.now(timezone.utc).isoformat()
        service._redis_client.lrange.return_value = [
            json.dumps({
                "timestamp": timestamp,
                "level": "info",
                "message": "Info log",
                "agent_id": "agent-1",
            }),
            json.dumps({
                "timestamp": timestamp,
                "level": "error",
                "message": "Error log",
                "agent_id": "agent-1",
            }),
            json.dumps({
                "timestamp": timestamp,
                "level": "debug",
                "message": "Debug log",
                "agent_id": "agent-1",
            }),
        ]

        result = await service.get_agent_logs("agent-1", level=AgentLogLevel.ERROR)

        assert len(result) == 1
        assert result[0].level == AgentLogLevel.ERROR

    @pytest.mark.asyncio
    async def test_get_agent_logs_empty(
        self, service: AgentTelemetryService
    ) -> None:
        """Test get_agent_logs when no logs exist."""
        service._redis_client.lrange.return_value = []

        result = await service.get_agent_logs("agent-1")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_agent_logs_default_limit(
        self, service: AgentTelemetryService
    ) -> None:
        """Test that default limit is 100."""
        service._redis_client.lrange.return_value = []

        await service.get_agent_logs("agent-1")

        call_args = service._redis_client.lrange.call_args
        assert call_args[0][2] == 99  # end (default limit 100 - 1)


class TestGetAgentMetrics:
    """Tests for get_agent_metrics method."""

    @pytest.fixture
    def service(self) -> AgentTelemetryService:
        """Create a service instance with mocked Redis."""
        mock_client = AsyncMock()
        return AgentTelemetryService(redis_client=mock_client)

    @pytest.mark.asyncio
    async def test_get_agent_metrics_returns_list(
        self, service: AgentTelemetryService
    ) -> None:
        """Test that get_agent_metrics returns a list of AgentMetrics."""
        service._redis_client.keys.return_value = [
            "agent:metrics:backend",
            "agent:metrics:frontend",
        ]
        service._redis_client.get.side_effect = [
            json.dumps({
                "agent_type": "backend",
                "total_executions": 100,
                "success_rate": 0.95,
                "avg_duration": 5.5,
            }),
            json.dumps({
                "agent_type": "frontend",
                "total_executions": 50,
                "success_rate": 0.90,
                "avg_duration": 3.2,
            }),
        ]

        result = await service.get_agent_metrics()

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(m, AgentMetrics) for m in result)

    @pytest.mark.asyncio
    async def test_get_agent_metrics_parses_data(
        self, service: AgentTelemetryService
    ) -> None:
        """Test that metrics data is correctly parsed."""
        service._redis_client.keys.return_value = ["agent:metrics:backend"]
        service._redis_client.get.return_value = json.dumps({
            "agent_type": "backend",
            "total_executions": 100,
            "success_rate": 0.95,
            "avg_duration": 5.5,
        })

        result = await service.get_agent_metrics()

        assert len(result) == 1
        metrics = result[0]
        assert metrics.agent_type == AgentType.BACKEND
        assert metrics.total_executions == 100
        assert metrics.success_rate == 0.95
        assert metrics.avg_duration == 5.5

    @pytest.mark.asyncio
    async def test_get_agent_metrics_empty(
        self, service: AgentTelemetryService
    ) -> None:
        """Test get_agent_metrics when no metrics exist."""
        service._redis_client.keys.return_value = []

        result = await service.get_agent_metrics()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_agent_metrics_handles_missing_data(
        self, service: AgentTelemetryService
    ) -> None:
        """Test handling when metrics data is missing."""
        service._redis_client.keys.return_value = ["agent:metrics:backend"]
        service._redis_client.get.return_value = None

        result = await service.get_agent_metrics()

        # Should skip metrics with missing data
        assert result == []


class TestGetAgentTelemetryServiceSingleton:
    """Tests for the singleton get_agent_telemetry_service function."""

    def test_get_agent_telemetry_service_returns_service(self) -> None:
        """Test that get_agent_telemetry_service returns a service instance."""
        service = get_agent_telemetry_service()
        assert isinstance(service, AgentTelemetryService)

    def test_get_agent_telemetry_service_returns_singleton(self) -> None:
        """Test that get_agent_telemetry_service returns the same instance."""
        service1 = get_agent_telemetry_service()
        service2 = get_agent_telemetry_service()
        assert service1 is service2

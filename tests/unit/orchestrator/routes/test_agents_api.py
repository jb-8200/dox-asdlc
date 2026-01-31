"""Unit tests for Agent Telemetry API endpoints.

Tests the REST API and WebSocket endpoints for agent activity monitoring.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from src.orchestrator.api.models.agent_telemetry import (
    AgentLog,
    AgentLogLevel,
    AgentMetrics,
    AgentStatus,
    AgentStatusEnum,
    AgentTimelineEntry,
    AgentType,
)
from src.orchestrator.routes.agents_api import (
    router,
    ws_router,
    get_telemetry_service,
    ConnectionManager,
)


@pytest.fixture
def mock_service() -> AsyncMock:
    """Create a mock AgentTelemetryService."""
    service = AsyncMock()
    return service


@pytest.fixture
def client(mock_service: AsyncMock) -> TestClient:
    """Create test client with mocked service."""
    app = FastAPI()
    app.include_router(router)
    app.include_router(ws_router)  # Include the WebSocket router

    # Override the service dependency
    app.dependency_overrides[get_telemetry_service] = lambda: mock_service

    return TestClient(app)


class TestGetAgentsStatus:
    """Tests for GET /api/agents/status endpoint."""

    def test_get_agents_status_empty(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Test getting status when no agents exist."""
        mock_service.get_all_agent_status.return_value = []

        response = client.get("/api/agents/status")

        assert response.status_code == 200
        data = response.json()
        assert data["agents"] == []
        assert "timestamp" in data

    def test_get_agents_status_with_agents(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Test getting status with active agents."""
        mock_service.get_all_agent_status.return_value = [
            AgentStatus(
                agent_id="agent-1",
                agent_type=AgentType.BACKEND,
                status=AgentStatusEnum.RUNNING,
                current_task="task-1",
                progress=50,
            ),
            AgentStatus(
                agent_id="agent-2",
                agent_type=AgentType.FRONTEND,
                status=AgentStatusEnum.IDLE,
                current_task=None,
                progress=0,
            ),
        ]

        response = client.get("/api/agents/status")

        assert response.status_code == 200
        data = response.json()
        assert len(data["agents"]) == 2
        assert data["agents"][0]["agent_id"] == "agent-1"
        assert data["agents"][0]["agent_type"] == "backend"
        assert data["agents"][0]["status"] == "running"
        assert data["agents"][0]["current_task"] == "task-1"
        assert data["agents"][0]["progress"] == 50

    def test_get_agents_status_service_error(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Test handling of service errors returns generic message."""
        mock_service.get_all_agent_status.side_effect = Exception("Service error")

        response = client.get("/api/agents/status")

        assert response.status_code == 503
        data = response.json()
        # Generic error message - should not expose internal error details
        assert "unavailable" in data["detail"].lower()


class TestGetAgentLogs:
    """Tests for GET /api/agents/{id}/logs endpoint."""

    def test_get_agent_logs_empty(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Test getting logs when no logs exist."""
        mock_service.get_agent_logs.return_value = []

        response = client.get("/api/agents/agent-1/logs")

        assert response.status_code == 200
        data = response.json()
        assert data["logs"] == []
        assert data["agent_id"] == "agent-1"

    def test_get_agent_logs_with_data(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Test getting logs with data."""
        timestamp = datetime.now(timezone.utc)
        mock_service.get_agent_logs.return_value = [
            AgentLog(
                timestamp=timestamp,
                level=AgentLogLevel.INFO,
                message="Task started",
                agent_id="agent-1",
            ),
            AgentLog(
                timestamp=timestamp,
                level=AgentLogLevel.DEBUG,
                message="Processing",
                agent_id="agent-1",
            ),
        ]

        response = client.get("/api/agents/agent-1/logs")

        assert response.status_code == 200
        data = response.json()
        assert len(data["logs"]) == 2
        assert data["logs"][0]["level"] == "info"
        assert data["logs"][0]["message"] == "Task started"

    def test_get_agent_logs_with_limit(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Test getting logs with limit parameter."""
        mock_service.get_agent_logs.return_value = []

        response = client.get("/api/agents/agent-1/logs?limit=50")

        assert response.status_code == 200
        mock_service.get_agent_logs.assert_called_once_with(
            "agent-1", limit=50, level=None
        )

    def test_get_agent_logs_with_level_filter(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Test getting logs with level filter."""
        mock_service.get_agent_logs.return_value = []

        response = client.get("/api/agents/agent-1/logs?level=error")

        assert response.status_code == 200
        mock_service.get_agent_logs.assert_called_once_with(
            "agent-1", limit=100, level=AgentLogLevel.ERROR
        )

    def test_get_agent_logs_invalid_limit(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Test getting logs with invalid limit."""
        response = client.get("/api/agents/agent-1/logs?limit=-1")

        assert response.status_code == 422

    def test_get_agent_logs_limit_too_large(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Test getting logs with limit too large."""
        response = client.get("/api/agents/agent-1/logs?limit=10000")

        assert response.status_code == 422

    def test_get_agent_logs_invalid_level(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Test getting logs with invalid level."""
        response = client.get("/api/agents/agent-1/logs?level=invalid")

        assert response.status_code == 422


class TestGetAgentMetrics:
    """Tests for GET /api/agents/metrics endpoint."""

    def test_get_agent_metrics_empty(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Test getting metrics when no metrics exist."""
        mock_service.get_agent_metrics.return_value = []

        response = client.get("/api/agents/metrics")

        assert response.status_code == 200
        data = response.json()
        assert data["metrics"] == []
        assert "timestamp" in data

    def test_get_agent_metrics_with_data(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Test getting metrics with data."""
        mock_service.get_agent_metrics.return_value = [
            AgentMetrics(
                agent_type=AgentType.BACKEND,
                total_executions=100,
                success_rate=0.95,
                avg_duration=5.5,
            ),
            AgentMetrics(
                agent_type=AgentType.FRONTEND,
                total_executions=50,
                success_rate=0.90,
                avg_duration=3.2,
            ),
        ]

        response = client.get("/api/agents/metrics")

        assert response.status_code == 200
        data = response.json()
        assert len(data["metrics"]) == 2
        assert data["metrics"][0]["agent_type"] == "backend"
        assert data["metrics"][0]["total_executions"] == 100
        assert data["metrics"][0]["success_rate"] == 0.95
        assert data["metrics"][0]["avg_duration"] == 5.5

    def test_get_agent_metrics_service_error(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Test handling of service errors returns generic message."""
        mock_service.get_agent_metrics.side_effect = Exception("Service error")

        response = client.get("/api/agents/metrics")

        assert response.status_code == 503
        data = response.json()
        # Generic error message - should not expose internal error details
        assert "unavailable" in data["detail"].lower()


class TestGetAgentTimeline:
    """Tests for GET /api/agents/timeline endpoint."""

    def test_get_agent_timeline_empty(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Test getting timeline when no entries exist."""
        mock_service.get_agent_timeline.return_value = []

        response = client.get("/api/agents/timeline")

        assert response.status_code == 200
        data = response.json()
        assert data["entries"] == []
        assert "time_range" in data
        assert "start" in data["time_range"]
        assert "end" in data["time_range"]

    def test_get_agent_timeline_with_entries(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Test getting timeline with data."""
        timestamp = datetime.now(timezone.utc)
        mock_service.get_agent_timeline.return_value = [
            AgentTimelineEntry(
                agent_id="agent-1",
                agent_type="backend",
                task_id="task-1",
                task_name="Build API",
                status="completed",
                start_time=timestamp,
                end_time=timestamp,
                duration_ms=1000,
            ),
        ]

        response = client.get("/api/agents/timeline")

        assert response.status_code == 200
        data = response.json()
        assert len(data["entries"]) == 1
        assert data["entries"][0]["agent_id"] == "agent-1"
        assert data["entries"][0]["task_id"] == "task-1"
        assert data["entries"][0]["task_name"] == "Build API"
        assert data["entries"][0]["status"] == "completed"
        assert data["entries"][0]["duration_ms"] == 1000

    def test_get_agent_timeline_with_time_range_1h(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Test getting timeline with 1h time range."""
        mock_service.get_agent_timeline.return_value = []

        response = client.get("/api/agents/timeline?time_range=1h")

        assert response.status_code == 200
        mock_service.get_agent_timeline.assert_called_once_with("1h")

    def test_get_agent_timeline_with_time_range_7d(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Test getting timeline with 7d time range."""
        mock_service.get_agent_timeline.return_value = []

        response = client.get("/api/agents/timeline?time_range=7d")

        assert response.status_code == 200
        mock_service.get_agent_timeline.assert_called_once_with("7d")

    def test_get_agent_timeline_service_error(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Test handling of service errors returns generic message."""
        mock_service.get_agent_timeline.side_effect = Exception("Service error")

        response = client.get("/api/agents/timeline")

        assert response.status_code == 503
        data = response.json()
        # Generic error message - should not expose internal error details
        assert "unavailable" in data["detail"].lower()


class TestGetAgentDetail:
    """Tests for GET /api/agents/{id}/detail endpoint."""

    def test_get_agent_detail_found(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Test getting agent detail when agent exists."""
        mock_service.get_agent_status_by_id.return_value = AgentStatus(
            agent_id="agent-1",
            agent_type=AgentType.BACKEND,
            status=AgentStatusEnum.RUNNING,
            current_task="task-1",
            progress=75,
        )

        response = client.get("/api/agents/agent-1/detail")

        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "agent-1"
        assert data["agent_type"] == "backend"
        assert data["status"] == "running"
        assert data["current_task"] == "task-1"
        assert data["progress"] == 75

    def test_get_agent_detail_not_found(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Test getting agent detail when agent does not exist."""
        mock_service.get_agent_status_by_id.return_value = None

        response = client.get("/api/agents/agent-1/detail")

        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Agent not found"

    def test_get_agent_detail_invalid_id_format(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Test getting agent detail with invalid ID format."""
        # ID with special characters not allowed
        response = client.get("/api/agents/agent@invalid!/detail")

        assert response.status_code == 422

    def test_get_agent_detail_service_error(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Test handling of service errors returns generic message."""
        mock_service.get_agent_status_by_id.side_effect = Exception("Service error")

        response = client.get("/api/agents/agent-1/detail")

        assert response.status_code == 503
        data = response.json()
        # Generic error message - should not expose internal error details
        assert "unavailable" in data["detail"].lower()


class TestConnectionManager:
    """Tests for WebSocket connection manager."""

    @pytest.fixture
    def manager(self) -> ConnectionManager:
        """Create a connection manager instance."""
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_connect_adds_connection(self, manager: ConnectionManager) -> None:
        """Test that connect adds a WebSocket to active connections."""
        websocket = MagicMock()
        websocket.accept = AsyncMock()

        await manager.connect(websocket)

        assert websocket in manager.active_connections
        websocket.accept.assert_called_once()

    def test_disconnect_removes_connection(self, manager: ConnectionManager) -> None:
        """Test that disconnect removes a WebSocket from active connections."""
        websocket = MagicMock()
        manager.active_connections.append(websocket)

        manager.disconnect(websocket)

        assert websocket not in manager.active_connections

    def test_disconnect_nonexistent_connection(
        self, manager: ConnectionManager
    ) -> None:
        """Test that disconnect handles non-existent connections gracefully."""
        websocket = MagicMock()

        # Should not raise an error
        manager.disconnect(websocket)

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all(self, manager: ConnectionManager) -> None:
        """Test that broadcast sends message to all connections."""
        ws1 = MagicMock()
        ws1.send_json = AsyncMock()
        ws2 = MagicMock()
        ws2.send_json = AsyncMock()

        manager.active_connections = [ws1, ws2]
        message = {"type": "test", "data": "hello"}

        await manager.broadcast(message)

        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_removes_disconnected(
        self, manager: ConnectionManager
    ) -> None:
        """Test that broadcast removes disconnected clients."""
        ws1 = MagicMock()
        ws1.send_json = AsyncMock()
        ws2 = MagicMock()
        ws2.send_json = AsyncMock(side_effect=Exception("Connection closed"))

        manager.active_connections = [ws1, ws2]
        message = {"type": "test", "data": "hello"}

        await manager.broadcast(message)

        # ws2 should be removed due to error
        assert ws1 in manager.active_connections
        assert ws2 not in manager.active_connections


class TestWebSocketAgents:
    """Tests for WebSocket /ws/agents endpoint."""

    def test_websocket_connect(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Test WebSocket connection."""
        with client.websocket_connect("/ws/agents") as websocket:
            # Send ping
            websocket.send_json({"type": "ping"})

            # Should receive pong
            data = websocket.receive_json()
            assert data["type"] == "pong"

    def test_websocket_heartbeat(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Test WebSocket heartbeat mechanism."""
        with client.websocket_connect("/ws/agents") as websocket:
            # Send heartbeat request
            websocket.send_json({"type": "heartbeat"})

            # Should receive heartbeat response
            data = websocket.receive_json()
            assert data["type"] == "heartbeat"
            assert "timestamp" in data

    def test_websocket_subscribe_status(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Test WebSocket subscription to status updates."""
        mock_service.get_all_agent_status.return_value = [
            AgentStatus(
                agent_id="agent-1",
                agent_type=AgentType.BACKEND,
                status=AgentStatusEnum.RUNNING,
                current_task="task-1",
                progress=50,
            ),
        ]

        with client.websocket_connect("/ws/agents") as websocket:
            # Subscribe to status updates
            websocket.send_json({"type": "subscribe", "channel": "status"})

            # Should receive current status
            data = websocket.receive_json()
            assert data["type"] == "status_update"
            assert "agents" in data["data"]

    def test_websocket_unknown_message_type(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Test WebSocket handles unknown message types."""
        with client.websocket_connect("/ws/agents") as websocket:
            # Send unknown message type
            websocket.send_json({"type": "unknown"})

            # Should receive error message
            data = websocket.receive_json()
            assert data["type"] == "error"
            assert "unknown" in data["message"].lower()


class TestRouterIntegration:
    """Integration tests for the agents router."""

    def test_router_has_correct_prefix(self) -> None:
        """Test that router has the correct API prefix."""
        assert router.prefix == "/api/agents"

    def test_router_has_correct_tags(self) -> None:
        """Test that router has the correct tags."""
        assert "agents" in router.tags

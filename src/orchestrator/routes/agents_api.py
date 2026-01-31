"""Agent Telemetry API endpoints.

Provides REST API and WebSocket endpoints for real-time agent activity
monitoring (P02-F08).

Endpoints:
- GET /api/agents/status - All agent statuses
- GET /api/agents/{id}/logs - Agent logs with limit/level filters
- GET /api/agents/metrics - Aggregated metrics by type
- GET /api/agents/timeline - Execution timeline for Gantt view
- GET /api/agents/{id}/detail - Detailed status for a specific agent
- WS /ws/agents - Real-time updates via WebSocket
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import re

from fastapi import APIRouter, Depends, HTTPException, Path, Query, WebSocket, WebSocketDisconnect
from pydantic import Field

from src.orchestrator.api.models.agent_telemetry import (
    AgentLog,
    AgentLogLevel,
    AgentLogsResponse,
    AgentMetrics,
    AgentMetricsResponse,
    AgentStatus,
    AgentStatusResponse,
    AgentTimelineEntry,
    AgentTimelineResponse,
)
from src.orchestrator.services.agent_telemetry import (
    AgentTelemetryService,
    get_agent_telemetry_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agents"])


# Dependency injection for service
def get_telemetry_service() -> AgentTelemetryService:
    """Get the agent telemetry service instance.

    Returns:
        AgentTelemetryService: The service instance.
    """
    return get_agent_telemetry_service()


class ConnectionManager:
    """Manages WebSocket connections for real-time updates.

    Handles connection lifecycle, broadcasting, and heartbeat management.
    """

    def __init__(self) -> None:
        """Initialize the connection manager."""
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection.

        Args:
            websocket: The WebSocket to connect.
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection.

        Args:
            websocket: The WebSocket to disconnect.
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Send a message to all connected clients.

        Args:
            message: The message to broadcast.
        """
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def send_personal_message(
        self, message: dict[str, Any], websocket: WebSocket
    ) -> None:
        """Send a message to a specific client.

        Args:
            message: The message to send.
            websocket: The target WebSocket.
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.warning(f"Failed to send personal message: {e}")


# Global connection manager instance
manager = ConnectionManager()


# =============================================================================
# REST API Endpoints
# =============================================================================


@router.get("/status", response_model=AgentStatusResponse)
async def get_agents_status(
    service: AgentTelemetryService = Depends(get_telemetry_service),
) -> AgentStatusResponse:
    """Get status for all active agents.

    Returns:
        AgentStatusResponse: List of agent statuses with timestamp.

    Raises:
        HTTPException: 503 if service is unavailable.
    """
    try:
        agents = await service.get_all_agent_status()
        return AgentStatusResponse(
            agents=agents,
            timestamp=datetime.now(timezone.utc),
        )
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable",
        ) from e


# Agent ID validation pattern: alphanumeric, underscores, hyphens, 1-64 chars
AGENT_ID_PATTERN = r"^[a-zA-Z0-9_-]{1,64}$"


@router.get("/{agent_id}/logs", response_model=AgentLogsResponse)
async def get_agent_logs(
    agent_id: str = Path(..., pattern=AGENT_ID_PATTERN, description="Agent identifier"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum logs to return"),
    level: Optional[AgentLogLevel] = Query(None, description="Filter by log level"),
    service: AgentTelemetryService = Depends(get_telemetry_service),
) -> AgentLogsResponse:
    """Get logs for a specific agent.

    Args:
        agent_id: The agent ID to get logs for.
        limit: Maximum number of logs to return (1-1000, default 100).
        level: Optional filter by log level.

    Returns:
        AgentLogsResponse: List of log entries for the agent.

    Raises:
        HTTPException: 503 if service is unavailable.
    """
    try:
        logs = await service.get_agent_logs(agent_id, limit=limit, level=level)
        return AgentLogsResponse(
            logs=logs,
            agent_id=agent_id,
            total_count=len(logs),
        )
    except Exception as e:
        logger.error(f"Error getting agent logs: {e}")
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable",
        ) from e


@router.get("/metrics", response_model=AgentMetricsResponse)
async def get_agent_metrics(
    service: AgentTelemetryService = Depends(get_telemetry_service),
) -> AgentMetricsResponse:
    """Get aggregated metrics for all agent types.

    Returns:
        AgentMetricsResponse: List of metrics by agent type.

    Raises:
        HTTPException: 503 if service is unavailable.
    """
    try:
        metrics = await service.get_agent_metrics()
        return AgentMetricsResponse(
            metrics=metrics,
            timestamp=datetime.now(timezone.utc),
        )
    except Exception as e:
        logger.error(f"Error getting agent metrics: {e}")
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable",
        ) from e


@router.get("/timeline", response_model=AgentTimelineResponse)
async def get_agent_timeline(
    time_range: str = Query("24h", description="Time range (1h, 24h, 7d)"),
    service: AgentTelemetryService = Depends(get_telemetry_service),
) -> AgentTimelineResponse:
    """Get execution timeline for all agents.

    Returns timeline entries for agent task executions, suitable for
    Gantt-style visualization.

    Args:
        time_range: Time range filter (1h, 24h, 7d). Defaults to "24h".

    Returns:
        AgentTimelineResponse: List of timeline entries with time range bounds.

    Raises:
        HTTPException: 503 if service is unavailable.
    """
    try:
        entries = await service.get_agent_timeline(time_range)
        now = datetime.now(timezone.utc)
        # Calculate time range bounds
        hours = {"1h": 1, "24h": 24, "7d": 168}.get(time_range, 24)
        start = now - timedelta(hours=hours)
        return AgentTimelineResponse(
            entries=entries,
            time_range={"start": start, "end": now}
        )
    except Exception as e:
        logger.error(f"Error getting agent timeline: {e}")
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable",
        ) from e


@router.get("/{agent_id}/detail", response_model=AgentStatus)
async def get_agent_detail(
    agent_id: str = Path(..., pattern=AGENT_ID_PATTERN, description="Agent identifier"),
    service: AgentTelemetryService = Depends(get_telemetry_service),
) -> AgentStatus:
    """Get detailed status for a specific agent.

    Args:
        agent_id: The agent ID to get details for.

    Returns:
        AgentStatus: Detailed status for the specified agent.

    Raises:
        HTTPException: 404 if agent not found.
        HTTPException: 503 if service is unavailable.
    """
    try:
        status = await service.get_agent_status_by_id(agent_id)
        if not status:
            raise HTTPException(status_code=404, detail="Agent not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent detail: {e}")
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable",
        ) from e


# =============================================================================
# WebSocket Endpoint
# =============================================================================


@router.websocket("/ws")
async def websocket_agents(
    websocket: WebSocket,
    service: AgentTelemetryService = Depends(get_telemetry_service),
) -> None:
    """WebSocket endpoint for real-time agent updates.

    Supports the following message types:
    - ping/pong: Connection health check
    - heartbeat: Periodic heartbeat with timestamp
    - subscribe: Subscribe to status updates

    Args:
        websocket: The WebSocket connection.
        service: The telemetry service instance.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Wait for incoming messages
            data = await websocket.receive_json()
            message_type = data.get("type", "")

            if message_type == "ping":
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()},
                    websocket,
                )

            elif message_type == "heartbeat":
                await manager.send_personal_message(
                    {"type": "heartbeat", "timestamp": datetime.now(timezone.utc).isoformat()},
                    websocket,
                )

            elif message_type == "subscribe":
                channel = data.get("channel", "")
                if channel == "status":
                    # Send current status immediately
                    try:
                        agents = await service.get_all_agent_status()
                        await manager.send_personal_message(
                            {
                                "type": "status_update",
                                "data": {
                                    "agents": [
                                        {
                                            "agent_id": a.agent_id,
                                            "agent_type": a.agent_type,
                                            "status": a.status,
                                            "current_task": a.current_task,
                                            "progress": a.progress,
                                        }
                                        for a in agents
                                    ]
                                },
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            },
                            websocket,
                        )
                    except Exception as e:
                        logger.error(f"Error sending status update: {e}")
                        await manager.send_personal_message(
                            {"type": "error", "message": "Failed to retrieve status"},
                            websocket,
                        )
                else:
                    await manager.send_personal_message(
                        {"type": "error", "message": f"Unknown channel: {channel}"},
                        websocket,
                    )

            else:
                await manager.send_personal_message(
                    {"type": "error", "message": f"Unknown message type: {message_type}"},
                    websocket,
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# Standalone WebSocket endpoint at /ws/agents for direct access
# This is registered separately from the router prefix
ws_router = APIRouter(tags=["agents"])


@ws_router.websocket("/ws/agents")
async def websocket_agents_direct(
    websocket: WebSocket,
    service: AgentTelemetryService = Depends(get_telemetry_service),
) -> None:
    """WebSocket endpoint for real-time agent updates (direct path).

    Same functionality as /api/agents/ws but at /ws/agents for convenience.
    """
    await websocket_agents(websocket, service)

"""Agent Telemetry Service.

Provides methods for retrieving agent status, logs, and metrics from Redis.
Used by the Agent Telemetry API (P02-F08) for real-time agent monitoring.

Redis Keys:
- agent:status:{id} - JSON status object
- agent:logs:{id} - List of log entries (capped at 1000)
- agent:metrics:{type} - Metrics JSON by agent type
- agent:active - Set of active agent IDs
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

import redis.asyncio as redis

from src.orchestrator.api.models.agent_telemetry import (
    AgentLog,
    AgentLogLevel,
    AgentMetrics,
    AgentStatus,
    AgentStatusEnum,
    AgentType,
)

logger = logging.getLogger(__name__)

# Redis key prefixes
AGENT_STATUS_KEY_PREFIX = "agent:status:"
AGENT_LOGS_KEY_PREFIX = "agent:logs:"
AGENT_METRICS_KEY_PREFIX = "agent:metrics:"
AGENT_ACTIVE_SET_KEY = "agent:active"

# Default values
DEFAULT_LOG_LIMIT = 100
MAX_LOG_LIMIT = 1000


class AgentTelemetryService:
    """Service for retrieving agent telemetry data from Redis.

    Provides methods to query agent status, logs, and metrics with
    graceful error handling and optional filtering.
    """

    def __init__(self, redis_client: Optional[redis.Redis] = None) -> None:
        """Initialize the agent telemetry service.

        Args:
            redis_client: Optional Redis client. If not provided, a client
                will be created lazily when needed.
        """
        self._redis_client = redis_client
        self._client_initialized = redis_client is not None

    async def _get_client(self) -> redis.Redis:
        """Get or create the Redis client.

        Returns:
            redis.Redis: The async Redis client.
        """
        if not self._client_initialized:
            from src.core.redis_client import get_redis_client
            self._redis_client = await get_redis_client()
            self._client_initialized = True
        return self._redis_client

    async def get_all_agent_status(self) -> list[AgentStatus]:
        """Get status for all active agents.

        Retrieves the list of active agent IDs from the agent:active set,
        then fetches status details for each agent.

        Returns:
            list[AgentStatus]: List of agent statuses, sorted by agent_id.
        """
        try:
            client = await self._get_client()

            # Get all active agent IDs
            active_ids = await client.smembers(AGENT_ACTIVE_SET_KEY)
            if not active_ids:
                return []

            statuses = []
            for agent_id in active_ids:
                status_key = f"{AGENT_STATUS_KEY_PREFIX}{agent_id}"
                status_json = await client.get(status_key)

                if status_json:
                    try:
                        status_data = json.loads(status_json)
                        status = self._parse_agent_status(status_data)
                        if status:
                            statuses.append(status)
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(f"Failed to parse status for {agent_id}: {e}")

            # Sort by agent_id for consistent ordering
            return sorted(statuses, key=lambda s: s.agent_id)

        except Exception as e:
            logger.error(f"Error getting agent statuses: {e}")
            return []

    def _parse_agent_status(self, data: dict[str, Any]) -> Optional[AgentStatus]:
        """Parse agent status data from JSON.

        Args:
            data: Dictionary containing agent status fields.

        Returns:
            AgentStatus or None if parsing fails.
        """
        try:
            agent_type = data.get("agent_type", "").lower()
            status = data.get("status", "").lower()

            return AgentStatus(
                agent_id=data["agent_id"],
                agent_type=AgentType(agent_type),
                status=AgentStatusEnum(status),
                current_task=data.get("current_task"),
                progress=int(data.get("progress", 0)),
            )
        except (KeyError, ValueError) as e:
            logger.warning(f"Invalid agent status data: {e}")
            return None

    async def get_agent_logs(
        self,
        agent_id: str,
        limit: int = DEFAULT_LOG_LIMIT,
        level: Optional[AgentLogLevel] = None,
    ) -> list[AgentLog]:
        """Get logs for a specific agent.

        Retrieves log entries from the agent:logs:{id} list in Redis.
        Logs are stored newest-first, so lrange 0 to limit-1 gets recent logs.

        Args:
            agent_id: The agent ID to get logs for.
            limit: Maximum number of logs to return (default 100, max 1000).
            level: Optional filter by log level.

        Returns:
            list[AgentLog]: List of log entries, newest first.
        """
        try:
            client = await self._get_client()

            # Clamp limit to valid range
            limit = min(max(1, limit), MAX_LOG_LIMIT)

            logs_key = f"{AGENT_LOGS_KEY_PREFIX}{agent_id}"
            log_entries = await client.lrange(logs_key, 0, limit - 1)

            logs = []
            for entry in log_entries:
                try:
                    log_data = json.loads(entry)
                    log = self._parse_agent_log(log_data)
                    if log:
                        # Apply level filter if specified
                        if level is None or log.level == level:
                            logs.append(log)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse log entry: {e}")

            return logs

        except Exception as e:
            logger.error(f"Error getting agent logs for {agent_id}: {e}")
            return []

    def _parse_agent_log(self, data: dict[str, Any]) -> Optional[AgentLog]:
        """Parse agent log data from JSON.

        Args:
            data: Dictionary containing log fields.

        Returns:
            AgentLog or None if parsing fails.
        """
        try:
            timestamp_str = data.get("timestamp")
            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            else:
                timestamp = datetime.now(timezone.utc)

            level_str = data.get("level", "info").lower()

            return AgentLog(
                timestamp=timestamp,
                level=AgentLogLevel(level_str),
                message=data.get("message", ""),
                agent_id=data.get("agent_id", ""),
            )
        except (KeyError, ValueError) as e:
            logger.warning(f"Invalid agent log data: {e}")
            return None

    async def get_agent_metrics(self) -> list[AgentMetrics]:
        """Get aggregated metrics for all agent types.

        Retrieves metrics from agent:metrics:{type} keys for each agent type.

        Returns:
            list[AgentMetrics]: List of metrics by agent type.
        """
        try:
            client = await self._get_client()

            # Find all metrics keys
            metrics_keys = await client.keys(f"{AGENT_METRICS_KEY_PREFIX}*")
            if not metrics_keys:
                return []

            metrics_list = []
            for key in metrics_keys:
                metrics_json = await client.get(key)

                if metrics_json:
                    try:
                        metrics_data = json.loads(metrics_json)
                        metrics = self._parse_agent_metrics(metrics_data)
                        if metrics:
                            metrics_list.append(metrics)
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(f"Failed to parse metrics for {key}: {e}")

            # Sort by agent_type for consistent ordering
            return sorted(metrics_list, key=lambda m: m.agent_type)

        except Exception as e:
            logger.error(f"Error getting agent metrics: {e}")
            return []

    def _parse_agent_metrics(self, data: dict[str, Any]) -> Optional[AgentMetrics]:
        """Parse agent metrics data from JSON.

        Args:
            data: Dictionary containing metrics fields.

        Returns:
            AgentMetrics or None if parsing fails.
        """
        try:
            agent_type = data.get("agent_type", "").lower()

            return AgentMetrics(
                agent_type=AgentType(agent_type),
                total_executions=int(data.get("total_executions", 0)),
                success_rate=float(data.get("success_rate", 0.0)),
                avg_duration=float(data.get("avg_duration", 0.0)),
            )
        except (KeyError, ValueError) as e:
            logger.warning(f"Invalid agent metrics data: {e}")
            return None

    async def get_agent_status_by_id(self, agent_id: str) -> Optional[AgentStatus]:
        """Get status for a specific agent.

        Args:
            agent_id: The agent ID to get status for.

        Returns:
            AgentStatus or None if not found.
        """
        try:
            client = await self._get_client()
            status_key = f"{AGENT_STATUS_KEY_PREFIX}{agent_id}"
            status_json = await client.get(status_key)

            if status_json:
                status_data = json.loads(status_json)
                return self._parse_agent_status(status_data)

            return None

        except Exception as e:
            logger.error(f"Error getting status for agent {agent_id}: {e}")
            return None

    async def get_agent_timeline(self, time_range: str = "24h") -> list:
        """Get timeline entries for all agents within time range.

        Returns timeline entries for agent task executions, suitable for
        Gantt-style visualization. For now, returns an empty list as the
        real implementation would query Redis agent:timeline:{id} keys.

        Args:
            time_range: Time range filter (1h, 24h, 7d). Defaults to "24h".

        Returns:
            list: List of timeline entries (empty for now).
        """
        # For now, return empty list - real implementation would query Redis
        # agent:timeline:{id} keys
        return []


# Module-level singleton instance
_service_instance: Optional[AgentTelemetryService] = None


def get_agent_telemetry_service() -> AgentTelemetryService:
    """Get the singleton agent telemetry service instance.

    Returns:
        AgentTelemetryService: The service instance.
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = AgentTelemetryService()
    return _service_instance

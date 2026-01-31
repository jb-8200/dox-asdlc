"""Agent Telemetry API data models.

Defines Pydantic models for agent status, logs, and metrics used in the
Agent Telemetry API (P02-F08).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """Types of agents in the aSDLC system."""

    BACKEND = "backend"
    FRONTEND = "frontend"
    PLANNER = "planner"
    REVIEWER = "reviewer"
    ORCHESTRATOR = "orchestrator"
    DEVOPS = "devops"


class AgentStatusEnum(str, Enum):
    """Status states for an agent."""

    IDLE = "idle"
    RUNNING = "running"
    BLOCKED = "blocked"
    ERROR = "error"
    COMPLETED = "completed"


class AgentLogLevel(str, Enum):
    """Log levels for agent logs."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class AgentStatus(BaseModel):
    """Status information for a single agent.

    Attributes:
        agent_id: Unique identifier for the agent instance.
        agent_type: Type of agent (backend, frontend, etc.).
        status: Current status of the agent.
        current_task: ID of the task currently being worked on, if any.
        progress: Progress percentage (0-100) of current task.
    """

    agent_id: str = Field(..., description="Unique agent identifier")
    agent_type: AgentType = Field(..., description="Type of agent")
    status: AgentStatusEnum = Field(..., description="Current agent status")
    current_task: Optional[str] = Field(None, description="Current task ID")
    progress: int = Field(0, ge=0, le=100, description="Task progress percentage")

    class Config:
        """Pydantic config for JSON serialization."""

        use_enum_values = True


class AgentStatusResponse(BaseModel):
    """Response model for agent status list.

    Attributes:
        agents: List of agent statuses.
        timestamp: Time when the status was retrieved.
    """

    agents: list[AgentStatus] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config for JSON serialization."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class AgentLog(BaseModel):
    """Log entry from an agent.

    Attributes:
        timestamp: When the log was created.
        level: Log level (debug, info, warning, error).
        message: Log message content.
        agent_id: ID of the agent that created this log.
    """

    timestamp: datetime = Field(..., description="Log timestamp")
    level: AgentLogLevel = Field(..., description="Log level")
    message: str = Field(..., description="Log message")
    agent_id: str = Field(..., description="Agent ID")

    class Config:
        """Pydantic config for JSON serialization."""

        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class AgentLogsResponse(BaseModel):
    """Response model for agent logs.

    Attributes:
        logs: List of agent log entries.
        agent_id: ID of the agent these logs belong to.
        total_count: Total number of logs (may be more than returned).
    """

    logs: list[AgentLog] = Field(default_factory=list)
    agent_id: str = Field(..., description="Agent ID")
    total_count: int = Field(0, description="Total log count")


class AgentMetrics(BaseModel):
    """Aggregated metrics for an agent type.

    Attributes:
        agent_type: Type of agent these metrics are for.
        total_executions: Total number of task executions.
        success_rate: Ratio of successful executions (0.0-1.0).
        avg_duration: Average task duration in seconds.
    """

    agent_type: AgentType = Field(..., description="Agent type")
    total_executions: int = Field(0, ge=0, description="Total executions")
    success_rate: float = Field(0.0, ge=0.0, le=1.0, description="Success rate")
    avg_duration: float = Field(0.0, ge=0.0, description="Average duration in seconds")

    class Config:
        """Pydantic config for JSON serialization."""

        use_enum_values = True


class AgentMetricsResponse(BaseModel):
    """Response model for agent metrics.

    Attributes:
        metrics: List of agent metrics by type.
        timestamp: Time when the metrics were retrieved.
    """

    metrics: list[AgentMetrics] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config for JSON serialization."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class WebSocketMessage(BaseModel):
    """WebSocket message for real-time agent updates.

    Attributes:
        type: Message type (status_update, heartbeat, etc.).
        data: Message payload.
        timestamp: When the message was created.
    """

    type: str = Field(..., description="Message type")
    data: dict = Field(default_factory=dict, description="Message payload")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config for JSON serialization."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class AgentTimelineEntry(BaseModel):
    """Timeline entry for agent task execution.

    Represents a single task execution period for an agent,
    used in Gantt-style timeline visualizations.

    Attributes:
        agent_id: Unique identifier for the agent instance.
        agent_type: Type of agent (backend, frontend, etc.).
        task_id: ID of the task being executed.
        task_name: Human-readable task name.
        status: Current status of the task execution.
        start_time: When the task execution started.
        end_time: When the task execution ended, if completed.
        duration_ms: Duration in milliseconds, if completed.
    """

    agent_id: str = Field(..., description="Unique agent identifier")
    agent_type: str = Field(..., description="Type of agent")
    task_id: str = Field(..., description="Task identifier")
    task_name: str = Field(..., description="Human-readable task name")
    status: str = Field(..., description="Task execution status")
    start_time: datetime = Field(..., description="Task start time")
    end_time: Optional[datetime] = Field(None, description="Task end time")
    duration_ms: Optional[int] = Field(None, ge=0, description="Duration in milliseconds")

    class Config:
        """Pydantic config for JSON serialization."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class AgentTimelineResponse(BaseModel):
    """Response model for agent timeline.

    Attributes:
        entries: List of timeline entries for agent task executions.
        time_range: Dictionary containing start and end timestamps for the query range.
    """

    entries: list[AgentTimelineEntry] = Field(default_factory=list)
    time_range: dict[str, datetime] = Field(
        default_factory=dict,
        description="Time range with 'start' and 'end' keys"
    )

    class Config:
        """Pydantic config for JSON serialization."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

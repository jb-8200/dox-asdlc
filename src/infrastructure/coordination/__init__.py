"""CLI Coordination module for Redis-backed message passing."""

from src.infrastructure.coordination.types import (
    MessageType,
    CoordinationMessage,
    MessagePayload,
    MessageQuery,
    NotificationEvent,
    PresenceInfo,
    CoordinationStats,
)
from src.infrastructure.coordination.config import (
    CoordinationConfig,
    get_coordination_config,
    reset_coordination_config,
)

__all__ = [
    # Types
    "MessageType",
    "CoordinationMessage",
    "MessagePayload",
    "MessageQuery",
    "NotificationEvent",
    "PresenceInfo",
    "CoordinationStats",
    # Config
    "CoordinationConfig",
    "get_coordination_config",
    "reset_coordination_config",
]

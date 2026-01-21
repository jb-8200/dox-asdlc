"""Infrastructure services for the aSDLC system.

This module provides:
- Redis streams for event coordination
- Health check endpoints
"""

from src.infrastructure.health import (
    DependencyHealth,
    HealthChecker,
    HealthResponse,
    HealthStatus,
    get_health_checker,
    health_check_handler,
    liveness_check_handler,
    readiness_check_handler,
)
from src.infrastructure.redis_streams import (
    StreamEvent,
    create_consumer_group,
    ensure_stream_exists,
    get_stream_info,
    initialize_consumer_groups,
    publish_event,
)

__all__ = [
    # Health
    "HealthStatus",
    "DependencyHealth",
    "HealthResponse",
    "HealthChecker",
    "get_health_checker",
    "health_check_handler",
    "liveness_check_handler",
    "readiness_check_handler",
    # Streams
    "StreamEvent",
    "ensure_stream_exists",
    "create_consumer_group",
    "initialize_consumer_groups",
    "get_stream_info",
    "publish_event",
]

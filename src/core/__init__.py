"""Core aSDLC infrastructure components.

This module provides the foundational components for the aSDLC system:
- Configuration management
- Custom exceptions
- Redis client factory
"""

from src.core.config import (
    AppConfig,
    RedisConfig,
    ServiceConfig,
    clear_config_cache,
    get_config,
    get_redis_config,
)
from src.core.exceptions import (
    ASDLCError,
    AgentError,
    AgentExecutionError,
    AgentTimeoutError,
    ArtifactNotFoundError,
    ArtifactValidationError,
    ConfigurationError,
    ConsumerGroupError,
    DependencyHealthError,
    DuplicateEventError,
    EventProcessingError,
    GateApprovalError,
    GitOperationError,
    HealthCheckError,
    HITLError,
    RedisConnectionError,
    RedisOperationError,
    StreamError,
    TaskNotFoundError,
    TaskStateError,
)
from src.core.redis_client import (
    check_redis_health,
    close_redis_client,
    get_redis_client,
    ping_redis,
    redis_client,
)

__all__ = [
    # Config
    "AppConfig",
    "RedisConfig",
    "ServiceConfig",
    "get_config",
    "get_redis_config",
    "clear_config_cache",
    # Exceptions
    "ASDLCError",
    "ConfigurationError",
    "RedisConnectionError",
    "RedisOperationError",
    "StreamError",
    "ConsumerGroupError",
    "TaskNotFoundError",
    "TaskStateError",
    "EventProcessingError",
    "DuplicateEventError",
    "AgentError",
    "AgentTimeoutError",
    "AgentExecutionError",
    "GitOperationError",
    "ArtifactNotFoundError",
    "ArtifactValidationError",
    "HITLError",
    "GateApprovalError",
    "HealthCheckError",
    "DependencyHealthError",
    # Redis client
    "get_redis_client",
    "close_redis_client",
    "redis_client",
    "ping_redis",
    "check_redis_health",
]

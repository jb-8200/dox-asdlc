"""Configuration management for aSDLC services.

Provides environment-based configuration with sensible defaults.
Configuration is loaded once and cached as a singleton.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import ClassVar

from src.core.exceptions import ConfigurationError


@dataclass(frozen=True)
class RedisConfig:
    """Redis connection configuration."""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None
    max_connections: int = 10
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    retry_on_timeout: bool = True

    # Stream configuration
    stream_name: str = "asdlc:events"
    consumer_groups: tuple[str, ...] = (
        "discovery-handlers",
        "design-handlers",
        "development-handlers",
        "validation-handlers",
        "deployment-handlers",
        "hitl-handlers",
    )

    # Key prefixes
    task_prefix: str = "asdlc:task:"
    session_prefix: str = "asdlc:session:"

    @classmethod
    def from_env(cls) -> RedisConfig:
        """Create Redis configuration from environment variables."""
        return cls(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            password=os.getenv("REDIS_PASSWORD"),
            max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "10")),
            socket_timeout=float(os.getenv("REDIS_SOCKET_TIMEOUT", "5.0")),
            socket_connect_timeout=float(
                os.getenv("REDIS_CONNECT_TIMEOUT", "5.0")
            ),
        )


@dataclass(frozen=True)
class TenantConfig:
    """Multi-tenancy configuration."""

    enabled: bool = False
    default_tenant: str = "default"
    allowed_tenants: tuple[str, ...] = ("*",)
    tenant_header: str = "X-Tenant-ID"

    @classmethod
    def from_env(cls) -> TenantConfig:
        """Create tenant configuration from environment variables."""
        enabled = os.getenv("MULTI_TENANCY_ENABLED", "false").lower() in (
            "true",
            "1",
            "yes",
        )

        # Parse allowed tenants from comma-separated string
        allowed_str = os.getenv("ALLOWED_TENANTS", "*")
        allowed_tenants = tuple(
            t.strip() for t in allowed_str.split(",") if t.strip()
        )

        return cls(
            enabled=enabled,
            default_tenant=os.getenv("DEFAULT_TENANT_ID", "default"),
            allowed_tenants=allowed_tenants,
            tenant_header=os.getenv("TENANT_HEADER", "X-Tenant-ID"),
        )


@dataclass(frozen=True)
class ServiceConfig:
    """Service-specific configuration."""

    name: str
    port: int
    host: str = "0.0.0.0"
    debug: bool = False
    git_write_access: bool = False

    @classmethod
    def from_env(cls) -> ServiceConfig:
        """Create service configuration from environment variables."""
        name = os.getenv("SERVICE_NAME")
        if not name:
            raise ConfigurationError(
                "SERVICE_NAME environment variable is required"
            )

        return cls(
            name=name,
            port=int(os.getenv("SERVICE_PORT", "8080")),
            host=os.getenv("SERVICE_HOST", "0.0.0.0"),
            debug=os.getenv("DEBUG", "false").lower() in ("true", "1", "yes"),
            git_write_access=os.getenv("GIT_WRITE_ACCESS", "false").lower()
            in ("true", "1", "yes"),
        )


@dataclass(frozen=True)
class AppConfig:
    """Main application configuration."""

    redis: RedisConfig
    service: ServiceConfig
    tenant: TenantConfig = field(default_factory=TenantConfig)

    # Application-wide settings
    log_level: str = "INFO"
    workspace_path: str = "/app/workspace"

    # RLM settings (from System_Design.md Section 5.2)
    max_subcalls: int = 50
    max_subcalls_per_iteration: int = 8

    # Default instance for when full config not needed
    _default_redis: ClassVar[RedisConfig] = RedisConfig()

    @classmethod
    def from_env(cls) -> AppConfig:
        """Create application configuration from environment variables."""
        return cls(
            redis=RedisConfig.from_env(),
            service=ServiceConfig.from_env(),
            tenant=TenantConfig.from_env(),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            workspace_path=os.getenv("WORKSPACE_PATH", "/app/workspace"),
            max_subcalls=int(os.getenv("MAX_SUBCALLS", "50")),
            max_subcalls_per_iteration=int(
                os.getenv("MAX_SUBCALLS_PER_ITERATION", "8")
            ),
        )


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Get the singleton application configuration.

    Configuration is loaded from environment variables on first call
    and cached for subsequent calls.

    Returns:
        AppConfig: The application configuration singleton.

    Raises:
        ConfigurationError: If required configuration is missing.
    """
    return AppConfig.from_env()


@lru_cache(maxsize=1)
def get_redis_config() -> RedisConfig:
    """Get Redis configuration without full app config.

    Useful for scripts and tests that only need Redis connection.

    Returns:
        RedisConfig: Redis configuration from environment.
    """
    return RedisConfig.from_env()


@lru_cache(maxsize=1)
def get_tenant_config() -> TenantConfig:
    """Get tenant configuration without full app config.

    Useful for middleware and components that only need tenant settings.

    Returns:
        TenantConfig: Tenant configuration from environment.
    """
    return TenantConfig.from_env()


def clear_config_cache() -> None:
    """Clear configuration cache.

    Call this when testing or when configuration might have changed.
    """
    get_config.cache_clear()
    get_redis_config.cache_clear()
    get_tenant_config.cache_clear()

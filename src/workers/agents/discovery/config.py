"""Configuration for Discovery agents.

Provides configuration dataclass with sensible defaults and
environment variable overrides for PRD and Acceptance agents.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""

    pass


# Default values as constants for class method access
_DEFAULT_PRD_MODEL = "claude-sonnet-4-20250514"
_DEFAULT_ACCEPTANCE_MODEL = "claude-sonnet-4-20250514"
_DEFAULT_MAX_TOKENS = 8192
_DEFAULT_TEMPERATURE = 0.3
_DEFAULT_ARTIFACT_BASE_PATH = Path("artifacts/discovery")
_DEFAULT_ENABLE_RLM = True
_DEFAULT_RLM_CONTEXT_THRESHOLD = 100_000
_DEFAULT_MAX_RETRIES = 3
_DEFAULT_RETRY_DELAY_SECONDS = 1.0


@dataclass
class DiscoveryConfig:
    """Configuration for Discovery agents.

    Attributes:
        prd_model: LLM model for PRD generation.
        acceptance_model: LLM model for acceptance criteria generation.
        max_tokens: Maximum tokens for LLM responses.
        temperature: LLM temperature for generation.
        artifact_base_path: Base path for artifact output.
        enable_rlm: Whether to enable RLM integration.
        rlm_context_threshold: Token threshold for RLM activation.
        max_retries: Maximum retry attempts on failure.
        retry_delay_seconds: Delay between retries.
    """

    prd_model: str = _DEFAULT_PRD_MODEL
    acceptance_model: str = _DEFAULT_ACCEPTANCE_MODEL
    max_tokens: int = _DEFAULT_MAX_TOKENS
    temperature: float = _DEFAULT_TEMPERATURE
    artifact_base_path: Path = field(default_factory=lambda: _DEFAULT_ARTIFACT_BASE_PATH)
    enable_rlm: bool = _DEFAULT_ENABLE_RLM
    rlm_context_threshold: int = _DEFAULT_RLM_CONTEXT_THRESHOLD
    max_retries: int = _DEFAULT_MAX_RETRIES
    retry_delay_seconds: float = _DEFAULT_RETRY_DELAY_SECONDS

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate configuration values.

        Raises:
            ConfigValidationError: If validation fails.
        """
        if self.max_tokens < 100:
            raise ConfigValidationError(
                f"max_tokens must be at least 100, got {self.max_tokens}"
            )

        if not 0 <= self.temperature <= 2:
            raise ConfigValidationError(
                f"temperature must be between 0 and 2, got {self.temperature}"
            )

        if self.max_retries < 0:
            raise ConfigValidationError(
                f"max_retries must be non-negative, got {self.max_retries}"
            )

        if self.rlm_context_threshold < 1000:
            raise ConfigValidationError(
                f"rlm_context_threshold must be at least 1000, got {self.rlm_context_threshold}"
            )

        if self.retry_delay_seconds < 0:
            raise ConfigValidationError(
                f"retry_delay_seconds must be non-negative, got {self.retry_delay_seconds}"
            )

    @classmethod
    def from_env(cls) -> DiscoveryConfig:
        """Create configuration from environment variables.

        Environment variables:
            DISCOVERY_PRD_MODEL: Model for PRD generation
            DISCOVERY_ACCEPTANCE_MODEL: Model for acceptance criteria
            DISCOVERY_MAX_TOKENS: Maximum tokens for LLM responses
            DISCOVERY_TEMPERATURE: LLM temperature
            DISCOVERY_ARTIFACT_PATH: Base path for artifacts
            DISCOVERY_ENABLE_RLM: Enable RLM integration (true/false)
            DISCOVERY_RLM_THRESHOLD: Token threshold for RLM
            DISCOVERY_MAX_RETRIES: Maximum retry attempts
            DISCOVERY_RETRY_DELAY: Delay between retries in seconds

        Returns:
            DiscoveryConfig: Configuration from environment.
        """
        def get_bool(key: str, default: bool) -> bool:
            value = os.getenv(key)
            if value is None:
                return default
            return value.lower() in ("true", "1", "yes")

        def get_float(key: str, default: float) -> float:
            value = os.getenv(key)
            if value is None:
                return default
            return float(value)

        def get_int(key: str, default: int) -> int:
            value = os.getenv(key)
            if value is None:
                return default
            return int(value)

        artifact_path = os.getenv("DISCOVERY_ARTIFACT_PATH")

        return cls(
            prd_model=os.getenv("DISCOVERY_PRD_MODEL", _DEFAULT_PRD_MODEL),
            acceptance_model=os.getenv("DISCOVERY_ACCEPTANCE_MODEL", _DEFAULT_ACCEPTANCE_MODEL),
            max_tokens=get_int("DISCOVERY_MAX_TOKENS", _DEFAULT_MAX_TOKENS),
            temperature=get_float("DISCOVERY_TEMPERATURE", _DEFAULT_TEMPERATURE),
            artifact_base_path=Path(artifact_path) if artifact_path else _DEFAULT_ARTIFACT_BASE_PATH,
            enable_rlm=get_bool("DISCOVERY_ENABLE_RLM", _DEFAULT_ENABLE_RLM),
            rlm_context_threshold=get_int("DISCOVERY_RLM_THRESHOLD", _DEFAULT_RLM_CONTEXT_THRESHOLD),
            max_retries=get_int("DISCOVERY_MAX_RETRIES", _DEFAULT_MAX_RETRIES),
            retry_delay_seconds=get_float("DISCOVERY_RETRY_DELAY", _DEFAULT_RETRY_DELAY_SECONDS),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            dict: Configuration as dictionary.
        """
        return {
            "prd_model": self.prd_model,
            "acceptance_model": self.acceptance_model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "artifact_base_path": str(self.artifact_base_path),
            "enable_rlm": self.enable_rlm,
            "rlm_context_threshold": self.rlm_context_threshold,
            "max_retries": self.max_retries,
            "retry_delay_seconds": self.retry_delay_seconds,
        }

    def with_overrides(self, **kwargs: Any) -> DiscoveryConfig:
        """Create new config with overridden values.

        Args:
            **kwargs: Values to override.

        Returns:
            DiscoveryConfig: New config with overrides.
        """
        current = self.to_dict()
        current.update(kwargs)

        # Handle Path conversion
        if isinstance(current.get("artifact_base_path"), str):
            current["artifact_base_path"] = Path(current["artifact_base_path"])

        return DiscoveryConfig(**current)

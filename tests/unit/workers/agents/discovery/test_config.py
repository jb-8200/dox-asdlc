"""Unit tests for DiscoveryConfig."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.workers.agents.discovery.config import (
    DiscoveryConfig,
    ConfigValidationError,
)


class TestDiscoveryConfig:
    """Tests for DiscoveryConfig dataclass."""

    def test_default_config_has_sensible_defaults(self) -> None:
        """Test that default config has sensible defaults."""
        config = DiscoveryConfig()

        assert config.prd_model == "claude-sonnet-4-20250514"
        assert config.acceptance_model == "claude-sonnet-4-20250514"
        assert config.max_tokens == 8192
        assert config.temperature == 0.3
        assert config.artifact_base_path == Path("artifacts/discovery")
        assert config.enable_rlm is True
        assert config.rlm_context_threshold == 100_000
        assert config.max_retries == 3
        assert config.retry_delay_seconds == 1.0

    def test_config_accepts_custom_values(self) -> None:
        """Test that config accepts custom values."""
        config = DiscoveryConfig(
            prd_model="custom-model",
            max_tokens=4096,
            temperature=0.5,
            enable_rlm=False,
        )

        assert config.prd_model == "custom-model"
        assert config.max_tokens == 4096
        assert config.temperature == 0.5
        assert config.enable_rlm is False

    def test_config_validates_max_tokens_minimum(self) -> None:
        """Test that max_tokens has minimum validation."""
        with pytest.raises(ConfigValidationError) as exc_info:
            DiscoveryConfig(max_tokens=50)

        assert "max_tokens must be at least 100" in str(exc_info.value)

    def test_config_validates_temperature_range(self) -> None:
        """Test that temperature has range validation."""
        with pytest.raises(ConfigValidationError) as exc_info:
            DiscoveryConfig(temperature=2.5)

        assert "temperature must be between 0 and 2" in str(exc_info.value)

        with pytest.raises(ConfigValidationError):
            DiscoveryConfig(temperature=-0.1)

    def test_config_validates_max_retries_non_negative(self) -> None:
        """Test that max_retries must be non-negative."""
        with pytest.raises(ConfigValidationError) as exc_info:
            DiscoveryConfig(max_retries=-1)

        assert "max_retries must be non-negative" in str(exc_info.value)

    def test_config_validates_rlm_context_threshold(self) -> None:
        """Test that rlm_context_threshold has minimum validation."""
        with pytest.raises(ConfigValidationError) as exc_info:
            DiscoveryConfig(rlm_context_threshold=500)

        assert "rlm_context_threshold must be at least 1000" in str(exc_info.value)

    def test_config_validates_retry_delay_non_negative(self) -> None:
        """Test that retry_delay_seconds must be non-negative."""
        with pytest.raises(ConfigValidationError) as exc_info:
            DiscoveryConfig(retry_delay_seconds=-1.0)

        assert "retry_delay_seconds must be non-negative" in str(exc_info.value)


class TestDiscoveryConfigFromEnv:
    """Tests for DiscoveryConfig.from_env()."""

    def test_from_env_returns_defaults_without_env_vars(self) -> None:
        """Test that from_env returns defaults when no env vars are set."""
        with patch.dict(os.environ, {}, clear=True):
            config = DiscoveryConfig.from_env()

        assert config.prd_model == "claude-sonnet-4-20250514"
        assert config.max_tokens == 8192

    def test_from_env_reads_model_from_env(self) -> None:
        """Test that from_env reads model from environment."""
        with patch.dict(os.environ, {"DISCOVERY_PRD_MODEL": "test-model"}):
            config = DiscoveryConfig.from_env()

        assert config.prd_model == "test-model"

    def test_from_env_reads_max_tokens_from_env(self) -> None:
        """Test that from_env reads max_tokens from environment."""
        with patch.dict(os.environ, {"DISCOVERY_MAX_TOKENS": "4096"}):
            config = DiscoveryConfig.from_env()

        assert config.max_tokens == 4096

    def test_from_env_reads_temperature_from_env(self) -> None:
        """Test that from_env reads temperature from environment."""
        with patch.dict(os.environ, {"DISCOVERY_TEMPERATURE": "0.7"}):
            config = DiscoveryConfig.from_env()

        assert config.temperature == 0.7

    def test_from_env_reads_artifact_path_from_env(self) -> None:
        """Test that from_env reads artifact path from environment."""
        with patch.dict(os.environ, {"DISCOVERY_ARTIFACT_PATH": "/custom/path"}):
            config = DiscoveryConfig.from_env()

        assert config.artifact_base_path == Path("/custom/path")

    def test_from_env_reads_enable_rlm_from_env(self) -> None:
        """Test that from_env reads enable_rlm from environment."""
        with patch.dict(os.environ, {"DISCOVERY_ENABLE_RLM": "false"}):
            config = DiscoveryConfig.from_env()

        assert config.enable_rlm is False

        with patch.dict(os.environ, {"DISCOVERY_ENABLE_RLM": "true"}):
            config = DiscoveryConfig.from_env()

        assert config.enable_rlm is True

    def test_from_env_reads_rlm_threshold_from_env(self) -> None:
        """Test that from_env reads RLM threshold from environment."""
        with patch.dict(os.environ, {"DISCOVERY_RLM_THRESHOLD": "50000"}):
            config = DiscoveryConfig.from_env()

        assert config.rlm_context_threshold == 50000


class TestDiscoveryConfigToDict:
    """Tests for DiscoveryConfig.to_dict()."""

    def test_to_dict_serializes_all_fields(self) -> None:
        """Test that to_dict serializes all fields."""
        config = DiscoveryConfig(
            prd_model="test-model",
            acceptance_model="test-acceptance-model",
            max_tokens=4096,
            temperature=0.5,
            artifact_base_path=Path("/test/path"),
            enable_rlm=False,
            rlm_context_threshold=50000,
            max_retries=5,
            retry_delay_seconds=2.0,
        )

        result = config.to_dict()

        assert result["prd_model"] == "test-model"
        assert result["acceptance_model"] == "test-acceptance-model"
        assert result["max_tokens"] == 4096
        assert result["temperature"] == 0.5
        assert result["artifact_base_path"] == "/test/path"
        assert result["enable_rlm"] is False
        assert result["rlm_context_threshold"] == 50000
        assert result["max_retries"] == 5
        assert result["retry_delay_seconds"] == 2.0


class TestDiscoveryConfigWithOverrides:
    """Tests for DiscoveryConfig.with_overrides()."""

    def test_with_overrides_creates_new_config(self) -> None:
        """Test that with_overrides creates a new config."""
        original = DiscoveryConfig()
        modified = original.with_overrides(max_tokens=4096)

        assert original.max_tokens == 8192  # Original unchanged
        assert modified.max_tokens == 4096  # New config has override

    def test_with_overrides_preserves_unmodified_values(self) -> None:
        """Test that with_overrides preserves unmodified values."""
        original = DiscoveryConfig(temperature=0.5)
        modified = original.with_overrides(max_tokens=4096)

        assert modified.temperature == 0.5  # Preserved
        assert modified.max_tokens == 4096  # Overridden

    def test_with_overrides_handles_path_conversion(self) -> None:
        """Test that with_overrides handles path string conversion."""
        original = DiscoveryConfig()
        modified = original.with_overrides(artifact_base_path="/new/path")

        assert modified.artifact_base_path == Path("/new/path")

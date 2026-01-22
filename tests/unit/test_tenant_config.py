"""Tests for tenant configuration (P06-F05)."""

from __future__ import annotations

import os
from unittest import mock

import pytest

from src.core.config import TenantConfig, clear_config_cache, get_tenant_config


class TestTenantConfig:
    """Test the TenantConfig dataclass."""

    def test_default_values(self) -> None:
        """Test TenantConfig has sensible defaults."""
        config = TenantConfig()

        assert config.enabled is False
        assert config.default_tenant == "default"
        assert config.allowed_tenants == ("*",)
        assert config.tenant_header == "X-Tenant-ID"

    def test_custom_values(self) -> None:
        """Test TenantConfig with custom values."""
        config = TenantConfig(
            enabled=True,
            default_tenant="acme-corp",
            allowed_tenants=("acme-corp", "widgets-inc"),
            tenant_header="X-Organization-ID",
        )

        assert config.enabled is True
        assert config.default_tenant == "acme-corp"
        assert config.allowed_tenants == ("acme-corp", "widgets-inc")
        assert config.tenant_header == "X-Organization-ID"


class TestTenantConfigFromEnv:
    """Test TenantConfig.from_env() method."""

    def setup_method(self) -> None:
        """Clear config cache before each test."""
        clear_config_cache()

    def teardown_method(self) -> None:
        """Clear config cache after each test."""
        clear_config_cache()

    def test_from_env_defaults(self) -> None:
        """Test from_env with no environment variables."""
        with mock.patch.dict(os.environ, {}, clear=True):
            config = TenantConfig.from_env()

        assert config.enabled is False
        assert config.default_tenant == "default"
        assert config.allowed_tenants == ("*",)

    def test_from_env_enabled_true(self) -> None:
        """Test MULTI_TENANCY_ENABLED=true."""
        env = {"MULTI_TENANCY_ENABLED": "true"}
        with mock.patch.dict(os.environ, env, clear=True):
            config = TenantConfig.from_env()

        assert config.enabled is True

    def test_from_env_enabled_yes(self) -> None:
        """Test MULTI_TENANCY_ENABLED=yes."""
        env = {"MULTI_TENANCY_ENABLED": "yes"}
        with mock.patch.dict(os.environ, env, clear=True):
            config = TenantConfig.from_env()

        assert config.enabled is True

    def test_from_env_enabled_1(self) -> None:
        """Test MULTI_TENANCY_ENABLED=1."""
        env = {"MULTI_TENANCY_ENABLED": "1"}
        with mock.patch.dict(os.environ, env, clear=True):
            config = TenantConfig.from_env()

        assert config.enabled is True

    def test_from_env_enabled_false(self) -> None:
        """Test MULTI_TENANCY_ENABLED=false."""
        env = {"MULTI_TENANCY_ENABLED": "false"}
        with mock.patch.dict(os.environ, env, clear=True):
            config = TenantConfig.from_env()

        assert config.enabled is False

    def test_from_env_default_tenant(self) -> None:
        """Test DEFAULT_TENANT_ID environment variable."""
        env = {"DEFAULT_TENANT_ID": "my-org"}
        with mock.patch.dict(os.environ, env, clear=True):
            config = TenantConfig.from_env()

        assert config.default_tenant == "my-org"

    def test_from_env_allowed_tenants_single(self) -> None:
        """Test ALLOWED_TENANTS with single tenant."""
        env = {"ALLOWED_TENANTS": "acme-corp"}
        with mock.patch.dict(os.environ, env, clear=True):
            config = TenantConfig.from_env()

        assert config.allowed_tenants == ("acme-corp",)

    def test_from_env_allowed_tenants_multiple(self) -> None:
        """Test ALLOWED_TENANTS with multiple tenants."""
        env = {"ALLOWED_TENANTS": "acme-corp,widgets-inc,demo-tenant"}
        with mock.patch.dict(os.environ, env, clear=True):
            config = TenantConfig.from_env()

        assert config.allowed_tenants == ("acme-corp", "widgets-inc", "demo-tenant")

    def test_from_env_allowed_tenants_with_spaces(self) -> None:
        """Test ALLOWED_TENANTS with spaces around commas."""
        env = {"ALLOWED_TENANTS": "tenant-a , tenant-b , tenant-c"}
        with mock.patch.dict(os.environ, env, clear=True):
            config = TenantConfig.from_env()

        assert config.allowed_tenants == ("tenant-a", "tenant-b", "tenant-c")

    def test_from_env_allowed_tenants_wildcard(self) -> None:
        """Test ALLOWED_TENANTS with wildcard."""
        env = {"ALLOWED_TENANTS": "*"}
        with mock.patch.dict(os.environ, env, clear=True):
            config = TenantConfig.from_env()

        assert config.allowed_tenants == ("*",)

    def test_from_env_tenant_header(self) -> None:
        """Test TENANT_HEADER environment variable."""
        env = {"TENANT_HEADER": "X-Organization-ID"}
        with mock.patch.dict(os.environ, env, clear=True):
            config = TenantConfig.from_env()

        assert config.tenant_header == "X-Organization-ID"

    def test_from_env_full_config(self) -> None:
        """Test from_env with all environment variables set."""
        env = {
            "MULTI_TENANCY_ENABLED": "true",
            "DEFAULT_TENANT_ID": "production-org",
            "ALLOWED_TENANTS": "org-a,org-b,org-c",
            "TENANT_HEADER": "X-Org-Header",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            config = TenantConfig.from_env()

        assert config.enabled is True
        assert config.default_tenant == "production-org"
        assert config.allowed_tenants == ("org-a", "org-b", "org-c")
        assert config.tenant_header == "X-Org-Header"


class TestGetTenantConfig:
    """Test the get_tenant_config function."""

    def setup_method(self) -> None:
        """Clear config cache before each test."""
        clear_config_cache()

    def teardown_method(self) -> None:
        """Clear config cache after each test."""
        clear_config_cache()

    def test_get_tenant_config_returns_tenant_config(self) -> None:
        """Test that get_tenant_config returns TenantConfig instance."""
        config = get_tenant_config()
        assert isinstance(config, TenantConfig)

    def test_get_tenant_config_is_cached(self) -> None:
        """Test that get_tenant_config returns cached instance."""
        config1 = get_tenant_config()
        config2 = get_tenant_config()
        assert config1 is config2

    def test_clear_config_cache_clears_tenant_config(self) -> None:
        """Test that clear_config_cache clears tenant config cache."""
        with mock.patch.dict(os.environ, {"DEFAULT_TENANT_ID": "first"}, clear=True):
            config1 = get_tenant_config()

        clear_config_cache()

        with mock.patch.dict(os.environ, {"DEFAULT_TENANT_ID": "second"}, clear=True):
            config2 = get_tenant_config()

        # After clearing cache, new config should be loaded
        assert config2.default_tenant == "second"


class TestTenantConfigImmutability:
    """Test that TenantConfig is immutable."""

    def test_tenant_config_is_frozen(self) -> None:
        """Test that TenantConfig cannot be modified."""
        config = TenantConfig()

        with pytest.raises(AttributeError):
            config.enabled = True  # type: ignore[misc]

        with pytest.raises(AttributeError):
            config.default_tenant = "new-tenant"  # type: ignore[misc]

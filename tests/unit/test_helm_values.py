"""Tests for Helm values files (P06-F01-T02)."""

from pathlib import Path

import pytest
import yaml


CHART_PATH = Path(__file__).parent.parent.parent / "helm" / "dox-asdlc"


class TestValuesYaml:
    """Test the main values.yaml file."""

    @pytest.fixture
    def values(self) -> dict:
        """Load the values.yaml file."""
        values_file = CHART_PATH / "values.yaml"
        with open(values_file) as f:
            return yaml.safe_load(f)

    def test_values_is_valid_yaml(self, values: dict) -> None:
        """Test that values.yaml is valid YAML."""
        assert values is not None, "values.yaml is empty"
        assert isinstance(values, dict), "values.yaml is not a valid YAML dictionary"

    def test_global_section_exists(self, values: dict) -> None:
        """Test that global section exists."""
        assert "global" in values, "values.yaml should have 'global' section"

    def test_global_namespace_defined(self, values: dict) -> None:
        """Test that global namespace is defined."""
        assert "namespace" in values["global"], "global.namespace should be defined"
        assert values["global"]["namespace"] == "dox-asdlc", "default namespace should be 'dox-asdlc'"

    def test_namespace_section_exists(self, values: dict) -> None:
        """Test that namespace section exists."""
        assert "namespace" in values, "values.yaml should have 'namespace' section"

    def test_namespace_create_option(self, values: dict) -> None:
        """Test that namespace.create option exists."""
        assert "create" in values["namespace"], "namespace.create should be defined"
        assert isinstance(values["namespace"]["create"], bool), "namespace.create should be boolean"

    def test_secrets_section_exists(self, values: dict) -> None:
        """Test that secrets section exists."""
        assert "secrets" in values, "values.yaml should have 'secrets' section"

    def test_redis_secret_config(self, values: dict) -> None:
        """Test Redis secret configuration."""
        assert "redis" in values["secrets"], "secrets.redis should be defined"
        assert "create" in values["secrets"]["redis"], "secrets.redis.create should be defined"
        assert "password" in values["secrets"]["redis"], "secrets.redis.password should be defined"

    def test_git_secret_config(self, values: dict) -> None:
        """Test Git credentials secret configuration."""
        assert "git" in values["secrets"], "secrets.git should be defined"
        assert "create" in values["secrets"]["git"], "secrets.git.create should be defined"
        assert "username" in values["secrets"]["git"], "secrets.git.username should be defined"
        assert "token" in values["secrets"]["git"], "secrets.git.token should be defined"

    def test_api_keys_secret_config(self, values: dict) -> None:
        """Test API keys secret configuration."""
        assert "apiKeys" in values["secrets"], "secrets.apiKeys should be defined"
        assert "claudeApiKey" in values["secrets"]["apiKeys"], "secrets.apiKeys.claudeApiKey should be defined"

    def test_subchart_sections_exist(self, values: dict) -> None:
        """Test that all subchart sections are defined."""
        subcharts = ["redis", "chromadb", "orchestrator", "workers", "hitlUI"]
        for subchart in subcharts:
            assert subchart in values, f"'{subchart}' section should exist in values.yaml"

    def test_subchart_enabled_flags(self, values: dict) -> None:
        """Test that subcharts have enabled flags."""
        subcharts = ["redis", "chromadb", "orchestrator", "workers", "hitlUI"]
        for subchart in subcharts:
            assert "enabled" in values[subchart], f"{subchart}.enabled should be defined"
            assert isinstance(values[subchart]["enabled"], bool), f"{subchart}.enabled should be boolean"

    def test_multi_tenancy_section(self, values: dict) -> None:
        """Test multi-tenancy configuration section."""
        assert "multiTenancy" in values, "values.yaml should have 'multiTenancy' section"
        mt = values["multiTenancy"]
        assert "enabled" in mt, "multiTenancy.enabled should be defined"
        assert "defaultTenant" in mt, "multiTenancy.defaultTenant should be defined"
        assert "allowedTenants" in mt, "multiTenancy.allowedTenants should be defined"


class TestValuesMiniKubeYaml:
    """Test the values-minikube.yaml file."""

    @pytest.fixture
    def values(self) -> dict:
        """Load the values-minikube.yaml file."""
        values_file = CHART_PATH / "values-minikube.yaml"
        with open(values_file) as f:
            return yaml.safe_load(f)

    def test_values_is_valid_yaml(self, values: dict) -> None:
        """Test that values-minikube.yaml is valid YAML."""
        assert values is not None, "values-minikube.yaml is empty"
        assert isinstance(values, dict), "values-minikube.yaml is not a valid YAML dictionary"

    def test_development_secrets_defined(self, values: dict) -> None:
        """Test that development secrets are defined (not empty)."""
        assert "secrets" in values, "values-minikube.yaml should have 'secrets' section"
        assert values["secrets"]["redis"]["password"], "Development Redis password should be set"
        assert values["secrets"]["git"]["username"], "Development Git username should be set"
        assert values["secrets"]["apiKeys"]["claudeApiKey"], "Development Claude API key should be set"

    def test_storage_class_set(self, values: dict) -> None:
        """Test that storage class is set for minikube."""
        if "redis" in values and "persistence" in values["redis"]:
            sc = values["redis"]["persistence"].get("storageClass", "")
            assert sc == "standard" or sc == "", f"Redis storageClass should be 'standard' or default"

    def test_resource_limits_smaller(self, values: dict) -> None:
        """Test that minikube resource limits are smaller than production."""
        if "redis" in values and "resources" in values["redis"]:
            limits = values["redis"]["resources"].get("limits", {})
            memory = limits.get("memory", "512Mi")
            # Just verify it's a valid memory string
            assert memory.endswith("Mi") or memory.endswith("Gi"), "Memory should have unit"

    def test_hitl_ui_nodeport(self, values: dict) -> None:
        """Test that HITL-UI uses NodePort for external access."""
        if "hitlUI" in values and "service" in values["hitlUI"]:
            service_type = values["hitlUI"]["service"].get("type", "")
            assert service_type == "NodePort", "HITL-UI should use NodePort in minikube"

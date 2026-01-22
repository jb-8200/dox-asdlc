"""Tests for Redis subchart (P06-F02)."""

from pathlib import Path

import pytest
import yaml


CHART_PATH = Path(__file__).parent.parent.parent / "helm" / "dox-asdlc" / "charts" / "redis"


class TestRedisChartStructure:
    """Test that the Redis chart structure is correct."""

    def test_chart_yaml_exists(self) -> None:
        """Test that Chart.yaml exists."""
        chart_file = CHART_PATH / "Chart.yaml"
        assert chart_file.exists(), f"Chart.yaml not found at {chart_file}"

    def test_chart_yaml_valid(self) -> None:
        """Test that Chart.yaml is valid YAML."""
        chart_file = CHART_PATH / "Chart.yaml"
        with open(chart_file) as f:
            chart = yaml.safe_load(f)

        assert chart is not None, "Chart.yaml is empty"
        assert chart["name"] == "redis", "Chart name should be 'redis'"
        assert chart["apiVersion"] == "v2", "Chart should use API version v2"

    def test_values_yaml_exists(self) -> None:
        """Test that values.yaml exists."""
        values_file = CHART_PATH / "values.yaml"
        assert values_file.exists(), f"values.yaml not found at {values_file}"

    def test_templates_directory_exists(self) -> None:
        """Test that templates directory exists."""
        templates_dir = CHART_PATH / "templates"
        assert templates_dir.is_dir(), f"templates directory not found at {templates_dir}"

    def test_required_templates_exist(self) -> None:
        """Test that required templates exist."""
        templates_dir = CHART_PATH / "templates"
        required_templates = [
            "statefulset.yaml",
            "service.yaml",
            "configmap.yaml",
            "_helpers.tpl",
        ]
        for template in required_templates:
            template_file = templates_dir / template
            assert template_file.exists(), f"Template not found: {template}"


class TestRedisValues:
    """Test the Redis values file."""

    @pytest.fixture
    def values(self) -> dict:
        """Load the values.yaml file."""
        values_file = CHART_PATH / "values.yaml"
        with open(values_file) as f:
            return yaml.safe_load(f)

    def test_enabled_flag_exists(self, values: dict) -> None:
        """Test that enabled flag exists."""
        assert "enabled" in values, "values.yaml should have 'enabled' flag"
        assert isinstance(values["enabled"], bool), "enabled should be boolean"

    def test_replicas_defined(self, values: dict) -> None:
        """Test that replicas is defined."""
        assert "replicas" in values, "values.yaml should have 'replicas'"
        assert values["replicas"] == 1, "Default replicas should be 1"

    def test_image_configuration(self, values: dict) -> None:
        """Test image configuration."""
        assert "image" in values, "values.yaml should have 'image' section"
        assert "repository" in values["image"], "image.repository should be defined"
        assert "tag" in values["image"], "image.tag should be defined"
        assert "redis" in values["image"]["repository"], "Should use redis image"

    def test_persistence_configuration(self, values: dict) -> None:
        """Test persistence configuration."""
        assert "persistence" in values, "values.yaml should have 'persistence' section"
        assert "enabled" in values["persistence"], "persistence.enabled should be defined"
        assert "size" in values["persistence"], "persistence.size should be defined"

    def test_auth_configuration(self, values: dict) -> None:
        """Test authentication configuration."""
        assert "auth" in values, "values.yaml should have 'auth' section"
        assert "enabled" in values["auth"], "auth.enabled should be defined"

    def test_resource_limits(self, values: dict) -> None:
        """Test resource limits are defined."""
        assert "resources" in values, "values.yaml should have 'resources' section"
        assert "requests" in values["resources"], "resources.requests should be defined"
        assert "limits" in values["resources"], "resources.limits should be defined"

    def test_service_configuration(self, values: dict) -> None:
        """Test service configuration."""
        assert "service" in values, "values.yaml should have 'service' section"
        assert "type" in values["service"], "service.type should be defined"
        assert "port" in values["service"], "service.port should be defined"
        assert values["service"]["port"] == 6379, "Redis port should be 6379"

    def test_probe_configuration(self, values: dict) -> None:
        """Test probe configuration."""
        assert "livenessProbe" in values, "values.yaml should have 'livenessProbe'"
        assert "readinessProbe" in values, "values.yaml should have 'readinessProbe'"


class TestRedisStatefulSetTemplate:
    """Test the Redis StatefulSet template."""

    def test_statefulset_template_exists(self) -> None:
        """Test that statefulset.yaml exists."""
        template_file = CHART_PATH / "templates" / "statefulset.yaml"
        assert template_file.exists(), f"statefulset.yaml not found at {template_file}"

    def test_statefulset_has_conditional(self) -> None:
        """Test that StatefulSet has conditional creation."""
        template_file = CHART_PATH / "templates" / "statefulset.yaml"
        content = template_file.read_text()

        assert "if .Values.enabled" in content, "StatefulSet should be conditional"

    def test_statefulset_has_volume_claim_templates(self) -> None:
        """Test that StatefulSet has volumeClaimTemplates for persistence."""
        template_file = CHART_PATH / "templates" / "statefulset.yaml"
        content = template_file.read_text()

        assert "volumeClaimTemplates" in content, "Should have volumeClaimTemplates"

    def test_statefulset_has_config_volume(self) -> None:
        """Test that StatefulSet mounts config volume."""
        template_file = CHART_PATH / "templates" / "statefulset.yaml"
        content = template_file.read_text()

        assert "configMap" in content, "Should mount ConfigMap"
        assert "/etc/redis" in content, "Should mount config at /etc/redis"

    def test_statefulset_has_probes(self) -> None:
        """Test that StatefulSet has liveness and readiness probes."""
        template_file = CHART_PATH / "templates" / "statefulset.yaml"
        content = template_file.read_text()

        assert "livenessProbe" in content, "Should have livenessProbe"
        assert "readinessProbe" in content, "Should have readinessProbe"

    def test_statefulset_auth_support(self) -> None:
        """Test that StatefulSet supports authentication."""
        template_file = CHART_PATH / "templates" / "statefulset.yaml"
        content = template_file.read_text()

        assert "REDIS_PASSWORD" in content, "Should support REDIS_PASSWORD"
        assert "requirepass" in content, "Should use requirepass"


class TestRedisServiceTemplate:
    """Test the Redis Service template."""

    def test_service_template_exists(self) -> None:
        """Test that service.yaml exists."""
        template_file = CHART_PATH / "templates" / "service.yaml"
        assert template_file.exists(), f"service.yaml not found at {template_file}"

    def test_service_has_conditional(self) -> None:
        """Test that Service has conditional creation."""
        template_file = CHART_PATH / "templates" / "service.yaml"
        content = template_file.read_text()

        assert "if .Values.enabled" in content, "Service should be conditional"

    def test_service_exposes_redis_port(self) -> None:
        """Test that Service exposes Redis port."""
        template_file = CHART_PATH / "templates" / "service.yaml"
        content = template_file.read_text()

        assert "port:" in content, "Should define port"
        assert "targetPort:" in content, "Should define targetPort"


class TestRedisConfigMapTemplate:
    """Test the Redis ConfigMap template."""

    def test_configmap_template_exists(self) -> None:
        """Test that configmap.yaml exists."""
        template_file = CHART_PATH / "templates" / "configmap.yaml"
        assert template_file.exists(), f"configmap.yaml not found at {template_file}"

    def test_configmap_has_redis_conf(self) -> None:
        """Test that ConfigMap contains redis.conf."""
        template_file = CHART_PATH / "templates" / "configmap.yaml"
        content = template_file.read_text()

        assert "redis.conf" in content, "Should define redis.conf"

    def test_configmap_has_persistence_config(self) -> None:
        """Test that ConfigMap has persistence configuration."""
        template_file = CHART_PATH / "templates" / "configmap.yaml"
        content = template_file.read_text()

        assert "appendonly" in content, "Should have AOF config"
        assert "save" in content, "Should have RDB config"

    def test_configmap_binds_to_all_interfaces(self) -> None:
        """Test that Redis binds to all interfaces for pod networking."""
        template_file = CHART_PATH / "templates" / "configmap.yaml"
        content = template_file.read_text()

        assert "bind 0.0.0.0" in content, "Should bind to 0.0.0.0"


class TestRedisHelpers:
    """Test the Redis helpers template."""

    @pytest.fixture
    def helpers_content(self) -> str:
        """Load the _helpers.tpl file content."""
        helpers_file = CHART_PATH / "templates" / "_helpers.tpl"
        return helpers_file.read_text()

    def test_helpers_file_exists(self) -> None:
        """Test that _helpers.tpl exists."""
        helpers_file = CHART_PATH / "templates" / "_helpers.tpl"
        assert helpers_file.exists(), f"_helpers.tpl not found at {helpers_file}"

    def test_name_helper_defined(self, helpers_content: str) -> None:
        """Test that redis.name helper is defined."""
        assert 'define "redis.name"' in helpers_content, "Should define redis.name"

    def test_fullname_helper_defined(self, helpers_content: str) -> None:
        """Test that redis.fullname helper is defined."""
        assert 'define "redis.fullname"' in helpers_content, "Should define redis.fullname"

    def test_labels_helper_defined(self, helpers_content: str) -> None:
        """Test that redis.labels helper is defined."""
        assert 'define "redis.labels"' in helpers_content, "Should define redis.labels"

    def test_selector_labels_helper_defined(self, helpers_content: str) -> None:
        """Test that redis.selectorLabels helper is defined."""
        assert 'define "redis.selectorLabels"' in helpers_content, "Should define redis.selectorLabels"

    def test_parent_fullname_helper_defined(self, helpers_content: str) -> None:
        """Test that redis.parentFullname helper is defined for accessing parent secrets."""
        assert 'define "redis.parentFullname"' in helpers_content, \
            "Should define redis.parentFullname for parent chart integration"

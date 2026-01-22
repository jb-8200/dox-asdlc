"""Tests for HITL-UI subchart (P06-F04)."""

from pathlib import Path

import pytest
import yaml


CHART_PATH = Path(__file__).parent.parent.parent / "helm" / "dox-asdlc" / "charts" / "hitl-ui"


class TestHitlUIChartStructure:
    """Test that the HITL-UI chart structure is correct."""

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
        assert chart["name"] == "hitl-ui", "Chart name should be 'hitl-ui'"
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
            "deployment.yaml",
            "service.yaml",
            "configmap.yaml",
            "_helpers.tpl",
        ]
        for template in required_templates:
            template_file = templates_dir / template
            assert template_file.exists(), f"Template not found: {template}"


class TestHitlUIValues:
    """Test the HITL-UI values file."""

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
        assert "hitl-ui" in values["image"]["repository"], "Should use hitl-ui image"

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
        assert values["service"]["type"] == "NodePort", "HITL-UI service should be NodePort for external access"
        assert values["service"]["port"] == 3000, "HITL-UI should use port 3000"

    def test_nodeport_configured(self, values: dict) -> None:
        """Test that NodePort is configured for external access."""
        assert "nodePort" in values["service"], "service.nodePort should be defined"
        nodeport = values["service"]["nodePort"]
        assert 30000 <= nodeport <= 32767, "NodePort should be in valid range (30000-32767)"

    def test_probe_configuration(self, values: dict) -> None:
        """Test probe configuration."""
        assert "livenessProbe" in values, "values.yaml should have 'livenessProbe'"
        assert "readinessProbe" in values, "values.yaml should have 'readinessProbe'"
        assert values["livenessProbe"]["path"] == "/health", "livenessProbe should use /health"
        assert values["readinessProbe"]["path"] == "/health", "readinessProbe should use /health"

    def test_env_configuration(self, values: dict) -> None:
        """Test environment configuration."""
        assert "env" in values, "values.yaml should have 'env' section"
        assert "REDIS_URL" in values["env"], "env should have REDIS_URL"
        assert "API_BASE_URL" in values["env"], "env should have API_BASE_URL for orchestrator"

    def test_env_has_node_env(self, values: dict) -> None:
        """Test that NODE_ENV is configured for Node.js app."""
        assert "NODE_ENV" in values["env"], "env should have NODE_ENV"


class TestHitlUIDeploymentTemplate:
    """Test the HITL-UI Deployment template."""

    def test_deployment_template_exists(self) -> None:
        """Test that deployment.yaml exists."""
        template_file = CHART_PATH / "templates" / "deployment.yaml"
        assert template_file.exists(), f"deployment.yaml not found at {template_file}"

    def test_deployment_has_conditional(self) -> None:
        """Test that Deployment has conditional creation."""
        template_file = CHART_PATH / "templates" / "deployment.yaml"
        content = template_file.read_text()

        assert "if .Values.enabled" in content, "Deployment should be conditional"

    def test_deployment_kind_is_deployment(self) -> None:
        """Test that kind is Deployment (not StatefulSet)."""
        template_file = CHART_PATH / "templates" / "deployment.yaml"
        content = template_file.read_text()

        assert "kind: Deployment" in content, "Should be Deployment (stateless)"

    def test_deployment_has_probes(self) -> None:
        """Test that Deployment has liveness and readiness probes."""
        template_file = CHART_PATH / "templates" / "deployment.yaml"
        content = template_file.read_text()

        assert "livenessProbe" in content, "Should have livenessProbe"
        assert "readinessProbe" in content, "Should have readinessProbe"

    def test_deployment_has_configmap_ref(self) -> None:
        """Test that Deployment references ConfigMap."""
        template_file = CHART_PATH / "templates" / "deployment.yaml"
        content = template_file.read_text()

        assert "configMapRef" in content, "Should reference ConfigMap for env vars"

    def test_deployment_has_redis_password_secret(self) -> None:
        """Test that Deployment injects Redis password from secret."""
        template_file = CHART_PATH / "templates" / "deployment.yaml"
        content = template_file.read_text()

        assert "REDIS_PASSWORD" in content, "Should inject REDIS_PASSWORD from secret"
        assert "secretKeyRef" in content, "Should use secretKeyRef"

    def test_deployment_has_resources(self) -> None:
        """Test that Deployment has resource limits."""
        template_file = CHART_PATH / "templates" / "deployment.yaml"
        content = template_file.read_text()

        assert "resources:" in content, "Should have resources section"


class TestHitlUIServiceTemplate:
    """Test the HITL-UI Service template."""

    def test_service_template_exists(self) -> None:
        """Test that service.yaml exists."""
        template_file = CHART_PATH / "templates" / "service.yaml"
        assert template_file.exists(), f"service.yaml not found at {template_file}"

    def test_service_has_conditional(self) -> None:
        """Test that Service has conditional creation."""
        template_file = CHART_PATH / "templates" / "service.yaml"
        content = template_file.read_text()

        assert "if .Values.enabled" in content, "Service should be conditional"

    def test_service_exposes_http_port(self) -> None:
        """Test that Service exposes HTTP port."""
        template_file = CHART_PATH / "templates" / "service.yaml"
        content = template_file.read_text()

        assert "port:" in content, "Should define port"
        assert "targetPort:" in content, "Should define targetPort"
        assert "name: http" in content, "Should name port 'http'"

    def test_service_supports_nodeport(self) -> None:
        """Test that Service supports NodePort configuration."""
        template_file = CHART_PATH / "templates" / "service.yaml"
        content = template_file.read_text()

        assert "NodePort" in content, "Should support NodePort type"
        assert "nodePort" in content, "Should support nodePort configuration"


class TestHitlUIConfigMapTemplate:
    """Test the HITL-UI ConfigMap template."""

    def test_configmap_template_exists(self) -> None:
        """Test that configmap.yaml exists."""
        template_file = CHART_PATH / "templates" / "configmap.yaml"
        assert template_file.exists(), f"configmap.yaml not found at {template_file}"

    def test_configmap_has_conditional(self) -> None:
        """Test that ConfigMap has conditional creation."""
        template_file = CHART_PATH / "templates" / "configmap.yaml"
        content = template_file.read_text()

        assert "if .Values.enabled" in content, "ConfigMap should be conditional"


class TestHitlUIHelpers:
    """Test the HITL-UI helpers template."""

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
        """Test that hitl-ui.name helper is defined."""
        assert 'define "hitl-ui.name"' in helpers_content, "Should define hitl-ui.name"

    def test_fullname_helper_defined(self, helpers_content: str) -> None:
        """Test that hitl-ui.fullname helper is defined."""
        assert 'define "hitl-ui.fullname"' in helpers_content, "Should define hitl-ui.fullname"

    def test_labels_helper_defined(self, helpers_content: str) -> None:
        """Test that hitl-ui.labels helper is defined."""
        assert 'define "hitl-ui.labels"' in helpers_content, "Should define hitl-ui.labels"

    def test_selector_labels_helper_defined(self, helpers_content: str) -> None:
        """Test that hitl-ui.selectorLabels helper is defined."""
        assert 'define "hitl-ui.selectorLabels"' in helpers_content, "Should define hitl-ui.selectorLabels"

    def test_parent_fullname_helper_defined(self, helpers_content: str) -> None:
        """Test that hitl-ui.parentFullname helper is defined for accessing parent secrets."""
        assert 'define "hitl-ui.parentFullname"' in helpers_content, \
            "Should define hitl-ui.parentFullname for parent chart integration"

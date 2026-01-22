"""Tests for Workers subchart (P06-F04)."""

from pathlib import Path

import pytest
import yaml


CHART_PATH = Path(__file__).parent.parent.parent / "helm" / "dox-asdlc" / "charts" / "workers"


class TestWorkersChartStructure:
    """Test that the Workers chart structure is correct."""

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
        assert chart["name"] == "workers", "Chart name should be 'workers'"
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
            "hpa.yaml",
            "_helpers.tpl",
        ]
        for template in required_templates:
            template_file = templates_dir / template
            assert template_file.exists(), f"Template not found: {template}"


class TestWorkersValues:
    """Test the Workers values file."""

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

    def test_hpa_configuration(self, values: dict) -> None:
        """Test that HPA configuration is defined."""
        assert "minReplicas" in values, "values.yaml should have 'minReplicas'"
        assert "maxReplicas" in values, "values.yaml should have 'maxReplicas'"
        assert "targetCPUUtilization" in values, "values.yaml should have 'targetCPUUtilization'"
        assert values["minReplicas"] >= 1, "minReplicas should be at least 1"
        assert values["maxReplicas"] > values["minReplicas"], "maxReplicas should be greater than minReplicas"

    def test_image_configuration(self, values: dict) -> None:
        """Test image configuration."""
        assert "image" in values, "values.yaml should have 'image' section"
        assert "repository" in values["image"], "image.repository should be defined"
        assert "tag" in values["image"], "image.tag should be defined"
        assert "workers" in values["image"]["repository"], "Should use workers image"

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
        assert values["service"]["type"] == "ClusterIP", "Workers service should be ClusterIP"

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
        assert "KNOWLEDGE_STORE_URL" in values["env"], "env should have KNOWLEDGE_STORE_URL"


class TestWorkersDeploymentTemplate:
    """Test the Workers Deployment template."""

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

    def test_deployment_uses_min_replicas(self) -> None:
        """Test that Deployment uses minReplicas (HPA manages scaling)."""
        template_file = CHART_PATH / "templates" / "deployment.yaml"
        content = template_file.read_text()

        assert "minReplicas" in content, "Should use minReplicas for initial replica count"

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

    def test_deployment_has_secret_refs(self) -> None:
        """Test that Deployment references secrets for sensitive data."""
        template_file = CHART_PATH / "templates" / "deployment.yaml"
        content = template_file.read_text()

        assert "secretKeyRef" in content, "Should reference secrets"
        assert "REDIS_PASSWORD" in content, "Should inject REDIS_PASSWORD from secret"
        assert "CLAUDE_API_KEY" in content, "Should inject CLAUDE_API_KEY from secret"

    def test_deployment_no_git_credentials(self) -> None:
        """Test that Workers don't have Git credentials (no commit access)."""
        template_file = CHART_PATH / "templates" / "deployment.yaml"
        content = template_file.read_text()

        # Workers should NOT mount git credentials - only orchestrator has commit access
        assert "git-credentials" not in content.lower() or "gitcredentials" not in content.lower(), \
            "Workers should not have git credentials (governance principle)"

    def test_deployment_has_resources(self) -> None:
        """Test that Deployment has resource limits."""
        template_file = CHART_PATH / "templates" / "deployment.yaml"
        content = template_file.read_text()

        assert "resources:" in content, "Should have resources section"


class TestWorkersHPATemplate:
    """Test the Workers HPA template."""

    def test_hpa_template_exists(self) -> None:
        """Test that hpa.yaml exists."""
        template_file = CHART_PATH / "templates" / "hpa.yaml"
        assert template_file.exists(), f"hpa.yaml not found at {template_file}"

    def test_hpa_has_conditional(self) -> None:
        """Test that HPA has conditional creation."""
        template_file = CHART_PATH / "templates" / "hpa.yaml"
        content = template_file.read_text()

        assert "if .Values.enabled" in content, "HPA should be conditional"

    def test_hpa_targets_deployment(self) -> None:
        """Test that HPA targets the correct Deployment."""
        template_file = CHART_PATH / "templates" / "hpa.yaml"
        content = template_file.read_text()

        assert "scaleTargetRef" in content, "Should have scaleTargetRef"
        assert "kind: Deployment" in content, "Should target Deployment"

    def test_hpa_has_min_max_replicas(self) -> None:
        """Test that HPA has min and max replicas."""
        template_file = CHART_PATH / "templates" / "hpa.yaml"
        content = template_file.read_text()

        assert "minReplicas" in content, "Should have minReplicas"
        assert "maxReplicas" in content, "Should have maxReplicas"

    def test_hpa_has_cpu_metric(self) -> None:
        """Test that HPA uses CPU metric."""
        template_file = CHART_PATH / "templates" / "hpa.yaml"
        content = template_file.read_text()

        assert "type: Resource" in content, "Should use Resource metric type"
        assert "name: cpu" in content, "Should target CPU"
        assert "averageUtilization" in content, "Should use averageUtilization"

    def test_hpa_has_scale_behavior(self) -> None:
        """Test that HPA has scaling behavior configuration."""
        template_file = CHART_PATH / "templates" / "hpa.yaml"
        content = template_file.read_text()

        assert "behavior:" in content, "Should have behavior section"
        assert "scaleDown:" in content, "Should have scaleDown behavior"
        assert "scaleUp:" in content, "Should have scaleUp behavior"

    def test_hpa_uses_autoscaling_v2(self) -> None:
        """Test that HPA uses autoscaling/v2 API."""
        template_file = CHART_PATH / "templates" / "hpa.yaml"
        content = template_file.read_text()

        assert "autoscaling/v2" in content, "Should use autoscaling/v2 API"


class TestWorkersServiceTemplate:
    """Test the Workers Service template."""

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


class TestWorkersConfigMapTemplate:
    """Test the Workers ConfigMap template."""

    def test_configmap_template_exists(self) -> None:
        """Test that configmap.yaml exists."""
        template_file = CHART_PATH / "templates" / "configmap.yaml"
        assert template_file.exists(), f"configmap.yaml not found at {template_file}"

    def test_configmap_has_conditional(self) -> None:
        """Test that ConfigMap has conditional creation."""
        template_file = CHART_PATH / "templates" / "configmap.yaml"
        content = template_file.read_text()

        assert "if .Values.enabled" in content, "ConfigMap should be conditional"


class TestWorkersHelpers:
    """Test the Workers helpers template."""

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
        """Test that workers.name helper is defined."""
        assert 'define "workers.name"' in helpers_content, "Should define workers.name"

    def test_fullname_helper_defined(self, helpers_content: str) -> None:
        """Test that workers.fullname helper is defined."""
        assert 'define "workers.fullname"' in helpers_content, "Should define workers.fullname"

    def test_labels_helper_defined(self, helpers_content: str) -> None:
        """Test that workers.labels helper is defined."""
        assert 'define "workers.labels"' in helpers_content, "Should define workers.labels"

    def test_selector_labels_helper_defined(self, helpers_content: str) -> None:
        """Test that workers.selectorLabels helper is defined."""
        assert 'define "workers.selectorLabels"' in helpers_content, "Should define workers.selectorLabels"

    def test_parent_fullname_helper_defined(self, helpers_content: str) -> None:
        """Test that workers.parentFullname helper is defined for accessing parent secrets."""
        assert 'define "workers.parentFullname"' in helpers_content, \
            "Should define workers.parentFullname for parent chart integration"

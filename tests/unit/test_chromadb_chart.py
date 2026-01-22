"""Tests for ChromaDB subchart (P06-F03)."""

from pathlib import Path

import pytest
import yaml


CHART_PATH = Path(__file__).parent.parent.parent / "helm" / "dox-asdlc" / "charts" / "chromadb"


class TestChromaDBChartStructure:
    """Test that the ChromaDB chart structure is correct."""

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
        assert chart["name"] == "chromadb", "Chart name should be 'chromadb'"
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


class TestChromaDBValues:
    """Test the ChromaDB values file."""

    @pytest.fixture
    def values(self) -> dict:
        """Load the values.yaml file."""
        values_file = CHART_PATH / "values.yaml"
        with open(values_file) as f:
            return yaml.safe_load(f)

    def test_enabled_flag_exists(self, values: dict) -> None:
        """Test that enabled flag exists."""
        assert "enabled" in values, "values.yaml should have 'enabled' flag"

    def test_image_configuration(self, values: dict) -> None:
        """Test image configuration."""
        assert "image" in values, "values.yaml should have 'image' section"
        assert "chromadb" in values["image"]["repository"], "Should use chromadb image"

    def test_persistence_configuration(self, values: dict) -> None:
        """Test persistence configuration."""
        assert "persistence" in values, "values.yaml should have 'persistence' section"
        assert "enabled" in values["persistence"], "persistence.enabled should be defined"
        assert "mountPath" in values["persistence"], "persistence.mountPath should be defined"

    def test_service_configuration(self, values: dict) -> None:
        """Test service configuration."""
        assert "service" in values, "values.yaml should have 'service' section"
        assert "nameOverride" in values["service"], "service.nameOverride should be defined"
        assert values["service"]["nameOverride"] == "knowledge-store", \
            "Service should be named 'knowledge-store' for abstraction"
        assert values["service"]["port"] == 8000, "ChromaDB port should be 8000"

    def test_probe_configuration(self, values: dict) -> None:
        """Test probe configuration uses heartbeat endpoint."""
        assert "livenessProbe" in values, "values.yaml should have 'livenessProbe'"
        assert "readinessProbe" in values, "values.yaml should have 'readinessProbe'"
        assert values["livenessProbe"]["path"] == "/api/v1/heartbeat", \
            "Liveness probe should use heartbeat endpoint"


class TestChromaDBStatefulSetTemplate:
    """Test the ChromaDB StatefulSet template."""

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

    def test_statefulset_has_env_config(self) -> None:
        """Test that StatefulSet has environment configuration."""
        template_file = CHART_PATH / "templates" / "statefulset.yaml"
        content = template_file.read_text()

        assert "CHROMA_SERVER_HOST" in content, "Should configure host"
        assert "CHROMA_SERVER_HTTP_PORT" in content, "Should configure port"
        assert "ANONYMIZED_TELEMETRY" in content, "Should disable telemetry"

    def test_statefulset_has_probes(self) -> None:
        """Test that StatefulSet has liveness and readiness probes."""
        template_file = CHART_PATH / "templates" / "statefulset.yaml"
        content = template_file.read_text()

        assert "livenessProbe" in content, "Should have livenessProbe"
        assert "readinessProbe" in content, "Should have readinessProbe"
        assert "httpGet" in content, "Probes should use httpGet"


class TestChromaDBServiceTemplate:
    """Test the ChromaDB Service template."""

    def test_service_template_exists(self) -> None:
        """Test that service.yaml exists."""
        template_file = CHART_PATH / "templates" / "service.yaml"
        assert template_file.exists(), f"service.yaml not found at {template_file}"

    def test_service_uses_name_override(self) -> None:
        """Test that Service uses name override for abstraction."""
        template_file = CHART_PATH / "templates" / "service.yaml"
        content = template_file.read_text()

        assert "chromadb.serviceName" in content, \
            "Service should use serviceName helper for name override"


class TestChromaDBHelpers:
    """Test the ChromaDB helpers template."""

    @pytest.fixture
    def helpers_content(self) -> str:
        """Load the _helpers.tpl file content."""
        helpers_file = CHART_PATH / "templates" / "_helpers.tpl"
        return helpers_file.read_text()

    def test_helpers_file_exists(self) -> None:
        """Test that _helpers.tpl exists."""
        helpers_file = CHART_PATH / "templates" / "_helpers.tpl"
        assert helpers_file.exists(), f"_helpers.tpl not found at {helpers_file}"

    def test_service_name_helper_defined(self, helpers_content: str) -> None:
        """Test that chromadb.serviceName helper is defined for abstraction."""
        assert 'define "chromadb.serviceName"' in helpers_content, \
            "Should define chromadb.serviceName helper"

    def test_labels_include_component(self, helpers_content: str) -> None:
        """Test that labels include knowledge-store component."""
        assert "knowledge-store" in helpers_content, \
            "Labels should identify this as knowledge-store component"

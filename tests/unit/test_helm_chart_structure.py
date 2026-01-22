"""Tests for Helm chart structure validation (P06-F01-T01)."""

from pathlib import Path

import pytest
import yaml


CHART_PATH = Path(__file__).parent.parent.parent / "helm" / "dox-asdlc"


class TestHelmChartStructure:
    """Test that the Helm chart structure is correct."""

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
        assert isinstance(chart, dict), "Chart.yaml is not a valid YAML dictionary"

    def test_chart_yaml_required_fields(self) -> None:
        """Test that Chart.yaml has all required fields."""
        chart_file = CHART_PATH / "Chart.yaml"
        with open(chart_file) as f:
            chart = yaml.safe_load(f)

        required_fields = ["apiVersion", "name", "version", "description"]
        for field in required_fields:
            assert field in chart, f"Required field '{field}' missing from Chart.yaml"

    def test_chart_api_version(self) -> None:
        """Test that Chart uses API version v2."""
        chart_file = CHART_PATH / "Chart.yaml"
        with open(chart_file) as f:
            chart = yaml.safe_load(f)

        assert chart["apiVersion"] == "v2", "Chart should use API version v2"

    def test_chart_name(self) -> None:
        """Test that chart name is dox-asdlc."""
        chart_file = CHART_PATH / "Chart.yaml"
        with open(chart_file) as f:
            chart = yaml.safe_load(f)

        assert chart["name"] == "dox-asdlc", "Chart name should be 'dox-asdlc'"

    def test_values_yaml_exists(self) -> None:
        """Test that values.yaml exists."""
        values_file = CHART_PATH / "values.yaml"
        assert values_file.exists(), f"values.yaml not found at {values_file}"

    def test_values_minikube_yaml_exists(self) -> None:
        """Test that values-minikube.yaml exists."""
        values_file = CHART_PATH / "values-minikube.yaml"
        assert values_file.exists(), f"values-minikube.yaml not found at {values_file}"

    def test_templates_directory_exists(self) -> None:
        """Test that templates directory exists."""
        templates_dir = CHART_PATH / "templates"
        assert templates_dir.is_dir(), f"templates directory not found at {templates_dir}"

    def test_helpers_tpl_exists(self) -> None:
        """Test that _helpers.tpl exists."""
        helpers_file = CHART_PATH / "templates" / "_helpers.tpl"
        assert helpers_file.exists(), f"_helpers.tpl not found at {helpers_file}"

    def test_charts_directory_exists(self) -> None:
        """Test that charts directory exists for subcharts."""
        charts_dir = CHART_PATH / "charts"
        assert charts_dir.is_dir(), f"charts directory not found at {charts_dir}"


class TestHelmChartMetadata:
    """Test Helm chart metadata."""

    def test_chart_has_maintainers(self) -> None:
        """Test that chart has maintainers defined."""
        chart_file = CHART_PATH / "Chart.yaml"
        with open(chart_file) as f:
            chart = yaml.safe_load(f)

        assert "maintainers" in chart, "Chart should have maintainers"
        assert len(chart["maintainers"]) > 0, "Chart should have at least one maintainer"

    def test_chart_has_app_version(self) -> None:
        """Test that chart has appVersion."""
        chart_file = CHART_PATH / "Chart.yaml"
        with open(chart_file) as f:
            chart = yaml.safe_load(f)

        assert "appVersion" in chart, "Chart should have appVersion"

    def test_chart_version_is_semver(self) -> None:
        """Test that chart version follows semver format."""
        import re

        chart_file = CHART_PATH / "Chart.yaml"
        with open(chart_file) as f:
            chart = yaml.safe_load(f)

        version = chart["version"]
        semver_pattern = r"^\d+\.\d+\.\d+(-[\w.]+)?(\+[\w.]+)?$"
        assert re.match(semver_pattern, version), f"Version '{version}' should follow semver"

"""Tests for namespace template (P06-F01-T03)."""

import subprocess
from pathlib import Path

import pytest
import yaml


CHART_PATH = Path(__file__).parent.parent.parent / "helm" / "dox-asdlc"


class TestNamespaceTemplate:
    """Test the namespace.yaml template."""

    def test_namespace_template_exists(self) -> None:
        """Test that namespace.yaml template exists."""
        template_file = CHART_PATH / "templates" / "namespace.yaml"
        assert template_file.exists(), f"namespace.yaml not found at {template_file}"

    def test_namespace_template_valid_yaml(self) -> None:
        """Test that namespace.yaml is syntactically valid YAML with Go templates."""
        template_file = CHART_PATH / "templates" / "namespace.yaml"
        content = template_file.read_text()

        # Check for basic Kubernetes structure markers
        assert "apiVersion:" in content, "Template should define apiVersion"
        assert "kind: Namespace" in content, "Template should define kind: Namespace"
        assert "metadata:" in content, "Template should have metadata"

    @pytest.mark.skipif(
        subprocess.run(["which", "helm"], capture_output=True).returncode != 0,
        reason="Helm not installed"
    )
    def test_helm_template_renders(self) -> None:
        """Test that helm template command succeeds."""
        result = subprocess.run(
            ["helm", "template", "test-release", str(CHART_PATH),
             "--set", "namespace.create=true"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Helm template failed: {result.stderr}"

    @pytest.mark.skipif(
        subprocess.run(["which", "helm"], capture_output=True).returncode != 0,
        reason="Helm not installed"
    )
    def test_namespace_created_when_enabled(self) -> None:
        """Test that namespace is created when namespace.create=true."""
        result = subprocess.run(
            ["helm", "template", "test-release", str(CHART_PATH),
             "--set", "namespace.create=true"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Helm template failed: {result.stderr}"

        # Parse the output to find Namespace resource
        docs = list(yaml.safe_load_all(result.stdout))
        namespace_docs = [d for d in docs if d and d.get("kind") == "Namespace"]

        assert len(namespace_docs) == 1, "Should create exactly one Namespace"
        assert namespace_docs[0]["metadata"]["name"] == "dox-asdlc", "Namespace name should be 'dox-asdlc'"

    @pytest.mark.skipif(
        subprocess.run(["which", "helm"], capture_output=True).returncode != 0,
        reason="Helm not installed"
    )
    def test_namespace_not_created_when_disabled(self) -> None:
        """Test that namespace is not created when namespace.create=false."""
        result = subprocess.run(
            ["helm", "template", "test-release", str(CHART_PATH),
             "--set", "namespace.create=false"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Helm template failed: {result.stderr}"

        # Parse the output to check for Namespace
        docs = list(yaml.safe_load_all(result.stdout))
        namespace_docs = [d for d in docs if d and d.get("kind") == "Namespace"]

        assert len(namespace_docs) == 0, "Should not create Namespace when disabled"

    @pytest.mark.skipif(
        subprocess.run(["which", "helm"], capture_output=True).returncode != 0,
        reason="Helm not installed"
    )
    def test_resource_quota_when_enabled(self) -> None:
        """Test that ResourceQuota is created when enabled."""
        result = subprocess.run(
            ["helm", "template", "test-release", str(CHART_PATH),
             "--set", "namespace.create=true",
             "--set", "namespace.resourceQuotas.enabled=true"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Helm template failed: {result.stderr}"

        # Parse output for ResourceQuota
        docs = list(yaml.safe_load_all(result.stdout))
        quota_docs = [d for d in docs if d and d.get("kind") == "ResourceQuota"]

        assert len(quota_docs) == 1, "Should create ResourceQuota when enabled"

    def test_namespace_template_uses_helpers(self) -> None:
        """Test that namespace template uses helper functions."""
        template_file = CHART_PATH / "templates" / "namespace.yaml"
        content = template_file.read_text()

        # Check for common helper usage
        assert "dox-asdlc.namespace" in content or "dox-asdlc.labels" in content, \
            "Template should use helper functions"

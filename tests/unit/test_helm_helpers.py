"""Tests for Helm helper template functions (P06-F01-T05)."""

import subprocess
from pathlib import Path

import pytest
import yaml


CHART_PATH = Path(__file__).parent.parent.parent / "helm" / "dox-asdlc"


class TestHelmHelpers:
    """Test the _helpers.tpl file."""

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
        """Test that dox-asdlc.name helper is defined."""
        assert 'define "dox-asdlc.name"' in helpers_content, \
            "Should define dox-asdlc.name helper"

    def test_fullname_helper_defined(self, helpers_content: str) -> None:
        """Test that dox-asdlc.fullname helper is defined."""
        assert 'define "dox-asdlc.fullname"' in helpers_content, \
            "Should define dox-asdlc.fullname helper"

    def test_chart_helper_defined(self, helpers_content: str) -> None:
        """Test that dox-asdlc.chart helper is defined."""
        assert 'define "dox-asdlc.chart"' in helpers_content, \
            "Should define dox-asdlc.chart helper"

    def test_labels_helper_defined(self, helpers_content: str) -> None:
        """Test that dox-asdlc.labels helper is defined."""
        assert 'define "dox-asdlc.labels"' in helpers_content, \
            "Should define dox-asdlc.labels helper"

    def test_selector_labels_helper_defined(self, helpers_content: str) -> None:
        """Test that dox-asdlc.selectorLabels helper is defined."""
        assert 'define "dox-asdlc.selectorLabels"' in helpers_content, \
            "Should define dox-asdlc.selectorLabels helper"

    def test_namespace_helper_defined(self, helpers_content: str) -> None:
        """Test that dox-asdlc.namespace helper is defined."""
        assert 'define "dox-asdlc.namespace"' in helpers_content, \
            "Should define dox-asdlc.namespace helper"

    def test_redis_secret_name_helper_defined(self, helpers_content: str) -> None:
        """Test that dox-asdlc.redisSecretName helper is defined."""
        assert 'define "dox-asdlc.redisSecretName"' in helpers_content, \
            "Should define dox-asdlc.redisSecretName helper"

    def test_git_secret_name_helper_defined(self, helpers_content: str) -> None:
        """Test that dox-asdlc.gitSecretName helper is defined."""
        assert 'define "dox-asdlc.gitSecretName"' in helpers_content, \
            "Should define dox-asdlc.gitSecretName helper"

    def test_redis_url_helper_defined(self, helpers_content: str) -> None:
        """Test that dox-asdlc.redisUrl helper is defined."""
        assert 'define "dox-asdlc.redisUrl"' in helpers_content, \
            "Should define dox-asdlc.redisUrl helper"

    def test_knowledge_store_url_helper_defined(self, helpers_content: str) -> None:
        """Test that dox-asdlc.knowledgeStoreUrl helper is defined."""
        assert 'define "dox-asdlc.knowledgeStoreUrl"' in helpers_content, \
            "Should define dox-asdlc.knowledgeStoreUrl helper"

    def test_labels_include_required_fields(self, helpers_content: str) -> None:
        """Test that labels helper includes required Kubernetes labels."""
        # Check that labels helper references standard labels
        assert "helm.sh/chart" in helpers_content, "Labels should include helm.sh/chart"
        assert "app.kubernetes.io/version" in helpers_content, "Labels should include app version"
        assert "app.kubernetes.io/managed-by" in helpers_content, "Labels should include managed-by"

    def test_selector_labels_include_required_fields(self, helpers_content: str) -> None:
        """Test that selector labels include required fields."""
        assert "app.kubernetes.io/name" in helpers_content, \
            "Selector labels should include app.kubernetes.io/name"
        assert "app.kubernetes.io/instance" in helpers_content, \
            "Selector labels should include app.kubernetes.io/instance"

    @pytest.mark.skipif(
        subprocess.run(["which", "helm"], capture_output=True).returncode != 0,
        reason="Helm not installed"
    )
    def test_helpers_render_correctly(self) -> None:
        """Test that helpers render without errors."""
        result = subprocess.run(
            ["helm", "template", "test-release", str(CHART_PATH)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Helm template failed: {result.stderr}"

    @pytest.mark.skipif(
        subprocess.run(["which", "helm"], capture_output=True).returncode != 0,
        reason="Helm not installed"
    )
    def test_namespace_helper_produces_expected_value(self) -> None:
        """Test that namespace helper produces expected value."""
        result = subprocess.run(
            ["helm", "template", "test-release", str(CHART_PATH),
             "--set", "namespace.create=true"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Helm template failed: {result.stderr}"

        # Parse output and check namespace
        docs = list(yaml.safe_load_all(result.stdout))
        namespace_docs = [d for d in docs if d and d.get("kind") == "Namespace"]

        if namespace_docs:
            ns_name = namespace_docs[0]["metadata"]["name"]
            assert ns_name == "dox-asdlc", f"Namespace should be 'dox-asdlc', got '{ns_name}'"

"""Tests for secrets template (P06-F01-T04)."""

import subprocess
from pathlib import Path

import pytest
import yaml


CHART_PATH = Path(__file__).parent.parent.parent / "helm" / "dox-asdlc"


class TestSecretsTemplate:
    """Test the secrets.yaml template."""

    def test_secrets_template_exists(self) -> None:
        """Test that secrets.yaml template exists."""
        template_file = CHART_PATH / "templates" / "secrets.yaml"
        assert template_file.exists(), f"secrets.yaml not found at {template_file}"

    def test_secrets_template_has_redis_secret(self) -> None:
        """Test that secrets template defines Redis secret."""
        template_file = CHART_PATH / "templates" / "secrets.yaml"
        content = template_file.read_text()

        assert "redis" in content.lower(), "Template should reference Redis secret"
        assert "redis-password" in content, "Template should define redis-password key"

    def test_secrets_template_has_git_secret(self) -> None:
        """Test that secrets template defines Git credentials secret."""
        template_file = CHART_PATH / "templates" / "secrets.yaml"
        content = template_file.read_text()

        assert "git" in content.lower(), "Template should reference Git secret"
        assert "username" in content, "Template should define username key"
        assert "token" in content, "Template should define token key"

    def test_secrets_template_has_api_keys(self) -> None:
        """Test that secrets template defines API keys secret."""
        template_file = CHART_PATH / "templates" / "secrets.yaml"
        content = template_file.read_text()

        assert "apiKeys" in content or "api-keys" in content, "Template should reference API keys secret"
        assert "claude" in content.lower(), "Template should define Claude API key"

    def test_secrets_are_base64_encoded(self) -> None:
        """Test that secrets use base64 encoding."""
        template_file = CHART_PATH / "templates" / "secrets.yaml"
        content = template_file.read_text()

        assert "b64enc" in content, "Secrets should use b64enc function for encoding"

    @pytest.mark.skipif(
        subprocess.run(["which", "helm"], capture_output=True).returncode != 0,
        reason="Helm not installed"
    )
    def test_helm_template_creates_secrets(self) -> None:
        """Test that helm template creates all secrets."""
        result = subprocess.run(
            ["helm", "template", "test-release", str(CHART_PATH),
             "--set", "secrets.redis.create=true",
             "--set", "secrets.redis.password=testpass",
             "--set", "secrets.git.create=true",
             "--set", "secrets.git.username=testuser",
             "--set", "secrets.git.token=testtoken",
             "--set", "secrets.apiKeys.create=true",
             "--set", "secrets.apiKeys.claudeApiKey=testapikey"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Helm template failed: {result.stderr}"

        # Parse output for Secrets
        docs = list(yaml.safe_load_all(result.stdout))
        secret_docs = [d for d in docs if d and d.get("kind") == "Secret"]

        assert len(secret_docs) >= 3, "Should create at least 3 secrets (redis, git, apiKeys)"

        # Verify secret types
        secret_names = [s["metadata"]["name"] for s in secret_docs]
        assert any("redis" in name for name in secret_names), "Should create Redis secret"
        assert any("git" in name for name in secret_names), "Should create Git secret"
        assert any("api" in name.lower() or "key" in name.lower() for name in secret_names), \
            "Should create API keys secret"

    @pytest.mark.skipif(
        subprocess.run(["which", "helm"], capture_output=True).returncode != 0,
        reason="Helm not installed"
    )
    def test_secrets_not_created_when_disabled(self) -> None:
        """Test that secrets are not created when disabled."""
        result = subprocess.run(
            ["helm", "template", "test-release", str(CHART_PATH),
             "--set", "secrets.redis.create=false",
             "--set", "secrets.git.create=false",
             "--set", "secrets.apiKeys.create=false"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Helm template failed: {result.stderr}"

        # Parse output - should have no secrets
        docs = list(yaml.safe_load_all(result.stdout))
        secret_docs = [d for d in docs if d and d.get("kind") == "Secret"]

        assert len(secret_docs) == 0, "Should not create secrets when disabled"

    @pytest.mark.skipif(
        subprocess.run(["which", "helm"], capture_output=True).returncode != 0,
        reason="Helm not installed"
    )
    def test_secrets_have_labels(self) -> None:
        """Test that secrets have proper labels."""
        result = subprocess.run(
            ["helm", "template", "test-release", str(CHART_PATH),
             "--set", "secrets.redis.create=true",
             "--set", "secrets.redis.password=testpass"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Helm template failed: {result.stderr}"

        docs = list(yaml.safe_load_all(result.stdout))
        secret_docs = [d for d in docs if d and d.get("kind") == "Secret"]

        for secret in secret_docs:
            labels = secret.get("metadata", {}).get("labels", {})
            assert "app.kubernetes.io/name" in labels, "Secret should have app.kubernetes.io/name label"
            assert "helm.sh/chart" in labels, "Secret should have helm.sh/chart label"

    def test_secrets_template_conditional_creation(self) -> None:
        """Test that secrets template has conditional creation."""
        template_file = CHART_PATH / "templates" / "secrets.yaml"
        content = template_file.read_text()

        # Check for conditional statements
        assert "if" in content, "Template should have conditional creation"
        assert ".Values.secrets" in content, "Template should reference secrets values"

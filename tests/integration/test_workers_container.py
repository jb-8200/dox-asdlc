"""Integration tests for workers container configuration.

Tests Dockerfile configuration without running Docker.
"""

from __future__ import annotations

import pathlib


class TestWorkersDockerfile:
    """Tests for workers container Dockerfile."""

    @classmethod
    def setup_class(cls) -> None:
        """Load Dockerfile content."""
        project_root = pathlib.Path(__file__).parent.parent.parent
        dockerfile_path = project_root / "docker" / "workers" / "Dockerfile"
        assert dockerfile_path.exists(), "Workers Dockerfile not found"

        with open(dockerfile_path) as f:
            cls.dockerfile = f.read()

    def test_base_image_is_python311(self) -> None:
        """Test that base image is Python 3.11."""
        assert "FROM python:3.11" in self.dockerfile

    def test_installs_git(self) -> None:
        """Test that Git is installed for repo access."""
        assert "git" in self.dockerfile

    def test_exposes_health_port(self) -> None:
        """Test that port 8081 is exposed."""
        assert "EXPOSE 8081" in self.dockerfile

    def test_has_healthcheck(self) -> None:
        """Test that HEALTHCHECK is defined."""
        assert "HEALTHCHECK" in self.dockerfile

    def test_sets_pythonpath(self) -> None:
        """Test that PYTHONPATH is set."""
        assert "PYTHONPATH" in self.dockerfile

    def test_creates_non_root_user(self) -> None:
        """Test that a non-root user is created."""
        assert "useradd" in self.dockerfile

    def test_switches_to_non_root(self) -> None:
        """Test that USER directive is used."""
        assert "USER asdlc" in self.dockerfile

    def test_git_write_access_env_false(self) -> None:
        """Test that GIT_WRITE_ACCESS is set to false."""
        assert "GIT_WRITE_ACCESS=false" in self.dockerfile

    def test_copies_requirements(self) -> None:
        """Test that requirements.txt is copied."""
        assert "requirements.txt" in self.dockerfile

    def test_copies_source(self) -> None:
        """Test that source code is copied."""
        assert "COPY src/" in self.dockerfile

    def test_runs_workers_main(self) -> None:
        """Test that CMD runs workers main module."""
        assert "src.workers.main" in self.dockerfile

    def test_service_port_env(self) -> None:
        """Test that SERVICE_PORT is set to 8081."""
        assert "SERVICE_PORT=8081" in self.dockerfile

"""Integration tests for HITL UI container configuration.

Tests Dockerfile and server configuration without running Docker.
"""

from __future__ import annotations

import json
import pathlib


class TestHITLUIDockerfile:
    """Tests for HITL UI container Dockerfile."""

    @classmethod
    def setup_class(cls) -> None:
        """Load Dockerfile content."""
        project_root = pathlib.Path(__file__).parent.parent.parent
        dockerfile_path = project_root / "docker" / "hitl-ui" / "Dockerfile"
        assert dockerfile_path.exists(), "HITL UI Dockerfile not found"

        with open(dockerfile_path) as f:
            cls.dockerfile = f.read()

    def test_base_image_is_node20(self) -> None:
        """Test that base image is Node 20."""
        assert "FROM node:20" in self.dockerfile

    def test_uses_alpine(self) -> None:
        """Test that Alpine variant is used for smaller image."""
        assert "alpine" in self.dockerfile

    def test_exposes_port_3000(self) -> None:
        """Test that port 3000 is exposed."""
        assert "EXPOSE 3000" in self.dockerfile

    def test_has_healthcheck(self) -> None:
        """Test that HEALTHCHECK is defined."""
        assert "HEALTHCHECK" in self.dockerfile

    def test_creates_non_root_user(self) -> None:
        """Test that a non-root user is created."""
        assert "adduser" in self.dockerfile

    def test_service_port_env(self) -> None:
        """Test that SERVICE_PORT is set to 3000."""
        assert "SERVICE_PORT=3000" in self.dockerfile

    def test_copies_server_js(self) -> None:
        """Test that server.js is copied."""
        assert "server.js" in self.dockerfile

    def test_copies_package_json(self) -> None:
        """Test that package.json is copied."""
        assert "package.json" in self.dockerfile


class TestHITLUIPackageJson:
    """Tests for HITL UI package.json."""

    @classmethod
    def setup_class(cls) -> None:
        """Load package.json content."""
        project_root = pathlib.Path(__file__).parent.parent.parent
        package_path = project_root / "docker" / "hitl-ui" / "package.json"
        assert package_path.exists(), "package.json not found"

        with open(package_path) as f:
            cls.package = json.load(f)

    def test_name_set(self) -> None:
        """Test that package name is set."""
        assert self.package.get("name") == "asdlc-hitl-ui"

    def test_main_is_server_js(self) -> None:
        """Test that main is server.js."""
        assert self.package.get("main") == "server.js"

    def test_start_script_defined(self) -> None:
        """Test that start script is defined."""
        scripts = self.package.get("scripts", {})
        assert "start" in scripts
        assert "server.js" in scripts["start"]

    def test_node_version_requirement(self) -> None:
        """Test that Node version requirement is set."""
        engines = self.package.get("engines", {})
        assert "node" in engines
        assert "20" in engines["node"]

    def test_is_private(self) -> None:
        """Test that package is marked as private."""
        assert self.package.get("private") is True


class TestHITLUIServerJs:
    """Tests for HITL UI server.js."""

    @classmethod
    def setup_class(cls) -> None:
        """Load server.js content."""
        project_root = pathlib.Path(__file__).parent.parent.parent
        server_path = project_root / "docker" / "hitl-ui" / "server.js"
        assert server_path.exists(), "server.js not found"

        with open(server_path) as f:
            cls.server = f.read()

    def test_has_health_endpoint(self) -> None:
        """Test that /health endpoint is defined."""
        assert "/health" in self.server

    def test_returns_json(self) -> None:
        """Test that JSON content type is set."""
        assert "application/json" in self.server

    def test_handles_sigterm(self) -> None:
        """Test that SIGTERM is handled for graceful shutdown."""
        assert "SIGTERM" in self.server

    def test_uses_port_from_env(self) -> None:
        """Test that port is read from environment."""
        assert "SERVICE_PORT" in self.server

    def test_has_root_endpoint(self) -> None:
        """Test that root endpoint is defined."""
        # Check for root route handling
        assert "'/' " in self.server or '"/")' in self.server or "=== '/'" in self.server

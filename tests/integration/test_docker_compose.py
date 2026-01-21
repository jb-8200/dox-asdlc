"""Integration tests for Docker Compose configuration.

These tests validate the docker-compose.yml configuration
without requiring Docker to be running.
"""

from __future__ import annotations

import pathlib
import yaml


class TestDockerComposeConfig:
    """Tests for docker-compose.yml configuration."""

    @classmethod
    def setup_class(cls) -> None:
        """Load docker-compose.yml once for all tests."""
        project_root = pathlib.Path(__file__).parent.parent.parent
        compose_path = project_root / "docker" / "docker-compose.yml"
        assert compose_path.exists(), "docker-compose.yml not found"

        with open(compose_path) as f:
            cls.config = yaml.safe_load(f)

    def test_four_services_defined(self) -> None:
        """Test that all four services are defined."""
        services = self.config.get("services", {})
        assert len(services) == 4

        expected_services = {"orchestrator", "workers", "infrastructure", "hitl-ui"}
        assert set(services.keys()) == expected_services

    def test_orchestrator_service_config(self) -> None:
        """Test orchestrator service configuration."""
        service = self.config["services"]["orchestrator"]

        # Check port mapping
        assert "8080:8080" in service.get("ports", [])

        # Check environment
        env = service.get("environment", [])
        env_dict = self._parse_env_list(env)
        assert env_dict.get("SERVICE_NAME") == "orchestrator"
        assert env_dict.get("GIT_WRITE_ACCESS") == "true"

        # Check health check exists
        assert "healthcheck" in service

        # Check depends_on infrastructure
        depends = service.get("depends_on", {})
        assert "infrastructure" in depends

    def test_workers_service_config(self) -> None:
        """Test workers service configuration."""
        service = self.config["services"]["workers"]

        # Check port mapping
        assert "8081:8081" in service.get("ports", [])

        # Check environment
        env = service.get("environment", [])
        env_dict = self._parse_env_list(env)
        assert env_dict.get("SERVICE_NAME") == "workers"
        assert env_dict.get("GIT_WRITE_ACCESS") == "false"

        # Check health check exists
        assert "healthcheck" in service

        # Check read-only workspace
        volumes = service.get("volumes", [])
        workspace_vol = [v for v in volumes if "workspace" in v]
        assert len(workspace_vol) == 1
        assert ":ro" in workspace_vol[0]

    def test_infrastructure_service_config(self) -> None:
        """Test infrastructure service configuration."""
        service = self.config["services"]["infrastructure"]

        # Check Redis port mapping
        assert "6379:6379" in service.get("ports", [])

        # Check health check exists
        assert "healthcheck" in service
        healthcheck = service["healthcheck"]
        # Should use redis-cli ping
        test_cmd = healthcheck.get("test", [])
        assert "redis-cli" in str(test_cmd)

        # Check data volume
        volumes = service.get("volumes", [])
        assert any("redis-data" in v for v in volumes)

    def test_hitl_ui_service_config(self) -> None:
        """Test HITL UI service configuration."""
        service = self.config["services"]["hitl-ui"]

        # Check port mapping
        assert "3000:3000" in service.get("ports", [])

        # Check environment
        env = service.get("environment", [])
        env_dict = self._parse_env_list(env)
        assert env_dict.get("SERVICE_NAME") == "hitl-ui"

        # Check health check exists
        assert "healthcheck" in service

        # Check depends_on
        depends = service.get("depends_on", {})
        assert "infrastructure" in depends
        assert "orchestrator" in depends

    def test_network_defined(self) -> None:
        """Test that asdlc-network is defined."""
        networks = self.config.get("networks", {})
        assert "asdlc-network" in networks

        # Check all services use this network
        for service_name, service in self.config["services"].items():
            service_networks = service.get("networks", [])
            assert "asdlc-network" in service_networks, (
                f"Service {service_name} not on asdlc-network"
            )

    def test_volumes_defined(self) -> None:
        """Test that required volumes are defined."""
        volumes = self.config.get("volumes", {})
        assert "redis-data" in volumes
        assert "git-credentials" in volumes

    def test_health_check_intervals(self) -> None:
        """Test that health check intervals are reasonable."""
        for service_name, service in self.config["services"].items():
            healthcheck = service.get("healthcheck", {})
            if healthcheck:
                # Check interval exists and is reasonable
                interval = healthcheck.get("interval", "30s")
                assert interval.endswith("s"), (
                    f"{service_name} health interval should be in seconds"
                )

    def test_container_names_set(self) -> None:
        """Test that container names are explicitly set."""
        for service_name, service in self.config["services"].items():
            assert "container_name" in service, (
                f"Service {service_name} missing container_name"
            )
            assert service["container_name"].startswith("asdlc-")

    def _parse_env_list(self, env: list) -> dict:
        """Parse environment list into dictionary."""
        result = {}
        for item in env:
            if "=" in item:
                key, value = item.split("=", 1)
                result[key] = value
        return result

"""Integration tests for infrastructure container configuration.

Tests Redis Dockerfile and configuration without running Docker.
"""

from __future__ import annotations

import pathlib


class TestInfrastructureDockerfile:
    """Tests for infrastructure container Dockerfile."""

    @classmethod
    def setup_class(cls) -> None:
        """Load Dockerfile content."""
        project_root = pathlib.Path(__file__).parent.parent.parent
        dockerfile_path = project_root / "docker" / "infrastructure" / "Dockerfile"
        assert dockerfile_path.exists(), "Infrastructure Dockerfile not found"

        with open(dockerfile_path) as f:
            cls.dockerfile = f.read()

    def test_base_image_is_redis(self) -> None:
        """Test that base image is Redis 7."""
        assert "FROM redis:7" in self.dockerfile

    def test_exposes_redis_port(self) -> None:
        """Test that port 6379 is exposed."""
        assert "EXPOSE 6379" in self.dockerfile

    def test_has_healthcheck(self) -> None:
        """Test that HEALTHCHECK is defined."""
        assert "HEALTHCHECK" in self.dockerfile

    def test_uses_custom_config(self) -> None:
        """Test that custom redis.conf is used."""
        assert "redis.conf" in self.dockerfile

    def test_creates_data_directory(self) -> None:
        """Test that /data directory is created."""
        assert "/data" in self.dockerfile


class TestRedisConfig:
    """Tests for Redis configuration file."""

    @classmethod
    def setup_class(cls) -> None:
        """Load redis.conf content."""
        project_root = pathlib.Path(__file__).parent.parent.parent
        config_path = project_root / "docker" / "infrastructure" / "redis.conf"
        assert config_path.exists(), "redis.conf not found"

        with open(config_path) as f:
            cls.config = f.read()

    def test_binds_to_all_interfaces(self) -> None:
        """Test that Redis binds to 0.0.0.0 for container networking."""
        assert "bind 0.0.0.0" in self.config

    def test_port_configured(self) -> None:
        """Test that port 6379 is configured."""
        assert "port 6379" in self.config

    def test_persistence_enabled(self) -> None:
        """Test that RDB persistence is enabled."""
        assert "save 60 1" in self.config

    def test_data_directory_set(self) -> None:
        """Test that data directory is set to /data."""
        assert "dir /data" in self.config

    def test_max_memory_configured(self) -> None:
        """Test that maxmemory is configured."""
        assert "maxmemory" in self.config

    def test_dbfilename_set(self) -> None:
        """Test that dump filename is set."""
        assert "dbfilename" in self.config
        assert "asdlc" in self.config  # Custom filename

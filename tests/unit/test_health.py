"""Unit tests for health check endpoints.

Tests health status generation and response formatting.
"""

from __future__ import annotations

import os
from datetime import datetime
from http import HTTPStatus
from unittest.mock import AsyncMock, patch

import pytest

from src.infrastructure.health import (
    DependencyHealth,
    HealthChecker,
    HealthResponse,
    HealthStatus,
    get_health_checker,
)


class TestHealthStatus:
    """Tests for HealthStatus enum."""

    def test_health_status_values(self) -> None:
        """Test health status enum values."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"


class TestDependencyHealth:
    """Tests for DependencyHealth dataclass."""

    def test_dependency_health_creation(self) -> None:
        """Test DependencyHealth creation."""
        dep = DependencyHealth(
            name="redis",
            status=HealthStatus.HEALTHY,
            latency_ms=1.5,
            details={"version": "7.0.0"},
        )
        assert dep.name == "redis"
        assert dep.status == HealthStatus.HEALTHY
        assert dep.latency_ms == 1.5
        assert dep.details["version"] == "7.0.0"

    def test_dependency_health_defaults(self) -> None:
        """Test DependencyHealth default values."""
        dep = DependencyHealth(
            name="test",
            status=HealthStatus.HEALTHY,
        )
        assert dep.latency_ms is None
        assert dep.details == {}


class TestHealthResponse:
    """Tests for HealthResponse dataclass."""

    def test_health_response_creation(self) -> None:
        """Test HealthResponse creation."""
        response = HealthResponse(
            status=HealthStatus.HEALTHY,
            service="test-service",
            timestamp="2026-01-21T00:00:00",
            uptime_seconds=100.5,
        )
        assert response.status == HealthStatus.HEALTHY
        assert response.service == "test-service"
        assert response.uptime_seconds == 100.5
        assert response.dependencies == []

    def test_health_response_to_dict(self) -> None:
        """Test HealthResponse to_dict serialization."""
        dep = DependencyHealth(
            name="redis",
            status=HealthStatus.HEALTHY,
            latency_ms=2.5,
        )
        response = HealthResponse(
            status=HealthStatus.HEALTHY,
            service="test-service",
            timestamp="2026-01-21T00:00:00",
            uptime_seconds=100.5,
            dependencies=[dep],
        )

        result = response.to_dict()

        assert result["status"] == "healthy"
        assert result["service"] == "test-service"
        assert result["uptime_seconds"] == 100.5
        assert len(result["dependencies"]) == 1
        assert result["dependencies"][0]["name"] == "redis"
        assert result["dependencies"][0]["status"] == "healthy"

    def test_health_response_http_status_healthy(self) -> None:
        """Test HTTP status code for healthy response."""
        response = HealthResponse(
            status=HealthStatus.HEALTHY,
            service="test",
            timestamp="2026-01-21T00:00:00",
            uptime_seconds=100,
        )
        assert response.http_status_code() == HTTPStatus.OK

    def test_health_response_http_status_degraded(self) -> None:
        """Test HTTP status code for degraded response."""
        response = HealthResponse(
            status=HealthStatus.DEGRADED,
            service="test",
            timestamp="2026-01-21T00:00:00",
            uptime_seconds=100,
        )
        # Degraded still returns OK since service is functional
        assert response.http_status_code() == HTTPStatus.OK

    def test_health_response_http_status_unhealthy(self) -> None:
        """Test HTTP status code for unhealthy response."""
        response = HealthResponse(
            status=HealthStatus.UNHEALTHY,
            service="test",
            timestamp="2026-01-21T00:00:00",
            uptime_seconds=100,
        )
        assert response.http_status_code() == HTTPStatus.SERVICE_UNAVAILABLE


class TestHealthChecker:
    """Tests for HealthChecker class."""

    def test_health_checker_creation(self) -> None:
        """Test HealthChecker creation."""
        checker = HealthChecker("test-service")
        assert checker.service_name == "test-service"
        assert checker.uptime_seconds >= 0

    def test_uptime_increases(self) -> None:
        """Test that uptime increases over time."""
        import time

        checker = HealthChecker("test-service")
        initial = checker.uptime_seconds
        time.sleep(0.1)
        assert checker.uptime_seconds > initial

    @pytest.mark.asyncio
    async def test_check_redis_dependency_healthy(self) -> None:
        """Test Redis dependency check when healthy."""
        checker = HealthChecker("test-service")

        with patch(
            "src.infrastructure.health.check_redis_health"
        ) as mock_check:
            mock_check.return_value = {
                "status": "healthy",
                "host": "localhost",
                "port": 6379,
                "server_version": "7.0.0",
            }

            dep = await checker.check_redis_dependency()

            assert dep.name == "redis"
            assert dep.status == HealthStatus.HEALTHY
            assert dep.latency_ms is not None
            assert dep.details["host"] == "localhost"

    @pytest.mark.asyncio
    async def test_check_redis_dependency_unhealthy(self) -> None:
        """Test Redis dependency check when unhealthy."""
        checker = HealthChecker("test-service")

        with patch(
            "src.infrastructure.health.check_redis_health"
        ) as mock_check:
            mock_check.return_value = {
                "status": "unhealthy",
                "error": "Connection refused",
            }

            dep = await checker.check_redis_dependency()

            assert dep.name == "redis"
            assert dep.status == HealthStatus.UNHEALTHY
            assert "error" in dep.details

    @pytest.mark.asyncio
    async def test_check_health_all_dependencies_healthy(self) -> None:
        """Test full health check with healthy dependencies."""
        checker = HealthChecker("test-service")

        with patch(
            "src.infrastructure.health.check_redis_health"
        ) as mock_check:
            mock_check.return_value = {
                "status": "healthy",
                "host": "localhost",
                "port": 6379,
                "server_version": "7.0.0",
            }

            response = await checker.check_health()

            assert response.status == HealthStatus.HEALTHY
            assert response.service == "test-service"
            assert len(response.dependencies) == 1
            assert response.dependencies[0].status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_check_health_dependency_unhealthy(self) -> None:
        """Test full health check with unhealthy dependency."""
        checker = HealthChecker("test-service")

        with patch(
            "src.infrastructure.health.check_redis_health"
        ) as mock_check:
            mock_check.return_value = {
                "status": "unhealthy",
                "error": "Connection refused",
            }

            response = await checker.check_health()

            assert response.status == HealthStatus.UNHEALTHY
            assert len(response.dependencies) == 1
            assert response.dependencies[0].status == HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_check_liveness_no_dependencies(self) -> None:
        """Test liveness check does not check dependencies."""
        checker = HealthChecker("test-service")

        response = await checker.check_liveness()

        assert response.status == HealthStatus.HEALTHY
        assert response.dependencies == []


class TestGetHealthChecker:
    """Tests for get_health_checker singleton function."""

    def test_get_health_checker_creates_singleton(self) -> None:
        """Test that get_health_checker returns singleton."""
        import src.infrastructure.health as health_module

        # Reset singleton
        health_module._health_checker = None

        checker1 = get_health_checker("service1")
        checker2 = get_health_checker("service2")

        # Should be same instance
        assert checker1 is checker2
        # First call sets the name
        assert checker1.service_name == "service1"

    def test_get_health_checker_with_env_config(self) -> None:
        """Test get_health_checker uses config when available."""
        import src.infrastructure.health as health_module

        # Reset singleton
        health_module._health_checker = None

        with patch.dict(
            os.environ,
            {"SERVICE_NAME": "env-service", "SERVICE_PORT": "8080"},
        ):
            from src.core.config import clear_config_cache

            clear_config_cache()
            checker = get_health_checker()
            # Service name from config
            assert checker.service_name == "env-service"


class TestDirectoryStructure:
    """Tests for project directory structure."""

    def test_required_directories_exist(self) -> None:
        """Test that required directories exist."""
        import pathlib

        project_root = pathlib.Path(__file__).parent.parent.parent

        required_dirs = [
            "src",
            "src/core",
            "src/infrastructure",
            "src/orchestrator",
            "src/workers",
            "tests",
            "tests/unit",
            "tests/integration",
            "tools",
            "scripts",
            "docker",
        ]

        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            assert dir_path.is_dir(), f"Directory missing: {dir_name}"

    def test_init_files_exist(self) -> None:
        """Test that __init__.py files exist in packages."""
        import pathlib

        project_root = pathlib.Path(__file__).parent.parent.parent

        packages = [
            "src",
            "src/core",
            "src/infrastructure",
            "src/orchestrator",
            "src/workers",
            "tests",
            "tests/unit",
            "tests/integration",
        ]

        for pkg in packages:
            init_path = project_root / pkg / "__init__.py"
            assert init_path.exists(), f"Missing __init__.py: {pkg}"

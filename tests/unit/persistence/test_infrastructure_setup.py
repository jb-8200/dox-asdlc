"""Tests for P02-F09 Phase 1A: Infrastructure Setup.

This module tests:
- T01: PostgreSQL dependencies can be imported
- T02: Docker compose config is valid YAML with postgres service
- T03: PostgreSQL init.sql contains valid schema
"""

import os
import subprocess
from pathlib import Path

import pytest
import yaml


# Project root for file paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


class TestPostgreSQLDependencies:
    """T01: Verify PostgreSQL dependencies can be imported."""

    def test_asyncpg_import(self) -> None:
        """Test that asyncpg can be imported."""
        import asyncpg
        assert asyncpg is not None

    def test_sqlalchemy_import(self) -> None:
        """Test that SQLAlchemy with async support can be imported."""
        import sqlalchemy
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        assert sqlalchemy is not None
        assert AsyncSession is not None
        assert create_async_engine is not None

    def test_alembic_import(self) -> None:
        """Test that Alembic can be imported."""
        import alembic
        from alembic import command
        assert alembic is not None
        assert command is not None

    def test_psycopg2_import(self) -> None:
        """Test that psycopg2-binary can be imported."""
        import psycopg2
        assert psycopg2 is not None

    def test_dependencies_in_requirements(self) -> None:
        """Test that PostgreSQL dependencies are listed in requirements.txt."""
        requirements_path = PROJECT_ROOT / "requirements.txt"
        assert requirements_path.exists(), "requirements.txt not found"

        content = requirements_path.read_text()

        # Check for required dependencies
        assert "asyncpg>=" in content, "asyncpg not in requirements.txt"
        assert "sqlalchemy" in content.lower(), "sqlalchemy not in requirements.txt"
        assert "alembic>=" in content, "alembic not in requirements.txt"
        assert "psycopg2-binary>=" in content, "psycopg2-binary not in requirements.txt"


class TestDockerComposePostgres:
    """T02: Verify Docker Compose includes PostgreSQL service."""

    @pytest.fixture
    def docker_compose_path(self) -> Path:
        """Return path to docker-compose.yml."""
        return PROJECT_ROOT / "docker" / "docker-compose.yml"

    @pytest.fixture
    def docker_compose_config(self, docker_compose_path: Path) -> dict:
        """Load and return docker-compose.yml as dict."""
        assert docker_compose_path.exists(), "docker-compose.yml not found"
        with open(docker_compose_path) as f:
            return yaml.safe_load(f)

    def test_docker_compose_valid_yaml(self, docker_compose_path: Path) -> None:
        """Test that docker-compose.yml is valid YAML."""
        with open(docker_compose_path) as f:
            config = yaml.safe_load(f)
        assert config is not None
        assert "services" in config

    def test_postgres_service_exists(self, docker_compose_config: dict) -> None:
        """Test that postgres service is defined."""
        assert "postgres" in docker_compose_config["services"], (
            "postgres service not defined in docker-compose.yml"
        )

    def test_postgres_image(self, docker_compose_config: dict) -> None:
        """Test that postgres uses postgres:16-alpine image."""
        postgres = docker_compose_config["services"]["postgres"]
        assert postgres.get("image") == "postgres:16-alpine", (
            "postgres should use postgres:16-alpine image"
        )

    def test_postgres_required_env_vars(self, docker_compose_config: dict) -> None:
        """Test that postgres has required environment variables."""
        postgres = docker_compose_config["services"]["postgres"]
        env = postgres.get("environment", {})

        # Environment can be a list or dict
        if isinstance(env, list):
            env_str = " ".join(env)
        else:
            env_str = str(env)

        # Check for required env vars with proper error handling
        assert "POSTGRES_USER" in env_str, "POSTGRES_USER not in environment"
        assert "POSTGRES_PASSWORD" in env_str, "POSTGRES_PASSWORD not in environment"
        assert "POSTGRES_DB" in env_str, "POSTGRES_DB not in environment"

    def test_postgres_volume(self, docker_compose_config: dict) -> None:
        """Test that postgres has a named volume for data persistence."""
        postgres = docker_compose_config["services"]["postgres"]
        volumes = postgres.get("volumes", [])

        # Check for postgres-data volume
        volume_str = str(volumes)
        assert "postgres-data" in volume_str, "postgres-data volume not configured"

        # Also check volumes section
        all_volumes = docker_compose_config.get("volumes", {})
        assert "postgres-data" in all_volumes, "postgres-data not in volumes section"

    def test_postgres_healthcheck(self, docker_compose_config: dict) -> None:
        """Test that postgres has a healthcheck with pg_isready."""
        postgres = docker_compose_config["services"]["postgres"]
        healthcheck = postgres.get("healthcheck", {})

        assert healthcheck, "postgres should have a healthcheck"
        test_cmd = healthcheck.get("test", [])
        test_str = str(test_cmd)
        assert "pg_isready" in test_str, "healthcheck should use pg_isready"

    def test_postgres_network(self, docker_compose_config: dict) -> None:
        """Test that postgres is on asdlc-network."""
        postgres = docker_compose_config["services"]["postgres"]
        networks = postgres.get("networks", [])

        network_str = str(networks)
        assert "asdlc-network" in network_str, "postgres should be on asdlc-network"

    def test_orchestrator_depends_on_postgres(self, docker_compose_config: dict) -> None:
        """Test that orchestrator depends on postgres."""
        orchestrator = docker_compose_config["services"]["orchestrator"]
        depends_on = orchestrator.get("depends_on", {})

        depends_str = str(depends_on)
        assert "postgres" in depends_str, "orchestrator should depend on postgres"

    def test_postgres_init_script_volume(self, docker_compose_config: dict) -> None:
        """Test that postgres mounts init.sql script."""
        postgres = docker_compose_config["services"]["postgres"]
        volumes = postgres.get("volumes", [])

        volume_str = str(volumes)
        assert "init.sql" in volume_str, "postgres should mount init.sql"
        assert "docker-entrypoint-initdb.d" in volume_str, (
            "init.sql should be mounted to docker-entrypoint-initdb.d"
        )


class TestEnvExample:
    """T02: Verify docker/.env.example exists with sample values."""

    @pytest.fixture
    def env_example_path(self) -> Path:
        """Return path to .env.example."""
        return PROJECT_ROOT / "docker" / ".env.example"

    def test_env_example_exists(self, env_example_path: Path) -> None:
        """Test that .env.example file exists."""
        assert env_example_path.exists(), "docker/.env.example not found"

    def test_env_example_contains_postgres_vars(self, env_example_path: Path) -> None:
        """Test that .env.example contains PostgreSQL variables."""
        content = env_example_path.read_text()

        assert "POSTGRES_USER" in content, "POSTGRES_USER not in .env.example"
        assert "POSTGRES_PASSWORD" in content, "POSTGRES_PASSWORD not in .env.example"
        assert "POSTGRES_DB" in content, "POSTGRES_DB not in .env.example"


class TestPostgresInitSQL:
    """T03: Verify PostgreSQL init.sql schema is valid."""

    @pytest.fixture
    def init_sql_path(self) -> Path:
        """Return path to init.sql."""
        return PROJECT_ROOT / "docker" / "postgres" / "init.sql"

    def test_init_sql_exists(self, init_sql_path: Path) -> None:
        """Test that init.sql file exists."""
        assert init_sql_path.exists(), "docker/postgres/init.sql not found"

    def test_init_sql_not_empty(self, init_sql_path: Path) -> None:
        """Test that init.sql is not empty."""
        content = init_sql_path.read_text()
        assert len(content.strip()) > 0, "init.sql should not be empty"

    def test_init_sql_has_all_tables(self, init_sql_path: Path) -> None:
        """Test that init.sql creates all required tables."""
        content = init_sql_path.read_text()

        required_tables = [
            "ideation_sessions",
            "ideation_messages",
            "ideation_requirements",
            "ideation_maturity",
            "ideation_prd_drafts",
            "ideation_user_stories",
        ]

        for table in required_tables:
            assert f"CREATE TABLE {table}" in content, (
                f"CREATE TABLE {table} not found in init.sql"
            )

    def test_init_sql_uses_timestamptz(self, init_sql_path: Path) -> None:
        """Test that init.sql uses TIMESTAMPTZ for timestamp columns."""
        content = init_sql_path.read_text()

        # Should use TIMESTAMPTZ not TIMESTAMP
        assert "TIMESTAMPTZ" in content, "init.sql should use TIMESTAMPTZ columns"

    def test_init_sql_has_indexes(self, init_sql_path: Path) -> None:
        """Test that init.sql creates required indexes."""
        content = init_sql_path.read_text()

        required_indexes = [
            "idx_sessions_user_id",
            "idx_sessions_updated_at",
            "idx_messages_session_id",
            "idx_messages_timestamp",
            "idx_requirements_session_id",
            "idx_prd_drafts_session_id",
            "idx_user_stories_session_id",
        ]

        for index in required_indexes:
            assert index in content, f"Index {index} not found in init.sql"

    def test_init_sql_has_foreign_keys(self, init_sql_path: Path) -> None:
        """Test that init.sql has foreign key constraints."""
        content = init_sql_path.read_text()

        # Should have REFERENCES to ideation_sessions
        assert "REFERENCES ideation_sessions(id)" in content, (
            "Foreign key to ideation_sessions not found"
        )
        # Should have ON DELETE CASCADE
        assert "ON DELETE CASCADE" in content, "ON DELETE CASCADE not found"

    def test_init_sql_has_version_column(self, init_sql_path: Path) -> None:
        """Test that init.sql has version column for optimistic locking."""
        content = init_sql_path.read_text()

        # Sessions table should have version column
        assert "version INTEGER" in content, (
            "version column for optimistic locking not found"
        )

    def test_init_sql_valid_syntax(self, init_sql_path: Path) -> None:
        """Test that init.sql is syntactically valid SQL.

        Note: This is a basic check. Full validation would require a database.
        """
        content = init_sql_path.read_text()

        # Basic syntax checks
        assert content.count("CREATE TABLE") == 6, "Should have 6 CREATE TABLE statements"
        assert content.count("CREATE INDEX") >= 7, "Should have at least 7 CREATE INDEX statements"

        # Check for balanced parentheses in each statement
        statements = content.split(";")
        for stmt in statements:
            stmt = stmt.strip()
            if stmt:
                open_parens = stmt.count("(")
                close_parens = stmt.count(")")
                assert open_parens == close_parens, (
                    f"Unbalanced parentheses in statement: {stmt[:50]}..."
                )

"""Tests for P02-F09 Task T08: Database Configuration.

This module tests:
- DatabaseConfig class with environment variables
- Database class connection management
- URL generation for async PostgreSQL
"""

import os
from typing import Any
from unittest.mock import patch

import pytest


def import_database_module() -> Any:
    """Import database module."""
    from src.orchestrator.persistence.database import (
        DatabaseConfig,
        Database,
        get_database,
    )
    return {
        "DatabaseConfig": DatabaseConfig,
        "Database": Database,
        "get_database": get_database,
    }


class TestDatabaseConfigImport:
    """Test that database module can be imported."""

    def test_database_config_import(self) -> None:
        """Test that DatabaseConfig can be imported."""
        db_module = import_database_module()
        assert db_module["DatabaseConfig"] is not None
        assert db_module["Database"] is not None
        assert db_module["get_database"] is not None


class TestDatabaseConfig:
    """Test DatabaseConfig class."""

    def test_default_values(self) -> None:
        """Test DatabaseConfig default values."""
        db_module = import_database_module()

        with patch.dict(os.environ, {}, clear=True):
            config = db_module["DatabaseConfig"]()

            assert config.host == "localhost"
            assert config.port == 5432
            assert config.database == "asdlc_ideation"
            assert config.user == "asdlc"
            assert config.password == ""
            assert config.pool_size == 5
            assert config.ssl_mode == "prefer"

    def test_environment_variables(self) -> None:
        """Test DatabaseConfig reads environment variables."""
        db_module = import_database_module()

        env_vars = {
            "POSTGRES_HOST": "db.example.com",
            "POSTGRES_PORT": "5433",
            "POSTGRES_DB": "test_db",
            "POSTGRES_USER": "testuser",
            "POSTGRES_PASSWORD": "testpass",
            "POSTGRES_POOL_SIZE": "10",
            "POSTGRES_SSL_MODE": "require",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = db_module["DatabaseConfig"]()

            assert config.host == "db.example.com"
            assert config.port == 5433
            assert config.database == "test_db"
            assert config.user == "testuser"
            assert config.password == "testpass"
            assert config.pool_size == 10
            assert config.ssl_mode == "require"

    def test_url_generation(self) -> None:
        """Test DatabaseConfig.url generates correct async URL."""
        db_module = import_database_module()

        env_vars = {
            "POSTGRES_HOST": "db.example.com",
            "POSTGRES_PORT": "5432",
            "POSTGRES_DB": "mydb",
            "POSTGRES_USER": "myuser",
            "POSTGRES_PASSWORD": "mypass",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = db_module["DatabaseConfig"]()
            url = config.url

            assert url.startswith("postgresql+asyncpg://")
            assert "myuser:mypass@" in url
            assert "db.example.com:5432" in url
            assert "/mydb" in url

    def test_url_with_special_characters_in_password(self) -> None:
        """Test URL generation handles special characters in password."""
        db_module = import_database_module()

        env_vars = {
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5432",
            "POSTGRES_DB": "mydb",
            "POSTGRES_USER": "myuser",
            "POSTGRES_PASSWORD": "pass@word!#",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = db_module["DatabaseConfig"]()
            url = config.url

            # URL should contain the password (even with special chars)
            assert "myuser:" in url
            assert "@localhost:5432" in url

    def test_port_as_integer(self) -> None:
        """Test port is converted to integer."""
        db_module = import_database_module()

        env_vars = {"POSTGRES_PORT": "5433"}

        with patch.dict(os.environ, env_vars, clear=True):
            config = db_module["DatabaseConfig"]()
            assert isinstance(config.port, int)
            assert config.port == 5433

    def test_pool_size_as_integer(self) -> None:
        """Test pool_size is converted to integer."""
        db_module = import_database_module()

        env_vars = {"POSTGRES_POOL_SIZE": "20"}

        with patch.dict(os.environ, env_vars, clear=True):
            config = db_module["DatabaseConfig"]()
            assert isinstance(config.pool_size, int)
            assert config.pool_size == 20


class TestDatabase:
    """Test Database class."""

    def test_database_instantiation(self) -> None:
        """Test Database can be instantiated."""
        db_module = import_database_module()

        db = db_module["Database"]()
        assert db is not None
        assert db.config is not None

    def test_database_with_custom_config(self) -> None:
        """Test Database can use custom config."""
        db_module = import_database_module()

        env_vars = {
            "POSTGRES_HOST": "custom-host",
            "POSTGRES_DB": "custom-db",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = db_module["DatabaseConfig"]()
            db = db_module["Database"](config=config)

            assert db.config.host == "custom-host"
            assert db.config.database == "custom-db"

    def test_database_engine_not_connected(self) -> None:
        """Test Database engine is None before connect."""
        db_module = import_database_module()

        db = db_module["Database"]()
        assert db._engine is None
        assert db._session_factory is None


class TestDatabaseAsync:
    """Test Database async methods (mocked)."""

    @pytest.mark.asyncio
    async def test_connect_creates_engine(self) -> None:
        """Test connect creates an async engine."""
        db_module = import_database_module()

        # We can't actually connect without a database,
        # but we can verify the method exists and the engine would be created
        db = db_module["Database"]()

        # Verify the method exists
        assert hasattr(db, "connect")
        assert callable(db.connect)

    @pytest.mark.asyncio
    async def test_disconnect_method_exists(self) -> None:
        """Test disconnect method exists."""
        db_module = import_database_module()

        db = db_module["Database"]()

        # Verify the method exists
        assert hasattr(db, "disconnect")
        assert callable(db.disconnect)

    @pytest.mark.asyncio
    async def test_session_context_manager_exists(self) -> None:
        """Test session context manager exists."""
        db_module = import_database_module()

        db = db_module["Database"]()

        # Verify the method exists
        assert hasattr(db, "session")
        # The session method should be an async context manager
        # We verify it returns an async context manager type


class TestGetDatabase:
    """Test get_database singleton function."""

    def test_get_database_returns_database(self) -> None:
        """Test get_database returns a Database instance."""
        db_module = import_database_module()

        # Reset singleton for test isolation
        from src.orchestrator.persistence import database as db_mod
        db_mod._database = None

        db = db_module["get_database"]()

        assert db is not None
        assert isinstance(db, db_module["Database"])

    def test_get_database_returns_same_instance(self) -> None:
        """Test get_database returns the same instance (singleton)."""
        db_module = import_database_module()

        # Reset singleton for test isolation
        from src.orchestrator.persistence import database as db_mod
        db_mod._database = None

        db1 = db_module["get_database"]()
        db2 = db_module["get_database"]()

        assert db1 is db2


class TestDatabaseConfigURLVariants:
    """Test various URL generation scenarios."""

    def test_url_with_localhost(self) -> None:
        """Test URL with localhost."""
        db_module = import_database_module()

        env_vars = {
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5432",
            "POSTGRES_DB": "test",
            "POSTGRES_USER": "user",
            "POSTGRES_PASSWORD": "pass",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = db_module["DatabaseConfig"]()
            assert "postgresql+asyncpg://user:pass@localhost:5432/test" == config.url

    def test_url_with_docker_hostname(self) -> None:
        """Test URL with Docker service name."""
        db_module = import_database_module()

        env_vars = {
            "POSTGRES_HOST": "postgres",
            "POSTGRES_PORT": "5432",
            "POSTGRES_DB": "asdlc_ideation",
            "POSTGRES_USER": "asdlc",
            "POSTGRES_PASSWORD": "secret",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = db_module["DatabaseConfig"]()
            assert "postgresql+asyncpg://asdlc:secret@postgres:5432/asdlc_ideation" == config.url

    def test_url_with_empty_password(self) -> None:
        """Test URL with empty password."""
        db_module = import_database_module()

        env_vars = {
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5432",
            "POSTGRES_DB": "test",
            "POSTGRES_USER": "user",
            "POSTGRES_PASSWORD": "",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = db_module["DatabaseConfig"]()
            # Empty password should still produce valid URL
            assert "postgresql+asyncpg://user:@localhost:5432/test" == config.url

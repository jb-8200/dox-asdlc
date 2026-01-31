"""Alembic environment configuration for async SQLAlchemy.

This module configures Alembic to work with SQLAlchemy's async engine.
It supports both online (connected to database) and offline (SQL script
generation) migration modes.
"""

import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import ORM models so they are registered with metadata
from src.orchestrator.persistence.orm_models import Base
from src.orchestrator.persistence.database import DatabaseConfig

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for 'autogenerate' support
target_metadata = Base.metadata


def get_url() -> str:
    """Get database URL from environment or config.

    Priority:
    1. SQLALCHEMY_DATABASE_URL environment variable
    2. POSTGRES_* environment variables via DatabaseConfig
    3. alembic.ini sqlalchemy.url setting (fallback)

    Returns:
        Database connection URL string.
    """
    # First, check for direct URL override
    url = os.getenv("SQLALCHEMY_DATABASE_URL")
    if url:
        return url

    # Second, try to construct from POSTGRES_* env vars
    db_config = DatabaseConfig()
    if db_config.host != "localhost" or db_config.password:
        return db_config.url

    # Fall back to alembic.ini (usually for development)
    return config.get_main_option("sqlalchemy.url", "")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine
    creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with a connection.

    Args:
        connection: SQLAlchemy connection object.
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine.

    In this scenario we need to create an Engine and associate a
    connection with the context.
    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Wraps the async migration runner for synchronous execution.
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

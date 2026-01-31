"""Database configuration and connection management.

This module provides:
- DatabaseConfig: Configuration from environment variables
- Database: Async connection management with SQLAlchemy
- get_database: Singleton accessor
"""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class DatabaseConfig:
    """Configuration for PostgreSQL database connection.

    Reads configuration from environment variables with sensible defaults.

    Attributes:
        host: PostgreSQL host (default: localhost).
        port: PostgreSQL port (default: 5432).
        database: Database name (default: asdlc_ideation).
        user: Database user (default: asdlc).
        password: Database password (default: empty).
        pool_size: Connection pool size (default: 5).
        ssl_mode: SSL mode (default: prefer).
    """

    def __init__(self) -> None:
        """Initialize configuration from environment variables."""
        self.host: str = os.getenv("POSTGRES_HOST", "localhost")
        self.port: int = int(os.getenv("POSTGRES_PORT", "5432"))
        self.database: str = os.getenv("POSTGRES_DB", "asdlc_ideation")
        self.user: str = os.getenv("POSTGRES_USER", "asdlc")
        self.password: str = os.getenv("POSTGRES_PASSWORD", "")
        self.pool_size: int = int(os.getenv("POSTGRES_POOL_SIZE", "5"))
        self.ssl_mode: str = os.getenv("POSTGRES_SSL_MODE", "prefer")

    @property
    def url(self) -> str:
        """Generate async PostgreSQL connection URL.

        Returns:
            Connection URL for asyncpg driver.
        """
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


class Database:
    """Async database connection manager.

    Manages SQLAlchemy async engine and session factory for PostgreSQL.

    Usage:
        db = Database()
        await db.connect()

        async with db.session() as session:
            # Use session for queries
            pass

        await db.disconnect()
    """

    def __init__(self, config: DatabaseConfig | None = None) -> None:
        """Initialize database with optional configuration.

        Args:
            config: Database configuration. If None, creates default from env.
        """
        self.config: DatabaseConfig = config or DatabaseConfig()
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    async def connect(self) -> None:
        """Create async engine and session factory.

        Creates an async SQLAlchemy engine with connection pooling.
        """
        self._engine = create_async_engine(
            self.config.url,
            pool_size=self.config.pool_size,
            echo=False,
        )
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def disconnect(self) -> None:
        """Dispose of the engine and close all connections."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Create an async session context manager.

        Yields:
            An AsyncSession for database operations.

        Raises:
            RuntimeError: If database is not connected.

        Usage:
            async with db.session() as session:
                result = await session.execute(query)
        """
        if self._session_factory is None:
            raise RuntimeError("Database not connected. Call connect() first.")

        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


# Singleton instance
_database: Database | None = None


def get_database() -> Database:
    """Get or create the singleton Database instance.

    Returns:
        The shared Database instance.
    """
    global _database
    if _database is None:
        _database = Database()
    return _database

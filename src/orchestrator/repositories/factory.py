"""Repository factory for persistence backend selection.

This module provides a factory for creating repository instances based on
the configured persistence backend (PostgreSQL or Redis).

Usage:
    factory = get_repository_factory()
    session_repo = factory.get_session_repository(db_session)
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from src.orchestrator.repositories.interfaces import (
    IMaturityRepository,
    IMessageRepository,
    IPRDRepository,
    IRequirementRepository,
    ISessionRepository,
)
from src.orchestrator.repositories.postgres import (
    PostgresMaturityRepository,
    PostgresMessageRepository,
    PostgresPRDRepository,
    PostgresRequirementRepository,
    PostgresSessionRepository,
)

if TYPE_CHECKING:
    pass


class RepositoryFactory(Protocol):
    """Protocol for repository factories.

    Defines the interface that all repository factories must implement.
    Each method returns a repository instance for the corresponding domain entity.
    """

    def get_session_repository(self, db_session: AsyncSession) -> ISessionRepository:
        """Get a session repository instance.

        Args:
            db_session: Database session for repository operations.

        Returns:
            Session repository implementation.
        """
        ...

    def get_message_repository(self, db_session: AsyncSession) -> IMessageRepository:
        """Get a message repository instance.

        Args:
            db_session: Database session for repository operations.

        Returns:
            Message repository implementation.
        """
        ...

    def get_requirement_repository(
        self, db_session: AsyncSession
    ) -> IRequirementRepository:
        """Get a requirement repository instance.

        Args:
            db_session: Database session for repository operations.

        Returns:
            Requirement repository implementation.
        """
        ...

    def get_maturity_repository(self, db_session: AsyncSession) -> IMaturityRepository:
        """Get a maturity repository instance.

        Args:
            db_session: Database session for repository operations.

        Returns:
            Maturity repository implementation.
        """
        ...

    def get_prd_repository(self, db_session: AsyncSession) -> IPRDRepository:
        """Get a PRD repository instance.

        Args:
            db_session: Database session for repository operations.

        Returns:
            PRD repository implementation.
        """
        ...


class PostgresRepositoryFactory:
    """Factory for PostgreSQL repositories.

    Creates repository instances backed by PostgreSQL using SQLAlchemy.

    Usage:
        factory = PostgresRepositoryFactory()
        async with db.session() as session:
            session_repo = factory.get_session_repository(session)
            result = await session_repo.get_by_id("session-123")
    """

    def get_session_repository(self, db_session: AsyncSession) -> ISessionRepository:
        """Get a PostgreSQL session repository.

        Args:
            db_session: SQLAlchemy async session.

        Returns:
            PostgresSessionRepository instance.
        """
        return PostgresSessionRepository(db_session)

    def get_message_repository(self, db_session: AsyncSession) -> IMessageRepository:
        """Get a PostgreSQL message repository.

        Args:
            db_session: SQLAlchemy async session.

        Returns:
            PostgresMessageRepository instance.
        """
        return PostgresMessageRepository(db_session)

    def get_requirement_repository(
        self, db_session: AsyncSession
    ) -> IRequirementRepository:
        """Get a PostgreSQL requirement repository.

        Args:
            db_session: SQLAlchemy async session.

        Returns:
            PostgresRequirementRepository instance.
        """
        return PostgresRequirementRepository(db_session)

    def get_maturity_repository(self, db_session: AsyncSession) -> IMaturityRepository:
        """Get a PostgreSQL maturity repository.

        Args:
            db_session: SQLAlchemy async session.

        Returns:
            PostgresMaturityRepository instance.
        """
        return PostgresMaturityRepository(db_session)

    def get_prd_repository(self, db_session: AsyncSession) -> IPRDRepository:
        """Get a PostgreSQL PRD repository.

        Args:
            db_session: SQLAlchemy async session.

        Returns:
            PostgresPRDRepository instance.
        """
        return PostgresPRDRepository(db_session)


def get_repository_factory() -> RepositoryFactory:
    """Get repository factory based on IDEATION_PERSISTENCE_BACKEND env var.

    The factory selection is based on the environment variable:
    - "postgres" (default): Returns PostgresRepositoryFactory
    - "redis": Returns RedisRepositoryFactory

    Returns:
        A repository factory instance.

    Raises:
        ValueError: If the backend is not recognized.
    """
    backend = os.getenv("IDEATION_PERSISTENCE_BACKEND", "postgres")

    if backend == "postgres":
        return PostgresRepositoryFactory()
    elif backend == "redis":
        # Import lazily to avoid circular imports and allow Redis to be optional
        from src.orchestrator.repositories.redis import RedisRepositoryFactory

        return RedisRepositoryFactory()
    else:
        raise ValueError(f"Unknown persistence backend: {backend}")

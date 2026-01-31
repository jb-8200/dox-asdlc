"""PostgreSQL implementation of ISessionRepository.

This module provides the PostgreSQL-backed implementation for session
persistence operations using SQLAlchemy async ORM.
"""


from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.ideation import IdeationSession
from src.orchestrator.persistence.mappers import SessionMapper
from src.orchestrator.persistence.orm_models import SessionORM
from src.orchestrator.repositories.interfaces import ISessionRepository
from src.orchestrator.repositories.validation import validate_id


class PostgresSessionRepository(ISessionRepository):
    """PostgreSQL implementation of session repository.

    Uses SQLAlchemy async session for database operations and mappers
    for domain <-> ORM conversion.

    Args:
        session: SQLAlchemy async session for database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with async session.

        Args:
            session: SQLAlchemy AsyncSession for database operations.
        """
        self._session = session

    async def create(self, session: IdeationSession) -> IdeationSession:
        """Create a new session and return it.

        Converts the domain model to ORM, adds it to the session,
        and flushes to persist.

        Args:
            session: The session to create.

        Returns:
            The created session (same as input since ID is pre-generated).
        """
        orm = SessionMapper.to_orm(session)
        self._session.add(orm)
        await self._session.flush()
        return SessionMapper.from_orm(orm)

    async def get_by_id(self, session_id: str) -> IdeationSession | None:
        """Get session by ID or None if not found.

        Args:
            session_id: The session ID to look up.

        Returns:
            The session if found, None otherwise.

        Raises:
            ValueError: If session_id is empty or too long.
            TypeError: If session_id is not a string.
        """
        validate_id(session_id, "session_id")
        result = await self._session.get(SessionORM, session_id)
        return SessionMapper.from_orm(result) if result else None

    async def update(self, session: IdeationSession) -> None:
        """Update an existing session.

        Uses merge to handle detached objects and upsert behavior.

        Args:
            session: The session with updated values.
        """
        orm = SessionMapper.to_orm(session)
        await self._session.merge(orm)
        await self._session.flush()

    async def delete(self, session_id: str) -> None:
        """Delete session by ID.

        Uses a direct delete statement for efficiency.
        Related data will be cascade deleted via foreign key constraints.

        Args:
            session_id: The ID of the session to delete.

        Raises:
            ValueError: If session_id is empty or too long.
            TypeError: If session_id is not a string.
        """
        validate_id(session_id, "session_id")
        stmt = delete(SessionORM).where(SessionORM.id == session_id)
        await self._session.execute(stmt)
        await self._session.flush()

    async def list_by_user(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> list[IdeationSession]:
        """List sessions for a user, ordered by updated_at desc.

        Args:
            user_id: The user ID to filter by.
            limit: Maximum number of sessions to return (default 50).
            offset: Number of sessions to skip (default 0).

        Returns:
            List of sessions for the user.

        Raises:
            ValueError: If user_id is empty or too long.
            TypeError: If user_id is not a string.
        """
        validate_id(user_id, "user_id")
        stmt = (
            select(SessionORM)
            .where(SessionORM.user_id == user_id)
            .order_by(SessionORM.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [SessionMapper.from_orm(orm) for orm in result.scalars().all()]

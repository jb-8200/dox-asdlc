"""PostgreSQL implementation of IMessageRepository.

This module provides the PostgreSQL-backed implementation for message
persistence operations using SQLAlchemy async ORM.
"""


from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.ideation import ChatMessage
from src.orchestrator.persistence.mappers import MessageMapper
from src.orchestrator.persistence.orm_models import MessageORM
from src.orchestrator.repositories.interfaces import IMessageRepository
from src.orchestrator.repositories.validation import validate_id


class PostgresMessageRepository(IMessageRepository):
    """PostgreSQL implementation of message repository.

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

    async def create(self, message: ChatMessage) -> ChatMessage:
        """Create a new message.

        Converts the domain model to ORM, adds it to the session,
        and flushes to persist.

        Args:
            message: The message to create.

        Returns:
            The created message.
        """
        orm = MessageMapper.to_orm(message)
        self._session.add(orm)
        await self._session.flush()
        return MessageMapper.from_orm(orm)

    async def get_by_session(
        self, session_id: str, limit: int = 100, offset: int = 0
    ) -> list[ChatMessage]:
        """Get messages for session, ordered by timestamp asc.

        Messages are ordered chronologically (oldest first) for proper
        conversation display.

        Args:
            session_id: The session ID to filter by.
            limit: Maximum number of messages to return (default 100).
            offset: Number of messages to skip (default 0).

        Returns:
            List of messages for the session.

        Raises:
            ValueError: If session_id is empty or too long.
            TypeError: If session_id is not a string.
        """
        validate_id(session_id, "session_id")
        stmt = (
            select(MessageORM)
            .where(MessageORM.session_id == session_id)
            .order_by(MessageORM.timestamp.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [MessageMapper.from_orm(orm) for orm in result.scalars().all()]

    async def delete_by_session(self, session_id: str) -> None:
        """Delete all messages for a session.

        Uses a direct delete statement for efficiency.

        Args:
            session_id: The session ID whose messages to delete.

        Raises:
            ValueError: If session_id is empty or too long.
            TypeError: If session_id is not a string.
        """
        validate_id(session_id, "session_id")
        stmt = delete(MessageORM).where(MessageORM.session_id == session_id)
        await self._session.execute(stmt)
        await self._session.flush()

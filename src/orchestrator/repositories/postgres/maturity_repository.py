"""PostgreSQL implementation of IMaturityRepository.

This module provides the PostgreSQL-backed implementation for maturity state
persistence operations using SQLAlchemy async ORM.
"""


from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.ideation import MaturityState
from src.orchestrator.persistence.mappers import MaturityMapper
from src.orchestrator.persistence.orm_models import MaturityORM
from src.orchestrator.repositories.interfaces import IMaturityRepository
from src.orchestrator.repositories.validation import validate_id


class PostgresMaturityRepository(IMaturityRepository):
    """PostgreSQL implementation of maturity repository.

    Uses SQLAlchemy async session for database operations and mappers
    for domain <-> ORM conversion.

    The maturity state uses session_id as primary key, allowing for
    upsert behavior using merge().

    Args:
        session: SQLAlchemy async session for database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with async session.

        Args:
            session: SQLAlchemy AsyncSession for database operations.
        """
        self._session = session

    async def save(self, maturity: MaturityState) -> None:
        """Save or update maturity state (upsert).

        Uses merge() to handle both insert and update cases since
        session_id is the primary key.

        Args:
            maturity: The maturity state to save.
        """
        orm = MaturityMapper.to_orm(maturity)
        await self._session.merge(orm)
        await self._session.flush()

    async def get_by_session(self, session_id: str) -> MaturityState | None:
        """Get maturity state for session.

        Args:
            session_id: The session ID to look up.

        Returns:
            The maturity state if found, None otherwise.

        Raises:
            ValueError: If session_id is empty or too long.
            TypeError: If session_id is not a string.
        """
        validate_id(session_id, "session_id")
        result = await self._session.get(MaturityORM, session_id)
        return MaturityMapper.from_orm(result) if result else None

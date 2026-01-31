"""PostgreSQL implementation of IRequirementRepository.

This module provides the PostgreSQL-backed implementation for requirement
persistence operations using SQLAlchemy async ORM.
"""


from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.ideation import ExtractedRequirement
from src.orchestrator.persistence.mappers import RequirementMapper
from src.orchestrator.persistence.orm_models import RequirementORM
from src.orchestrator.repositories.interfaces import IRequirementRepository
from src.orchestrator.repositories.validation import validate_id


class PostgresRequirementRepository(IRequirementRepository):
    """PostgreSQL implementation of requirement repository.

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

    async def create(self, requirement: ExtractedRequirement) -> ExtractedRequirement:
        """Create a new requirement.

        Converts the domain model to ORM, adds it to the session,
        and flushes to persist.

        Args:
            requirement: The requirement to create.

        Returns:
            The created requirement.
        """
        orm = RequirementMapper.to_orm(requirement)
        self._session.add(orm)
        await self._session.flush()
        return RequirementMapper.from_orm(orm)

    async def get_by_session(self, session_id: str) -> list[ExtractedRequirement]:
        """Get all requirements for a session.

        Args:
            session_id: The session ID to filter by.

        Returns:
            List of requirements for the session.

        Raises:
            ValueError: If session_id is empty or too long.
            TypeError: If session_id is not a string.
        """
        validate_id(session_id, "session_id")
        stmt = select(RequirementORM).where(RequirementORM.session_id == session_id)
        result = await self._session.execute(stmt)
        return [RequirementMapper.from_orm(orm) for orm in result.scalars().all()]

    async def update(self, requirement: ExtractedRequirement) -> None:
        """Update an existing requirement.

        Uses merge to handle detached objects and upsert behavior.

        Args:
            requirement: The requirement with updated values.
        """
        orm = RequirementMapper.to_orm(requirement)
        await self._session.merge(orm)
        await self._session.flush()

    async def delete(self, requirement_id: str) -> None:
        """Delete a requirement by ID.

        Uses a direct delete statement for efficiency.

        Args:
            requirement_id: The ID of the requirement to delete.

        Raises:
            ValueError: If requirement_id is empty or too long.
            TypeError: If requirement_id is not a string.
        """
        validate_id(requirement_id, "requirement_id")
        stmt = delete(RequirementORM).where(RequirementORM.id == requirement_id)
        await self._session.execute(stmt)
        await self._session.flush()

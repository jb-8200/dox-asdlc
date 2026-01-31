"""PostgreSQL implementation of IPRDRepository.

This module provides the PostgreSQL-backed implementation for PRD draft
and user story persistence operations using SQLAlchemy async ORM.
"""


from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.ideation import PRDDraft, UserStory
from src.orchestrator.persistence.mappers import PRDMapper, UserStoryMapper
from src.orchestrator.persistence.orm_models import PRDDraftORM, UserStoryORM
from src.orchestrator.repositories.interfaces import IPRDRepository
from src.orchestrator.repositories.validation import validate_id


class PostgresPRDRepository(IPRDRepository):
    """PostgreSQL implementation of PRD repository.

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

    async def save_draft(self, draft: PRDDraft) -> PRDDraft:
        """Save a PRD draft.

        Converts the domain model to ORM, adds it to the session,
        and flushes to persist.

        Args:
            draft: The PRD draft to save.

        Returns:
            The saved PRD draft.
        """
        orm = PRDMapper.to_orm(draft)
        self._session.add(orm)
        await self._session.flush()
        return PRDMapper.from_orm(orm)

    async def get_draft(self, session_id: str) -> PRDDraft | None:
        """Get latest PRD draft for session.

        Returns the most recently created draft for the session.
        Orders by created_at descending and takes the first result.

        Args:
            session_id: The session ID to look up.

        Returns:
            The PRD draft if found, None otherwise.

        Raises:
            ValueError: If session_id is empty or too long.
            TypeError: If session_id is not a string.
        """
        validate_id(session_id, "session_id")
        stmt = (
            select(PRDDraftORM)
            .where(PRDDraftORM.session_id == session_id)
            .order_by(PRDDraftORM.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        orm = result.scalars().first()
        return PRDMapper.from_orm(orm) if orm else None

    async def save_user_stories(
        self, session_id: str, stories: list[UserStory]
    ) -> None:
        """Save user stories for session.

        Replaces all existing user stories for the session with the new ones.
        First deletes existing stories, then adds the new ones.

        Args:
            session_id: The session ID to associate stories with.
            stories: List of user stories to save.

        Raises:
            ValueError: If session_id is empty or too long.
            TypeError: If session_id is not a string.
        """
        validate_id(session_id, "session_id")
        # Delete existing stories for this session
        delete_stmt = delete(UserStoryORM).where(
            UserStoryORM.session_id == session_id
        )
        await self._session.execute(delete_stmt)

        # Add new stories
        for story in stories:
            orm = UserStoryMapper.to_orm(story)
            self._session.add(orm)

        await self._session.flush()

    async def get_user_stories(self, session_id: str) -> list[UserStory]:
        """Get user stories for session.

        Args:
            session_id: The session ID to look up.

        Returns:
            List of user stories for the session.

        Raises:
            ValueError: If session_id is empty or too long.
            TypeError: If session_id is not a string.
        """
        validate_id(session_id, "session_id")
        stmt = select(UserStoryORM).where(UserStoryORM.session_id == session_id)
        result = await self._session.execute(stmt)
        return [UserStoryMapper.from_orm(orm) for orm in result.scalars().all()]

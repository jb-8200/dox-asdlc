"""Tests for P02-F09 Task T14: PostgresPRDRepository.

This module tests the PostgreSQL implementation of IPRDRepository:
- save_draft() - Save PRD draft
- get_draft() - Get latest draft for session
- save_user_stories() - Bulk save user stories
- get_user_stories() - Get all user stories for session
"""

from datetime import datetime
from typing import Any, List
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.models.ideation import (
    PRDDraft,
    PRDSection,
    RequirementPriority,
    UserStory,
)
from src.orchestrator.persistence.orm_models import PRDDraftORM, UserStoryORM
from src.orchestrator.repositories.interfaces import IPRDRepository


def make_domain_prd_draft(
    draft_id: str = "prd-123",
    session_id: str = "session-456",
    title: str = "Test PRD Document",
    version: str = "0.1.0",
    status: str = "draft",
) -> PRDDraft:
    """Create a domain PRDDraft for testing."""
    return PRDDraft(
        id=draft_id,
        session_id=session_id,
        title=title,
        version=version,
        sections=[
            PRDSection(
                id="sec-1",
                heading="Overview",
                content="This is the overview.",
                order=1,
            ),
            PRDSection(
                id="sec-2",
                heading="Goals",
                content="These are the goals.",
                order=2,
            ),
        ],
        status=status,
        created_at=datetime(2024, 1, 15, 10, 30, 0),
    )


def make_orm_prd_draft(
    draft_id: str = "prd-123",
    session_id: str = "session-456",
    title: str = "Test PRD Document",
    version: str = "0.1.0",
    status: str = "draft",
) -> PRDDraftORM:
    """Create an ORM PRDDraftORM for testing."""
    return PRDDraftORM(
        id=draft_id,
        session_id=session_id,
        title=title,
        version=version,
        sections=[
            {"id": "sec-1", "heading": "Overview", "content": "This is the overview.", "order": 1},
            {"id": "sec-2", "heading": "Goals", "content": "These are the goals.", "order": 2},
        ],
        status=status,
        created_at=datetime(2024, 1, 15, 10, 30, 0),
    )


def make_domain_user_story(
    story_id: str = "story-123",
    session_id: str = "session-456",
    title: str = "User Login",
    priority: RequirementPriority = RequirementPriority.MUST_HAVE,
) -> UserStory:
    """Create a domain UserStory for testing."""
    return UserStory(
        id=story_id,
        session_id=session_id,
        title=title,
        as_a="registered user",
        i_want="to login to my account",
        so_that="I can access my personal data",
        acceptance_criteria=[
            "Given valid credentials, login succeeds",
            "Given invalid credentials, error shown",
        ],
        linked_requirements=["req-123"],
        priority=priority,
        created_at=datetime(2024, 1, 15, 10, 30, 0),
    )


def make_orm_user_story(
    story_id: str = "story-123",
    session_id: str = "session-456",
    title: str = "User Login",
    priority: str = "must_have",
) -> UserStoryORM:
    """Create an ORM UserStoryORM for testing."""
    return UserStoryORM(
        id=story_id,
        session_id=session_id,
        title=title,
        as_a="registered user",
        i_want="to login to my account",
        so_that="I can access my personal data",
        acceptance_criteria=[
            "Given valid credentials, login succeeds",
            "Given invalid credentials, error shown",
        ],
        linked_requirements=["req-123"],
        priority=priority,
        created_at=datetime(2024, 1, 15, 10, 30, 0),
    )


class TestPostgresPRDRepositoryImport:
    """Test that PostgresPRDRepository can be imported."""

    def test_import_repository(self) -> None:
        """Test that repository module can be imported."""
        from src.orchestrator.repositories.postgres.prd_repository import (
            PostgresPRDRepository,
        )
        assert PostgresPRDRepository is not None

    def test_implements_interface(self) -> None:
        """Test that PostgresPRDRepository implements IPRDRepository."""
        from src.orchestrator.repositories.postgres.prd_repository import (
            PostgresPRDRepository,
        )
        assert issubclass(PostgresPRDRepository, IPRDRepository)


class TestPostgresPRDRepositorySaveDraft:
    """Test PostgresPRDRepository.save_draft() method."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_save_draft_adds_orm_to_session(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that save_draft() adds ORM object to session."""
        from src.orchestrator.repositories.postgres.prd_repository import (
            PostgresPRDRepository,
        )

        repo = PostgresPRDRepository(mock_session)
        domain_draft = make_domain_prd_draft()

        result = await repo.save_draft(domain_draft)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_draft_returns_domain_model(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that save_draft() returns a domain PRDDraft."""
        from src.orchestrator.repositories.postgres.prd_repository import (
            PostgresPRDRepository,
        )

        repo = PostgresPRDRepository(mock_session)
        domain_draft = make_domain_prd_draft()

        result = await repo.save_draft(domain_draft)

        assert isinstance(result, PRDDraft)
        assert result.id == "prd-123"
        assert result.session_id == "session-456"
        assert result.title == "Test PRD Document"

    @pytest.mark.asyncio
    async def test_save_draft_converts_to_orm(self, mock_session: AsyncMock) -> None:
        """Test that save_draft() converts domain to ORM for storage."""
        from src.orchestrator.repositories.postgres.prd_repository import (
            PostgresPRDRepository,
        )

        repo = PostgresPRDRepository(mock_session)
        domain_draft = make_domain_prd_draft(
            title="Updated PRD",
            version="1.0.0",
            status="approved",
        )

        await repo.save_draft(domain_draft)

        added_orm = mock_session.add.call_args[0][0]
        assert isinstance(added_orm, PRDDraftORM)
        assert added_orm.title == "Updated PRD"
        assert added_orm.version == "1.0.0"
        assert added_orm.status == "approved"

    @pytest.mark.asyncio
    async def test_save_draft_serializes_sections(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that save_draft() serializes sections to JSONB."""
        from src.orchestrator.repositories.postgres.prd_repository import (
            PostgresPRDRepository,
        )

        repo = PostgresPRDRepository(mock_session)
        domain_draft = make_domain_prd_draft()

        await repo.save_draft(domain_draft)

        added_orm = mock_session.add.call_args[0][0]
        assert isinstance(added_orm.sections, list)
        assert len(added_orm.sections) == 2
        assert added_orm.sections[0]["heading"] == "Overview"


class TestPostgresPRDRepositoryGetDraft:
    """Test PostgresPRDRepository.get_draft() method."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock AsyncSession."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_get_draft_returns_latest_draft(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that get_draft() returns the latest draft for session."""
        from src.orchestrator.repositories.postgres.prd_repository import (
            PostgresPRDRepository,
        )

        orm_draft = make_orm_prd_draft()

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = orm_draft
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = PostgresPRDRepository(mock_session)
        result = await repo.get_draft("session-456")

        assert result is not None
        assert isinstance(result, PRDDraft)
        assert result.id == "prd-123"
        assert result.session_id == "session-456"

    @pytest.mark.asyncio
    async def test_get_draft_returns_none_when_not_found(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that get_draft() returns None when no draft found."""
        from src.orchestrator.repositories.postgres.prd_repository import (
            PostgresPRDRepository,
        )

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = PostgresPRDRepository(mock_session)
        result = await repo.get_draft("nonexistent-session")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_draft_deserializes_sections(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that get_draft() deserializes sections from JSONB."""
        from src.orchestrator.repositories.postgres.prd_repository import (
            PostgresPRDRepository,
        )

        orm_draft = make_orm_prd_draft()

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = orm_draft
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = PostgresPRDRepository(mock_session)
        result = await repo.get_draft("session-456")

        assert result is not None
        assert len(result.sections) == 2
        assert isinstance(result.sections[0], PRDSection)
        assert result.sections[0].heading == "Overview"


class TestPostgresPRDRepositorySaveUserStories:
    """Test PostgresPRDRepository.save_user_stories() method."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.add = MagicMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_save_user_stories_adds_all_stories(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that save_user_stories() adds all stories to session."""
        from src.orchestrator.repositories.postgres.prd_repository import (
            PostgresPRDRepository,
        )

        repo = PostgresPRDRepository(mock_session)
        stories = [
            make_domain_user_story("story-1", "session-123"),
            make_domain_user_story("story-2", "session-123"),
        ]

        await repo.save_user_stories("session-123", stories)

        # Should call add for each story
        assert mock_session.add.call_count == 2
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_user_stories_converts_to_orm(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that save_user_stories() converts domain to ORM."""
        from src.orchestrator.repositories.postgres.prd_repository import (
            PostgresPRDRepository,
        )

        repo = PostgresPRDRepository(mock_session)
        stories = [make_domain_user_story("story-1", "session-123")]

        await repo.save_user_stories("session-123", stories)

        added_orm = mock_session.add.call_args[0][0]
        assert isinstance(added_orm, UserStoryORM)
        assert added_orm.id == "story-1"
        assert added_orm.session_id == "session-123"
        assert added_orm.priority == "must_have"

    @pytest.mark.asyncio
    async def test_save_user_stories_handles_empty_list(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that save_user_stories() handles empty list."""
        from src.orchestrator.repositories.postgres.prd_repository import (
            PostgresPRDRepository,
        )

        repo = PostgresPRDRepository(mock_session)

        await repo.save_user_stories("session-123", [])

        mock_session.add.assert_not_called()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_user_stories_deletes_existing_first(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that save_user_stories() deletes existing stories first."""
        from src.orchestrator.repositories.postgres.prd_repository import (
            PostgresPRDRepository,
        )

        repo = PostgresPRDRepository(mock_session)
        stories = [make_domain_user_story("story-1", "session-123")]

        await repo.save_user_stories("session-123", stories)

        # Should execute delete before adding new stories
        mock_session.execute.assert_called_once()


class TestPostgresPRDRepositoryGetUserStories:
    """Test PostgresPRDRepository.get_user_stories() method."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock AsyncSession."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_get_user_stories_returns_stories(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that get_user_stories() returns list of stories."""
        from src.orchestrator.repositories.postgres.prd_repository import (
            PostgresPRDRepository,
        )

        orm_stories = [
            make_orm_user_story("story-1", "session-123"),
            make_orm_user_story("story-2", "session-123"),
        ]

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = orm_stories
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = PostgresPRDRepository(mock_session)
        result = await repo.get_user_stories("session-123")

        assert len(result) == 2
        assert all(isinstance(s, UserStory) for s in result)
        assert result[0].id == "story-1"
        assert result[1].id == "story-2"

    @pytest.mark.asyncio
    async def test_get_user_stories_returns_empty_list(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that get_user_stories() returns empty list when no stories."""
        from src.orchestrator.repositories.postgres.prd_repository import (
            PostgresPRDRepository,
        )

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = PostgresPRDRepository(mock_session)
        result = await repo.get_user_stories("session-no-stories")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_user_stories_converts_to_domain(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that get_user_stories() converts ORM to domain models."""
        from src.orchestrator.repositories.postgres.prd_repository import (
            PostgresPRDRepository,
        )

        orm_stories = [make_orm_user_story()]

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = orm_stories
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = PostgresPRDRepository(mock_session)
        result = await repo.get_user_stories("session-456")

        assert len(result) == 1
        story = result[0]
        assert isinstance(story, UserStory)
        assert story.as_a == "registered user"
        assert story.i_want == "to login to my account"
        assert story.so_that == "I can access my personal data"
        assert story.priority == RequirementPriority.MUST_HAVE

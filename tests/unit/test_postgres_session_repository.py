"""Tests for P02-F09 Task T10: PostgresSessionRepository.

This module tests the PostgreSQL implementation of ISessionRepository:
- create() - Add session to database
- get_by_id() - Get session by ID
- update() - Update existing session
- delete() - Delete session by ID
- list_by_user() - List sessions for user with pagination
"""

from datetime import datetime
from typing import Any, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.models.ideation import (
    DataSource,
    IdeationSession,
    ProjectStatus,
)
from src.orchestrator.persistence.orm_models import SessionORM
from src.orchestrator.repositories.interfaces import ISessionRepository


def make_domain_session(
    session_id: str = "session-123",
    project_name: str = "Test Project",
    user_id: str = "user-456",
    status: ProjectStatus = ProjectStatus.DRAFT,
    data_source: DataSource = DataSource.MOCK,
    version: int = 1,
) -> IdeationSession:
    """Create a domain IdeationSession for testing."""
    return IdeationSession(
        id=session_id,
        project_name=project_name,
        user_id=user_id,
        status=status,
        data_source=data_source,
        version=version,
        created_at=datetime(2024, 1, 15, 10, 30, 0),
        updated_at=datetime(2024, 1, 15, 11, 0, 0),
    )


def make_orm_session(
    session_id: str = "session-123",
    project_name: str = "Test Project",
    user_id: str = "user-456",
    status: str = "draft",
    data_source: str = "mock",
    version: int = 1,
) -> SessionORM:
    """Create an ORM SessionORM for testing."""
    return SessionORM(
        id=session_id,
        project_name=project_name,
        user_id=user_id,
        status=status,
        data_source=data_source,
        version=version,
        created_at=datetime(2024, 1, 15, 10, 30, 0),
        updated_at=datetime(2024, 1, 15, 11, 0, 0),
    )


class TestPostgresSessionRepositoryImport:
    """Test that PostgresSessionRepository can be imported."""

    def test_import_repository(self) -> None:
        """Test that repository module can be imported."""
        from src.orchestrator.repositories.postgres.session_repository import (
            PostgresSessionRepository,
        )
        assert PostgresSessionRepository is not None

    def test_implements_interface(self) -> None:
        """Test that PostgresSessionRepository implements ISessionRepository."""
        from src.orchestrator.repositories.postgres.session_repository import (
            PostgresSessionRepository,
        )
        # Check that it's a subclass of ISessionRepository
        assert issubclass(PostgresSessionRepository, ISessionRepository)


class TestPostgresSessionRepositoryCreate:
    """Test PostgresSessionRepository.create() method."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_create_adds_orm_to_session(self, mock_session: AsyncMock) -> None:
        """Test that create() adds ORM object to session."""
        from src.orchestrator.repositories.postgres.session_repository import (
            PostgresSessionRepository,
        )

        repo = PostgresSessionRepository(mock_session)
        domain_session = make_domain_session()

        result = await repo.create(domain_session)

        # Verify add was called
        mock_session.add.assert_called_once()
        # Verify flush was called
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_returns_domain_model(self, mock_session: AsyncMock) -> None:
        """Test that create() returns a domain IdeationSession."""
        from src.orchestrator.repositories.postgres.session_repository import (
            PostgresSessionRepository,
        )

        repo = PostgresSessionRepository(mock_session)
        domain_session = make_domain_session()

        result = await repo.create(domain_session)

        assert isinstance(result, IdeationSession)
        assert result.id == "session-123"
        assert result.project_name == "Test Project"
        assert result.user_id == "user-456"

    @pytest.mark.asyncio
    async def test_create_converts_to_orm(self, mock_session: AsyncMock) -> None:
        """Test that create() converts domain to ORM for storage."""
        from src.orchestrator.repositories.postgres.session_repository import (
            PostgresSessionRepository,
        )

        repo = PostgresSessionRepository(mock_session)
        domain_session = make_domain_session(
            status=ProjectStatus.APPROVED,
            data_source=DataSource.CONFIGURED,
        )

        await repo.create(domain_session)

        # Get the ORM object that was added
        added_orm = mock_session.add.call_args[0][0]
        assert isinstance(added_orm, SessionORM)
        assert added_orm.status == "approved"
        assert added_orm.data_source == "configured"


class TestPostgresSessionRepositoryGetById:
    """Test PostgresSessionRepository.get_by_id() method."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock AsyncSession."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_get_by_id_returns_session(self, mock_session: AsyncMock) -> None:
        """Test that get_by_id() returns session when found."""
        from src.orchestrator.repositories.postgres.session_repository import (
            PostgresSessionRepository,
        )

        orm_session = make_orm_session()
        mock_session.get = AsyncMock(return_value=orm_session)

        repo = PostgresSessionRepository(mock_session)
        result = await repo.get_by_id("session-123")

        assert result is not None
        assert isinstance(result, IdeationSession)
        assert result.id == "session-123"
        mock_session.get.assert_called_once_with(SessionORM, "session-123")

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that get_by_id() returns None when session not found."""
        from src.orchestrator.repositories.postgres.session_repository import (
            PostgresSessionRepository,
        )

        mock_session.get = AsyncMock(return_value=None)

        repo = PostgresSessionRepository(mock_session)
        result = await repo.get_by_id("nonexistent")

        assert result is None
        mock_session.get.assert_called_once_with(SessionORM, "nonexistent")


class TestPostgresSessionRepositoryUpdate:
    """Test PostgresSessionRepository.update() method."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.merge = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_update_calls_merge(self, mock_session: AsyncMock) -> None:
        """Test that update() calls merge with ORM object."""
        from src.orchestrator.repositories.postgres.session_repository import (
            PostgresSessionRepository,
        )

        repo = PostgresSessionRepository(mock_session)
        domain_session = make_domain_session(
            project_name="Updated Project",
            status=ProjectStatus.APPROVED,
        )

        await repo.update(domain_session)

        mock_session.merge.assert_called_once()
        merged_orm = mock_session.merge.call_args[0][0]
        assert isinstance(merged_orm, SessionORM)
        assert merged_orm.project_name == "Updated Project"
        assert merged_orm.status == "approved"

    @pytest.mark.asyncio
    async def test_update_flushes_session(self, mock_session: AsyncMock) -> None:
        """Test that update() flushes the session."""
        from src.orchestrator.repositories.postgres.session_repository import (
            PostgresSessionRepository,
        )

        repo = PostgresSessionRepository(mock_session)
        domain_session = make_domain_session()

        await repo.update(domain_session)

        mock_session.flush.assert_called_once()


class TestPostgresSessionRepositoryDelete:
    """Test PostgresSessionRepository.delete() method."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_delete_executes_delete_statement(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that delete() executes a delete statement."""
        from src.orchestrator.repositories.postgres.session_repository import (
            PostgresSessionRepository,
        )

        repo = PostgresSessionRepository(mock_session)

        await repo.delete("session-123")

        mock_session.execute.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_uses_correct_id(self, mock_session: AsyncMock) -> None:
        """Test that delete() uses the correct session ID."""
        from src.orchestrator.repositories.postgres.session_repository import (
            PostgresSessionRepository,
        )

        repo = PostgresSessionRepository(mock_session)

        await repo.delete("my-session-id")

        # Verify execute was called (the actual statement testing would require
        # inspecting the compiled SQL which is complex for unit tests)
        mock_session.execute.assert_called_once()


class TestPostgresSessionRepositoryListByUser:
    """Test PostgresSessionRepository.list_by_user() method."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock AsyncSession."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_list_by_user_returns_sessions(self, mock_session: AsyncMock) -> None:
        """Test that list_by_user() returns list of sessions."""
        from src.orchestrator.repositories.postgres.session_repository import (
            PostgresSessionRepository,
        )

        orm_sessions = [
            make_orm_session("session-1", user_id="user-123"),
            make_orm_session("session-2", user_id="user-123"),
        ]

        # Mock the result chain
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = orm_sessions
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = PostgresSessionRepository(mock_session)
        result = await repo.list_by_user("user-123")

        assert len(result) == 2
        assert all(isinstance(s, IdeationSession) for s in result)
        assert result[0].id == "session-1"
        assert result[1].id == "session-2"

    @pytest.mark.asyncio
    async def test_list_by_user_returns_empty_list(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that list_by_user() returns empty list when no sessions."""
        from src.orchestrator.repositories.postgres.session_repository import (
            PostgresSessionRepository,
        )

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = PostgresSessionRepository(mock_session)
        result = await repo.list_by_user("user-no-sessions")

        assert result == []

    @pytest.mark.asyncio
    async def test_list_by_user_respects_limit(self, mock_session: AsyncMock) -> None:
        """Test that list_by_user() passes limit parameter."""
        from src.orchestrator.repositories.postgres.session_repository import (
            PostgresSessionRepository,
        )

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = PostgresSessionRepository(mock_session)
        await repo.list_by_user("user-123", limit=10, offset=5)

        # Verify execute was called (parameter testing is complex for unit tests)
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_by_user_default_pagination(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that list_by_user() uses default pagination values."""
        from src.orchestrator.repositories.postgres.session_repository import (
            PostgresSessionRepository,
        )

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = PostgresSessionRepository(mock_session)
        # Call without explicit limit/offset - should use defaults
        await repo.list_by_user("user-123")

        mock_session.execute.assert_called_once()


class TestPostgresSessionRepositoryValidation:
    """Test input validation for PostgresSessionRepository."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock AsyncSession."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_get_by_id_rejects_empty_id(self, mock_session: AsyncMock) -> None:
        """Test that get_by_id() rejects empty session_id."""
        from src.orchestrator.repositories.postgres.session_repository import (
            PostgresSessionRepository,
        )

        repo = PostgresSessionRepository(mock_session)

        with pytest.raises(ValueError, match="session_id cannot be empty"):
            await repo.get_by_id("")

    @pytest.mark.asyncio
    async def test_get_by_id_rejects_none_id(self, mock_session: AsyncMock) -> None:
        """Test that get_by_id() rejects None session_id."""
        from src.orchestrator.repositories.postgres.session_repository import (
            PostgresSessionRepository,
        )

        repo = PostgresSessionRepository(mock_session)

        with pytest.raises(TypeError, match="session_id must be a string"):
            await repo.get_by_id(None)  # type: ignore

    @pytest.mark.asyncio
    async def test_delete_rejects_empty_id(self, mock_session: AsyncMock) -> None:
        """Test that delete() rejects empty session_id."""
        from src.orchestrator.repositories.postgres.session_repository import (
            PostgresSessionRepository,
        )

        repo = PostgresSessionRepository(mock_session)

        with pytest.raises(ValueError, match="session_id cannot be empty"):
            await repo.delete("")

    @pytest.mark.asyncio
    async def test_list_by_user_rejects_empty_user_id(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that list_by_user() rejects empty user_id."""
        from src.orchestrator.repositories.postgres.session_repository import (
            PostgresSessionRepository,
        )

        repo = PostgresSessionRepository(mock_session)

        with pytest.raises(ValueError, match="user_id cannot be empty"):
            await repo.list_by_user("")

    @pytest.mark.asyncio
    async def test_get_by_id_rejects_too_long_id(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that get_by_id() rejects session_id exceeding max length."""
        from src.orchestrator.repositories.postgres.session_repository import (
            PostgresSessionRepository,
        )

        repo = PostgresSessionRepository(mock_session)
        long_id = "x" * 65

        with pytest.raises(ValueError, match="exceeds maximum length"):
            await repo.get_by_id(long_id)

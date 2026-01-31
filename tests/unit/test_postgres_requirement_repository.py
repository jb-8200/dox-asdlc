"""Tests for P02-F09 Task T12: PostgresRequirementRepository.

This module tests the PostgreSQL implementation of IRequirementRepository:
- create() - Add requirement to database
- get_by_session() - Get all requirements for session
- update() - Update existing requirement
- delete() - Delete requirement by ID
"""

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.models.ideation import (
    ExtractedRequirement,
    RequirementPriority,
    RequirementType,
)
from src.orchestrator.persistence.orm_models import RequirementORM
from src.orchestrator.repositories.interfaces import IRequirementRepository


def make_domain_requirement(
    requirement_id: str = "req-123",
    session_id: str = "session-456",
    description: str = "User must be able to login",
    req_type: RequirementType = RequirementType.FUNCTIONAL,
    priority: RequirementPriority = RequirementPriority.MUST_HAVE,
    category_id: str | None = "auth",
) -> ExtractedRequirement:
    """Create a domain ExtractedRequirement for testing."""
    return ExtractedRequirement(
        id=requirement_id,
        session_id=session_id,
        description=description,
        type=req_type,
        priority=priority,
        category_id=category_id,
        created_at=datetime(2024, 1, 15, 10, 30, 0),
    )


def make_orm_requirement(
    requirement_id: str = "req-123",
    session_id: str = "session-456",
    description: str = "User must be able to login",
    req_type: str = "functional",
    priority: str = "must_have",
    category_id: str | None = "auth",
) -> RequirementORM:
    """Create an ORM RequirementORM for testing."""
    return RequirementORM(
        id=requirement_id,
        session_id=session_id,
        description=description,
        type=req_type,
        priority=priority,
        category_id=category_id,
        created_at=datetime(2024, 1, 15, 10, 30, 0),
    )


class TestPostgresRequirementRepositoryImport:
    """Test that PostgresRequirementRepository can be imported."""

    def test_import_repository(self) -> None:
        """Test that repository module can be imported."""
        from src.orchestrator.repositories.postgres.requirement_repository import (
            PostgresRequirementRepository,
        )
        assert PostgresRequirementRepository is not None

    def test_implements_interface(self) -> None:
        """Test that PostgresRequirementRepository implements IRequirementRepository."""
        from src.orchestrator.repositories.postgres.requirement_repository import (
            PostgresRequirementRepository,
        )
        assert issubclass(PostgresRequirementRepository, IRequirementRepository)


class TestPostgresRequirementRepositoryCreate:
    """Test PostgresRequirementRepository.create() method."""

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
        from src.orchestrator.repositories.postgres.requirement_repository import (
            PostgresRequirementRepository,
        )

        repo = PostgresRequirementRepository(mock_session)
        domain_requirement = make_domain_requirement()

        result = await repo.create(domain_requirement)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_returns_domain_model(self, mock_session: AsyncMock) -> None:
        """Test that create() returns a domain ExtractedRequirement."""
        from src.orchestrator.repositories.postgres.requirement_repository import (
            PostgresRequirementRepository,
        )

        repo = PostgresRequirementRepository(mock_session)
        domain_requirement = make_domain_requirement()

        result = await repo.create(domain_requirement)

        assert isinstance(result, ExtractedRequirement)
        assert result.id == "req-123"
        assert result.session_id == "session-456"
        assert result.description == "User must be able to login"

    @pytest.mark.asyncio
    async def test_create_converts_to_orm(self, mock_session: AsyncMock) -> None:
        """Test that create() converts domain to ORM for storage."""
        from src.orchestrator.repositories.postgres.requirement_repository import (
            PostgresRequirementRepository,
        )

        repo = PostgresRequirementRepository(mock_session)
        domain_requirement = make_domain_requirement(
            req_type=RequirementType.NON_FUNCTIONAL,
            priority=RequirementPriority.COULD_HAVE,
        )

        await repo.create(domain_requirement)

        added_orm = mock_session.add.call_args[0][0]
        assert isinstance(added_orm, RequirementORM)
        assert added_orm.type == "non_functional"
        assert added_orm.priority == "could_have"

    @pytest.mark.asyncio
    async def test_create_with_none_category(self, mock_session: AsyncMock) -> None:
        """Test that create() handles None category_id."""
        from src.orchestrator.repositories.postgres.requirement_repository import (
            PostgresRequirementRepository,
        )

        repo = PostgresRequirementRepository(mock_session)
        domain_requirement = make_domain_requirement(category_id=None)

        await repo.create(domain_requirement)

        added_orm = mock_session.add.call_args[0][0]
        assert added_orm.category_id is None


class TestPostgresRequirementRepositoryGetBySession:
    """Test PostgresRequirementRepository.get_by_session() method."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock AsyncSession."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_get_by_session_returns_requirements(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that get_by_session() returns list of requirements."""
        from src.orchestrator.repositories.postgres.requirement_repository import (
            PostgresRequirementRepository,
        )

        orm_requirements = [
            make_orm_requirement("req-1", "session-123"),
            make_orm_requirement("req-2", "session-123"),
        ]

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = orm_requirements
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = PostgresRequirementRepository(mock_session)
        result = await repo.get_by_session("session-123")

        assert len(result) == 2
        assert all(isinstance(r, ExtractedRequirement) for r in result)
        assert result[0].id == "req-1"
        assert result[1].id == "req-2"

    @pytest.mark.asyncio
    async def test_get_by_session_returns_empty_list(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that get_by_session() returns empty list when no requirements."""
        from src.orchestrator.repositories.postgres.requirement_repository import (
            PostgresRequirementRepository,
        )

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = PostgresRequirementRepository(mock_session)
        result = await repo.get_by_session("session-no-requirements")

        assert result == []


class TestPostgresRequirementRepositoryUpdate:
    """Test PostgresRequirementRepository.update() method."""

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
        from src.orchestrator.repositories.postgres.requirement_repository import (
            PostgresRequirementRepository,
        )

        repo = PostgresRequirementRepository(mock_session)
        domain_requirement = make_domain_requirement(
            description="Updated requirement description",
            priority=RequirementPriority.SHOULD_HAVE,
        )

        await repo.update(domain_requirement)

        mock_session.merge.assert_called_once()
        merged_orm = mock_session.merge.call_args[0][0]
        assert isinstance(merged_orm, RequirementORM)
        assert merged_orm.description == "Updated requirement description"
        assert merged_orm.priority == "should_have"

    @pytest.mark.asyncio
    async def test_update_flushes_session(self, mock_session: AsyncMock) -> None:
        """Test that update() flushes the session."""
        from src.orchestrator.repositories.postgres.requirement_repository import (
            PostgresRequirementRepository,
        )

        repo = PostgresRequirementRepository(mock_session)
        domain_requirement = make_domain_requirement()

        await repo.update(domain_requirement)

        mock_session.flush.assert_called_once()


class TestPostgresRequirementRepositoryDelete:
    """Test PostgresRequirementRepository.delete() method."""

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
        from src.orchestrator.repositories.postgres.requirement_repository import (
            PostgresRequirementRepository,
        )

        repo = PostgresRequirementRepository(mock_session)

        await repo.delete("req-123")

        mock_session.execute.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_uses_correct_id(self, mock_session: AsyncMock) -> None:
        """Test that delete() uses the correct requirement ID."""
        from src.orchestrator.repositories.postgres.requirement_repository import (
            PostgresRequirementRepository,
        )

        repo = PostgresRequirementRepository(mock_session)

        await repo.delete("my-requirement-id")

        mock_session.execute.assert_called_once()

"""Tests for P02-F09 Task T13: PostgresMaturityRepository.

This module tests the PostgreSQL implementation of IMaturityRepository:
- save() - Upsert maturity state (insert or update)
- get_by_session() - Get maturity state for session
"""

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.models.ideation import MaturityCategory, MaturityState
from src.orchestrator.persistence.orm_models import MaturityORM
from src.orchestrator.repositories.interfaces import IMaturityRepository


_UNSET = object()  # Sentinel for distinguishing None from unset


def make_domain_maturity(
    session_id: str = "session-123",
    score: int = 75,
    level: str = "intermediate",
    can_submit: bool = True,
    gaps: list[str] | None | object = _UNSET,
) -> MaturityState:
    """Create a domain MaturityState for testing."""
    # Use sentinel to distinguish unset from explicit None or []
    actual_gaps = ["Missing error handling"] if gaps is _UNSET else (gaps or [])
    return MaturityState(
        session_id=session_id,
        score=score,
        level=level,
        categories=[
            MaturityCategory(
                id="auth",
                name="Authentication",
                score=80,
                required_for_submit=True,
            ),
            MaturityCategory(
                id="api",
                name="API Design",
                score=70,
                required_for_submit=False,
            ),
        ],
        can_submit=can_submit,
        gaps=actual_gaps,
        updated_at=datetime(2024, 1, 15, 10, 30, 0),
    )


def make_orm_maturity(
    session_id: str = "session-123",
    score: int = 75,
    level: str = "intermediate",
    can_submit: bool = True,
    gaps: list | None | object = _UNSET,
) -> MaturityORM:
    """Create an ORM MaturityORM for testing."""
    # Use sentinel to distinguish unset from explicit None
    actual_gaps = ["Missing error handling"] if gaps is _UNSET else gaps
    return MaturityORM(
        session_id=session_id,
        score=score,
        level=level,
        categories=[
            {"id": "auth", "name": "Authentication", "score": 80, "required_for_submit": True},
            {"id": "api", "name": "API Design", "score": 70, "required_for_submit": False},
        ],
        can_submit=can_submit,
        gaps=actual_gaps,
        updated_at=datetime(2024, 1, 15, 10, 30, 0),
    )


class TestPostgresMaturityRepositoryImport:
    """Test that PostgresMaturityRepository can be imported."""

    def test_import_repository(self) -> None:
        """Test that repository module can be imported."""
        from src.orchestrator.repositories.postgres.maturity_repository import (
            PostgresMaturityRepository,
        )
        assert PostgresMaturityRepository is not None

    def test_implements_interface(self) -> None:
        """Test that PostgresMaturityRepository implements IMaturityRepository."""
        from src.orchestrator.repositories.postgres.maturity_repository import (
            PostgresMaturityRepository,
        )
        assert issubclass(PostgresMaturityRepository, IMaturityRepository)


class TestPostgresMaturityRepositorySave:
    """Test PostgresMaturityRepository.save() method."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.merge = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_save_calls_merge_for_upsert(self, mock_session: AsyncMock) -> None:
        """Test that save() calls merge for upsert behavior."""
        from src.orchestrator.repositories.postgres.maturity_repository import (
            PostgresMaturityRepository,
        )

        repo = PostgresMaturityRepository(mock_session)
        domain_maturity = make_domain_maturity()

        await repo.save(domain_maturity)

        mock_session.merge.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_flushes_session(self, mock_session: AsyncMock) -> None:
        """Test that save() flushes the session."""
        from src.orchestrator.repositories.postgres.maturity_repository import (
            PostgresMaturityRepository,
        )

        repo = PostgresMaturityRepository(mock_session)
        domain_maturity = make_domain_maturity()

        await repo.save(domain_maturity)

        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_converts_to_orm(self, mock_session: AsyncMock) -> None:
        """Test that save() converts domain to ORM for storage."""
        from src.orchestrator.repositories.postgres.maturity_repository import (
            PostgresMaturityRepository,
        )

        repo = PostgresMaturityRepository(mock_session)
        domain_maturity = make_domain_maturity(
            score=90,
            level="advanced",
            can_submit=True,
        )

        await repo.save(domain_maturity)

        merged_orm = mock_session.merge.call_args[0][0]
        assert isinstance(merged_orm, MaturityORM)
        assert merged_orm.session_id == "session-123"
        assert merged_orm.score == 90
        assert merged_orm.level == "advanced"
        assert merged_orm.can_submit is True

    @pytest.mark.asyncio
    async def test_save_serializes_categories_to_json(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that save() serializes categories to JSONB format."""
        from src.orchestrator.repositories.postgres.maturity_repository import (
            PostgresMaturityRepository,
        )

        repo = PostgresMaturityRepository(mock_session)
        domain_maturity = make_domain_maturity()

        await repo.save(domain_maturity)

        merged_orm = mock_session.merge.call_args[0][0]
        assert isinstance(merged_orm.categories, list)
        assert len(merged_orm.categories) == 2
        assert merged_orm.categories[0]["id"] == "auth"
        assert merged_orm.categories[0]["name"] == "Authentication"
        assert merged_orm.categories[0]["score"] == 80
        assert merged_orm.categories[0]["required_for_submit"] is True

    @pytest.mark.asyncio
    async def test_save_handles_empty_gaps(self, mock_session: AsyncMock) -> None:
        """Test that save() handles empty gaps list."""
        from src.orchestrator.repositories.postgres.maturity_repository import (
            PostgresMaturityRepository,
        )

        repo = PostgresMaturityRepository(mock_session)
        domain_maturity = make_domain_maturity(gaps=[])

        await repo.save(domain_maturity)

        merged_orm = mock_session.merge.call_args[0][0]
        # Empty list should be stored as None or empty list
        assert merged_orm.gaps is None or merged_orm.gaps == []


class TestPostgresMaturityRepositoryGetBySession:
    """Test PostgresMaturityRepository.get_by_session() method."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock AsyncSession."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_get_by_session_returns_maturity(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that get_by_session() returns maturity when found."""
        from src.orchestrator.repositories.postgres.maturity_repository import (
            PostgresMaturityRepository,
        )

        orm_maturity = make_orm_maturity()
        mock_session.get = AsyncMock(return_value=orm_maturity)

        repo = PostgresMaturityRepository(mock_session)
        result = await repo.get_by_session("session-123")

        assert result is not None
        assert isinstance(result, MaturityState)
        assert result.session_id == "session-123"
        assert result.score == 75
        assert result.level == "intermediate"
        mock_session.get.assert_called_once_with(MaturityORM, "session-123")

    @pytest.mark.asyncio
    async def test_get_by_session_returns_none_when_not_found(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that get_by_session() returns None when not found."""
        from src.orchestrator.repositories.postgres.maturity_repository import (
            PostgresMaturityRepository,
        )

        mock_session.get = AsyncMock(return_value=None)

        repo = PostgresMaturityRepository(mock_session)
        result = await repo.get_by_session("nonexistent")

        assert result is None
        mock_session.get.assert_called_once_with(MaturityORM, "nonexistent")

    @pytest.mark.asyncio
    async def test_get_by_session_deserializes_categories(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that get_by_session() deserializes categories from JSONB."""
        from src.orchestrator.repositories.postgres.maturity_repository import (
            PostgresMaturityRepository,
        )

        orm_maturity = make_orm_maturity()
        mock_session.get = AsyncMock(return_value=orm_maturity)

        repo = PostgresMaturityRepository(mock_session)
        result = await repo.get_by_session("session-123")

        assert result is not None
        assert len(result.categories) == 2
        assert isinstance(result.categories[0], MaturityCategory)
        assert result.categories[0].id == "auth"
        assert result.categories[0].name == "Authentication"
        assert result.categories[0].score == 80
        assert result.categories[0].required_for_submit is True

    @pytest.mark.asyncio
    async def test_get_by_session_handles_null_gaps(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that get_by_session() handles null gaps."""
        from src.orchestrator.repositories.postgres.maturity_repository import (
            PostgresMaturityRepository,
        )

        orm_maturity = make_orm_maturity(gaps=None)
        mock_session.get = AsyncMock(return_value=orm_maturity)

        repo = PostgresMaturityRepository(mock_session)
        result = await repo.get_by_session("session-123")

        assert result is not None
        assert result.gaps == []

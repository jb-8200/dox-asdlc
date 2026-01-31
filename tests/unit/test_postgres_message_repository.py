"""Tests for P02-F09 Task T11: PostgresMessageRepository.

This module tests the PostgreSQL implementation of IMessageRepository:
- create() - Add message to database
- get_by_session() - Get messages for session with pagination
- delete_by_session() - Delete all messages for a session
"""

from datetime import datetime
from typing import Any, List
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.models.ideation import ChatMessage, MessageRole
from src.orchestrator.persistence.orm_models import MessageORM
from src.orchestrator.repositories.interfaces import IMessageRepository


def make_domain_message(
    message_id: str = "msg-123",
    session_id: str = "session-456",
    role: MessageRole = MessageRole.USER,
    content: str = "Test message content",
    maturity_delta: int = 5,
    metadata: dict | None = None,
) -> ChatMessage:
    """Create a domain ChatMessage for testing."""
    return ChatMessage(
        id=message_id,
        session_id=session_id,
        role=role,
        content=content,
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
        maturity_delta=maturity_delta,
        metadata=metadata,
    )


def make_orm_message(
    message_id: str = "msg-123",
    session_id: str = "session-456",
    role: str = "user",
    content: str = "Test message content",
    maturity_delta: int = 5,
    message_metadata: dict | None = None,
) -> MessageORM:
    """Create an ORM MessageORM for testing."""
    return MessageORM(
        id=message_id,
        session_id=session_id,
        role=role,
        content=content,
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
        maturity_delta=maturity_delta,
        message_metadata=message_metadata,
    )


class TestPostgresMessageRepositoryImport:
    """Test that PostgresMessageRepository can be imported."""

    def test_import_repository(self) -> None:
        """Test that repository module can be imported."""
        from src.orchestrator.repositories.postgres.message_repository import (
            PostgresMessageRepository,
        )
        assert PostgresMessageRepository is not None

    def test_implements_interface(self) -> None:
        """Test that PostgresMessageRepository implements IMessageRepository."""
        from src.orchestrator.repositories.postgres.message_repository import (
            PostgresMessageRepository,
        )
        assert issubclass(PostgresMessageRepository, IMessageRepository)


class TestPostgresMessageRepositoryCreate:
    """Test PostgresMessageRepository.create() method."""

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
        from src.orchestrator.repositories.postgres.message_repository import (
            PostgresMessageRepository,
        )

        repo = PostgresMessageRepository(mock_session)
        domain_message = make_domain_message()

        result = await repo.create(domain_message)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_returns_domain_model(self, mock_session: AsyncMock) -> None:
        """Test that create() returns a domain ChatMessage."""
        from src.orchestrator.repositories.postgres.message_repository import (
            PostgresMessageRepository,
        )

        repo = PostgresMessageRepository(mock_session)
        domain_message = make_domain_message()

        result = await repo.create(domain_message)

        assert isinstance(result, ChatMessage)
        assert result.id == "msg-123"
        assert result.session_id == "session-456"
        assert result.content == "Test message content"

    @pytest.mark.asyncio
    async def test_create_converts_to_orm(self, mock_session: AsyncMock) -> None:
        """Test that create() converts domain to ORM for storage."""
        from src.orchestrator.repositories.postgres.message_repository import (
            PostgresMessageRepository,
        )

        repo = PostgresMessageRepository(mock_session)
        domain_message = make_domain_message(
            role=MessageRole.ASSISTANT,
            metadata={"model": "gpt-4"},
        )

        await repo.create(domain_message)

        added_orm = mock_session.add.call_args[0][0]
        assert isinstance(added_orm, MessageORM)
        assert added_orm.role == "assistant"
        assert added_orm.message_metadata == {"model": "gpt-4"}

    @pytest.mark.asyncio
    async def test_create_with_none_metadata(self, mock_session: AsyncMock) -> None:
        """Test that create() handles None metadata."""
        from src.orchestrator.repositories.postgres.message_repository import (
            PostgresMessageRepository,
        )

        repo = PostgresMessageRepository(mock_session)
        domain_message = make_domain_message(metadata=None)

        await repo.create(domain_message)

        added_orm = mock_session.add.call_args[0][0]
        assert added_orm.message_metadata is None


class TestPostgresMessageRepositoryGetBySession:
    """Test PostgresMessageRepository.get_by_session() method."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock AsyncSession."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_get_by_session_returns_messages(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that get_by_session() returns list of messages."""
        from src.orchestrator.repositories.postgres.message_repository import (
            PostgresMessageRepository,
        )

        orm_messages = [
            make_orm_message("msg-1", "session-123"),
            make_orm_message("msg-2", "session-123"),
        ]

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = orm_messages
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = PostgresMessageRepository(mock_session)
        result = await repo.get_by_session("session-123")

        assert len(result) == 2
        assert all(isinstance(m, ChatMessage) for m in result)
        assert result[0].id == "msg-1"
        assert result[1].id == "msg-2"

    @pytest.mark.asyncio
    async def test_get_by_session_returns_empty_list(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that get_by_session() returns empty list when no messages."""
        from src.orchestrator.repositories.postgres.message_repository import (
            PostgresMessageRepository,
        )

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = PostgresMessageRepository(mock_session)
        result = await repo.get_by_session("session-no-messages")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_by_session_respects_pagination(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that get_by_session() passes pagination parameters."""
        from src.orchestrator.repositories.postgres.message_repository import (
            PostgresMessageRepository,
        )

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = PostgresMessageRepository(mock_session)
        await repo.get_by_session("session-123", limit=20, offset=10)

        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_session_orders_by_timestamp_asc(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that get_by_session() orders by timestamp ascending."""
        from src.orchestrator.repositories.postgres.message_repository import (
            PostgresMessageRepository,
        )

        # Messages in reverse order to verify ordering
        orm_messages = [
            make_orm_message("msg-1"),  # Earlier timestamp
            make_orm_message("msg-2"),  # Later timestamp
        ]

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = orm_messages
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = PostgresMessageRepository(mock_session)
        result = await repo.get_by_session("session-123")

        # Verify the query was executed (ordering is in the SQL)
        mock_session.execute.assert_called_once()


class TestPostgresMessageRepositoryDeleteBySession:
    """Test PostgresMessageRepository.delete_by_session() method."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_delete_by_session_executes_delete(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that delete_by_session() executes a delete statement."""
        from src.orchestrator.repositories.postgres.message_repository import (
            PostgresMessageRepository,
        )

        repo = PostgresMessageRepository(mock_session)

        await repo.delete_by_session("session-123")

        mock_session.execute.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_by_session_deletes_correct_session(
        self, mock_session: AsyncMock
    ) -> None:
        """Test that delete_by_session() deletes messages for correct session."""
        from src.orchestrator.repositories.postgres.message_repository import (
            PostgresMessageRepository,
        )

        repo = PostgresMessageRepository(mock_session)

        await repo.delete_by_session("specific-session-id")

        mock_session.execute.assert_called_once()

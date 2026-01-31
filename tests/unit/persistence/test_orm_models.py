"""Tests for P02-F09 Task T06: SQLAlchemy ORM Models.

This module tests:
- ORM model instantiation
- ORM model relationships
- ORM model column types and constraints
"""

from datetime import datetime, timezone
from typing import Any

import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase


# Import will be tested after implementation
def import_orm_models() -> Any:
    """Import ORM models module."""
    from src.orchestrator.persistence.orm_models import (
        Base,
        SessionORM,
        MessageORM,
        RequirementORM,
        MaturityORM,
        PRDDraftORM,
        UserStoryORM,
    )
    return {
        "Base": Base,
        "SessionORM": SessionORM,
        "MessageORM": MessageORM,
        "RequirementORM": RequirementORM,
        "MaturityORM": MaturityORM,
        "PRDDraftORM": PRDDraftORM,
        "UserStoryORM": UserStoryORM,
    }


class TestORMModelsImport:
    """Test that ORM models can be imported."""

    def test_orm_models_import(self) -> None:
        """Test that orm_models module can be imported."""
        models = import_orm_models()
        assert models["Base"] is not None
        assert models["SessionORM"] is not None
        assert models["MessageORM"] is not None
        assert models["RequirementORM"] is not None
        assert models["MaturityORM"] is not None
        assert models["PRDDraftORM"] is not None
        assert models["UserStoryORM"] is not None

    def test_base_is_declarative_base(self) -> None:
        """Test that Base is a SQLAlchemy DeclarativeBase."""
        models = import_orm_models()
        assert issubclass(models["Base"], DeclarativeBase)


class TestSessionORM:
    """Test SessionORM model."""

    @pytest.fixture
    def session_orm(self) -> Any:
        """Create a SessionORM instance for testing."""
        models = import_orm_models()
        return models["SessionORM"](
            id="session-123",
            project_name="Test Project",
            user_id="user-456",
            status="draft",
            data_source="mock",
            version=1,
        )

    def test_session_orm_instantiation(self, session_orm: Any) -> None:
        """Test SessionORM can be instantiated."""
        assert session_orm.id == "session-123"
        assert session_orm.project_name == "Test Project"
        assert session_orm.user_id == "user-456"
        assert session_orm.status == "draft"
        assert session_orm.data_source == "mock"
        assert session_orm.version == 1

    def test_session_orm_tablename(self) -> None:
        """Test SessionORM table name."""
        models = import_orm_models()
        assert models["SessionORM"].__tablename__ == "ideation_sessions"

    def test_session_orm_has_relationships(self) -> None:
        """Test SessionORM has expected relationships."""
        models = import_orm_models()
        mapper = inspect(models["SessionORM"])
        relationships = {r.key for r in mapper.relationships}

        assert "messages" in relationships
        assert "requirements" in relationships
        assert "maturity" in relationships
        assert "prd_drafts" in relationships
        assert "user_stories" in relationships

    def test_session_orm_column_types(self) -> None:
        """Test SessionORM column types."""
        models = import_orm_models()
        mapper = inspect(models["SessionORM"])
        columns = {c.key: c for c in mapper.columns}

        assert "id" in columns
        assert "project_name" in columns
        assert "user_id" in columns
        assert "status" in columns
        assert "data_source" in columns
        assert "version" in columns
        assert "created_at" in columns
        assert "updated_at" in columns


class TestMessageORM:
    """Test MessageORM model."""

    @pytest.fixture
    def message_orm(self) -> Any:
        """Create a MessageORM instance for testing."""
        models = import_orm_models()
        return models["MessageORM"](
            id="msg-123",
            session_id="session-123",
            role="user",
            content="Test message",
            maturity_delta=5,
            message_metadata={"model": "gpt-4"},
        )

    def test_message_orm_instantiation(self, message_orm: Any) -> None:
        """Test MessageORM can be instantiated."""
        assert message_orm.id == "msg-123"
        assert message_orm.session_id == "session-123"
        assert message_orm.role == "user"
        assert message_orm.content == "Test message"
        assert message_orm.maturity_delta == 5
        assert message_orm.message_metadata == {"model": "gpt-4"}

    def test_message_orm_tablename(self) -> None:
        """Test MessageORM table name."""
        models = import_orm_models()
        assert models["MessageORM"].__tablename__ == "ideation_messages"

    def test_message_orm_has_session_relationship(self) -> None:
        """Test MessageORM has session relationship."""
        models = import_orm_models()
        mapper = inspect(models["MessageORM"])
        relationships = {r.key for r in mapper.relationships}

        assert "session" in relationships


class TestRequirementORM:
    """Test RequirementORM model."""

    @pytest.fixture
    def requirement_orm(self) -> Any:
        """Create a RequirementORM instance for testing."""
        models = import_orm_models()
        return models["RequirementORM"](
            id="req-123",
            session_id="session-123",
            description="User must be able to login",
            type="functional",
            priority="must_have",
            category_id="auth",
        )

    def test_requirement_orm_instantiation(self, requirement_orm: Any) -> None:
        """Test RequirementORM can be instantiated."""
        assert requirement_orm.id == "req-123"
        assert requirement_orm.session_id == "session-123"
        assert requirement_orm.description == "User must be able to login"
        assert requirement_orm.type == "functional"
        assert requirement_orm.priority == "must_have"
        assert requirement_orm.category_id == "auth"

    def test_requirement_orm_tablename(self) -> None:
        """Test RequirementORM table name."""
        models = import_orm_models()
        assert models["RequirementORM"].__tablename__ == "ideation_requirements"


class TestMaturityORM:
    """Test MaturityORM model."""

    @pytest.fixture
    def maturity_orm(self) -> Any:
        """Create a MaturityORM instance for testing."""
        models = import_orm_models()
        return models["MaturityORM"](
            session_id="session-123",
            score=75,
            level="intermediate",
            categories={"auth": 80, "api": 70},
            can_submit=True,
            gaps=["Missing error handling"],
        )

    def test_maturity_orm_instantiation(self, maturity_orm: Any) -> None:
        """Test MaturityORM can be instantiated."""
        assert maturity_orm.session_id == "session-123"
        assert maturity_orm.score == 75
        assert maturity_orm.level == "intermediate"
        assert maturity_orm.categories == {"auth": 80, "api": 70}
        assert maturity_orm.can_submit is True
        assert maturity_orm.gaps == ["Missing error handling"]

    def test_maturity_orm_tablename(self) -> None:
        """Test MaturityORM table name."""
        models = import_orm_models()
        assert models["MaturityORM"].__tablename__ == "ideation_maturity"

    def test_maturity_orm_primary_key_is_session_id(self) -> None:
        """Test MaturityORM primary key is session_id."""
        models = import_orm_models()
        mapper = inspect(models["MaturityORM"])
        pk_columns = [c.key for c in mapper.primary_key]

        assert pk_columns == ["session_id"]


class TestPRDDraftORM:
    """Test PRDDraftORM model."""

    @pytest.fixture
    def prd_draft_orm(self) -> Any:
        """Create a PRDDraftORM instance for testing."""
        models = import_orm_models()
        return models["PRDDraftORM"](
            id="prd-123",
            session_id="session-123",
            title="Test PRD",
            version="0.1.0",
            sections={"overview": "This is a test", "goals": ["Goal 1"]},
            status="draft",
        )

    def test_prd_draft_orm_instantiation(self, prd_draft_orm: Any) -> None:
        """Test PRDDraftORM can be instantiated."""
        assert prd_draft_orm.id == "prd-123"
        assert prd_draft_orm.session_id == "session-123"
        assert prd_draft_orm.title == "Test PRD"
        assert prd_draft_orm.version == "0.1.0"
        assert prd_draft_orm.sections == {"overview": "This is a test", "goals": ["Goal 1"]}
        assert prd_draft_orm.status == "draft"

    def test_prd_draft_orm_tablename(self) -> None:
        """Test PRDDraftORM table name."""
        models = import_orm_models()
        assert models["PRDDraftORM"].__tablename__ == "ideation_prd_drafts"


class TestUserStoryORM:
    """Test UserStoryORM model."""

    @pytest.fixture
    def user_story_orm(self) -> Any:
        """Create a UserStoryORM instance for testing."""
        models = import_orm_models()
        return models["UserStoryORM"](
            id="story-123",
            session_id="session-123",
            title="User Login",
            as_a="registered user",
            i_want="to login to my account",
            so_that="I can access my data",
            acceptance_criteria=["Given valid credentials", "When I submit login"],
            linked_requirements=["req-123"],
            priority="must_have",
        )

    def test_user_story_orm_instantiation(self, user_story_orm: Any) -> None:
        """Test UserStoryORM can be instantiated."""
        assert user_story_orm.id == "story-123"
        assert user_story_orm.session_id == "session-123"
        assert user_story_orm.title == "User Login"
        assert user_story_orm.as_a == "registered user"
        assert user_story_orm.i_want == "to login to my account"
        assert user_story_orm.so_that == "I can access my data"
        assert user_story_orm.acceptance_criteria == ["Given valid credentials", "When I submit login"]
        assert user_story_orm.linked_requirements == ["req-123"]
        assert user_story_orm.priority == "must_have"

    def test_user_story_orm_tablename(self) -> None:
        """Test UserStoryORM table name."""
        models = import_orm_models()
        assert models["UserStoryORM"].__tablename__ == "ideation_user_stories"


class TestORMRelationships:
    """Test ORM model relationships."""

    def test_session_messages_cascade(self) -> None:
        """Test SessionORM.messages has cascade delete."""
        models = import_orm_models()
        mapper = inspect(models["SessionORM"])
        messages_rel = None
        for r in mapper.relationships:
            if r.key == "messages":
                messages_rel = r
                break

        assert messages_rel is not None
        assert "delete-orphan" in str(messages_rel.cascade)

    def test_session_requirements_cascade(self) -> None:
        """Test SessionORM.requirements has cascade delete."""
        models = import_orm_models()
        mapper = inspect(models["SessionORM"])
        req_rel = None
        for r in mapper.relationships:
            if r.key == "requirements":
                req_rel = r
                break

        assert req_rel is not None
        assert "delete-orphan" in str(req_rel.cascade)

    def test_session_maturity_one_to_one(self) -> None:
        """Test SessionORM.maturity is one-to-one (uselist=False)."""
        models = import_orm_models()
        mapper = inspect(models["SessionORM"])
        maturity_rel = None
        for r in mapper.relationships:
            if r.key == "maturity":
                maturity_rel = r
                break

        assert maturity_rel is not None
        assert maturity_rel.uselist is False


class TestORMForeignKeys:
    """Test ORM model foreign keys."""

    def test_message_session_foreign_key(self) -> None:
        """Test MessageORM has foreign key to sessions."""
        models = import_orm_models()
        mapper = inspect(models["MessageORM"])
        columns = {c.key: c for c in mapper.columns}

        session_id_col = columns["session_id"]
        fks = list(session_id_col.foreign_keys)

        assert len(fks) == 1
        assert "ideation_sessions.id" in str(fks[0])

    def test_requirement_session_foreign_key(self) -> None:
        """Test RequirementORM has foreign key to sessions."""
        models = import_orm_models()
        mapper = inspect(models["RequirementORM"])
        columns = {c.key: c for c in mapper.columns}

        session_id_col = columns["session_id"]
        fks = list(session_id_col.foreign_keys)

        assert len(fks) == 1
        assert "ideation_sessions.id" in str(fks[0])

    def test_maturity_session_foreign_key(self) -> None:
        """Test MaturityORM has foreign key to sessions."""
        models = import_orm_models()
        mapper = inspect(models["MaturityORM"])
        columns = {c.key: c for c in mapper.columns}

        session_id_col = columns["session_id"]
        fks = list(session_id_col.foreign_keys)

        assert len(fks) == 1
        assert "ideation_sessions.id" in str(fks[0])

    def test_prd_draft_session_foreign_key(self) -> None:
        """Test PRDDraftORM has foreign key to sessions."""
        models = import_orm_models()
        mapper = inspect(models["PRDDraftORM"])
        columns = {c.key: c for c in mapper.columns}

        session_id_col = columns["session_id"]
        fks = list(session_id_col.foreign_keys)

        assert len(fks) == 1
        assert "ideation_sessions.id" in str(fks[0])

    def test_user_story_session_foreign_key(self) -> None:
        """Test UserStoryORM has foreign key to sessions."""
        models = import_orm_models()
        mapper = inspect(models["UserStoryORM"])
        columns = {c.key: c for c in mapper.columns}

        session_id_col = columns["session_id"]
        fks = list(session_id_col.foreign_keys)

        assert len(fks) == 1
        assert "ideation_sessions.id" in str(fks[0])

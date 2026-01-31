"""Tests for P02-F09 Task T07: Domain-ORM Mappers.

This module tests:
- Mapper classes convert domain models to ORM models
- Mapper classes convert ORM models to domain models
- JSON serialization for JSONB fields
"""

from datetime import datetime, timezone
from typing import Any

import pytest


def import_domain_models() -> Any:
    """Import domain models module."""
    from src.core.models.ideation import (
        IdeationSession,
        ChatMessage,
        ExtractedRequirement,
        MaturityState,
        MaturityCategory,
        PRDDraft,
        PRDSection,
        UserStory,
        ProjectStatus,
        DataSource,
        MessageRole,
        RequirementType,
        RequirementPriority,
    )
    return {
        "IdeationSession": IdeationSession,
        "ChatMessage": ChatMessage,
        "ExtractedRequirement": ExtractedRequirement,
        "MaturityState": MaturityState,
        "MaturityCategory": MaturityCategory,
        "PRDDraft": PRDDraft,
        "PRDSection": PRDSection,
        "UserStory": UserStory,
        "ProjectStatus": ProjectStatus,
        "DataSource": DataSource,
        "MessageRole": MessageRole,
        "RequirementType": RequirementType,
        "RequirementPriority": RequirementPriority,
    }


def import_orm_models() -> Any:
    """Import ORM models module."""
    from src.orchestrator.persistence.orm_models import (
        SessionORM,
        MessageORM,
        RequirementORM,
        MaturityORM,
        PRDDraftORM,
        UserStoryORM,
    )
    return {
        "SessionORM": SessionORM,
        "MessageORM": MessageORM,
        "RequirementORM": RequirementORM,
        "MaturityORM": MaturityORM,
        "PRDDraftORM": PRDDraftORM,
        "UserStoryORM": UserStoryORM,
    }


def import_mappers() -> Any:
    """Import mapper classes."""
    from src.orchestrator.persistence.mappers import (
        SessionMapper,
        MessageMapper,
        RequirementMapper,
        MaturityMapper,
        PRDMapper,
        UserStoryMapper,
    )
    return {
        "SessionMapper": SessionMapper,
        "MessageMapper": MessageMapper,
        "RequirementMapper": RequirementMapper,
        "MaturityMapper": MaturityMapper,
        "PRDMapper": PRDMapper,
        "UserStoryMapper": UserStoryMapper,
    }


class TestMappersImport:
    """Test that mapper classes can be imported."""

    def test_mappers_import(self) -> None:
        """Test that mappers module can be imported."""
        mappers = import_mappers()
        assert mappers["SessionMapper"] is not None
        assert mappers["MessageMapper"] is not None
        assert mappers["RequirementMapper"] is not None
        assert mappers["MaturityMapper"] is not None
        assert mappers["PRDMapper"] is not None
        assert mappers["UserStoryMapper"] is not None


class TestSessionMapper:
    """Test SessionMapper domain <-> ORM conversion."""

    @pytest.fixture
    def domain_session(self) -> Any:
        """Create a domain IdeationSession for testing."""
        models = import_domain_models()
        return models["IdeationSession"](
            id="session-123",
            project_name="Test Project",
            user_id="user-456",
            status=models["ProjectStatus"].DRAFT,
            data_source=models["DataSource"].MOCK,
            version=1,
            created_at=datetime(2024, 1, 15, 10, 30, 0),
            updated_at=datetime(2024, 1, 15, 11, 0, 0),
        )

    @pytest.fixture
    def orm_session(self) -> Any:
        """Create an ORM SessionORM for testing."""
        models = import_orm_models()
        return models["SessionORM"](
            id="session-123",
            project_name="Test Project",
            user_id="user-456",
            status="draft",
            data_source="mock",
            version=1,
            created_at=datetime(2024, 1, 15, 10, 30, 0),
            updated_at=datetime(2024, 1, 15, 11, 0, 0),
        )

    def test_session_to_orm(self, domain_session: Any) -> None:
        """Test SessionMapper.to_orm converts domain to ORM."""
        mappers = import_mappers()
        orm_models = import_orm_models()

        orm = mappers["SessionMapper"].to_orm(domain_session)

        assert isinstance(orm, orm_models["SessionORM"])
        assert orm.id == "session-123"
        assert orm.project_name == "Test Project"
        assert orm.user_id == "user-456"
        assert orm.status == "draft"
        assert orm.data_source == "mock"
        assert orm.version == 1

    def test_session_from_orm(self, orm_session: Any) -> None:
        """Test SessionMapper.from_orm converts ORM to domain."""
        mappers = import_mappers()
        domain_models = import_domain_models()

        domain = mappers["SessionMapper"].from_orm(orm_session)

        assert isinstance(domain, domain_models["IdeationSession"])
        assert domain.id == "session-123"
        assert domain.project_name == "Test Project"
        assert domain.user_id == "user-456"
        assert domain.status == domain_models["ProjectStatus"].DRAFT
        assert domain.data_source == domain_models["DataSource"].MOCK
        assert domain.version == 1

    def test_session_roundtrip(self, domain_session: Any) -> None:
        """Test domain -> ORM -> domain roundtrip preserves data."""
        mappers = import_mappers()

        orm = mappers["SessionMapper"].to_orm(domain_session)
        back = mappers["SessionMapper"].from_orm(orm)

        assert back.id == domain_session.id
        assert back.project_name == domain_session.project_name
        assert back.user_id == domain_session.user_id
        assert back.status == domain_session.status
        assert back.data_source == domain_session.data_source
        assert back.version == domain_session.version


class TestMessageMapper:
    """Test MessageMapper domain <-> ORM conversion."""

    @pytest.fixture
    def domain_message(self) -> Any:
        """Create a domain ChatMessage for testing."""
        models = import_domain_models()
        return models["ChatMessage"](
            id="msg-123",
            session_id="session-123",
            role=models["MessageRole"].USER,
            content="Test message content",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            maturity_delta=5,
            metadata={"model": "gpt-4", "tokens": 100},
        )

    @pytest.fixture
    def orm_message(self) -> Any:
        """Create an ORM MessageORM for testing."""
        models = import_orm_models()
        return models["MessageORM"](
            id="msg-123",
            session_id="session-123",
            role="user",
            content="Test message content",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            maturity_delta=5,
            message_metadata={"model": "gpt-4", "tokens": 100},
        )

    def test_message_to_orm(self, domain_message: Any) -> None:
        """Test MessageMapper.to_orm converts domain to ORM."""
        mappers = import_mappers()
        orm_models = import_orm_models()

        orm = mappers["MessageMapper"].to_orm(domain_message)

        assert isinstance(orm, orm_models["MessageORM"])
        assert orm.id == "msg-123"
        assert orm.session_id == "session-123"
        assert orm.role == "user"
        assert orm.content == "Test message content"
        assert orm.maturity_delta == 5
        assert orm.message_metadata == {"model": "gpt-4", "tokens": 100}

    def test_message_from_orm(self, orm_message: Any) -> None:
        """Test MessageMapper.from_orm converts ORM to domain."""
        mappers = import_mappers()
        domain_models = import_domain_models()

        domain = mappers["MessageMapper"].from_orm(orm_message)

        assert isinstance(domain, domain_models["ChatMessage"])
        assert domain.id == "msg-123"
        assert domain.session_id == "session-123"
        assert domain.role == domain_models["MessageRole"].USER
        assert domain.content == "Test message content"
        assert domain.maturity_delta == 5
        assert domain.metadata == {"model": "gpt-4", "tokens": 100}

    def test_message_with_none_metadata(self) -> None:
        """Test MessageMapper handles None metadata."""
        mappers = import_mappers()
        domain_models = import_domain_models()

        domain = domain_models["ChatMessage"](
            id="msg-456",
            session_id="session-123",
            role=domain_models["MessageRole"].ASSISTANT,
            content="Response",
            metadata=None,
        )

        orm = mappers["MessageMapper"].to_orm(domain)
        assert orm.message_metadata is None

        back = mappers["MessageMapper"].from_orm(orm)
        assert back.metadata is None


class TestRequirementMapper:
    """Test RequirementMapper domain <-> ORM conversion."""

    @pytest.fixture
    def domain_requirement(self) -> Any:
        """Create a domain ExtractedRequirement for testing."""
        models = import_domain_models()
        return models["ExtractedRequirement"](
            id="req-123",
            session_id="session-123",
            description="User must be able to login",
            type=models["RequirementType"].FUNCTIONAL,
            priority=models["RequirementPriority"].MUST_HAVE,
            category_id="auth",
            created_at=datetime(2024, 1, 15, 10, 30, 0),
        )

    @pytest.fixture
    def orm_requirement(self) -> Any:
        """Create an ORM RequirementORM for testing."""
        models = import_orm_models()
        return models["RequirementORM"](
            id="req-123",
            session_id="session-123",
            description="User must be able to login",
            type="functional",
            priority="must_have",
            category_id="auth",
            created_at=datetime(2024, 1, 15, 10, 30, 0),
        )

    def test_requirement_to_orm(self, domain_requirement: Any) -> None:
        """Test RequirementMapper.to_orm converts domain to ORM."""
        mappers = import_mappers()
        orm_models = import_orm_models()

        orm = mappers["RequirementMapper"].to_orm(domain_requirement)

        assert isinstance(orm, orm_models["RequirementORM"])
        assert orm.id == "req-123"
        assert orm.description == "User must be able to login"
        assert orm.type == "functional"
        assert orm.priority == "must_have"
        assert orm.category_id == "auth"

    def test_requirement_from_orm(self, orm_requirement: Any) -> None:
        """Test RequirementMapper.from_orm converts ORM to domain."""
        mappers = import_mappers()
        domain_models = import_domain_models()

        domain = mappers["RequirementMapper"].from_orm(orm_requirement)

        assert isinstance(domain, domain_models["ExtractedRequirement"])
        assert domain.id == "req-123"
        assert domain.description == "User must be able to login"
        assert domain.type == domain_models["RequirementType"].FUNCTIONAL
        assert domain.priority == domain_models["RequirementPriority"].MUST_HAVE
        assert domain.category_id == "auth"

    def test_requirement_with_none_category(self) -> None:
        """Test RequirementMapper handles None category_id."""
        mappers = import_mappers()
        domain_models = import_domain_models()

        domain = domain_models["ExtractedRequirement"](
            id="req-456",
            session_id="session-123",
            description="Another requirement",
            type=domain_models["RequirementType"].NON_FUNCTIONAL,
            priority=domain_models["RequirementPriority"].COULD_HAVE,
            category_id=None,
        )

        orm = mappers["RequirementMapper"].to_orm(domain)
        assert orm.category_id is None

        back = mappers["RequirementMapper"].from_orm(orm)
        assert back.category_id is None


class TestMaturityMapper:
    """Test MaturityMapper domain <-> ORM conversion."""

    @pytest.fixture
    def domain_maturity(self) -> Any:
        """Create a domain MaturityState for testing."""
        models = import_domain_models()
        return models["MaturityState"](
            session_id="session-123",
            score=75,
            level="intermediate",
            categories=[
                models["MaturityCategory"](
                    id="auth",
                    name="Authentication",
                    score=80,
                    required_for_submit=True,
                ),
                models["MaturityCategory"](
                    id="api",
                    name="API Design",
                    score=70,
                    required_for_submit=False,
                ),
            ],
            can_submit=True,
            gaps=["Missing error handling", "No rate limiting"],
            updated_at=datetime(2024, 1, 15, 10, 30, 0),
        )

    @pytest.fixture
    def orm_maturity(self) -> Any:
        """Create an ORM MaturityORM for testing."""
        models = import_orm_models()
        return models["MaturityORM"](
            session_id="session-123",
            score=75,
            level="intermediate",
            categories=[
                {"id": "auth", "name": "Authentication", "score": 80, "required_for_submit": True},
                {"id": "api", "name": "API Design", "score": 70, "required_for_submit": False},
            ],
            can_submit=True,
            gaps=["Missing error handling", "No rate limiting"],
            updated_at=datetime(2024, 1, 15, 10, 30, 0),
        )

    def test_maturity_to_orm(self, domain_maturity: Any) -> None:
        """Test MaturityMapper.to_orm converts domain to ORM."""
        mappers = import_mappers()
        orm_models = import_orm_models()

        orm = mappers["MaturityMapper"].to_orm(domain_maturity)

        assert isinstance(orm, orm_models["MaturityORM"])
        assert orm.session_id == "session-123"
        assert orm.score == 75
        assert orm.level == "intermediate"
        assert orm.can_submit is True
        assert len(orm.categories) == 2
        assert orm.categories[0]["id"] == "auth"
        assert orm.gaps == ["Missing error handling", "No rate limiting"]

    def test_maturity_from_orm(self, orm_maturity: Any) -> None:
        """Test MaturityMapper.from_orm converts ORM to domain."""
        mappers = import_mappers()
        domain_models = import_domain_models()

        domain = mappers["MaturityMapper"].from_orm(orm_maturity)

        assert isinstance(domain, domain_models["MaturityState"])
        assert domain.session_id == "session-123"
        assert domain.score == 75
        assert domain.level == "intermediate"
        assert domain.can_submit is True
        assert len(domain.categories) == 2
        assert isinstance(domain.categories[0], domain_models["MaturityCategory"])
        assert domain.categories[0].id == "auth"
        assert domain.categories[0].name == "Authentication"
        assert domain.gaps == ["Missing error handling", "No rate limiting"]

    def test_maturity_categories_serialization(self, domain_maturity: Any) -> None:
        """Test MaturityMapper properly serializes categories to JSON."""
        mappers = import_mappers()

        orm = mappers["MaturityMapper"].to_orm(domain_maturity)

        # Categories should be a list of dicts for JSONB storage
        assert isinstance(orm.categories, list)
        for cat in orm.categories:
            assert isinstance(cat, dict)
            assert "id" in cat
            assert "name" in cat
            assert "score" in cat
            assert "required_for_submit" in cat


class TestPRDMapper:
    """Test PRDMapper domain <-> ORM conversion."""

    @pytest.fixture
    def domain_prd(self) -> Any:
        """Create a domain PRDDraft for testing."""
        models = import_domain_models()
        return models["PRDDraft"](
            id="prd-123",
            session_id="session-123",
            title="Test PRD Document",
            version="0.1.0",
            sections=[
                models["PRDSection"](
                    id="sec-1",
                    heading="Overview",
                    content="This is the overview section.",
                    order=1,
                ),
                models["PRDSection"](
                    id="sec-2",
                    heading="Goals",
                    content="These are the goals.",
                    order=2,
                ),
            ],
            status="draft",
            created_at=datetime(2024, 1, 15, 10, 30, 0),
        )

    @pytest.fixture
    def orm_prd(self) -> Any:
        """Create an ORM PRDDraftORM for testing."""
        models = import_orm_models()
        return models["PRDDraftORM"](
            id="prd-123",
            session_id="session-123",
            title="Test PRD Document",
            version="0.1.0",
            sections=[
                {"id": "sec-1", "heading": "Overview", "content": "This is the overview section.", "order": 1},
                {"id": "sec-2", "heading": "Goals", "content": "These are the goals.", "order": 2},
            ],
            status="draft",
            created_at=datetime(2024, 1, 15, 10, 30, 0),
        )

    def test_prd_to_orm(self, domain_prd: Any) -> None:
        """Test PRDMapper.to_orm converts domain to ORM."""
        mappers = import_mappers()
        orm_models = import_orm_models()

        orm = mappers["PRDMapper"].to_orm(domain_prd)

        assert isinstance(orm, orm_models["PRDDraftORM"])
        assert orm.id == "prd-123"
        assert orm.session_id == "session-123"
        assert orm.title == "Test PRD Document"
        assert orm.version == "0.1.0"
        assert orm.status == "draft"
        assert len(orm.sections) == 2
        assert orm.sections[0]["heading"] == "Overview"

    def test_prd_from_orm(self, orm_prd: Any) -> None:
        """Test PRDMapper.from_orm converts ORM to domain."""
        mappers = import_mappers()
        domain_models = import_domain_models()

        domain = mappers["PRDMapper"].from_orm(orm_prd)

        assert isinstance(domain, domain_models["PRDDraft"])
        assert domain.id == "prd-123"
        assert domain.session_id == "session-123"
        assert domain.title == "Test PRD Document"
        assert domain.version == "0.1.0"
        assert domain.status == "draft"
        assert len(domain.sections) == 2
        assert isinstance(domain.sections[0], domain_models["PRDSection"])
        assert domain.sections[0].heading == "Overview"

    def test_prd_sections_serialization(self, domain_prd: Any) -> None:
        """Test PRDMapper properly serializes sections to JSON."""
        mappers = import_mappers()

        orm = mappers["PRDMapper"].to_orm(domain_prd)

        # Sections should be a list of dicts for JSONB storage
        assert isinstance(orm.sections, list)
        for sec in orm.sections:
            assert isinstance(sec, dict)
            assert "id" in sec
            assert "heading" in sec
            assert "content" in sec
            assert "order" in sec


class TestUserStoryMapper:
    """Test UserStoryMapper domain <-> ORM conversion."""

    @pytest.fixture
    def domain_user_story(self) -> Any:
        """Create a domain UserStory for testing."""
        models = import_domain_models()
        return models["UserStory"](
            id="story-123",
            session_id="session-123",
            title="User Login",
            as_a="registered user",
            i_want="to login to my account",
            so_that="I can access my personal data",
            acceptance_criteria=[
                "Given valid credentials, login succeeds",
                "Given invalid credentials, error shown",
            ],
            linked_requirements=["req-123", "req-456"],
            priority=models["RequirementPriority"].MUST_HAVE,
            created_at=datetime(2024, 1, 15, 10, 30, 0),
        )

    @pytest.fixture
    def orm_user_story(self) -> Any:
        """Create an ORM UserStoryORM for testing."""
        models = import_orm_models()
        return models["UserStoryORM"](
            id="story-123",
            session_id="session-123",
            title="User Login",
            as_a="registered user",
            i_want="to login to my account",
            so_that="I can access my personal data",
            acceptance_criteria=[
                "Given valid credentials, login succeeds",
                "Given invalid credentials, error shown",
            ],
            linked_requirements=["req-123", "req-456"],
            priority="must_have",
            created_at=datetime(2024, 1, 15, 10, 30, 0),
        )

    def test_user_story_to_orm(self, domain_user_story: Any) -> None:
        """Test UserStoryMapper.to_orm converts domain to ORM."""
        mappers = import_mappers()
        orm_models = import_orm_models()

        orm = mappers["UserStoryMapper"].to_orm(domain_user_story)

        assert isinstance(orm, orm_models["UserStoryORM"])
        assert orm.id == "story-123"
        assert orm.session_id == "session-123"
        assert orm.title == "User Login"
        assert orm.as_a == "registered user"
        assert orm.i_want == "to login to my account"
        assert orm.so_that == "I can access my personal data"
        assert orm.priority == "must_have"
        assert orm.acceptance_criteria == [
            "Given valid credentials, login succeeds",
            "Given invalid credentials, error shown",
        ]
        assert orm.linked_requirements == ["req-123", "req-456"]

    def test_user_story_from_orm(self, orm_user_story: Any) -> None:
        """Test UserStoryMapper.from_orm converts ORM to domain."""
        mappers = import_mappers()
        domain_models = import_domain_models()

        domain = mappers["UserStoryMapper"].from_orm(orm_user_story)

        assert isinstance(domain, domain_models["UserStory"])
        assert domain.id == "story-123"
        assert domain.session_id == "session-123"
        assert domain.title == "User Login"
        assert domain.as_a == "registered user"
        assert domain.i_want == "to login to my account"
        assert domain.so_that == "I can access my personal data"
        assert domain.priority == domain_models["RequirementPriority"].MUST_HAVE
        assert domain.acceptance_criteria == [
            "Given valid credentials, login succeeds",
            "Given invalid credentials, error shown",
        ]
        assert domain.linked_requirements == ["req-123", "req-456"]

    def test_user_story_with_empty_linked_requirements(self) -> None:
        """Test UserStoryMapper handles empty linked_requirements."""
        mappers = import_mappers()
        domain_models = import_domain_models()

        domain = domain_models["UserStory"](
            id="story-456",
            session_id="session-123",
            title="Another Story",
            as_a="admin",
            i_want="to manage users",
            so_that="I can control access",
            acceptance_criteria=["Criteria 1"],
            linked_requirements=[],
            priority=domain_models["RequirementPriority"].SHOULD_HAVE,
        )

        orm = mappers["UserStoryMapper"].to_orm(domain)
        assert orm.linked_requirements == []

        back = mappers["UserStoryMapper"].from_orm(orm)
        assert back.linked_requirements == []

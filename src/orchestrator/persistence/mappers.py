"""Mappers for converting between domain models and ORM models.

This module provides static methods to convert between the pure Python domain
models in src/core/models/ideation.py and the SQLAlchemy ORM models used for
database persistence.
"""


from src.core.models.ideation import (
    ChatMessage,
    DataSource,
    ExtractedRequirement,
    IdeationSession,
    MaturityCategory,
    MaturityState,
    MessageRole,
    PRDDraft,
    PRDSection,
    ProjectStatus,
    RequirementPriority,
    RequirementType,
    UserStory,
)
from src.orchestrator.persistence.orm_models import (
    MaturityORM,
    MessageORM,
    PRDDraftORM,
    RequirementORM,
    SessionORM,
    UserStoryORM,
)


class SessionMapper:
    """Mapper for IdeationSession <-> SessionORM conversion."""

    @staticmethod
    def to_orm(domain: IdeationSession) -> SessionORM:
        """Convert domain IdeationSession to ORM SessionORM.

        Args:
            domain: The domain model to convert.

        Returns:
            The corresponding ORM model.
        """
        return SessionORM(
            id=domain.id,
            project_name=domain.project_name,
            user_id=domain.user_id,
            status=domain.status.value if isinstance(domain.status, ProjectStatus) else domain.status,
            data_source=domain.data_source.value if isinstance(domain.data_source, DataSource) else domain.data_source,
            version=domain.version,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
        )

    @staticmethod
    def from_orm(orm: SessionORM) -> IdeationSession:
        """Convert ORM SessionORM to domain IdeationSession.

        Args:
            orm: The ORM model to convert.

        Returns:
            The corresponding domain model.
        """
        return IdeationSession(
            id=orm.id,
            project_name=orm.project_name,
            user_id=orm.user_id,
            status=ProjectStatus(orm.status),
            data_source=DataSource(orm.data_source),
            version=orm.version,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )


class MessageMapper:
    """Mapper for ChatMessage <-> MessageORM conversion."""

    @staticmethod
    def to_orm(domain: ChatMessage) -> MessageORM:
        """Convert domain ChatMessage to ORM MessageORM.

        Args:
            domain: The domain model to convert.

        Returns:
            The corresponding ORM model.
        """
        return MessageORM(
            id=domain.id,
            session_id=domain.session_id,
            role=domain.role.value if isinstance(domain.role, MessageRole) else domain.role,
            content=domain.content,
            timestamp=domain.timestamp,
            maturity_delta=domain.maturity_delta,
            message_metadata=domain.metadata,
        )

    @staticmethod
    def from_orm(orm: MessageORM) -> ChatMessage:
        """Convert ORM MessageORM to domain ChatMessage.

        Args:
            orm: The ORM model to convert.

        Returns:
            The corresponding domain model.
        """
        return ChatMessage(
            id=orm.id,
            session_id=orm.session_id,
            role=MessageRole(orm.role),
            content=orm.content,
            timestamp=orm.timestamp,
            maturity_delta=orm.maturity_delta,
            metadata=orm.message_metadata,
        )


class RequirementMapper:
    """Mapper for ExtractedRequirement <-> RequirementORM conversion."""

    @staticmethod
    def to_orm(domain: ExtractedRequirement) -> RequirementORM:
        """Convert domain ExtractedRequirement to ORM RequirementORM.

        Args:
            domain: The domain model to convert.

        Returns:
            The corresponding ORM model.
        """
        return RequirementORM(
            id=domain.id,
            session_id=domain.session_id,
            description=domain.description,
            type=domain.type.value if isinstance(domain.type, RequirementType) else domain.type,
            priority=domain.priority.value if isinstance(domain.priority, RequirementPriority) else domain.priority,
            category_id=domain.category_id,
            created_at=domain.created_at,
        )

    @staticmethod
    def from_orm(orm: RequirementORM) -> ExtractedRequirement:
        """Convert ORM RequirementORM to domain ExtractedRequirement.

        Args:
            orm: The ORM model to convert.

        Returns:
            The corresponding domain model.
        """
        return ExtractedRequirement(
            id=orm.id,
            session_id=orm.session_id,
            description=orm.description,
            type=RequirementType(orm.type),
            priority=RequirementPriority(orm.priority),
            category_id=orm.category_id,
            created_at=orm.created_at,
        )


class MaturityMapper:
    """Mapper for MaturityState <-> MaturityORM conversion."""

    @staticmethod
    def to_orm(domain: MaturityState) -> MaturityORM:
        """Convert domain MaturityState to ORM MaturityORM.

        Serializes MaturityCategory objects to dictionaries for JSONB storage.

        Args:
            domain: The domain model to convert.

        Returns:
            The corresponding ORM model.
        """
        # Serialize categories to list of dicts for JSONB
        categories_json = [
            {
                "id": cat.id,
                "name": cat.name,
                "score": cat.score,
                "required_for_submit": cat.required_for_submit,
            }
            for cat in domain.categories
        ]

        return MaturityORM(
            session_id=domain.session_id,
            score=domain.score,
            level=domain.level,
            categories=categories_json,
            can_submit=domain.can_submit,
            gaps=domain.gaps if domain.gaps else None,
            updated_at=domain.updated_at,
        )

    @staticmethod
    def from_orm(orm: MaturityORM) -> MaturityState:
        """Convert ORM MaturityORM to domain MaturityState.

        Deserializes JSONB categories to MaturityCategory objects.

        Args:
            orm: The ORM model to convert.

        Returns:
            The corresponding domain model.
        """
        # Deserialize categories from list of dicts
        categories = [
            MaturityCategory(
                id=cat["id"],
                name=cat["name"],
                score=cat["score"],
                required_for_submit=cat["required_for_submit"],
            )
            for cat in orm.categories
        ]

        return MaturityState(
            session_id=orm.session_id,
            score=orm.score,
            level=orm.level,
            categories=categories,
            can_submit=orm.can_submit,
            gaps=orm.gaps if orm.gaps else [],
            updated_at=orm.updated_at,
        )


class PRDMapper:
    """Mapper for PRDDraft <-> PRDDraftORM conversion."""

    @staticmethod
    def to_orm(domain: PRDDraft) -> PRDDraftORM:
        """Convert domain PRDDraft to ORM PRDDraftORM.

        Serializes PRDSection objects to dictionaries for JSONB storage.

        Args:
            domain: The domain model to convert.

        Returns:
            The corresponding ORM model.
        """
        # Serialize sections to list of dicts for JSONB
        sections_json = [
            {
                "id": sec.id,
                "heading": sec.heading,
                "content": sec.content,
                "order": sec.order,
            }
            for sec in domain.sections
        ]

        return PRDDraftORM(
            id=domain.id,
            session_id=domain.session_id,
            title=domain.title,
            version=domain.version,
            sections=sections_json,
            status=domain.status,
            created_at=domain.created_at,
        )

    @staticmethod
    def from_orm(orm: PRDDraftORM) -> PRDDraft:
        """Convert ORM PRDDraftORM to domain PRDDraft.

        Deserializes JSONB sections to PRDSection objects.

        Args:
            orm: The ORM model to convert.

        Returns:
            The corresponding domain model.
        """
        # Deserialize sections from list of dicts
        sections = [
            PRDSection(
                id=sec["id"],
                heading=sec["heading"],
                content=sec["content"],
                order=sec["order"],
            )
            for sec in orm.sections
        ]

        return PRDDraft(
            id=orm.id,
            session_id=orm.session_id,
            title=orm.title,
            version=orm.version,
            sections=sections,
            status=orm.status,
            created_at=orm.created_at,
        )


class UserStoryMapper:
    """Mapper for UserStory <-> UserStoryORM conversion."""

    @staticmethod
    def to_orm(domain: UserStory) -> UserStoryORM:
        """Convert domain UserStory to ORM UserStoryORM.

        Args:
            domain: The domain model to convert.

        Returns:
            The corresponding ORM model.
        """
        return UserStoryORM(
            id=domain.id,
            session_id=domain.session_id,
            title=domain.title,
            as_a=domain.as_a,
            i_want=domain.i_want,
            so_that=domain.so_that,
            acceptance_criteria=domain.acceptance_criteria,
            linked_requirements=domain.linked_requirements if domain.linked_requirements else [],
            priority=domain.priority.value if isinstance(domain.priority, RequirementPriority) else domain.priority,
            created_at=domain.created_at,
        )

    @staticmethod
    def from_orm(orm: UserStoryORM) -> UserStory:
        """Convert ORM UserStoryORM to domain UserStory.

        Args:
            orm: The ORM model to convert.

        Returns:
            The corresponding domain model.
        """
        return UserStory(
            id=orm.id,
            session_id=orm.session_id,
            title=orm.title,
            as_a=orm.as_a,
            i_want=orm.i_want,
            so_that=orm.so_that,
            acceptance_criteria=orm.acceptance_criteria,
            linked_requirements=orm.linked_requirements if orm.linked_requirements else [],
            priority=RequirementPriority(orm.priority),
            created_at=orm.created_at,
        )

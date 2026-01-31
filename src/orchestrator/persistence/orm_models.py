"""SQLAlchemy ORM models for ideation persistence.

This module defines the ORM models that map to the PostgreSQL database tables.
These models use SQLAlchemy 2.0+ style with Mapped type hints.
"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class SessionORM(Base):
    """ORM model for ideation sessions.

    Maps to the ideation_sessions table in PostgreSQL.

    Attributes:
        id: Unique session identifier.
        project_name: Name of the project being ideated.
        user_id: ID of the user who owns this session.
        status: Current status (draft, approved, in_build, closed).
        data_source: Data source type (mock, configured).
        version: Version number for optimistic locking.
        created_at: Timestamp when session was created.
        updated_at: Timestamp when session was last updated.
        messages: Related chat messages.
        requirements: Related extracted requirements.
        maturity: Related maturity state (one-to-one).
        prd_drafts: Related PRD drafts.
        user_stories: Related user stories.
    """

    __tablename__ = "ideation_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    data_source: Mapped[str] = mapped_column(String(32), default="mock")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    messages: Mapped[list["MessageORM"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    requirements: Mapped[list["RequirementORM"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    maturity: Mapped[Optional["MaturityORM"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", uselist=False
    )
    prd_drafts: Mapped[list["PRDDraftORM"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    user_stories: Mapped[list["UserStoryORM"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class MessageORM(Base):
    """ORM model for chat messages.

    Maps to the ideation_messages table in PostgreSQL.

    Attributes:
        id: Unique message identifier.
        session_id: ID of the parent session.
        role: Role of the message sender (user, assistant, system).
        content: Text content of the message.
        timestamp: When the message was created.
        maturity_delta: Change in maturity score from this message.
        message_metadata: Optional JSON metadata (model info, tokens, etc.).
        session: Related session object.
    """

    __tablename__ = "ideation_messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("ideation_sessions.id", ondelete="CASCADE"),
        index=True,
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), index=True
    )
    maturity_delta: Mapped[int] = mapped_column(Integer, default=0)
    message_metadata: Mapped[Any | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )

    # Relationship
    session: Mapped["SessionORM"] = relationship(back_populates="messages")


class RequirementORM(Base):
    """ORM model for extracted requirements.

    Maps to the ideation_requirements table in PostgreSQL.

    Attributes:
        id: Unique requirement identifier.
        session_id: ID of the parent session.
        description: Text description of the requirement.
        type: Requirement type (functional, non_functional).
        priority: Priority level (must_have, should_have, could_have).
        category_id: Optional category for grouping.
        created_at: When the requirement was extracted.
        session: Related session object.
    """

    __tablename__ = "ideation_requirements"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("ideation_sessions.id", ondelete="CASCADE"),
        index=True,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    priority: Mapped[str] = mapped_column(String(32), nullable=False)
    category_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    # Relationship
    session: Mapped["SessionORM"] = relationship(back_populates="requirements")


class MaturityORM(Base):
    """ORM model for maturity state.

    Maps to the ideation_maturity table in PostgreSQL.
    Uses session_id as primary key (one-to-one with session).

    Attributes:
        session_id: ID of the parent session (also primary key).
        score: Overall maturity score (0-100).
        level: Maturity level name (beginner, intermediate, advanced).
        categories: JSON array of category scores.
        can_submit: Whether session is ready for PRD submission.
        gaps: JSON array of identified gaps.
        updated_at: When the maturity state was last updated.
        session: Related session object.
    """

    __tablename__ = "ideation_maturity"

    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("ideation_sessions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    level: Mapped[str] = mapped_column(String(32), nullable=False)
    categories: Mapped[Any] = mapped_column(JSONB, nullable=False)
    can_submit: Mapped[bool] = mapped_column(Boolean, default=False)
    gaps: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    session: Mapped["SessionORM"] = relationship(back_populates="maturity")


class PRDDraftORM(Base):
    """ORM model for PRD drafts.

    Maps to the ideation_prd_drafts table in PostgreSQL.

    Attributes:
        id: Unique draft identifier.
        session_id: ID of the parent session.
        title: Title of the PRD.
        version: Version string (e.g., "0.1.0").
        sections: JSON array of PRD sections.
        status: Draft status (draft, approved, etc.).
        created_at: When the draft was created.
        session: Related session object.
    """

    __tablename__ = "ideation_prd_drafts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("ideation_sessions.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    sections: Mapped[Any] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    # Relationship
    session: Mapped["SessionORM"] = relationship(back_populates="prd_drafts")


class UserStoryORM(Base):
    """ORM model for user stories.

    Maps to the ideation_user_stories table in PostgreSQL.

    Attributes:
        id: Unique story identifier.
        session_id: ID of the parent session.
        title: Short title for the story.
        as_a: The user role part of the story.
        i_want: The action/feature part of the story.
        so_that: The benefit/reason part of the story.
        acceptance_criteria: JSON array of acceptance criteria.
        linked_requirements: JSON array of linked requirement IDs.
        priority: Priority level (must_have, should_have, could_have).
        created_at: When the story was created.
        session: Related session object.
    """

    __tablename__ = "ideation_user_stories"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("ideation_sessions.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    as_a: Mapped[str] = mapped_column(Text, nullable=False)
    i_want: Mapped[str] = mapped_column(Text, nullable=False)
    so_that: Mapped[str] = mapped_column(Text, nullable=False)
    acceptance_criteria: Mapped[Any] = mapped_column(JSONB, nullable=False)
    linked_requirements: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    priority: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    # Relationship
    session: Mapped["SessionORM"] = relationship(back_populates="user_stories")

"""Domain models for Ideation Studio persistence.

Pure Python dataclasses with NO external dependencies.
These models represent the core domain entities for ideation sessions,
messages, requirements, maturity tracking, PRD drafts, and user stories.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List


class ProjectStatus(str, Enum):
    """Status of an ideation project/session.

    Inherits from str for JSON serialization compatibility.
    """

    DRAFT = "draft"
    APPROVED = "approved"
    IN_BUILD = "in_build"
    CLOSED = "closed"


class DataSource(str, Enum):
    """Data source for ideation session.

    Indicates whether the session uses mock data or configured backend.
    """

    MOCK = "mock"
    CONFIGURED = "configured"


class MessageRole(str, Enum):
    """Role of a chat message in the ideation conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class RequirementType(str, Enum):
    """Type classification for extracted requirements."""

    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"


class RequirementPriority(str, Enum):
    """Priority classification using MoSCoW method (without Won't Have)."""

    MUST_HAVE = "must_have"
    SHOULD_HAVE = "should_have"
    COULD_HAVE = "could_have"


@dataclass
class IdeationSession:
    """An ideation session for PRD development.

    Represents a user's ideation conversation that leads to a PRD.

    Attributes:
        id: Unique identifier for the session.
        project_name: Name of the project being ideated.
        user_id: Identifier of the user who owns this session.
        status: Current status of the project.
        data_source: Data source type (mock or configured).
        version: Version number for optimistic locking.
        created_at: When the session was created.
        updated_at: When the session was last updated.
    """

    id: str
    project_name: str
    user_id: str
    status: ProjectStatus = ProjectStatus.DRAFT
    data_source: DataSource = DataSource.MOCK
    version: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ChatMessage:
    """A message in the ideation conversation.

    Represents a single message exchanged during the ideation process.

    Attributes:
        id: Unique identifier for the message.
        session_id: ID of the session this message belongs to.
        role: Role of the message sender (user, assistant, system).
        content: Text content of the message.
        timestamp: When the message was created.
        maturity_delta: Change in maturity score caused by this message.
        metadata: Optional additional metadata (e.g., model info).
    """

    id: str
    session_id: str
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    maturity_delta: int = 0
    metadata: Optional[dict] = None


@dataclass
class ExtractedRequirement:
    """A requirement extracted from the ideation conversation.

    Attributes:
        id: Unique identifier for the requirement.
        session_id: ID of the session this requirement belongs to.
        description: Text description of the requirement.
        type: Type classification (functional, non-functional).
        priority: Priority level (must_have, should_have, could_have).
        category_id: Optional category for grouping requirements.
        created_at: When the requirement was extracted.
    """

    id: str
    session_id: str
    description: str
    type: RequirementType
    priority: RequirementPriority
    category_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MaturityCategory:
    """A category for maturity assessment.

    Represents one dimension of PRD maturity that is tracked.

    Attributes:
        id: Unique identifier for the category.
        name: Human-readable name of the category.
        score: Current score for this category (0-100).
        required_for_submit: Whether this category must meet threshold to submit.
    """

    id: str
    name: str
    score: int
    required_for_submit: bool


@dataclass
class MaturityState:
    """Current maturity state of an ideation session.

    Tracks the overall maturity and readiness for PRD generation.

    Attributes:
        session_id: ID of the session this state belongs to.
        score: Overall maturity score (0-100).
        level: Maturity level name (e.g., "beginner", "intermediate", "advanced").
        categories: List of category scores.
        can_submit: Whether the session is ready to submit for PRD generation.
        gaps: List of identified gaps that need to be addressed.
        updated_at: When the maturity state was last updated.
    """

    session_id: str
    score: int
    level: str
    categories: List[MaturityCategory]
    can_submit: bool = False
    gaps: List[str] = field(default_factory=list)
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PRDSection:
    """A section within a PRD document.

    Attributes:
        id: Unique identifier for the section.
        heading: Section heading/title.
        content: Markdown content of the section.
        order: Display order within the PRD.
    """

    id: str
    heading: str
    content: str
    order: int


@dataclass
class PRDDraft:
    """A draft PRD document.

    Represents a generated PRD that can be reviewed and refined.

    Attributes:
        id: Unique identifier for the draft.
        session_id: ID of the session this draft belongs to.
        title: Title of the PRD.
        version: Version string (e.g., "0.1.0", "1.0.0").
        sections: List of sections in the PRD.
        status: Status of the draft (draft, approved, etc.).
        created_at: When the draft was created.
    """

    id: str
    session_id: str
    title: str
    version: str
    sections: List[PRDSection]
    status: str = "draft"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class UserStory:
    """A user story extracted from the ideation session.

    Uses the standard "As a... I want... So that..." format.

    Attributes:
        id: Unique identifier for the user story.
        session_id: ID of the session this story belongs to.
        title: Short title for the story.
        as_a: The user role (e.g., "registered user").
        i_want: The desired action or feature.
        so_that: The benefit or reason.
        acceptance_criteria: List of criteria that must be met.
        linked_requirements: IDs of requirements this story addresses.
        priority: Priority level of the story.
        created_at: When the story was created.
    """

    id: str
    session_id: str
    title: str
    as_a: str
    i_want: str
    so_that: str
    acceptance_criteria: List[str]
    linked_requirements: List[str] = field(default_factory=list)
    priority: RequirementPriority = RequirementPriority.SHOULD_HAVE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

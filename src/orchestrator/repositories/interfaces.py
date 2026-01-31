"""Repository interfaces for ideation persistence.

Abstract base classes defining the contract for persistence operations.
Implementations can use PostgreSQL, Redis, or other backends.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, List

from src.core.models.ideation import (
    IdeationSession,
    ChatMessage,
    ExtractedRequirement,
    MaturityState,
    PRDDraft,
    UserStory,
)


class ISessionRepository(ABC):
    """Abstract base class for session persistence operations.

    Implementations must provide async methods for CRUD operations
    on ideation sessions.
    """

    @abstractmethod
    async def create(self, session: IdeationSession) -> IdeationSession:
        """Create a new session and return it with generated ID.

        Args:
            session: The session to create.

        Returns:
            The created session with ID populated.
        """
        pass

    @abstractmethod
    async def get_by_id(self, session_id: str) -> Optional[IdeationSession]:
        """Get session by ID or None if not found.

        Args:
            session_id: The session ID to look up.

        Returns:
            The session if found, None otherwise.
        """
        pass

    @abstractmethod
    async def update(self, session: IdeationSession) -> None:
        """Update an existing session.

        Args:
            session: The session with updated values.
        """
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> None:
        """Delete session and all related data.

        Args:
            session_id: The ID of the session to delete.
        """
        pass

    @abstractmethod
    async def list_by_user(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[IdeationSession]:
        """List sessions for a user, ordered by updated_at desc.

        Args:
            user_id: The user ID to filter by.
            limit: Maximum number of sessions to return.
            offset: Number of sessions to skip.

        Returns:
            List of sessions for the user.
        """
        pass


class IMessageRepository(ABC):
    """Abstract base class for message persistence operations.

    Implementations must provide async methods for creating and
    retrieving chat messages.
    """

    @abstractmethod
    async def create(self, message: ChatMessage) -> ChatMessage:
        """Create a new message.

        Args:
            message: The message to create.

        Returns:
            The created message.
        """
        pass

    @abstractmethod
    async def get_by_session(
        self, session_id: str, limit: int = 100, offset: int = 0
    ) -> List[ChatMessage]:
        """Get messages for session, ordered by timestamp asc.

        Args:
            session_id: The session ID to filter by.
            limit: Maximum number of messages to return.
            offset: Number of messages to skip.

        Returns:
            List of messages for the session.
        """
        pass

    @abstractmethod
    async def delete_by_session(self, session_id: str) -> None:
        """Delete all messages for a session.

        Args:
            session_id: The session ID whose messages to delete.
        """
        pass


class IRequirementRepository(ABC):
    """Abstract base class for requirement persistence operations.

    Implementations must provide async methods for CRUD operations
    on extracted requirements.
    """

    @abstractmethod
    async def create(self, requirement: ExtractedRequirement) -> ExtractedRequirement:
        """Create a new requirement.

        Args:
            requirement: The requirement to create.

        Returns:
            The created requirement.
        """
        pass

    @abstractmethod
    async def get_by_session(self, session_id: str) -> List[ExtractedRequirement]:
        """Get all requirements for a session.

        Args:
            session_id: The session ID to filter by.

        Returns:
            List of requirements for the session.
        """
        pass

    @abstractmethod
    async def update(self, requirement: ExtractedRequirement) -> None:
        """Update an existing requirement.

        Args:
            requirement: The requirement with updated values.
        """
        pass

    @abstractmethod
    async def delete(self, requirement_id: str) -> None:
        """Delete a requirement by ID.

        Args:
            requirement_id: The ID of the requirement to delete.
        """
        pass


class IMaturityRepository(ABC):
    """Abstract base class for maturity state persistence operations.

    Implementations must provide async methods for saving and
    retrieving maturity state.
    """

    @abstractmethod
    async def save(self, maturity: MaturityState) -> None:
        """Save or update maturity state (upsert).

        Args:
            maturity: The maturity state to save.
        """
        pass

    @abstractmethod
    async def get_by_session(self, session_id: str) -> Optional[MaturityState]:
        """Get maturity state for session.

        Args:
            session_id: The session ID to look up.

        Returns:
            The maturity state if found, None otherwise.
        """
        pass


class IPRDRepository(ABC):
    """Abstract base class for PRD persistence operations.

    Implementations must provide async methods for saving and
    retrieving PRD drafts and user stories.
    """

    @abstractmethod
    async def save_draft(self, draft: PRDDraft) -> PRDDraft:
        """Save a PRD draft.

        Args:
            draft: The PRD draft to save.

        Returns:
            The saved PRD draft.
        """
        pass

    @abstractmethod
    async def get_draft(self, session_id: str) -> Optional[PRDDraft]:
        """Get latest PRD draft for session.

        Args:
            session_id: The session ID to look up.

        Returns:
            The PRD draft if found, None otherwise.
        """
        pass

    @abstractmethod
    async def save_user_stories(
        self, session_id: str, stories: List[UserStory]
    ) -> None:
        """Save user stories for session.

        Args:
            session_id: The session ID to associate stories with.
            stories: List of user stories to save.
        """
        pass

    @abstractmethod
    async def get_user_stories(self, session_id: str) -> List[UserStory]:
        """Get user stories for session.

        Args:
            session_id: The session ID to look up.

        Returns:
            List of user stories for the session.
        """
        pass

"""Ideation Service Implementation.

This module provides the real implementation of IdeationService that uses
the LLM client factory and IdeationAgent for processing ideation chat.

The service uses the repository pattern for persistence, supporting both
PostgreSQL (default) and Redis backends via the repository factory.
"""

from __future__ import annotations

import logging
import os
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Callable, TypeVar

from src.core.models.ideation import (
    ChatMessage,
    MessageRole,
)
from src.core.models.ideation import (
    MaturityCategory as DomainMaturityCategory,
)
from src.core.models.ideation import (
    MaturityState as DomainMaturityState,
)
from src.infrastructure.llm.factory import (
    LLMClientError,
    LLMClientFactory,
    get_llm_client_factory,
)
from src.orchestrator.api.models.llm_config import AgentRole
from src.orchestrator.repositories.factory import (
    RepositoryFactory,
    get_repository_factory,
)
from src.workers.agents.ideation.ideation_agent import (
    MATURITY_CATEGORIES,
    IdeationAgent,
    IdeationConfig,
)
from src.workers.agents.protocols import AgentContext

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.orchestrator.persistence.database import Database
    from src.orchestrator.repositories.interfaces import (
        IMaturityRepository,
        IMessageRepository,
        IRequirementRepository,
        ISessionRepository,
    )

T = TypeVar("T")

logger = logging.getLogger(__name__)


class IdeationServiceImpl:
    """Real implementation of IdeationService using LLM factory.

    Integrates with IdeationAgent, PRDGenerator, and UserStoryExtractor
    using configured LLM clients from the admin panel.

    Uses the repository pattern for persistence, supporting both PostgreSQL
    and Redis backends via the repository factory.

    Usage:
        service = IdeationServiceImpl()
        response = await service.process_chat(request)
    """

    def __init__(
        self,
        llm_factory: LLMClientFactory | None = None,
        repository_factory: RepositoryFactory | None = None,
        database: Database | None = None,
    ) -> None:
        """Initialize the ideation service.

        Args:
            llm_factory: Optional LLM client factory. Uses global singleton if not provided.
            repository_factory: Optional repository factory. Uses env-based factory if not provided.
            database: Optional database instance for PostgreSQL backend.
        """
        self._llm_factory = llm_factory
        self._repository_factory = repository_factory
        self._database = database
        self._backend = os.getenv("IDEATION_PERSISTENCE_BACKEND", "postgres")

    def _get_factory(self) -> LLMClientFactory:
        """Get the LLM client factory.

        Returns:
            LLMClientFactory: The factory instance.
        """
        if self._llm_factory is None:
            self._llm_factory = get_llm_client_factory()
        return self._llm_factory

    def _get_repository_factory(self) -> RepositoryFactory:
        """Get the repository factory.

        Returns:
            RepositoryFactory: The factory instance based on environment configuration.
        """
        if self._repository_factory is None:
            self._repository_factory = get_repository_factory()
        return self._repository_factory

    def _get_database(self) -> Database:
        """Get the database instance for PostgreSQL backend.

        Returns:
            Database: The database instance.
        """
        if self._database is None:
            from src.orchestrator.persistence.database import get_database

            self._database = get_database()
        return self._database

    def _is_postgres_backend(self) -> bool:
        """Check if using PostgreSQL backend.

        Returns:
            bool: True if using PostgreSQL, False for Redis.
        """
        return self._backend == "postgres"

    @asynccontextmanager
    async def _db_session(self) -> AsyncIterator[AsyncSession | None]:
        """Get a database session context for PostgreSQL, or None for Redis.

        For PostgreSQL backend, provides a managed session with commit/rollback.
        For Redis backend, yields None (session is ignored by Redis repos).

        Yields:
            AsyncSession | None: Database session for PostgreSQL, None for Redis.
        """
        if self._is_postgres_backend():
            db = self._get_database()
            async with db.session() as session:
                yield session
        else:
            yield None

    async def _with_session(
        self,
        callback: Callable[[AsyncSession | None], Any],
    ) -> Any:
        """Execute callback with a database session.

        Args:
            callback: Async function that takes a session and returns a result.

        Returns:
            The result of the callback.
        """
        async with self._db_session() as session:
            return await callback(session)

    def _get_message_repository(
        self, db_session: AsyncSession | None = None
    ) -> IMessageRepository:
        """Get the message repository.

        Args:
            db_session: Database session for PostgreSQL backend.

        Returns:
            IMessageRepository: Message repository instance.
        """
        factory = self._get_repository_factory()
        return factory.get_message_repository(db_session)

    def _get_maturity_repository(
        self, db_session: AsyncSession | None = None
    ) -> IMaturityRepository:
        """Get the maturity repository.

        Args:
            db_session: Database session for PostgreSQL backend.

        Returns:
            IMaturityRepository: Maturity repository instance.
        """
        factory = self._get_repository_factory()
        return factory.get_maturity_repository(db_session)

    def _get_session_repository(
        self, db_session: AsyncSession | None = None
    ) -> ISessionRepository:
        """Get the session repository.

        Args:
            db_session: Database session for PostgreSQL backend.

        Returns:
            ISessionRepository: Session repository instance.
        """
        factory = self._get_repository_factory()
        return factory.get_session_repository(db_session)

    def _get_requirement_repository(
        self, db_session: AsyncSession | None = None
    ) -> IRequirementRepository:
        """Get the requirement repository.

        Args:
            db_session: Database session for PostgreSQL backend.

        Returns:
            IRequirementRepository: Requirement repository instance.
        """
        factory = self._get_repository_factory()
        return factory.get_requirement_repository(db_session)

    async def _ensure_session_exists(
        self,
        session_id: str,
        project_name: str = "Untitled Project",
        user_id: str = "anonymous",
        data_source: str = "mock",
    ) -> None:
        """Ensure a session exists in the database, creating it if needed.

        Args:
            session_id: Session identifier.
            project_name: Project name for new sessions.
            user_id: User ID for new sessions.
            data_source: Data source for new sessions.
        """
        from src.core.models.ideation import DataSource, IdeationSession, ProjectStatus

        async with self._db_session() as db_session:
            session_repo = self._get_session_repository(db_session)
            existing = await session_repo.get_by_id(session_id)

            if existing is None:
                # Create new session
                new_session = IdeationSession(
                    id=session_id,
                    project_name=project_name,
                    user_id=user_id,
                    status=ProjectStatus.DRAFT,
                    data_source=DataSource(data_source)
                    if data_source in ["mock", "configured"]
                    else DataSource.MOCK,
                    version=1,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
                await session_repo.create(new_session)

    async def process_chat(
        self,
        request: Any,  # IdeationChatRequest from routes
        model: str | None = None,
    ) -> Any:  # IdeationChatResponse from routes
        """Process chat message using IdeationAgent with configured LLM.

        Args:
            request: Chat request with message and context.
            model: Optional model override (not used, config determines model).

        Returns:
            IdeationChatResponse: Response with maturity update.

        Raises:
            LLMClientError: If LLM client cannot be created.
        """
        from src.orchestrator.routes.ideation_api import (
            CategoryMaturity,
            IdeationChatResponse,
            IdeationMessage,
            MaturityState,
            Requirement,
        )

        # Get the discovery LLM client for ideation
        factory = self._get_factory()

        try:
            llm_client = await factory.get_client(AgentRole.DISCOVERY)
        except LLMClientError as e:
            logger.error(f"Failed to get LLM client for ideation: {e}")
            # Fall back to raising to let API return appropriate error
            raise

        # Create ideation agent with the configured client
        agent = IdeationAgent(
            llm_client=llm_client,
            config=IdeationConfig(
                model=llm_client.model,
                max_tokens=llm_client.max_tokens,
                temperature=llm_client.temperature,
            ),
        )

        # Create agent context
        context = AgentContext(
            session_id=request.sessionId,
            task_id=f"chat-{uuid.uuid4().hex[:8]}",
            tenant_id="default",
            workspace_path="/tmp/ideation",
        )

        # Ensure session exists in database before any other operations
        await self._ensure_session_exists(
            request.sessionId,
            project_name=getattr(request, "projectName", None) or "Untitled Project",
            user_id=getattr(request, "userId", "anonymous"),
            data_source=getattr(request, "dataSource", "mock"),
        )

        # Get conversation history from session if available
        conversation_history = await self._get_conversation_history(request.sessionId)

        # Get current maturity from session or request
        current_maturity = await self._get_session_maturity_dict(request.sessionId)
        if not current_maturity:
            current_maturity = {}

        # Execute the agent
        result = await agent.execute(
            context,
            {
                "user_message": request.message,
                "conversation_history": conversation_history,
                "current_maturity": current_maturity,
            },
        )

        if not result.success:
            logger.error(f"IdeationAgent failed: {result.error_message}")
            raise LLMClientError(f"Ideation agent failed: {result.error_message}")

        # Extract response data
        metadata = result.metadata or {}
        now = datetime.now(UTC).isoformat()

        # Update maturity from agent response
        maturity_updates = metadata.get("maturity_updates", {})
        for cat_id, score in maturity_updates.items():
            current_maturity[cat_id] = score

        # Calculate overall maturity
        overall_score = agent.calculate_overall_maturity(current_maturity)
        maturity_level = agent.get_maturity_level(overall_score)
        can_submit = agent.can_submit(current_maturity)
        gaps = agent.identify_gaps(current_maturity)

        # Build category maturity list
        categories = []
        for cat in MATURITY_CATEGORIES:
            categories.append(
                CategoryMaturity(
                    id=cat.id,
                    name=cat.name,
                    score=current_maturity.get(cat.id, 0),
                    requiredForSubmit=True,
                    sections=[],
                )
            )

        maturity_state = MaturityState(
            score=overall_score,
            level=maturity_level,
            categories=categories,
            canSubmit=can_submit,
            gaps=gaps,
        )

        # Build extracted requirements
        extracted_requirements = []
        for req in metadata.get("extracted_requirements", []):
            extracted_requirements.append(
                Requirement(
                    id=req.get("id", f"REQ-{uuid.uuid4().hex[:6]}"),
                    description=req.get("description", ""),
                    type=req.get("type", "functional"),
                    priority=req.get("priority", "should_have"),
                    categoryId=req.get("category_id", "functional"),
                    sourceMessageId=context.task_id,
                    createdAt=now,
                )
            )

        # Get suggested followups
        suggested_followups = metadata.get("follow_up_questions", [])

        # Create response message
        message = IdeationMessage(
            id=f"msg-{uuid.uuid4().hex[:8]}",
            role="assistant",
            content=metadata.get("response", ""),
            timestamp=now,
            maturityDelta=overall_score - request.currentMaturity,
            extractedRequirements=extracted_requirements,
            suggestedFollowups=suggested_followups,
        )

        # Save conversation to session
        await self._save_conversation_message(
            request.sessionId,
            {"role": "user", "content": request.message},
        )
        await self._save_conversation_message(
            request.sessionId,
            {"role": "assistant", "content": metadata.get("response", "")},
        )

        # Save updated maturity
        await self._save_session_maturity(request.sessionId, current_maturity)

        return IdeationChatResponse(
            message=message,
            maturityUpdate=maturity_state,
            extractedRequirements=extracted_requirements,
            suggestedFollowups=suggested_followups,
        )

    async def submit_for_prd(self, request: Any) -> Any:
        """Submit ideation session for PRD generation.

        Args:
            request: PRD submission request.

        Returns:
            SubmitPRDResponse: Response with PRD draft and user stories.

        Note:
            Full implementation pending - uses mock for now.
        """
        # TODO: Implement using PRDGenerator and UserStoryExtractor
        raise NotImplementedError("submit_for_prd not yet implemented with real LLM")

    async def get_session_maturity(self, session_id: str) -> Any | None:
        """Get current maturity state for a session.

        Args:
            session_id: Session identifier.

        Returns:
            MaturityState | None: Current maturity or None if not found.
        """
        from src.orchestrator.routes.ideation_api import (
            CategoryMaturity,
            MaturityState,
        )

        async with self._db_session() as db_session:
            # Use repository to get maturity state
            maturity_repo = self._get_maturity_repository(db_session)
            domain_maturity = await maturity_repo.get_by_session(session_id)

            if domain_maturity is None:
                return None

            # Convert domain model to API model
            categories = []
            for cat in domain_maturity.categories:
                categories.append(
                    CategoryMaturity(
                        id=cat.id,
                        name=cat.name,
                        score=cat.score,
                        requiredForSubmit=cat.required_for_submit,
                        sections=[],
                    )
                )

            return MaturityState(
                score=domain_maturity.score,
                level=domain_maturity.level,
                categories=categories,
                canSubmit=domain_maturity.can_submit,
                gaps=domain_maturity.gaps,
            )

    async def save_draft(self, session_id: str, request: Any) -> Any:
        """Save session draft.

        Args:
            session_id: Session identifier.
            request: Draft data to save.

        Returns:
            SaveDraftResponse: Response confirming save.
        """
        from src.orchestrator.routes.ideation_api import SaveDraftResponse

        async with self._db_session() as db_session:
            # Save maturity state using repository
            maturity_repo = self._get_maturity_repository(db_session)

            # Convert API model to domain model
            domain_categories = []
            for cat in request.maturityState.categories:
                domain_categories.append(
                    DomainMaturityCategory(
                        id=cat.id,
                        name=cat.name,
                        score=cat.score,
                        required_for_submit=cat.requiredForSubmit,
                    )
                )

            domain_maturity = DomainMaturityState(
                session_id=session_id,
                score=request.maturityState.score,
                level=request.maturityState.level,
                categories=domain_categories,
                can_submit=request.maturityState.canSubmit,
                gaps=request.maturityState.gaps or [],
                updated_at=datetime.now(UTC),
            )

            await maturity_repo.save(domain_maturity)

            # Update session project name if provided
            if hasattr(request, "projectName") and request.projectName:
                session_repo = self._get_session_repository(db_session)
                session = await session_repo.get_by_id(session_id)
                if session:
                    session.project_name = request.projectName
                    session.updated_at = datetime.now(UTC)
                    await session_repo.update(session)

            # Save messages using repository - within same session
            message_repo = self._get_message_repository(db_session)
            for msg in request.messages:
                domain_message = ChatMessage(
                    id=f"msg-{uuid.uuid4().hex[:8]}",
                    session_id=session_id,
                    role=MessageRole(msg.role),
                    content=msg.content,
                    timestamp=datetime.now(UTC),
                    maturity_delta=0,
                    metadata=None,
                )
                await message_repo.create(domain_message)

        return SaveDraftResponse(
            success=True,
            sessionId=session_id,
            savedAt=datetime.now(UTC).isoformat(),
        )

    async def list_sessions(
        self,
        user_id: str = "anonymous",
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list, int]:
        """List sessions for a user.

        Args:
            user_id: User identifier.
            limit: Maximum number of sessions to return.
            offset: Number of sessions to skip.

        Returns:
            tuple[list, int]: List of session summaries and total count.
        """
        async with self._db_session() as db_session:
            session_repo = self._get_session_repository(db_session)
            sessions = await session_repo.list_by_user(user_id, limit, offset)

            # Get message counts and maturity for each session
            result = []
            for session in sessions:
                msg_repo = self._get_message_repository(db_session)
                messages = await msg_repo.get_by_session(session.id, limit=1000, offset=0)

                mat_repo = self._get_maturity_repository(db_session)
                maturity = await mat_repo.get_by_session(session.id)

                result.append({
                    "id": session.id,
                    "project_name": session.project_name,
                    "status": session.status.value,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "message_count": len(messages),
                    "maturity_score": float(maturity.score) if maturity else 0.0,
                })

            return result, len(sessions)

    async def get_session(self, session_id: str) -> dict | None:
        """Get full session details including messages and maturity.

        Args:
            session_id: Session identifier.

        Returns:
            dict | None: Session details or None if not found.
        """
        async with self._db_session() as db_session:
            session_repo = self._get_session_repository(db_session)
            session = await session_repo.get_by_id(session_id)

            if session is None:
                return None

            msg_repo = self._get_message_repository(db_session)
            messages = await msg_repo.get_by_session(session_id, limit=1000, offset=0)

            mat_repo = self._get_maturity_repository(db_session)
            maturity = await mat_repo.get_by_session(session_id)

            req_repo = self._get_requirement_repository(db_session)
            requirements = await req_repo.get_by_session(session_id)

            return {
                "id": session.id,
                "project_name": session.project_name,
                "status": session.status.value,
                "messages": messages,
                "maturity": maturity,
                "requirements": requirements,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
            }

    async def update_session(
        self,
        session_id: str,
        project_name: str | None,
        status: str | None,
    ) -> bool | None:
        """Update session details.

        Args:
            session_id: Session identifier.
            project_name: New project name (optional).
            status: New status (optional).

        Returns:
            bool | None: True if updated, None if session not found.
        """
        from src.core.models.ideation import ProjectStatus

        async with self._db_session() as db_session:
            session_repo = self._get_session_repository(db_session)
            session = await session_repo.get_by_id(session_id)

            if session is None:
                return None

            # Update fields if provided
            if project_name is not None:
                session.project_name = project_name
            if status is not None:
                session.status = ProjectStatus(status)
            session.updated_at = datetime.now(UTC)

            await session_repo.update(session)
            return True

    # =========================================================================
    # Session Storage Helpers
    # =========================================================================

    async def _get_conversation_history(self, session_id: str) -> list[dict[str, str]]:
        """Get conversation history using message repository.

        Args:
            session_id: Session identifier.

        Returns:
            list[dict[str, str]]: Conversation history as list of role/content dicts.
        """
        async with self._db_session() as db_session:
            message_repo = self._get_message_repository(db_session)
            messages = await message_repo.get_by_session(session_id)

            # Convert domain messages to dict format expected by agent
            return [
                {"role": msg.role.value, "content": msg.content} for msg in messages
            ]

    async def _save_conversation_message(
        self,
        session_id: str,
        message: dict[str, str],
    ) -> None:
        """Save a conversation message using message repository.

        Args:
            session_id: Session identifier.
            message: Message dict with 'role' and 'content' keys.
        """
        async with self._db_session() as db_session:
            message_repo = self._get_message_repository(db_session)

            # Convert dict to domain model
            domain_message = ChatMessage(
                id=f"msg-{uuid.uuid4().hex[:8]}",
                session_id=session_id,
                role=MessageRole(message["role"]),
                content=message["content"],
                timestamp=datetime.now(UTC),
                maturity_delta=0,
                metadata=None,
            )

            await message_repo.create(domain_message)

    async def _get_session_maturity_dict(
        self,
        session_id: str,
    ) -> dict[str, float]:
        """Get session maturity as dict using maturity repository.

        Args:
            session_id: Session identifier.

        Returns:
            dict[str, float]: Maturity scores by category.
        """
        async with self._db_session() as db_session:
            maturity_repo = self._get_maturity_repository(db_session)
            domain_maturity = await maturity_repo.get_by_session(session_id)

            if domain_maturity is None:
                return {}

            # Convert domain model to dict format expected by agent
            return {cat.id: cat.score for cat in domain_maturity.categories}

    async def _save_session_maturity(
        self,
        session_id: str,
        maturity: dict[str, float],
    ) -> None:
        """Save session maturity using maturity repository.

        Args:
            session_id: Session identifier.
            maturity: Maturity scores by category.
        """
        async with self._db_session() as db_session:
            maturity_repo = self._get_maturity_repository(db_session)

            # Build domain categories from dict
            domain_categories = []
            for cat in MATURITY_CATEGORIES:
                domain_categories.append(
                    DomainMaturityCategory(
                        id=cat.id,
                        name=cat.name,
                        score=int(maturity.get(cat.id, 0)),
                        required_for_submit=True,
                    )
                )

            # Calculate overall metrics
            agent = IdeationAgent(
                llm_client=None,  # type: ignore
                config=IdeationConfig(),
            )
            overall_score = agent.calculate_overall_maturity(maturity)
            maturity_level = agent.get_maturity_level(overall_score)
            can_submit = agent.can_submit(maturity)
            gaps = agent.identify_gaps(maturity)

            domain_maturity = DomainMaturityState(
                session_id=session_id,
                score=overall_score,
                level=maturity_level,
                categories=domain_categories,
                can_submit=can_submit,
                gaps=gaps,
                updated_at=datetime.now(UTC),
            )

            await maturity_repo.save(domain_maturity)



# Global service instance
_ideation_service_impl: IdeationServiceImpl | None = None


def get_ideation_service_impl() -> IdeationServiceImpl:
    """Get the global ideation service implementation instance.

    Returns:
        IdeationServiceImpl: The service instance.
    """
    global _ideation_service_impl
    if _ideation_service_impl is None:
        _ideation_service_impl = IdeationServiceImpl()
    return _ideation_service_impl

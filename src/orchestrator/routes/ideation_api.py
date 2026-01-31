"""Ideation API routes for PRD Ideation Studio.

This module provides API endpoints for the PRD Ideation Studio (P05-F11):
- POST /api/studio/ideation/chat - Process chat messages
- POST /api/studio/ideation/submit-prd - Submit for PRD generation
- GET /api/studio/ideation/{sessionId}/maturity - Get session maturity
- POST /api/studio/ideation/{sessionId}/draft - Save session draft
- GET /api/studio/ideation/sessions - List all sessions for a user
- GET /api/studio/ideation/sessions/{session_id} - Load a specific session
- PATCH /api/studio/ideation/sessions/{session_id} - Update session details
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/studio/ideation", tags=["ideation"])


# =============================================================================
# Request/Response Models
# =============================================================================


class SectionMaturity(BaseModel):
    """Section maturity within a category."""

    id: str
    name: str
    score: float


class CategoryMaturity(BaseModel):
    """Category maturity state."""

    id: str
    name: str
    score: float
    requiredForSubmit: bool
    sections: list[SectionMaturity] = []


class MaturityState(BaseModel):
    """Overall maturity state."""

    score: float
    level: str
    categories: list[CategoryMaturity]
    canSubmit: bool
    gaps: list[str] = []


class Requirement(BaseModel):
    """Extracted requirement."""

    id: str
    description: str
    type: str  # functional, non_functional, constraint
    priority: str  # must_have, should_have, could_have
    categoryId: str
    sourceMessageId: str | None = None
    createdAt: str


class IdeationMessage(BaseModel):
    """Message in ideation chat."""

    id: str
    role: str  # user, assistant, system
    content: str
    timestamp: str
    maturityDelta: float | None = None
    extractedRequirements: list[Requirement] = []
    suggestedFollowups: list[str] = []


class IdeationChatRequest(BaseModel):
    """Request for ideation chat."""

    sessionId: str
    message: str
    currentMaturity: float
    projectName: str | None = None
    model: str | None = None  # sonnet, opus, haiku
    rlmEnabled: bool | None = None

    model_config = {"populate_by_name": True}


class IdeationChatResponse(BaseModel):
    """Response from ideation chat."""

    message: IdeationMessage
    maturityUpdate: MaturityState
    extractedRequirements: list[Requirement]
    projectName: str | None = None
    suggestedFollowups: list[str]

    model_config = {"populate_by_name": True}


class PRDSection(BaseModel):
    """Section in a PRD document."""

    id: str
    heading: str
    content: str
    order: int


class PRDDocument(BaseModel):
    """PRD document structure."""

    id: str
    title: str
    version: str
    sections: list[PRDSection]
    createdAt: str
    status: str  # draft, pending_review, approved

    model_config = {"populate_by_name": True}


class UserStory(BaseModel):
    """User story."""

    id: str
    title: str
    asA: str
    iWant: str
    soThat: str
    acceptanceCriteria: list[str]
    linkedRequirements: list[str]
    priority: str  # must_have, should_have, could_have

    model_config = {"populate_by_name": True}


class SubmitPRDRequest(BaseModel):
    """Request to submit for PRD generation."""

    sessionId: str
    maturityState: MaturityState
    includeUserStories: bool = True

    model_config = {"populate_by_name": True}


class SubmitPRDResponse(BaseModel):
    """Response from PRD submission."""

    gateId: str
    prdDraft: PRDDocument
    userStories: list[UserStory]
    status: str

    model_config = {"populate_by_name": True}


class SaveDraftRequest(BaseModel):
    """Request to save session draft."""

    messages: list[IdeationMessage]
    maturityState: MaturityState
    extractedRequirements: list[Requirement]
    projectName: str | None = None

    model_config = {"populate_by_name": True}


class SaveDraftResponse(BaseModel):
    """Response from save draft."""

    success: bool
    sessionId: str
    savedAt: str

    model_config = {"populate_by_name": True}


class SessionSummary(BaseModel):
    """Summary of an ideation session."""

    id: str
    projectName: str
    status: str
    createdAt: str
    updatedAt: str
    messageCount: int = 0
    maturityScore: float = 0.0

    model_config = {"populate_by_name": True}


class SessionListResponse(BaseModel):
    """Response for session list."""

    sessions: list[SessionSummary]
    total: int
    limit: int
    offset: int


class SessionDetailResponse(BaseModel):
    """Response for session detail."""

    id: str
    projectName: str
    status: str
    messages: list[IdeationMessage]
    maturityState: MaturityState | None
    requirements: list[Requirement]
    createdAt: str
    updatedAt: str

    model_config = {"populate_by_name": True}


class UpdateSessionRequest(BaseModel):
    """Request to update session details."""

    projectName: str | None = None
    status: str | None = None

    model_config = {"populate_by_name": True}


# =============================================================================
# Service Interface
# =============================================================================


def _get_service() -> Any:
    """Get the ideation service instance.

    Returns:
        IdeationService: Service instance.
    """
    return get_ideation_service()


class IdeationService:
    """Service interface for ideation operations.

    Delegates to IdeationServiceImpl when configured LLM is available,
    falls back to NotImplementedError which triggers mock responses.

    The service provides:
    - Chat processing with maturity tracking
    - PRD document generation
    - Session maturity retrieval
    - Draft persistence
    - Session listing and retrieval
    - Session update (rename, status change)
    """

    def __init__(self) -> None:
        """Initialize the ideation service."""
        self._impl: Any = None
        self._use_real_impl = True

    def _get_impl(self) -> Any:
        """Get the real implementation if available.

        Returns:
            IdeationServiceImpl: The real implementation.

        Raises:
            NotImplementedError: If real implementation not available.
        """
        if not self._use_real_impl:
            raise NotImplementedError("Using mock implementation")

        if self._impl is None:
            try:
                from src.orchestrator.services.ideation_service import (
                    get_ideation_service_impl,
                )
                self._impl = get_ideation_service_impl()
            except ImportError:
                self._use_real_impl = False
                raise NotImplementedError("Real implementation not available")

        return self._impl

    async def process_chat(
        self,
        request: IdeationChatRequest,
        model: str | None = None,
    ) -> IdeationChatResponse:
        """Process chat message and return response with maturity update.

        Args:
            request: Chat request.
            model: Optional model override.

        Returns:
            IdeationChatResponse: Response with maturity update.
        """
        impl = self._get_impl()
        return await impl.process_chat(request, model)

    async def submit_for_prd(
        self,
        request: SubmitPRDRequest,
    ) -> SubmitPRDResponse:
        """Submit ideation session for PRD generation.

        Args:
            request: PRD submission request.

        Returns:
            SubmitPRDResponse: Response with PRD draft and user stories.
        """
        impl = self._get_impl()
        return await impl.submit_for_prd(request)

    async def get_session_maturity(
        self,
        session_id: str,
    ) -> MaturityState | None:
        """Get current maturity state for a session.

        Args:
            session_id: Session identifier.

        Returns:
            MaturityState | None: Current maturity or None if not found.
        """
        impl = self._get_impl()
        return await impl.get_session_maturity(session_id)

    async def save_draft(
        self,
        session_id: str,
        request: SaveDraftRequest,
    ) -> SaveDraftResponse:
        """Save session draft.

        Args:
            session_id: Session identifier.
            request: Draft data to save.

        Returns:
            SaveDraftResponse: Response confirming save.
        """
        impl = self._get_impl()
        return await impl.save_draft(session_id, request)

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
        impl = self._get_impl()
        return await impl.list_sessions(user_id, limit, offset)

    async def get_session(self, session_id: str) -> dict | None:
        """Get full session details.

        Args:
            session_id: Session identifier.

        Returns:
            dict | None: Session details or None if not found.
        """
        impl = self._get_impl()
        return await impl.get_session(session_id)

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
        impl = self._get_impl()
        return await impl.update_session(session_id, project_name, status)


# Global service instance (will be replaced with DI)
_ideation_service: IdeationService | None = None


def get_ideation_service() -> IdeationService:
    """Get the ideation service instance.

    Returns:
        IdeationService: Service instance.
    """
    global _ideation_service
    if _ideation_service is None:
        _ideation_service = IdeationService()
    return _ideation_service


# =============================================================================
# API Endpoints
# =============================================================================


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    user_id: str = Query("anonymous", description="User ID to filter sessions"),
    limit: int = Query(20, ge=1, le=100, description="Maximum sessions to return"),
    offset: int = Query(0, ge=0, description="Number of sessions to skip"),
) -> SessionListResponse:
    """List saved ideation sessions.

    Args:
        user_id: User identifier to filter sessions.
        limit: Maximum number of sessions to return.
        offset: Number of sessions to skip for pagination.

    Returns:
        SessionListResponse: List of session summaries with pagination info.

    Raises:
        HTTPException: 500 on service error.
    """
    try:
        sessions, total = await _get_service().list_sessions(user_id, limit, offset)
        return SessionListResponse(
            sessions=[
                SessionSummary(
                    id=s["id"],
                    projectName=s["project_name"],
                    status=s["status"],
                    createdAt=s["created_at"],
                    updatedAt=s["updated_at"],
                    messageCount=s["message_count"],
                    maturityScore=s["maturity_score"],
                )
                for s in sessions
            ],
            total=total,
            limit=limit,
            offset=offset,
        )
    except NotImplementedError:
        return SessionListResponse(sessions=[], total=0, limit=limit, offset=offset)
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: str = Path(..., description="Session ID"),
) -> SessionDetailResponse:
    """Get details of a specific session.

    Args:
        session_id: Session identifier.

    Returns:
        SessionDetailResponse: Full session details with messages and maturity.

    Raises:
        HTTPException: 404 if session not found.
        HTTPException: 500 on service error.
    """
    try:
        session = await _get_service().get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")

        # Convert domain models to API models
        messages = [
            IdeationMessage(
                id=m.id,
                role=m.role.value,
                content=m.content,
                timestamp=m.timestamp.isoformat(),
                maturityDelta=float(m.maturity_delta) if m.maturity_delta else None,
                extractedRequirements=[],
                suggestedFollowups=[],
            )
            for m in session["messages"]
        ]

        maturity_state = None
        if session["maturity"]:
            mat = session["maturity"]
            maturity_state = MaturityState(
                score=float(mat.score),
                level=mat.level,
                categories=[
                    CategoryMaturity(
                        id=c.id,
                        name=c.name,
                        score=float(c.score),
                        requiredForSubmit=c.required_for_submit,
                        sections=[],
                    )
                    for c in mat.categories
                ],
                canSubmit=mat.can_submit,
                gaps=mat.gaps or [],
            )

        requirements = [
            Requirement(
                id=r.id,
                description=r.description,
                type=r.type.value,
                priority=r.priority.value,
                categoryId=r.category_id or "",
                createdAt=r.created_at.isoformat(),
            )
            for r in session["requirements"]
        ]

        return SessionDetailResponse(
            id=session["id"],
            projectName=session["project_name"],
            status=session["status"],
            messages=messages,
            maturityState=maturity_state,
            requirements=requirements,
            createdAt=session["created_at"],
            updatedAt=session["updated_at"],
        )
    except HTTPException:
        raise
    except NotImplementedError:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        logger.error(f"Failed to get session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.patch("/sessions/{session_id}")
async def update_session(
    session_id: str = Path(..., description="Session ID"),
    request: UpdateSessionRequest = ...,
) -> dict:
    """Update session details (rename, change status).

    Args:
        session_id: Session identifier.
        request: Update request with optional projectName and status.

    Returns:
        dict: Success response with session ID.

    Raises:
        HTTPException: 404 if session not found.
        HTTPException: 501 if not implemented.
        HTTPException: 500 on service error.
    """
    try:
        result = await _get_service().update_session(
            session_id, request.projectName, request.status
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"success": True, "sessionId": session_id}
    except HTTPException:
        raise
    except NotImplementedError:
        raise HTTPException(status_code=501, detail="Not implemented")
    except Exception as e:
        logger.error(f"Failed to update session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=IdeationChatResponse)
async def process_chat(
    request: IdeationChatRequest,
    service: IdeationService = Depends(get_ideation_service),
) -> IdeationChatResponse:
    """Process ideation chat message.

    Sends the user message to the IdeationAgent and returns the response
    along with updated maturity scores and extracted requirements.

    Args:
        request: Chat request with message and context.
        service: Ideation service instance.

    Returns:
        IdeationChatResponse: Agent response with maturity update.

    Raises:
        HTTPException: 400 if message is empty or whitespace-only.
        HTTPException: 400 if session_id format is invalid.
        HTTPException: 500 on service error.
    """
    # Validate message is not empty or whitespace-only
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty",
        )

    # Validate session_id format (non-empty, alphanumeric with hyphens/underscores)
    if not request.sessionId or not request.sessionId.strip():
        raise HTTPException(
            status_code=400,
            detail="Session ID cannot be empty",
        )

    try:
        return await service.process_chat(
            request,
            model=request.model,
        )
    except NotImplementedError:
        # Return mock response for development
        return _mock_chat_response(request)
    except Exception as e:
        logger.error(f"Chat processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat: {str(e)}",
        ) from e


@router.post("/submit-prd", response_model=SubmitPRDResponse)
async def submit_prd(
    request: SubmitPRDRequest,
    service: IdeationService = Depends(get_ideation_service),
) -> SubmitPRDResponse:
    """Submit ideation session for PRD generation.

    Triggers PRD generation from the ideation session if maturity
    threshold is met. Creates a HITL gate for review.

    Args:
        request: PRD submission request.
        service: Ideation service instance.

    Returns:
        SubmitPRDResponse: PRD draft and user stories.

    Raises:
        HTTPException: 400 if maturity below threshold.
        HTTPException: 500 on service error.
    """
    # Check maturity threshold
    if not request.maturityState.canSubmit or request.maturityState.score < 80:
        raise HTTPException(
            status_code=400,
            detail=f"Maturity score {request.maturityState.score}% is below the 80% threshold required for PRD submission",
        )

    try:
        return await service.submit_for_prd(request)
    except NotImplementedError:
        # Return mock response for development
        return _mock_submit_response(request)
    except Exception as e:
        logger.error(f"PRD submission failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit PRD: {str(e)}",
        ) from e


@router.get("/{session_id}/maturity", response_model=MaturityState)
async def get_maturity(
    session_id: str = Path(..., description="Session ID"),
    service: IdeationService = Depends(get_ideation_service),
) -> MaturityState:
    """Get current maturity state for a session.

    Args:
        session_id: Session identifier.
        service: Ideation service instance.

    Returns:
        MaturityState: Current maturity state.

    Raises:
        HTTPException: 404 if session not found.
    """
    try:
        maturity = await service.get_session_maturity(session_id)
        if maturity is None:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found",
            )
        return maturity
    except NotImplementedError:
        # Return mock response for development
        return _mock_maturity_state()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get maturity failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get maturity: {str(e)}",
        ) from e


@router.post("/{session_id}/draft", response_model=SaveDraftResponse)
async def save_draft(
    request: SaveDraftRequest,
    session_id: str = Path(..., description="Session ID"),
    service: IdeationService = Depends(get_ideation_service),
) -> SaveDraftResponse:
    """Save ideation session draft.

    Persists the current session state for later resumption.

    Args:
        request: Draft data to save.
        session_id: Session identifier.
        service: Ideation service instance.

    Returns:
        SaveDraftResponse: Confirmation of save.

    Raises:
        HTTPException: 500 on service error.
    """
    try:
        return await service.save_draft(session_id, request)
    except NotImplementedError:
        # Return mock response for development
        return SaveDraftResponse(
            success=True,
            sessionId=session_id,
            savedAt=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        logger.error(f"Save draft failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save draft: {str(e)}",
        ) from e


# =============================================================================
# Mock Responses for Development
# =============================================================================


def _mock_maturity_state() -> MaturityState:
    """Create mock maturity state for development."""
    return MaturityState(
        score=45.0,
        level="defined",
        categories=[
            CategoryMaturity(
                id="problem",
                name="Problem Statement",
                score=80.0,
                requiredForSubmit=True,
            ),
            CategoryMaturity(
                id="users",
                name="Target Users",
                score=60.0,
                requiredForSubmit=True,
            ),
            CategoryMaturity(
                id="functional",
                name="Functional Requirements",
                score=30.0,
                requiredForSubmit=True,
            ),
            CategoryMaturity(
                id="nfr",
                name="Non-Functional Requirements",
                score=20.0,
                requiredForSubmit=True,
            ),
            CategoryMaturity(
                id="scope",
                name="Scope & Constraints",
                score=50.0,
                requiredForSubmit=True,
            ),
            CategoryMaturity(
                id="success",
                name="Success Criteria",
                score=40.0,
                requiredForSubmit=True,
            ),
            CategoryMaturity(
                id="risks",
                name="Risks & Assumptions",
                score=25.0,
                requiredForSubmit=True,
            ),
        ],
        canSubmit=False,
        gaps=["Functional Requirements", "Non-Functional Requirements", "Risks & Assumptions"],
    )


def _mock_chat_response(request: IdeationChatRequest) -> IdeationChatResponse:
    """Create mock chat response for development."""
    now = datetime.now(timezone.utc).isoformat()

    return IdeationChatResponse(
        message=IdeationMessage(
            id=f"msg-{now}",
            role="assistant",
            content="Thank you for sharing that. Let me ask some follow-up questions to better understand your requirements.",
            timestamp=now,
            maturityDelta=5.0,
            extractedRequirements=[],
            suggestedFollowups=[
                "What are the main user roles in this system?",
                "What are the most critical features?",
            ],
        ),
        maturityUpdate=_mock_maturity_state(),
        extractedRequirements=[],
        suggestedFollowups=[
            "What are the main user roles in this system?",
            "What are the most critical features?",
        ],
    )


def _mock_submit_response(request: SubmitPRDRequest) -> SubmitPRDResponse:
    """Create mock submit response for development."""
    now = datetime.now(timezone.utc).isoformat()

    return SubmitPRDResponse(
        gateId=f"gate-{request.sessionId}",
        prdDraft=PRDDocument(
            id=f"prd-{request.sessionId}",
            title="Generated PRD",
            version="1.0.0",
            sections=[
                PRDSection(
                    id="sec-001",
                    heading="Overview",
                    content="This PRD outlines the requirements for the system.",
                    order=1,
                ),
                PRDSection(
                    id="sec-002",
                    heading="Functional Requirements",
                    content="The system shall provide the following functionality...",
                    order=2,
                ),
            ],
            createdAt=now,
            status="pending_review",
        ),
        userStories=[
            UserStory(
                id="US-001",
                title="Sample User Story",
                asA="user",
                iWant="to perform an action",
                soThat="I can achieve a goal",
                acceptanceCriteria=["Criterion 1", "Criterion 2"],
                linkedRequirements=["REQ-001"],
                priority="must_have",
            ),
        ],
        status="pending_review",
    )

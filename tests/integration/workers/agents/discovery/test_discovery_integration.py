"""Integration tests for Discovery agents.

Tests the full PRD → Acceptance workflow with mocked LLM responses
and real file operations.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.workers.agents.protocols import AgentContext
from src.workers.agents.discovery.config import DiscoveryConfig
from src.workers.agents.discovery.coordinator import (
    DiscoveryCoordinator,
    ProjectContext,
)
from src.workers.agents.discovery.prd_agent import PRDAgent
from src.workers.agents.discovery.acceptance_agent import AcceptanceAgent
from src.workers.artifacts.writer import ArtifactWriter
from src.workers.llm.client import LLMResponse


@pytest.fixture
def workspace_path(tmp_path):
    """Create a temporary workspace."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace


@pytest.fixture
def artifact_writer(workspace_path):
    """Create a real artifact writer."""
    return ArtifactWriter(str(workspace_path))


@pytest.fixture
def config():
    """Create test configuration."""
    return DiscoveryConfig(max_retries=2, retry_delay_seconds=0.1)


@pytest.fixture
def agent_context(workspace_path):
    """Create test agent context."""
    return AgentContext(
        session_id="integration-session",
        task_id="integration-task",
        tenant_id="default",
        workspace_path=str(workspace_path),
    )


@pytest.fixture
def project_context():
    """Create test project context."""
    return ProjectContext(
        name="Integration Test Project",
        description="A project for integration testing",
        git_sha="abc123def",
    )


@pytest.fixture
def mock_llm_client_for_prd():
    """Create mock LLM client with PRD generation responses."""
    client = MagicMock()

    # Extraction response
    extraction_response = {
        "requirements": [
            {
                "id": "REQ-001",
                "description": "Users shall be able to register with email and password",
                "priority": "must_have",
                "type": "functional",
                "rationale": "Core user onboarding functionality",
                "source": "User input",
            },
            {
                "id": "REQ-002",
                "description": "Users shall be able to login with credentials",
                "priority": "must_have",
                "type": "functional",
                "rationale": "Core authentication functionality",
                "source": "User input",
            },
            {
                "id": "REQ-003",
                "description": "Passwords shall be stored securely using bcrypt",
                "priority": "must_have",
                "type": "non_functional",
                "rationale": "Security requirement",
                "source": "Implied security best practice",
            },
        ],
        "ambiguous_areas": [],
        "suggested_questions": [],
    }

    # PRD generation response
    prd_response = {
        "title": "User Authentication System PRD",
        "version": "1.0.0",
        "executive_summary": "This document describes the requirements for a user authentication system that enables secure user registration and login.",
        "objectives": {
            "title": "Objectives",
            "content": "Provide secure user authentication for the application.",
            "requirements": [],
            "subsections": [],
        },
        "scope": {
            "title": "Scope",
            "content": "In scope: Registration, Login, Password security. Out of scope: OAuth, MFA.",
            "requirements": [],
            "subsections": [],
        },
        "sections": [
            {
                "title": "Functional Requirements",
                "content": "Core functional requirements for authentication.",
                "requirements": [
                    {
                        "id": "REQ-001",
                        "description": "Users shall be able to register with email and password",
                        "priority": "must_have",
                        "type": "functional",
                        "rationale": "Core user onboarding functionality",
                        "source": "User input",
                    },
                    {
                        "id": "REQ-002",
                        "description": "Users shall be able to login with credentials",
                        "priority": "must_have",
                        "type": "functional",
                        "rationale": "Core authentication functionality",
                        "source": "User input",
                    },
                ],
                "subsections": [],
            },
            {
                "title": "Non-Functional Requirements",
                "content": "Security and performance requirements.",
                "requirements": [
                    {
                        "id": "REQ-003",
                        "description": "Passwords shall be stored securely using bcrypt",
                        "priority": "must_have",
                        "type": "non_functional",
                        "rationale": "Security requirement",
                        "source": "Implied security best practice",
                    },
                ],
                "subsections": [],
            },
        ],
    }

    client.generate = AsyncMock(
        side_effect=[
            LLMResponse(content=json.dumps(extraction_response), model="test"),
            LLMResponse(content=json.dumps(prd_response), model="test"),
        ]
    )
    client.model_name = "test-model"

    return client


@pytest.fixture
def mock_llm_client_for_acceptance():
    """Create mock LLM client with acceptance criteria responses."""
    client = MagicMock()

    criteria_response = {
        "criteria": [
            {
                "id": "AC-001",
                "requirement_ids": ["REQ-001"],
                "given": "a new user with a valid email address",
                "when": "the user submits the registration form with email and password",
                "then": "a new user account is created and a confirmation email is sent",
                "notes": "Password must meet minimum strength requirements",
            },
            {
                "id": "AC-002",
                "requirement_ids": ["REQ-001"],
                "given": "a user trying to register with an existing email",
                "when": "the user submits the registration form",
                "then": "an error message is displayed indicating the email is already registered",
                "notes": "Do not reveal whether email exists in system for security",
            },
            {
                "id": "AC-003",
                "requirement_ids": ["REQ-002"],
                "given": "a registered user with valid credentials",
                "when": "the user logs in with correct email and password",
                "then": "the user is authenticated and redirected to the dashboard",
                "notes": "",
            },
            {
                "id": "AC-004",
                "requirement_ids": ["REQ-002"],
                "given": "a registered user with invalid password",
                "when": "the user attempts to login",
                "then": "an error message 'Invalid credentials' is displayed",
                "notes": "Generic message to prevent user enumeration",
            },
            {
                "id": "AC-005",
                "requirement_ids": ["REQ-003"],
                "given": "a new user registration",
                "when": "the password is stored in the database",
                "then": "the password is hashed using bcrypt with a cost factor of at least 10",
                "notes": "",
            },
        ]
    }

    client.generate = AsyncMock(
        return_value=LLMResponse(content=json.dumps(criteria_response), model="test")
    )
    client.model_name = "test-model"

    return client


class TestPRDAgentIntegration:
    """Integration tests for PRD Agent."""

    @pytest.mark.asyncio
    async def test_prd_agent_generates_valid_prd_document(
        self,
        mock_llm_client_for_prd,
        artifact_writer,
        agent_context,
        config,
    ) -> None:
        """Test that PRD agent generates a valid PRD document."""
        agent = PRDAgent(
            llm_client=mock_llm_client_for_prd,
            artifact_writer=artifact_writer,
            config=config,
        )

        result = await agent.execute(
            agent_context,
            {
                "raw_requirements": "Build a user authentication system with registration and login",
                "project_title": "Auth System",
            },
        )

        assert result.success is True
        assert len(result.artifact_paths) >= 1

        # Verify artifact file exists and is valid JSON
        artifact_path = Path(result.artifact_paths[0])
        assert artifact_path.exists()

        content = artifact_path.read_text()
        data = json.loads(content)

        assert data["title"] == "User Authentication System PRD"
        assert len(data["sections"]) >= 2

    @pytest.mark.asyncio
    async def test_prd_agent_writes_markdown_artifact(
        self,
        mock_llm_client_for_prd,
        artifact_writer,
        agent_context,
        config,
    ) -> None:
        """Test that PRD agent writes markdown artifact alongside JSON."""
        agent = PRDAgent(
            llm_client=mock_llm_client_for_prd,
            artifact_writer=artifact_writer,
            config=config,
        )

        result = await agent.execute(
            agent_context,
            {"raw_requirements": "Build auth system"},
        )

        assert result.success is True

        # Find markdown file
        artifact_dir = Path(artifact_writer.get_artifact_directory(agent_context.session_id))
        md_files = list(artifact_dir.glob("*.md"))

        assert len(md_files) >= 1

        md_content = md_files[0].read_text()
        assert "# User Authentication System PRD" in md_content


class TestAcceptanceAgentIntegration:
    """Integration tests for Acceptance Agent."""

    @pytest.mark.asyncio
    async def test_acceptance_agent_generates_valid_criteria(
        self,
        mock_llm_client_for_acceptance,
        artifact_writer,
        agent_context,
        config,
    ) -> None:
        """Test that Acceptance agent generates valid criteria."""
        from src.workers.agents.discovery.models import (
            PRDDocument,
            PRDSection,
            Requirement,
        )

        # Create a PRD document
        prd = PRDDocument.create(
            title="Test PRD",
            executive_summary="Test summary",
            objectives=PRDSection(title="Objectives", content="Test"),
            scope=PRDSection(title="Scope", content="Test"),
            sections=[
                PRDSection(
                    title="Requirements",
                    content="Test",
                    requirements=[
                        Requirement(id="REQ-001", description="Registration"),
                        Requirement(id="REQ-002", description="Login"),
                        Requirement(id="REQ-003", description="Security"),
                    ],
                )
            ],
        )

        agent = AcceptanceAgent(
            llm_client=mock_llm_client_for_acceptance,
            artifact_writer=artifact_writer,
            config=config,
        )

        result = await agent.execute(
            agent_context,
            {"prd_document": prd},
        )

        assert result.success is True
        assert len(result.artifact_paths) >= 1

        # Verify artifact content
        artifact_path = Path(result.artifact_paths[0])
        content = artifact_path.read_text()
        data = json.loads(content)

        assert len(data["criteria"]) == 5
        assert data["criteria"][0]["id"] == "AC-001"

    @pytest.mark.asyncio
    async def test_acceptance_agent_calculates_coverage(
        self,
        mock_llm_client_for_acceptance,
        artifact_writer,
        agent_context,
        config,
    ) -> None:
        """Test that Acceptance agent calculates coverage correctly."""
        from src.workers.agents.discovery.models import (
            PRDDocument,
            PRDSection,
            Requirement,
        )

        prd = PRDDocument.create(
            title="Test PRD",
            executive_summary="Test",
            objectives=PRDSection(title="Objectives", content=""),
            scope=PRDSection(title="Scope", content=""),
            sections=[
                PRDSection(
                    title="Requirements",
                    content="",
                    requirements=[
                        Requirement(id="REQ-001", description="Req 1"),
                        Requirement(id="REQ-002", description="Req 2"),
                        Requirement(id="REQ-003", description="Req 3"),
                    ],
                )
            ],
        )

        agent = AcceptanceAgent(
            llm_client=mock_llm_client_for_acceptance,
            artifact_writer=artifact_writer,
            config=config,
        )

        result = await agent.execute(
            agent_context,
            {"prd_document": prd},
        )

        assert result.success is True
        assert result.metadata["coverage_percentage"] == 100.0
        assert result.metadata["uncovered_requirements"] == []


class TestDiscoveryCoordinatorIntegration:
    """Integration tests for Discovery Coordinator."""

    @pytest.mark.asyncio
    async def test_coordinator_runs_full_discovery_workflow(
        self,
        artifact_writer,
        agent_context,
        project_context,
        config,
        workspace_path,
    ) -> None:
        """Test that coordinator runs full PRD → Acceptance workflow."""
        # Create mock LLM client with all responses
        mock_client = MagicMock()

        # PRD extraction response
        extraction_response = {
            "requirements": [
                {
                    "id": "REQ-001",
                    "description": "User registration",
                    "priority": "must_have",
                    "type": "functional",
                },
            ],
        }

        # PRD generation response
        prd_response = {
            "title": "Test PRD",
            "version": "1.0.0",
            "executive_summary": "Test",
            "objectives": {"title": "Obj", "content": "", "requirements": [], "subsections": []},
            "scope": {"title": "Scope", "content": "", "requirements": [], "subsections": []},
            "sections": [
                {
                    "title": "Requirements",
                    "content": "",
                    "requirements": [
                        {
                            "id": "REQ-001",
                            "description": "User registration",
                            "priority": "must_have",
                            "type": "functional",
                        },
                    ],
                    "subsections": [],
                }
            ],
        }

        # Acceptance criteria response
        criteria_response = {
            "criteria": [
                {
                    "id": "AC-001",
                    "requirement_ids": ["REQ-001"],
                    "given": "a user",
                    "when": "they register",
                    "then": "account is created",
                },
            ]
        }

        mock_client.generate = AsyncMock(
            side_effect=[
                LLMResponse(content=json.dumps(extraction_response), model="test"),
                LLMResponse(content=json.dumps(prd_response), model="test"),
                LLMResponse(content=json.dumps(criteria_response), model="test"),
            ]
        )
        mock_client.model_name = "test-model"

        coordinator = DiscoveryCoordinator(
            llm_client=mock_client,
            artifact_writer=artifact_writer,
            config=config,
        )

        result = await coordinator.run_discovery(
            user_input="Build user registration",
            project_context=project_context,
            context=agent_context,
            submit_to_hitl=False,
        )

        assert result.success is True
        assert result.prd is not None
        assert result.acceptance_criteria is not None
        assert result.prd.title == "Test PRD"
        assert len(result.acceptance_criteria.criteria) == 1

    @pytest.mark.asyncio
    async def test_coordinator_generates_artifacts(
        self,
        artifact_writer,
        agent_context,
        project_context,
        config,
        workspace_path,
    ) -> None:
        """Test that coordinator generates all expected artifacts."""
        mock_client = MagicMock()

        extraction_response = {
            "requirements": [{"id": "REQ-001", "description": "Test"}],
        }
        prd_response = {
            "title": "Test",
            "version": "1.0.0",
            "executive_summary": "",
            "objectives": {"title": "Obj", "content": "", "requirements": [], "subsections": []},
            "scope": {"title": "Scope", "content": "", "requirements": [], "subsections": []},
            "sections": [
                {
                    "title": "Requirements",
                    "content": "",
                    "requirements": [
                        {"id": "REQ-001", "description": "Test", "priority": "must_have", "type": "functional"},
                    ],
                    "subsections": [],
                }
            ],
        }
        criteria_response = {
            "criteria": [
                {"id": "AC-001", "requirement_ids": ["REQ-001"], "given": "G", "when": "W", "then": "T"},
            ]
        }

        mock_client.generate = AsyncMock(
            side_effect=[
                LLMResponse(content=json.dumps(extraction_response), model="test"),
                LLMResponse(content=json.dumps(prd_response), model="test"),
                LLMResponse(content=json.dumps(criteria_response), model="test"),
            ]
        )
        mock_client.model_name = "test-model"

        coordinator = DiscoveryCoordinator(
            llm_client=mock_client,
            artifact_writer=artifact_writer,
            config=config,
        )

        result = await coordinator.run_discovery(
            user_input="Test",
            project_context=project_context,
            context=agent_context,
            submit_to_hitl=False,
        )

        assert result.success is True

        # Check artifacts exist
        artifact_dir = Path(artifact_writer.get_artifact_directory(agent_context.session_id))
        files = list(artifact_dir.iterdir())

        # Should have PRD (json + md) and acceptance criteria (json + md)
        assert len(files) >= 4

        json_files = [f for f in files if f.suffix == ".json"]
        md_files = [f for f in files if f.suffix == ".md"]

        assert len(json_files) >= 2
        assert len(md_files) >= 2

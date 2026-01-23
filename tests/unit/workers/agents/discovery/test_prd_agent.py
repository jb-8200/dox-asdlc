"""Unit tests for PRDAgent."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.workers.agents.protocols import AgentContext, AgentResult
from src.workers.agents.discovery.config import DiscoveryConfig
from src.workers.agents.discovery.prd_agent import PRDAgent
from src.workers.llm.client import LLMResponse


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    client = MagicMock()
    client.generate = AsyncMock()
    client.model_name = "test-model"
    return client


@pytest.fixture
def mock_artifact_writer(tmp_path):
    """Create a mock artifact writer."""
    writer = MagicMock()
    writer.workspace_path = str(tmp_path)

    async def write_artifact(**kwargs):
        path = tmp_path / kwargs.get("filename", "artifact.json")
        path.write_text(kwargs.get("content", "{}"))
        return str(path)

    writer.write_artifact = AsyncMock(side_effect=write_artifact)
    return writer


@pytest.fixture
def agent_context():
    """Create a test agent context."""
    return AgentContext(
        session_id="test-session",
        task_id="test-task",
        tenant_id="default",
        workspace_path="/tmp/workspace",
    )


@pytest.fixture
def config():
    """Create test configuration."""
    return DiscoveryConfig(max_retries=1, retry_delay_seconds=0)


class TestPRDAgent:
    """Tests for PRDAgent."""

    def test_agent_type_returns_correct_value(
        self,
        mock_llm_client,
        mock_artifact_writer,
        config,
    ) -> None:
        """Test that agent_type returns 'prd_agent'."""
        agent = PRDAgent(
            llm_client=mock_llm_client,
            artifact_writer=mock_artifact_writer,
            config=config,
        )

        assert agent.agent_type == "prd_agent"

    @pytest.mark.asyncio
    async def test_execute_returns_error_when_no_requirements(
        self,
        mock_llm_client,
        mock_artifact_writer,
        agent_context,
        config,
    ) -> None:
        """Test that execute returns error when no raw_requirements provided."""
        agent = PRDAgent(
            llm_client=mock_llm_client,
            artifact_writer=mock_artifact_writer,
            config=config,
        )

        result = await agent.execute(agent_context, {})

        assert result.success is False
        assert "No raw_requirements provided" in result.error_message
        assert result.should_retry is False

    @pytest.mark.asyncio
    async def test_execute_extracts_requirements_and_generates_prd(
        self,
        mock_llm_client,
        mock_artifact_writer,
        agent_context,
        config,
    ) -> None:
        """Test that execute extracts requirements and generates PRD."""
        # Mock requirements extraction response
        extraction_response = {
            "requirements": [
                {
                    "id": "REQ-001",
                    "description": "User can login",
                    "priority": "must_have",
                    "type": "functional",
                    "rationale": "Core feature",
                    "source": "User input",
                }
            ],
            "ambiguous_areas": [],
            "suggested_questions": [],
        }

        # Mock PRD generation response
        prd_response = {
            "title": "Test PRD",
            "version": "1.0.0",
            "executive_summary": "Test summary",
            "objectives": {"title": "Objectives", "content": "Test", "requirements": []},
            "scope": {"title": "Scope", "content": "Test", "requirements": []},
            "sections": [
                {
                    "title": "Functional Requirements",
                    "content": "Test",
                    "requirements": [
                        {
                            "id": "REQ-001",
                            "description": "User can login",
                            "priority": "must_have",
                            "type": "functional",
                        }
                    ],
                    "subsections": [],
                }
            ],
        }

        mock_llm_client.generate.side_effect = [
            LLMResponse(
                content=json.dumps(extraction_response),
                model="test-model",
            ),
            LLMResponse(
                content=json.dumps(prd_response),
                model="test-model",
            ),
        ]

        agent = PRDAgent(
            llm_client=mock_llm_client,
            artifact_writer=mock_artifact_writer,
            config=config,
        )

        result = await agent.execute(
            agent_context,
            {"raw_requirements": "Build a login system"},
        )

        assert result.success is True
        assert result.agent_type == "prd_agent"
        assert len(result.artifact_paths) == 1
        assert result.metadata["requirement_count"] == 1

    @pytest.mark.asyncio
    async def test_execute_handles_extraction_failure(
        self,
        mock_llm_client,
        mock_artifact_writer,
        agent_context,
        config,
    ) -> None:
        """Test that execute handles extraction failure gracefully."""
        # Mock invalid response
        mock_llm_client.generate.return_value = LLMResponse(
            content="Invalid JSON",
            model="test-model",
        )

        agent = PRDAgent(
            llm_client=mock_llm_client,
            artifact_writer=mock_artifact_writer,
            config=config,
        )

        result = await agent.execute(
            agent_context,
            {"raw_requirements": "Build something"},
        )

        assert result.success is False
        assert result.should_retry is True

    @pytest.mark.asyncio
    async def test_execute_parses_json_from_code_blocks(
        self,
        mock_llm_client,
        mock_artifact_writer,
        agent_context,
        config,
    ) -> None:
        """Test that execute parses JSON from markdown code blocks."""
        extraction_response = {
            "requirements": [
                {
                    "id": "REQ-001",
                    "description": "Test",
                    "priority": "should_have",
                    "type": "functional",
                }
            ],
        }

        prd_response = {
            "title": "Test",
            "version": "1.0.0",
            "executive_summary": "Test",
            "objectives": {"title": "Obj", "content": "", "requirements": []},
            "scope": {"title": "Scope", "content": "", "requirements": []},
            "sections": [],
        }

        # Wrap in code blocks
        mock_llm_client.generate.side_effect = [
            LLMResponse(
                content=f"```json\n{json.dumps(extraction_response)}\n```",
                model="test-model",
            ),
            LLMResponse(
                content=f"Here is the PRD:\n```json\n{json.dumps(prd_response)}\n```",
                model="test-model",
            ),
        ]

        agent = PRDAgent(
            llm_client=mock_llm_client,
            artifact_writer=mock_artifact_writer,
            config=config,
        )

        result = await agent.execute(
            agent_context,
            {"raw_requirements": "Build something"},
        )

        assert result.success is True


class TestPRDAgentValidation:
    """Tests for PRDAgent validation methods."""

    def test_validate_context_returns_true_for_valid_context(
        self,
        mock_llm_client,
        mock_artifact_writer,
        agent_context,
        config,
    ) -> None:
        """Test that validate_context returns True for valid context."""
        agent = PRDAgent(
            llm_client=mock_llm_client,
            artifact_writer=mock_artifact_writer,
            config=config,
        )

        assert agent.validate_context(agent_context) is True

    def test_validate_context_returns_false_for_missing_session_id(
        self,
        mock_llm_client,
        mock_artifact_writer,
        config,
    ) -> None:
        """Test that validate_context returns False for missing session_id."""
        context = AgentContext(
            session_id="",
            task_id="test-task",
            tenant_id="default",
            workspace_path="/tmp",
        )

        agent = PRDAgent(
            llm_client=mock_llm_client,
            artifact_writer=mock_artifact_writer,
            config=config,
        )

        assert agent.validate_context(context) is False

    def test_validate_context_returns_false_for_missing_workspace(
        self,
        mock_llm_client,
        mock_artifact_writer,
        config,
    ) -> None:
        """Test that validate_context returns False for missing workspace."""
        context = AgentContext(
            session_id="test-session",
            task_id="test-task",
            tenant_id="default",
            workspace_path="",
        )

        agent = PRDAgent(
            llm_client=mock_llm_client,
            artifact_writer=mock_artifact_writer,
            config=config,
        )

        assert agent.validate_context(context) is False


class TestPRDAgentJSONParsing:
    """Tests for PRDAgent JSON parsing."""

    def test_parse_json_from_response_handles_direct_json(
        self,
        mock_llm_client,
        mock_artifact_writer,
        config,
    ) -> None:
        """Test that JSON is parsed from direct JSON content."""
        agent = PRDAgent(
            llm_client=mock_llm_client,
            artifact_writer=mock_artifact_writer,
            config=config,
        )

        result = agent._parse_json_from_response('{"key": "value"}')

        assert result == {"key": "value"}

    def test_parse_json_from_response_handles_json_code_block(
        self,
        mock_llm_client,
        mock_artifact_writer,
        config,
    ) -> None:
        """Test that JSON is parsed from code blocks."""
        agent = PRDAgent(
            llm_client=mock_llm_client,
            artifact_writer=mock_artifact_writer,
            config=config,
        )

        content = '```json\n{"key": "value"}\n```'
        result = agent._parse_json_from_response(content)

        assert result == {"key": "value"}

    def test_parse_json_from_response_handles_plain_code_block(
        self,
        mock_llm_client,
        mock_artifact_writer,
        config,
    ) -> None:
        """Test that JSON is parsed from plain code blocks."""
        agent = PRDAgent(
            llm_client=mock_llm_client,
            artifact_writer=mock_artifact_writer,
            config=config,
        )

        content = '```\n{"key": "value"}\n```'
        result = agent._parse_json_from_response(content)

        assert result == {"key": "value"}

    def test_parse_json_from_response_handles_embedded_json(
        self,
        mock_llm_client,
        mock_artifact_writer,
        config,
    ) -> None:
        """Test that JSON is found in mixed content."""
        agent = PRDAgent(
            llm_client=mock_llm_client,
            artifact_writer=mock_artifact_writer,
            config=config,
        )

        content = 'Here is the result: {"key": "value"} - that is all'
        result = agent._parse_json_from_response(content)

        assert result == {"key": "value"}

    def test_parse_json_from_response_returns_none_for_invalid_json(
        self,
        mock_llm_client,
        mock_artifact_writer,
        config,
    ) -> None:
        """Test that None is returned for invalid JSON."""
        agent = PRDAgent(
            llm_client=mock_llm_client,
            artifact_writer=mock_artifact_writer,
            config=config,
        )

        result = agent._parse_json_from_response("not valid json at all")

        assert result is None

"""Unit tests for Architect Service.

Tests the ArchitectService class for translating SVG diagrams
to various export formats using LLM.
"""

from __future__ import annotations

import base64
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.orchestrator.api.models.architect import (
    ExportFormat,
    TranslateErrorCode,
    TranslateResponse,
)
from src.orchestrator.services.architect_service import (
    ArchitectService,
    ArchitectServiceError,
    get_architect_service,
    MERMAID_PROMPT,
    DRAWIO_PROMPT,
)


class TestArchitectServiceInit:
    """Tests for ArchitectService initialization."""

    def test_init_with_defaults(self) -> None:
        """Test service can be instantiated with defaults."""
        service = ArchitectService()
        assert service is not None

    def test_init_with_custom_dependencies(self) -> None:
        """Test service can be instantiated with custom dependencies."""
        mock_llm_factory = AsyncMock()
        mock_config_service = AsyncMock()

        service = ArchitectService(
            llm_factory=mock_llm_factory,
            config_service=mock_config_service,
        )

        assert service._llm_factory is mock_llm_factory
        assert service._config_service is mock_config_service


class TestTranslateToMermaid:
    """Tests for translate method with Mermaid format."""

    @pytest.fixture
    def service(self) -> ArchitectService:
        """Create a service instance with mocked dependencies."""
        mock_llm_factory = AsyncMock()
        mock_config_service = AsyncMock()

        return ArchitectService(
            llm_factory=mock_llm_factory,
            config_service=mock_config_service,
        )

    @pytest.mark.asyncio
    async def test_translate_to_mermaid_success(
        self,
        service: ArchitectService,
    ) -> None:
        """Test successful Mermaid translation."""
        # Setup mocks
        mock_llm_client = AsyncMock()
        mock_llm_client.model = "claude-sonnet-4"
        mock_response = MagicMock()
        mock_response.content = """flowchart TD
    A[Start] --> B[Process]
    B --> C[End]"""
        mock_llm_client.generate.return_value = mock_response
        service._llm_factory.get_client.return_value = mock_llm_client

        svg_content = "<svg><rect/><text>Start</text></svg>"
        result = await service.translate(
            svg_content=svg_content,
            format=ExportFormat.MERMAID,
        )

        assert result.format == ExportFormat.MERMAID
        assert "flowchart" in result.content
        assert result.model_used == "claude-sonnet-4"

    @pytest.mark.asyncio
    async def test_translate_to_mermaid_with_diagram_type_option(
        self,
        service: ArchitectService,
    ) -> None:
        """Test Mermaid translation with diagram type hint."""
        mock_llm_client = AsyncMock()
        mock_llm_client.model = "claude-sonnet-4"
        mock_response = MagicMock()
        mock_response.content = """sequenceDiagram
    Alice->>Bob: Hello
    Bob->>Alice: Hi"""
        mock_llm_client.generate.return_value = mock_response
        service._llm_factory.get_client.return_value = mock_llm_client

        svg_content = "<svg><rect/><text>Alice</text><text>Bob</text></svg>"
        result = await service.translate(
            svg_content=svg_content,
            format=ExportFormat.MERMAID,
            options={"diagram_type": "sequence"},
        )

        assert result.format == ExportFormat.MERMAID
        assert "sequenceDiagram" in result.content

    @pytest.mark.asyncio
    async def test_translate_extracts_mermaid_from_code_block(
        self,
        service: ArchitectService,
    ) -> None:
        """Test that Mermaid code is extracted from markdown code blocks."""
        mock_llm_client = AsyncMock()
        mock_llm_client.model = "claude-sonnet-4"
        mock_response = MagicMock()
        mock_response.content = """```mermaid
flowchart LR
    A --> B
```"""
        mock_llm_client.generate.return_value = mock_response
        service._llm_factory.get_client.return_value = mock_llm_client

        result = await service.translate(
            svg_content="<svg></svg>",
            format=ExportFormat.MERMAID,
        )

        # Should extract just the Mermaid code
        assert result.content.startswith("flowchart")
        assert "```" not in result.content


class TestTranslateToDrawio:
    """Tests for translate method with Draw.io format."""

    @pytest.fixture
    def service(self) -> ArchitectService:
        """Create a service instance with mocked dependencies."""
        mock_llm_factory = AsyncMock()
        mock_config_service = AsyncMock()

        return ArchitectService(
            llm_factory=mock_llm_factory,
            config_service=mock_config_service,
        )

    @pytest.mark.asyncio
    async def test_translate_to_drawio_success(
        self,
        service: ArchitectService,
    ) -> None:
        """Test successful Draw.io translation."""
        mock_llm_client = AsyncMock()
        mock_llm_client.model = "claude-sonnet-4"
        mock_response = MagicMock()
        mock_response.content = """<mxGraphModel>
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
  </root>
</mxGraphModel>"""
        mock_llm_client.generate.return_value = mock_response
        service._llm_factory.get_client.return_value = mock_llm_client

        svg_content = "<svg><rect/></svg>"
        result = await service.translate(
            svg_content=svg_content,
            format=ExportFormat.DRAWIO,
        )

        assert result.format == ExportFormat.DRAWIO
        assert "mxGraphModel" in result.content
        assert result.model_used == "claude-sonnet-4"

    @pytest.mark.asyncio
    async def test_translate_extracts_xml_from_code_block(
        self,
        service: ArchitectService,
    ) -> None:
        """Test that Draw.io XML is extracted from markdown code blocks."""
        mock_llm_client = AsyncMock()
        mock_llm_client.model = "claude-sonnet-4"
        mock_response = MagicMock()
        mock_response.content = """```xml
<mxGraphModel><root></root></mxGraphModel>
```"""
        mock_llm_client.generate.return_value = mock_response
        service._llm_factory.get_client.return_value = mock_llm_client

        result = await service.translate(
            svg_content="<svg></svg>",
            format=ExportFormat.DRAWIO,
        )

        # Should extract just the XML
        assert result.content.startswith("<mxGraphModel")
        assert "```" not in result.content


class TestTranslateToPng:
    """Tests for translate method with PNG format."""

    @pytest.fixture
    def service(self) -> ArchitectService:
        """Create a service instance with mocked dependencies."""
        mock_llm_factory = AsyncMock()
        mock_config_service = AsyncMock()

        return ArchitectService(
            llm_factory=mock_llm_factory,
            config_service=mock_config_service,
        )

    @pytest.mark.asyncio
    async def test_translate_to_png_not_implemented(
        self,
        service: ArchitectService,
    ) -> None:
        """Test that PNG translation raises not implemented error for now."""
        # PNG translation requires Gemini image generation which is Phase 2
        # For now, it should raise an appropriate error
        mock_llm_client = AsyncMock()
        mock_llm_client.model = "claude-sonnet-4"
        service._llm_factory.get_client.return_value = mock_llm_client

        with pytest.raises(ArchitectServiceError) as exc_info:
            await service.translate(
                svg_content="<svg></svg>",
                format=ExportFormat.PNG,
            )

        assert exc_info.value.code == TranslateErrorCode.UNSUPPORTED_FORMAT


class TestErrorHandling:
    """Tests for error handling in translate method."""

    @pytest.fixture
    def service(self) -> ArchitectService:
        """Create a service instance with mocked dependencies."""
        mock_llm_factory = AsyncMock()
        mock_config_service = AsyncMock()

        return ArchitectService(
            llm_factory=mock_llm_factory,
            config_service=mock_config_service,
        )

    @pytest.mark.asyncio
    async def test_llm_error_raises_service_error(
        self,
        service: ArchitectService,
    ) -> None:
        """Test that LLM errors are wrapped in ArchitectServiceError."""
        service._llm_factory.get_client.side_effect = Exception("LLM unavailable")

        with pytest.raises(ArchitectServiceError) as exc_info:
            await service.translate(
                svg_content="<svg></svg>",
                format=ExportFormat.MERMAID,
            )

        assert exc_info.value.code == TranslateErrorCode.MODEL_ERROR

    @pytest.mark.asyncio
    async def test_agent_not_configured_error(
        self,
        service: ArchitectService,
    ) -> None:
        """Test error when Design agent is not configured."""
        from src.infrastructure.llm.factory import LLMClientError

        service._llm_factory.get_client.side_effect = LLMClientError(
            "No API key configured for agent design"
        )

        with pytest.raises(ArchitectServiceError) as exc_info:
            await service.translate(
                svg_content="<svg></svg>",
                format=ExportFormat.MERMAID,
            )

        assert exc_info.value.code == TranslateErrorCode.AGENT_NOT_CONFIGURED

    @pytest.mark.asyncio
    async def test_rate_limit_error(
        self,
        service: ArchitectService,
    ) -> None:
        """Test error handling for rate limit errors."""
        mock_llm_client = AsyncMock()
        mock_llm_client.generate.side_effect = Exception("Rate limit exceeded (429)")
        service._llm_factory.get_client.return_value = mock_llm_client

        with pytest.raises(ArchitectServiceError) as exc_info:
            await service.translate(
                svg_content="<svg></svg>",
                format=ExportFormat.MERMAID,
            )

        assert exc_info.value.code == TranslateErrorCode.RATE_LIMIT


class TestUsesDesignAgentConfig:
    """Tests that the service uses the Design agent configuration."""

    @pytest.fixture
    def service(self) -> ArchitectService:
        """Create a service instance with mocked dependencies."""
        mock_llm_factory = AsyncMock()
        mock_config_service = AsyncMock()

        return ArchitectService(
            llm_factory=mock_llm_factory,
            config_service=mock_config_service,
        )

    @pytest.mark.asyncio
    async def test_uses_design_agent_role(
        self,
        service: ArchitectService,
    ) -> None:
        """Test that DESIGN agent role is used for translation."""
        from src.orchestrator.api.models.llm_config import AgentRole

        mock_llm_client = AsyncMock()
        mock_llm_client.model = "claude-sonnet-4"
        mock_response = MagicMock()
        mock_response.content = "flowchart TD\n    A-->B"
        mock_llm_client.generate.return_value = mock_response
        service._llm_factory.get_client.return_value = mock_llm_client

        await service.translate(
            svg_content="<svg></svg>",
            format=ExportFormat.MERMAID,
        )

        service._llm_factory.get_client.assert_called_once_with(AgentRole.DESIGN)


class TestPrompts:
    """Tests for prompt templates."""

    def test_mermaid_prompt_contains_instructions(self) -> None:
        """Test that Mermaid prompt contains proper instructions."""
        assert "Mermaid" in MERMAID_PROMPT
        assert "SVG" in MERMAID_PROMPT
        assert "ONLY" in MERMAID_PROMPT  # Should output only code

    def test_drawio_prompt_contains_instructions(self) -> None:
        """Test that Draw.io prompt contains proper instructions."""
        assert "Draw.io" in DRAWIO_PROMPT or "mxGraph" in DRAWIO_PROMPT
        assert "XML" in DRAWIO_PROMPT
        assert "ONLY" in DRAWIO_PROMPT  # Should output only code


class TestGetArchitectService:
    """Tests for get_architect_service function."""

    def test_returns_service_instance(self) -> None:
        """Test that function returns a service instance."""
        # Reset the global instance first
        import src.orchestrator.services.architect_service as module

        module._architect_service = None

        service = get_architect_service()
        assert isinstance(service, ArchitectService)

    def test_returns_same_instance(self) -> None:
        """Test that function returns the same singleton instance."""
        # Reset the global instance first
        import src.orchestrator.services.architect_service as module

        module._architect_service = None

        service1 = get_architect_service()
        service2 = get_architect_service()

        assert service1 is service2

"""Architect Service for diagram translation.

This module provides the core translation logic for converting SVG diagrams
from the Architect Board to various export formats (PNG, Mermaid, Draw.io)
using LLM.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

from src.core.exceptions import ASDLCError
from src.orchestrator.api.models.architect import (
    ExportFormat,
    TranslateErrorCode,
    TranslateResponse,
)
from src.orchestrator.api.models.llm_config import AgentRole

if TYPE_CHECKING:
    from src.infrastructure.llm.factory import LLMClientFactory
    from src.orchestrator.services.llm_config_service import LLMConfigService


logger = logging.getLogger(__name__)


# Prompt templates for translation
MERMAID_PROMPT = """Analyze this SVG diagram and convert it to Mermaid syntax.

SVG Content:
{svg_content}

{diagram_type_hint}

Instructions:
- Identify the diagram type (flowchart, sequence, class, state, etc.)
- Extract all shapes, connections, and text labels
- Convert to valid Mermaid syntax
- Preserve the structure and relationships from the original diagram
- Output ONLY the Mermaid code, no explanations or markdown code blocks

Output the Mermaid code:"""

DRAWIO_PROMPT = """Analyze this SVG diagram and convert it to Draw.io (mxGraph) XML format.

SVG Content:
{svg_content}

Instructions:
- Extract all shapes, connections, and text labels from the SVG
- Convert to valid mxGraph XML format compatible with Draw.io
- Preserve positions and relationships from the original diagram
- Include proper mxCell elements for each shape and connection
- Output ONLY the XML code, no explanations or markdown code blocks

Output the Draw.io XML:"""


class ArchitectServiceError(ASDLCError):
    """Error raised by ArchitectService operations.

    Attributes:
        message: Human-readable error message.
        code: Machine-readable error code.
        details: Optional additional error details.
    """

    def __init__(
        self,
        message: str,
        code: TranslateErrorCode,
        details: str | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Human-readable error message.
            code: Machine-readable error code.
            details: Optional additional error details.
        """
        super().__init__(message)
        self.code = code
        self.details = details


class ArchitectService:
    """Service for translating SVG diagrams to various export formats.

    Uses the Design agent configuration from LLM Admin to perform translations.

    Usage:
        service = ArchitectService()
        result = await service.translate(
            svg_content="<svg>...</svg>",
            format=ExportFormat.MERMAID,
        )

        # With options
        result = await service.translate(
            svg_content="<svg>...</svg>",
            format=ExportFormat.MERMAID,
            options={"diagram_type": "flowchart"},
        )
    """

    def __init__(
        self,
        llm_factory: LLMClientFactory | None = None,
        config_service: LLMConfigService | None = None,
    ) -> None:
        """Initialize the architect service.

        Args:
            llm_factory: Optional LLM client factory. If not provided,
                will use the global singleton.
            config_service: Optional LLM config service. If not provided,
                will use the global singleton.
        """
        self._llm_factory = llm_factory
        self._config_service = config_service

    def _get_llm_factory(self) -> LLMClientFactory:
        """Get or create the LLM factory.

        Returns:
            LLMClientFactory: The LLM factory instance.
        """
        if self._llm_factory is None:
            from src.infrastructure.llm.factory import get_llm_client_factory

            self._llm_factory = get_llm_client_factory()
        return self._llm_factory

    def _get_config_service(self) -> LLMConfigService:
        """Get or create the config service.

        Returns:
            LLMConfigService: The config service instance.
        """
        if self._config_service is None:
            from src.orchestrator.services.llm_config_service import (
                get_llm_config_service,
            )

            self._config_service = get_llm_config_service()
        return self._config_service

    async def translate(
        self,
        svg_content: str,
        format: ExportFormat,
        options: dict[str, Any] | None = None,
    ) -> TranslateResponse:
        """Translate an SVG diagram to the specified format.

        Args:
            svg_content: Raw SVG string from Excalidraw export.
            format: Target export format.
            options: Optional format-specific options.

        Returns:
            TranslateResponse: The translation result.

        Raises:
            ArchitectServiceError: If translation fails.
        """
        if format == ExportFormat.PNG:
            # PNG translation requires Gemini image generation (Phase 2)
            raise ArchitectServiceError(
                message="PNG translation is not yet implemented",
                code=TranslateErrorCode.UNSUPPORTED_FORMAT,
                details="PNG export requires Gemini image generation (Phase 2)",
            )

        if format == ExportFormat.MERMAID:
            return await self._translate_to_mermaid(svg_content, options)

        if format == ExportFormat.DRAWIO:
            return await self._translate_to_drawio(svg_content, options)

        raise ArchitectServiceError(
            message=f"Unsupported format: {format}",
            code=TranslateErrorCode.UNSUPPORTED_FORMAT,
        )

    async def _translate_to_mermaid(
        self,
        svg_content: str,
        options: dict[str, Any] | None = None,
    ) -> TranslateResponse:
        """Translate SVG to Mermaid syntax.

        Args:
            svg_content: Raw SVG string.
            options: Optional options including diagram_type hint.

        Returns:
            TranslateResponse: The Mermaid translation result.
        """
        # Build the prompt
        diagram_type_hint = ""
        if options and options.get("diagram_type"):
            diagram_type_hint = (
                f"Hint: This appears to be a {options['diagram_type']} diagram."
            )

        prompt = MERMAID_PROMPT.format(
            svg_content=svg_content,
            diagram_type_hint=diagram_type_hint,
        )

        # Get LLM response using Design agent
        content, model_used = await self._call_llm(prompt)

        # Extract Mermaid code from potential markdown blocks
        mermaid_content = self._extract_code_from_blocks(content, ["mermaid", ""])

        return TranslateResponse(
            content=mermaid_content,
            format=ExportFormat.MERMAID,
            model_used=model_used,
            metadata={"diagram_type": options.get("diagram_type") if options else None},
        )

    async def _translate_to_drawio(
        self,
        svg_content: str,
        options: dict[str, Any] | None = None,
    ) -> TranslateResponse:
        """Translate SVG to Draw.io XML format.

        Args:
            svg_content: Raw SVG string.
            options: Optional options.

        Returns:
            TranslateResponse: The Draw.io translation result.
        """
        prompt = DRAWIO_PROMPT.format(svg_content=svg_content)

        # Get LLM response using Design agent
        content, model_used = await self._call_llm(prompt)

        # Extract XML from potential markdown blocks
        xml_content = self._extract_code_from_blocks(content, ["xml", ""])

        return TranslateResponse(
            content=xml_content,
            format=ExportFormat.DRAWIO,
            model_used=model_used,
            metadata=None,
        )

    async def _call_llm(self, prompt: str) -> tuple[str, str]:
        """Call the LLM with the given prompt using Design agent config.

        Args:
            prompt: The prompt to send to the LLM.

        Returns:
            tuple[str, str]: The response content and model name.

        Raises:
            ArchitectServiceError: If the LLM call fails.
        """
        try:
            llm_factory = self._get_llm_factory()
            client = await llm_factory.get_client(AgentRole.DESIGN)

            response = await client.generate(prompt=prompt)
            return response.content, client.model

        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"LLM call failed: {e}")

            # Check for specific error types
            if "no api key" in error_msg or "not configured" in error_msg:
                raise ArchitectServiceError(
                    message="Design agent is not configured",
                    code=TranslateErrorCode.AGENT_NOT_CONFIGURED,
                    details="Configure the Design agent in LLM Admin settings",
                ) from e

            if "429" in error_msg or "rate limit" in error_msg:
                raise ArchitectServiceError(
                    message="Rate limit exceeded",
                    code=TranslateErrorCode.RATE_LIMIT,
                    details="Too many requests. Please try again later.",
                ) from e

            raise ArchitectServiceError(
                message="Failed to generate translation",
                code=TranslateErrorCode.MODEL_ERROR,
                details=str(e),
            ) from e

    def _extract_code_from_blocks(
        self,
        content: str,
        languages: list[str],
    ) -> str:
        """Extract code from markdown code blocks.

        If the content is wrapped in markdown code blocks (```lang ... ```),
        extract just the code inside. Otherwise, return the content as-is.

        Args:
            content: The content potentially containing code blocks.
            languages: List of language identifiers to look for (e.g., ["mermaid", "xml"]).

        Returns:
            str: The extracted code or original content.
        """
        content = content.strip()

        # Try to extract from code blocks for each language
        for lang in languages:
            if lang:
                pattern = rf"```{lang}\s*([\s\S]*?)\s*```"
            else:
                # Match any code block
                pattern = r"```\s*([\s\S]*?)\s*```"

            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # If no code block found, return content as-is (after removing any ``` markers)
        return content.replace("```", "").strip()


# Global service instance
_architect_service: ArchitectService | None = None


def get_architect_service() -> ArchitectService:
    """Get the singleton architect service instance.

    Returns:
        ArchitectService: The service instance.
    """
    global _architect_service
    if _architect_service is None:
        _architect_service = ArchitectService()
    return _architect_service

"""Pydantic models for Architect Board translation endpoints.

This module defines the data models for translating SVG diagrams
from the Architect Board to various export formats (PNG, Mermaid, Draw.io).
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ExportFormat(str, Enum):
    """Supported export formats for diagram translation."""

    PNG = "png"
    MERMAID = "mmd"
    DRAWIO = "drawio"


class TranslateRequest(BaseModel):
    """Request model for diagram translation.

    Attributes:
        svg_content: Raw SVG string from Excalidraw export.
        format: Target export format.
        options: Optional format-specific options.
            - For PNG: {"width": int, "height": int}
            - For Mermaid: {"diagram_type": str}  # e.g., "flowchart", "sequence"
            - For Draw.io: {"style": str}
    """

    svg_content: str = Field(
        ...,
        alias="svgContent",
        description="Raw SVG string from Excalidraw export",
        min_length=1,
    )
    format: ExportFormat = Field(
        ...,
        description="Target export format",
    )
    options: dict[str, Any] | None = Field(
        default=None,
        description="Format-specific options (size for PNG, diagramType hint for Mermaid)",
    )

    model_config = {"populate_by_name": True}


class TranslateResponse(BaseModel):
    """Response model for successful diagram translation.

    Attributes:
        content: Translated content (Base64 for PNG, raw string for Mermaid/Draw.io).
        format: The format of the translated content.
        model_used: The LLM model used for translation (for transparency).
        metadata: Optional format-specific metadata.
            - For PNG: {"width": int, "height": int, "size_bytes": int}
            - For Mermaid: {"diagram_type": str}
            - For Draw.io: {"element_count": int}
    """

    content: str = Field(
        ...,
        description="Base64 for PNG, raw string for Mermaid/Draw.io",
    )
    format: ExportFormat = Field(
        ...,
        description="The format of the translated content",
    )
    model_used: str = Field(
        ...,
        serialization_alias="modelUsed",
        description="The LLM model used for translation",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Format-specific metadata (width/height for PNG, diagramType for Mermaid)",
    )

    model_config = {"populate_by_name": True}


class TranslateErrorCode(str, Enum):
    """Error codes for translation failures."""

    MODEL_ERROR = "MODEL_ERROR"
    INVALID_FORMAT = "INVALID_FORMAT"
    SVG_PARSE_ERROR = "SVG_PARSE_ERROR"
    RATE_LIMIT = "RATE_LIMIT"
    AGENT_NOT_CONFIGURED = "AGENT_NOT_CONFIGURED"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"


class TranslateErrorResponse(BaseModel):
    """Response model for translation errors.

    Attributes:
        error: Human-readable error message.
        code: Machine-readable error code.
        details: Optional additional error details.
    """

    error: str = Field(
        ...,
        description="Human-readable error message",
    )
    code: TranslateErrorCode = Field(
        ...,
        description="Machine-readable error code",
    )
    details: str | None = Field(
        default=None,
        description="Optional additional error details",
    )

    model_config = {"populate_by_name": True}

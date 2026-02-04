"""Unit tests for Architect Board translation models.

Tests the Pydantic models for diagram translation requests and responses.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.orchestrator.api.models.architect import (
    ExportFormat,
    TranslateErrorCode,
    TranslateErrorResponse,
    TranslateRequest,
    TranslateResponse,
)


class TestExportFormat:
    """Tests for ExportFormat enum."""

    def test_png_value(self) -> None:
        """Test PNG format value."""
        assert ExportFormat.PNG.value == "png"

    def test_mermaid_value(self) -> None:
        """Test Mermaid format value."""
        assert ExportFormat.MERMAID.value == "mmd"

    def test_drawio_value(self) -> None:
        """Test Draw.io format value."""
        assert ExportFormat.DRAWIO.value == "drawio"

    def test_format_from_string(self) -> None:
        """Test creating format from string."""
        assert ExportFormat("png") == ExportFormat.PNG
        assert ExportFormat("mmd") == ExportFormat.MERMAID
        assert ExportFormat("drawio") == ExportFormat.DRAWIO

    def test_invalid_format_raises_error(self) -> None:
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError):
            ExportFormat("invalid")


class TestTranslateRequest:
    """Tests for TranslateRequest model."""

    def test_valid_request_minimal(self) -> None:
        """Test creating a valid request with minimal fields."""
        request = TranslateRequest(
            svg_content="<svg></svg>",
            format=ExportFormat.PNG,
        )
        assert request.svg_content == "<svg></svg>"
        assert request.format == ExportFormat.PNG
        assert request.options is None

    def test_valid_request_with_options(self) -> None:
        """Test creating a valid request with options."""
        request = TranslateRequest(
            svg_content="<svg><rect/></svg>",
            format=ExportFormat.MERMAID,
            options={"diagram_type": "flowchart"},
        )
        assert request.svg_content == "<svg><rect/></svg>"
        assert request.format == ExportFormat.MERMAID
        assert request.options == {"diagram_type": "flowchart"}

    def test_valid_request_with_png_options(self) -> None:
        """Test creating a valid PNG request with size options."""
        request = TranslateRequest(
            svg_content="<svg width='800' height='600'></svg>",
            format=ExportFormat.PNG,
            options={"width": 1600, "height": 1200},
        )
        assert request.options["width"] == 1600
        assert request.options["height"] == 1200

    def test_request_from_dict(self) -> None:
        """Test creating request from dictionary."""
        data = {
            "svg_content": "<svg></svg>",
            "format": "png",
            "options": {"width": 800},
        }
        request = TranslateRequest(**data)
        assert request.format == ExportFormat.PNG
        assert request.options["width"] == 800

    def test_empty_svg_raises_error(self) -> None:
        """Test that empty SVG content raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            TranslateRequest(
                svg_content="",
                format=ExportFormat.PNG,
            )
        errors = exc_info.value.errors()
        assert any("min_length" in str(e) for e in errors)

    def test_missing_svg_raises_error(self) -> None:
        """Test that missing SVG content raises validation error."""
        with pytest.raises(ValidationError):
            TranslateRequest(format=ExportFormat.PNG)

    def test_missing_format_raises_error(self) -> None:
        """Test that missing format raises validation error."""
        with pytest.raises(ValidationError):
            TranslateRequest(svg_content="<svg></svg>")

    def test_invalid_format_raises_error(self) -> None:
        """Test that invalid format raises validation error."""
        with pytest.raises(ValidationError):
            TranslateRequest(
                svg_content="<svg></svg>",
                format="invalid_format",
            )


class TestTranslateResponse:
    """Tests for TranslateResponse model."""

    def test_valid_response_minimal(self) -> None:
        """Test creating a valid response with minimal fields."""
        response = TranslateResponse(
            content="base64-encoded-png-data",
            format=ExportFormat.PNG,
            model_used="gemini-2.0-flash",
        )
        assert response.content == "base64-encoded-png-data"
        assert response.format == ExportFormat.PNG
        assert response.model_used == "gemini-2.0-flash"
        assert response.metadata is None

    def test_valid_response_with_metadata(self) -> None:
        """Test creating a valid response with metadata."""
        response = TranslateResponse(
            content="flowchart TD\n    A-->B",
            format=ExportFormat.MERMAID,
            model_used="claude-sonnet-4",
            metadata={"diagram_type": "flowchart"},
        )
        assert response.content == "flowchart TD\n    A-->B"
        assert response.metadata["diagram_type"] == "flowchart"

    def test_png_response_with_size_metadata(self) -> None:
        """Test PNG response with size metadata."""
        response = TranslateResponse(
            content="iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB...",
            format=ExportFormat.PNG,
            model_used="gemini-2.0-flash",
            metadata={"width": 800, "height": 600, "size_bytes": 12345},
        )
        assert response.metadata["width"] == 800
        assert response.metadata["height"] == 600
        assert response.metadata["size_bytes"] == 12345

    def test_drawio_response(self) -> None:
        """Test Draw.io XML response."""
        drawio_xml = "<mxGraphModel><root></root></mxGraphModel>"
        response = TranslateResponse(
            content=drawio_xml,
            format=ExportFormat.DRAWIO,
            model_used="claude-sonnet-4",
            metadata={"element_count": 5},
        )
        assert response.format == ExportFormat.DRAWIO
        assert response.metadata["element_count"] == 5

    def test_missing_content_raises_error(self) -> None:
        """Test that missing content raises validation error."""
        with pytest.raises(ValidationError):
            TranslateResponse(
                format=ExportFormat.PNG,
                model_used="test-model",
            )

    def test_missing_format_raises_error(self) -> None:
        """Test that missing format raises validation error."""
        with pytest.raises(ValidationError):
            TranslateResponse(
                content="test-content",
                model_used="test-model",
            )

    def test_missing_model_raises_error(self) -> None:
        """Test that missing model_used raises validation error."""
        with pytest.raises(ValidationError):
            TranslateResponse(
                content="test-content",
                format=ExportFormat.PNG,
            )


class TestTranslateErrorCode:
    """Tests for TranslateErrorCode enum."""

    def test_all_error_codes_exist(self) -> None:
        """Test that all expected error codes exist."""
        assert TranslateErrorCode.MODEL_ERROR.value == "MODEL_ERROR"
        assert TranslateErrorCode.INVALID_FORMAT.value == "INVALID_FORMAT"
        assert TranslateErrorCode.SVG_PARSE_ERROR.value == "SVG_PARSE_ERROR"
        assert TranslateErrorCode.RATE_LIMIT.value == "RATE_LIMIT"
        assert TranslateErrorCode.AGENT_NOT_CONFIGURED.value == "AGENT_NOT_CONFIGURED"
        assert TranslateErrorCode.UNSUPPORTED_FORMAT.value == "UNSUPPORTED_FORMAT"


class TestTranslateErrorResponse:
    """Tests for TranslateErrorResponse model."""

    def test_valid_error_minimal(self) -> None:
        """Test creating a valid error response with minimal fields."""
        error = TranslateErrorResponse(
            error="Translation failed",
            code=TranslateErrorCode.MODEL_ERROR,
        )
        assert error.error == "Translation failed"
        assert error.code == TranslateErrorCode.MODEL_ERROR
        assert error.details is None

    def test_valid_error_with_details(self) -> None:
        """Test creating a valid error response with details."""
        error = TranslateErrorResponse(
            error="Rate limit exceeded",
            code=TranslateErrorCode.RATE_LIMIT,
            details="Try again in 60 seconds",
        )
        assert error.error == "Rate limit exceeded"
        assert error.code == TranslateErrorCode.RATE_LIMIT
        assert error.details == "Try again in 60 seconds"

    def test_svg_parse_error(self) -> None:
        """Test SVG parse error response."""
        error = TranslateErrorResponse(
            error="Invalid SVG content",
            code=TranslateErrorCode.SVG_PARSE_ERROR,
            details="SVG is missing required xmlns attribute",
        )
        assert error.code == TranslateErrorCode.SVG_PARSE_ERROR

    def test_agent_not_configured_error(self) -> None:
        """Test agent not configured error response."""
        error = TranslateErrorResponse(
            error="Design agent not configured",
            code=TranslateErrorCode.AGENT_NOT_CONFIGURED,
            details="Configure the Design agent in LLM Admin settings",
        )
        assert error.code == TranslateErrorCode.AGENT_NOT_CONFIGURED

    def test_missing_error_raises_error(self) -> None:
        """Test that missing error message raises validation error."""
        with pytest.raises(ValidationError):
            TranslateErrorResponse(code=TranslateErrorCode.MODEL_ERROR)

    def test_missing_code_raises_error(self) -> None:
        """Test that missing code raises validation error."""
        with pytest.raises(ValidationError):
            TranslateErrorResponse(error="Error occurred")

    def test_invalid_code_raises_error(self) -> None:
        """Test that invalid code raises validation error."""
        with pytest.raises(ValidationError):
            TranslateErrorResponse(
                error="Error occurred",
                code="INVALID_CODE",
            )

    def test_error_response_from_dict(self) -> None:
        """Test creating error response from dictionary."""
        data = {
            "error": "Model unavailable",
            "code": "MODEL_ERROR",
            "details": "The specified model is not available",
        }
        error = TranslateErrorResponse(**data)
        assert error.code == TranslateErrorCode.MODEL_ERROR

"""Unit tests for Architect API routes.

Tests the architect API endpoints for diagram translation.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.orchestrator.api.models.architect import (
    ExportFormat,
    TranslateErrorCode,
    TranslateResponse,
)
from src.orchestrator.services.architect_service import ArchitectServiceError


class TestTranslateEndpoint:
    """Tests for POST /api/architect/translate endpoint."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client."""
        from src.orchestrator.routes.architect_api import router

        app = FastAPI()
        app.include_router(router)

        return TestClient(app)

    def test_translate_to_mermaid_success(self, client: TestClient) -> None:
        """Test successful Mermaid translation."""
        with patch(
            "src.orchestrator.routes.architect_api.get_architect_service"
        ) as mock_get_service:
            mock_service = AsyncMock()
            mock_service.translate.return_value = TranslateResponse(
                content="flowchart TD\n    A-->B",
                format=ExportFormat.MERMAID,
                model_used="claude-sonnet-4",
                metadata={"diagram_type": "flowchart"},
            )
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/architect/translate",
                json={
                    "svgContent": "<svg><rect/></svg>",
                    "format": "mmd",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["format"] == "mmd"
            assert "flowchart" in data["content"]
            assert data["modelUsed"] == "claude-sonnet-4"

    def test_translate_to_drawio_success(self, client: TestClient) -> None:
        """Test successful Draw.io translation."""
        with patch(
            "src.orchestrator.routes.architect_api.get_architect_service"
        ) as mock_get_service:
            mock_service = AsyncMock()
            mock_service.translate.return_value = TranslateResponse(
                content="<mxGraphModel><root></root></mxGraphModel>",
                format=ExportFormat.DRAWIO,
                model_used="claude-sonnet-4",
            )
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/architect/translate",
                json={
                    "svgContent": "<svg><rect/></svg>",
                    "format": "drawio",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["format"] == "drawio"
            assert "mxGraphModel" in data["content"]

    def test_translate_with_options(self, client: TestClient) -> None:
        """Test translation with format-specific options."""
        with patch(
            "src.orchestrator.routes.architect_api.get_architect_service"
        ) as mock_get_service:
            mock_service = AsyncMock()
            mock_service.translate.return_value = TranslateResponse(
                content="sequenceDiagram\n    Alice->>Bob: Hello",
                format=ExportFormat.MERMAID,
                model_used="claude-sonnet-4",
                metadata={"diagram_type": "sequence"},
            )
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/architect/translate",
                json={
                    "svgContent": "<svg><text>Alice</text><text>Bob</text></svg>",
                    "format": "mmd",
                    "options": {"diagram_type": "sequence"},
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "sequenceDiagram" in data["content"]
            assert data["metadata"]["diagram_type"] == "sequence"

            # Verify options were passed to service
            mock_service.translate.assert_called_once()
            call_args = mock_service.translate.call_args
            assert call_args.kwargs["options"]["diagram_type"] == "sequence"


class TestTranslateEndpointValidation:
    """Tests for request validation on translate endpoint."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client."""
        from src.orchestrator.routes.architect_api import router

        app = FastAPI()
        app.include_router(router)

        return TestClient(app)

    def test_missing_svgContent(self, client: TestClient) -> None:
        """Test validation error for missing SVG content."""
        response = client.post(
            "/api/architect/translate",
            json={"format": "mmd"},
        )

        assert response.status_code == 422  # Validation error

    def test_empty_svgContent(self, client: TestClient) -> None:
        """Test validation error for empty SVG content."""
        response = client.post(
            "/api/architect/translate",
            json={"svgContent": "", "format": "mmd"},
        )

        assert response.status_code == 422  # Validation error

    def test_missing_format(self, client: TestClient) -> None:
        """Test validation error for missing format."""
        response = client.post(
            "/api/architect/translate",
            json={"svgContent": "<svg></svg>"},
        )

        assert response.status_code == 422  # Validation error

    def test_invalid_format(self, client: TestClient) -> None:
        """Test validation error for invalid format."""
        response = client.post(
            "/api/architect/translate",
            json={"svgContent": "<svg></svg>", "format": "invalid_format"},
        )

        assert response.status_code == 422  # Validation error


class TestTranslateEndpointErrors:
    """Tests for error handling on translate endpoint."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client."""
        from src.orchestrator.routes.architect_api import router

        app = FastAPI()
        app.include_router(router)

        return TestClient(app)

    def test_unsupported_format_error(self, client: TestClient) -> None:
        """Test error response for unsupported format (PNG)."""
        with patch(
            "src.orchestrator.routes.architect_api.get_architect_service"
        ) as mock_get_service:
            mock_service = AsyncMock()
            mock_service.translate.side_effect = ArchitectServiceError(
                message="PNG translation is not yet implemented",
                code=TranslateErrorCode.UNSUPPORTED_FORMAT,
                details="PNG export requires Gemini image generation (Phase 2)",
            )
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/architect/translate",
                json={"svgContent": "<svg></svg>", "format": "png"},
            )

            assert response.status_code == 501  # Not Implemented
            data = response.json()
            assert data["error"] == "PNG translation is not yet implemented"
            assert data["code"] == "UNSUPPORTED_FORMAT"

    def test_agent_not_configured_error(self, client: TestClient) -> None:
        """Test error response when Design agent is not configured."""
        with patch(
            "src.orchestrator.routes.architect_api.get_architect_service"
        ) as mock_get_service:
            mock_service = AsyncMock()
            mock_service.translate.side_effect = ArchitectServiceError(
                message="Design agent is not configured",
                code=TranslateErrorCode.AGENT_NOT_CONFIGURED,
                details="Configure the Design agent in LLM Admin settings",
            )
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/architect/translate",
                json={"svgContent": "<svg></svg>", "format": "mmd"},
            )

            assert response.status_code == 503  # Service Unavailable
            data = response.json()
            assert data["code"] == "AGENT_NOT_CONFIGURED"

    def test_model_error(self, client: TestClient) -> None:
        """Test error response for LLM model errors."""
        with patch(
            "src.orchestrator.routes.architect_api.get_architect_service"
        ) as mock_get_service:
            mock_service = AsyncMock()
            mock_service.translate.side_effect = ArchitectServiceError(
                message="Failed to generate translation",
                code=TranslateErrorCode.MODEL_ERROR,
                details="LLM API returned an error",
            )
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/architect/translate",
                json={"svgContent": "<svg></svg>", "format": "mmd"},
            )

            assert response.status_code == 500  # Internal Server Error
            data = response.json()
            assert data["code"] == "MODEL_ERROR"

    def test_rate_limit_error(self, client: TestClient) -> None:
        """Test error response for rate limit errors."""
        with patch(
            "src.orchestrator.routes.architect_api.get_architect_service"
        ) as mock_get_service:
            mock_service = AsyncMock()
            mock_service.translate.side_effect = ArchitectServiceError(
                message="Rate limit exceeded",
                code=TranslateErrorCode.RATE_LIMIT,
                details="Try again in 60 seconds",
            )
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/architect/translate",
                json={"svgContent": "<svg></svg>", "format": "mmd"},
            )

            assert response.status_code == 429  # Too Many Requests
            data = response.json()
            assert data["code"] == "RATE_LIMIT"

    def test_svg_parse_error(self, client: TestClient) -> None:
        """Test error response for SVG parse errors."""
        with patch(
            "src.orchestrator.routes.architect_api.get_architect_service"
        ) as mock_get_service:
            mock_service = AsyncMock()
            mock_service.translate.side_effect = ArchitectServiceError(
                message="Invalid SVG content",
                code=TranslateErrorCode.SVG_PARSE_ERROR,
                details="Could not parse SVG structure",
            )
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/architect/translate",
                json={"svgContent": "not valid svg", "format": "mmd"},
            )

            assert response.status_code == 400  # Bad Request
            data = response.json()
            assert data["code"] == "SVG_PARSE_ERROR"

    def test_unexpected_error(self, client: TestClient) -> None:
        """Test error response for unexpected errors."""
        with patch(
            "src.orchestrator.routes.architect_api.get_architect_service"
        ) as mock_get_service:
            mock_service = AsyncMock()
            mock_service.translate.side_effect = Exception("Unexpected error")
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/architect/translate",
                json={"svgContent": "<svg></svg>", "format": "mmd"},
            )

            assert response.status_code == 500  # Internal Server Error
            data = response.json()
            assert data["code"] == "MODEL_ERROR"


class TestTranslateEndpointMetadata:
    """Tests for metadata handling on translate endpoint."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client."""
        from src.orchestrator.routes.architect_api import router

        app = FastAPI()
        app.include_router(router)

        return TestClient(app)

    def test_response_includes_metadata(self, client: TestClient) -> None:
        """Test that response includes metadata when present."""
        with patch(
            "src.orchestrator.routes.architect_api.get_architect_service"
        ) as mock_get_service:
            mock_service = AsyncMock()
            mock_service.translate.return_value = TranslateResponse(
                content="flowchart TD\n    A-->B",
                format=ExportFormat.MERMAID,
                model_used="claude-sonnet-4",
                metadata={"diagram_type": "flowchart", "node_count": 2},
            )
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/architect/translate",
                json={"svgContent": "<svg></svg>", "format": "mmd"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["metadata"] is not None
            assert data["metadata"]["diagram_type"] == "flowchart"

    def test_response_without_metadata(self, client: TestClient) -> None:
        """Test that response works without metadata."""
        with patch(
            "src.orchestrator.routes.architect_api.get_architect_service"
        ) as mock_get_service:
            mock_service = AsyncMock()
            mock_service.translate.return_value = TranslateResponse(
                content="<mxGraphModel></mxGraphModel>",
                format=ExportFormat.DRAWIO,
                model_used="claude-sonnet-4",
                metadata=None,
            )
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/architect/translate",
                json={"svgContent": "<svg></svg>", "format": "drawio"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["metadata"] is None

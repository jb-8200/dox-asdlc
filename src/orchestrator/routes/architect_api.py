"""Architect Board translation API routes.

This module provides REST API endpoints for translating SVG diagrams
from the Architect Board to various export formats (PNG, Mermaid, Draw.io).

Endpoints:
- POST /api/architect/translate - Translate SVG to target format
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from src.orchestrator.api.models.architect import (
    ExportFormat,
    TranslateErrorCode,
    TranslateErrorResponse,
    TranslateRequest,
    TranslateResponse,
)
from src.orchestrator.services.architect_service import (
    ArchitectService,
    ArchitectServiceError,
    get_architect_service,
)


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/architect", tags=["architect"])


# HTTP status codes for each error code
ERROR_CODE_TO_STATUS: dict[TranslateErrorCode, int] = {
    TranslateErrorCode.MODEL_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    TranslateErrorCode.INVALID_FORMAT: status.HTTP_400_BAD_REQUEST,
    TranslateErrorCode.SVG_PARSE_ERROR: status.HTTP_400_BAD_REQUEST,
    TranslateErrorCode.RATE_LIMIT: status.HTTP_429_TOO_MANY_REQUESTS,
    TranslateErrorCode.AGENT_NOT_CONFIGURED: status.HTTP_503_SERVICE_UNAVAILABLE,
    TranslateErrorCode.UNSUPPORTED_FORMAT: status.HTTP_501_NOT_IMPLEMENTED,
}


@router.post(
    "/translate",
    response_model=TranslateResponse,
    response_model_by_alias=True,
    responses={
        400: {"model": TranslateErrorResponse, "description": "Bad request"},
        429: {"model": TranslateErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": TranslateErrorResponse, "description": "Server error"},
        501: {"model": TranslateErrorResponse, "description": "Not implemented"},
        503: {"model": TranslateErrorResponse, "description": "Service unavailable"},
    },
)
async def translate_diagram(request: TranslateRequest) -> TranslateResponse:
    """Translate an SVG diagram to the specified format.

    This endpoint accepts an SVG diagram exported from the Architect Board
    and translates it to the specified format using the Design agent's LLM.

    Args:
        request: The translation request with SVG content and target format.

    Returns:
        TranslateResponse: The translated content and metadata.

    Raises:
        HTTPException: If translation fails with appropriate status code.
    """
    service = get_architect_service()

    try:
        result = await service.translate(
            svg_content=request.svg_content,
            format=request.format,
            options=request.options,
        )
        return result

    except ArchitectServiceError as e:
        logger.warning(f"Translation failed: {e.code} - {e}")
        status_code = ERROR_CODE_TO_STATUS.get(
            e.code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        return JSONResponse(
            status_code=status_code,
            content=TranslateErrorResponse(
                error=str(e),
                code=e.code,
                details=e.details,
            ).model_dump(by_alias=True),
        )

    except Exception as e:
        logger.error(f"Unexpected error during translation: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=TranslateErrorResponse(
                error="An unexpected error occurred during translation",
                code=TranslateErrorCode.MODEL_ERROR,
                details=str(e),
            ).model_dump(by_alias=True),
        )

"""Tests for tenant middleware (P06-F05)."""

from __future__ import annotations

from typing import Any
from unittest import mock

import pytest

from src.core.config import TenantConfig
from src.core.middleware import (
    TenantMiddleware,
    extract_tenant_from_event,
    inject_tenant_into_event,
    process_event_with_tenant,
)
from src.core.tenant import TenantContext


class TestTenantMiddleware:
    """Test the TenantMiddleware class."""

    @pytest.fixture
    def config_enabled(self) -> TenantConfig:
        """Create a tenant config with multi-tenancy enabled."""
        return TenantConfig(
            enabled=True,
            default_tenant="test-default",
            allowed_tenants=("tenant-a", "tenant-b", "*"),
        )

    @pytest.fixture
    def config_disabled(self) -> TenantConfig:
        """Create a tenant config with multi-tenancy disabled."""
        return TenantConfig(
            enabled=False,
            default_tenant="disabled-default",
        )

    @pytest.mark.asyncio
    async def test_middleware_sets_tenant_from_header(
        self, config_enabled: TenantConfig
    ) -> None:
        """Test that middleware extracts tenant from header."""
        captured_tenant = None

        async def app(scope: dict, receive: Any, send: Any) -> None:
            nonlocal captured_tenant
            captured_tenant = TenantContext.get_current_tenant()

        middleware = TenantMiddleware(app, config=config_enabled)

        scope = {
            "type": "http",
            "headers": [(b"x-tenant-id", b"tenant-a")],
        }

        await middleware(scope, mock.AsyncMock(), mock.AsyncMock())

        assert captured_tenant == "tenant-a"

    @pytest.mark.asyncio
    async def test_middleware_uses_default_tenant_when_no_header(
        self, config_enabled: TenantConfig
    ) -> None:
        """Test that middleware uses default tenant when header is missing."""
        captured_tenant = None

        async def app(scope: dict, receive: Any, send: Any) -> None:
            nonlocal captured_tenant
            captured_tenant = TenantContext.get_current_tenant()

        middleware = TenantMiddleware(app, config=config_enabled)

        scope = {
            "type": "http",
            "headers": [],
        }

        await middleware(scope, mock.AsyncMock(), mock.AsyncMock())

        assert captured_tenant == "test-default"

    @pytest.mark.asyncio
    async def test_middleware_disabled_uses_default(
        self, config_disabled: TenantConfig
    ) -> None:
        """Test that disabled middleware uses default tenant."""
        captured_tenant = None

        async def app(scope: dict, receive: Any, send: Any) -> None:
            nonlocal captured_tenant
            captured_tenant = TenantContext.get_current_tenant()

        middleware = TenantMiddleware(app, config=config_disabled)

        scope = {
            "type": "http",
            "headers": [(b"x-tenant-id", b"ignored-tenant")],
        }

        await middleware(scope, mock.AsyncMock(), mock.AsyncMock())

        assert captured_tenant == "disabled-default"

    @pytest.mark.asyncio
    async def test_middleware_rejects_invalid_tenant(self) -> None:
        """Test that middleware rejects tenants not in allowlist."""
        config = TenantConfig(
            enabled=True,
            default_tenant="default",
            allowed_tenants=("allowed-tenant",),
        )

        app_called = False

        async def app(scope: dict, receive: Any, send: Any) -> None:
            nonlocal app_called
            app_called = True

        middleware = TenantMiddleware(app, config=config)

        scope = {
            "type": "http",
            "headers": [(b"x-tenant-id", b"not-allowed")],
        }

        # Capture the send calls
        send_calls = []

        async def mock_send(message: dict) -> None:
            send_calls.append(message)

        await middleware(scope, mock.AsyncMock(), mock_send)

        # App should not be called
        assert app_called is False

        # Should send 403 response
        assert len(send_calls) == 2
        assert send_calls[0]["status"] == 403
        assert b"Forbidden" in send_calls[1]["body"]

    @pytest.mark.asyncio
    async def test_middleware_passes_through_non_http(
        self, config_enabled: TenantConfig
    ) -> None:
        """Test that middleware passes through non-HTTP requests."""
        app_called = False

        async def app(scope: dict, receive: Any, send: Any) -> None:
            nonlocal app_called
            app_called = True

        middleware = TenantMiddleware(app, config=config_enabled)

        scope = {"type": "websocket"}

        await middleware(scope, mock.AsyncMock(), mock.AsyncMock())

        assert app_called is True

    @pytest.mark.asyncio
    async def test_middleware_custom_header(self) -> None:
        """Test middleware with custom tenant header."""
        config = TenantConfig(
            enabled=True,
            default_tenant="default",
            allowed_tenants=("*",),
            tenant_header="X-Organization-ID",
        )

        captured_tenant = None

        async def app(scope: dict, receive: Any, send: Any) -> None:
            nonlocal captured_tenant
            captured_tenant = TenantContext.get_current_tenant()

        middleware = TenantMiddleware(app, config=config)

        scope = {
            "type": "http",
            "headers": [(b"x-organization-id", b"custom-org")],
        }

        await middleware(scope, mock.AsyncMock(), mock.AsyncMock())

        assert captured_tenant == "custom-org"


class TestExtractTenantFromEvent:
    """Test the extract_tenant_from_event function."""

    def test_extracts_tenant_id(self) -> None:
        """Test extracting tenant_id from event."""
        event = {"event_type": "task_created", "tenant_id": "acme-corp"}
        assert extract_tenant_from_event(event) == "acme-corp"

    def test_returns_none_when_missing(self) -> None:
        """Test returns None when tenant_id is missing."""
        event = {"event_type": "task_created"}
        assert extract_tenant_from_event(event) is None

    def test_returns_none_for_empty_event(self) -> None:
        """Test returns None for empty event."""
        assert extract_tenant_from_event({}) is None


class TestInjectTenantIntoEvent:
    """Test the inject_tenant_into_event function."""

    def test_injects_tenant_id(self) -> None:
        """Test injecting tenant_id into event."""
        with TenantContext.tenant_scope("widgets-inc"):
            event = {"event_type": "task_completed"}
            result = inject_tenant_into_event(event)

            assert result["tenant_id"] == "widgets-inc"
            assert result["event_type"] == "task_completed"

    def test_does_not_modify_original_event(self) -> None:
        """Test that original event is not modified."""
        with TenantContext.tenant_scope("test-tenant"):
            original = {"event_type": "test"}
            result = inject_tenant_into_event(original)

            assert "tenant_id" not in original
            assert "tenant_id" in result


class TestProcessEventWithTenant:
    """Test the process_event_with_tenant function."""

    @pytest.mark.asyncio
    async def test_processes_with_event_tenant(self) -> None:
        """Test processing event with tenant from event."""
        captured_tenant = None

        async def handler(event: dict) -> str:
            nonlocal captured_tenant
            captured_tenant = TenantContext.get_current_tenant()
            return "processed"

        event = {"tenant_id": "event-tenant", "data": "test"}
        result = await process_event_with_tenant(event, handler)

        assert result == "processed"
        assert captured_tenant == "event-tenant"

    @pytest.mark.asyncio
    async def test_uses_default_tenant_when_missing(self) -> None:
        """Test processing event without tenant_id uses default."""
        captured_tenant = None

        async def handler(event: dict) -> str:
            nonlocal captured_tenant
            captured_tenant = TenantContext.get_current_tenant()
            return "processed"

        event = {"data": "test"}
        await process_event_with_tenant(event, handler, default_tenant="fallback")

        assert captured_tenant == "fallback"

    @pytest.mark.asyncio
    async def test_restores_context_after_processing(self) -> None:
        """Test that context is restored after processing."""
        TenantContext.set_tenant("outer-tenant")

        async def handler(event: dict) -> None:
            assert TenantContext.get_current_tenant() == "inner-tenant"

        await process_event_with_tenant(
            {"tenant_id": "inner-tenant"},
            handler,
        )

        assert TenantContext.get_current_tenant() == "outer-tenant"

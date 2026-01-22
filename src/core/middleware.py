"""Middleware components for the aSDLC system.

Provides request processing middleware including tenant validation.
"""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from src.core.config import TenantConfig, get_tenant_config
from src.core.exceptions import TenantNotAllowedError
from src.core.tenant import TenantContext, validate_tenant

logger = logging.getLogger(__name__)

# Type alias for ASGI scope
Scope = dict[str, Any]
Receive = Callable[[], Awaitable[dict[str, Any]]]
Send = Callable[[dict[str, Any]], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


class TenantMiddleware:
    """ASGI middleware for tenant context management.

    Extracts tenant ID from HTTP headers and sets the tenant context
    for the duration of the request. Validates tenant against allowlist.

    Usage with FastAPI:
        app = FastAPI()
        app.add_middleware(TenantMiddleware)

    Usage with Starlette:
        app = Starlette(middleware=[Middleware(TenantMiddleware)])
    """

    def __init__(
        self,
        app: ASGIApp,
        config: TenantConfig | None = None,
    ) -> None:
        """Initialize the middleware.

        Args:
            app: The ASGI application to wrap.
            config: Optional tenant configuration. If not provided,
                    will be loaded from environment.
        """
        self.app = app
        self.config = config or get_tenant_config()

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        """Process the request.

        Args:
            scope: The ASGI scope dictionary.
            receive: The receive channel.
            send: The send channel.
        """
        if scope["type"] != "http":
            # Pass through non-HTTP requests (e.g., websocket, lifespan)
            await self.app(scope, receive, send)
            return

        if not self.config.enabled:
            # Multi-tenancy disabled, use default tenant
            with TenantContext.tenant_scope(self.config.default_tenant):
                await self.app(scope, receive, send)
            return

        # Extract tenant from headers
        tenant_id = self._extract_tenant_from_headers(scope)

        if not tenant_id:
            # No tenant header, use default
            tenant_id = self.config.default_tenant
            logger.debug(f"No tenant header, using default: {tenant_id}")

        # Validate tenant
        try:
            validate_tenant(
                tenant_id,
                list(self.config.allowed_tenants),
            )
        except TenantNotAllowedError as e:
            logger.warning(f"Tenant validation failed: {e}")
            await self._send_forbidden_response(send, str(e))
            return

        # Set tenant context and process request
        logger.debug(f"Processing request with tenant: {tenant_id}")
        with TenantContext.tenant_scope(tenant_id):
            await self.app(scope, receive, send)

    def _extract_tenant_from_headers(self, scope: Scope) -> str | None:
        """Extract tenant ID from request headers.

        Args:
            scope: The ASGI scope containing headers.

        Returns:
            The tenant ID if found, None otherwise.
        """
        headers = dict(scope.get("headers", []))
        header_name = self.config.tenant_header.lower().encode()

        tenant_bytes = headers.get(header_name)
        if tenant_bytes:
            return tenant_bytes.decode("utf-8")

        return None

    async def _send_forbidden_response(
        self,
        send: Send,
        message: str,
    ) -> None:
        """Send a 403 Forbidden response.

        Args:
            send: The send channel.
            message: Error message to include in the response.
        """
        body = f'{{"error": "Forbidden", "message": "{message}"}}'.encode()

        await send({
            "type": "http.response.start",
            "status": 403,
            "headers": [
                [b"content-type", b"application/json"],
                [b"content-length", str(len(body)).encode()],
            ],
        })
        await send({
            "type": "http.response.body",
            "body": body,
        })


def extract_tenant_from_event(event: dict[str, Any]) -> str | None:
    """Extract tenant ID from an event payload.

    Args:
        event: The event dictionary.

    Returns:
        The tenant ID if present, None otherwise.
    """
    return event.get("tenant_id")


def inject_tenant_into_event(event: dict[str, Any]) -> dict[str, Any]:
    """Inject the current tenant ID into an event payload.

    Args:
        event: The event dictionary to modify.

    Returns:
        The event dictionary with tenant_id added.

    Raises:
        TenantNotSetError: If no tenant is set in the current context.
    """
    tenant_id = TenantContext.get_current_tenant()
    return {**event, "tenant_id": tenant_id}


async def process_event_with_tenant(
    event: dict[str, Any],
    handler: Callable[[dict[str, Any]], Awaitable[Any]],
    default_tenant: str = "default",
) -> Any:
    """Process an event with tenant context from the event payload.

    Extracts tenant_id from the event and sets the tenant context
    before calling the handler.

    Args:
        event: The event dictionary containing tenant_id.
        handler: The async handler function to call.
        default_tenant: Default tenant if event has no tenant_id.

    Returns:
        The result from the handler.
    """
    tenant_id = extract_tenant_from_event(event) or default_tenant
    logger.debug(f"Processing event with tenant: {tenant_id}")

    with TenantContext.tenant_scope(tenant_id):
        return await handler(event)

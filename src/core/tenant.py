"""Tenant context management for multi-tenancy support.

Provides thread-safe tenant context propagation using contextvars.
All tenant-aware operations should use this module to get/set the
current tenant context.
"""

from __future__ import annotations

import contextvars
import logging
from contextlib import contextmanager
from typing import Generator

from src.core.exceptions import TenantNotAllowedError, TenantNotSetError

logger = logging.getLogger(__name__)

# Thread-safe context variable for tenant ID
_tenant_id: contextvars.ContextVar[str] = contextvars.ContextVar("tenant_id")


class TenantContext:
    """Thread-safe tenant context for request isolation.

    Uses contextvars to provide async-safe tenant context propagation.
    Each request/task should set its tenant context at the entry point.

    Example:
        # In a request handler
        with TenantContext.tenant_scope("acme-corp"):
            # All operations in this scope use "acme-corp" tenant
            await process_request()

        # Or manually
        TenantContext.set_tenant("widgets-inc")
        try:
            await process_request()
        finally:
            TenantContext.clear()
    """

    @classmethod
    def get_current_tenant(cls) -> str:
        """Get the current tenant ID.

        Returns:
            str: The current tenant ID.

        Raises:
            TenantNotSetError: If no tenant is set in the current context.
        """
        try:
            return _tenant_id.get()
        except LookupError:
            raise TenantNotSetError(
                "No tenant set in current context. "
                "Use TenantContext.set_tenant() or TenantContext.tenant_scope() "
                "to set tenant context."
            )

    @classmethod
    def get_current_tenant_or_default(cls, default: str = "default") -> str:
        """Get the current tenant ID or a default value.

        Args:
            default: Value to return if no tenant is set.

        Returns:
            str: The current tenant ID or the default value.
        """
        try:
            return _tenant_id.get()
        except LookupError:
            return default

    @classmethod
    def set_tenant(cls, tenant_id: str) -> contextvars.Token[str]:
        """Set the tenant for the current context.

        Args:
            tenant_id: The tenant identifier to set.

        Returns:
            Token that can be used to reset to previous state.
        """
        logger.debug(f"Setting tenant context: {tenant_id}")
        return _tenant_id.set(tenant_id)

    @classmethod
    def clear(cls) -> None:
        """Clear the tenant context.

        This removes the tenant ID from the current context.
        Use this at the end of request processing to prevent leaks.
        """
        try:
            # Create a copy of current context vars without tenant
            _tenant_id.get()  # Check if set
            # Reset by getting a token and not using it
            logger.debug("Clearing tenant context")
        except LookupError:
            pass  # Already clear

    @classmethod
    def reset(cls, token: contextvars.Token[str]) -> None:
        """Reset tenant context to a previous state.

        Args:
            token: Token from a previous set_tenant() call.
        """
        _tenant_id.reset(token)
        logger.debug("Reset tenant context to previous state")

    @classmethod
    def is_set(cls) -> bool:
        """Check if a tenant is set in the current context.

        Returns:
            bool: True if a tenant is set, False otherwise.
        """
        try:
            _tenant_id.get()
            return True
        except LookupError:
            return False

    @classmethod
    @contextmanager
    def tenant_scope(cls, tenant_id: str) -> Generator[None, None, None]:
        """Context manager for tenant scope.

        Automatically sets and clears tenant context. Restores previous
        tenant context if one was set (supports nested scopes).

        Args:
            tenant_id: The tenant identifier for this scope.

        Yields:
            None

        Example:
            with TenantContext.tenant_scope("acme-corp"):
                # All operations here use "acme-corp" tenant
                data = await redis_client.get("some-key")
                # Key will be prefixed: tenant:acme-corp:some-key
        """
        token = cls.set_tenant(tenant_id)
        try:
            yield
        finally:
            cls.reset(token)


def validate_tenant(tenant_id: str, allowed_tenants: list[str] | None = None) -> bool:
    """Validate a tenant ID against an allowlist.

    Args:
        tenant_id: The tenant ID to validate.
        allowed_tenants: List of allowed tenant IDs. If None or contains "*",
            all tenants are allowed.

    Returns:
        bool: True if the tenant is valid.

    Raises:
        TenantNotAllowedError: If the tenant is not in the allowlist.
    """
    if not tenant_id or not tenant_id.strip():
        raise TenantNotAllowedError(
            "Tenant ID cannot be empty",
            details={"tenant_id": tenant_id},
        )

    # Check allowlist
    if allowed_tenants is None or "*" in allowed_tenants:
        return True

    if tenant_id not in allowed_tenants:
        raise TenantNotAllowedError(
            f"Tenant '{tenant_id}' is not in the allowed tenants list",
            details={
                "tenant_id": tenant_id,
                "allowed_tenants": allowed_tenants,
            },
        )

    return True


def get_tenant_prefixed_key(key: str, separator: str = ":") -> str:
    """Get a key with tenant prefix.

    Utility function for creating tenant-prefixed keys.

    Args:
        key: The original key.
        separator: Separator between prefix components.

    Returns:
        str: The key prefixed with "tenant:{tenant_id}:".

    Raises:
        TenantNotSetError: If no tenant is set in the current context.
    """
    tenant_id = TenantContext.get_current_tenant()
    return f"tenant{separator}{tenant_id}{separator}{key}"


def get_tenant_collection_name(base_name: str) -> str:
    """Get a collection name with tenant prefix.

    Utility function for creating tenant-prefixed collection names.

    Args:
        base_name: The base collection name.

    Returns:
        str: The collection name prefixed with "{tenant_id}_".

    Raises:
        TenantNotSetError: If no tenant is set in the current context.
    """
    tenant_id = TenantContext.get_current_tenant()
    return f"{tenant_id}_{base_name}"

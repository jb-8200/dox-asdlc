"""Unit tests for tenant-aware KnowledgeStore.

Tests that documents are isolated by tenant context.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from src.core.tenant import TenantContext
from src.infrastructure.knowledge_store.config import KnowledgeStoreConfig
from src.infrastructure.knowledge_store.mock_anthology import MockAnthologyStore
from src.infrastructure.knowledge_store.models import Document


@pytest.fixture
def mock_store() -> MockAnthologyStore:
    """Create a fresh MockAnthologyStore for testing."""
    config = KnowledgeStoreConfig(backend="mock_anthology")
    store = MockAnthologyStore(config)
    return store


@pytest.fixture
def multi_tenant_env():
    """Enable multi-tenancy via environment variables."""
    with patch.dict(
        os.environ,
        {
            "MULTI_TENANCY_ENABLED": "true",
            "DEFAULT_TENANT_ID": "default-tenant",
            "ALLOWED_TENANTS": "tenant-a,tenant-b,default-tenant",
        },
    ):
        # Clear any cached config
        from src.core import config as config_module
        if hasattr(config_module, "_tenant_config"):
            config_module._tenant_config = None
        yield
        # Cleanup
        if hasattr(config_module, "_tenant_config"):
            config_module._tenant_config = None


class TestMockAnthologyStoreTenantIsolation:
    """Tests for tenant isolation in MockAnthologyStore."""

    @pytest.mark.asyncio
    async def test_documents_isolated_by_tenant(
        self, mock_store: MockAnthologyStore, multi_tenant_env
    ) -> None:
        """Test that documents indexed by one tenant are not visible to another."""
        doc_a = Document(doc_id="doc-1", content="Tenant A document")
        doc_b = Document(doc_id="doc-1", content="Tenant B document")

        # Index document as tenant A
        with TenantContext.tenant_scope("tenant-a"):
            await mock_store.index_document(doc_a)

        # Index document with same ID as tenant B
        with TenantContext.tenant_scope("tenant-b"):
            await mock_store.index_document(doc_b)

        # Verify tenant A sees their document
        with TenantContext.tenant_scope("tenant-a"):
            result = await mock_store.get_by_id("doc-1")
            assert result is not None
            assert result.content == "Tenant A document"

        # Verify tenant B sees their document
        with TenantContext.tenant_scope("tenant-b"):
            result = await mock_store.get_by_id("doc-1")
            assert result is not None
            assert result.content == "Tenant B document"

    @pytest.mark.asyncio
    async def test_search_only_returns_tenant_documents(
        self, mock_store: MockAnthologyStore, multi_tenant_env
    ) -> None:
        """Test that search only returns documents from current tenant."""
        # Index documents for tenant A
        with TenantContext.tenant_scope("tenant-a"):
            await mock_store.index_document(
                Document(doc_id="a-1", content="Alpha document about cats")
            )
            await mock_store.index_document(
                Document(doc_id="a-2", content="Alpha document about dogs")
            )

        # Index documents for tenant B
        with TenantContext.tenant_scope("tenant-b"):
            await mock_store.index_document(
                Document(doc_id="b-1", content="Beta document about cats")
            )

        # Search as tenant A
        with TenantContext.tenant_scope("tenant-a"):
            results = await mock_store.search("cats", top_k=10)
            doc_ids = [r.doc_id for r in results]
            assert "a-1" in doc_ids
            assert "b-1" not in doc_ids  # Should not see tenant B's document

        # Search as tenant B
        with TenantContext.tenant_scope("tenant-b"):
            results = await mock_store.search("cats", top_k=10)
            doc_ids = [r.doc_id for r in results]
            assert "b-1" in doc_ids
            assert "a-1" not in doc_ids  # Should not see tenant A's document

    @pytest.mark.asyncio
    async def test_delete_only_affects_tenant_documents(
        self, mock_store: MockAnthologyStore, multi_tenant_env
    ) -> None:
        """Test that delete only affects current tenant's documents."""
        # Index same doc_id for both tenants
        with TenantContext.tenant_scope("tenant-a"):
            await mock_store.index_document(
                Document(doc_id="shared-id", content="Tenant A content")
            )

        with TenantContext.tenant_scope("tenant-b"):
            await mock_store.index_document(
                Document(doc_id="shared-id", content="Tenant B content")
            )

        # Delete as tenant A
        with TenantContext.tenant_scope("tenant-a"):
            deleted = await mock_store.delete("shared-id")
            assert deleted is True

        # Verify tenant A's document is gone
        with TenantContext.tenant_scope("tenant-a"):
            result = await mock_store.get_by_id("shared-id")
            assert result is None

        # Verify tenant B's document still exists
        with TenantContext.tenant_scope("tenant-b"):
            result = await mock_store.get_by_id("shared-id")
            assert result is not None
            assert result.content == "Tenant B content"

    @pytest.mark.asyncio
    async def test_health_check_includes_tenant(
        self, mock_store: MockAnthologyStore, multi_tenant_env
    ) -> None:
        """Test that health check reports current tenant."""
        with TenantContext.tenant_scope("tenant-a"):
            health = await mock_store.health_check()
            assert health["tenant"] == "tenant-a"

        with TenantContext.tenant_scope("tenant-b"):
            health = await mock_store.health_check()
            assert health["tenant"] == "tenant-b"

    @pytest.mark.asyncio
    async def test_clear_only_affects_current_tenant(
        self, mock_store: MockAnthologyStore, multi_tenant_env
    ) -> None:
        """Test that clear() only affects current tenant's documents."""
        # Index documents for both tenants
        with TenantContext.tenant_scope("tenant-a"):
            await mock_store.index_document(
                Document(doc_id="doc-a", content="Tenant A")
            )

        with TenantContext.tenant_scope("tenant-b"):
            await mock_store.index_document(
                Document(doc_id="doc-b", content="Tenant B")
            )

        # Clear tenant A's data
        with TenantContext.tenant_scope("tenant-a"):
            mock_store.clear()

        # Verify tenant A's document is gone
        with TenantContext.tenant_scope("tenant-a"):
            result = await mock_store.get_by_id("doc-a")
            assert result is None

        # Verify tenant B's document still exists
        with TenantContext.tenant_scope("tenant-b"):
            result = await mock_store.get_by_id("doc-b")
            assert result is not None

    @pytest.mark.asyncio
    async def test_clear_all_tenants(
        self, mock_store: MockAnthologyStore, multi_tenant_env
    ) -> None:
        """Test that clear(all_tenants=True) clears all data."""
        # Index documents for both tenants
        with TenantContext.tenant_scope("tenant-a"):
            await mock_store.index_document(
                Document(doc_id="doc-a", content="Tenant A")
            )

        with TenantContext.tenant_scope("tenant-b"):
            await mock_store.index_document(
                Document(doc_id="doc-b", content="Tenant B")
            )

        # Clear all tenants
        mock_store.clear(all_tenants=True)

        # Verify both tenants' documents are gone
        with TenantContext.tenant_scope("tenant-a"):
            result = await mock_store.get_by_id("doc-a")
            assert result is None

        with TenantContext.tenant_scope("tenant-b"):
            result = await mock_store.get_by_id("doc-b")
            assert result is None


class TestMockAnthologyStoreSingleTenant:
    """Tests for single-tenant mode (multi-tenancy disabled)."""

    @pytest.mark.asyncio
    async def test_works_without_tenant_context(
        self, mock_store: MockAnthologyStore
    ) -> None:
        """Test store works when multi-tenancy is disabled."""
        doc = Document(doc_id="doc-1", content="Test content")

        # Index without tenant context
        doc_id = await mock_store.index_document(doc)
        assert doc_id == "doc-1"

        # Retrieve without tenant context
        result = await mock_store.get_by_id("doc-1")
        assert result is not None
        assert result.content == "Test content"

    @pytest.mark.asyncio
    async def test_search_works_without_tenant_context(
        self, mock_store: MockAnthologyStore
    ) -> None:
        """Test search works when multi-tenancy is disabled."""
        await mock_store.index_document(
            Document(doc_id="doc-1", content="Hello world")
        )

        results = await mock_store.search("hello", top_k=5)
        assert len(results) > 0
        assert results[0].doc_id == "doc-1"

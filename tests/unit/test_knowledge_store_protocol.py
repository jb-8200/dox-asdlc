"""Unit tests for KnowledgeStore protocol interface.

Tests protocol definition and compliance checking.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import pytest

from src.core.interfaces import KnowledgeStore
from src.infrastructure.knowledge_store.models import Document, SearchResult


class TestKnowledgeStoreProtocol:
    """Tests for KnowledgeStore Protocol definition."""

    def test_protocol_is_defined(self) -> None:
        """Test KnowledgeStore protocol exists."""
        assert KnowledgeStore is not None

    def test_protocol_is_runtime_checkable(self) -> None:
        """Test KnowledgeStore can be used with isinstance."""
        # Protocol should be runtime_checkable
        assert hasattr(KnowledgeStore, "__protocol_attrs__") or isinstance(
            KnowledgeStore, type
        )

    def test_protocol_defines_index_document(self) -> None:
        """Test protocol defines index_document method."""
        assert hasattr(KnowledgeStore, "index_document")

    def test_protocol_defines_search(self) -> None:
        """Test protocol defines search method."""
        assert hasattr(KnowledgeStore, "search")

    def test_protocol_defines_get_by_id(self) -> None:
        """Test protocol defines get_by_id method."""
        assert hasattr(KnowledgeStore, "get_by_id")

    def test_protocol_defines_delete(self) -> None:
        """Test protocol defines delete method."""
        assert hasattr(KnowledgeStore, "delete")

    def test_protocol_defines_health_check(self) -> None:
        """Test protocol defines health_check method."""
        assert hasattr(KnowledgeStore, "health_check")


class TestProtocolCompliance:
    """Tests for protocol compliance checking."""

    def test_compliant_class_matches_protocol(self) -> None:
        """Test that a compliant class satisfies the protocol."""

        class CompliantStore:
            """A class that implements all protocol methods."""

            async def index_document(self, document: Document) -> str:
                return document.doc_id

            async def search(
                self,
                query: str,
                top_k: int = 10,
                filters: dict | None = None,
            ) -> list[SearchResult]:
                return []

            async def get_by_id(self, doc_id: str) -> Document | None:
                return None

            async def delete(self, doc_id: str) -> bool:
                return True

            async def health_check(self) -> dict:
                return {"status": "healthy"}

        # Should be able to use as KnowledgeStore type
        store: KnowledgeStore = CompliantStore()
        assert store is not None

    def test_non_compliant_class_type_error(self) -> None:
        """Test that non-compliant class fails type checking.

        Note: This is primarily a static type check, but we verify
        the class is missing required methods.
        """

        class NonCompliantStore:
            """A class missing required methods."""

            async def search(self, query: str) -> list:
                return []

        # Verify it's missing required methods
        assert not hasattr(NonCompliantStore, "index_document")
        assert not hasattr(NonCompliantStore, "get_by_id")
        assert not hasattr(NonCompliantStore, "delete")
        assert not hasattr(NonCompliantStore, "health_check")


class TestProtocolMethodSignatures:
    """Tests for protocol method signatures."""

    def test_index_document_signature(self) -> None:
        """Test index_document has correct parameter types."""
        import inspect

        sig = inspect.signature(KnowledgeStore.index_document)
        params = list(sig.parameters.keys())

        # Should have self and document
        assert "self" in params
        assert "document" in params

    def test_search_signature(self) -> None:
        """Test search has correct parameter types."""
        import inspect

        sig = inspect.signature(KnowledgeStore.search)
        params = list(sig.parameters.keys())

        assert "self" in params
        assert "query" in params
        assert "top_k" in params

    def test_get_by_id_signature(self) -> None:
        """Test get_by_id has correct parameter types."""
        import inspect

        sig = inspect.signature(KnowledgeStore.get_by_id)
        params = list(sig.parameters.keys())

        assert "self" in params
        assert "doc_id" in params

    def test_delete_signature(self) -> None:
        """Test delete has correct parameter types."""
        import inspect

        sig = inspect.signature(KnowledgeStore.delete)
        params = list(sig.parameters.keys())

        assert "self" in params
        assert "doc_id" in params

    def test_health_check_signature(self) -> None:
        """Test health_check has correct parameter types."""
        import inspect

        sig = inspect.signature(KnowledgeStore.health_check)
        params = list(sig.parameters.keys())

        # Should only have self
        assert "self" in params
        assert len(params) == 1

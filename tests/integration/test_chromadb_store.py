"""Integration tests for ChromaDB knowledge store.

These tests require a running ChromaDB instance.
Run with: docker compose up chromadb -d
"""

from __future__ import annotations

import os
import uuid

import pytest

# Skip all tests if ChromaDB is not available
pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_CHROMADB_TESTS", "true").lower() == "true",
    reason="ChromaDB not available. Set SKIP_CHROMADB_TESTS=false to run.",
)


@pytest.fixture
def test_config():
    """Create test configuration for ChromaDB."""
    from src.infrastructure.knowledge_store.config import KnowledgeStoreConfig

    return KnowledgeStoreConfig(
        host=os.getenv("KNOWLEDGE_STORE_HOST", "localhost"),
        port=int(os.getenv("KNOWLEDGE_STORE_PORT", "8000")),
        collection_name=f"test_collection_{uuid.uuid4().hex[:8]}",
        embedding_model="all-MiniLM-L6-v2",
    )


@pytest.fixture
async def store(test_config):
    """Create a ChromaDBStore instance for testing."""
    from src.infrastructure.knowledge_store.chromadb_store import ChromaDBStore

    store = ChromaDBStore(test_config)
    yield store

    # Cleanup: delete the test collection
    try:
        store._client.delete_collection(test_config.collection_name)
    except Exception:
        pass


class TestChromaDBIntegration:
    """Integration tests for ChromaDB store."""

    @pytest.mark.asyncio
    async def test_index_and_retrieve_document(self, store) -> None:
        """Test indexing a document and retrieving it by ID."""
        from src.infrastructure.knowledge_store.models import Document

        doc = Document(
            doc_id="test-doc-1",
            content="This is a test document about machine learning.",
            metadata={"author": "test", "category": "ml"},
        )

        # Index the document
        result_id = await store.index_document(doc)
        assert result_id == "test-doc-1"

        # Retrieve by ID
        retrieved = await store.get_by_id("test-doc-1")
        assert retrieved is not None
        assert retrieved.doc_id == "test-doc-1"
        assert retrieved.content == doc.content
        assert retrieved.metadata["author"] == "test"

    @pytest.mark.asyncio
    async def test_search_returns_relevant_results(self, store) -> None:
        """Test semantic search returns relevant documents."""
        from src.infrastructure.knowledge_store.models import Document

        # Index multiple documents
        docs = [
            Document(
                doc_id="ml-doc",
                content="Machine learning is a subset of artificial intelligence.",
                metadata={"topic": "ml"},
            ),
            Document(
                doc_id="cooking-doc",
                content="The best way to cook pasta is in salted boiling water.",
                metadata={"topic": "cooking"},
            ),
            Document(
                doc_id="ai-doc",
                content="Deep learning uses neural networks with many layers.",
                metadata={"topic": "ai"},
            ),
        ]

        for doc in docs:
            await store.index_document(doc)

        # Search for AI-related content
        results = await store.search("artificial intelligence neural networks", top_k=3)

        assert len(results) > 0
        # ML and AI docs should rank higher than cooking doc
        doc_ids = [r.doc_id for r in results]
        assert "cooking-doc" not in doc_ids[:2]  # Cooking should not be top 2

    @pytest.mark.asyncio
    async def test_search_with_metadata_filter(self, store) -> None:
        """Test search with metadata filtering."""
        from src.infrastructure.knowledge_store.models import Document

        docs = [
            Document(
                doc_id="python-doc",
                content="Python is a popular programming language.",
                metadata={"language": "python"},
            ),
            Document(
                doc_id="java-doc",
                content="Java is also a popular programming language.",
                metadata={"language": "java"},
            ),
        ]

        for doc in docs:
            await store.index_document(doc)

        # Search with filter
        results = await store.search(
            "programming language",
            top_k=5,
            filters={"language": "python"},
        )

        assert len(results) == 1
        assert results[0].doc_id == "python-doc"

    @pytest.mark.asyncio
    async def test_update_document(self, store) -> None:
        """Test updating an existing document."""
        from src.infrastructure.knowledge_store.models import Document

        # Index original
        doc = Document(
            doc_id="update-test",
            content="Original content",
            metadata={"version": "1"},
        )
        await store.index_document(doc)

        # Update (upsert)
        updated_doc = Document(
            doc_id="update-test",
            content="Updated content with new information",
            metadata={"version": "2"},
        )
        await store.index_document(updated_doc)

        # Verify update
        retrieved = await store.get_by_id("update-test")
        assert retrieved is not None
        assert "Updated content" in retrieved.content
        assert retrieved.metadata["version"] == "2"

    @pytest.mark.asyncio
    async def test_delete_document(self, store) -> None:
        """Test deleting a document."""
        from src.infrastructure.knowledge_store.models import Document

        doc = Document(
            doc_id="delete-test",
            content="This document will be deleted.",
        )
        await store.index_document(doc)

        # Verify it exists
        assert await store.get_by_id("delete-test") is not None

        # Delete
        result = await store.delete("delete-test")
        assert result is True

        # Verify deleted
        assert await store.get_by_id("delete-test") is None

        # Delete again should return False
        result = await store.delete("delete-test")
        assert result is False

    @pytest.mark.asyncio
    async def test_health_check(self, store) -> None:
        """Test health check returns healthy status."""
        health = await store.health_check()

        assert health["status"] == "healthy"
        assert health["backend"] == "chromadb"
        assert "heartbeat" in health

    @pytest.mark.asyncio
    async def test_search_empty_results(self, store) -> None:
        """Test search with no matching documents."""
        results = await store.search("xyzzy nonexistent query 12345", top_k=5)
        assert results == []

    @pytest.mark.asyncio
    async def test_get_nonexistent_document(self, store) -> None:
        """Test getting a document that doesn't exist."""
        result = await store.get_by_id("nonexistent-doc-id")
        assert result is None


class TestChromaDBConcurrency:
    """Tests for concurrent operations."""

    @pytest.mark.asyncio
    async def test_concurrent_indexing(self, store) -> None:
        """Test concurrent document indexing."""
        import asyncio

        from src.infrastructure.knowledge_store.models import Document

        async def index_doc(i: int) -> str:
            doc = Document(
                doc_id=f"concurrent-{i}",
                content=f"Document number {i} for concurrency testing.",
            )
            return await store.index_document(doc)

        # Index 10 documents concurrently
        tasks = [index_doc(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert all(r.startswith("concurrent-") for r in results)

        # Verify all were indexed
        for i in range(10):
            doc = await store.get_by_id(f"concurrent-{i}")
            assert doc is not None

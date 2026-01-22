"""Tests for MockAnthologyStore (P06-F03)."""

import pytest

from src.infrastructure.knowledge_store.config import KnowledgeStoreConfig
from src.infrastructure.knowledge_store.mock_anthology import MockAnthologyStore
from src.infrastructure.knowledge_store.models import Document


class TestMockAnthologyStore:
    """Test the MockAnthologyStore implementation."""

    @pytest.fixture
    def config(self) -> KnowledgeStoreConfig:
        """Create test configuration."""
        return KnowledgeStoreConfig(backend="mock_anthology")

    @pytest.fixture
    def store(self, config: KnowledgeStoreConfig) -> MockAnthologyStore:
        """Create test store instance."""
        return MockAnthologyStore(config)

    @pytest.mark.asyncio
    async def test_index_document(self, store: MockAnthologyStore) -> None:
        """Test indexing a document."""
        doc = Document(doc_id="test-1", content="Hello world")
        result = await store.index_document(doc)

        assert result == "test-1"
        assert "test-1" in store._documents

    @pytest.mark.asyncio
    async def test_index_document_with_metadata(
        self, store: MockAnthologyStore
    ) -> None:
        """Test indexing a document with metadata."""
        doc = Document(
            doc_id="test-2",
            content="Test content",
            metadata={"type": "test", "version": 1},
        )
        result = await store.index_document(doc)

        assert result == "test-2"
        stored_doc = store._documents["test-2"]
        assert stored_doc.metadata["type"] == "test"

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, store: MockAnthologyStore) -> None:
        """Test retrieving an existing document."""
        doc = Document(doc_id="test-3", content="Get me")
        await store.index_document(doc)

        result = await store.get_by_id("test-3")

        assert result is not None
        assert result.doc_id == "test-3"
        assert result.content == "Get me"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, store: MockAnthologyStore) -> None:
        """Test retrieving a non-existent document."""
        result = await store.get_by_id("non-existent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_existing(self, store: MockAnthologyStore) -> None:
        """Test deleting an existing document."""
        doc = Document(doc_id="test-4", content="Delete me")
        await store.index_document(doc)

        result = await store.delete("test-4")

        assert result is True
        assert "test-4" not in store._documents

    @pytest.mark.asyncio
    async def test_delete_non_existent(self, store: MockAnthologyStore) -> None:
        """Test deleting a non-existent document."""
        result = await store.delete("non-existent")
        assert result is False

    @pytest.mark.asyncio
    async def test_search_empty_store(self, store: MockAnthologyStore) -> None:
        """Test searching in an empty store."""
        results = await store.search("query", top_k=5)
        assert results == []

    @pytest.mark.asyncio
    async def test_search_returns_results(
        self, store: MockAnthologyStore
    ) -> None:
        """Test that search returns results."""
        # Index some documents
        await store.index_document(Document(doc_id="d1", content="Python programming"))
        await store.index_document(Document(doc_id="d2", content="Java programming"))
        await store.index_document(Document(doc_id="d3", content="Python tutorials"))

        results = await store.search("Python", top_k=10)

        assert len(results) == 3
        # Results should be ordered by relevance
        assert all(r.score >= 0 for r in results)

    @pytest.mark.asyncio
    async def test_search_respects_top_k(
        self, store: MockAnthologyStore
    ) -> None:
        """Test that search respects top_k limit."""
        # Index 5 documents
        for i in range(5):
            await store.index_document(
                Document(doc_id=f"d{i}", content=f"Document {i}")
            )

        results = await store.search("Document", top_k=2)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_with_filters(
        self, store: MockAnthologyStore
    ) -> None:
        """Test that search respects metadata filters."""
        await store.index_document(
            Document(doc_id="d1", content="Python code", metadata={"lang": "python"})
        )
        await store.index_document(
            Document(doc_id="d2", content="Java code", metadata={"lang": "java"})
        )

        results = await store.search("code", filters={"lang": "python"})

        assert len(results) == 1
        assert results[0].doc_id == "d1"

    @pytest.mark.asyncio
    async def test_health_check(self, store: MockAnthologyStore) -> None:
        """Test health check returns expected format."""
        health = await store.health_check()

        assert health["status"] == "healthy"
        assert health["backend"] == "mock_anthology"
        assert "document_count" in health
        assert "timestamp" in health

    @pytest.mark.asyncio
    async def test_health_check_document_count(
        self, store: MockAnthologyStore
    ) -> None:
        """Test that health check reports correct document count."""
        await store.index_document(Document(doc_id="d1", content="One"))
        await store.index_document(Document(doc_id="d2", content="Two"))

        health = await store.health_check()
        assert health["document_count"] == 2

    def test_clear(self, store: MockAnthologyStore) -> None:
        """Test clearing all documents."""
        store._documents["test"] = Document(doc_id="test", content="test")
        store._embeddings["test"] = [0.1, 0.2]

        store.clear()

        assert len(store._documents) == 0
        assert len(store._embeddings) == 0

    @pytest.mark.asyncio
    async def test_deterministic_embeddings(
        self, store: MockAnthologyStore
    ) -> None:
        """Test that same text produces same embedding."""
        text = "Test text for embedding"

        embedding1 = store._generate_embedding(text)
        embedding2 = store._generate_embedding(text)

        assert (embedding1 == embedding2).all()

    @pytest.mark.asyncio
    async def test_update_existing_document(
        self, store: MockAnthologyStore
    ) -> None:
        """Test that re-indexing updates the document."""
        doc_v1 = Document(doc_id="doc", content="Version 1")
        doc_v2 = Document(doc_id="doc", content="Version 2")

        await store.index_document(doc_v1)
        await store.index_document(doc_v2)

        result = await store.get_by_id("doc")
        assert result is not None
        assert result.content == "Version 2"

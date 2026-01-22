"""Unit tests for KnowledgeStore data models.

Tests Document and SearchResult dataclasses.
"""

from __future__ import annotations

import json

import pytest

from src.infrastructure.knowledge_store.models import Document, SearchResult


class TestDocument:
    """Tests for Document dataclass."""

    def test_document_creation_with_all_fields(self) -> None:
        """Test Document creation with all fields."""
        embedding = [0.1, 0.2, 0.3]
        metadata = {"author": "test", "version": 1}

        doc = Document(
            doc_id="doc-123",
            content="Test content",
            metadata=metadata,
            embedding=embedding,
        )

        assert doc.doc_id == "doc-123"
        assert doc.content == "Test content"
        assert doc.metadata == metadata
        assert doc.embedding == embedding

    def test_document_creation_minimal(self) -> None:
        """Test Document creation with minimal fields."""
        doc = Document(
            doc_id="doc-456",
            content="Minimal content",
        )

        assert doc.doc_id == "doc-456"
        assert doc.content == "Minimal content"
        assert doc.metadata == {}
        assert doc.embedding is None

    def test_document_is_immutable(self) -> None:
        """Test Document is frozen (immutable)."""
        doc = Document(doc_id="doc-1", content="test")

        with pytest.raises(AttributeError):
            doc.doc_id = "new-id"  # type: ignore[misc]

    def test_document_metadata_types(self) -> None:
        """Test Document metadata supports various types."""
        metadata = {
            "str_val": "string",
            "int_val": 42,
            "float_val": 3.14,
            "bool_val": True,
        }

        doc = Document(
            doc_id="doc-1",
            content="test",
            metadata=metadata,
        )

        assert doc.metadata["str_val"] == "string"
        assert doc.metadata["int_val"] == 42
        assert doc.metadata["float_val"] == 3.14
        assert doc.metadata["bool_val"] is True

    def test_document_to_dict(self) -> None:
        """Test Document to_dict serialization."""
        doc = Document(
            doc_id="doc-1",
            content="test content",
            metadata={"key": "value"},
            embedding=[0.1, 0.2],
        )

        result = doc.to_dict()

        assert result["doc_id"] == "doc-1"
        assert result["content"] == "test content"
        assert result["metadata"] == {"key": "value"}
        assert result["embedding"] == [0.1, 0.2]

    def test_document_to_dict_without_embedding(self) -> None:
        """Test Document to_dict without embedding."""
        doc = Document(doc_id="doc-1", content="test")

        result = doc.to_dict()

        assert result["doc_id"] == "doc-1"
        assert result["embedding"] is None

    def test_document_json_serialization(self) -> None:
        """Test Document can be JSON serialized via to_dict."""
        doc = Document(
            doc_id="doc-1",
            content="test",
            metadata={"key": "value"},
            embedding=[0.5],
        )

        # Should not raise
        json_str = json.dumps(doc.to_dict())
        parsed = json.loads(json_str)

        assert parsed["doc_id"] == "doc-1"

    def test_document_from_dict(self) -> None:
        """Test Document creation from dictionary."""
        data = {
            "doc_id": "doc-1",
            "content": "test content",
            "metadata": {"key": "value"},
            "embedding": [0.1, 0.2],
        }

        doc = Document.from_dict(data)

        assert doc.doc_id == "doc-1"
        assert doc.content == "test content"
        assert doc.metadata == {"key": "value"}
        assert doc.embedding == [0.1, 0.2]

    def test_document_from_dict_minimal(self) -> None:
        """Test Document creation from minimal dictionary."""
        data = {"doc_id": "doc-1", "content": "test"}

        doc = Document.from_dict(data)

        assert doc.doc_id == "doc-1"
        assert doc.metadata == {}
        assert doc.embedding is None


class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_search_result_creation(self) -> None:
        """Test SearchResult creation with all fields."""
        result = SearchResult(
            doc_id="doc-1",
            content="Found content",
            metadata={"type": "article"},
            score=0.95,
            source="chromadb",
        )

        assert result.doc_id == "doc-1"
        assert result.content == "Found content"
        assert result.metadata == {"type": "article"}
        assert result.score == 0.95
        assert result.source == "chromadb"

    def test_search_result_minimal(self) -> None:
        """Test SearchResult creation with minimal fields."""
        result = SearchResult(
            doc_id="doc-1",
            content="content",
            score=0.8,
        )

        assert result.doc_id == "doc-1"
        assert result.metadata == {}
        assert result.source is None

    def test_search_result_is_immutable(self) -> None:
        """Test SearchResult is frozen (immutable)."""
        result = SearchResult(doc_id="doc-1", content="test", score=0.9)

        with pytest.raises(AttributeError):
            result.score = 0.5  # type: ignore[misc]

    def test_search_result_score_validation(self) -> None:
        """Test SearchResult score is a valid float."""
        result = SearchResult(doc_id="doc-1", content="test", score=0.5)
        assert isinstance(result.score, float)

    def test_search_result_to_dict(self) -> None:
        """Test SearchResult to_dict serialization."""
        result = SearchResult(
            doc_id="doc-1",
            content="test",
            metadata={"key": "value"},
            score=0.85,
            source="chromadb",
        )

        data = result.to_dict()

        assert data["doc_id"] == "doc-1"
        assert data["content"] == "test"
        assert data["metadata"] == {"key": "value"}
        assert data["score"] == 0.85
        assert data["source"] == "chromadb"

    def test_search_result_json_serialization(self) -> None:
        """Test SearchResult can be JSON serialized via to_dict."""
        result = SearchResult(
            doc_id="doc-1",
            content="test",
            score=0.9,
        )

        # Should not raise
        json_str = json.dumps(result.to_dict())
        parsed = json.loads(json_str)

        assert parsed["doc_id"] == "doc-1"
        assert parsed["score"] == 0.9

    def test_search_result_from_dict(self) -> None:
        """Test SearchResult creation from dictionary."""
        data = {
            "doc_id": "doc-1",
            "content": "test",
            "metadata": {"key": "value"},
            "score": 0.85,
            "source": "chromadb",
        }

        result = SearchResult.from_dict(data)

        assert result.doc_id == "doc-1"
        assert result.score == 0.85
        assert result.source == "chromadb"


class TestModelEquality:
    """Tests for model equality and hashing."""

    def test_document_equality(self) -> None:
        """Test Document equality comparison."""
        doc1 = Document(doc_id="doc-1", content="test")
        doc2 = Document(doc_id="doc-1", content="test")

        assert doc1 == doc2

    def test_document_inequality(self) -> None:
        """Test Document inequality comparison."""
        doc1 = Document(doc_id="doc-1", content="test")
        doc2 = Document(doc_id="doc-2", content="test")

        assert doc1 != doc2

    def test_search_result_equality(self) -> None:
        """Test SearchResult equality comparison."""
        r1 = SearchResult(doc_id="doc-1", content="test", score=0.9)
        r2 = SearchResult(doc_id="doc-1", content="test", score=0.9)

        assert r1 == r2

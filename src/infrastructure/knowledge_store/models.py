"""Data models for KnowledgeStore operations.

Provides Document and SearchResult dataclasses for knowledge store interactions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Type alias for metadata values
MetadataValue = str | int | float | bool
Metadata = dict[str, MetadataValue]


@dataclass(frozen=True)
class Document:
    """Represents a document in the knowledge store.

    Attributes:
        doc_id: Unique identifier for the document.
        content: Text content of the document.
        metadata: Additional metadata (str, int, float, bool values).
        embedding: Optional pre-computed embedding vector.
    """

    doc_id: str
    content: str
    metadata: Metadata = field(default_factory=dict)
    embedding: list[float] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert document to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the document.
        """
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "metadata": self.metadata,
            "embedding": self.embedding,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Document:
        """Create a Document from a dictionary.

        Args:
            data: Dictionary containing document fields.

        Returns:
            Document instance.
        """
        return cls(
            doc_id=data["doc_id"],
            content=data["content"],
            metadata=data.get("metadata", {}),
            embedding=data.get("embedding"),
        )


@dataclass(frozen=True)
class SearchResult:
    """Represents a search result from the knowledge store.

    Attributes:
        doc_id: Unique identifier of the matching document.
        content: Text content of the matching document.
        score: Relevance score (higher is more relevant).
        metadata: Document metadata.
        source: Optional source identifier (e.g., backend name).
    """

    doc_id: str
    content: str
    score: float
    metadata: Metadata = field(default_factory=dict)
    source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert search result to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the search result.
        """
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "metadata": self.metadata,
            "score": self.score,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SearchResult:
        """Create a SearchResult from a dictionary.

        Args:
            data: Dictionary containing search result fields.

        Returns:
            SearchResult instance.
        """
        return cls(
            doc_id=data["doc_id"],
            content=data["content"],
            score=data["score"],
            metadata=data.get("metadata", {}),
            source=data.get("source"),
        )

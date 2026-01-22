"""Mock Anthology Store implementation for testing.

Provides an in-memory implementation of the KnowledgeStore protocol
for testing and development without requiring ChromaDB or external services.
This simulates the behavior of an enterprise search service like Anthology.
"""

from __future__ import annotations

import hashlib
import logging
import time
from typing import Any

import numpy as np

from src.infrastructure.knowledge_store.config import KnowledgeStoreConfig
from src.infrastructure.knowledge_store.models import Document, SearchResult

logger = logging.getLogger(__name__)


class MockAnthologyStore:
    """In-memory mock implementation of the KnowledgeStore protocol.

    Simulates an enterprise knowledge store (like Anthology) for testing
    the anthology replacement path without external dependencies.

    Features:
        - In-memory document storage
        - Simple cosine similarity search using random embeddings
        - No external dependencies required
        - Useful for unit tests and local development

    Example:
        ```python
        from src.infrastructure.knowledge_store.mock_anthology import MockAnthologyStore
        from src.infrastructure.knowledge_store.config import KnowledgeStoreConfig

        config = KnowledgeStoreConfig(backend="mock_anthology")
        store = MockAnthologyStore(config)

        # Index a document
        doc = Document(doc_id="doc-1", content="Hello world")
        await store.index_document(doc)

        # Search
        results = await store.search("greeting", top_k=5)
        ```
    """

    def __init__(self, config: KnowledgeStoreConfig) -> None:
        """Initialize the mock anthology store.

        Args:
            config: Configuration for the store.
        """
        self._config = config
        self._documents: dict[str, Document] = {}
        self._embeddings: dict[str, np.ndarray] = {}
        self._embedding_dim = 384  # Simulated embedding dimension

        logger.info(
            "MockAnthologyStore initialized (in-memory, for testing only)"
        )

    def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate a deterministic pseudo-embedding for text.

        Uses a hash-based approach to generate consistent embeddings
        for the same text, enabling reproducible test behavior.

        Args:
            text: The text to embed.

        Returns:
            A numpy array representing the embedding.
        """
        # Use hash to generate deterministic "embedding"
        hash_bytes = hashlib.sha256(text.encode()).digest()
        # Expand hash to embedding dimension
        rng = np.random.default_rng(int.from_bytes(hash_bytes[:8], "big"))
        embedding = rng.random(self._embedding_dim).astype(np.float32)
        # Normalize to unit vector
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors.

        Args:
            a: First vector.
            b: Second vector.

        Returns:
            Cosine similarity score between -1 and 1.
        """
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot_product / (norm_a * norm_b))

    async def index_document(self, document: Document) -> str:
        """Index a document in the mock store.

        Args:
            document: The document to index.

        Returns:
            The doc_id of the indexed document.
        """
        self._documents[document.doc_id] = document
        self._embeddings[document.doc_id] = self._generate_embedding(
            document.content
        )

        logger.debug(
            f"MockAnthologyStore: Indexed document {document.doc_id}"
        )
        return document.doc_id

    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search for documents similar to the query.

        Args:
            query: The search query text.
            top_k: Maximum number of results to return.
            filters: Optional metadata filters to apply.

        Returns:
            List of SearchResult objects, ordered by relevance.
        """
        if not self._documents:
            return []

        query_embedding = self._generate_embedding(query)

        # Calculate similarities
        scores: list[tuple[str, float]] = []
        for doc_id, doc_embedding in self._embeddings.items():
            doc = self._documents[doc_id]

            # Apply filters if provided
            if filters:
                match = True
                for key, value in filters.items():
                    if key not in doc.metadata or doc.metadata[key] != value:
                        match = False
                        break
                if not match:
                    continue

            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            scores.append((doc_id, similarity))

        # Sort by similarity (descending) and take top_k
        scores.sort(key=lambda x: x[1], reverse=True)
        top_results = scores[:top_k]

        # Build SearchResult objects
        results = []
        for doc_id, score in top_results:
            doc = self._documents[doc_id]
            results.append(
                SearchResult(
                    doc_id=doc_id,
                    content=doc.content,
                    score=score,
                    metadata=doc.metadata,
                )
            )

        logger.debug(
            f"MockAnthologyStore: Search for '{query}' returned {len(results)} results"
        )
        return results

    async def get_by_id(self, doc_id: str) -> Document | None:
        """Retrieve a document by its ID.

        Args:
            doc_id: The unique identifier of the document.

        Returns:
            The Document if found, None otherwise.
        """
        return self._documents.get(doc_id)

    async def delete(self, doc_id: str) -> bool:
        """Delete a document from the mock store.

        Args:
            doc_id: The unique identifier of the document to delete.

        Returns:
            True if the document was deleted, False if not found.
        """
        if doc_id in self._documents:
            del self._documents[doc_id]
            del self._embeddings[doc_id]
            logger.debug(f"MockAnthologyStore: Deleted document {doc_id}")
            return True
        return False

    async def health_check(self) -> dict[str, Any]:
        """Check the health of the mock store.

        Returns:
            Dictionary with health status information.
        """
        return {
            "status": "healthy",
            "backend": "mock_anthology",
            "document_count": len(self._documents),
            "timestamp": time.time(),
        }

    def clear(self) -> None:
        """Clear all documents from the store.

        Useful for test cleanup.
        """
        self._documents.clear()
        self._embeddings.clear()
        logger.debug("MockAnthologyStore: Cleared all documents")

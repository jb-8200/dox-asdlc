"""Mock Anthology Store implementation for testing.

Provides an in-memory implementation of the KnowledgeStore protocol
for testing and development without requiring ChromaDB or external services.
This simulates the behavior of an enterprise search service like Anthology.
Supports multi-tenancy through tenant-prefixed storage.
"""

from __future__ import annotations

import hashlib
import logging
import time
from typing import Any

import numpy as np

from src.core.config import get_tenant_config
from src.core.tenant import TenantContext
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
        # Tenant-keyed storage: {tenant_id: {doc_id: Document}}
        self._tenant_documents: dict[str, dict[str, Document]] = {}
        self._tenant_embeddings: dict[str, dict[str, np.ndarray]] = {}
        self._embedding_dim = 384  # Simulated embedding dimension

        logger.info(
            "MockAnthologyStore initialized (in-memory, for testing only)"
        )

    def _get_tenant_key(self) -> str:
        """Get the tenant key for current context.

        Returns:
            str: The tenant ID or default tenant.
        """
        tenant_config = get_tenant_config()
        if tenant_config.enabled:
            try:
                return TenantContext.get_current_tenant()
            except Exception:
                return tenant_config.default_tenant
        return "_default"

    def _get_documents(self) -> dict[str, Document]:
        """Get documents dict for current tenant."""
        tenant = self._get_tenant_key()
        if tenant not in self._tenant_documents:
            self._tenant_documents[tenant] = {}
        return self._tenant_documents[tenant]

    def _get_embeddings(self) -> dict[str, np.ndarray]:
        """Get embeddings dict for current tenant."""
        tenant = self._get_tenant_key()
        if tenant not in self._tenant_embeddings:
            self._tenant_embeddings[tenant] = {}
        return self._tenant_embeddings[tenant]

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

        Uses tenant-specific storage in multi-tenant mode.

        Args:
            document: The document to index.

        Returns:
            The doc_id of the indexed document.
        """
        documents = self._get_documents()
        embeddings = self._get_embeddings()

        documents[document.doc_id] = document
        embeddings[document.doc_id] = self._generate_embedding(
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

        Uses tenant-specific storage in multi-tenant mode.

        Args:
            query: The search query text.
            top_k: Maximum number of results to return.
            filters: Optional metadata filters to apply.

        Returns:
            List of SearchResult objects, ordered by relevance.
        """
        documents = self._get_documents()
        embeddings = self._get_embeddings()

        if not documents:
            return []

        query_embedding = self._generate_embedding(query)

        # Calculate similarities
        scores: list[tuple[str, float]] = []
        for doc_id, doc_embedding in embeddings.items():
            doc = documents[doc_id]

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
            doc = documents[doc_id]
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

        Uses tenant-specific storage in multi-tenant mode.

        Args:
            doc_id: The unique identifier of the document.

        Returns:
            The Document if found, None otherwise.
        """
        documents = self._get_documents()
        return documents.get(doc_id)

    async def delete(self, doc_id: str) -> bool:
        """Delete a document from the mock store.

        Uses tenant-specific storage in multi-tenant mode.

        Args:
            doc_id: The unique identifier of the document to delete.

        Returns:
            True if the document was deleted, False if not found.
        """
        documents = self._get_documents()
        embeddings = self._get_embeddings()

        if doc_id in documents:
            del documents[doc_id]
            del embeddings[doc_id]
            logger.debug(f"MockAnthologyStore: Deleted document {doc_id}")
            return True
        return False

    async def health_check(self) -> dict[str, Any]:
        """Check the health of the mock store.

        Returns:
            Dictionary with health status information.
        """
        documents = self._get_documents()
        tenant = self._get_tenant_key()
        return {
            "status": "healthy",
            "backend": "mock_anthology",
            "tenant": tenant,
            "document_count": len(documents),
            "timestamp": time.time(),
        }

    def clear(self, all_tenants: bool = False) -> None:
        """Clear documents from the store.

        Args:
            all_tenants: If True, clears all tenant data. If False, only
                clears current tenant's data. Useful for test cleanup.
        """
        if all_tenants:
            self._tenant_documents.clear()
            self._tenant_embeddings.clear()
            logger.debug("MockAnthologyStore: Cleared all tenant documents")
        else:
            tenant = self._get_tenant_key()
            if tenant in self._tenant_documents:
                self._tenant_documents[tenant].clear()
            if tenant in self._tenant_embeddings:
                self._tenant_embeddings[tenant].clear()
            logger.debug(f"MockAnthologyStore: Cleared documents for tenant {tenant}")

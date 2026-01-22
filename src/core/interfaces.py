"""Protocol interfaces for aSDLC components.

Defines abstract interfaces that concrete implementations must follow.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from src.infrastructure.knowledge_store.models import Document, SearchResult


@runtime_checkable
class KnowledgeStore(Protocol):
    """Protocol for knowledge store backends.

    Defines the interface that all knowledge store implementations must follow.
    This enables swapping backends (e.g., ChromaDB, Pinecone) without changing
    calling code.

    All methods are async to support non-blocking I/O operations.

    Example:
        ```python
        async def example(store: KnowledgeStore) -> None:
            # Index a document
            doc = Document(doc_id="doc-1", content="Hello world")
            await store.index_document(doc)

            # Search for similar documents
            results = await store.search("greeting", top_k=5)

            # Get specific document
            doc = await store.get_by_id("doc-1")

            # Delete document
            await store.delete("doc-1")

            # Check health
            health = await store.health_check()
        ```
    """

    async def index_document(self, document: Document) -> str:
        """Index a document in the knowledge store.

        If a document with the same doc_id exists, it will be updated.

        Args:
            document: The document to index.

        Returns:
            The doc_id of the indexed document.

        Raises:
            IndexingError: If indexing fails.
            EmbeddingError: If embedding generation fails.
            BackendConnectionError: If connection to backend fails.
        """
        ...

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
            List of SearchResult objects, ordered by relevance (highest first).

        Raises:
            SearchError: If the search operation fails.
            EmbeddingError: If query embedding generation fails.
            BackendConnectionError: If connection to backend fails.
        """
        ...

    async def get_by_id(self, doc_id: str) -> Document | None:
        """Retrieve a document by its ID.

        Args:
            doc_id: The unique identifier of the document.

        Returns:
            The Document if found, None otherwise.

        Raises:
            BackendConnectionError: If connection to backend fails.
        """
        ...

    async def delete(self, doc_id: str) -> bool:
        """Delete a document from the knowledge store.

        Args:
            doc_id: The unique identifier of the document to delete.

        Returns:
            True if the document was deleted, False if not found.

        Raises:
            BackendConnectionError: If connection to backend fails.
        """
        ...

    async def health_check(self) -> dict[str, Any]:
        """Check the health of the knowledge store backend.

        Returns:
            Dictionary with health status information:
                - status: "healthy" or "unhealthy"
                - backend: Name of the backend
                - Additional backend-specific details

        Raises:
            BackendConnectionError: If health check fails due to connection issues.
        """
        ...

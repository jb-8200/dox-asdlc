"""ChromaDB implementation of the KnowledgeStore interface.

Provides vector storage and semantic search using ChromaDB backend.
"""

from __future__ import annotations

import logging
from typing import Any

import chromadb

from src.core.exceptions import (
    BackendConnectionError,
    IndexingError,
    SearchError,
)
from src.infrastructure.knowledge_store.config import KnowledgeStoreConfig
from src.infrastructure.knowledge_store.models import Document, SearchResult

logger = logging.getLogger(__name__)


class ChromaDBStore:
    """ChromaDB implementation of KnowledgeStore protocol.

    Connects to a ChromaDB instance via HTTP and provides document
    indexing, semantic search, and retrieval operations.

    Attributes:
        config: Configuration for the ChromaDB connection.

    Example:
        ```python
        config = KnowledgeStoreConfig.from_env()
        store = ChromaDBStore(config)

        # Index a document
        doc = Document(doc_id="doc-1", content="Hello world")
        await store.index_document(doc)

        # Search
        results = await store.search("greeting", top_k=5)
        ```
    """

    def __init__(self, config: KnowledgeStoreConfig) -> None:
        """Initialize ChromaDB store with configuration.

        Args:
            config: Configuration for ChromaDB connection.

        Raises:
            BackendConnectionError: If connection to ChromaDB fails.
        """
        self.config = config

        try:
            self._client = chromadb.HttpClient(
                host=config.host,
                port=config.port,
            )
            self._collection = self._client.get_or_create_collection(
                name=config.collection_name,
            )
            logger.info(
                f"Connected to ChromaDB at {config.host}:{config.port}, "
                f"collection: {config.collection_name}"
            )
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            raise BackendConnectionError(
                f"Failed to connect to ChromaDB: {e}",
                details={
                    "host": config.host,
                    "port": config.port,
                },
            ) from e

    async def index_document(self, document: Document) -> str:
        """Index a document in ChromaDB.

        If a document with the same doc_id exists, it will be updated (upsert).

        Args:
            document: The document to index.

        Returns:
            The doc_id of the indexed document.

        Raises:
            IndexingError: If indexing fails.
        """
        try:
            upsert_kwargs: dict[str, Any] = {
                "ids": [document.doc_id],
                "documents": [document.content],
                "metadatas": [document.metadata] if document.metadata else None,
            }

            # Include embedding if provided
            if document.embedding is not None:
                upsert_kwargs["embeddings"] = [document.embedding]

            self._collection.upsert(**upsert_kwargs)

            logger.debug(f"Indexed document: {document.doc_id}")
            return document.doc_id

        except Exception as e:
            logger.error(f"Failed to index document {document.doc_id}: {e}")
            raise IndexingError(
                f"Failed to index document: {e}",
                details={"doc_id": document.doc_id},
            ) from e

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

        Raises:
            SearchError: If the search operation fails.
        """
        try:
            query_kwargs: dict[str, Any] = {
                "query_texts": [query],
                "n_results": top_k,
            }

            if filters:
                query_kwargs["where"] = filters

            results = self._collection.query(**query_kwargs)

            # Convert ChromaDB results to SearchResult objects
            search_results: list[SearchResult] = []

            ids = results.get("ids", [[]])[0]
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]

            for i, doc_id in enumerate(ids):
                # Convert distance to similarity score (1 - distance)
                score = 1.0 - distances[i] if i < len(distances) else 0.0

                search_results.append(
                    SearchResult(
                        doc_id=doc_id,
                        content=documents[i] if i < len(documents) else "",
                        metadata=metadatas[i] if i < len(metadatas) else {},
                        score=score,
                        source="chromadb",
                    )
                )

            logger.debug(f"Search returned {len(search_results)} results")
            return search_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise SearchError(
                f"Search failed: {e}",
                details={"query": query, "top_k": top_k},
            ) from e

    async def get_by_id(self, doc_id: str) -> Document | None:
        """Retrieve a document by its ID.

        Args:
            doc_id: The unique identifier of the document.

        Returns:
            The Document if found, None otherwise.

        Raises:
            BackendConnectionError: If connection to backend fails.
        """
        try:
            result = self._collection.get(
                ids=[doc_id],
                include=["documents", "metadatas", "embeddings"],
            )

            if not result["ids"]:
                return None

            return Document(
                doc_id=result["ids"][0],
                content=result["documents"][0] if result["documents"] else "",
                metadata=result["metadatas"][0] if result["metadatas"] else {},
                embedding=result["embeddings"][0] if result.get("embeddings") else None,
            )

        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            raise BackendConnectionError(
                f"Failed to retrieve document: {e}",
                details={"doc_id": doc_id},
            ) from e

    async def delete(self, doc_id: str) -> bool:
        """Delete a document from the knowledge store.

        Args:
            doc_id: The unique identifier of the document to delete.

        Returns:
            True if the document was deleted, False if not found.

        Raises:
            BackendConnectionError: If connection to backend fails.
        """
        try:
            # Check if document exists first
            result = self._collection.get(ids=[doc_id])

            if not result["ids"]:
                return False

            self._collection.delete(ids=[doc_id])
            logger.debug(f"Deleted document: {doc_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            raise BackendConnectionError(
                f"Failed to delete document: {e}",
                details={"doc_id": doc_id},
            ) from e

    async def health_check(self) -> dict[str, Any]:
        """Check the health of the ChromaDB backend.

        Returns:
            Dictionary with health status information.
        """
        try:
            heartbeat = self._client.heartbeat()
            return {
                "status": "healthy",
                "backend": "chromadb",
                "host": self.config.host,
                "port": self.config.port,
                "collection": self.config.collection_name,
                "heartbeat": heartbeat,
            }
        except Exception as e:
            logger.warning(f"ChromaDB health check failed: {e}")
            return {
                "status": "unhealthy",
                "backend": "chromadb",
                "host": self.config.host,
                "port": self.config.port,
                "error": str(e),
            }

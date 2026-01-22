"""KnowledgeStore module for RAG and semantic search.

This module provides a knowledge store abstraction for document indexing,
semantic search, and retrieval using ChromaDB as the backend.

Usage:
    ```python
    from src.infrastructure.knowledge_store import (
        get_knowledge_store,
        Document,
        SearchResult,
        KnowledgeStoreConfig,
    )

    # Get the knowledge store (singleton)
    store = get_knowledge_store()

    # Index a document
    doc = Document(
        doc_id="doc-1",
        content="This is a sample document about agentic workflows.",
        metadata={"author": "system", "type": "reference"},
    )
    await store.index_document(doc)

    # Search for similar documents
    results = await store.search("agentic development", top_k=5)
    for result in results:
        print(f"{result.doc_id}: {result.score:.2f}")

    # Get a specific document
    doc = await store.get_by_id("doc-1")

    # Delete a document
    await store.delete("doc-1")

    # Check health
    health = await store.health_check()
    ```
"""

from src.infrastructure.knowledge_store.chromadb_store import ChromaDBStore
from src.infrastructure.knowledge_store.config import KnowledgeStoreConfig
from src.infrastructure.knowledge_store.factory import (
    get_knowledge_store,
    reset_knowledge_store,
)
from src.infrastructure.knowledge_store.models import Document, SearchResult

__all__ = [
    # Factory functions
    "get_knowledge_store",
    "reset_knowledge_store",
    # Data models
    "Document",
    "SearchResult",
    # Configuration
    "KnowledgeStoreConfig",
    # Backend (for advanced use)
    "ChromaDBStore",
]

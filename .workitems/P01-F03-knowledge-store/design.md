# Feature Design: P01-F03 KnowledgeStore Interface and ChromaDB Backend

## Overview

This feature implements the RAG (Retrieval-Augmented Generation) abstraction layer for the aSDLC system. The KnowledgeStore interface provides a uniform API for document indexing and semantic search, with ChromaDB as the prototype backend. All access to the retrieval layer goes through this interface, ensuring implementation-agnostic agent prompts and enabling future backend replacement.

## Dependencies

### Internal Dependencies

- **P01-F01**: Infrastructure setup - COMPLETE
  - Docker Compose configuration (requires update for ChromaDB)
  - Python core modules (`src/core/config.py`, `src/core/exceptions.py`)
  - Infrastructure container base

- **P01-F02**: Bash tool abstraction layer - COMPLETE
  - Testing infrastructure for validation

### External Dependencies

- ChromaDB 0.4+ (vector database)
- Sentence-transformers or OpenAI embeddings (embedding provider)
- Python 3.11+

## Interfaces

### Provided Interfaces

**KnowledgeStore Protocol**

The abstract interface that all backends must implement:

```python
from typing import Protocol
from dataclasses import dataclass

@dataclass
class Document:
    """Represents a document in the knowledge store."""
    doc_id: str
    content: str
    metadata: dict[str, str | int | float | bool]
    embedding: list[float] | None = None

@dataclass
class SearchResult:
    """Represents a search result with relevance scoring."""
    doc_id: str
    content: str
    metadata: dict[str, str | int | float | bool]
    score: float
    source: str  # Source attribution (file path, URL, etc.)

class KnowledgeStore(Protocol):
    """Abstract interface for the RAG retrieval layer."""

    async def index_document(
        self,
        doc_id: str,
        content: str,
        metadata: dict[str, str | int | float | bool] | None = None,
    ) -> bool:
        """Index a document for semantic search.

        Args:
            doc_id: Unique identifier for the document
            content: Text content to index
            metadata: Optional metadata (source, type, timestamp, etc.)

        Returns:
            True if indexing succeeded, False otherwise
        """
        ...

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, str | int | float | bool] | None = None,
    ) -> list[SearchResult]:
        """Search for documents matching the query.

        Args:
            query: Natural language search query
            top_k: Maximum number of results to return
            filters: Optional metadata filters

        Returns:
            List of SearchResult objects ordered by relevance
        """
        ...

    async def get_by_id(self, doc_id: str) -> Document | None:
        """Retrieve a document by its ID.

        Args:
            doc_id: Document identifier

        Returns:
            Document if found, None otherwise
        """
        ...

    async def delete(self, doc_id: str) -> bool:
        """Delete a document from the store.

        Args:
            doc_id: Document identifier to delete

        Returns:
            True if deleted, False if not found
        """
        ...

    async def health_check(self) -> bool:
        """Check if the knowledge store backend is healthy.

        Returns:
            True if healthy, False otherwise
        """
        ...
```

**ChromaDB Backend**

Concrete implementation of the KnowledgeStore interface:

```python
class ChromaDBStore(KnowledgeStore):
    """ChromaDB implementation of the KnowledgeStore interface."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8000,
        collection_name: str = "asdlc_documents",
        embedding_function: EmbeddingFunction | None = None,
    ) -> None:
        ...
```

**Configuration**

```python
@dataclass(frozen=True)
class KnowledgeStoreConfig:
    """KnowledgeStore configuration."""

    host: str = "localhost"
    port: int = 8000
    collection_name: str = "asdlc_documents"
    embedding_model: str = "all-MiniLM-L6-v2"  # Default sentence-transformers model

    @classmethod
    def from_env(cls) -> KnowledgeStoreConfig:
        """Create configuration from environment variables."""
        ...
```

### Required Interfaces

- Docker Compose networking (from P01-F01)
- Exception hierarchy (from P01-F01)
- Configuration patterns (from P01-F01)

## Technical Approach

### Architecture

The implementation follows the system design's principle of interface-first development:

1. **Abstract Interface Layer**: Define `KnowledgeStore` protocol in `src/core/interfaces.py`
2. **Data Models**: Define `Document` and `SearchResult` dataclasses
3. **Exception Types**: Add KnowledgeStore-specific exceptions
4. **ChromaDB Backend**: Implement `ChromaDBStore` in `src/infrastructure/knowledge_store/`
5. **Factory Pattern**: Provide `get_knowledge_store()` factory for dependency injection

### Embedding Strategy

For the prototype, use sentence-transformers with the `all-MiniLM-L6-v2` model:
- Fast and lightweight
- Good quality embeddings for code and documentation
- No external API calls required
- Can be replaced with OpenAI embeddings for production

### ChromaDB Configuration

ChromaDB runs in server mode for containerized deployment:
- Persistent storage via Docker volume
- HTTP API for client connections
- Collection-based document organization

### Docker Integration

Update the infrastructure container to include ChromaDB:
- Add ChromaDB service to docker-compose.yml
- Configure persistent storage
- Set up health checks
- Network connectivity with other containers

## File Structure

```
src/
├── core/
│   ├── interfaces.py          # KnowledgeStore protocol definition
│   └── exceptions.py          # Add KnowledgeStore exceptions
└── infrastructure/
    └── knowledge_store/
        ├── __init__.py
        ├── models.py          # Document, SearchResult dataclasses
        ├── config.py          # KnowledgeStoreConfig
        ├── chromadb_store.py  # ChromaDB implementation
        └── factory.py         # get_knowledge_store() factory

docker/
├── docker-compose.yml         # Update with ChromaDB service
└── infrastructure/
    └── Dockerfile             # Update for ChromaDB

tests/
├── unit/
│   ├── test_knowledge_store_interface.py
│   ├── test_knowledge_store_models.py
│   └── test_knowledge_store_config.py
└── integration/
    └── test_chromadb_store.py

requirements.txt               # Add chromadb, sentence-transformers
```

## API Examples

### Indexing Documents

```python
store = await get_knowledge_store()

# Index a spec document
await store.index_document(
    doc_id="spec/epics/E001/product_reqs.md",
    content="# Product Requirements\n\n...",
    metadata={
        "type": "spec",
        "epic_id": "E001",
        "source": "spec/epics/E001/product_reqs.md",
    }
)
```

### Searching

```python
# Search for relevant context
results = await store.search(
    query="user authentication requirements",
    top_k=5,
    filters={"type": "spec"}
)

for result in results:
    print(f"{result.source} (score: {result.score:.3f})")
    print(f"  {result.content[:100]}...")
```

### Document Lifecycle

```python
# Retrieve specific document
doc = await store.get_by_id("spec/epics/E001/product_reqs.md")

# Delete outdated document
await store.delete("spec/epics/E001/old_draft.md")
```

## Error Handling

### Exception Hierarchy

```python
# Add to src/core/exceptions.py

class KnowledgeStoreError(ASDLCError):
    """Base error for KnowledgeStore operations."""

class DocumentNotFoundError(KnowledgeStoreError):
    """Raised when a document cannot be found."""

class IndexingError(KnowledgeStoreError):
    """Raised when document indexing fails."""

class SearchError(KnowledgeStoreError):
    """Raised when search operation fails."""

class EmbeddingError(KnowledgeStoreError):
    """Raised when embedding generation fails."""

class BackendConnectionError(KnowledgeStoreError):
    """Raised when connection to backend fails."""
```

## Migration Path

The interface design supports future backend replacement:

| Backend | Use Case | Migration Effort |
|---------|----------|------------------|
| ChromaDB | Prototype, single-node | Current |
| Qdrant | Production, distributed | Implement QdrantStore |
| Elasticsearch | Enterprise, full-text + vector | Implement ElasticsearchStore |
| Azure AI Search | Azure-native deployments | Implement AzureSearchStore |
| Vertex AI Search | GCP deployments | Implement VertexSearchStore |

Migration requires only implementing a new class conforming to the `KnowledgeStore` protocol.

## Security Considerations

1. **Input Validation**: Sanitize document IDs and content before indexing
2. **Metadata Safety**: Validate metadata types to prevent injection
3. **Access Control**: KnowledgeStore access restricted to authorized containers
4. **No PII**: Documents should not contain sensitive personal information

## Performance Considerations

1. **Batch Indexing**: Support bulk document indexing for initial loads
2. **Connection Pooling**: Reuse ChromaDB connections
3. **Embedding Caching**: Cache embeddings for unchanged documents
4. **Query Limits**: Enforce reasonable `top_k` limits (max 100)

## Open Questions

1. Should we support multiple collections (per-epic, per-type)?
2. What is the retention policy for indexed documents?
3. Should search support hybrid (semantic + keyword) queries?

## Risks

1. **Embedding Model Size**: sentence-transformers models require ~500MB RAM. Mitigation: use quantized models or remote embedding API.
2. **ChromaDB Stability**: ChromaDB is relatively new. Mitigation: comprehensive error handling and health checks.
3. **Index Consistency**: Documents may be updated in Git but not in the index. Mitigation: implement sync mechanism in future feature.

## Success Criteria

1. KnowledgeStore interface is fully defined and documented
2. ChromaDB backend passes all interface contract tests
3. Docker Compose includes working ChromaDB service
4. Health checks verify backend connectivity
5. Integration tests demonstrate index/search/retrieve/delete operations
6. Documentation includes usage examples and migration guidance

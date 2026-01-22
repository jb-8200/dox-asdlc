# P01-F03: KnowledgeStore Interface and ChromaDB Backend - Tasks

## Overview

This task breakdown covers implementing the KnowledgeStore interface and ChromaDB backend for the RAG abstraction layer.

## Dependencies

- **P01-F01**: Infrastructure setup - COMPLETE
- **P01-F02**: Bash tool abstraction layer - COMPLETE

## Task List

### T01: Add KnowledgeStore exceptions to exception hierarchy

**Model**: haiku
**Description**: Extend the existing exception hierarchy with KnowledgeStore-specific exceptions.

**Subtasks**:
- [ ] Add `KnowledgeStoreError` base exception
- [ ] Add `DocumentNotFoundError` exception
- [ ] Add `IndexingError` exception
- [ ] Add `SearchError` exception
- [ ] Add `EmbeddingError` exception
- [ ] Add `BackendConnectionError` exception
- [ ] Write unit tests for exception hierarchy

**Acceptance Criteria**:
- [ ] All exceptions inherit from appropriate base classes
- [ ] Exceptions include `message` and `details` fields
- [ ] Exceptions support JSON serialization via `to_dict()`
- [ ] Unit tests verify inheritance chain

**Test Cases**:
- [ ] Test exception instantiation with message
- [ ] Test exception instantiation with details
- [ ] Test to_dict() serialization
- [ ] Test inheritance from ASDLCError

**Estimate**: 30min

---

### T02: Define data models (Document, SearchResult)

**Model**: haiku
**Description**: Create dataclass models for documents and search results.

**Subtasks**:
- [ ] Create `src/infrastructure/knowledge_store/` directory
- [ ] Create `models.py` with `Document` dataclass
- [ ] Create `SearchResult` dataclass
- [ ] Add JSON serialization methods
- [ ] Write unit tests for models

**Acceptance Criteria**:
- [ ] `Document` has fields: `doc_id`, `content`, `metadata`, `embedding`
- [ ] `SearchResult` has fields: `doc_id`, `content`, `metadata`, `score`, `source`
- [ ] Metadata supports str, int, float, bool values
- [ ] Models are immutable (frozen dataclass)
- [ ] Unit tests verify field types and serialization

**Test Cases**:
- [ ] Test Document creation with all fields
- [ ] Test Document creation with minimal fields
- [ ] Test SearchResult creation and score validation
- [ ] Test JSON serialization round-trip
- [ ] Test metadata type validation

**Estimate**: 45min

---

### T03: Define KnowledgeStore protocol interface

**Model**: haiku
**Description**: Create the abstract interface that all backends must implement.

**Subtasks**:
- [ ] Create `src/core/interfaces.py` (or add to existing)
- [ ] Define `KnowledgeStore` Protocol class
- [ ] Define `index_document` method signature
- [ ] Define `search` method signature
- [ ] Define `get_by_id` method signature
- [ ] Define `delete` method signature
- [ ] Define `health_check` method signature
- [ ] Add comprehensive docstrings
- [ ] Write unit tests for protocol compliance

**Acceptance Criteria**:
- [ ] Protocol is defined using `typing.Protocol`
- [ ] All methods are `async`
- [ ] Type hints are complete and mypy-compliant
- [ ] Docstrings follow Google style
- [ ] Protocol can be used for static type checking

**Test Cases**:
- [ ] Test protocol defines required methods
- [ ] Test mypy compliance with protocol
- [ ] Test that non-compliant class fails type check

**Estimate**: 45min

---

### T04: Create KnowledgeStore configuration

**Model**: haiku
**Description**: Add configuration dataclass for KnowledgeStore settings.

**Subtasks**:
- [ ] Create `src/infrastructure/knowledge_store/config.py`
- [ ] Define `KnowledgeStoreConfig` dataclass
- [ ] Implement `from_env()` class method
- [ ] Add configuration to main `AppConfig`
- [ ] Write unit tests for configuration

**Acceptance Criteria**:
- [ ] Config includes: `host`, `port`, `collection_name`, `embedding_model`
- [ ] Config loads from environment variables with defaults
- [ ] Config integrates with existing `AppConfig` pattern
- [ ] Missing required config raises `ConfigurationError`
- [ ] Unit tests verify default values and env loading

**Test Cases**:
- [ ] Test default configuration values
- [ ] Test configuration from environment variables
- [ ] Test configuration validation
- [ ] Test integration with AppConfig

**Estimate**: 30min

---

### T05: Update Docker Compose with ChromaDB service

**Model**: haiku
**Description**: Add ChromaDB to the infrastructure container configuration.

**Subtasks**:
- [ ] Add ChromaDB service to `docker/docker-compose.yml`
- [ ] Configure persistent volume for ChromaDB data
- [ ] Add health check for ChromaDB
- [ ] Configure network connectivity
- [ ] Update environment variables for other services
- [ ] Test container startup

**Acceptance Criteria**:
- [ ] ChromaDB service runs on port 8000 (internal)
- [ ] Data persists across container restarts
- [ ] Health check verifies ChromaDB is responding
- [ ] Orchestrator and workers can reach ChromaDB
- [ ] `docker compose up` starts all services

**Test Cases**:
- [ ] Test docker compose config is valid
- [ ] Test ChromaDB health check endpoint
- [ ] Test volume persistence (manual verification)
- [ ] Test network connectivity from other containers

**Estimate**: 1hr

---

### T06: Add ChromaDB and embedding dependencies

**Model**: haiku
**Description**: Update requirements with ChromaDB and sentence-transformers.

**Subtasks**:
- [ ] Add `chromadb` to requirements.txt
- [ ] Add `sentence-transformers` to requirements.txt
- [ ] Update `pyproject.toml` with dependency groups
- [ ] Verify dependencies install correctly
- [ ] Test import in Python

**Acceptance Criteria**:
- [ ] `pip install -r requirements.txt` succeeds
- [ ] `import chromadb` works
- [ ] `import sentence_transformers` works
- [ ] No dependency conflicts
- [ ] Docker build includes new dependencies

**Test Cases**:
- [ ] Test dependency installation
- [ ] Test imports in Python shell
- [ ] Test Docker build with new dependencies

**Estimate**: 30min

---

### T07: Implement ChromaDB client wrapper

**Model**: sonnet
**Description**: Create the ChromaDB backend implementation of KnowledgeStore.

**Subtasks**:
- [ ] Create `src/infrastructure/knowledge_store/chromadb_store.py`
- [ ] Implement `__init__` with connection setup
- [ ] Implement `index_document` method
- [ ] Implement `search` method
- [ ] Implement `get_by_id` method
- [ ] Implement `delete` method
- [ ] Implement `health_check` method
- [ ] Handle ChromaDB-specific errors
- [ ] Write comprehensive unit tests (mocked)

**Acceptance Criteria**:
- [ ] Class implements `KnowledgeStore` protocol
- [ ] Connects to ChromaDB via HTTP client
- [ ] Handles connection errors with `BackendConnectionError`
- [ ] Generates embeddings using configured model
- [ ] All methods have proper error handling
- [ ] Unit tests cover all methods and error cases

**Test Cases**:
- [ ] Test successful index_document
- [ ] Test index_document with existing doc (update)
- [ ] Test search returns ranked results
- [ ] Test search with filters
- [ ] Test search with empty results
- [ ] Test get_by_id found
- [ ] Test get_by_id not found
- [ ] Test delete success
- [ ] Test delete not found
- [ ] Test health_check healthy
- [ ] Test health_check unhealthy
- [ ] Test connection error handling

**Estimate**: 2hr

---

### T08: Implement embedding function wrapper

**Model**: haiku
**Description**: Create a wrapper for embedding generation that works with ChromaDB.

**Subtasks**:
- [ ] Create embedding function class compatible with ChromaDB
- [ ] Support sentence-transformers models
- [ ] Handle embedding errors gracefully
- [ ] Add caching for repeated texts (optional)
- [ ] Write unit tests

**Acceptance Criteria**:
- [ ] Embedding function generates 384-dimensional vectors (MiniLM)
- [ ] Works with ChromaDB's embedding function interface
- [ ] Raises `EmbeddingError` on failure
- [ ] Model is configurable via config
- [ ] Unit tests verify embedding generation

**Test Cases**:
- [ ] Test embedding generation for single text
- [ ] Test embedding generation for batch
- [ ] Test embedding dimensions
- [ ] Test error handling for invalid input
- [ ] Test model loading

**Estimate**: 1hr

---

### T09: Create factory function for KnowledgeStore

**Model**: haiku
**Description**: Implement factory function for obtaining configured KnowledgeStore instance.

**Subtasks**:
- [ ] Create `src/infrastructure/knowledge_store/factory.py`
- [ ] Implement `get_knowledge_store()` async function
- [ ] Support singleton pattern for connection reuse
- [ ] Support async context manager
- [ ] Write unit tests

**Acceptance Criteria**:
- [ ] Factory returns `ChromaDBStore` instance
- [ ] Factory reads config from environment
- [ ] Multiple calls return same instance (singleton)
- [ ] Factory handles configuration errors
- [ ] Unit tests verify factory behavior

**Test Cases**:
- [ ] Test factory returns KnowledgeStore instance
- [ ] Test singleton behavior
- [ ] Test configuration from environment
- [ ] Test error handling for missing config

**Estimate**: 45min

---

### T10: Write integration tests with real ChromaDB

**Model**: sonnet
**Description**: Create integration tests that run against actual ChromaDB instance.

**Subtasks**:
- [ ] Create `tests/integration/test_chromadb_store.py`
- [ ] Test full index/search/retrieve/delete cycle
- [ ] Test search relevance ordering
- [ ] Test metadata filtering
- [ ] Test concurrent operations
- [ ] Add pytest fixtures for test data

**Acceptance Criteria**:
- [ ] Tests run against Docker ChromaDB
- [ ] Tests clean up after themselves
- [ ] Tests verify actual semantic search works
- [ ] Tests pass in CI/CD environment
- [ ] Test coverage > 80%

**Test Cases**:
- [ ] Test index and immediate search
- [ ] Test multiple document indexing
- [ ] Test search relevance (similar docs ranked higher)
- [ ] Test metadata filter accuracy
- [ ] Test document update (re-index)
- [ ] Test delete and verify removal
- [ ] Test health check against real server

**Estimate**: 1.5hr

---

### T11: Update infrastructure health checks

**Model**: haiku
**Description**: Add KnowledgeStore health check to infrastructure monitoring.

**Subtasks**:
- [ ] Update `src/infrastructure/health.py` with knowledge store check
- [ ] Add KnowledgeStore status to health endpoint response
- [ ] Handle unavailable knowledge store gracefully
- [ ] Write unit tests

**Acceptance Criteria**:
- [ ] Health endpoint includes knowledge store status
- [ ] Unhealthy knowledge store doesn't crash health check
- [ ] Status includes connection details
- [ ] Unit tests verify health check behavior

**Test Cases**:
- [ ] Test health check with healthy knowledge store
- [ ] Test health check with unhealthy knowledge store
- [ ] Test health response format

**Estimate**: 30min

---

### T12: Create module exports and documentation

**Model**: haiku
**Description**: Set up clean module exports and add documentation.

**Subtasks**:
- [ ] Create `src/infrastructure/knowledge_store/__init__.py` with exports
- [ ] Add docstrings to all public functions
- [ ] Create usage examples in docstrings
- [ ] Update design.md with final implementation notes

**Acceptance Criteria**:
- [ ] `from src.infrastructure.knowledge_store import KnowledgeStore, get_knowledge_store` works
- [ ] All public APIs have docstrings
- [ ] Examples are accurate and runnable
- [ ] Documentation matches implementation

**Test Cases**:
- [ ] Test module imports
- [ ] Test exported symbols match documentation

**Estimate**: 30min

---

## Progress

- **Started**: 2026-01-22
- **Tasks Complete**: 12/12
- **Percentage**: 100%
- **Status**: COMPLETE
- **Blockers**: None

## Task Summary

| Task | Description | Estimate | Status |
|------|-------------|----------|--------|
| T01 | Add KnowledgeStore exceptions | 30 min | [x] |
| T02 | Define data models | 45 min | [x] |
| T03 | Define KnowledgeStore protocol | 45 min | [x] |
| T04 | Create configuration | 30 min | [x] |
| T05 | Update Docker Compose with ChromaDB | 1 hr | [x] |
| T06 | Add dependencies | 30 min | [x] |
| T07 | Implement ChromaDB backend | 2 hr | [x] |
| T08 | Implement embedding wrapper | 1 hr | [x] |
| T09 | Create factory function | 45 min | [x] |
| T10 | Write integration tests | 1.5 hr | [x] |
| T11 | Update health checks | 30 min | [x] |
| T12 | Module exports and documentation | 30 min | [x] |

**Total Estimated Time**: 10 hours

## Completion Checklist

- [ ] All tasks in Task List are marked complete
- [ ] All unit tests pass: `./tools/test.sh tests/unit/`
- [ ] All integration tests pass: `./tools/test.sh tests/integration/`
- [ ] E2E tests pass: `./tools/e2e.sh`
- [ ] Linter passes: `./tools/lint.sh src/`
- [ ] No type errors: `mypy src/`
- [ ] Documentation updated
- [ ] Interface contracts verified against design.md
- [ ] Progress marked as 100% in tasks.md

## Notes

### Task Dependencies

```
T01 ────┐
        ├──► T03 ──► T07 ──► T09 ──► T10
T02 ────┘              │
                       ▼
T04 ──────────────► T07
                       │
T05 ──────────────►────┘
T06 ──────────────►────┘
                       │
T08 ──────────────►────┘

T11 depends on T07
T12 depends on all others
```

### Implementation Order

1. Foundation: T01, T02 (parallel)
2. Interface: T03
3. Infrastructure: T04, T05, T06 (parallel)
4. Implementation: T07, T08
5. Factory: T09
6. Testing: T10, T11 (parallel)
7. Documentation: T12

### Testing Strategy

- Unit tests mock ChromaDB client for fast execution
- Integration tests use real ChromaDB in Docker
- Test fixtures provide sample documents and queries
- Cleanup ensures test isolation

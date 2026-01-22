# Feature Design: P06-F03 ChromaDB StatefulSet (RAG Service)

## Overview

This feature deploys ChromaDB as a Kubernetes StatefulSet with persistent storage, providing the RAG (Retrieval Augmented Generation) backend for the aSDLC KnowledgeStore. Additionally, it introduces a Mock Anthology service implementation to enable testing the replacement path to enterprise search services.

## Dependencies

- **P06-F01**: Kubernetes base infrastructure (umbrella chart, namespace, secrets)
- **P01-F03**: KnowledgeStore interface and ChromaDB backend (existing implementation)

Note: P06-F02 (Redis) and P06-F03 (ChromaDB) can be developed in parallel after P06-F01 completes.

## Interfaces

### Provided Interfaces

**ChromaDB StatefulSet**
Single-replica ChromaDB StatefulSet with stable network identity and persistent storage:
```yaml
Service: knowledge-store.dox-asdlc.svc.cluster.local:8000
```

Note: The service is named `knowledge-store` rather than `chromadb` to abstract the backend implementation.

**Knowledge Store Service**
Generic service name allowing backend substitution:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: knowledge-store
spec:
  ports:
    - port: 8000
      targetPort: 8000
```

**Mock Anthology Backend**
Python implementation of KnowledgeStoreProtocol for testing:
```python
class MockAnthologyStore(KnowledgeStoreProtocol):
    """In-memory KnowledgeStore for testing anthology replacement."""
```

### Required Interfaces

**From P06-F01:**
- Namespace `dox-asdlc`
- Helm umbrella chart structure

**From P01-F03:**
- `KnowledgeStoreProtocol` interface
- `KnowledgeStoreFactory` for backend selection

## Technical Approach

### ChromaDB Kubernetes Deployment

ChromaDB runs as a StatefulSet for persistence guarantees. The deployment uses the official `chromadb/chroma` image with persistent storage mounted at `/chroma/chroma`.

Configuration is managed via environment variables and ConfigMap:
- `CHROMA_SERVER_HOST`: Bind address (0.0.0.0)
- `CHROMA_SERVER_HTTP_PORT`: Service port (8000)
- `ANONYMIZED_TELEMETRY`: Disabled for privacy

### Mock Anthology Service

A mock anthology implementation provides:
1. Testing path for anthology replacement without external dependencies
2. Validation that the KnowledgeStore interface is truly implementation-agnostic
3. Unit testing without requiring ChromaDB

The mock uses in-memory storage with optional file persistence for test isolation.

### Backend Selection

The existing `KnowledgeStoreFactory` is extended to support backend selection:
```python
store = KnowledgeStoreFactory.create(
    backend="chromadb",  # or "mock_anthology"
    config=config
)
```

Environment variable `KNOWLEDGE_STORE_BACKEND` controls runtime selection.

## File Structure

```
helm/dox-asdlc/charts/chromadb/
├── Chart.yaml              # Subchart definition
├── values.yaml             # ChromaDB-specific values
└── templates/
    ├── statefulset.yaml    # ChromaDB StatefulSet
    ├── service.yaml        # knowledge-store Service
    ├── configmap.yaml      # ChromaDB configuration
    └── pvc.yaml            # PVC template

src/infrastructure/knowledge_store/
├── mock_anthology.py       # Mock anthology implementation
└── factory.py              # Modified to support backend selection

tests/unit/
└── test_mock_anthology.py  # Mock anthology tests
```

## Configuration

### Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `chromadb.enabled` | `true` | Enable ChromaDB deployment |
| `chromadb.persistence.size` | `5Gi` | PVC size |
| `chromadb.persistence.storageClass` | `""` | Storage class |
| `chromadb.resources.requests.memory` | `512Mi` | Memory request |
| `chromadb.resources.limits.memory` | `1Gi` | Memory limit |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KNOWLEDGE_STORE_BACKEND` | `chromadb` | Backend selection |
| `KNOWLEDGE_STORE_URL` | `http://knowledge-store:8000` | Service URL |

## Open Questions

The specific embedding model used by ChromaDB should be configurable. The prototype uses ChromaDB's default embedding function.

## Risks

**Risk 1: ChromaDB API compatibility**
Mitigation: Pin to a specific ChromaDB version and test upgrade paths.

**Risk 2: Large collection performance**
Mitigation: Document collection size limits and scaling recommendations.

# User Stories: P06-F03 ChromaDB StatefulSet (RAG Service)

## US-01: Deploy ChromaDB with Persistent Storage

**As a** operator
**I want** ChromaDB deployed as a StatefulSet with persistent storage
**So that** indexed documents survive pod restarts

### Acceptance Criteria

ChromaDB runs as a StatefulSet with 1 replica. A PersistentVolumeClaim is created and bound. Indexed documents persist across pod deletions. The StatefulSet uses a stable network identity.

### Test Scenarios

**Scenario 1: Initial deployment**
Given the Helm chart is installed, when I check the ChromaDB StatefulSet, then exactly 1 pod is running with a bound PVC.

**Scenario 2: Data persistence**
Given documents indexed in ChromaDB, when the pod is deleted and recreated, then the documents are searchable after restart.

---

## US-02: Access ChromaDB via Abstract Service Name

**As a** service component
**I want** ChromaDB accessible via a generic service name
**So that** the backend can be replaced without client changes

### Acceptance Criteria

A ClusterIP Service named `knowledge-store` exposes ChromaDB on port 8000. The service is resolvable as `knowledge-store.dox-asdlc.svc.cluster.local`. The KnowledgeStore client connects using this abstract name.

### Test Scenarios

**Scenario 1: Service resolution**
Given ChromaDB is deployed, when I resolve `knowledge-store.dox-asdlc.svc.cluster.local`, then I get the correct ClusterIP.

**Scenario 2: Abstract connectivity**
Given the knowledge-store service, when I change the backend implementation, then existing clients still connect without code changes.

---

## US-03: Use Mock Anthology for Testing

**As a** developer
**I want** a mock anthology implementation of KnowledgeStore
**So that** I can test without ChromaDB dependencies

### Acceptance Criteria

The `MockAnthologyStore` class implements `KnowledgeStoreProtocol`. All protocol methods work with in-memory storage. The mock can be enabled via configuration. Unit tests use the mock by default.

### Test Scenarios

**Scenario 1: Mock creation**
Given `KNOWLEDGE_STORE_BACKEND=mock_anthology`, when I create a KnowledgeStore, then I get a MockAnthologyStore instance.

**Scenario 2: Full interface support**
Given a MockAnthologyStore, when I call index_document, search, get_by_id, and delete, then all operations succeed.

---

## US-04: Select Backend via Configuration

**As a** operator
**I want** to select the KnowledgeStore backend via environment variable
**So that** I can switch implementations without code changes

### Acceptance Criteria

The `KNOWLEDGE_STORE_BACKEND` environment variable controls backend selection. Valid values are `chromadb` and `mock_anthology`. Invalid values raise clear error messages. The factory logs which backend is selected.

### Test Scenarios

**Scenario 1: ChromaDB selection**
Given `KNOWLEDGE_STORE_BACKEND=chromadb`, when the factory creates a store, then it returns a ChromaDBStore.

**Scenario 2: Mock selection**
Given `KNOWLEDGE_STORE_BACKEND=mock_anthology`, when the factory creates a store, then it returns a MockAnthologyStore.

**Scenario 3: Invalid backend**
Given `KNOWLEDGE_STORE_BACKEND=invalid`, when the factory creates a store, then it raises a ConfigurationError.

---

## US-05: Configure ChromaDB Resources

**As a** operator
**I want** ChromaDB resource limits configurable
**So that** I can control cluster resource usage

### Acceptance Criteria

Memory requests and limits are set on the ChromaDB container. Storage size is configurable via Helm values. Minikube defaults are appropriate for development. Production values can request more resources.

### Test Scenarios

**Scenario 1: Development resources**
Given minikube values, when ChromaDB is deployed, then memory is limited to 1Gi.

**Scenario 2: Storage allocation**
Given `chromadb.persistence.size=10Gi`, when deployed, then the PVC requests 10Gi of storage.

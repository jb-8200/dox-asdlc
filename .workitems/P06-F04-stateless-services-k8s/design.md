# Feature Design: P06-F04 Stateless Services Deployment

## Overview

This feature deploys the stateless application services (Orchestrator, Workers, HITL-UI) as Kubernetes Deployments with appropriate scaling configurations. These services replace the corresponding Docker Compose services with Kubernetes-native patterns including HorizontalPodAutoscaler for workers.

## Dependencies

- **P06-F01**: Kubernetes base infrastructure (umbrella chart, namespace, secrets)
- **P06-F02**: Redis StatefulSet (event streaming backend)
- **P06-F03**: ChromaDB StatefulSet (KnowledgeStore backend)

## Interfaces

### Provided Interfaces

**Orchestrator Deployment**
Single-replica Deployment with exclusive Git write access:
```yaml
Service: orchestrator.dox-asdlc.svc.cluster.local:8080
```

**Workers Deployment**
Scalable worker pool with HorizontalPodAutoscaler:
```yaml
Deployment: workers (2-10 replicas based on CPU)
Service: workers.dox-asdlc.svc.cluster.local:8081
```

**HITL-UI Deployment**
Web interface with external access:
```yaml
Service: hitl-ui.dox-asdlc.svc.cluster.local:3000
NodePort: 30000 (for minikube external access)
```

### Required Interfaces

**From P06-F01:**
- Namespace `dox-asdlc`
- Secret templates (Git credentials, API keys)
- Helm umbrella chart structure

**From P06-F02:**
- Redis service at `redis.dox-asdlc.svc.cluster.local:6379`

**From P06-F03:**
- KnowledgeStore service at `knowledge-store.dox-asdlc.svc.cluster.local:8000`

## Technical Approach

### Orchestrator Deployment

The orchestrator runs as a single-replica Deployment (not StatefulSet, as it's stateless). Key characteristics:
- Exclusive Git credentials via mounted Secret
- Connects to Redis for event consumption
- Connects to KnowledgeStore for RAG queries
- Single replica ensures no duplicate event processing (leader election optional future enhancement)

### Workers Deployment

Workers are stateless execution pods that:
- Receive tasks from Redis streams
- Execute Claude Agent SDK queries
- Return results to Redis
- Scale horizontally based on workload

HorizontalPodAutoscaler configuration:
- Min replicas: 2 (fault tolerance)
- Max replicas: 10 (resource cap)
- Target CPU utilization: 70%

### HITL-UI Deployment

The HITL UI serves the approval interface:
- Stateless HTTP server
- NodePort service for external access in minikube
- Ingress support for production (HTTP only as specified)
- Connects to Redis for gate request retrieval

### Service Discovery

All services use Kubernetes DNS for service discovery:
```python
REDIS_URL = "redis://redis.dox-asdlc.svc.cluster.local:6379"
KNOWLEDGE_STORE_URL = "http://knowledge-store.dox-asdlc.svc.cluster.local:8000"
```

Configuration is injected via ConfigMaps with environment-specific values.

## File Structure

```
helm/dox-asdlc/charts/orchestrator/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    └── configmap.yaml

helm/dox-asdlc/charts/workers/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    ├── hpa.yaml
    └── configmap.yaml

helm/dox-asdlc/charts/hitl-ui/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    └── configmap.yaml
```

## Configuration

### Orchestrator Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `orchestrator.replicas` | `1` | Replica count (should stay 1) |
| `orchestrator.resources.requests.memory` | `512Mi` | Memory request |
| `orchestrator.resources.limits.memory` | `1Gi` | Memory limit |

### Workers Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `workers.minReplicas` | `2` | HPA minimum |
| `workers.maxReplicas` | `10` | HPA maximum |
| `workers.targetCPUUtilization` | `70` | HPA target |
| `workers.resources.requests.memory` | `256Mi` | Memory request |
| `workers.resources.limits.memory` | `512Mi` | Memory limit |

### HITL-UI Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `hitlUI.replicas` | `1` | Replica count |
| `hitlUI.service.type` | `NodePort` | Service type |
| `hitlUI.service.nodePort` | `30000` | External port |

## Open Questions

Leader election for orchestrator high availability is not implemented. Single replica is acceptable for the prototype.

## Risks

**Risk 1: Worker scaling lag**
Mitigation: Pre-warm minimum replicas. Tune HPA stabilization windows.

**Risk 2: Orchestrator single point of failure**
Mitigation: Kubernetes restarts failed pods. Redis ensures no event loss.

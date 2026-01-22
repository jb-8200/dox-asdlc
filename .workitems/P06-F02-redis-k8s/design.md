# Feature Design: P06-F02 Redis StatefulSet

## Overview

This feature deploys Redis as a Kubernetes StatefulSet with persistent storage, providing the event streaming and caching infrastructure for the aSDLC system. It replaces the Docker Compose Redis deployment with a Kubernetes-native configuration.

## Dependencies

- **P06-F01**: Kubernetes base infrastructure (umbrella chart, namespace, secrets)

## Interfaces

### Provided Interfaces

**Redis StatefulSet**
Single-replica Redis StatefulSet with stable network identity and persistent storage:
```yaml
Service: redis.dox-asdlc.svc.cluster.local:6379
```

**Redis Secret**
Kubernetes Secret containing Redis authentication credentials:
```yaml
Secret: dox-asdlc-redis-auth
Keys: redis-password
```

**Redis ConfigMap**
Configurable Redis settings:
```yaml
ConfigMap: dox-asdlc-redis-config
Keys: redis.conf
```

### Required Interfaces

**From P06-F01:**
- Namespace `dox-asdlc`
- Base secret templates
- Helm umbrella chart structure

## Technical Approach

Redis is deployed as a StatefulSet rather than Deployment to ensure:
1. Stable pod identity for predictable network addressing
2. Ordered startup/shutdown for data consistency
3. Persistent volume binding that survives pod rescheduling

The StatefulSet uses a PersistentVolumeClaim template to automatically provision storage. For minikube, this uses the default `standard` storage class (hostPath). For production, this should be configured to use appropriate persistent storage.

Redis configuration is managed via ConfigMap:
- Development: RDB snapshots only for speed
- Production: AOF (append-only file) for durability

Authentication is required and managed via Kubernetes Secrets. The password is injected as an environment variable and referenced by the `requirepass` directive.

The Redis subchart is created within the umbrella chart's `charts/` directory following Helm subchart patterns.

## File Structure

```
helm/dox-asdlc/charts/redis/
├── Chart.yaml              # Subchart definition
├── values.yaml             # Redis-specific values
└── templates/
    ├── statefulset.yaml    # Redis StatefulSet
    ├── service.yaml        # ClusterIP Service
    ├── configmap.yaml      # Redis configuration
    └── pvc.yaml            # PVC template (optional, can be inline)
```

## Configuration

### Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `redis.enabled` | `true` | Enable Redis deployment |
| `redis.replicas` | `1` | Number of Redis replicas |
| `redis.persistence.size` | `1Gi` | PVC size |
| `redis.persistence.storageClass` | `""` | Storage class (default if empty) |
| `redis.resources.requests.memory` | `256Mi` | Memory request |
| `redis.resources.limits.memory` | `512Mi` | Memory limit |
| `redis.aof.enabled` | `false` | Enable AOF persistence |

## Open Questions

Sentinel/cluster mode is not implemented in this feature. Single-replica Redis with persistence is sufficient for the prototype and many production scenarios. High availability can be addressed in a future feature if required.

## Risks

**Risk 1: Data loss on PVC failure**
Mitigation: Regular RDB snapshots. For production, use storage class with replication (e.g., managed cloud storage).

**Risk 2: Connection disruption during pod reschedule**
Mitigation: Client-side retry logic (already implemented in `src/core/redis_client.py`). StatefulSet ensures stable DNS.

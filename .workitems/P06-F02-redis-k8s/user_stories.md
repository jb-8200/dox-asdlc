# User Stories: P06-F02 Redis StatefulSet

## US-01: Deploy Redis with Persistent Storage

**As a** operator
**I want** Redis deployed as a StatefulSet with persistent storage
**So that** event streams and state survive pod restarts

### Acceptance Criteria

Redis runs as a StatefulSet with 1 replica by default. A PersistentVolumeClaim is created and bound. Data persists across pod deletions and restarts. The StatefulSet uses a stable network identity.

### Test Scenarios

**Scenario 1: Initial deployment**
Given the Helm chart is installed, when I check the Redis StatefulSet, then exactly 1 pod is running with a bound PVC.

**Scenario 2: Data persistence**
Given data written to Redis, when the pod is deleted and recreated, then the data is still available after pod restart.

---

## US-02: Access Redis via ClusterIP Service

**As a** service component
**I want** Redis accessible via a stable DNS name
**So that** I can connect without tracking pod IPs

### Acceptance Criteria

A ClusterIP Service exposes Redis on port 6379. The service is resolvable as `redis.dox-asdlc.svc.cluster.local`. Other pods in the namespace can connect using the service DNS name.

### Test Scenarios

**Scenario 1: Service resolution**
Given Redis is deployed, when I resolve `redis.dox-asdlc.svc.cluster.local`, then I get the correct ClusterIP.

**Scenario 2: Connectivity**
Given the Redis service exists, when I connect from another pod using the service DNS, then I can execute Redis commands.

---

## US-03: Configure Redis via ConfigMap

**As a** operator
**I want** Redis configuration managed via ConfigMap
**So that** I can tune settings without rebuilding images

### Acceptance Criteria

A ConfigMap contains the `redis.conf` file content. The StatefulSet mounts this ConfigMap as a volume. Changes to the ConfigMap trigger a pod restart via checksum annotation. Key settings (persistence, memory policy) are configurable via Helm values.

### Test Scenarios

**Scenario 1: Configuration applied**
Given a ConfigMap with `maxmemory 256mb`, when Redis starts, then the `CONFIG GET maxmemory` returns `256mb`.

**Scenario 2: Configuration update**
Given a running Redis pod, when I update the ConfigMap and trigger rollout, then the new configuration is applied.

---

## US-04: Secure Redis with Authentication

**As a** security engineer
**I want** Redis protected with password authentication
**So that** unauthorized access is prevented

### Acceptance Criteria

Redis requires authentication via the `requirepass` directive. The password is stored in a Kubernetes Secret. The password is not logged or exposed in pod specs. Client connections fail without the correct password.

### Test Scenarios

**Scenario 1: Authentication required**
Given Redis is deployed with auth enabled, when I connect without a password, then the connection is rejected with AUTH required.

**Scenario 2: Successful authentication**
Given the correct password from the Secret, when I authenticate with `AUTH <password>`, then subsequent commands succeed.

---

## US-05: Configure Resource Limits

**As a** operator
**I want** Redis resource limits configurable
**So that** I can control cluster resource usage

### Acceptance Criteria

Memory requests and limits are set on the Redis container. CPU requests and limits are configurable. Values are overridable via Helm values. Minikube defaults are appropriate for development.

### Test Scenarios

**Scenario 1: Resource limits applied**
Given the minikube values file, when Redis is deployed, then the container has memory limits of 512Mi.

**Scenario 2: Production scaling**
Given production values with higher limits, when deployed, then Redis runs with the specified resources.

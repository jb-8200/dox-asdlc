# User Stories: P06-F04 Stateless Services Deployment

## US-01: Deploy Orchestrator Service

**As a** operator
**I want** the orchestrator deployed as a Kubernetes Deployment
**So that** governance services run in the cluster with proper credentials

### Acceptance Criteria

Orchestrator runs as a single-replica Deployment. Git credentials are mounted from a Secret. Redis and KnowledgeStore URLs are configured via ConfigMap. Health endpoint is exposed for liveness/readiness probes.

### Test Scenarios

**Scenario 1: Orchestrator deployment**
Given the Helm chart is installed, when I check the orchestrator Deployment, then 1 pod is running with Ready status.

**Scenario 2: Credentials access**
Given the orchestrator pod, when I check the mounted secrets, then Git credentials are available at the expected path.

**Scenario 3: Service connectivity**
Given the orchestrator service, when I connect from another pod, then the health endpoint responds.

---

## US-02: Deploy Scalable Worker Pool

**As a** operator
**I want** workers deployed with horizontal autoscaling
**So that** the system handles variable workloads efficiently

### Acceptance Criteria

Workers run as a Deployment with HPA. Minimum 2 replicas for fault tolerance. Maximum 10 replicas for resource cap. Scaling triggers at 70% CPU utilization. Workers connect to Redis for task reception.

### Test Scenarios

**Scenario 1: Initial deployment**
Given the Helm chart, when deployed, then at least 2 worker pods are running.

**Scenario 2: HPA configuration**
Given the HPA resource, when I describe it, then min=2, max=10, targetCPU=70%.

**Scenario 3: Scale up**
Given high CPU load, when utilization exceeds 70%, then additional pods are created (up to max).

---

## US-03: Deploy HITL-UI with External Access

**As a** operator
**I want** HITL-UI accessible from outside the cluster
**So that** users can access the approval interface

### Acceptance Criteria

HITL-UI runs as a Deployment. NodePort service exposes port 30000 for minikube access. The UI is accessible at `http://<minikube-ip>:30000`. Ingress support available for production.

### Test Scenarios

**Scenario 1: UI deployment**
Given the Helm chart, when deployed, then the HITL-UI pod is running.

**Scenario 2: External access**
Given minikube, when I access `http://$(minikube ip):30000`, then the UI loads.

**Scenario 3: Service type**
Given the HITL-UI service, when I describe it, then type is NodePort with nodePort 30000.

---

## US-04: Configure Services via ConfigMaps

**As a** operator
**I want** service configuration managed via ConfigMaps
**So that** I can update settings without rebuilding images

### Acceptance Criteria

Each service has a ConfigMap with environment configuration. Redis and KnowledgeStore URLs are configurable. Environment-specific values are applied via Helm. Changes trigger pod restarts via checksum annotation.

### Test Scenarios

**Scenario 1: ConfigMap creation**
Given the Helm chart, when deployed, then ConfigMaps exist for orchestrator, workers, and hitl-ui.

**Scenario 2: Environment injection**
Given a worker pod, when I check env vars, then REDIS_URL and KNOWLEDGE_STORE_URL are set correctly.

---

## US-05: Verify Pod Health

**As a** operator
**I want** health probes configured on all services
**So that** unhealthy pods are restarted automatically

### Acceptance Criteria

All Deployments have liveness and readiness probes. Probes use HTTP health endpoints. Failed probes trigger pod restart. Startup probes prevent premature termination during initialization.

### Test Scenarios

**Scenario 1: Probe configuration**
Given any Deployment, when I describe it, then livenessProbe and readinessProbe are configured.

**Scenario 2: Health recovery**
Given a pod with failing health check, when Kubernetes detects failure, then the pod is restarted.

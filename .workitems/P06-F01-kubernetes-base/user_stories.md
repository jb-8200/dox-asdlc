# User Stories: P06-F01 Kubernetes Base Infrastructure

## US-01: Initialize Kubernetes Development Environment

**As a** developer
**I want** to start a local Kubernetes cluster with a single command
**So that** I can develop and test Kubernetes deployments locally

### Acceptance Criteria

The command `./scripts/k8s/start-minikube.sh` initializes a minikube cluster with required addons. The cluster has ingress, metrics-server, and storage-provisioner enabled. The script is idempotent and can be run multiple times without error. The cluster is accessible via `kubectl` after initialization.

### Test Scenarios

**Scenario 1: Fresh cluster initialization**
Given no minikube cluster exists, when I run `./scripts/k8s/start-minikube.sh`, then a cluster named `dox-asdlc` is created with all required addons enabled.

**Scenario 2: Idempotent re-run**
Given a cluster already exists, when I run `./scripts/k8s/start-minikube.sh`, then the script completes without error and the cluster remains functional.

---

## US-02: Deploy System via Helm

**As a** developer
**I want** to deploy the entire aSDLC system with a single Helm command
**So that** I can test the full system in Kubernetes

### Acceptance Criteria

The command `./scripts/k8s/deploy.sh` deploys the umbrella Helm chart. The namespace `dox-asdlc` is created if it doesn't exist. All resource definitions are syntactically valid. The deployment is upgradeable via subsequent `deploy.sh` calls.

### Test Scenarios

**Scenario 1: Initial deployment**
Given a running minikube cluster, when I run `./scripts/k8s/deploy.sh`, then the Helm release `dox-asdlc` is installed in the `dox-asdlc` namespace.

**Scenario 2: Upgrade deployment**
Given an existing deployment, when I modify values and run `./scripts/k8s/deploy.sh`, then the release is upgraded with new values.

---

## US-03: Clean Up Deployment

**As a** developer
**I want** to remove the Kubernetes deployment cleanly
**So that** I can start fresh or free up resources

### Acceptance Criteria

The command `./scripts/k8s/teardown.sh` removes the Helm release. An optional `--delete-namespace` flag also removes the namespace. PersistentVolumeClaims are preserved by default unless `--delete-data` is specified.

### Test Scenarios

**Scenario 1: Remove deployment only**
Given a running deployment, when I run `./scripts/k8s/teardown.sh`, then the Helm release is removed but the namespace persists.

**Scenario 2: Full cleanup**
Given a running deployment, when I run `./scripts/k8s/teardown.sh --delete-namespace --delete-data`, then all resources including PVCs and namespace are removed.

---

## US-04: Use Helm Values for Configuration

**As a** operator
**I want** environment-specific configuration via Helm values
**So that** I can deploy to different environments without modifying templates

### Acceptance Criteria

The `values.yaml` contains production-oriented defaults. The `values-minikube.yaml` contains development overrides. Values can be further overridden at deployment time via `--set` flags. All configurable parameters are documented in the values file.

### Test Scenarios

**Scenario 1: Minikube values applied**
Given the minikube values file, when I deploy with `-f values-minikube.yaml`, then resource limits are set to development-appropriate levels.

**Scenario 2: Runtime override**
Given a deployment command with `--set redis.replicas=2`, when the chart is installed, then Redis is configured with 2 replicas.

---

## US-05: Manage Secrets Securely

**As a** security engineer
**I want** secrets managed via Kubernetes Secrets
**So that** credentials are not stored in plain text in Git

### Acceptance Criteria

The Helm chart includes Secret templates for required credentials. Secrets reference values that can be provided at deploy time. Default values are placeholder-only and clearly marked as requiring replacement. Documentation describes how to provide real secrets.

### Test Scenarios

**Scenario 1: Secret creation**
Given deployment with secret values provided, when the chart is installed, then Kubernetes Secrets are created with the provided values.

**Scenario 2: Missing secrets warning**
Given deployment without required secret values, when the chart is installed, then a warning indicates which secrets need configuration.

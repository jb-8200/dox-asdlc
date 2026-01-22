# Feature Design: P06-F01 Kubernetes Base Infrastructure

## Overview

This feature establishes the foundational Kubernetes infrastructure for the aSDLC system, migrating from Docker Compose to a Helm-based deployment model. It provides the namespace definition, umbrella Helm chart structure, base secret templates, and development scripts for minikube-based local development.

## Dependencies

This feature has no internal dependencies within Phase 6 as it is the foundation. It requires:
- minikube 1.32+ or compatible Kubernetes cluster
- Helm 3.12+
- kubectl configured for the target cluster

P01-F01 through P01-F03 remain functional via Docker Compose during migration.

## Interfaces

### Provided Interfaces

**Helm Umbrella Chart**
The feature provides a `helm/dox-asdlc/` chart that orchestrates all subcharts for the system:
```
helm install dox-asdlc ./helm/dox-asdlc -f values-minikube.yaml
```

**Namespace Definition**
Single namespace `dox-asdlc` for all resources, providing logical isolation and resource quota boundaries.

**Secret Templates**
Base Kubernetes Secret definitions for:
- Redis authentication credentials
- Git credentials (orchestrator only)
- API keys for external services

**Development Scripts**
```bash
./scripts/k8s/start-minikube.sh   # Initialize minikube with required addons
./scripts/k8s/deploy.sh           # Deploy all services via Helm
./scripts/k8s/teardown.sh         # Remove deployment and optionally namespace
```

### Required Interfaces

No required interfaces for this foundational feature.

## Technical Approach

The implementation creates a Helm umbrella chart structure that will orchestrate subchart deployments for Redis, ChromaDB, and application services. The umbrella chart uses Helm's dependency mechanism to compose the full deployment.

Minikube is the target development environment with the following addons enabled:
- `ingress` for HTTP routing
- `metrics-server` for HorizontalPodAutoscaler support
- `storage-provisioner` for PersistentVolumeClaim support

The namespace is created via a Helm template to ensure it exists before other resources. Secrets use Kubernetes native secrets with optional SOPS encryption for production.

Values are separated into base (`values.yaml`) and environment-specific overlays (`values-minikube.yaml`) to support different deployment targets.

## File Structure

```
helm/
└── dox-asdlc/
    ├── Chart.yaml              # Umbrella chart definition
    ├── values.yaml             # Default values (production-oriented)
    ├── values-minikube.yaml    # Minikube-specific overrides
    └── templates/
        ├── _helpers.tpl        # Template helper functions
        ├── namespace.yaml      # Namespace definition
        └── secrets.yaml        # Base secret templates

scripts/k8s/
├── start-minikube.sh           # Minikube initialization
├── deploy.sh                   # Helm deployment wrapper
└── teardown.sh                 # Cleanup script
```

## Open Questions

The specific minikube resource allocation (CPU, memory) should be tuned based on developer machine capabilities. Default allocation of 4 CPUs and 8GB RAM is recommended.

## Risks

**Risk 1: Minikube compatibility across platforms**
Mitigation: Test scripts on macOS (hyperkit, docker), Linux (docker, kvm2), and Windows (hyperv, docker) drivers.

**Risk 2: Helm version incompatibilities**
Mitigation: Pin Helm chart API version to v2 and document minimum Helm version requirement.

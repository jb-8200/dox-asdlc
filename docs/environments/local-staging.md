# Local Staging Environment (Minikube)

Kubernetes environment for testing Helm charts and K8s-specific features.

## Prerequisites

- Docker Desktop or Docker Engine
- minikube
- kubectl
- helm 3.x

## When to Use

Use local staging when you need to:
- Test Helm chart changes
- Validate K8s manifests
- Test Ingress configuration
- Test HPA/scaling behavior
- Prepare for GKE deployment

**Do NOT use for rapid UI development** - use Docker Compose instead.

## Quick Start

### 1. Start Minikube

```bash
minikube start -p dox-asdlc \
  --cpus=4 \
  --memory=8192 \
  --driver=docker
```

### 2. Build Images Locally

```bash
# Build all images
docker build -t dox-asdlc/orchestrator:latest -f docker/orchestrator/Dockerfile .
docker build -t dox-asdlc/workers:latest -f docker/workers/Dockerfile .
docker build -t dox-asdlc/hitl-ui:latest -f docker/hitl-ui/Dockerfile .

# Load into minikube
minikube image load dox-asdlc/orchestrator:latest -p dox-asdlc
minikube image load dox-asdlc/workers:latest -p dox-asdlc
minikube image load dox-asdlc/hitl-ui:latest -p dox-asdlc
```

### 3. Deploy with Helm

```bash
# Create namespace
kubectl create namespace dox-asdlc

# Install
helm upgrade --install dox-asdlc ./helm/dox-asdlc \
  -n dox-asdlc \
  --set global.imagePullPolicy=IfNotPresent
```

### 4. Access Services

Port forwarding:
```bash
# HITL UI
kubectl port-forward -n dox-asdlc svc/dox-asdlc-hitl-ui 3000:3000

# Orchestrator API
kubectl port-forward -n dox-asdlc svc/dox-asdlc-orchestrator 8080:8080

# VictoriaMetrics
kubectl port-forward -n dox-asdlc svc/dox-asdlc-victoriametrics 8428:8428
```

Or use NodePort (check values.yaml for ports):
```bash
minikube service dox-asdlc-hitl-ui -n dox-asdlc -p dox-asdlc
```

## Updating After Code Changes

This is the slow part - avoid for rapid development.

```bash
# 1. Rebuild image
docker build -t dox-asdlc/orchestrator:v$(date +%s) -f docker/orchestrator/Dockerfile .

# 2. Load into minikube
minikube image load dox-asdlc/orchestrator:v<tag> -p dox-asdlc

# 3. Update deployment
kubectl set image deployment/dox-asdlc-orchestrator \
  orchestrator=dox-asdlc/orchestrator:v<tag> \
  -n dox-asdlc

# 4. Wait for rollout
kubectl rollout status deployment/dox-asdlc-orchestrator -n dox-asdlc
```

## Viewing Logs

```bash
# Pod logs
kubectl logs -n dox-asdlc -l app=orchestrator -f

# All pods
kubectl logs -n dox-asdlc --all-containers -f
```

## Checking Status

```bash
# Pods
kubectl get pods -n dox-asdlc

# Services
kubectl get svc -n dox-asdlc

# Helm release
helm status dox-asdlc -n dox-asdlc
```

## Cleanup

```bash
# Uninstall Helm release
helm uninstall dox-asdlc -n dox-asdlc

# Delete namespace
kubectl delete namespace dox-asdlc

# Stop minikube
minikube stop -p dox-asdlc

# Delete cluster
minikube delete -p dox-asdlc
```

## Common Issues

### ImagePullBackOff
Image not loaded into minikube:
```bash
minikube image load dox-asdlc/<image>:latest -p dox-asdlc
```

### Pod CrashLoopBackOff
Check logs:
```bash
kubectl logs -n dox-asdlc <pod-name> --previous
```

### Service not accessible
Check endpoints:
```bash
kubectl get endpoints -n dox-asdlc
```

## Helm Values Reference

Key values for local staging:

```yaml
global:
  imagePullPolicy: IfNotPresent  # Use local images

orchestrator:
  image:
    repository: dox-asdlc/orchestrator
    tag: latest

hitlUI:
  service:
    type: NodePort
    nodePort: 30000
```

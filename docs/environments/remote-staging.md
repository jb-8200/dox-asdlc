# Remote Staging Environment (GCP GKE)

Production-like Kubernetes environment for pre-production testing.

## Prerequisites

- GCP account with billing enabled
- gcloud CLI installed and configured
- kubectl
- helm 3.x

## When to Use

Use GKE staging when you need to:
- Production-like environment
- Full Kubernetes features
- Load testing
- Multi-replica testing
- Full observability stack
- Pre-production validation

## Architecture

```
GKE Cluster:
├── orchestrator (Deployment, 2+ replicas)
├── workers (Deployment, 2+ replicas, HPA)
├── hitl-ui (Deployment, 2+ replicas)
├── redis (StatefulSet or Memorystore)
├── elasticsearch (StatefulSet or Elastic Cloud)
└── victoriametrics (StatefulSet)

Ingress:
└── nginx-ingress or GCP HTTP(S) LB
```

## Quick Start

### 1. Configure GCP

```bash
export PROJECT_ID=your-project-id
export REGION=us-central1
export CLUSTER_NAME=dox-staging

gcloud config set project $PROJECT_ID
```

### 2. Create GKE Cluster

```bash
gcloud container clusters create $CLUSTER_NAME \
  --region $REGION \
  --num-nodes 2 \
  --machine-type e2-standard-4 \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 5
```

### 3. Get Credentials

```bash
gcloud container clusters get-credentials $CLUSTER_NAME --region $REGION
```

### 4. Build and Push Images

```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Build and push all images
for svc in orchestrator workers hitl-ui; do
  docker build -t gcr.io/$PROJECT_ID/$svc:latest \
    -f docker/$svc/Dockerfile .
  docker push gcr.io/$PROJECT_ID/$svc:latest
done
```

### 5. Create Namespace and Secrets

```bash
kubectl create namespace dox-staging

# Create Redis auth secret
kubectl create secret generic dox-asdlc-redis-auth \
  -n dox-staging \
  --from-literal=redis-password=your-redis-password
```

### 6. Deploy with Helm

```bash
helm upgrade --install dox-asdlc ./helm/dox-asdlc \
  -n dox-staging \
  --set global.imagePullPolicy=Always \
  --set orchestrator.image.repository=gcr.io/$PROJECT_ID/orchestrator \
  --set workers.image.repository=gcr.io/$PROJECT_ID/workers \
  --set hitlUI.image.repository=gcr.io/$PROJECT_ID/hitl-ui \
  --set ingress.enabled=true \
  --set ingress.host=staging.your-domain.com
```

### 7. Configure DNS

Get ingress IP:
```bash
kubectl get ingress -n dox-staging
```

Add DNS A record pointing to ingress IP.

## Updating

### Quick Update (image only)

```bash
# Build and push new image
docker build -t gcr.io/$PROJECT_ID/orchestrator:v$(date +%s) \
  -f docker/orchestrator/Dockerfile .
docker push gcr.io/$PROJECT_ID/orchestrator:v$(date +%s)

# Update deployment
kubectl set image deployment/dox-asdlc-orchestrator \
  orchestrator=gcr.io/$PROJECT_ID/orchestrator:v$(date +%s) \
  -n dox-staging
```

### Full Update (Helm)

```bash
helm upgrade dox-asdlc ./helm/dox-asdlc -n dox-staging
```

## Monitoring

### VictoriaMetrics UI
```bash
kubectl port-forward -n dox-staging svc/dox-asdlc-victoriametrics 8428:8428
```
Open: http://localhost:8428/vmui

### Pod Logs
```bash
kubectl logs -n dox-staging -l app=orchestrator -f
```

### Metrics
```bash
kubectl top pods -n dox-staging
```

## Scaling

### Manual Scaling
```bash
kubectl scale deployment dox-asdlc-workers --replicas=5 -n dox-staging
```

### HPA (if enabled)
```bash
kubectl get hpa -n dox-staging
```

## Cost Control

### Scale Down When Not Needed
```bash
# Scale to minimum
kubectl scale deployment --all --replicas=1 -n dox-staging

# Or delete non-essential services
kubectl delete deployment dox-asdlc-workers -n dox-staging
```

### Use Preemptible Nodes
```bash
gcloud container node-pools create preemptible-pool \
  --cluster $CLUSTER_NAME \
  --region $REGION \
  --preemptible \
  --num-nodes 2
```

## Cleanup

```bash
# Uninstall Helm release
helm uninstall dox-asdlc -n dox-staging

# Delete namespace
kubectl delete namespace dox-staging

# Delete cluster
gcloud container clusters delete $CLUSTER_NAME --region $REGION --quiet

# Delete images
for svc in orchestrator workers hitl-ui; do
  gcloud container images delete gcr.io/$PROJECT_ID/$svc --quiet
done
```

## Helm Values for Staging

Key overrides in `values-staging.yaml`:

```yaml
global:
  imagePullPolicy: Always

orchestrator:
  replicas: 2
  image:
    repository: gcr.io/PROJECT_ID/orchestrator
    tag: latest
  resources:
    requests:
      memory: 512Mi
      cpu: 250m
    limits:
      memory: 1Gi
      cpu: 1000m

workers:
  replicas: 2
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 10

hitlUI:
  replicas: 2

ingress:
  enabled: true
  className: nginx
  host: staging.your-domain.com
  tls:
    enabled: true

victoriametrics:
  enabled: true
  retention: 30d
```

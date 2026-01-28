# Remote Lab Environment (GCP Cloud Run)

Serverless environment for quick demos and external testing.

## Prerequisites

- GCP account with billing enabled
- gcloud CLI installed and configured
- Docker (for building images)

## When to Use

Use Cloud Run when you need to:
- Demo to external stakeholders
- Quick external testing
- Serverless deployment (no K8s overhead)
- Cost-effective short-term environments

**Limitations:**
- No persistent volumes (use managed services)
- Cold start latency
- Request timeout limits (60s default, 60min max)

## Architecture

```
Cloud Run Services:
├── orchestrator (API)
├── hitl-ui (Dashboard)
└── workers (optional, can be combined)

Managed Services:
├── Cloud Memorystore (Redis)
├── Elastic Cloud or Cloud Search (Elasticsearch)
└── Cloud Monitoring (instead of VictoriaMetrics)
```

## Quick Start

### 1. Configure GCP Project

```bash
export PROJECT_ID=your-project-id
export REGION=us-central1

gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION
```

### 2. Enable APIs

```bash
gcloud services enable \
  run.googleapis.com \
  containerregistry.googleapis.com \
  redis.googleapis.com
```

### 3. Build and Push Images

```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Build and push
docker build -t gcr.io/$PROJECT_ID/orchestrator:latest \
  -f docker/orchestrator/Dockerfile .
docker push gcr.io/$PROJECT_ID/orchestrator:latest

docker build -t gcr.io/$PROJECT_ID/hitl-ui:latest \
  -f docker/hitl-ui/Dockerfile .
docker push gcr.io/$PROJECT_ID/hitl-ui:latest
```

### 4. Create Redis Instance

```bash
gcloud redis instances create asdlc-redis \
  --size=1 \
  --region=$REGION \
  --redis-version=redis_7_0
```

Get Redis IP:
```bash
gcloud redis instances describe asdlc-redis --region=$REGION \
  --format='get(host)'
```

### 5. Deploy to Cloud Run

```bash
# Deploy orchestrator
gcloud run deploy orchestrator \
  --image gcr.io/$PROJECT_ID/orchestrator:latest \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "REDIS_HOST=<redis-ip>,REDIS_PORT=6379" \
  --memory 1Gi \
  --cpu 1

# Get orchestrator URL
ORCH_URL=$(gcloud run services describe orchestrator --format='value(status.url)')

# Deploy hitl-ui
gcloud run deploy hitl-ui \
  --image gcr.io/$PROJECT_ID/hitl-ui:latest \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "API_BACKEND_URL=$ORCH_URL" \
  --memory 256Mi \
  --cpu 1
```

### 6. Access

```bash
gcloud run services describe hitl-ui --format='value(status.url)'
```

## Updating

Quick redeploy after code changes:

```bash
# Rebuild and push
docker build -t gcr.io/$PROJECT_ID/orchestrator:v$(date +%s) \
  -f docker/orchestrator/Dockerfile .
docker push gcr.io/$PROJECT_ID/orchestrator:v$(date +%s)

# Deploy new version
gcloud run deploy orchestrator \
  --image gcr.io/$PROJECT_ID/orchestrator:v$(date +%s)
```

## Viewing Logs

```bash
gcloud run services logs read orchestrator --limit=100
```

Or use Cloud Console: https://console.cloud.google.com/run

## Cost Control

```bash
# Set max instances to limit cost
gcloud run services update orchestrator --max-instances=2

# Delete when not needed
gcloud run services delete orchestrator
gcloud run services delete hitl-ui
gcloud redis instances delete asdlc-redis --region=$REGION
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| REDIS_HOST | Memorystore Redis IP |
| REDIS_PORT | 6379 |
| API_BACKEND_URL | Orchestrator Cloud Run URL |
| ELASTICSEARCH_URL | Elastic Cloud endpoint |

## Cleanup

```bash
# Delete Cloud Run services
gcloud run services delete orchestrator --quiet
gcloud run services delete hitl-ui --quiet

# Delete Redis
gcloud redis instances delete asdlc-redis --region=$REGION --quiet

# Delete images
gcloud container images delete gcr.io/$PROJECT_ID/orchestrator --quiet
gcloud container images delete gcr.io/$PROJECT_ID/hitl-ui --quiet
```

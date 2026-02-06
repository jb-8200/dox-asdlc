# GCP Cloud Run Deployment Guide (Cost-Optimized)

**Status:** Analysis / Recommendation
**Optimization Target:** Cost (not performance or resilience)
**Date:** 2026-02-06

## Service Classification

| Service | Port | Stateful? | Cloud Run? | Notes |
|---------|------|-----------|------------|-------|
| Orchestrator | 8080 | No (external DB) | ✅ Yes | Needs Cloud SQL connector |
| Workers | 8081 | No | ✅ Yes | Redis Streams consumer — needs always-on CPU |
| Review Swarm | 8082 | No | ✅ Yes | Ephemeral sessions in Redis |
| HITL-UI | 3000 | No | ✅ Yes | Static SPA + Express proxy |
| Slack Bridge | 8085 | No | ✅ Yes | Optional; Socket Mode (long-lived conn) |
| Redis | 6379 | **YES** | ❌ No | Event streams, task state, coordination |
| Elasticsearch | 9200 | **YES** | ❌ No | Vector search / RAG backend |
| PostgreSQL | 5432 | **YES** | ❌ No | Ideation session persistence |
| VictoriaMetrics | 8428 | **YES** | ❌ No | Replace with Cloud Monitoring |

## Recommended Architecture

```
                        ┌──────────────────────────────┐
                        │       Cloud Run (Serverless)  │
                        │                              │
                        │  ┌────────────┐ scale-to-0   │
   Internet ──────────► │  │  HITL-UI   │──────────┐   │
        │               │  └────────────┘          │   │
        │               │  ┌────────────┐          │   │
        └──────────────►│  │Orchestrator│──┐   ┌───┘   │
                        │  └────────────┘  │   │       │
                        │  ┌────────────┐  │   │       │
                        │  │  Workers   │──┤   │       │
                        │  └────────────┘  │   │       │
                        │  ┌────────────┐  │   │       │
                        │  │Review Swarm│──┤   │       │
                        │  └────────────┘  │   │       │
                        └──────────────────┼───┼───────┘
                                           │   │
                    ┌──────────────────────┐│   │
                    │  e2-small VM (~$13)  ││   │
                    │                      ││   │
                    │  ┌────────┐          ││   │
                    │  │ Redis  │◄─────────┘│   │
                    │  │ 7-alp  │           │   │
                    │  └────────┘           │   │
                    │  ┌─────────────────┐  │   │
                    │  │ Elasticsearch   │◄─┘   │
                    │  │ 8.17 (512MB hp) │      │
                    │  └─────────────────┘      │
                    └──────────────────────┘    │
                    ┌──────────────────────┐    │
                    │  Cloud SQL (Postgres) │    │
                    │  db-f1-micro (shared) │◄───┘
                    │  ~$7/mo               │
                    └──────────────────────┘
```

## Cost Estimates

### Option A: Full Stack (~$22-27/month)

| Component | GCP Service | Spec | Cost/month |
|-----------|------------|------|------------|
| Cloud Run (4 services) | Cloud Run | scale-to-0, 1 vCPU each | $0-5 |
| PostgreSQL | Cloud SQL | db-f1-micro, 10GB SSD | ~$7 |
| Redis + ES | Compute Engine | e2-small (2GB RAM) | ~$13 |
| Disk | Persistent Disk | 30GB pd-standard | ~$1.20 |
| Images | Artifact Registry | <1GB storage | ~$0-1 |
| **Total** | | | **~$22-27** |

### Option B: Minimal (~$8-13/month)

Drop Elasticsearch, use e2-micro (free-tier eligible):

| Component | GCP Service | Spec | Cost/month |
|-----------|------------|------|------------|
| Cloud Run (4 services) | Cloud Run | scale-to-0 | $0-5 |
| PostgreSQL | Cloud SQL | db-f1-micro | ~$7 |
| Redis | Compute Engine | e2-micro (1GB, free tier) | $0 |
| Disk | Persistent Disk | 10GB pd-standard | ~$0.40 |
| **Total** | | | **~$8-13** |

### What NOT to Use (Cost Traps)

| Service | Minimum Cost | Why to Avoid |
|---------|-------------|-------------|
| Memorystore (Redis) | ~$29/mo | Overkill for lab; run Redis on VM instead |
| Elastic Cloud | ~$95/mo | Run ES on VM or use lighter alternative |
| GKE Autopilot | ~$72/mo | Cluster management fee alone is $72 |
| Cloud Run always-on | +$20-40/mo | Only use for workers if stream consumption needed |

## Cloud Run Service Configuration

### Orchestrator

```bash
gcloud run deploy orchestrator \
  --image=${REGION}-docker.pkg.dev/${PROJECT}/asdlc/orchestrator:latest \
  --region=${REGION} \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=2 \
  --concurrency=80 \
  --timeout=300 \
  --set-env-vars="REDIS_HOST=${VM_IP},REDIS_PORT=6379,REDIS_PASSWORD=${REDIS_PW}" \
  --set-env-vars="ELASTICSEARCH_URL=http://${VM_IP}:9200" \
  --set-env-vars="GIT_WRITE_ACCESS=true" \
  --add-cloudsql-instances=${PROJECT}:${REGION}:asdlc-db \
  --set-env-vars="POSTGRES_HOST=/cloudsql/${PROJECT}:${REGION}:asdlc-db" \
  --set-env-vars="POSTGRES_USER=asdlc,POSTGRES_DB=asdlc_ideation" \
  --set-secrets="POSTGRES_PASSWORD=asdlc-db-password:latest" \
  --allow-unauthenticated=false \
  --ingress=internal-and-cloud-load-balancing
```

### Workers

```bash
gcloud run deploy workers \
  --image=${REGION}-docker.pkg.dev/${PROJECT}/asdlc/workers:latest \
  --region=${REGION} \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=4 \
  --concurrency=10 \
  --timeout=3600 \
  --no-cpu-throttling \
  --set-env-vars="REDIS_HOST=${VM_IP},REDIS_PORT=6379,REDIS_PASSWORD=${REDIS_PW}" \
  --set-env-vars="ELASTICSEARCH_URL=http://${VM_IP}:9200" \
  --set-env-vars="GIT_WRITE_ACCESS=false" \
  --allow-unauthenticated=false \
  --ingress=internal
```

> **Note:** `--no-cpu-throttling` is needed because workers consume Redis Streams
> (background processing). This increases cost — see "Workers Caveat" below.

### Review Swarm

```bash
gcloud run deploy review-swarm \
  --image=${REGION}-docker.pkg.dev/${PROJECT}/asdlc/review-swarm:latest \
  --region=${REGION} \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=2 \
  --concurrency=5 \
  --timeout=3600 \
  --set-env-vars="REDIS_HOST=${VM_IP},REDIS_PORT=6379,REDIS_PASSWORD=${REDIS_PW}" \
  --set-env-vars="ELASTICSEARCH_URL=http://${VM_IP}:9200" \
  --set-secrets="ANTHROPIC_API_KEY=anthropic-api-key:latest" \
  --allow-unauthenticated=false \
  --ingress=internal
```

### HITL-UI

```bash
gcloud run deploy hitl-ui \
  --image=${REGION}-docker.pkg.dev/${PROJECT}/asdlc/hitl-ui:latest \
  --region=${REGION} \
  --memory=256Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=2 \
  --concurrency=200 \
  --timeout=60 \
  --set-env-vars="API_BACKEND_URL=https://orchestrator-xxxx-uc.a.run.app" \
  --set-env-vars="REDIS_HOST=${VM_IP},REDIS_PORT=6379" \
  --allow-unauthenticated
```

## Backing Services Setup

### Cloud SQL (PostgreSQL)

```bash
# Create instance (smallest possible)
gcloud sql instances create asdlc-db \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region=${REGION} \
  --storage-size=10 \
  --storage-type=HDD \
  --no-backup \
  --availability-type=zonal

# Create database
gcloud sql databases create asdlc_ideation --instance=asdlc-db

# Create user
gcloud sql users create asdlc \
  --instance=asdlc-db \
  --password=${DB_PASSWORD}

# Store password in Secret Manager
echo -n "${DB_PASSWORD}" | gcloud secrets create asdlc-db-password --data-file=-
```

Cost optimizations applied:
- `db-f1-micro`: shared CPU, 0.6GB RAM (~$7/mo)
- `HDD` storage: cheaper than SSD for lab use
- `--no-backup`: skip automated backups (lab only)
- `zonal`: no HA replica

### Compute Engine VM (Redis + Elasticsearch)

```bash
# Create VM
gcloud compute instances create asdlc-backing \
  --machine-type=e2-small \
  --zone=${REGION}-a \
  --boot-disk-size=30GB \
  --boot-disk-type=pd-standard \
  --tags=asdlc-backing \
  --metadata-from-file=startup-script=scripts/gcp/vm-startup.sh

# Firewall: allow Cloud Run → VM
gcloud compute firewall-rules create allow-cloudrun-to-backing \
  --direction=INGRESS \
  --action=ALLOW \
  --rules=tcp:6379,tcp:9200 \
  --target-tags=asdlc-backing \
  --source-ranges="0.0.0.0/0" \
  # Replace with Cloud Run egress range for production
```

VM runs a minimal docker-compose:

```yaml
# docker-compose.gcp-backing.yml
services:
  redis:
    image: redis:7-alpine
    command: redis-server /etc/redis/redis.conf
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
      - ./redis.conf:/etc/redis/redis.conf:ro
    restart: unless-stopped

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.17.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - ES_JAVA_OPTS=-Xms512m -Xmx512m
    ports:
      - "9200:9200"
    volumes:
      - es-data:/usr/share/elasticsearch/data
    restart: unless-stopped

volumes:
  redis-data:
  es-data:
```

### VictoriaMetrics Replacement

Drop VictoriaMetrics entirely. Cloud Run provides built-in metrics:
- Request count, latency (p50/p95/p99), error rate
- Instance count, CPU/memory utilization
- Available in Cloud Console → Cloud Run → Metrics tab

For custom application metrics, use Cloud Monitoring client library (free for GCP resources).

## Networking

### Option 1: Public IP + Firewall (Cheapest, $0)

- VM gets a public ephemeral IP
- Firewall rules restrict access to Cloud Run egress IPs
- Cloud SQL uses built-in Cloud Run connector (no VPC needed)

```bash
# Get VM IP
VM_IP=$(gcloud compute instances describe asdlc-backing \
  --zone=${REGION}-a --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
```

### Option 2: VPC Connector (~$7/month additional)

- Private networking between Cloud Run and VM
- More secure, no public exposure of Redis/ES

```bash
gcloud compute networks vpc-access connectors create asdlc-connector \
  --region=${REGION} \
  --range=10.8.0.0/28 \
  --min-instances=2 \
  --max-instances=3 \
  --machine-type=e2-micro
```

**Recommendation:** Use public IP for lab. Switch to VPC connector for staging/production.

## Artifact Registry

```bash
# Create repository
gcloud artifacts repositories create asdlc \
  --repository-format=docker \
  --location=${REGION}

# Build and push images
docker build -f docker/orchestrator/Dockerfile -t ${REGION}-docker.pkg.dev/${PROJECT}/asdlc/orchestrator:latest .
docker build -f docker/workers/Dockerfile -t ${REGION}-docker.pkg.dev/${PROJECT}/asdlc/workers:latest .
docker build -f docker/review-swarm/Dockerfile -t ${REGION}-docker.pkg.dev/${PROJECT}/asdlc/review-swarm:latest .
docker build -f docker/hitl-ui/Dockerfile -t ${REGION}-docker.pkg.dev/${PROJECT}/asdlc/hitl-ui:latest .

docker push ${REGION}-docker.pkg.dev/${PROJECT}/asdlc/orchestrator:latest
docker push ${REGION}-docker.pkg.dev/${PROJECT}/asdlc/workers:latest
docker push ${REGION}-docker.pkg.dev/${PROJECT}/asdlc/review-swarm:latest
docker push ${REGION}-docker.pkg.dev/${PROJECT}/asdlc/hitl-ui:latest
```

## Known Caveats and Mitigations

### Workers: Redis Streams on Cloud Run

**Problem:** Workers consume Redis Streams via blocking reads (XREADGROUP). Cloud Run
throttles CPU between requests by default, which breaks background stream consumption.

**Options (ranked by cost):**

1. **`--no-cpu-throttling`** (~$5-15/mo extra): CPU always allocated. Workers stay
   warm and consume streams. Simplest migration path.

2. **Refactor to HTTP-triggered** ($0 extra): Change workers from stream consumers to
   HTTP endpoints. Orchestrator calls workers via HTTP instead of publishing to streams.
   Requires code changes but is the Cloud Run-native pattern.

3. **Cloud Run Jobs** ($0 extra): Run workers as Cloud Run Jobs triggered by Cloud
   Scheduler or Pub/Sub. Good for batch processing, not real-time events.

### Orchestrator: Workspace Volume

**Problem:** Orchestrator mounts the git workspace as a read-write volume (`../:/app/workspace`).
Cloud Run has no persistent filesystem.

**Options:**
1. **Clone repo at startup** — add a startup script that `git clone`s into `/tmp/workspace`
2. **Cloud Storage FUSE** — mount a GCS bucket as a filesystem (read-write, ~$0.02/GB/mo)
3. **Skip workspace mount** — if orchestrator only needs it for git operations, consider
   using the GitHub API instead

### HITL-UI: WebSocket/Socket.io

**Problem:** HITL-UI uses Socket.io for real-time updates. Cloud Run supports HTTP/2
streaming and WebSocket since 2021, but connections are limited to request timeout.

**Mitigation:** Set `--timeout=3600` (1 hour max) on HITL-UI, or switch to
Server-Sent Events (SSE) which work more naturally with Cloud Run.

### Cold Starts

All services set to `min-instances=0` for cost. Expect 2-5 second cold starts on
first request after idle period. Python services (orchestrator, workers) will be
slower than Node.js (hitl-ui).

**Mitigation:** If cold starts are unacceptable for HITL-UI, set `--min-instances=1`
(adds ~$5-10/month).

## Deployment Order

1. Create Artifact Registry repository
2. Build and push all Docker images
3. Create Cloud SQL PostgreSQL instance + database + user
4. Run schema migration (init.sql) against Cloud SQL
5. Create Compute Engine VM with Redis + Elasticsearch
6. Wait for VM startup, note its IP address
7. Store secrets in Secret Manager (DB password, Redis password, Anthropic key)
8. Deploy Cloud Run services (orchestrator first, then workers, review-swarm, hitl-ui)
9. Configure Cloud Run service-to-service auth (orchestrator → workers)
10. Test health endpoints on all services
11. (Optional) Set up Cloud Load Balancer for custom domain

## Elasticsearch Alternatives (Further Cost Savings)

If ES is too heavy for the VM:

| Alternative | RAM | ES-Compatible API? | Vector Search? | Notes |
|-------------|-----|--------------------|----------------|-------|
| Keep ES 8.17 | 512MB-1GB | Yes | Yes (kNN) | Needs e2-small minimum |
| Zinc | ~50MB | Partial | No | Drop-in for basic search |
| Meilisearch | ~100MB | No | No | Fast, lightweight |
| Typesense | ~100MB | No | Yes | Vector + full-text |
| Skip entirely | 0 | N/A | N/A | Disable KnowledgeStore |

**To use Zinc as a drop-in:** Your `KnowledgeStore` interface already supports backend
swapping (see `src/core/interfaces.py`). Implement a Zinc adapter or disable the feature.

## Secrets Management

Use GCP Secret Manager (free for first 10k access operations/month):

```bash
# Store secrets
gcloud secrets create redis-password --data-file=- <<< "${REDIS_PW}"
gcloud secrets create anthropic-api-key --data-file=- <<< "${ANTHROPIC_KEY}"
gcloud secrets create asdlc-db-password --data-file=- <<< "${DB_PW}"
gcloud secrets create llm-encryption-key --data-file=- <<< "${ENC_KEY}"

# Grant Cloud Run access
gcloud secrets add-iam-policy-binding redis-password \
  --member="serviceAccount:${SA}" --role="roles/secretmanager.secretAccessor"
```

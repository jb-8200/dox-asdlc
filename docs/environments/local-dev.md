# Local Dev Environment (Docker Compose)

Fastest development environment for day-to-day work.

## Prerequisites

- Docker Desktop or Docker Engine
- Node.js 20+ (for UI hot reload)
- Python 3.11+ (for local testing)

## Services

| Service | Port | Description |
|---------|------|-------------|
| orchestrator | 8080 | API + governance |
| workers | 8081 | Agent workers |
| redis | 6379 | Event streams |
| elasticsearch | 9200 | Knowledge store |
| victoriametrics | 8428 | Metrics |
| hitl-ui | 3000 | Dashboard |

## Quick Start

### Option A: Full Stack (Docker)

```bash
cd docker
docker compose up -d
```

Wait for health checks:
```bash
docker compose ps
```

Access:
- Dashboard: http://localhost:3000
- API: http://localhost:8080
- Metrics: http://localhost:8428

### Option B: UI Hot Reload (Recommended for frontend)

Start backend services:
```bash
cd docker
docker compose up -d redis elasticsearch orchestrator workers victoriametrics
```

Run UI with Vite hot reload:
```bash
cd docker/hitl-ui
echo "VITE_USE_MOCKS=false" > .env.local
echo "VITE_API_BASE_URL=http://localhost:8080/api" >> .env.local
npm run dev
```

Access: http://localhost:5173 (Vite dev server)

### Option C: Mock Mode (No backend)

```bash
cd docker/hitl-ui
echo "VITE_USE_MOCKS=true" > .env.local
npm run dev
```

## Rebuilding Services

After code changes:

```bash
# Rebuild single service
docker compose build orchestrator
docker compose up -d orchestrator

# Rebuild all
docker compose build
docker compose up -d
```

## Viewing Logs

```bash
# All services
docker compose logs -f

# Single service
docker compose logs -f orchestrator

# Last 100 lines
docker compose logs --tail=100 orchestrator
```

## Metrics & Monitoring

VictoriaMetrics scrapes:
- orchestrator:8080/metrics
- workers:8081/metrics

Query UI: http://localhost:8428/vmui

Example queries:
```promql
# CPU usage
asdlc_process_cpu_percent{service="orchestrator"}

# Memory usage
asdlc_process_memory_bytes{type="rss"}

# Request rate
rate(asdlc_http_requests_total[5m])
```

## Cleanup

```bash
# Stop services (keep data)
docker compose down

# Stop and remove volumes
docker compose down -v
```

## Troubleshooting

### Service won't start
```bash
docker compose logs <service>
```

### Port already in use
```bash
lsof -i :8080
kill <pid>
```

### Reset everything
```bash
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| REDIS_HOST | redis | Redis hostname |
| REDIS_PORT | 6379 | Redis port |
| ELASTICSEARCH_URL | http://elasticsearch:9200 | ES endpoint |
| API_BACKEND_URL | http://orchestrator:8080 | API proxy target |

# K8s Service Access from Workstation

This document describes how to access Kubernetes services from your development workstation.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Workstation                                                     │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Claude CLI   │  │ Browser      │  │ .mcp.json            │  │
│  │              │  │              │  │                      │  │
│  │ Uses MCP     │  │ http://      │  │ ES: localhost:9200   │  │
│  │ tools        │  │ dox.local/   │  │ Redis: localhost:6379│  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                      │              │
│         │     minikube tunnel (sudo)             │              │
│         │          ┌──────┴──────┐               │              │
│         │          ▼             ▼               │              │
│         │   ┌─────────────────────────┐          │              │
│         │   │  Ingress (localhost:80) │          │              │
│         │   │  /api/* → orchestrator  │          │              │
│         │   │  /*     → hitl-ui       │          │              │
│         │   └─────────────────────────┘          │              │
│         │                                        │              │
│         │   Port-forward (background)            │              │
│         │   ┌──────────────────────────────────┐ │              │
│         └──►│ localhost:9200 → ES              │◄┘              │
│             │ localhost:9000 → Redis MCP       │                │
│             │ localhost:3000 → HITL UI         │                │
│             └──────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Minikube Cluster (dox-asdlc)                                   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Ingress Controller (nginx)                              │   │
│  │  Routes: /api/* → orchestrator, /* → hitl-ui             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Elasticsearch│  │ Redis        │  │ Orchestrator         │  │
│  │ NodePort     │  │ NodePort     │  │ ClusterIP            │  │
│  │ 30920→9200   │  │ 30637→6379   │  │ :8080                │  │
│  │ 30921→9000   │  │ 30900→9000   │  │                      │  │
│  │ (MCP sidecar)│  │ (MCP sidecar)│  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ HITL UI      │  │ Workers      │  │ VictoriaMetrics      │  │
│  │ NodePort     │  │ ClusterIP    │  │ ClusterIP            │  │
│  │ 30000→3000   │  │ :8081        │  │ :8428                │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## macOS Docker Driver Limitation

On macOS with Docker driver, the minikube VM IP (192.168.49.2) is **not directly reachable** from the host. This requires using one of:

1. **minikube tunnel** - For Ingress/LoadBalancer access
2. **Port-forward** - For direct service access
3. **minikube service** - Opens browser to specific service

## Quick Start

### Option 1: Full Access (Recommended)

Start both tunnel and port-forwards:

```bash
# Terminal 1: Start minikube tunnel for ingress
sudo minikube tunnel -p dox-asdlc

# Terminal 2: Start port-forwards for MCP services
./scripts/k8s/port-forward-mcp.sh all
```

Then access:
- **HITL UI**: http://dox.local/ (via tunnel) or http://localhost:3000 (via port-forward)
- **API Docs**: http://dox.local/docs
- **Knowledge Store MCP**: Uses localhost:9200
- **Redis MCP**: Uses localhost:9000

### Option 2: Port-Forward Only (Simpler)

Just use port-forwards without tunnel:

```bash
./scripts/k8s/port-forward-mcp.sh all
```

Access via localhost ports:
- **HITL UI**: http://localhost:3000
- **Elasticsearch**: http://localhost:9200
- **Redis MCP**: http://localhost:9000

### Option 3: Individual Services

Forward specific services as needed:

```bash
# Just Elasticsearch for ks_search
./scripts/k8s/port-forward-mcp.sh elasticsearch

# Just Redis MCP
./scripts/k8s/port-forward-mcp.sh redis

# Just HITL UI
./scripts/k8s/port-forward-mcp.sh hitl
```

## Service Ports Reference

| Service | ClusterIP Port | NodePort | Port-Forward |
|---------|---------------|----------|--------------|
| HITL UI | 3000 | 30000 | localhost:3000 |
| Orchestrator API | 8080 | - | via Ingress |
| Elasticsearch | 9200 | 30920 | localhost:9200 |
| ES MCP Sidecar | 9000 | 30921 | localhost:9001 |
| Redis | 6379 | 30637 | localhost:6379 |
| Redis MCP Sidecar | 9000 | 30900 | localhost:9000 |
| VictoriaMetrics | 8428 | - | localhost:8428 |

## MCP Configuration

The `.mcp.json` expects services at localhost. Ensure port-forwards are running:

```json
{
  "mcpServers": {
    "knowledge-store": {
      "env": {
        "ELASTICSEARCH_URL": "http://localhost:9200"
      }
    },
    "coordination": {
      "comment": "Uses local Redis via Homebrew for CLI coordination"
    }
  }
}
```

## Ingress Routes

When using `minikube tunnel`, the Ingress routes requests:

| Path | Backend | Description |
|------|---------|-------------|
| `/api/*` | orchestrator:8080 | REST API |
| `/health` | orchestrator:8080 | Health check |
| `/docs` | orchestrator:8080 | OpenAPI docs |
| `/openapi.json` | orchestrator:8080 | OpenAPI spec |
| `/*` | hitl-ui:3000 | SPA frontend |

## Troubleshooting

### Port-forward keeps disconnecting

Port-forwards disconnect when:
- Pod restarts
- Network issues
- Terminal closes

Solution: Re-run `./scripts/k8s/port-forward-mcp.sh all`

### "Connection refused" errors

Check if services are running:
```bash
kubectl get pods -n dox-asdlc
```

### Ingress not working

1. Verify tunnel is running: `ps aux | grep "minikube tunnel"`
2. Check ingress: `kubectl get ingress -n dox-asdlc`
3. Verify /etc/hosts has: `127.0.0.1 dox.local`

### MCP tools failing

Ensure port-forwards are running:
```bash
# Check if ports are listening
lsof -i :9200  # Elasticsearch
lsof -i :9000  # Redis MCP
```

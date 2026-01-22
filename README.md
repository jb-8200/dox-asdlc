# aSDLC Implementation Project

An Agentic Software Development Lifecycle system implementing Spec Driven Development with explicit HITL governance gates.

## Quick Start

This project uses Claude Code CLI for development. The workflow enforces planning before implementation.

**Prerequisites:**
- Docker 24+
- Python 3.11+
- Claude Code CLI installed and authenticated

**Development Setup:**

```bash
# Clone and enter project
cd asdlc-project

# Start infrastructure (after P01-F01 is complete)
docker compose up -d

# Create a new feature
./scripts/new-feature.sh P01 F02 "feature-name"

# Validate planning before coding
./scripts/check-planning.sh P01-F02-feature-name

# After implementation, validate completion
./scripts/check-completion.sh P01-F02-feature-name
```

## Project Structure

```
asdlc-project/
├── CLAUDE.md              # Claude Code configuration
├── .claude/               # Claude Code settings and skills
│   ├── settings.json
│   ├── rules/             # Development rules
│   ├── skills/            # Custom skills
│   └── subagents/         # Subagent definitions
├── .workitems/            # Feature planning artifacts
│   └── Pnn-Fnn-{name}/    # Per-feature folders
├── docs/                  # Solution documentation
├── src/                   # Source code
├── tests/                 # Test suites
├── tools/                 # Bash tool wrappers
├── docker/                # Container definitions
├── helm/                  # Kubernetes Helm charts
│   └── dox-asdlc/         # Umbrella chart
│       └── charts/        # Sub-charts (redis, chromadb, etc.)
└── scripts/               # Development scripts
```

## Development Workflow

1. **Plan**: Create work item with design, user stories, and tasks
2. **Validate**: Run `check-planning.sh` to verify completeness
3. **Implement**: Execute tasks using TDD (Red-Green-Refactor)
4. **Complete**: Run `check-completion.sh` to verify all criteria met
5. **Commit**: Commit only when feature is 100% complete

## Kubernetes Deployment

For production-like deployments, the system supports Kubernetes via Helm:

```bash
# Start local Kubernetes cluster (minikube)
./scripts/k8s/start-minikube.sh

# Deploy all services via Helm
./scripts/k8s/deploy.sh

# Or deploy manually with Helm
helm upgrade --install dox-asdlc ./helm/dox-asdlc -f helm/dox-asdlc/values-minikube.yaml

# Verify deployment
kubectl get pods -n dox-asdlc
kubectl get services -n dox-asdlc

# Teardown
./scripts/k8s/teardown.sh
```

## Documentation

- [System Design](docs/System_Design.md) - Technical architecture
- [Main Features](docs/Main_Features.md) - Feature specifications
- [User Stories](docs/User_Stories.md) - Epic-level requirements
- [BRD HTML Diagram](docs/BRD_HTML_Diagram.md) - Blueprint visualization

## License

[License information here]

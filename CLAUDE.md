# aSDLC Project

Agentic Software Development Lifecycle using Claude Agent SDK, Redis coordination, and bash tools.

## PM CLI Role

This main session acts as Project Manager (PM CLI). It:
- Plans and delegates work, does NOT implement code
- Coordinates specialized agents
- Follows the 11-step workflow
- Enforces HITL gates for critical operations

See `.claude/rules/pm-cli.md` for full PM CLI behavior.

## The 11-Step Workflow

```
 1. Workplan         -> PM CLI drafts plan
 2. Planning         -> Planner creates work items
 3. Diagrams         -> Architecture diagrams
 4. Design Review    -> Reviewer validates
 5. Re-plan          -> PM CLI assigns scopes
 6. Parallel Build   -> Backend/Frontend (atomic tasks)
 7. Testing          -> Unit/integration tests
 8. Review           -> Reviewer inspects, issues created
 9. Orchestration    -> E2E, commits
10. DevOps           -> Infrastructure (HITL required)
11. Closure          -> Summary, close issues
```

See `.claude/rules/workflow.md` for full step details and HITL gates.

## Non-Negotiable Rules

1. **Plan before code** - Create `.workitems/Pnn-Fnn-name/` with design.md, user_stories.md, tasks.md BEFORE any implementation
2. **TDD required** - Red -> Green -> Refactor; never move on with failing tests
3. **Commit only complete features** - All tests pass, 100% task completion
4. **Review findings become issues** - All code review findings become GitHub issues
5. **Orchestrator owns meta files** - CLAUDE.md, docs/, contracts/, .claude/**
6. **Task visibility required** - Use TaskCreate/TaskUpdate for all multi-step work to show progress

See `.claude/rules/task-visibility.md` for the task tracking pattern.

## Roles

| Role | Purpose | Domain |
|------|---------|--------|
| planner | Creates planning artifacts only | .workitems/ |
| backend | Backend implementation | P01-P03, P06 |
| frontend | SPA/HITL UI, mock-first | P05 |
| reviewer | Read-only code review | All (read) |
| orchestrator | Coordination, docs, meta, commits | Meta files |
| devops | Docker, K8s, cloud, GitHub Actions | Infrastructure |

See `.claude/agents/` for full agent definitions.

## Commands

```bash
# Planning
./scripts/new-feature.sh P01 F02 "feature-name"
./scripts/check-planning.sh P01-F02-feature-name

# Testing
./tools/test.sh src/path/to/feature
./tools/lint.sh src/
./tools/e2e.sh

# Completion
./scripts/check-completion.sh P01-F02-feature-name

# Issue Tracking
gh issue list                    # List open issues
gh issue create --title "..."    # Create new issue
gh issue close <num>             # Close resolved issue
```

## Path Restrictions

- **backend**: `src/workers/`, `src/orchestrator/`, `src/infrastructure/`, `.workitems/P01-P03,P06`
- **frontend**: `docker/hitl-ui/`, `src/hitl_ui/`, `.workitems/P05-*`
- **devops**: `docker/`, `helm/`, `.github/workflows/`, `scripts/k8s/`
- **orchestrator**: All paths, exclusive: `CLAUDE.md`, `docs/`, `contracts/`, `.claude/`

## Work Item Format

```text
.workitems/Pnn-Fnn-{description}/
├── design.md        # Technical approach, interfaces
├── user_stories.md  # Acceptance criteria
└── tasks.md         # Atomic tasks (<2hr each)
```

## Skills

| Skill | Purpose |
|-------|---------|
| feature-planning | Create work item artifacts |
| tdd-execution | Red-Green-Refactor cycle |
| feature-completion | Validate and complete feature |
| contract-update | API contract changes |
| diagram-builder | Mermaid diagrams |

## Environment Tiers

The project uses a tiered environment strategy:

| Tier | Platform | Use Case |
|------|----------|----------|
| **Local Dev** | Docker Compose | Rapid iteration (recommended for daily dev) |
| **Local Staging** | K8s (minikube) | Helm chart testing |
| **Remote Lab** | GCP Cloud Run | Demos |
| **Remote Staging** | GCP GKE | Pre-production |

**Quick Start (Local Dev):**
```bash
cd docker && docker compose up -d
# UI: http://localhost:3000
# API: http://localhost:8080
```

See `docs/environments/README.md` for full environment guides.

## KnowledgeStore MCP

The project includes a semantic search MCP for exploring the indexed codebase.

### Tools Available

| Tool | Purpose |
|------|---------|
| `ks_search` | Semantic search across indexed code and docs |
| `ks_get` | Retrieve specific document by ID |
| `ks_index` | Add new documents to the index |
| `ks_health` | Check Elasticsearch status |

### Usage Examples

```bash
# Search for implementation patterns
ks_search query="HITL gate implementation" top_k=5

# Get specific file content
ks_get doc_id="src/core/interfaces.py:0"
```

### When to Use

- Exploring unfamiliar parts of the codebase
- Finding implementation patterns
- Locating related code during reviews
- Understanding how features are connected

### Configuration

MCP servers connect to localhost services exposed by Docker Compose or K8s port-forwards:
- **knowledge-store**: Elasticsearch at `localhost:9200`
- **coordination**: Redis at `localhost:6379`

**Local Dev (Docker Compose):** Services are automatically exposed on localhost.

**K8s (minikube):** Start port-forwards for MCP access:
```bash
./scripts/k8s/port-forward-mcp.sh all  # ES, Redis, HITL UI
```

## Multi-Session Infrastructure

The project supports running multiple Claude CLI sessions in parallel, each in an isolated git worktree with a unique identity.

### Quick Start

To start an agent session in a separate terminal:

```bash
# Start backend agent session
./scripts/start-agent-session.sh backend

# Follow the printed instructions:
cd .worktrees/backend && export CLAUDE_INSTANCE_ID=backend && claude
```

### Worktree Commands

| Command | Purpose |
|---------|---------|
| `./scripts/start-agent-session.sh <role>` | Complete setup for an agent session |
| `./scripts/worktree/setup-agent.sh <role>` | Create worktree and branch |
| `./scripts/worktree/list-agents.sh` | List all agent worktrees (JSON) |
| `./scripts/worktree/teardown-agent.sh <role> [--merge\|--abandon]` | Remove worktree |
| `./scripts/worktree/merge-agent.sh <role>` | Merge agent branch to main |

Valid roles: `backend`, `frontend`, `orchestrator`, `devops`

### Session Lifecycle

```
1. Setup     -> ./scripts/start-agent-session.sh <role>
               - Creates worktree at .worktrees/<role>/
               - Creates branch agent/<role>/active
               - Configures git identity

2. Work      -> cd .worktrees/<role> && export CLAUDE_INSTANCE_ID=<role> && claude
               - Session validates identity on startup
               - Registers presence in Redis
               - Checks for pending notifications

3. Commit    -> Work is committed to agent/<role>/active branch
               - Isolated from main and other agents

4. Merge     -> ./scripts/worktree/merge-agent.sh <role>
               - Merges agent branch to main
               - Fast-forward preferred

5. Teardown  -> ./scripts/worktree/teardown-agent.sh <role> --merge
               - Deregisters session presence
               - Removes worktree
               - Optionally merges changes first
```

### Session Identity

Each agent session has a unique identity:

| Role | Git Email | CLAUDE_INSTANCE_ID |
|------|-----------|-------------------|
| backend | claude-backend@asdlc.local | backend |
| frontend | claude-frontend@asdlc.local | frontend |
| orchestrator | claude-orchestrator@asdlc.local | orchestrator |
| devops | claude-devops@asdlc.local | devops |
| pm | (main repo email) | pm |

Identity is resolved from:
1. `CLAUDE_INSTANCE_ID` environment variable (preferred)
2. `git config user.email` (fallback)

### Presence Tracking

Sessions register their presence in Redis for coordination:
- **Heartbeat**: Sessions should heartbeat every 60 seconds
- **Stale Threshold**: 5 minutes without heartbeat marks session stale
- **Startup**: Session presence registered automatically
- **Shutdown**: Presence deregistered on worktree teardown

Check presence with the coordination MCP:
```
coord_get_presence
```

### Troubleshooting

**Session identity not recognized:**
```bash
# Set identity explicitly
export CLAUDE_INSTANCE_ID=backend

# Or configure git email
git config user.email claude-backend@asdlc.local
```

**Worktree already exists:**
```bash
# Script is idempotent - safe to run again
./scripts/worktree/setup-agent.sh backend
```

**Uncommitted changes in worktree:**
```bash
# Merge changes to main before removing
./scripts/worktree/teardown-agent.sh backend --merge

# Or abandon changes
./scripts/worktree/teardown-agent.sh backend --abandon
```

**Redis not available:**
- Sessions can start without Redis (warnings only)
- Coordination features will be limited
- Presence tracking disabled

**Merge conflicts:**
```bash
# merge-agent.sh will report conflicts
./scripts/worktree/merge-agent.sh backend

# Resolve manually in main repo, then teardown
cd /path/to/main/repo
git status  # see conflicts
# ... resolve conflicts ...
git add <files>
git commit

# Then teardown worktree
./scripts/worktree/teardown-agent.sh backend --abandon
```

## Related Docs

- @docs/environments/README.md - Environment tiers
- @docs/Main_Features.md - Feature specs
- @docs/K8s_Service_Access.md - K8s networking

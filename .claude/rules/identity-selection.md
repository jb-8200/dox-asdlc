# Role-Based Subagents

## Overview

This project uses role-specific subagents instead of interactive identity selection. Each subagent has built-in path restrictions, coordination protocols, and domain expertise.

## Available Role Subagents

| Subagent | Domain | Features |
|----------|--------|----------|
| `backend` | Workers, infrastructure | P01-P03, P06 |
| `frontend` | HITL UI, React | P05 |
| `orchestrator` | Meta files, coordination | All phases |

## When to Invoke Each Subagent

### Backend Subagent

Invoke for:
- Implementing worker agents (`src/workers/`)
- Orchestrator service changes (`src/orchestrator/`)
- Infrastructure components (`src/infrastructure/`)
- Core shared modules (`src/core/`)
- Backend Docker containers (`docker/workers/`, `docker/orchestrator/`)

```
"Use the backend subagent to implement the worker pool"
```

### Frontend Subagent

Invoke for:
- HITL Web UI components (`docker/hitl-ui/`)
- UI Python backend (`src/hitl_ui/`)
- Frontend tests and E2E tests

```
"Use the frontend subagent to add the approval dialog"
```

### Orchestrator Subagent

Invoke for:
- Documentation updates (`docs/`)
- Contract changes (`contracts/`)
- Rule updates (`.claude/rules/`)
- Processing coordination messages
- Resolving blocking issues

```
"Use the orchestrator subagent to update the API contract"
```

## Role Permissions Summary

| Role | Can Modify | Cannot Modify | Commits to Main |
|------|------------|---------------|-----------------|
| orchestrator | All files | - | Yes |
| backend | src/workers/, src/orchestrator/, src/infrastructure/, .workitems/P01-P03,P06 | src/hitl_ui/, docs/, contracts/, CLAUDE.md | Yes |
| frontend | src/hitl_ui/, docker/hitl-ui/, .workitems/P05-* | src/workers/, docs/, contracts/, CLAUDE.md | Yes |

## Git Identity

When a subagent starts work, it sets the appropriate git identity:

| Subagent | Git Email | Git Name |
|----------|-----------|----------|
| backend | `claude-backend@asdlc.local` | Claude Backend |
| frontend | `claude-frontend@asdlc.local` | Claude Frontend |
| orchestrator | `claude-orchestrator@asdlc.local` | Claude Orchestrator |

## Coordination

Each role subagent has built-in Redis coordination:
- Checks pending messages on start
- Publishes status updates on completion
- Can publish BLOCKING_ISSUE to orchestrator when stuck
- Acknowledges processed messages

See `.claude/agents/` for full subagent definitions.

## Legacy: Interactive Selection (Deprecated)

The previous `IDENTITY SELECTION REQUIRED` prompt system has been replaced by subagents. If you see that message, it means the session-start hook needs updating.

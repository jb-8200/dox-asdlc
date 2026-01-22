# Parallel CLI Coordination Rules

These rules govern how the three Claude CLI instances work simultaneously on this project.

---

## 3-CLI Architecture

```
┌─────────────────┐     ┌─────────────────┐
│  Backend-CLI    │     │  Frontend-CLI   │
│  (agent/)       │     │  (ui/)          │
│                 │     │                 │
│  - Workers      │     │  - HITL UI      │
│  - Orchestrator │     │  - Components   │
│  - Infra        │     │  - Frontend     │
└────────┬────────┘     └────────┬────────┘
         │                       │
         │  READY_FOR_REVIEW     │
         └───────────┬───────────┘
                     ▼
         ┌─────────────────────┐
         │  Orchestrator-CLI   │
         │  (main)             │
         │                     │
         │  - Code Review      │
         │  - E2E Tests        │
         │  - Contract Valid.  │
         │  - Merge to main    │
         └─────────────────────┘
```

### Instance Roles

| Instance | ID | Branch Prefix | Primary Responsibility |
|----------|-----|---------------|------------------------|
| Backend-CLI | `backend` | `agent/` | Workers, orchestrator, infrastructure |
| Frontend-CLI | `frontend` | `ui/` | HITL Web UI, frontend components |
| Orchestrator-CLI | `orchestrator` | (none) | Review, E2E tests, merge to main |

---

## MANDATORY: Session Start Checklist

**Run this BEFORE any other work:**

```bash
./scripts/check-compliance.sh --session-start
```

**If this fails, DO NOT proceed. Fix compliance issues first.**

The session start check verifies:
- `CLAUDE_INSTANCE_ID` is set
- You are on the correct branch for your instance
- No pending coordination messages require acknowledgment
- No file locks conflict with your planned work

**Manual verification (if script unavailable):**
```bash
# 1. Verify identity
echo "Instance: $CLAUDE_INSTANCE_ID, Branch Prefix: $CLAUDE_BRANCH_PREFIX"
[ -z "$CLAUDE_INSTANCE_ID" ] && echo "ERROR: Run 'source scripts/cli-identity.sh <backend|frontend|orchestrator>' first"

# 2. Verify branch (feature CLIs only)
git branch --show-current | grep "^${CLAUDE_BRANCH_PREFIX}" || echo "ERROR: Wrong branch!"

# 3. Check coordination messages
./scripts/coordination/check-messages.sh

# 4. Acknowledge any pending messages BEFORE starting work
./scripts/coordination/ack-message.sh <message-id>
```

---

## Planning Artifact Requirements

**MANDATORY:** ALL features require formal planning artifacts in `.workitems/` BEFORE any code.

**Even if the user provides:**
- Detailed inline implementation plans
- Complete specifications in chat
- Copy-paste ready code
- "Just do X" instructions with full context

**You MUST still:**
1. Run `./scripts/new-feature.sh Pnn Fnn "description"`
2. Populate `design.md`, `tasks.md`, `user_stories.md`
3. Commit planning artifacts to git
4. THEN begin implementation

**No exceptions.** Inline plans supplement but do NOT replace formal planning artifacts.

**Ownership:**
- `.workitems/` is **SHARED** (not a meta file)
- Backend-CLI: Creates and manages `.workitems/P01-*`, `P02-*`, `P03-*`, `P06-*`
- Frontend-CLI: Creates and manages `.workitems/P05-*`
- Orchestrator: Can read all, modify any, but does NOT create planning for feature CLIs

**Why this matters:**
- Planning artifacts are the source of truth for feature scope
- They enable TDD workflow (tasks → tests → code)
- They provide review checkpoints for orchestrator
- They prevent scope creep and "just one more thing" drift

**Common mistake:** Treating user's detailed prompt as permission to skip `.workitems/` creation. This is ALWAYS a workflow violation.

---

## Rule 1: Instance Identity

**BEFORE starting any work, verify your instance identity:**

```bash
echo $CLAUDE_INSTANCE_ID
```

If not set, run:
```bash
source scripts/cli-identity.sh <backend|frontend|orchestrator>
```

Your identity determines which files you can modify and which branches you can commit to.

## Rule 2: Branch Discipline

**Each instance commits ONLY to its designated branch prefix:**

| Instance | Branch Prefix | Example |
|----------|--------------|---------|
| Backend-CLI | `agent/` | `agent/P03-F01-worker-pool` |
| Frontend-CLI | `ui/` | `ui/P05-F01-hitl-ui` |
| Orchestrator-CLI | (none) | Works directly on `main` |

**Feature CLIs (Backend, Frontend) NEVER commit directly to:**
- `main` branch (only Orchestrator can)
- Another instance's branch prefix
- `contracts/*` without coordination

**Before committing, verify:**
```bash
git branch --show-current | grep "^${CLAUDE_BRANCH_PREFIX}"
```

## Rule 3: File Boundaries

**Backend-CLI (CLAUDE_INSTANCE_ID=backend):**
- CAN modify: `src/workers/`, `src/orchestrator/`, `src/infrastructure/`, `docker/workers/`, `docker/orchestrator/`
- CAN modify: `.workitems/P01-*`, `.workitems/P02-*`, `.workitems/P03-*`, `.workitems/P06-*` (planning & tasks)
- CAN read: `contracts/`, `src/core/`, `docs/`
- CANNOT touch: `src/hitl_ui/`, `docker/hitl-ui/`, `main` branch, meta files

**Frontend-CLI (CLAUDE_INSTANCE_ID=frontend):**
- CAN modify: `src/hitl_ui/`, `docker/hitl-ui/`, `tests/unit/hitl_ui/`
- CAN modify: `.workitems/P05-*` (planning & tasks)
- CAN read: `contracts/`, `src/core/`, `docs/`
- CANNOT touch: `src/workers/`, `src/orchestrator/`, `src/infrastructure/`, `main` branch, meta files

**Orchestrator-CLI (CLAUDE_INSTANCE_ID=orchestrator) — Master Agent:**
- EXCLUSIVE ownership of meta files (see below)
- CAN read: All files (for review purposes)
- CAN modify: `main` branch (via merge)
- CAN manage: All project configuration and documentation
- Primary role: Review, merge, and maintain project integrity

**Meta Files (Orchestrator EXCLUSIVE ownership):**

| Category | Files |
|----------|-------|
| Project Config | `CLAUDE.md`, `README.md` |
| Rules | `.claude/rules/**` |
| Skills | `.claude/skills/**` |
| Documentation | `docs/**` |
| Contracts | `contracts/**` |
| Coordination | `.claude/coordination/**` |

**Note:** `.workitems/` is NOT in the exclusive list — feature CLIs manage their own planning artifacts.

**Feature CLIs CANNOT modify other meta files directly.** To request changes:
```bash
./scripts/coordination/publish-message.sh META_CHANGE_REQUEST "<file>" "<description>" --to orchestrator
```

**Shared source files (require coordination):**
- `src/core/interfaces.py` — Coordinate via messages
- `src/core/events.py` — Coordinate via messages

## Rule 4: Feature Development Workflow

**For Backend-CLI and Frontend-CLI:**

1. **Start Session:**
   ```bash
   source scripts/cli-identity.sh backend  # or frontend
   ./scripts/check-compliance.sh --session-start
   ```

2. **Work on Feature Branch:**
   ```bash
   git checkout -b agent/P03-F01-feature-name  # or ui/...
   # Develop feature with TDD
   # Run local tests: ./tools/test.sh
   # Run linter: ./tools/lint.sh
   ```

3. **Request Review:**
   ```bash
   # When feature complete
   ./scripts/coordination/publish-message.sh READY_FOR_REVIEW "agent/P03-F01-feature-name" "Feature complete" --to orchestrator
   ```

4. **Wait for Response:**
   - `REVIEW_COMPLETE` → Feature merged to main
   - `REVIEW_FAILED` → Fix issues and re-submit

## Rule 5: Contract Changes (Orchestrator-Mediated)

**Any change to `contracts/` MUST follow this protocol:**

1. **Proposer creates change:**
   ```bash
   # Create proposed change
   cp contracts/current/events.json contracts/proposed/events-v1.1.0.json
   # Edit the proposed file
   ./scripts/coordination/publish-message.sh CONTRACT_CHANGE_PROPOSED events "Add new field X" --to orchestrator
   ```

2. **Orchestrator reviews and notifies:**
   ```bash
   # Orchestrator sends to consumer CLI
   ./scripts/coordination/publish-message.sh CONTRACT_REVIEW_NEEDED events "Backend proposes adding field X" --to frontend
   ```

3. **Consumer provides feedback:**
   ```bash
   ./scripts/coordination/publish-message.sh CONTRACT_FEEDBACK events "Approved - compatible with UI" --to orchestrator
   ```

4. **Orchestrator approves:**
   ```bash
   # Move to versions, update symlinks
   mv contracts/proposed/events-v1.1.0.json contracts/versions/v1.1.0/events.json
   ln -sf ../versions/v1.1.0/events.json contracts/current/events.json
   # Update CHANGELOG.md
   ./scripts/coordination/publish-message.sh CONTRACT_APPROVED events "v1.1.0 approved" --to all
   ```

**NEVER modify `contracts/current/*` or `contracts/versions/*` without orchestrator approval.**

## Rule 6: Coordination Messages

**Check for messages at the start of each work session:**
```bash
./scripts/coordination/check-messages.sh
```

**Acknowledge messages promptly:**
```bash
./scripts/coordination/ack-message.sh <message-id>
```

**Message Types:**

| Type | Direction | Purpose |
|------|-----------|---------|
| `READY_FOR_REVIEW` | Feature → Orchestrator | Request branch review and merge |
| `REVIEW_COMPLETE` | Orchestrator → Feature | Review passed, merged to main |
| `REVIEW_FAILED` | Orchestrator → Feature | Review failed, lists issues |
| `CONTRACT_CHANGE_PROPOSED` | Feature → Orchestrator | Propose contract change |
| `CONTRACT_REVIEW_NEEDED` | Orchestrator → Consumer | Request contract feedback |
| `CONTRACT_FEEDBACK` | Consumer → Orchestrator | Provide contract feedback |
| `CONTRACT_APPROVED` | Orchestrator → All | Contract change approved |
| `CONTRACT_REJECTED` | Orchestrator → Proposer | Contract change rejected |
| `META_CHANGE_REQUEST` | Feature → Orchestrator | Request meta file change |
| `META_CHANGE_COMPLETE` | Orchestrator → Feature | Meta file change completed |
| `INTERFACE_UPDATE` | Any → Any | Shared interface notification |
| `BLOCKING_ISSUE` | Any → Any | Work blocked, needs help |

## Rule 7: Status Updates

**Update your status when:**
- Starting work on a new task
- Completing a task
- Encountering a blocking issue
- Ending your session

**Status file location:** `.claude/coordination/status.json`

The status is automatically updated by `cli-identity.sh` when activating/deactivating.

## Rule 8: Review Process (Feature CLIs)

**Before requesting review, ensure:**

1. All tests pass: `./tools/test.sh`
2. Linter passes: `./tools/lint.sh`
3. Planning artifacts complete: `tasks.md` shows 100%
4. No unresolved coordination messages
5. Branch is up to date with main

**Request review:**
```bash
./scripts/coordination/publish-message.sh READY_FOR_REVIEW "<branch>" "Feature complete" --to orchestrator
```

**After receiving REVIEW_FAILED:**
1. Read the failure reasons in the message
2. Fix all listed issues
3. Run tests again
4. Re-submit review request

## Rule 9: Mock-First Development (Frontend-CLI)

**Frontend-CLI MUST create mocks that match contract schemas:**

Location: `src/hitl_ui/api/mocks/`

```python
# Example: src/hitl_ui/api/mocks/gates_mock.py
from contracts.current.hitl_api import GateRequest  # Validate against schema

def mock_pending_gates() -> list[GateRequest]:
    """Return mock data matching hitl_api.json contract."""
    pass
```

When Backend-CLI delivers real implementation, mocks are swapped seamlessly.

## Rule 10: Conflict Prevention

**If you need to modify a shared file:**

1. Check `.claude/coordination/locks/` for existing lock
2. Create lock file: `echo "$CLAUDE_INSTANCE_ID" > .claude/coordination/locks/<filename>.lock`
3. Publish message notifying other instances
4. Make changes
5. Commit
6. Remove lock file
7. Publish unlock message

**If a lock exists, wait or coordinate with the locking instance.**

## Rule 11: Session End Protocol

**Before ending your session:**

1. Commit all completed work to your branch
2. Update task progress in `.workitems/`
3. Update status file:
   ```bash
   source scripts/cli-identity.sh deactivate
   ```
4. Check for any unanswered coordination messages
5. Leave clear notes in `tasks.md` for resumption

---

## Quick Reference: Common Workflows

### Backend-CLI: Complete a Feature
```bash
source scripts/cli-identity.sh backend
./scripts/check-compliance.sh --session-start
# ... develop feature ...
./tools/test.sh && ./tools/lint.sh
./scripts/coordination/publish-message.sh READY_FOR_REVIEW "agent/P03-F01" "Complete"
# Wait for REVIEW_COMPLETE or REVIEW_FAILED
```

### Frontend-CLI: Complete a Feature
```bash
source scripts/cli-identity.sh frontend
./scripts/check-compliance.sh --session-start
# ... develop feature ...
./tools/test.sh && ./tools/lint.sh
./scripts/coordination/publish-message.sh READY_FOR_REVIEW "ui/P05-F01" "Complete"
# Wait for REVIEW_COMPLETE or REVIEW_FAILED
```

### Orchestrator-CLI: Review and Merge
```bash
source scripts/cli-identity.sh orchestrator
./scripts/coordination/check-messages.sh --reviews
./scripts/orchestrator/review-branch.sh agent/P03-F01
# If review passes:
./scripts/orchestrator/merge-branch.sh agent/P03-F01
./scripts/coordination/publish-message.sh REVIEW_COMPLETE "agent/P03-F01" "Merged as abc123" --to backend
```

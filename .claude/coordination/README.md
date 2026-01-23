# CLI Agent Coordination System

This directory contains configuration and documentation for coordinating multiple Claude CLI instances working on the same codebase.

## Architecture

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

## Starting a Session

**IMPORTANT:** Always use the launcher scripts to start Claude Code sessions.

```bash
# For backend development (workers, orchestrator, infrastructure)
./start-backend.sh

# For frontend development (HITL Web UI)
./start-frontend.sh

# For review/merge operations (orchestrator only)
./start-orchestrator.sh
```

The launcher scripts:
1. Create `.claude/instance-identity.json` with role-specific permissions
2. Set git user.name/email for commit attribution
3. Launch Claude Code with the identity configured

## Identity Enforcement

Identity is enforced at multiple layers:

### Layer 1: SessionStart Hook
- Runs when Claude Code starts
- Displays the active role and permissions
- Warns if on the wrong branch

### Layer 2: UserPromptSubmit Hook
- Runs before each user prompt is processed
- **BLOCKS** if no identity file exists (launcher not used)
- **BLOCKS** if on the wrong branch for the role

### Layer 3: PreToolUse Hook
- Runs before Edit, Write, and Bash (git) operations
- **BLOCKS** edits to forbidden paths
- **BLOCKS** git commits/pushes on wrong branches

### Layer 4: Pre-Commit Hook
- Runs before git commits (last line of defense)
- **BLOCKS** commits if identity indicates wrong branch
- Reads from `.claude/instance-identity.json`

## Role Permissions

### Backend CLI (`./start-backend.sh`)

| Permission | Value |
|------------|-------|
| Branch prefix | `agent/` |
| Can merge to main | No |
| Can modify meta files | No |

**Allowed paths:**
- `src/workers/`, `src/orchestrator/`, `src/infrastructure/`
- `docker/workers/`, `docker/orchestrator/`
- `.workitems/P01-*`, `P02-*`, `P03-*`, `P06-*`

**Forbidden paths:**
- `src/hitl_ui/`, `docker/hitl-ui/`
- `CLAUDE.md`, `README.md`, `.claude/rules/`, `docs/`, `contracts/`

### Frontend CLI (`./start-frontend.sh`)

| Permission | Value |
|------------|-------|
| Branch prefix | `ui/` |
| Can merge to main | No |
| Can modify meta files | No |

**Allowed paths:**
- `src/hitl_ui/`, `docker/hitl-ui/`
- `.workitems/P05-*`

**Forbidden paths:**
- `src/workers/`, `src/orchestrator/`, `src/infrastructure/`
- `CLAUDE.md`, `README.md`, `.claude/rules/`, `docs/`, `contracts/`

### Orchestrator CLI (`./start-orchestrator.sh`)

| Permission | Value |
|------------|-------|
| Branch prefix | (none - works on main) |
| Can merge to main | Yes |
| Can modify meta files | Yes |

**Exclusive ownership of:**
- `CLAUDE.md`, `README.md`
- `.claude/rules/`, `.claude/skills/`
- `docs/`, `contracts/`

## What Gets Blocked

### No Launcher Used
```
BLOCKED: NO LAUNCHER USED

You must start Claude Code using a launcher script:
  ./start-backend.sh      # For backend development
  ./start-frontend.sh     # For frontend development
  ./start-orchestrator.sh # For review/merge operations

Please exit and restart using the appropriate launcher.
```

### Wrong Branch
```
BLOCKED: WRONG BRANCH

Instance: backend
Expected branch prefix: agent/
Current branch: main

Switch to the correct branch before continuing:
  git checkout -b agent/<feature-name>
  git checkout agent/<existing-branch>
```

### Forbidden Path
```
BLOCKED: FORBIDDEN PATH

Instance 'backend' cannot modify: src/hitl_ui/App.tsx
This path is restricted for your role.
```

### Git Commit on Wrong Branch
```
BLOCKED: BRANCH VIOLATION - GIT COMMIT BLOCKED

Instance 'backend' can only commit to agent/* branches.
Current branch: main
Switch to a correct branch first.
```

## Message Types for Coordination

| Type | Direction | Purpose |
|------|-----------|---------|
| `READY_FOR_REVIEW` | Feature → Orchestrator | Request branch review and merge |
| `REVIEW_COMPLETE` | Orchestrator → Feature | Review passed, merged to main |
| `REVIEW_FAILED` | Orchestrator → Feature | Review failed, lists issues |
| `CONTRACT_CHANGE_PROPOSED` | Feature → Orchestrator | Propose contract change |
| `CONTRACT_APPROVED` | Orchestrator → All | Contract change approved |
| `META_CHANGE_REQUEST` | Feature → Orchestrator | Request meta file change |
| `BLOCKING_ISSUE` | Any → Any | Work blocked, needs help |

## Files in This Directory

| File | Purpose |
|------|---------|
| `README.md` | This documentation |
| `status.json` | Instance status tracking (runtime) |

## Troubleshooting

### "BLOCKED: NO LAUNCHER USED"
Exit Claude Code and restart using `./start-backend.sh`, `./start-frontend.sh`, or `./start-orchestrator.sh`.

### "BLOCKED: WRONG BRANCH"
Switch to a branch with the correct prefix:
- Backend: `git checkout -b agent/<feature>`
- Frontend: `git checkout -b ui/<feature>`

### Hooks not running
Check that `.claude/settings.json` has the hooks section configured and that the hook scripts in `scripts/hooks/` are executable.

### Identity file not found
Make sure you used a launcher script. The identity file is created at `.claude/instance-identity.json` by the launcher.

## Reverting This System

If the hooks cause issues:
1. Remove the `hooks` section from `.claude/settings.json`
2. Delete `scripts/hooks/` directory
3. Revert `.git/hooks/pre-commit` to the original env var check
4. Run `claude` directly without launchers

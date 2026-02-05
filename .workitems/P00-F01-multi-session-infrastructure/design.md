# Feature Design: P00-F01 Multi-Session Infrastructure

## Overview

This feature enables multiple Claude CLI sessions to work in parallel on isolated git branches using git worktrees, with enforced unique identities and mandatory coordination. It provides the infrastructure for true parallel agent development without file conflicts.

## Problem Statement

Current limitations preventing effective multi-session parallel work:

1. **No git worktree support** - Multiple agents would conflict editing the same files on the same branch
2. **Identity enforcement exists but no validation at startup** - Sessions can start without proper identity configured
3. **No rules requiring PM/Orchestrator to check coordination messages** - Messages can be missed
4. **No mechanism to see which agent sessions are active** - No visibility into parallel execution state

## Goals

1. Enable isolated parallel development using git worktrees per agent role
2. Enforce unique identity validation before session starts
3. Require coordination message checks at every PM/Orchestrator turn
4. Provide visibility into active agent sessions via presence tracking
5. Simplify agent session startup with automated setup

## Dependencies

### Internal Dependencies

- **P01-F04**: CLI Coordination Migration to Redis - COMPLETE
  - Provides `CoordinationClient` with presence tracking
  - Provides `coord_get_presence`, `coord_publish_message`, `coord_get_notifications`
  - Redis backend for real-time coordination

- **P01-F07**: CLI Subagents - COMPLETE
  - Defines agent roles (backend, frontend, orchestrator, devops)
  - Establishes path restrictions per agent
  - Git email to instance ID mapping

### External Dependencies

- Git 2.20+ (git worktree support)
- Redis (already deployed)
- Claude CLI

## Technical Approach

### 1. Git Worktree Architecture

Each agent role operates in its own git worktree with an isolated branch:

```
project-root/                      # Main worktree (PM CLI, main branch)
.worktrees/
  backend/                         # Backend agent worktree
    .git -> ../../.git/worktrees/backend
    (full project files)
  frontend/                        # Frontend agent worktree
    .git -> ../../.git/worktrees/frontend
    (full project files)
  orchestrator/                    # Orchestrator agent worktree
    ...
  devops/                          # DevOps agent worktree
    ...
```

**Branch Naming Convention**: `agent/{role}/active`

**Worktree Location**: `.worktrees/{role}/`

**Benefits**:
- Complete file system isolation between agents
- Each agent has its own working directory state
- Changes can be committed independently and merged to main
- Git tracks modifications across all worktrees

### 2. Worktree Lifecycle

```
Setup Phase:
1. Create worktree: git worktree add .worktrees/{role} -b agent/{role}/active
2. Configure git identity in worktree
3. Register presence in Redis

Teardown Phase:
1. Merge changes back to main (or create PR)
2. Unregister presence from Redis
3. Remove worktree: git worktree remove .worktrees/{role}
```

### 3. Session Startup Validation

Every Claude CLI session must pass startup validation:

```
+----------------------------------+
|        Session Startup           |
+----------------------------------+
|                                  |
| 1. Check CLAUDE_INSTANCE_ID or   |
|    git email is configured       |
|    - Fail fast if neither set    |
|                                  |
| 2. Validate identity is known    |
|    - Must be: backend, frontend, |
|      orchestrator, devops, pm    |
|                                  |
| 3. Register presence via Redis   |
|    - coord_publish_message       |
|      HEARTBEAT                   |
|                                  |
| 4. Check pending notifications   |
|    - coord_get_notifications     |
|    - Display any unread messages |
|                                  |
| 5. Verify worktree (non-PM only) |
|    - Must be in correct worktree |
|    - Branch must match identity  |
|                                  |
+----------------------------------+
```

### 4. Coordination Enforcement

**PM CLI Mandatory Checks** (add to `.claude/rules/pm-cli.md`):

```
PM CLI MUST at start of EVERY response:
1. Call coord_check_messages to_instance=pm pending_only=true
2. If pending messages exist:
   - Display summary to user
   - Ask if should handle before proceeding
3. Call coord_get_presence to see active agents
```

**Orchestrator Mandatory Checks** (add to `.claude/rules/orchestrator.md`):

```
Orchestrator MUST after EVERY operation:
1. Publish STATUS_UPDATE with operation result
2. Call coord_check_messages pending_only=true
3. Acknowledge all pending messages before completing
```

### 5. Presence Management Extension

Extend coordination MCP with automatic heartbeat:

```python
# New MCP tool: coord_register_presence
async def coord_register_presence(
    role: str,
    worktree_path: str,
    session_id: str,
) -> dict:
    """Register session as active with metadata."""

# Heartbeat auto-refresh
# - Every 60 seconds while session active
# - Redis key with 5-minute TTL
# - Stale detection: no heartbeat for 5 minutes = inactive

# New MCP tool: coord_deregister_presence
async def coord_deregister_presence(
    role: str,
) -> dict:
    """Mark session as inactive."""
```

### 6. Agent Session Launcher

Single script to bootstrap an agent session:

```bash
#!/bin/bash
# scripts/start-agent-session.sh

ROLE=$1

# 1. Create/verify worktree
./scripts/worktree/setup-agent.sh $ROLE

# 2. Set git identity
git config user.email "claude-${ROLE}@asdlc.local"
git config user.name "Claude ${ROLE^} Agent"

# 3. Set environment
export CLAUDE_INSTANCE_ID=$ROLE

# 4. Change to worktree directory
cd .worktrees/$ROLE

# 5. Start Claude CLI
# (User invokes claude after script completes)
echo "Worktree ready at .worktrees/$ROLE"
echo "Run: cd .worktrees/$ROLE && claude"
```

## Interfaces

### Provided Interfaces

**Worktree Scripts** (`scripts/worktree/`)

```bash
# Setup agent worktree
./scripts/worktree/setup-agent.sh <role>
# Creates: .worktrees/<role>/ with branch agent/<role>/active
# Returns: 0 on success, 1 on failure

# List active worktrees
./scripts/worktree/list-agents.sh
# Output: JSON array of {role, branch, path, status}

# Teardown agent worktree
./scripts/worktree/teardown-agent.sh <role> [--merge|--abandon]
# Default: prompts for merge strategy
# --merge: merges to main, removes worktree
# --abandon: removes worktree without merge

# Merge agent changes
./scripts/worktree/merge-agent.sh <role>
# Merges agent/<role>/active into main
```

**Startup Hook** (`.claude/hooks/startup.sh`)

```bash
# Called by Claude CLI at session start
# Validates identity and registers presence
# Exit code 0: proceed with session
# Exit code 1: abort session
```

**Extended Coordination MCP**

```python
# Additional tools in coordination MCP server

def coord_register_presence(
    role: str,
    worktree_path: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Register session as active."""

def coord_deregister_presence(role: str) -> dict[str, Any]:
    """Mark session as inactive."""

def coord_heartbeat(role: str) -> dict[str, Any]:
    """Update heartbeat timestamp."""
```

### Required Interfaces

- `src/infrastructure/coordination/client.py` - Existing coordination client
- `src/infrastructure/coordination/mcp_server.py` - Existing MCP server
- `.claude/rules/pm-cli.md` - PM CLI behavior rules
- `.claude/rules/orchestrator.md` - Orchestrator behavior rules

## File Structure

```
scripts/
  worktree/
    setup-agent.sh           # Create/configure agent worktree
    teardown-agent.sh        # Cleanup agent worktree
    list-agents.sh           # List active worktrees
    merge-agent.sh           # Merge agent branch to main
  start-agent-session.sh     # Combined session launcher

.claude/
  hooks/
    startup.sh               # Session startup validation hook
  rules/
    coordination-protocol.md # Message flow and heartbeat rules
    pm-cli.md               # Updated with coordination requirements
    orchestrator.md         # Updated with status update requirements

src/
  infrastructure/
    coordination/
      client.py              # Extended with heartbeat auto-refresh
      mcp_server.py          # Extended with presence tools

.worktrees/                  # Created at runtime (gitignored)
  backend/
  frontend/
  orchestrator/
  devops/
```

## Coordination Protocol Design

### Message Types for Multi-Session

| Type | Direction | Purpose |
|------|-----------|---------|
| `HEARTBEAT` | Agent -> Redis | Session alive signal |
| `SESSION_START` | Agent -> All | Announce session started |
| `SESSION_END` | Agent -> All | Announce session ending |
| `WORKTREE_CONFLICT` | System -> PM | Conflict detected in merge |

### Heartbeat Protocol

```
Heartbeat Frequency: Every 60 seconds
Heartbeat TTL: 5 minutes
Stale Detection: No heartbeat for 5 minutes

Redis Key: coord:presence:{role}
Fields:
  - active: "1" or "0"
  - last_heartbeat: ISO-8601 timestamp
  - session_id: UUID
  - worktree_path: absolute path to worktree
  - branch: current branch name
```

### Presence Query Response

```json
{
  "success": true,
  "instances": {
    "backend": {
      "active": true,
      "last_heartbeat": "2026-02-05T10:00:00Z",
      "session_id": "abc-123",
      "worktree_path": "/path/to/.worktrees/backend",
      "branch": "agent/backend/active",
      "stale": false
    },
    "frontend": {
      "active": false,
      "last_heartbeat": "2026-02-05T09:30:00Z",
      "stale": true
    }
  }
}
```

## Error Handling

### Worktree Errors

| Error | Cause | Recovery |
|-------|-------|----------|
| Worktree already exists | `setup-agent.sh` called twice | Skip creation, verify state |
| Branch already exists | Previous session not cleaned up | Reuse or force recreate |
| Merge conflict | Concurrent edits to same file | Manual resolution required |
| Dirty worktree | Uncommitted changes on teardown | Prompt user to commit/stash |

### Session Errors

| Error | Cause | Recovery |
|-------|-------|----------|
| No identity configured | Missing CLAUDE_INSTANCE_ID and git email | Fail with setup instructions |
| Unknown role | Identity not in allowed list | Fail with valid roles |
| Redis unavailable | Coordination backend down | Fail with Redis startup instructions |
| Worktree mismatch | Running in wrong directory | Warn and suggest correct directory |

## Security Considerations

1. **Worktree isolation**: Each agent can only modify files in its worktree
2. **Identity validation**: Sessions cannot start without valid identity
3. **Path restrictions**: Existing PreToolUse hook enforces path boundaries
4. **No cross-worktree access**: Agents should not access other `.worktrees/` directories

## Rollout Plan

### Phase 1: Git Worktree Scripts
- Implement `setup-agent.sh`, `teardown-agent.sh`, `list-agents.sh`, `merge-agent.sh`
- Test worktree creation and cleanup

### Phase 2: Presence Management
- Extend coordination MCP with `coord_register_presence`, `coord_deregister_presence`
- Implement heartbeat mechanism with auto-refresh
- Add stale detection logic

### Phase 3: Startup Validation
- Create `.claude/hooks/startup.sh`
- Implement identity validation
- Implement presence registration on startup
- Implement pending notification display

### Phase 4: Coordination Enforcement
- Update `.claude/rules/pm-cli.md` with mandatory message checks
- Update `.claude/rules/orchestrator.md` with status update requirements
- Create `.claude/rules/coordination-protocol.md`

### Phase 5: Agent Session Launcher
- Create `start-agent-session.sh`
- Integrate all components into single workflow

### Phase 6: Integration Testing
- Test full multi-session workflow
- Test conflict detection and resolution
- Document usage patterns

## Success Criteria

1. **Isolation**: Multiple agents can work simultaneously without file conflicts
2. **Identity**: All sessions have validated, unique identity
3. **Visibility**: `coord_get_presence` shows all active sessions with accurate state
4. **Coordination**: PM CLI sees all pending messages at start of each turn
5. **Automation**: Single script (`start-agent-session.sh`) sets up complete environment
6. **Reliability**: Stale sessions detected and marked inactive automatically
7. **Merging**: Agent changes merge cleanly to main in most cases

## Risks

1. **Merge Conflicts**: Concurrent edits to same file require manual resolution
   - Mitigation: Path restrictions reduce overlap; PM CLI coordinates assignments

2. **Disk Space**: Each worktree is a full copy of project files
   - Mitigation: Git uses hardlinks where possible; cleanup script removes old worktrees

3. **Session Tracking Accuracy**: Network issues may cause false stale detection
   - Mitigation: 5-minute timeout is generous; sessions re-register on reconnect

4. **Claude CLI Hook Support**: Startup hooks may not be fully supported
   - Mitigation: Fall back to manual validation via rules if hooks unavailable

## Open Questions

1. Should worktree creation be automatic when agent is invoked, or require explicit setup?
2. Should merge strategy be configurable per agent (fast-forward only vs. merge commit)?
3. Should there be a cleanup cron job for abandoned worktrees?
4. Should PM CLI be in its own worktree, or always use main?

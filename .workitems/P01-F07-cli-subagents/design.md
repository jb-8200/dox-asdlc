# P01-F07: CLI Role Subagents with Redis Coordination

## Technical Design

### Overview

Create dedicated subagents (`backend.md`, `frontend.md`, `orchestrator.md`) that replace the interactive identity selection system. Each subagent has specific instructions, path restrictions, and Redis-based message coordination built into their system prompts.

### Key Benefits

- No more "set identity" - invoke the right subagent directly
- Built-in message polling and publishing in each subagent
- Rapid coherent communication via existing MCP tools
- Clear domain boundaries enforced at subagent level

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Main Claude Agent                          │
│  (decides which subagent to invoke based on user request)       │
└─────────────────────────────────────────────────────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  backend.md     │  │  frontend.md    │  │  orchestrator.md│
│                 │  │                 │  │                 │
│  - Workers      │  │  - HITL UI      │  │  - Meta files   │
│  - Infra        │  │  - Components   │  │  - Contracts    │
│  - P01-P03,P06  │  │  - P05          │  │  - Coordination │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                   ┌──────────▼──────────┐
                   │   Redis MCP Tools   │
                   │  (coordination)     │
                   └─────────────────────┘
```

### Interfaces

#### Coordination MCP Tools (Already Exist)

```
mcp__coordination__coord_publish_message(msg_type, subject, description, to_instance)
mcp__coordination__coord_check_messages(to_instance, pending_only, msg_type)
mcp__coordination__coord_ack_message(message_id)
mcp__coordination__coord_get_presence()
mcp__coordination__coord_get_notifications()
```

#### Subagent Output Contract

Each subagent returns structured JSON:

```json
{
  "status": "complete" | "blocked" | "in_progress",
  "subagent": "backend" | "frontend" | "orchestrator",
  "files_modified": ["path/to/file1.py", "path/to/file2.py"],
  "test_results": {
    "passed": 5,
    "failed": 0,
    "skipped": 0
  },
  "messages_sent": ["msg-123"],
  "messages_received": ["msg-456"],
  "blockers": [],
  "handoff": "Recommendation for next action"
}
```

### Coordination Protocol

#### On Subagent Start
1. `coord_check_messages(to_instance="{role}", pending_only=true)`
2. `coord_get_notifications()`
3. `coord_ack_message()` for relevant messages
4. `coord_publish_message(STATUS_UPDATE, "{role} started", "{task}")`

#### During Execution (every ~5 operations)
```
coord_check_messages(to_instance="{role}", msg_type="BLOCKING_ISSUE", pending_only=true)
```

#### On Blocking Issue
```
coord_publish_message(BLOCKING_ISSUE, "Blocked: {reason}", "{details}", to="orchestrator")
```

#### On Completion
```
coord_publish_message(STATUS_UPDATE, "{role} complete", "{summary}", to="orchestrator")
```

### Path Restrictions

| Subagent | Allowed Paths | Blocked Paths |
|----------|---------------|---------------|
| backend | src/workers/**, src/orchestrator/**, src/infrastructure/**, src/core/**, docker/workers/**, docker/orchestrator/**, tests/**, tools/**, .workitems/P01-*/**, P02-*/**, P03-*/**, P06-*/** | src/hitl_ui/, docker/hitl-ui/, .workitems/P05-*, CLAUDE.md, docs/, contracts/, .claude/rules/ |
| frontend | docker/hitl-ui/**, src/hitl_ui/**, tests/unit/hitl_ui/**, .workitems/P05-*/**, contracts/current/** (read-only) | src/workers/, src/orchestrator/, src/infrastructure/, CLAUDE.md, docs/, contracts/versions/, .claude/rules/, .workitems/P01-*, P02-*, P03-*, P06-* |
| orchestrator | ALL paths (no restrictions) | None (exclusive: CLAUDE.md, docs/**, contracts/**, .claude/rules/**, .claude/skills/**) |

### Dependencies

- P01-F04: CLI coordination with Redis backend (complete)
- P01-F05: A2A push notifications (complete)
- P01-F06: Trunk-based development workflow (complete)

### Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `.claude/agents/backend.md` | Create | Backend developer subagent |
| `.claude/agents/frontend.md` | Create | Frontend developer subagent |
| `.claude/agents/orchestrator.md` | Create | Coordinator subagent |
| `CLAUDE.md` | Modify | Add subagent selection guide |
| `scripts/hooks/session-start.py` | Modify | Simplify (remove identity prompt) |

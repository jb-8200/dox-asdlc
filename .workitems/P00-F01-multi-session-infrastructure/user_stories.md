# User Stories: P00-F01 Multi-Session Infrastructure

## Epic Reference

This feature enables multiple Claude CLI sessions to work in parallel on isolated git branches using git worktrees, with enforced unique identities and mandatory coordination.

## User Stories

### US-F01-01: Setup Agent Worktree

**As a** developer
**I want** to create an isolated worktree for an agent role
**So that** the agent can work without conflicting with other agents

**Acceptance Criteria:**
- [ ] `setup-agent.sh backend` creates `.worktrees/backend/` directory
- [ ] Creates branch `agent/backend/active` from current main
- [ ] Configures git identity (claude-backend@asdlc.local) in worktree
- [ ] Registers agent presence via Redis coordination
- [ ] Returns success/failure with informative messages
- [ ] Idempotent: re-running on existing worktree succeeds without changes

**Priority:** High

---

### US-F01-02: List Active Agent Worktrees

**As a** PM CLI user
**I want** to see which agent worktrees are active
**So that** I can coordinate work assignments appropriately

**Acceptance Criteria:**
- [ ] `list-agents.sh` outputs JSON array of worktree info
- [ ] Each entry includes: role, branch, path, status (active/stale)
- [ ] Status reflects actual git worktree state
- [ ] Status reflects Redis presence state
- [ ] Empty array returned if no worktrees exist

**Priority:** High

---

### US-F01-03: Teardown Agent Worktree

**As a** developer
**I want** to cleanly remove an agent worktree
**So that** resources are freed and changes are preserved

**Acceptance Criteria:**
- [ ] `teardown-agent.sh backend` removes `.worktrees/backend/`
- [ ] Prompts for merge strategy if uncommitted changes exist
- [ ] `--merge` flag merges branch to main before removal
- [ ] `--abandon` flag removes without merge
- [ ] Deregisters presence from Redis
- [ ] Removes branch if fully merged
- [ ] Reports success/failure clearly

**Priority:** High

---

### US-F01-04: Merge Agent Changes to Main

**As an** orchestrator
**I want** to merge agent changes back to main
**So that** parallel work is integrated into the codebase

**Acceptance Criteria:**
- [ ] `merge-agent.sh backend` merges agent/backend/active to main
- [ ] Uses fast-forward merge when possible
- [ ] Creates merge commit when fast-forward not possible
- [ ] Detects and reports merge conflicts
- [ ] Does not delete worktree (separate operation)
- [ ] Updates main branch head after successful merge

**Priority:** Medium

---

### US-F01-05: Validate Session Identity at Startup

**As a** Claude CLI session
**I want** my identity validated before I can work
**So that** all sessions are properly identified for coordination

**Acceptance Criteria:**
- [ ] Startup hook checks CLAUDE_INSTANCE_ID environment variable
- [ ] Falls back to git user.email if env var not set
- [ ] Validates identity is in allowed list (backend, frontend, orchestrator, devops, pm)
- [ ] Fails with clear error if identity cannot be determined
- [ ] Fails with clear error if identity is not recognized

**Priority:** High

---

### US-F01-06: Register Presence at Session Start

**As a** Claude CLI session
**I want** my presence registered when I start
**So that** other sessions know I am active

**Acceptance Criteria:**
- [ ] Startup hook publishes HEARTBEAT message via coordination MCP
- [ ] Registers with session metadata (role, worktree path, session ID)
- [ ] Presence visible via `coord_get_presence`
- [ ] Registration is atomic (all or nothing)

**Priority:** High

---

### US-F01-07: Check Pending Notifications at Startup

**As a** Claude CLI session
**I want** to see pending notifications when I start
**So that** I don't miss messages sent while I was offline

**Acceptance Criteria:**
- [ ] Startup hook calls `coord_get_notifications`
- [ ] Displays summary of pending messages
- [ ] Shows count and high-level types
- [ ] Does not block startup if no messages pending
- [ ] Notifications are popped (removed from queue after display)

**Priority:** Medium

---

### US-F01-08: Verify Worktree at Non-PM Session Start

**As a** non-PM agent session
**I want** verification that I'm in the correct worktree
**So that** I don't accidentally work in the wrong directory

**Acceptance Criteria:**
- [ ] Startup hook checks if current directory is a worktree
- [ ] Verifies worktree matches session identity
- [ ] Warns if running in main worktree as non-PM role
- [ ] Suggests correct directory if mismatch detected
- [ ] Does not block PM CLI from running in main worktree

**Priority:** Medium

---

### US-F01-09: PM CLI Checks Messages Every Turn

**As a** PM CLI user
**I want** the PM CLI to check for pending messages at each response
**So that** important coordination messages are not missed

**Acceptance Criteria:**
- [ ] PM CLI rule requires `coord_check_messages` at start of every response
- [ ] Filters for messages to PM (`to_instance=pm`) and pending only
- [ ] Displays message summary to user if any pending
- [ ] Asks user if should handle messages before other work
- [ ] Rule is documented in `.claude/rules/pm-cli.md`

**Priority:** High

---

### US-F01-10: PM CLI Checks Agent Presence Before Delegation

**As a** PM CLI user
**I want** visibility into which agents are active before delegating
**So that** I can make informed delegation decisions

**Acceptance Criteria:**
- [ ] PM CLI rule requires `coord_get_presence` before delegating
- [ ] Shows which agents are active/stale
- [ ] Shows last heartbeat time for context
- [ ] Warns if delegating to an agent that appears stale
- [ ] Rule is documented in `.claude/rules/pm-cli.md`

**Priority:** Medium

---

### US-F01-11: Orchestrator Publishes Status After Operations

**As an** orchestrator
**I want** to publish status updates after operations
**So that** PM CLI and other agents know operation results

**Acceptance Criteria:**
- [ ] Orchestrator rule requires STATUS_UPDATE after each operation
- [ ] Status includes: operation type, success/failure, summary
- [ ] Message sent to PM CLI (to_instance=pm)
- [ ] Rule is documented in `.claude/rules/orchestrator.md`

**Priority:** High

---

### US-F01-12: Orchestrator Acknowledges All Pending Messages

**As an** orchestrator
**I want** to acknowledge all pending messages before completing
**So that** senders know their messages were received

**Acceptance Criteria:**
- [ ] Orchestrator rule requires `coord_check_messages` before completing
- [ ] Must acknowledge all pending messages addressed to orchestrator
- [ ] Cannot complete with unacknowledged messages
- [ ] Rule is documented in `.claude/rules/orchestrator.md`

**Priority:** Medium

---

### US-F01-13: Heartbeat Auto-Refresh

**As a** running session
**I want** my presence heartbeat automatically refreshed
**So that** I'm not marked as stale while actively working

**Acceptance Criteria:**
- [ ] Heartbeat sent every 60 seconds while session active
- [ ] Redis key has 5-minute TTL
- [ ] Missed heartbeat for 5+ minutes marks session stale
- [ ] Heartbeat includes timestamp update only (not full re-registration)
- [ ] Heartbeat mechanism works transparently

**Priority:** Medium

---

### US-F01-14: Stale Session Detection

**As a** PM CLI user
**I want** stale sessions automatically detected
**So that** I know which agents are truly active

**Acceptance Criteria:**
- [ ] `coord_get_presence` marks sessions stale if no heartbeat for 5 minutes
- [ ] Stale status is clearly indicated in presence response
- [ ] Stale sessions still appear in listing (not removed)
- [ ] Stale session can become active again with new heartbeat

**Priority:** Medium

---

### US-F01-15: Agent Session Launcher Script

**As a** developer
**I want** a single script to set up an agent session
**So that** starting a new agent is simple and consistent

**Acceptance Criteria:**
- [ ] `start-agent-session.sh backend` performs complete setup
- [ ] Creates/verifies worktree
- [ ] Sets git identity
- [ ] Sets CLAUDE_INSTANCE_ID environment variable
- [ ] Changes to worktree directory
- [ ] Outputs instructions for next steps
- [ ] Idempotent: can be run multiple times safely

**Priority:** High

---

### US-F01-16: Coordination Protocol Documentation

**As a** developer
**I want** clear documentation of the coordination protocol
**So that** I understand message flow and heartbeat rules

**Acceptance Criteria:**
- [ ] `.claude/rules/coordination-protocol.md` exists
- [ ] Documents all message types used for multi-session
- [ ] Documents heartbeat frequency and TTL
- [ ] Documents presence tracking mechanism
- [ ] Documents stale detection rules
- [ ] Includes examples for common scenarios

**Priority:** Medium

---

## Non-Functional Requirements

### Performance

- Worktree creation completes in < 30 seconds
- Heartbeat operations complete in < 100ms
- Presence queries return in < 500ms
- Merge operations depend on changeset size (best effort)

### Reliability

- Worktree scripts handle interruption gracefully
- Stale detection has 5-minute buffer to avoid false positives
- Redis connection failures logged but don't crash sessions
- Idempotent operations prevent duplicate state

### Usability

- All scripts provide clear success/error messages
- Help text available via `--help` flag
- Error messages include remediation steps
- Coordination rules are clear and actionable

### Maintainability

- Scripts follow existing bash patterns in project
- Python extensions follow existing coordination patterns
- Rules are self-documenting
- Tests cover critical paths

## Dependencies

| Story | Depends On |
|-------|-----------|
| US-F01-01 | None (foundational) |
| US-F01-02 | US-F01-01 |
| US-F01-03 | US-F01-01 |
| US-F01-04 | US-F01-01 |
| US-F01-05 | None (foundational) |
| US-F01-06 | US-F01-05 |
| US-F01-07 | US-F01-05 |
| US-F01-08 | US-F01-01, US-F01-05 |
| US-F01-09 | Existing coordination MCP |
| US-F01-10 | Existing coordination MCP |
| US-F01-11 | Existing coordination MCP |
| US-F01-12 | Existing coordination MCP |
| US-F01-13 | US-F01-06 |
| US-F01-14 | US-F01-13 |
| US-F01-15 | US-F01-01 through US-F01-08 |
| US-F01-16 | All above (documentation) |

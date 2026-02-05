# P00-F01: Multi-Session Infrastructure - Tasks

## Overview

This task breakdown covers enabling multiple Claude CLI sessions to work in parallel on isolated git branches using git worktrees, with enforced unique identities and mandatory coordination.

## Dependencies

- **P01-F04**: CLI Coordination Migration to Redis - COMPLETE
- **P01-F07**: CLI Subagents - COMPLETE

## Phase 1: Git Worktree Scripts (T01-T04)

### T01: Create setup-agent.sh script

**Description**: Create script to set up an agent worktree with proper branch and configuration.

**Subtasks**:
- [ ] Create `scripts/worktree/` directory
- [ ] Implement `setup-agent.sh` with argument parsing
- [ ] Create worktree at `.worktrees/<role>/`
- [ ] Create branch `agent/<role>/active` from main
- [ ] Configure git identity in worktree (user.email, user.name)
- [ ] Handle idempotent case (worktree already exists)
- [ ] Add help text and usage information
- [ ] Add to `.gitignore`: `.worktrees/`

**Acceptance Criteria**:
- [ ] Script creates worktree with correct structure
- [ ] Branch naming follows convention
- [ ] Git identity properly configured
- [ ] Idempotent (safe to run twice)
- [ ] Clear error messages on failure

**Test Cases**:
- [ ] Test creation of new worktree
- [ ] Test idempotent behavior on existing worktree
- [ ] Test with invalid role argument
- [ ] Test with no argument (shows help)

**Estimate**: 1.5hr

---

### T02: Create list-agents.sh script

**Description**: Create script to list all agent worktrees and their status.

**Subtasks**:
- [ ] Implement `list-agents.sh`
- [ ] Query git worktree list for `.worktrees/` entries
- [ ] Parse worktree path, branch, and HEAD state
- [ ] Query Redis presence for each detected role
- [ ] Output JSON format with role, branch, path, status
- [ ] Handle case of no worktrees existing

**Acceptance Criteria**:
- [ ] Lists all agent worktrees
- [ ] JSON output is valid and parseable
- [ ] Status reflects both git and Redis state
- [ ] Empty array when no worktrees exist

**Test Cases**:
- [ ] Test with no worktrees
- [ ] Test with single worktree
- [ ] Test with multiple worktrees
- [ ] Test status accuracy (active vs stale)

**Estimate**: 1hr

---

### T03: Create teardown-agent.sh script

**Description**: Create script to cleanly remove an agent worktree.

**Subtasks**:
- [ ] Implement `teardown-agent.sh` with argument parsing
- [ ] Check for uncommitted changes in worktree
- [ ] Implement `--merge` flag to merge before removal
- [ ] Implement `--abandon` flag to remove without merge
- [ ] Prompt user if no flag and uncommitted changes
- [ ] Remove worktree via `git worktree remove`
- [ ] Delete branch if fully merged
- [ ] Deregister presence from Redis
- [ ] Add help text and usage information

**Acceptance Criteria**:
- [ ] Removes worktree completely
- [ ] Handles uncommitted changes appropriately
- [ ] Merge flag works correctly
- [ ] Abandon flag works correctly
- [ ] Redis presence cleaned up

**Test Cases**:
- [ ] Test teardown with clean worktree
- [ ] Test teardown with uncommitted changes (prompt)
- [ ] Test --merge flag
- [ ] Test --abandon flag
- [ ] Test teardown of non-existent worktree

**Estimate**: 1.5hr

---

### T04: Create merge-agent.sh script

**Description**: Create script to merge agent branch changes back to main.

**Subtasks**:
- [ ] Implement `merge-agent.sh` with argument parsing
- [ ] Verify agent branch exists
- [ ] Checkout main branch in main worktree
- [ ] Attempt fast-forward merge first
- [ ] Fall back to merge commit if needed
- [ ] Detect and report merge conflicts
- [ ] Return appropriate exit codes
- [ ] Add help text and usage information

**Acceptance Criteria**:
- [ ] Merges agent branch to main
- [ ] Prefers fast-forward when possible
- [ ] Reports conflicts clearly
- [ ] Does not auto-resolve conflicts
- [ ] Returns exit code 1 on conflict

**Test Cases**:
- [ ] Test fast-forward merge
- [ ] Test merge commit case
- [ ] Test conflict detection
- [ ] Test with non-existent branch

**Estimate**: 1hr

---

## Phase 2: Presence Management in Coordination MCP (T05-T08)

### T05: Add coord_register_presence MCP tool

**Description**: Add tool to register session presence with metadata.

**Subtasks**:
- [ ] Add `coord_register_presence` method to MCP server
- [ ] Accept role, worktree_path, session_id parameters
- [ ] Store metadata in Redis presence hash
- [ ] Include registration timestamp
- [ ] Add to tool schema definitions
- [ ] Write unit tests

**Acceptance Criteria**:
- [ ] Tool registers presence with all metadata
- [ ] Metadata stored in Redis correctly
- [ ] Tool response indicates success/failure
- [ ] Schema matches expected input format

**Test Cases**:
- [ ] Test registration with all fields
- [ ] Test registration with minimal fields
- [ ] Test re-registration (update existing)
- [ ] Test Redis unavailable handling

**Estimate**: 1hr

---

### T06: Add coord_deregister_presence MCP tool

**Description**: Add tool to mark session as inactive.

**Subtasks**:
- [ ] Add `coord_deregister_presence` method to MCP server
- [ ] Accept role parameter
- [ ] Update presence hash to mark inactive
- [ ] Preserve last_heartbeat for history
- [ ] Add to tool schema definitions
- [ ] Write unit tests

**Acceptance Criteria**:
- [ ] Tool marks session inactive
- [ ] Presence entry not deleted (kept for history)
- [ ] last_heartbeat preserved
- [ ] Tool response indicates success/failure

**Test Cases**:
- [ ] Test deregistration of active session
- [ ] Test deregistration of already inactive session
- [ ] Test deregistration of non-existent session

**Estimate**: 45min

---

### T07: Add coord_heartbeat MCP tool

**Description**: Add explicit heartbeat tool for sessions.

**Subtasks**:
- [ ] Add `coord_heartbeat` method to MCP server
- [ ] Accept role parameter
- [ ] Update last_heartbeat timestamp only
- [ ] Ensure TTL is refreshed (5 minutes)
- [ ] Add to tool schema definitions
- [ ] Write unit tests

**Acceptance Criteria**:
- [ ] Tool updates heartbeat timestamp
- [ ] Only timestamp field modified
- [ ] Redis key TTL extended
- [ ] Fast operation (< 100ms)

**Test Cases**:
- [ ] Test heartbeat for active session
- [ ] Test heartbeat for stale session (reactivates)
- [ ] Test heartbeat for non-existent session

**Estimate**: 45min

---

### T08: Implement stale detection in coord_get_presence

**Description**: Update presence query to detect and mark stale sessions.

**Subtasks**:
- [ ] Update `coord_get_presence` to calculate staleness
- [ ] Mark sessions stale if no heartbeat for 5 minutes
- [ ] Include stale flag in response
- [ ] Include time since last heartbeat
- [ ] Update existing unit tests
- [ ] Add new tests for stale detection

**Acceptance Criteria**:
- [ ] Sessions correctly marked stale after 5 minutes
- [ ] Response includes stale flag
- [ ] Active sessions not marked stale
- [ ] Edge cases handled (exactly 5 minutes)

**Test Cases**:
- [ ] Test active session (recent heartbeat)
- [ ] Test stale session (old heartbeat)
- [ ] Test boundary case (exactly 5 minutes)
- [ ] Test session with no heartbeat record

**Estimate**: 1hr

---

## Phase 3: Startup Hook and Identity Validation (T09-T12)

### T09: Create startup.sh hook script

**Description**: Create session startup validation hook.

**Subtasks**:
- [ ] Create `.claude/hooks/` directory
- [ ] Create `startup.sh` with validation logic
- [ ] Make script executable
- [ ] Document hook integration (if manual)

**Acceptance Criteria**:
- [ ] Hook script exists and is executable
- [ ] Exit code 0 allows session to proceed
- [ ] Exit code 1 blocks session with error
- [ ] Script is self-contained

**Test Cases**:
- [ ] Test hook exits 0 on valid setup
- [ ] Test hook exits 1 on invalid setup

**Estimate**: 30min

---

### T10: Implement identity validation in startup hook

**Description**: Validate session identity at startup.

**Subtasks**:
- [ ] Check CLAUDE_INSTANCE_ID environment variable
- [ ] Fall back to git user.email if env var not set
- [ ] Validate against allowed roles list
- [ ] Output clear error if identity invalid
- [ ] Output identity confirmation if valid

**Acceptance Criteria**:
- [ ] CLAUDE_INSTANCE_ID takes precedence
- [ ] Git email fallback works correctly
- [ ] Invalid identity blocks startup
- [ ] Clear error message with remediation

**Test Cases**:
- [ ] Test with CLAUDE_INSTANCE_ID set
- [ ] Test with git email only
- [ ] Test with neither set (error)
- [ ] Test with unrecognized identity (error)

**Estimate**: 45min

---

### T11: Implement presence registration in startup hook

**Description**: Register presence via coordination MCP at startup.

**Subtasks**:
- [ ] Call coord_publish_message with HEARTBEAT type
- [ ] Include session metadata in message
- [ ] Handle Redis unavailable gracefully
- [ ] Log registration success/failure

**Acceptance Criteria**:
- [ ] HEARTBEAT message published on startup
- [ ] Presence visible in coord_get_presence
- [ ] Redis unavailable logs warning but doesn't block
- [ ] Registration includes role and timestamp

**Test Cases**:
- [ ] Test registration success
- [ ] Test registration with Redis unavailable
- [ ] Test presence visible after registration

**Estimate**: 45min

---

### T12: Implement notification check in startup hook

**Description**: Check and display pending notifications at startup.

**Subtasks**:
- [ ] Call coord_get_notifications for current role
- [ ] Display summary if notifications pending
- [ ] Show count and message types
- [ ] Handle no pending notifications case
- [ ] Don't block startup on notification errors

**Acceptance Criteria**:
- [ ] Pending notifications displayed at startup
- [ ] Summary includes count and types
- [ ] Clean output if no pending notifications
- [ ] Errors logged but don't block startup

**Test Cases**:
- [ ] Test with pending notifications
- [ ] Test with no pending notifications
- [ ] Test with notification retrieval error

**Estimate**: 45min

---

## Phase 4: Coordination Enforcement Rules (T13-T16)

### T13: Update pm-cli.md with message check requirement

**Description**: Add mandatory message check rule to PM CLI.

**Subtasks**:
- [ ] Add "Message Check at Every Turn" section to pm-cli.md
- [ ] Document required coord_check_messages call
- [ ] Document handling of pending messages
- [ ] Add example interaction pattern
- [ ] Specify this is non-negotiable

**Acceptance Criteria**:
- [ ] Rule clearly documented in pm-cli.md
- [ ] Example shows expected behavior
- [ ] Rule marked as mandatory/non-negotiable
- [ ] Integrates with existing PM CLI responsibilities

**Test Cases**:
- [ ] Manual review of documentation clarity

**Estimate**: 30min

---

### T14: Update pm-cli.md with presence check requirement

**Description**: Add mandatory presence check rule before delegation.

**Subtasks**:
- [ ] Add "Presence Check Before Delegation" section
- [ ] Document required coord_get_presence call
- [ ] Document stale agent handling
- [ ] Add example interaction pattern

**Acceptance Criteria**:
- [ ] Rule clearly documented in pm-cli.md
- [ ] Example shows expected behavior
- [ ] Stale agent warning documented
- [ ] Integrates with existing delegation rules

**Test Cases**:
- [ ] Manual review of documentation clarity

**Estimate**: 30min

---

### T15: Update orchestrator.md with status update requirement

**Description**: Add mandatory status update rule to orchestrator.

**Subtasks**:
- [ ] Add "Status Update After Operations" section to orchestrator.md
- [ ] Document required STATUS_UPDATE publishing
- [ ] Define what counts as an "operation"
- [ ] Add example message format

**Acceptance Criteria**:
- [ ] Rule clearly documented in orchestrator.md
- [ ] STATUS_UPDATE format defined
- [ ] Examples show expected behavior
- [ ] Rule marked as mandatory

**Test Cases**:
- [ ] Manual review of documentation clarity

**Estimate**: 30min

---

### T16: Create coordination-protocol.md rules document

**Description**: Create comprehensive coordination protocol documentation.

**Subtasks**:
- [ ] Create `.claude/rules/coordination-protocol.md`
- [ ] Document message types for multi-session
- [ ] Document heartbeat protocol (frequency, TTL)
- [ ] Document presence tracking mechanism
- [ ] Document stale detection rules
- [ ] Include examples for common scenarios
- [ ] Add troubleshooting section

**Acceptance Criteria**:
- [ ] Document covers all coordination aspects
- [ ] Examples are clear and actionable
- [ ] Troubleshooting helps diagnose issues
- [ ] Integrates with existing rules

**Test Cases**:
- [ ] Manual review of documentation completeness

**Estimate**: 1hr

---

## Phase 5: Agent Session Launcher (T17-T20)

### T17: Create start-agent-session.sh script

**Description**: Create unified agent session launcher script.

**Subtasks**:
- [ ] Create `scripts/start-agent-session.sh`
- [ ] Parse role argument
- [ ] Call setup-agent.sh to create/verify worktree
- [ ] Set git identity in worktree
- [ ] Export CLAUDE_INSTANCE_ID
- [ ] Change to worktree directory
- [ ] Output next steps instructions
- [ ] Add help text

**Acceptance Criteria**:
- [ ] Single script performs complete setup
- [ ] Idempotent (safe to run multiple times)
- [ ] Clear instructions for next steps
- [ ] All identity variables properly set

**Test Cases**:
- [ ] Test complete setup flow
- [ ] Test with existing worktree
- [ ] Test with invalid role

**Estimate**: 1hr

---

### T18: Add worktree verification to startup hook

**Description**: Verify non-PM sessions are in correct worktree.

**Subtasks**:
- [ ] Check if current directory is a git worktree
- [ ] Verify worktree matches session identity
- [ ] Warn if PM role not in main worktree
- [ ] Warn if non-PM role in main worktree
- [ ] Suggest correct directory if mismatch

**Acceptance Criteria**:
- [ ] Worktree verification works correctly
- [ ] Warnings are helpful not blocking
- [ ] PM CLI can work in main worktree
- [ ] Non-PM roles warned if not in worktree

**Test Cases**:
- [ ] Test backend role in backend worktree (pass)
- [ ] Test backend role in main worktree (warn)
- [ ] Test PM role in main worktree (pass)
- [ ] Test PM role in agent worktree (warn)

**Estimate**: 45min

---

### T19: Add session deregistration to teardown

**Description**: Ensure session presence is deregistered on teardown.

**Subtasks**:
- [ ] Update teardown-agent.sh to call coord_deregister_presence
- [ ] Handle deregistration failure gracefully
- [ ] Log deregistration result
- [ ] Verify presence marked inactive after teardown

**Acceptance Criteria**:
- [ ] Presence deregistered on teardown
- [ ] Failure doesn't block teardown
- [ ] Presence shows inactive after teardown

**Test Cases**:
- [ ] Test deregistration on normal teardown
- [ ] Test deregistration with Redis unavailable

**Estimate**: 30min

---

### T20: Add SESSION_START and SESSION_END message types

**Description**: Add message types for session lifecycle events.

**Subtasks**:
- [ ] Add SESSION_START to MessageType enum
- [ ] Add SESSION_END to MessageType enum
- [ ] Publish SESSION_START in startup hook
- [ ] Publish SESSION_END in teardown script
- [ ] Update coordination-protocol.md with new types

**Acceptance Criteria**:
- [ ] New message types defined
- [ ] Session lifecycle messages published
- [ ] Documentation updated
- [ ] Existing tests still pass

**Test Cases**:
- [ ] Test SESSION_START published on startup
- [ ] Test SESSION_END published on teardown
- [ ] Test message type validation

**Estimate**: 1hr

---

## Phase 6: Integration Testing and Documentation (T21-T24)

### T21: Write integration tests for worktree scripts

**Description**: Create integration tests for worktree management.

**Subtasks**:
- [ ] Create `tests/integration/scripts/test_worktree_scripts.sh`
- [ ] Test full setup -> work -> teardown cycle
- [ ] Test merge workflow
- [ ] Test conflict detection
- [ ] Test idempotent operations

**Acceptance Criteria**:
- [ ] Tests cover happy path workflow
- [ ] Tests cover error cases
- [ ] Tests are reproducible
- [ ] Tests clean up after themselves

**Test Cases**:
- [ ] Test setup-agent.sh creates worktree
- [ ] Test list-agents.sh shows worktree
- [ ] Test merge-agent.sh merges changes
- [ ] Test teardown-agent.sh removes worktree

**Estimate**: 1.5hr

---

### T22: Write integration tests for presence management

**Description**: Create integration tests for presence tracking.

**Subtasks**:
- [ ] Create `tests/integration/infrastructure/test_presence_management.py`
- [ ] Test registration and heartbeat
- [ ] Test stale detection timing
- [ ] Test deregistration
- [ ] Test concurrent sessions

**Acceptance Criteria**:
- [ ] Tests verify presence tracking accuracy
- [ ] Tests verify stale detection timing
- [ ] Tests run against real Redis
- [ ] Tests clean up state

**Test Cases**:
- [ ] Test register_presence stores metadata
- [ ] Test heartbeat updates timestamp
- [ ] Test stale detection after 5 minutes
- [ ] Test deregister_presence marks inactive

**Estimate**: 1.5hr

---

### T23: Write integration tests for startup hook

**Description**: Create integration tests for startup validation.

**Subtasks**:
- [ ] Create `tests/integration/hooks/test_startup_hook.sh`
- [ ] Test identity validation scenarios
- [ ] Test presence registration
- [ ] Test notification check
- [ ] Test worktree verification

**Acceptance Criteria**:
- [ ] Tests cover all validation paths
- [ ] Tests verify exit codes
- [ ] Tests check output messages
- [ ] Tests are reproducible

**Test Cases**:
- [ ] Test with valid CLAUDE_INSTANCE_ID
- [ ] Test with valid git email
- [ ] Test with invalid identity (exit 1)
- [ ] Test notification display

**Estimate**: 1hr

---

### T24: Update project documentation

**Description**: Update main documentation with multi-session information.

**Subtasks**:
- [ ] Add multi-session section to CLAUDE.md
- [ ] Document worktree commands in CLAUDE.md
- [ ] Update parallel-coordination.md with worktree info
- [ ] Verify all new scripts listed in relevant docs
- [ ] Add troubleshooting section

**Acceptance Criteria**:
- [ ] CLAUDE.md documents multi-session workflow
- [ ] Commands table updated with new scripts
- [ ] Troubleshooting covers common issues
- [ ] Documentation is accurate and complete

**Test Cases**:
- [ ] Manual review of documentation completeness

**Estimate**: 1hr

---

## Progress

- **Started**: Not started
- **Tasks Complete**: 0/24
- **Percentage**: 0%
- **Status**: PLANNED
- **Blockers**: None

## Task Summary

| Task | Description | Phase | Estimate | Status |
|------|-------------|-------|----------|--------|
| T01 | Create setup-agent.sh script | 1 | 1.5 hr | [ ] |
| T02 | Create list-agents.sh script | 1 | 1 hr | [ ] |
| T03 | Create teardown-agent.sh script | 1 | 1.5 hr | [ ] |
| T04 | Create merge-agent.sh script | 1 | 1 hr | [ ] |
| T05 | Add coord_register_presence MCP tool | 2 | 1 hr | [ ] |
| T06 | Add coord_deregister_presence MCP tool | 2 | 45 min | [ ] |
| T07 | Add coord_heartbeat MCP tool | 2 | 45 min | [ ] |
| T08 | Implement stale detection | 2 | 1 hr | [ ] |
| T09 | Create startup.sh hook script | 3 | 30 min | [ ] |
| T10 | Implement identity validation | 3 | 45 min | [ ] |
| T11 | Implement presence registration | 3 | 45 min | [ ] |
| T12 | Implement notification check | 3 | 45 min | [ ] |
| T13 | Update pm-cli.md with message check | 4 | 30 min | [ ] |
| T14 | Update pm-cli.md with presence check | 4 | 30 min | [ ] |
| T15 | Update orchestrator.md with status update | 4 | 30 min | [ ] |
| T16 | Create coordination-protocol.md | 4 | 1 hr | [ ] |
| T17 | Create start-agent-session.sh | 5 | 1 hr | [ ] |
| T18 | Add worktree verification to startup | 5 | 45 min | [ ] |
| T19 | Add session deregistration to teardown | 5 | 30 min | [ ] |
| T20 | Add SESSION_START and SESSION_END types | 5 | 1 hr | [ ] |
| T21 | Integration tests for worktree scripts | 6 | 1.5 hr | [ ] |
| T22 | Integration tests for presence management | 6 | 1.5 hr | [ ] |
| T23 | Integration tests for startup hook | 6 | 1 hr | [ ] |
| T24 | Update project documentation | 6 | 1 hr | [ ] |

**Total Estimated Time**: ~22 hours

## Task Dependencies

```
Phase 1 (Worktree Scripts):
T01 ────┬──► T02
        ├──► T03
        └──► T04

Phase 2 (Presence MCP):
T05 ──► T06
    ──► T07 ──► T08

Phase 3 (Startup Hook):
T09 ──► T10 ──► T11 ──► T12

Phase 4 (Rules):
T13, T14, T15, T16 (parallel, no dependencies)

Phase 5 (Session Launcher):
T01-T12 ──► T17
T01, T09-T10 ──► T18
T03, T05-T06 ──► T19
T05, T16 ──► T20

Phase 6 (Testing):
T01-T04 ──► T21
T05-T08 ──► T22
T09-T12 ──► T23
All ──► T24
```

## Implementation Order

**Phase 1** (Foundation - Worktrees):
1. T01: setup-agent.sh (foundation for all worktree ops)
2. T02, T03, T04 can run in parallel after T01

**Phase 2** (Foundation - Presence):
1. T05: register_presence (needed for registration)
2. T06, T07 can run in parallel after T05
3. T08 after T07 (depends on heartbeat for stale detection)

**Phase 3** (Startup Hook):
1. T09: Create hook structure
2. T10, T11, T12 sequentially (build on previous)

**Phase 4** (Rules - Parallel):
- T13, T14, T15, T16 can all run in parallel

**Phase 5** (Integration):
1. T17: Agent session launcher (integrates phase 1-3)
2. T18, T19, T20 can run in parallel after T17

**Phase 6** (Testing & Docs):
1. T21, T22, T23 can run in parallel after their dependencies
2. T24 last (documentation wraps up)

## Completion Checklist

- [ ] All tasks in Task List are marked complete
- [ ] All worktree scripts work correctly
- [ ] All MCP tools implemented and tested
- [ ] Startup hook validates identity and registers presence
- [ ] PM CLI rules updated and enforced
- [ ] Orchestrator rules updated and enforced
- [ ] All integration tests pass
- [ ] Documentation complete and accurate
- [ ] Progress marked as 100% in tasks.md

## Notes

### Worktree Management

- Worktrees are created in `.worktrees/` directory (gitignored)
- Each worktree has its own branch: `agent/{role}/active`
- Worktrees share git objects with main repo (space efficient)
- Teardown should always deregister presence, even on errors

### Presence Tracking

- Heartbeat frequency: 60 seconds
- Stale threshold: 5 minutes
- Presence data includes: role, worktree_path, session_id, last_heartbeat
- Stale sessions remain visible (not auto-removed)

### Hook Integration

- Claude CLI may not support custom hooks directly
- Startup validation may need to be manual or rule-based
- Document both automatic and manual validation approaches

### Testing Strategy

- Unit tests mock Redis and git commands
- Integration tests use real Redis in Docker
- Worktree tests need isolated git repo (temp directory)
- Clean up all test artifacts after each test

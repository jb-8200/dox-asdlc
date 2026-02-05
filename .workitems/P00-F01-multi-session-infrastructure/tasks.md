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
- [x] Create `scripts/worktree/` directory
- [x] Implement `setup-agent.sh` with argument parsing
- [x] Create worktree at `.worktrees/<role>/`
- [x] Create branch `agent/<role>/active` from main
- [x] Configure git identity in worktree (user.email, user.name)
- [x] Handle idempotent case (worktree already exists)
- [x] Add help text and usage information
- [x] Add to `.gitignore`: `.worktrees/`

**Acceptance Criteria**:
- [x] Script creates worktree with correct structure
- [x] Branch naming follows convention
- [x] Git identity properly configured
- [x] Idempotent (safe to run twice)
- [x] Clear error messages on failure

**Test Cases**:
- [x] Test creation of new worktree
- [x] Test idempotent behavior on existing worktree
- [x] Test with invalid role argument
- [x] Test with no argument (shows help)

**Estimate**: 1.5hr

---

### T02: Create list-agents.sh script

**Description**: Create script to list all agent worktrees and their status.

**Subtasks**:
- [x] Implement `list-agents.sh`
- [x] Query git worktree list for `.worktrees/` entries
- [x] Parse worktree path, branch, and HEAD state
- [ ] Query Redis presence for each detected role (deferred to Phase 2)
- [x] Output JSON format with role, branch, path, status
- [x] Handle case of no worktrees existing

**Acceptance Criteria**:
- [x] Lists all agent worktrees
- [x] JSON output is valid and parseable
- [ ] Status reflects both git and Redis state (Redis deferred to Phase 2)
- [x] Empty array when no worktrees exist

**Test Cases**:
- [x] Test with no worktrees
- [x] Test with single worktree
- [x] Test with multiple worktrees
- [ ] Test status accuracy (active vs stale) (deferred to Phase 2)

**Estimate**: 1hr

---

### T03: Create teardown-agent.sh script

**Description**: Create script to cleanly remove an agent worktree.

**Subtasks**:
- [x] Implement `teardown-agent.sh` with argument parsing
- [x] Check for uncommitted changes in worktree
- [x] Implement `--merge` flag to merge before removal
- [x] Implement `--abandon` flag to remove without merge
- [x] Prompt user if no flag and uncommitted changes
- [x] Remove worktree via `git worktree remove`
- [x] Delete branch if fully merged
- [ ] Deregister presence from Redis (deferred to Phase 2)
- [x] Add help text and usage information

**Acceptance Criteria**:
- [x] Removes worktree completely
- [x] Handles uncommitted changes appropriately
- [x] Merge flag works correctly
- [x] Abandon flag works correctly
- [ ] Redis presence cleaned up (deferred to Phase 2)

**Test Cases**:
- [x] Test teardown with clean worktree
- [x] Test teardown with uncommitted changes (prompt)
- [x] Test --merge flag
- [x] Test --abandon flag
- [x] Test teardown of non-existent worktree

**Estimate**: 1.5hr

---

### T04: Create merge-agent.sh script

**Description**: Create script to merge agent branch changes back to main.

**Subtasks**:
- [x] Implement `merge-agent.sh` with argument parsing
- [x] Verify agent branch exists
- [x] Checkout main branch in main worktree
- [x] Attempt fast-forward merge first
- [x] Fall back to merge commit if needed
- [x] Detect and report merge conflicts
- [x] Return appropriate exit codes
- [x] Add help text and usage information

**Acceptance Criteria**:
- [x] Merges agent branch to main
- [x] Prefers fast-forward when possible
- [x] Reports conflicts clearly
- [x] Does not auto-resolve conflicts
- [x] Returns exit code 1 on conflict

**Test Cases**:
- [x] Test fast-forward merge
- [x] Test merge commit case
- [x] Test conflict detection
- [x] Test with non-existent branch

**Estimate**: 1hr

---

## Phase 2: Presence Management in Coordination MCP (T05-T08)

### T05: Add coord_register_presence MCP tool

**Description**: Add tool to register session presence with metadata.

**Subtasks**:
- [x] Add `coord_register_presence` method to MCP server
- [x] Accept role, worktree_path, session_id parameters
- [x] Store metadata in Redis presence hash
- [x] Include registration timestamp
- [x] Add to tool schema definitions
- [x] Write unit tests

**Acceptance Criteria**:
- [x] Tool registers presence with all metadata
- [x] Metadata stored in Redis correctly
- [x] Tool response indicates success/failure
- [x] Schema matches expected input format

**Test Cases**:
- [x] Test registration with all fields
- [x] Test registration with minimal fields
- [x] Test re-registration (update existing)
- [x] Test Redis unavailable handling

**Estimate**: 1hr

---

### T06: Add coord_deregister_presence MCP tool

**Description**: Add tool to mark session as inactive.

**Subtasks**:
- [x] Add `coord_deregister_presence` method to MCP server
- [x] Accept role parameter
- [x] Update presence hash to mark inactive
- [x] Preserve last_heartbeat for history
- [x] Add to tool schema definitions
- [x] Write unit tests

**Acceptance Criteria**:
- [x] Tool marks session inactive
- [x] Presence entry not deleted (kept for history)
- [x] last_heartbeat preserved
- [x] Tool response indicates success/failure

**Test Cases**:
- [x] Test deregistration of active session
- [x] Test deregistration of already inactive session
- [x] Test deregistration of non-existent session

**Estimate**: 45min

---

### T07: Add coord_heartbeat MCP tool

**Description**: Add explicit heartbeat tool for sessions.

**Subtasks**:
- [x] Add `coord_heartbeat` method to MCP server
- [x] Accept role parameter
- [x] Update last_heartbeat timestamp only
- [x] Ensure TTL is refreshed (5 minutes)
- [x] Add to tool schema definitions
- [x] Write unit tests

**Acceptance Criteria**:
- [x] Tool updates heartbeat timestamp
- [x] Only timestamp field modified
- [x] Redis key TTL extended
- [x] Fast operation (< 100ms)

**Test Cases**:
- [x] Test heartbeat for active session
- [x] Test heartbeat for stale session (reactivates)
- [x] Test heartbeat for non-existent session

**Estimate**: 45min

---

### T08: Implement stale detection in coord_get_presence

**Description**: Update presence query to detect and mark stale sessions.

**Subtasks**:
- [x] Update `coord_get_presence` to calculate staleness
- [x] Mark sessions stale if no heartbeat for 5 minutes
- [x] Include stale flag in response
- [x] Include time since last heartbeat
- [x] Update existing unit tests
- [x] Add new tests for stale detection

**Acceptance Criteria**:
- [x] Sessions correctly marked stale after 5 minutes
- [x] Response includes stale flag
- [x] Active sessions not marked stale
- [x] Edge cases handled (exactly 5 minutes)

**Test Cases**:
- [x] Test active session (recent heartbeat)
- [x] Test stale session (old heartbeat)
- [x] Test boundary case (exactly 5 minutes)
- [x] Test session with no heartbeat record

**Estimate**: 1hr

---

## Phase 3: Startup Hook and Identity Validation (T09-T12)

### T09: Create startup.sh hook script

**Description**: Create session startup validation hook.

**Subtasks**:
- [x] Create `.claude/hooks/` directory
- [x] Create `startup.sh` with validation logic
- [x] Make script executable
- [x] Document hook integration (if manual)

**Acceptance Criteria**:
- [x] Hook script exists and is executable
- [x] Exit code 0 allows session to proceed
- [x] Exit code 1 blocks session with error
- [x] Script is self-contained

**Test Cases**:
- [x] Test hook exits 0 on valid setup
- [x] Test hook exits 1 on invalid setup

**Estimate**: 30min

---

### T10: Implement identity validation in startup hook

**Description**: Validate session identity at startup.

**Subtasks**:
- [x] Check CLAUDE_INSTANCE_ID environment variable
- [x] Fall back to git user.email if env var not set
- [x] Validate against allowed roles list
- [x] Output clear error if identity invalid
- [x] Output identity confirmation if valid

**Acceptance Criteria**:
- [x] CLAUDE_INSTANCE_ID takes precedence
- [x] Git email fallback works correctly
- [x] Invalid identity blocks startup
- [x] Clear error message with remediation

**Test Cases**:
- [x] Test with CLAUDE_INSTANCE_ID set
- [x] Test with git email only
- [x] Test with neither set (error)
- [x] Test with unrecognized identity (error)

**Estimate**: 45min

---

### T11: Implement presence registration in startup hook

**Description**: Register presence via coordination MCP at startup.

**Subtasks**:
- [x] Register presence via direct Redis commands (HSET to presence hash)
- [x] Include session metadata (session_id, timestamp)
- [x] Handle Redis unavailable gracefully
- [x] Log registration success/failure

**Acceptance Criteria**:
- [x] Presence updated on startup via Redis HSET
- [x] Presence visible in coord_get_presence
- [x] Redis unavailable logs warning but doesn't block
- [x] Registration includes role and timestamp

**Test Cases**:
- [x] Test registration success
- [x] Test registration with Redis unavailable
- [x] Test presence visible after registration

**Estimate**: 45min

---

### T12: Implement notification check in startup hook

**Description**: Check and display pending notifications at startup.

**Subtasks**:
- [x] Check inbox for current role via Redis SCARD
- [x] Display summary if notifications pending
- [x] Show count of pending messages
- [x] Handle no pending notifications case
- [x] Don't block startup on notification errors

**Acceptance Criteria**:
- [x] Pending notifications displayed at startup
- [x] Summary includes count
- [x] Clean output if no pending notifications
- [x] Errors logged but don't block startup

**Test Cases**:
- [x] Test with pending notifications
- [x] Test with no pending notifications
- [x] Test with notification retrieval error

**Estimate**: 45min

---

## Phase 4: Coordination Enforcement Rules (T13-T16)

### T13: Update pm-cli.md with message check requirement

**Description**: Add mandatory message check rule to PM CLI.

**Subtasks**:
- [x] Add "Message Check at Every Turn" section to pm-cli.md
- [x] Document required coord_check_messages call
- [x] Document handling of pending messages
- [x] Add example interaction pattern
- [x] Specify this is non-negotiable

**Acceptance Criteria**:
- [x] Rule clearly documented in pm-cli.md
- [x] Example shows expected behavior
- [x] Rule marked as mandatory/non-negotiable
- [x] Integrates with existing PM CLI responsibilities

**Test Cases**:
- [x] Manual review of documentation clarity

**Estimate**: 30min

---

### T14: Update pm-cli.md with presence check requirement

**Description**: Add mandatory presence check rule before delegation.

**Subtasks**:
- [x] Add "Presence Check Before Delegation" section
- [x] Document required coord_get_presence call
- [x] Document stale agent handling
- [x] Add example interaction pattern

**Acceptance Criteria**:
- [x] Rule clearly documented in pm-cli.md
- [x] Example shows expected behavior
- [x] Stale agent warning documented
- [x] Integrates with existing delegation rules

**Test Cases**:
- [x] Manual review of documentation clarity

**Estimate**: 30min

---

### T15: Update orchestrator.md with status update requirement

**Description**: Add mandatory status update rule to orchestrator.

**Subtasks**:
- [x] Add "Status Update After Operations" section to orchestrator.md
- [x] Document required STATUS_UPDATE publishing
- [x] Define what counts as an "operation"
- [x] Add example message format

**Acceptance Criteria**:
- [x] Rule clearly documented in orchestrator.md
- [x] STATUS_UPDATE format defined
- [x] Examples show expected behavior
- [x] Rule marked as mandatory

**Test Cases**:
- [x] Manual review of documentation clarity

**Estimate**: 30min

---

### T16: Create coordination-protocol.md rules document

**Description**: Create comprehensive coordination protocol documentation.

**Subtasks**:
- [x] Create `.claude/rules/coordination-protocol.md`
- [x] Document message types for multi-session
- [x] Document heartbeat protocol (frequency, TTL)
- [x] Document presence tracking mechanism
- [x] Document stale detection rules
- [x] Include examples for common scenarios
- [x] Add troubleshooting section

**Acceptance Criteria**:
- [x] Document covers all coordination aspects
- [x] Examples are clear and actionable
- [x] Troubleshooting helps diagnose issues
- [x] Integrates with existing rules

**Test Cases**:
- [ ] Manual review of documentation completeness

**Estimate**: 1hr

---

## Phase 5: Agent Session Launcher (T17-T20)

### T17: Create start-agent-session.sh script

**Description**: Create unified agent session launcher script.

**Subtasks**:
- [x] Create `scripts/start-agent-session.sh`
- [x] Parse role argument
- [x] Call setup-agent.sh to create/verify worktree
- [x] Set git identity in worktree
- [x] Export CLAUDE_INSTANCE_ID
- [x] Change to worktree directory
- [x] Output next steps instructions
- [x] Add help text

**Acceptance Criteria**:
- [x] Single script performs complete setup
- [x] Idempotent (safe to run multiple times)
- [x] Clear instructions for next steps
- [x] All identity variables properly set

**Test Cases**:
- [x] Test complete setup flow
- [x] Test with existing worktree
- [x] Test with invalid role

**Estimate**: 1hr

---

### T18: Add worktree verification to startup hook

**Description**: Verify non-PM sessions are in correct worktree.

**Subtasks**:
- [x] Check if current directory is a git worktree
- [x] Verify worktree matches session identity
- [x] Warn if PM role not in main worktree
- [x] Warn if non-PM role in main worktree
- [x] Suggest correct directory if mismatch

**Acceptance Criteria**:
- [x] Worktree verification works correctly
- [x] Warnings are helpful not blocking
- [x] PM CLI can work in main worktree
- [x] Non-PM roles warned if not in worktree

**Test Cases**:
- [x] Test backend role in backend worktree (pass)
- [x] Test backend role in main worktree (warn)
- [x] Test PM role in main worktree (pass)
- [x] Test PM role in agent worktree (warn)

**Estimate**: 45min

---

### T19: Add session deregistration to teardown

**Description**: Ensure session presence is deregistered on teardown.

**Subtasks**:
- [x] Update teardown-agent.sh to call coord_deregister_presence
- [x] Handle deregistration failure gracefully
- [x] Log deregistration result
- [x] Verify presence marked inactive after teardown

**Acceptance Criteria**:
- [x] Presence deregistered on teardown
- [x] Failure doesn't block teardown
- [x] Presence shows inactive after teardown

**Test Cases**:
- [x] Test deregistration on normal teardown
- [x] Test deregistration with Redis unavailable

**Estimate**: 30min

---

### T20: Add SESSION_START and SESSION_END message types

**Description**: Add message types for session lifecycle events.

**Subtasks**:
- [x] Add SESSION_START to MessageType enum
- [x] Add SESSION_END to MessageType enum
- [x] Publish SESSION_START in startup hook
- [x] Publish SESSION_END in teardown script
- [x] Update coordination-protocol.md with new types

**Acceptance Criteria**:
- [x] New message types defined
- [x] Session lifecycle messages published
- [x] Documentation updated
- [x] Existing tests still pass

**Test Cases**:
- [x] Test SESSION_START published on startup
- [x] Test SESSION_END published on teardown
- [x] Test message type validation

**Estimate**: 1hr

---

## Phase 6: Integration Testing and Documentation (T21-T24)

### T21: Write integration tests for worktree scripts

**Description**: Create integration tests for worktree management.

**Subtasks**:
- [x] Create `tests/integration/scripts/test_worktree_scripts.sh`
- [x] Test full setup -> work -> teardown cycle
- [x] Test merge workflow
- [x] Test conflict detection
- [x] Test idempotent operations

**Acceptance Criteria**:
- [x] Tests cover happy path workflow
- [x] Tests cover error cases
- [x] Tests are reproducible
- [x] Tests clean up after themselves

**Test Cases**:
- [x] Test setup-agent.sh creates worktree
- [x] Test list-agents.sh shows worktree
- [x] Test merge-agent.sh merges changes
- [x] Test teardown-agent.sh removes worktree

**Estimate**: 1.5hr

---

### T22: Write integration tests for presence management

**Description**: Create integration tests for presence tracking.

**Subtasks**:
- [x] Create `tests/integration/infrastructure/test_presence_management.py`
- [x] Test registration and heartbeat
- [x] Test stale detection timing
- [x] Test deregistration
- [x] Test concurrent sessions

**Acceptance Criteria**:
- [x] Tests verify presence tracking accuracy
- [x] Tests verify stale detection timing
- [x] Tests run against real Redis
- [x] Tests clean up state

**Test Cases**:
- [x] Test register_presence stores metadata
- [x] Test heartbeat updates timestamp
- [x] Test stale detection after 5 minutes
- [x] Test deregister_presence marks inactive

**Estimate**: 1.5hr

---

### T23: Write integration tests for startup hook

**Description**: Create integration tests for startup validation.

**Subtasks**:
- [x] Create `tests/integration/hooks/test_startup_hook.sh`
- [x] Test identity validation scenarios
- [x] Test presence registration
- [x] Test notification check
- [x] Test worktree verification

**Acceptance Criteria**:
- [x] Tests cover all validation paths
- [x] Tests verify exit codes
- [x] Tests check output messages
- [x] Tests are reproducible

**Test Cases**:
- [x] Test with valid CLAUDE_INSTANCE_ID
- [x] Test with valid git email
- [x] Test with invalid identity (exit 1)
- [x] Test notification display

**Estimate**: 1hr

---

### T24: Update project documentation

**Description**: Update main documentation with multi-session information.

**Subtasks**:
- [x] Add multi-session section to CLAUDE.md
- [x] Document worktree commands in CLAUDE.md
- [x] Update parallel-coordination.md with worktree info (note: parallel-coordination.md is a meta file - worktree info added to CLAUDE.md instead)
- [x] Verify all new scripts listed in relevant docs
- [x] Add troubleshooting section

**Acceptance Criteria**:
- [x] CLAUDE.md documents multi-session workflow
- [x] Commands table updated with new scripts
- [x] Troubleshooting covers common issues
- [x] Documentation is accurate and complete

**Test Cases**:
- [x] Manual review of documentation completeness

**Estimate**: 1hr

---

## Progress

- **Started**: 2026-02-05
- **Tasks Complete**: 24/24
- **Percentage**: 100%
- **Status**: COMPLETE
- **Blockers**: None

## Task Summary

| Task | Description | Phase | Estimate | Status |
|------|-------------|-------|----------|--------|
| T01 | Create setup-agent.sh script | 1 | 1.5 hr | [x] |
| T02 | Create list-agents.sh script | 1 | 1 hr | [x] |
| T03 | Create teardown-agent.sh script | 1 | 1.5 hr | [x] |
| T04 | Create merge-agent.sh script | 1 | 1 hr | [x] |
| T05 | Add coord_register_presence MCP tool | 2 | 1 hr | [x] |
| T06 | Add coord_deregister_presence MCP tool | 2 | 45 min | [x] |
| T07 | Add coord_heartbeat MCP tool | 2 | 45 min | [x] |
| T08 | Implement stale detection | 2 | 1 hr | [x] |
| T09 | Create startup.sh hook script | 3 | 30 min | [x] |
| T10 | Implement identity validation | 3 | 45 min | [x] |
| T11 | Implement presence registration | 3 | 45 min | [x] |
| T12 | Implement notification check | 3 | 45 min | [x] |
| T13 | Update pm-cli.md with message check | 4 | 30 min | [x] |
| T14 | Update pm-cli.md with presence check | 4 | 30 min | [x] |
| T15 | Update orchestrator.md with status update | 4 | 30 min | [x] |
| T16 | Create coordination-protocol.md | 4 | 1 hr | [x] |
| T17 | Create start-agent-session.sh | 5 | 1 hr | [x] |
| T18 | Add worktree verification to startup | 5 | 45 min | [x] |
| T19 | Add session deregistration to teardown | 5 | 30 min | [x] |
| T20 | Add SESSION_START and SESSION_END types | 5 | 1 hr | [x] |
| T21 | Integration tests for worktree scripts | 6 | 1.5 hr | [x] |
| T22 | Integration tests for presence management | 6 | 1.5 hr | [x] |
| T23 | Integration tests for startup hook | 6 | 1 hr | [x] |
| T24 | Update project documentation | 6 | 1 hr | [x] |

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

- [x] All tasks in Task List are marked complete
- [x] All worktree scripts work correctly
- [x] All MCP tools implemented and tested
- [x] Startup hook validates identity and registers presence
- [x] PM CLI rules updated and enforced
- [x] Orchestrator rules updated and enforced
- [x] All integration tests pass
- [x] Documentation complete and accurate
- [x] Progress marked as 100% in tasks.md

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

# P01-F07: CLI Role Subagents - User Stories

## Epic

As a developer using the aSDLC system, I want to invoke role-specific subagents directly so that I don't need to manually set my identity and can leverage built-in coordination.

---

## User Stories

### US01: Backend Developer Workflow

**As a** backend developer
**I want to** invoke the backend subagent for workers/infrastructure tasks
**So that** I can work on backend code with proper path restrictions and coordination

**Acceptance Criteria:**
- [ ] Backend subagent automatically checks for pending messages on start
- [ ] Backend subagent can only modify allowed paths (src/workers/, src/orchestrator/, etc.)
- [ ] Backend subagent publishes STATUS_UPDATE on completion
- [ ] Backend subagent blocks if trying to modify frontend paths
- [ ] Output includes structured JSON with status, files modified, and test results

---

### US02: Frontend Developer Workflow

**As a** frontend developer
**I want to** invoke the frontend subagent for HITL UI tasks
**So that** I can work on frontend code with proper path restrictions and mock-first development

**Acceptance Criteria:**
- [ ] Frontend subagent automatically checks for pending messages on start
- [ ] Frontend subagent can only modify allowed paths (docker/hitl-ui/, src/hitl_ui/, etc.)
- [ ] Frontend subagent can read contracts for mock development
- [ ] Frontend subagent publishes STATUS_UPDATE on completion
- [ ] Frontend subagent blocks if trying to modify backend paths

---

### US03: Orchestrator Coordination Workflow

**As a** project coordinator
**I want to** invoke the orchestrator subagent for meta file changes and coordination
**So that** I can manage contracts, documentation, and resolve blocking issues

**Acceptance Criteria:**
- [ ] Orchestrator subagent processes pending messages with priority order
- [ ] Orchestrator subagent can modify all paths including meta files
- [ ] Orchestrator subagent handles CONTRACT_CHANGE_PROPOSED mediation
- [ ] Orchestrator subagent handles META_CHANGE_REQUEST processing
- [ ] Orchestrator subagent handles BLOCKING_ISSUE escalations
- [ ] Output includes actions taken, messages processed, and pending items

---

### US04: Cross-Subagent Communication

**As a** developer using multiple subagents
**I want** subagents to communicate via Redis coordination messages
**So that** I can have coherent workflows across domain boundaries

**Acceptance Criteria:**
- [ ] Backend subagent can publish BLOCKING_ISSUE to orchestrator
- [ ] Orchestrator receives and processes BLOCKING_ISSUE messages
- [ ] Resolution messages are sent back to originating subagent
- [ ] Message acknowledgment prevents duplicate processing

---

### US05: Simplified Session Start

**As a** developer
**I want** session start to be simplified without identity selection prompts
**So that** I can start working immediately by invoking the appropriate subagent

**Acceptance Criteria:**
- [ ] Session start no longer prompts for identity selection
- [ ] Session start displays basic environment information
- [ ] Subagent selection is done by invoking the appropriate subagent directly
- [ ] CLAUDE.md includes subagent selection guide for reference

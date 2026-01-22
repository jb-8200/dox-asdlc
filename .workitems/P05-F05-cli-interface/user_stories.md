# P05-F05: User Stories

## US-01: Authenticate with aSDLC Server

**As a** developer using the CLI
**I want to** authenticate with my aSDLC server
**So that** I can access protected resources

### Acceptance Criteria
- [ ] `asdlc auth login` prompts for server URL (if not configured)
- [ ] Interactive login opens browser for OAuth flow
- [ ] `asdlc auth login --token=TOKEN` accepts API token directly
- [ ] Token is stored securely in `~/.asdlc/credentials`
- [ ] Credentials file has restricted permissions (600)
- [ ] `asdlc auth status` shows current authentication state
- [ ] `asdlc auth logout` clears stored credentials
- [ ] Expired tokens trigger re-authentication prompt

### Test Scenarios
- Given no credentials, when `auth login` runs, then browser opens for OAuth
- Given valid token, when `auth status` runs, then shows authenticated user
- Given expired token, when any command runs, then prompts for re-auth

---

## US-02: Manage Context (Repo/Environment)

**As a** developer working on multiple projects
**I want to** set my current repository and environment context
**So that** I don't have to specify them on every command

### Acceptance Criteria
- [ ] `asdlc context set --repo=X --env=Y` stores context
- [ ] Context persists across CLI sessions
- [ ] `asdlc context show` displays current context
- [ ] `asdlc context list` shows available repos and environments
- [ ] Commands can override context with `--repo` and `--env` flags
- [ ] Missing context prompts user to set it

### Test Scenarios
- Given no context, when command runs, then prompts to set context
- Given context set, when `epic list` runs, then uses stored context
- Given context set, when `epic list --env=staging` runs, then uses override

---

## US-03: Create and Monitor Epics

**As a** developer
**I want to** create epics and check their status from the terminal
**So that** I can manage work without leaving my workflow

### Acceptance Criteria
- [ ] `asdlc epic create "Title"` creates epic and returns ID
- [ ] `asdlc epic status EPIC-XXX` shows state, progress, gates, budget
- [ ] `asdlc epic list` shows all epics with filters
- [ ] `asdlc epic list --state=active` filters by state
- [ ] `asdlc epic list --mine` filters to user's epics
- [ ] Output supports `--output=json` for scripting

### Test Scenarios
- Given valid auth, when `epic create "Test"` runs, then returns new EPIC-ID
- Given existing epic, when `epic status EPIC-001` runs, then shows details
- Given multiple epics, when `epic list --state=active` runs, then shows filtered list

---

## US-04: Trigger Workflow Phases

**As a** developer
**I want to** trigger workflow phases from the CLI
**So that** I can advance epics without using the SPA

### Acceptance Criteria
- [ ] `asdlc run discovery EPIC-XXX` starts discovery phase
- [ ] `asdlc run design EPIC-XXX` starts design phase
- [ ] `asdlc run develop EPIC-XXX` starts development phase
- [ ] `asdlc run validate EPIC-XXX` starts validation phase
- [ ] `asdlc run deploy EPIC-XXX` starts deployment (with confirmation)
- [ ] Commands show run ID and initial status
- [ ] `--wait` flag blocks until phase completes
- [ ] `--open` flag opens SPA to monitor run

### Test Scenarios
- Given epic in discovery, when `run design EPIC-001` runs, then starts design phase
- Given `--wait` flag, when run completes, then command exits
- Given `--open` flag, when command runs, then opens browser

---

## US-05: Manage HITL Gates

**As a** developer
**I want to** view and approve gates from the CLI
**So that** I can quickly unblock workflows

### Acceptance Criteria
- [ ] `asdlc gates list` shows pending gates
- [ ] `asdlc gates list --type=HITL-1` filters by type
- [ ] `asdlc gates show GATE-XXX` shows gate details and evidence summary
- [ ] `asdlc gates approve GATE-XXX` approves gate (simple cases)
- [ ] `asdlc gates approve GATE-XXX --comment="LGTM"` adds comment
- [ ] `asdlc gates reject GATE-XXX --reason="..."` rejects with reason
- [ ] `asdlc gates check --epic=EPIC-XXX --required=HITL-3` checks gate status (for CI)
- [ ] `asdlc gates approve GATE-XXX --open` opens SPA for complex review

### Test Scenarios
- Given pending gates, when `gates list` runs, then shows gate queue
- Given simple gate, when `gates approve GATE-001` runs, then gate is approved
- Given complex gate, when `gates approve --open` runs, then opens SPA

---

## US-06: Monitor Runs and View Logs

**As a** developer
**I want to** monitor run status and stream logs
**So that** I can troubleshoot issues quickly

### Acceptance Criteria
- [ ] `asdlc runs list` shows active runs
- [ ] `asdlc runs list --epic=EPIC-XXX` filters by epic
- [ ] `asdlc runs show RUN-XXX` shows run details
- [ ] `asdlc runs logs RUN-XXX` outputs logs
- [ ] `asdlc runs logs RUN-XXX --follow` streams logs in real-time
- [ ] `asdlc runs cancel RUN-XXX` cancels a running task
- [ ] `asdlc runs rerun RUN-XXX` reruns with same inputs

### Test Scenarios
- Given active run, when `runs logs RUN-001 --follow` runs, then streams live
- Given failed run, when `runs rerun RUN-001` runs, then new run starts
- Given running task, when `runs cancel RUN-001` runs, then task is cancelled

---

## US-07: View and Export Artifacts

**As a** developer
**I want to** view artifacts and their history from the CLI
**So that** I can inspect specs without switching tools

### Acceptance Criteria
- [ ] `asdlc artifacts list EPIC-XXX` lists all artifacts
- [ ] `asdlc artifacts show EPIC-XXX/PRD.md` displays content
- [ ] `asdlc artifacts diff EPIC-XXX/PRD.md` shows changes from last version
- [ ] `asdlc artifacts history EPIC-XXX/PRD.md` shows version history
- [ ] `asdlc artifacts export EPIC-XXX -o bundle.zip` exports all artifacts
- [ ] Markdown rendering in terminal (optional, `--raw` for plain)

### Test Scenarios
- Given artifact exists, when `artifacts show` runs, then content displayed
- Given multiple versions, when `artifacts diff` runs, then diff shown
- Given epic with artifacts, when `artifacts export` runs, then ZIP created

---

## US-08: Check Budget and Alerts

**As a** developer
**I want to** check budget status and alerts
**So that** I can monitor spend

### Acceptance Criteria
- [ ] `asdlc budget status` shows overall spend
- [ ] `asdlc budget status EPIC-XXX` shows per-epic spend
- [ ] `asdlc budget alert` shows active budget alerts
- [ ] Output includes burn rate, limits, and projections

### Test Scenarios
- Given active epic, when `budget status EPIC-001` runs, then shows spend/limit
- Given budget alert, when `budget alert` runs, then alert is displayed

---

## US-09: Quick Actions and Deep Links

**As a** developer
**I want to** quickly open resources in the SPA
**So that** I can switch to rich UI when needed

### Acceptance Criteria
- [ ] `asdlc open EPIC-XXX` opens epic in browser
- [ ] `asdlc open GATE-XXX` opens gate in browser
- [ ] `asdlc open RUN-XXX` opens run in browser
- [ ] `asdlc watch EPIC-XXX` streams live activity feed
- [ ] `asdlc status` shows system health summary

### Test Scenarios
- Given valid epic ID, when `open EPIC-001` runs, then browser opens to epic page
- Given active epic, when `watch EPIC-001` runs, then events stream to terminal

---

## US-10: Interactive TUI Mode

**As a** developer
**I want to** use an interactive terminal UI
**So that** I can navigate aSDLC without memorizing commands

### Acceptance Criteria
- [ ] `asdlc tui` launches interactive terminal UI
- [ ] TUI shows epic status, pending gates, active runs
- [ ] Keyboard navigation (arrows, enter, escape)
- [ ] Hotkeys for common actions (g=gates, r=runs, a=artifacts)
- [ ] Can approve/reject simple gates from TUI
- [ ] Deep link to SPA for complex operations

### Test Scenarios
- Given `asdlc tui` runs, then interactive UI displays
- Given pending gate in TUI, when 'a' pressed, then gate is approved
- Given TUI open, when 'q' pressed, then TUI exits

---

## US-11: CI/CD Integration

**As a** CI/CD pipeline
**I want to** validate epic state and gate approvals
**So that** I can gate deployments on aSDLC workflow completion

### Acceptance Criteria
- [ ] `asdlc auth login --token=TOKEN` works non-interactively
- [ ] `asdlc gates check --epic=EPIC-XXX --required=HITL-3` returns exit code
- [ ] Exit code 0 if gate approved, non-zero otherwise
- [ ] `--quiet` flag suppresses output (exit code only)
- [ ] `--output=json` works for all commands
- [ ] Commands work in headless environments (no TTY)

### Test Scenarios
- Given approved HITL-3, when `gates check --required=HITL-3` runs, then exit 0
- Given pending HITL-3, when `gates check --required=HITL-3` runs, then exit 5
- Given `--quiet` flag, when command runs, then no output printed

---

## US-12: Output Formatting

**As a** developer or script
**I want to** control output format
**So that** I can parse results programmatically

### Acceptance Criteria
- [ ] Default output is human-readable (Rich tables, colors)
- [ ] `--output=json` outputs valid JSON
- [ ] `--output=yaml` outputs valid YAML
- [ ] `--no-color` disables color output
- [ ] Color auto-detects TTY (disabled in pipes)
- [ ] All list commands support consistent output formats

### Test Scenarios
- Given `--output=json`, when command runs, then valid JSON output
- Given command piped, when runs, then colors disabled automatically
- Given `--no-color`, when command runs, then no ANSI codes in output

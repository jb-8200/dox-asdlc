# P05-F05: Tasks

## Progress
- **Status**: NOT_STARTED
- **Completed**: 0/18
- **Progress**: 0%

---

## Task List

### T01: Project scaffolding and configuration
- **Story**: US-01, US-02
- **Estimate**: 2 hours
- **Dependencies**: None
- **Status**: [ ] Not Started

Create CLI package structure:
- `pyproject.toml` with dependencies (typer, rich, httpx, websockets)
- Entry point: `asdlc` command
- Configuration module: load/save `~/.asdlc/config.yaml`
- Credentials module: secure storage in `~/.asdlc/credentials`

---

### T02: API client foundation
- **Story**: US-01
- **Estimate**: 3 hours
- **Dependencies**: T01
- **Status**: [ ] Not Started

Implement `src/asdlc_cli/client/`:
- `api.py`: Async REST client with httpx
- `auth.py`: Token management, refresh logic
- `exceptions.py`: Custom exceptions (AuthError, NotFoundError, etc.)
- Base URL configuration
- Request/response logging (debug mode)

---

### T03: Authentication commands
- **Story**: US-01
- **Estimate**: 2 hours
- **Dependencies**: T02
- **Status**: [ ] Not Started

Implement `asdlc auth`:
- `login`: Interactive OAuth flow (open browser) or `--token` flag
- `logout`: Clear stored credentials
- `status`: Show current auth state
- Token validation on startup

---

### T04: Context management commands
- **Story**: US-02
- **Estimate**: 1.5 hours
- **Dependencies**: T01
- **Status**: [ ] Not Started

Implement `asdlc context`:
- `set --repo=X --env=Y`: Store in config
- `show`: Display current context
- `list`: Fetch available repos/envs from API
- Context injection into all commands

---

### T05: Output formatting system
- **Story**: US-12
- **Estimate**: 2 hours
- **Dependencies**: T01
- **Status**: [ ] Not Started

Implement `src/asdlc_cli/output/`:
- `formatters.py`: Text (Rich), JSON, YAML formatters
- `tables.py`: Reusable table components
- Auto-detect TTY for color
- `--output`, `--no-color` flag handling

---

### T06: Epic commands
- **Story**: US-03
- **Estimate**: 2 hours
- **Dependencies**: T02, T04, T05
- **Status**: [ ] Not Started

Implement `asdlc epic`:
- `create "Title"`: POST to /api/epics
- `status EPIC-XXX`: GET epic with formatted output
- `list`: GET epics with `--state`, `--mine` filters
- Rich table output with progress bars

---

### T07: Workflow trigger commands
- **Story**: US-04
- **Estimate**: 2 hours
- **Dependencies**: T06
- **Status**: [ ] Not Started

Implement `asdlc run`:
- `discovery EPIC-XXX`: Trigger discovery phase
- `design EPIC-XXX`: Trigger design phase
- `develop EPIC-XXX`: Trigger development phase
- `validate EPIC-XXX`: Trigger validation phase
- `deploy EPIC-XXX`: Trigger deployment (with confirmation)
- `--wait` flag: Poll until complete
- `--open` flag: Open browser to run

---

### T08: Gate commands
- **Story**: US-05
- **Estimate**: 3 hours
- **Dependencies**: T02, T05
- **Status**: [ ] Not Started

Implement `asdlc gates`:
- `list`: GET pending gates with filters
- `show GATE-XXX`: GET gate details, format evidence summary
- `approve GATE-XXX`: POST approval decision
- `reject GATE-XXX --reason=...`: POST rejection with reason
- `check --epic=EPIC-XXX --required=HITL-X`: Return exit code
- `--open` flag: Open in browser for complex review

---

### T09: Run management commands
- **Story**: US-06
- **Estimate**: 2.5 hours
- **Dependencies**: T02, T05
- **Status**: [ ] Not Started

Implement `asdlc runs`:
- `list`: GET active runs with filters
- `show RUN-XXX`: GET run details
- `cancel RUN-XXX`: POST cancel request
- `rerun RUN-XXX`: POST rerun request

---

### T10: WebSocket client for log streaming
- **Story**: US-06
- **Estimate**: 2 hours
- **Dependencies**: T02
- **Status**: [ ] Not Started

Implement `src/asdlc_cli/client/websocket.py`:
- Connect to `/ws/runs/:id/logs`
- Stream logs to terminal
- Handle reconnection on disconnect
- Graceful shutdown on Ctrl+C

---

### T11: Run logs command with streaming
- **Story**: US-06
- **Estimate**: 1.5 hours
- **Dependencies**: T09, T10
- **Status**: [ ] Not Started

Implement `asdlc runs logs`:
- `logs RUN-XXX`: Fetch and display logs
- `logs RUN-XXX --follow`: Stream via WebSocket
- `logs RUN-XXX --tail=100`: Last N lines
- Syntax highlighting for log output

---

### T12: Artifact commands
- **Story**: US-07
- **Estimate**: 2.5 hours
- **Dependencies**: T02, T05
- **Status**: [ ] Not Started

Implement `asdlc artifacts`:
- `list EPIC-XXX`: GET artifacts list
- `show EPIC-XXX/path.md`: GET and display content
- `diff EPIC-XXX/path.md`: GET diff, format with colors
- `history EPIC-XXX/path.md`: GET version history
- `export EPIC-XXX -o bundle.zip`: Download ZIP

---

### T13: Budget commands
- **Story**: US-08
- **Estimate**: 1.5 hours
- **Dependencies**: T02, T05
- **Status**: [ ] Not Started

Implement `asdlc budget`:
- `status`: Overall spend and burn rate
- `status EPIC-XXX`: Per-epic spend
- `alert`: List active budget alerts
- Progress bars for budget utilization

---

### T14: Quick action commands
- **Story**: US-09
- **Estimate**: 1.5 hours
- **Dependencies**: T02
- **Status**: [ ] Not Started

Implement quick commands:
- `asdlc open EPIC-XXX|GATE-XXX|RUN-XXX`: Open in browser
- `asdlc status`: System health summary
- `asdlc workers list`: Worker pool status

---

### T15: Watch command with event streaming
- **Story**: US-09
- **Estimate**: 2 hours
- **Dependencies**: T10
- **Status**: [ ] Not Started

Implement `asdlc watch EPIC-XXX`:
- Connect to `/ws/events` filtered by epic
- Stream events with timestamps
- Color-code by event type
- Graceful exit on Ctrl+C

---

### T16: TUI application shell
- **Story**: US-10
- **Estimate**: 3 hours
- **Dependencies**: T06, T08, T09
- **Status**: [ ] Not Started

Implement `src/asdlc_cli/tui/`:
- Textual app shell with header/footer
- Main screen with epic selector
- Keybinding framework
- Navigation between screens

---

### T17: TUI screens and widgets
- **Story**: US-10
- **Estimate**: 4 hours
- **Dependencies**: T16
- **Status**: [ ] Not Started

Implement TUI screens:
- Epic overview screen
- Gates list and quick approve
- Runs list with status
- Artifact browser
- Action confirmations

---

### T18: Shell completions and packaging
- **Story**: US-11
- **Estimate**: 2 hours
- **Dependencies**: T01-T15
- **Status**: [ ] Not Started

Finalize distribution:
- `asdlc completion bash/zsh/fish`: Generate completions
- PyPI packaging and upload
- Homebrew formula
- Binary builds (PyInstaller)
- README with installation instructions

---

## Completion Checklist
- [ ] All tasks completed
- [ ] Unit tests passing with ≥80% coverage
- [ ] Integration tests against mock API
- [ ] E2E tests against test server
- [ ] All commands documented with `--help`
- [ ] README with examples
- [ ] Shell completions working
- [ ] PyPI package published (test.pypi.org first)

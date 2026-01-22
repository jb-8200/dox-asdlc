# P05-F05: CLI Interface

## Overview

Implement a command-line interface for aSDLC that enables automation, scripting, CI/CD integration, and quick actions for power users. The CLI complements the SPA by providing programmatic access to all core workflows.

## Dependencies

### Internal Dependencies
- **P02-F01**: Redis event streams (for `watch` command)
- **P02-F02**: Manager Agent API (for triggering workflows)
- **P02-F03**: HITL Dispatcher (for gate operations)
- **P05-F01**: HITL API endpoints (shared with SPA)

### External Dependencies
- Python 3.11+ (implementation language)
- Click or Typer (CLI framework)
- Rich (terminal formatting)
- Textual (TUI mode)
- httpx (async HTTP client)
- websockets (for streaming)

## Interfaces

### Consumes

**aSDLC REST API**
```
POST   /api/auth/login
GET    /api/epics
POST   /api/epics
GET    /api/epics/:id
POST   /api/epics/:id/runs
GET    /api/gates
POST   /api/gates/:id/decision
GET    /api/artifacts/:id
GET    /api/runs/:id
GET    /api/budget
```

**aSDLC WebSocket API**
```
/ws/events              # Global event feed
/ws/runs/:id/logs       # Run log streaming
```

### Provides

**CLI Binary**: `asdlc`

Installable via:
- PyPI: `pip install asdlc-cli`
- Homebrew: `brew install asdlc/tap/asdlc`
- Binary download

**Configuration File**: `~/.asdlc/config.yaml`
```yaml
server: https://asdlc.example.com
default_env: dev
default_repo: myorg/myrepo
output_format: text  # text, json, yaml
color: auto          # auto, always, never
```

**Credentials File**: `~/.asdlc/credentials` (secure permissions)
```yaml
token: eyJ...
expires_at: 2026-02-22T00:00:00Z
```

## Technical Approach

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      asdlc CLI                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Commands   │  │   Commands   │  │   Commands   │      │
│  │   (auth)     │  │   (epic)     │  │   (gates)    │  ... │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │               │
│         ▼                 ▼                 ▼               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    API Client                        │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │  REST       │  │  WebSocket  │  │  Auth       │  │   │
│  │  │  Client     │  │  Client     │  │  Manager    │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   Output Formatters                  │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐             │   │
│  │  │  Text   │  │  JSON   │  │  YAML   │             │   │
│  │  │ (Rich)  │  │         │  │         │             │   │
│  │  └─────────┘  └─────────┘  └─────────┘             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Command Groups

```
asdlc
├── auth
│   ├── login
│   ├── logout
│   └── status
├── context
│   ├── set
│   ├── show
│   └── list
├── epic
│   ├── create
│   ├── status
│   └── list
├── run
│   ├── discovery
│   ├── design
│   ├── develop
│   ├── validate
│   └── deploy
├── gates
│   ├── list
│   ├── show
│   ├── approve
│   ├── reject
│   └── check
├── runs
│   ├── list
│   ├── show
│   ├── logs
│   ├── cancel
│   └── rerun
├── artifacts
│   ├── list
│   ├── show
│   ├── diff
│   ├── history
│   └── export
├── budget
│   ├── status
│   └── alert
├── workers
│   └── list
├── status
├── watch
├── open
└── tui
```

### Implementation Patterns

**Command Structure (using Typer)**
```python
import typer
from rich.console import Console

app = typer.Typer()
console = Console()

@app.command()
def status(
    epic_id: str = typer.Argument(..., help="Epic ID"),
    output: str = typer.Option("text", "--output", "-o", help="Output format"),
):
    """Show epic status and progress."""
    client = get_api_client()
    epic = client.get_epic(epic_id)
    
    if output == "json":
        print_json(epic)
    else:
        print_epic_status(epic)
```

**API Client**
```python
class ASDLCClient:
    def __init__(self, config: Config):
        self.base_url = config.server
        self.token = config.get_token()
        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    async def get_epic(self, epic_id: str) -> Epic:
        response = await self._http.get(f"/api/epics/{epic_id}")
        response.raise_for_status()
        return Epic(**response.json())
```

**Output Formatting**
```python
def print_epic_status(epic: Epic):
    table = Table(title=f"Epic: {epic.id}")
    table.add_column("Field", style="cyan")
    table.add_column("Value")
    
    table.add_row("Title", epic.title)
    table.add_row("State", format_state(epic.state))
    table.add_row("Progress", f"{epic.progress}%")
    table.add_row("Budget", f"${epic.budget_used:.2f} / ${epic.budget_limit:.2f}")
    
    console.print(table)
```

### TUI Mode (Textual)

```python
from textual.app import App
from textual.widgets import Header, Footer, DataTable

class ASDLCApp(App):
    BINDINGS = [
        ("g", "show_gates", "Gates"),
        ("r", "show_runs", "Runs"),
        ("a", "show_artifacts", "Artifacts"),
        ("q", "quit", "Quit"),
    ]
    
    def compose(self):
        yield Header()
        yield EpicPanel()
        yield GatesTable()
        yield RunsTable()
        yield Footer()
```

## File Structure

```
asdlc-cli/
├── pyproject.toml
├── README.md
├── src/
│   └── asdlc_cli/
│       ├── __init__.py
│       ├── main.py              # Entry point
│       ├── config.py            # Configuration management
│       ├── client/
│       │   ├── __init__.py
│       │   ├── api.py           # REST client
│       │   ├── websocket.py     # WebSocket client
│       │   └── auth.py          # Authentication
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   ├── context.py
│       │   ├── epic.py
│       │   ├── run.py
│       │   ├── gates.py
│       │   ├── runs.py
│       │   ├── artifacts.py
│       │   ├── budget.py
│       │   └── workers.py
│       ├── output/
│       │   ├── __init__.py
│       │   ├── formatters.py    # Text/JSON/YAML formatters
│       │   └── tables.py        # Rich table helpers
│       └── tui/
│           ├── __init__.py
│           ├── app.py           # Textual app
│           └── widgets.py       # Custom widgets
└── tests/
    ├── __init__.py
    ├── test_commands/
    ├── test_client/
    └── test_output/
```

## Open Questions

1. **Package distribution**: Single `asdlc-cli` package or part of main `asdlc` package?
   - Recommendation: Separate package for lighter install in CI/CD

2. **Shell completions**: Generate at install time or on-demand?
   - Recommendation: On-demand via `asdlc completion bash/zsh/fish`

3. **Offline mode**: Should CLI cache any data for offline viewing?
   - Recommendation: No caching in MVP; consider for Phase 2

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| API changes break CLI | Users get errors | Version API, CLI checks compatibility |
| Token expiry during long operations | Interrupted workflows | Auto-refresh tokens |
| Large log streams overwhelm terminal | Poor UX | Pagination, `--tail` option |
| TUI complexity | Delayed delivery | TUI is Phase 2, core commands first |

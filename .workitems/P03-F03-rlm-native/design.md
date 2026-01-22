# P03-F03: RLM Native Implementation - Design

## Overview

RLM (Recursive LLM) is a native implementation of recursive exploration for long-context tasks. It enables agents to iteratively explore codebases and documents that exceed practical context limits, using a sub-call budget and REPL-style tool surface.

## Architecture

### Component Model

```
┌────────────────────────────────────────────────────────────────┐
│                       RLM Execution Engine                      │
│                                                                │
│  ┌─────────────────┐    ┌─────────────────┐                   │
│  │   RLMOrchestrator│───▶│  SubCallBudget  │                   │
│  │                 │    │  Manager        │                   │
│  └────────┬────────┘    └─────────────────┘                   │
│           │                                                    │
│           ▼                                                    │
│  ┌─────────────────┐    ┌─────────────────┐                   │
│  │  RLMAgent       │◀───│  REPLToolSurface│                   │
│  │  (Haiku model)  │    │                 │                   │
│  └────────┬────────┘    └─────────────────┘                   │
│           │                                                    │
│           ▼                                                    │
│  ┌─────────────────────────────────────────┐                  │
│  │          Exploration Trajectory          │                  │
│  │                                         │                  │
│  │  - Query history                        │                  │
│  │  - Tool call log                        │                  │
│  │  - Intermediate findings                │                  │
│  │  - Final synthesis                      │                  │
│  └─────────────────────────────────────────┘                  │
│                                                                │
└───────────────────────────┬────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
      ┌───────────────┐           ┌───────────────┐
      │  File System  │           │ telemetry/rlm │
      │  (read-only)  │           │ (audit logs)  │
      └───────────────┘           └───────────────┘
```

### Key Components

1. **RLMOrchestrator** - Coordinates RLM execution with budget management
2. **RLMAgent** - Executes exploration steps with Haiku model
3. **SubCallBudgetManager** - Tracks and enforces sub-call limits
4. **REPLToolSurface** - Restricted tool surface for exploration
5. **ExplorationTrajectory** - Records the full exploration path
6. **ResultSynthesizer** - Combines findings into final output

## Interfaces

### RLMOrchestrator Interface

```python
class RLMOrchestrator:
    """Orchestrates RLM exploration tasks."""

    async def explore(
        self,
        task_id: str,
        query: str,
        context_hints: list[str],
        max_subcalls: int = 50,
        max_subcalls_per_iteration: int = 8,
        timeout_seconds: int = 300,
    ) -> RLMResult:
        """Execute RLM exploration.

        Args:
            task_id: Unique identifier for this exploration
            query: Natural language query to explore
            context_hints: Files or symbols to start from
            max_subcalls: Total sub-call budget
            max_subcalls_per_iteration: Max calls per iteration
            timeout_seconds: Hard wall time limit

        Returns:
            RLMResult with findings and trajectory
        """
        ...
```

### REPLToolSurface Interface

```python
class REPLToolSurface:
    """Restricted tool surface for RLM exploration."""

    async def list_files(
        self,
        directory: str,
        pattern: str = "*",
        recursive: bool = False,
    ) -> list[str]:
        """List files matching pattern."""
        ...

    async def read_file(
        self,
        path: str,
        start_line: int | None = None,
        end_line: int | None = None,
    ) -> str:
        """Read file content, optionally a range."""
        ...

    async def grep(
        self,
        pattern: str,
        paths: list[str],
        context_lines: int = 2,
    ) -> list[GrepMatch]:
        """Search for pattern in files."""
        ...

    async def extract_symbols(
        self,
        path: str,
    ) -> list[SymbolInfo]:
        """Extract symbols from a file."""
        ...

    async def parse_ast(
        self,
        path: str,
    ) -> ParsedFile:
        """Parse file and return AST structure."""
        ...

    async def llm_query(
        self,
        prompt: str,
        context: str,
        max_tokens: int = 500,
    ) -> str:
        """Sub-model query with strict budget."""
        ...
```

## Data Models

### RLMResult

```python
@dataclass
class RLMResult:
    """Result from RLM exploration."""
    task_id: str
    success: bool
    findings: list[Finding]
    synthesis: str  # Final summarized answer
    trajectory: ExplorationTrajectory
    usage: RLMUsage
    citations: list[Citation]
    error: str | None = None
```

### Finding

```python
@dataclass
class Finding:
    """Individual finding from exploration."""
    description: str
    evidence: str
    source_file: str
    line_range: tuple[int, int] | None
    confidence: float  # 0.0 to 1.0
```

### Citation

```python
@dataclass
class Citation:
    """Citation to source material."""
    file_path: str
    line_start: int
    line_end: int
    content_hash: str
```

### ExplorationTrajectory

```python
@dataclass
class ExplorationTrajectory:
    """Records the full exploration path."""
    steps: list[ExplorationStep]
    start_time: datetime
    end_time: datetime
    total_subcalls: int
    cached_hits: int
```

### ExplorationStep

```python
@dataclass
class ExplorationStep:
    """Single step in exploration."""
    iteration: int
    thought: str  # Agent's reasoning
    tool_calls: list[ToolCall]
    findings_so_far: list[str]
    next_direction: str
```

### RLMUsage

```python
@dataclass
class RLMUsage:
    """Resource usage for RLM execution."""
    subcall_count: int
    cached_subcalls: int
    total_tokens: int
    wall_time_seconds: float
    model_calls: int
```

## RLM Execution Flow

### Step 1: Initialize
- Create exploration trajectory
- Initialize sub-call budget
- Set up tool surface with read-only access

### Step 2: Iterative Exploration
```
while budget_remaining and not_complete:
    1. Agent receives: query, findings_so_far, remaining_budget
    2. Agent plans: what to explore next
    3. Agent executes: tool calls (up to max_per_iteration)
    4. Agent reflects: update findings, decide if complete
    5. Record step in trajectory
```

### Step 3: Synthesis
- Combine all findings
- Generate citations
- Produce final answer

### Step 4: Audit
- Save trajectory to `telemetry/rlm/<task_id>.json`
- Record usage metrics

## Trigger Conditions

RLM is enabled when ANY of:
- Context requirement exceeds 100K tokens
- Multi-file dependency tracing required
- Debugger triggered by `fail_count > 4`
- Explicit RLM mode requested

## Cost and Safety Controls

| Control | Default | Description |
|---------|---------|-------------|
| `max_subcalls` | 50 | Total sub-call budget per task |
| `max_subcalls_per_iteration` | 8 | Calls per exploration step |
| `timeout_seconds` | 300 | Hard wall time limit |
| `model` | `claude-3-5-haiku-20241022` | Model for sub-calls |
| `max_tokens_per_subcall` | 500 | Token limit per sub-query |

### Sub-Call Caching

- Cache key: hash of prompt + context
- Cache duration: session lifetime
- Reuse identical sub-queries
- Track cache hit rate in metrics

### Security Restrictions

1. **No network access** - Tools cannot make HTTP requests
2. **Read-only filesystem** - Cannot modify files
3. **No shell commands** - Only predefined tools
4. **Allowlisted imports** - Python environment restricted

## Enabled Agents

| Agent | When RLM Enabled |
|-------|-----------------|
| Repo Mapper | Context exceeds 100K tokens |
| Arch Surveyor | Multi-file dependency analysis |
| Debugger | fail_count > 4, needs deep investigation |
| Validation | Integration test analysis across modules |

## Dependencies

### Required Components

- P03-F01: AgentRunner integration
- P03-F02: RepoMapper for initial context

### External Dependencies

- `anthropic` - Claude API (Haiku model for sub-calls)
- `tiktoken` - Token counting

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `RLM_MAX_SUBCALLS` | `50` | Default sub-call budget |
| `RLM_MAX_PER_ITERATION` | `8` | Max calls per iteration |
| `RLM_TIMEOUT` | `300` | Timeout in seconds |
| `RLM_MODEL` | `claude-3-5-haiku-20241022` | Sub-call model |
| `RLM_CACHE_ENABLED` | `true` | Enable sub-call caching |
| `RLM_AUDIT_DIR` | `telemetry/rlm` | Audit log directory |

## Audit Artifacts

### Per-Run Audit Log

Location: `telemetry/rlm/<task_id>.json`

```json
{
  "task_id": "task-123",
  "query": "Find all usages of deprecated API",
  "start_time": "2026-01-22T10:00:00Z",
  "end_time": "2026-01-22T10:02:30Z",
  "trajectory": {
    "steps": [...],
    "total_subcalls": 35,
    "cached_hits": 12
  },
  "findings": [...],
  "citations": [...],
  "usage": {
    "subcall_count": 35,
    "total_tokens": 45000,
    "wall_time_seconds": 150
  }
}
```

## Testing Strategy

- Unit tests: Mock tool surface, verify budget enforcement
- Integration tests: Real file exploration on test repo
- Budget tests: Verify hard limits respected
- Cache tests: Verify sub-call deduplication

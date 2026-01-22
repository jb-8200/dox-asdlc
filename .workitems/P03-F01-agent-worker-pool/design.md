# P03-F01: Agent Worker Pool Framework - Design

## Overview

This feature implements the stateless agent worker pool that executes domain agents (Discovery, Design, Development, Validation, Deployment). Workers consume tasks from Redis streams, execute Claude Agent SDK queries with role-specific tools and context packs, and publish completion events.

## Architecture

### Component Model

```
┌──────────────────────────────────────────────────────────────┐
│                      Worker Container                         │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  Worker 1   │  │  Worker 2   │  │  Worker N   │          │
│  │             │  │             │  │             │          │
│  │ EventConsumer│  │ EventConsumer│  │ EventConsumer│         │
│  │      ↓      │  │      ↓      │  │      ↓      │          │
│  │ AgentRunner │  │ AgentRunner │  │ AgentRunner │          │
│  │      ↓      │  │      ↓      │  │      ↓      │          │
│  │ ToolRegistry│  │ ToolRegistry│  │ ToolRegistry│          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                              │
└─────────────────────────────────┬────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
            ┌───────────────┐           ┌───────────────┐
            │ Redis Streams │           │ KnowledgeStore│
            │ (Events)      │           │ (RAG)         │
            └───────────────┘           └───────────────┘
```

### Key Components

1. **WorkerPool** - Manages multiple concurrent worker instances
2. **AgentRunner** - Executes Claude Agent SDK queries with isolation
3. **AgentRole** - Defines role-specific configurations (tools, prompts, constraints)
4. **ToolRegistry** - Provides role-filtered access to bash tool wrappers
5. **ContextLoader** - Loads context packs for task execution

## Interfaces

### AgentRole Protocol

```python
class AgentRole(Protocol):
    """Defines an agent role configuration."""

    @property
    def name(self) -> str:
        """Role name (e.g., 'coding', 'reviewer')."""
        ...

    @property
    def cluster(self) -> AgentCluster:
        """Cluster this role belongs to."""
        ...

    @property
    def system_prompt(self) -> str:
        """System prompt template for this role."""
        ...

    @property
    def allowed_tools(self) -> list[str]:
        """List of tool names this role can use."""
        ...

    @property
    def max_tokens(self) -> int:
        """Maximum output tokens for this role."""
        ...
```

### AgentRunner Interface

```python
class AgentRunner:
    """Executes agent queries with Claude Agent SDK."""

    async def run(
        self,
        role: AgentRole,
        task_id: str,
        context_pack: ContextPack,
        input_prompt: str,
    ) -> AgentResult:
        """Execute agent with role configuration and context."""
        ...
```

### WorkerPool Interface

```python
class WorkerPool:
    """Manages worker instances consuming from Redis streams."""

    async def start(self, worker_count: int) -> None:
        """Start specified number of workers."""
        ...

    async def stop(self) -> None:
        """Gracefully stop all workers."""
        ...

    async def scale(self, target_count: int) -> None:
        """Scale worker count up or down."""
        ...
```

## Data Models

### AgentResult

```python
@dataclass
class AgentResult:
    """Result from agent execution."""
    task_id: str
    role: str
    success: bool
    output: str  # Main output text
    artifacts: list[ArtifactRef]  # Generated artifacts
    tool_calls: list[ToolCall]  # Tool execution log
    usage: TokenUsage  # Token consumption
    error: str | None = None
```

### ContextPack

```python
@dataclass
class ContextPack:
    """Context pack for agent execution."""
    task_id: str
    role: str
    files: list[FileContent]
    symbols: list[SymbolInfo]
    dependencies: list[DependencyInfo]
    metadata: dict[str, Any]
```

### ToolCall

```python
@dataclass
class ToolCall:
    """Record of a tool invocation."""
    tool_name: str
    args: dict[str, Any]
    result: dict[str, Any]
    duration_ms: int
    success: bool
```

## Event Flow

### Input Events (consumed)

| Event Type | Description |
|------------|-------------|
| `AGENT_STARTED` | Dispatch from Manager Agent with role and context |

### Output Events (published)

| Event Type | Description |
|------------|-------------|
| `AGENT_COMPLETED` | Success with artifacts and results |
| `AGENT_FAILED` | Failure with error details |

## Dependencies

### Required Components

- P01-F01: Redis client, health checks
- P02-F01: EventConsumer, EventPublisher
- P02-F02: Task state integration

### External Dependencies

- `anthropic` - Claude API client
- `pydantic` - Data validation

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `WORKER_COUNT` | `2` | Number of concurrent workers |
| `CLAUDE_API_KEY` | (required) | Anthropic API key |
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` | Default model |
| `MAX_TOOL_CALLS` | `50` | Max tool calls per execution |
| `EXECUTION_TIMEOUT` | `300` | Timeout in seconds |

## Security Considerations

1. Workers have NO Git write access (governance principle)
2. Tool allowlist enforced per role
3. No network access from tool execution sandbox
4. API keys injected via environment only
5. Isolated execution per task (fresh session)

## Testing Strategy

- Unit tests: Mock Claude API responses, verify tool dispatch
- Integration tests: Real tool execution with test fixtures
- E2E tests: Full event flow from dispatch to completion

# P04-F05: Parallel Review Swarm - Technical Design

## Overview

The Parallel Review Swarm is a multi-agent code review system that spawns three specialized reviewer agents in parallel to analyze code from different perspectives (security, performance, style). Results are aggregated into a unified review report.

This feature demonstrates true parallel agent coordination using the Task tool pattern and Redis-based result collection.

## Goals

1. **Parallel Execution**: Execute 3 reviewer agents simultaneously using Task tool
2. **Specialized Analysis**: Each reviewer focuses on a specific concern domain
3. **Result Aggregation**: Merge findings into a coherent, deduplicated report
4. **Traceability**: Track which reviewer identified each finding
5. **API Integration**: Expose swarm review via REST endpoint

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Swarm Review Flow                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  API Request ──► SwarmDispatcher ──► Task Spawner                       │
│       │                │                  │                              │
│       │                ▼                  ├──► Task(security-reviewer)   │
│       │          Swarm Session           ├──► Task(performance-reviewer)│
│       │          (swarm:{uuid})          └──► Task(style-reviewer)      │
│       │                │                             │                   │
│       │                │         ┌───────────────────┘                  │
│       │                ▼         ▼                                       │
│       │          Redis: swarm:{id}:results                              │
│       │                │                                                 │
│       │                ▼                                                 │
│       │          ResultAggregator                                        │
│       │                │                                                 │
│       ▼                ▼                                                 │
│  API Response    Unified Report                                          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Swarm Session (`src/workers/swarm/session.py`)

Manages the lifecycle of a parallel review swarm.

```python
@dataclass
class SwarmSession:
    """Tracks a parallel review swarm execution."""

    id: str                        # swarm-{uuid8}
    target_path: str               # Code path or PR reference
    reviewers: list[str]           # ["security", "performance", "style"]
    status: SwarmStatus            # PENDING, IN_PROGRESS, AGGREGATING, COMPLETE, FAILED
    created_at: datetime
    completed_at: datetime | None
    results: dict[str, ReviewerResult]  # reviewer_id -> result
    unified_report: UnifiedReport | None

class SwarmStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AGGREGATING = "aggregating"
    COMPLETE = "complete"
    FAILED = "failed"
```

### 2. Swarm Dispatcher (`src/workers/swarm/dispatcher.py`)

Spawns parallel reviewer tasks and coordinates collection.

```python
class SwarmDispatcher:
    """Dispatches parallel reviewer agents using Task tool pattern."""

    async def dispatch_swarm(
        self,
        target_path: str,
        reviewer_types: list[str] = ["security", "performance", "style"],
        timeout_seconds: int = 300,
    ) -> SwarmSession:
        """
        Spawn parallel reviewer tasks and return session for tracking.

        Uses asyncio.gather for true parallel execution of Task calls.
        """
        ...

    async def collect_results(
        self,
        session_id: str,
        timeout_seconds: int = 60,
    ) -> dict[str, ReviewerResult]:
        """
        Collect results from Redis when all reviewers complete.
        """
        ...
```

### 3. Reviewer Variants (`src/workers/swarm/reviewers/`)

Specialized prompts and configurations for each reviewer type.

```python
# Base reviewer protocol (extends .claude/agents/reviewer.md)
class SpecializedReviewer(Protocol):
    """Protocol for specialized code reviewers."""

    reviewer_type: str
    focus_areas: list[str]
    severity_weights: dict[str, float]

    def get_system_prompt(self) -> str:
        """Return specialized system prompt for this reviewer."""
        ...

    def get_checklist(self) -> list[str]:
        """Return domain-specific review checklist."""
        ...

# Security Reviewer
class SecurityReviewer:
    reviewer_type = "security"
    focus_areas = [
        "authentication",
        "authorization",
        "input_validation",
        "secrets_exposure",
        "injection_vulnerabilities",
        "cryptography",
    ]

# Performance Reviewer
class PerformanceReviewer:
    reviewer_type = "performance"
    focus_areas = [
        "algorithmic_complexity",
        "memory_usage",
        "database_queries",
        "caching",
        "async_patterns",
        "resource_leaks",
    ]

# Style Reviewer
class StyleReviewer:
    reviewer_type = "style"
    focus_areas = [
        "naming_conventions",
        "code_organization",
        "documentation",
        "type_hints",
        "error_handling_patterns",
        "test_coverage",
    ]
```

### 4. Result Models (`src/workers/swarm/models.py`)

```python
@dataclass
class ReviewFinding:
    """A single finding from a reviewer."""

    id: str                    # finding-{uuid8}
    reviewer_type: str         # Which reviewer found this
    severity: Severity         # CRITICAL, HIGH, MEDIUM, LOW, INFO
    category: str              # e.g., "security/injection", "performance/n+1"
    title: str                 # Brief description
    description: str           # Detailed explanation
    file_path: str             # Affected file
    line_start: int | None     # Start line (if applicable)
    line_end: int | None       # End line (if applicable)
    code_snippet: str | None   # Relevant code
    recommendation: str        # How to fix
    confidence: float          # 0.0-1.0 reviewer confidence

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class ReviewerResult:
    """Result from a single specialized reviewer."""

    reviewer_type: str
    status: str                # "success" | "failed" | "timeout"
    findings: list[ReviewFinding]
    duration_seconds: float
    files_reviewed: list[str]
    error_message: str | None

@dataclass
class UnifiedReport:
    """Aggregated report from all reviewers."""

    swarm_id: str
    target_path: str
    created_at: datetime
    reviewers_completed: list[str]
    reviewers_failed: list[str]

    # Aggregated findings by severity
    critical_findings: list[ReviewFinding]
    high_findings: list[ReviewFinding]
    medium_findings: list[ReviewFinding]
    low_findings: list[ReviewFinding]
    info_findings: list[ReviewFinding]

    # Summary statistics
    total_findings: int
    findings_by_reviewer: dict[str, int]
    findings_by_category: dict[str, int]

    # Deduplication info
    duplicates_removed: int
```

### 5. Result Aggregator (`src/workers/swarm/aggregator.py`)

Merges findings from all reviewers into unified report.

```python
class ResultAggregator:
    """Aggregates results from multiple reviewers."""

    def aggregate(
        self,
        session: SwarmSession,
        results: dict[str, ReviewerResult],
    ) -> UnifiedReport:
        """
        Merge findings from all reviewers.

        - Deduplicates similar findings (same file/line/category)
        - Preserves attribution to original reviewer
        - Sorts by severity
        - Generates summary statistics
        """
        ...

    def _detect_duplicates(
        self,
        findings: list[ReviewFinding],
    ) -> tuple[list[ReviewFinding], int]:
        """
        Identify and merge duplicate findings.

        Duplicates are detected by:
        - Same file path + overlapping line ranges
        - Similar category (e.g., security/injection)
        - High text similarity in title/description (>0.8)

        When merging duplicates:
        - Keep highest severity
        - Combine descriptions
        - List all reviewers that found it
        """
        ...
```

### 6. Redis Coordination (`src/workers/swarm/redis_store.py`)

```python
class SwarmRedisStore:
    """Redis storage for swarm sessions and results."""

    # Key patterns
    SESSION_KEY = "swarm:session:{session_id}"      # Hash
    RESULTS_KEY = "swarm:results:{session_id}"      # Hash (reviewer -> JSON)
    PROGRESS_KEY = "swarm:progress:{session_id}"    # Set of completed reviewers

    async def create_session(self, session: SwarmSession) -> None:
        """Store new swarm session."""
        ...

    async def update_session_status(
        self,
        session_id: str,
        status: SwarmStatus,
    ) -> None:
        """Update session status atomically."""
        ...

    async def store_reviewer_result(
        self,
        session_id: str,
        reviewer_type: str,
        result: ReviewerResult,
    ) -> None:
        """Store result from a single reviewer."""
        ...

    async def get_completed_reviewers(
        self,
        session_id: str,
    ) -> set[str]:
        """Get set of reviewers that have completed."""
        ...

    async def wait_for_completion(
        self,
        session_id: str,
        expected_reviewers: list[str],
        timeout_seconds: int = 300,
    ) -> bool:
        """
        Wait until all expected reviewers complete or timeout.
        Uses Redis pub/sub for efficient waiting.
        """
        ...
```

### 7. Swarm API Endpoint (`src/orchestrator/routes/swarm.py`)

```python
@router.post("/api/swarm/review")
async def trigger_swarm_review(
    request: SwarmReviewRequest,
) -> SwarmReviewResponse:
    """
    Trigger a parallel review swarm.

    Request:
        {
            "target_path": "src/workers/",
            "reviewer_types": ["security", "performance", "style"],  # optional
            "timeout_seconds": 300  # optional
        }

    Response:
        {
            "swarm_id": "swarm-abc12345",
            "status": "in_progress",
            "poll_url": "/api/swarm/review/swarm-abc12345"
        }
    """
    ...

@router.get("/api/swarm/review/{swarm_id}")
async def get_swarm_status(
    swarm_id: str,
) -> SwarmStatusResponse:
    """
    Get status/results of a swarm review.

    Response when complete:
        {
            "swarm_id": "swarm-abc12345",
            "status": "complete",
            "unified_report": { ... },
            "duration_seconds": 45.2
        }
    """
    ...
```

## LLM Integration (ReviewExecutor)

The `ReviewExecutor` (`src/workers/swarm/executor.py`) orchestrates actual LLM-based code reviews for each reviewer type. It is composed of three classes:

- **`CodeExtractor`** -- Reads code files from the workspace, filters by extension (`.py`, `.ts`, `.tsx`, etc.), and enforces per-file and total size limits to stay within LLM context windows.
- **`ResponseParser`** -- Extracts structured JSON findings from LLM prose-wrapped responses. Uses a bracket-finding strategy (locating the outermost `[...]` or `{...}`) rather than relying on code-fence stripping, since LLMs frequently wrap JSON in explanatory text.
- **`ReviewExecutor`** -- Accepts an `LLMConfigService` and reviewer configuration. Builds a specialized prompt per reviewer type, calls the LLM, parses findings, and returns a `ReviewerResult`.

**Dispatch pattern:** The dispatcher uses fire-and-forget `asyncio.create_task()` instead of `await asyncio.gather()` so the API response returns immediately while reviews run in the background. Results are polled via the status endpoint.

**Wiring:** `src/workers/swarm/main.py` creates the `ReviewExecutor` (with encryption key from env) and injects it into the `SwarmDispatcher`. The orchestrator's `swarm.py` routes use the same pattern via `_ensure_swarm_components()` for lazy initialization.

## Task Tool Parallel Execution Pattern

The swarm uses the Task tool to spawn parallel agents. Here is the execution pattern:

```python
async def dispatch_parallel_tasks(self, target_path: str):
    """
    Spawn 3 reviewer tasks in parallel using asyncio.gather.

    Each task is independent and writes its result to Redis.
    """
    session_id = generate_swarm_id()

    # Create task coroutines (not awaited yet)
    tasks = [
        self._spawn_reviewer_task(
            session_id=session_id,
            reviewer_type="security",
            target_path=target_path,
        ),
        self._spawn_reviewer_task(
            session_id=session_id,
            reviewer_type="performance",
            target_path=target_path,
        ),
        self._spawn_reviewer_task(
            session_id=session_id,
            reviewer_type="style",
            target_path=target_path,
        ),
    ]

    # Execute in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle results/exceptions
    for reviewer_type, result in zip(["security", "performance", "style"], results):
        if isinstance(result, Exception):
            await self._store_failed_result(session_id, reviewer_type, result)
        else:
            # Result already stored in Redis by task
            pass

    return session_id
```

## Integration Points

### Existing Components Used

| Component | Source | Usage |
|-----------|--------|-------|
| Redis Client | `src/core/redis_client.py` | Result storage and coordination |
| Coordination MCP | `src/infrastructure/coordination/` | Message passing for status updates |
| Reviewer Agent | `.claude/agents/reviewer.md` | Base reviewer behavior |
| Event Types | `src/infrastructure/coordination/types.py` | Status message types |
| FastAPI Router | `src/orchestrator/routes/` | API endpoint patterns |

### New Message Types

Add to `src/infrastructure/coordination/types.py`:

```python
class MessageType(str, Enum):
    # ... existing types ...

    # Swarm coordination
    SWARM_STARTED = "SWARM_STARTED"
    SWARM_REVIEWER_COMPLETE = "SWARM_REVIEWER_COMPLETE"
    SWARM_COMPLETE = "SWARM_COMPLETE"
    SWARM_FAILED = "SWARM_FAILED"
```

## File Structure

```
src/workers/swarm/
├── __init__.py              # Public exports
├── models.py                # Data models (SwarmSession, ReviewFinding, etc.)
├── session.py               # SwarmSession management
├── dispatcher.py            # SwarmDispatcher (parallel task spawning)
├── aggregator.py            # ResultAggregator
├── redis_store.py           # SwarmRedisStore
└── reviewers/
    ├── __init__.py          # Reviewer registry
    ├── base.py              # SpecializedReviewer protocol
    ├── security.py          # SecurityReviewer
    ├── performance.py       # PerformanceReviewer
    └── style.py             # StyleReviewer

src/orchestrator/routes/
└── swarm.py                 # REST API endpoints

tests/
├── unit/
│   └── workers/
│       └── swarm/
│           ├── test_models.py
│           ├── test_dispatcher.py
│           ├── test_aggregator.py
│           └── test_redis_store.py
└── integration/
    └── workers/
        └── test_swarm_e2e.py
```

## Configuration

```python
@dataclass
class SwarmConfig:
    """Configuration for parallel review swarm."""

    # Timeouts
    task_timeout_seconds: int = 300      # Per-reviewer timeout
    aggregate_timeout_seconds: int = 60  # Aggregation timeout

    # Parallelism
    max_concurrent_swarms: int = 5       # Global limit
    default_reviewers: list[str] = field(
        default_factory=lambda: ["security", "performance", "style"]
    )

    # Redis keys
    key_prefix: str = "swarm"
    result_ttl_seconds: int = 86400      # 24 hours

    # Deduplication
    duplicate_similarity_threshold: float = 0.8
```

## Error Handling

| Error Scenario | Handling |
|----------------|----------|
| Reviewer task timeout | Mark reviewer as failed, continue with others |
| Reviewer task exception | Log error, store partial result if any |
| All reviewers fail | Return FAILED status with error details |
| Redis connection error | Retry with backoff, fail after 3 attempts |
| Aggregation error | Return raw results without aggregation |

## Security Considerations

1. **Path Validation**: Validate target_path is within allowed directories
2. **Rate Limiting**: Limit swarm creation to prevent resource exhaustion
3. **Result Sanitization**: Strip sensitive paths from public reports
4. **Timeout Enforcement**: Hard limits prevent runaway reviewers

## Performance Expectations

| Metric | Target |
|--------|--------|
| Swarm dispatch latency | < 100ms |
| Per-reviewer execution | 30-120s depending on codebase size |
| Result aggregation | < 5s |
| Redis round-trip | < 10ms |

With 3 parallel reviewers, total review time should be close to single-reviewer time (not 3x).

## Testing Strategy

1. **Unit Tests**
   - Model serialization/deserialization
   - Aggregator deduplication logic
   - Redis key generation

2. **Integration Tests**
   - Full swarm flow with stub reviewers
   - Redis storage and retrieval
   - API endpoint responses

3. **E2E Tests**
   - Real parallel execution with mock LLM
   - Timeout handling
   - Failure scenarios

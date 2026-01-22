# P02-F03: HITL Dispatcher and Decision Logging

## Technical Design

### Overview

The HITL (Human-In-The-Loop) Dispatcher manages gate requests, evidence bundles, and decision logging. It ensures that no workflow gate advances without human approval and maintains a complete audit trail of all governance decisions.

### Architecture Reference

From `docs/System_Design.md`:
- No gate advancement without artifacts and evidence bundles
- Records all gate requests and decisions
- Logs evidence bundles for each gate
- Pushes responses back to Redis Streams

### Dependencies

**Internal:**
- P02-F01: Redis event streams (events, publishing) ✅
- P02-F02: Manager Agent (task state machine) ✅
- P01-F01: Infrastructure (Docker, Redis) ✅
- P06-F05: Multi-tenancy (TenantContext) ✅

**External:**
- `redis.asyncio` (state storage)
- `pydantic` (model validation)

### Components

#### 1. Gate Types (`src/orchestrator/hitl_dispatcher.py`)

```python
class GateType(str, Enum):
    """HITL gates in the aSDLC workflow."""
    HITL_1_BACKLOG = "hitl_1_backlog"       # Approve PRD and backlog
    HITL_2_DESIGN = "hitl_2_design"         # Approve architecture
    HITL_3_PLAN = "hitl_3_plan"             # Approve task plan
    HITL_4_CODE = "hitl_4_code"             # Approve code changes
    HITL_5_VALIDATION = "hitl_5_validation" # Approve validation results
    HITL_6_RELEASE = "hitl_6_release"       # Approve release

class GateStatus(str, Enum):
    PENDING = "pending"       # Awaiting human review
    APPROVED = "approved"     # Human approved
    REJECTED = "rejected"     # Human rejected
    EXPIRED = "expired"       # Timed out without decision
```

#### 2. Evidence Bundle (`src/orchestrator/evidence_bundle.py`)

```python
@dataclass
class EvidenceItem:
    """Single piece of evidence for gate review."""
    item_type: str          # "artifact", "test_result", "report", etc.
    path: str               # Git path or URL
    description: str        # Human-readable description
    content_hash: str       # SHA256 of content for integrity
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class EvidenceBundle:
    """Collection of evidence for a gate request."""
    bundle_id: str
    task_id: str
    gate_type: GateType
    git_sha: str
    items: list[EvidenceItem]
    created_at: datetime
    summary: str            # Human-readable summary

    @classmethod
    def create(
        cls,
        task_id: str,
        gate_type: GateType,
        git_sha: str,
        items: list[EvidenceItem],
        summary: str,
    ) -> EvidenceBundle:
        """Create evidence bundle with generated ID."""

    def validate(self) -> bool:
        """Validate bundle has required evidence for gate type."""

    def to_dict(self) -> dict:
        """Serialize for Redis storage."""

    @classmethod
    def from_dict(cls, data: dict) -> EvidenceBundle:
        """Deserialize from Redis."""
```

#### 3. Gate Request (`src/orchestrator/hitl_dispatcher.py`)

```python
@dataclass
class GateRequest:
    """Request for human approval at a gate."""
    request_id: str
    task_id: str
    session_id: str
    gate_type: GateType
    status: GateStatus
    evidence_bundle: EvidenceBundle
    requested_by: str       # Agent that requested the gate
    requested_at: datetime
    expires_at: datetime | None = None
    decision: GateDecision | None = None

@dataclass
class GateDecision:
    """Human decision on a gate request."""
    decision_id: str
    request_id: str
    approved: bool
    reviewer: str           # Human reviewer ID
    reason: str             # Explanation for decision
    decided_at: datetime
    conditions: list[str] = field(default_factory=list)  # Approval conditions
```

#### 4. HITL Dispatcher (`src/orchestrator/hitl_dispatcher.py`)

```python
class HITLDispatcher:
    """Manages HITL gate requests and decisions."""

    REQUEST_KEY = "asdlc:gate_request:{request_id}"
    PENDING_SET = "asdlc:pending_gates"
    DECISION_KEY = "asdlc:gate_decision:{decision_id}"

    def __init__(
        self,
        redis_client: redis.Redis,
        event_publisher: EventPublisher,
        decision_logger: DecisionLogger,
    ):
        ...

    async def request_gate(
        self,
        task_id: str,
        gate_type: GateType,
        evidence_bundle: EvidenceBundle,
        requested_by: str,
        ttl_seconds: int | None = None,
    ) -> GateRequest:
        """Create a gate request and publish event."""

    async def get_pending_requests(
        self,
        gate_type: GateType | None = None,
    ) -> list[GateRequest]:
        """Get all pending gate requests."""

    async def record_decision(
        self,
        request_id: str,
        approved: bool,
        reviewer: str,
        reason: str,
        conditions: list[str] | None = None,
    ) -> GateDecision:
        """Record human decision and publish event."""

    async def check_expired(self) -> list[GateRequest]:
        """Find and mark expired requests."""

    async def get_request_by_id(
        self,
        request_id: str,
    ) -> GateRequest | None:
        """Get a gate request by ID."""
```

#### 5. Decision Logger (`src/orchestrator/decision_logger.py`)

```python
class DecisionLogger:
    """Maintains audit trail of all gate decisions."""

    LOG_KEY = "asdlc:decision_log:{task_id}"
    AUDIT_STREAM = "asdlc:audit"

    def __init__(self, redis_client: redis.Redis):
        ...

    async def log_request(
        self,
        request: GateRequest,
    ) -> None:
        """Log gate request creation."""

    async def log_decision(
        self,
        request: GateRequest,
        decision: GateDecision,
    ) -> None:
        """Log gate decision with full context."""

    async def get_task_history(
        self,
        task_id: str,
    ) -> list[dict]:
        """Get all gate decisions for a task."""

    async def get_audit_trail(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        gate_type: GateType | None = None,
    ) -> list[dict]:
        """Query audit trail with filters."""

    async def export_audit_log(
        self,
        task_id: str,
        format: str = "json",
    ) -> str:
        """Export audit log for compliance."""
```

### Redis Schema

**Gate Request (`asdlc:gate_request:{request_id}`):**
```json
{
    "request_id": "uuid",
    "task_id": "task-123",
    "session_id": "session-456",
    "gate_type": "hitl_4_code",
    "status": "pending",
    "evidence_bundle_id": "bundle-789",
    "requested_by": "coding-agent",
    "requested_at": "2026-01-22T10:00:00Z",
    "expires_at": "2026-01-22T22:00:00Z"
}
```

**Evidence Bundle (`asdlc:evidence_bundle:{bundle_id}`):**
```json
{
    "bundle_id": "uuid",
    "task_id": "task-123",
    "gate_type": "hitl_4_code",
    "git_sha": "abc123",
    "items": "[{...}]",
    "created_at": "2026-01-22T10:00:00Z",
    "summary": "Code review for user authentication feature"
}
```

**Pending Gates Set (`asdlc:pending_gates`):**
```
ZSET with request_id as member, expires_at timestamp as score
```

**Audit Stream (`asdlc:audit`):**
```
Stream with audit events for compliance logging
```

### Event Flow

```
Agent completes work
        │
        ▼
┌──────────────────┐
│ Create Evidence  │
│ Bundle           │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────────┐
│ Request Gate     │────▶│ GATE_REQUESTED   │
│ (HITLDispatcher) │     │ event published  │
└────────┬─────────┘     └────────┬─────────┘
         │                        │
         ▼                        ▼
┌──────────────────┐     ┌──────────────────┐
│ Task blocked at  │     │ HITL-UI displays │
│ BLOCKED_HITL     │     │ request          │
└──────────────────┘     └────────┬─────────┘
                                  │
                         Human reviews
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Decision made    │
                         └────────┬─────────┘
                                  │
         ┌────────────────────────┴────────────────────────┐
         ▼                                                 ▼
┌──────────────────┐                              ┌──────────────────┐
│ GATE_APPROVED    │                              │ GATE_REJECTED    │
│ event published  │                              │ event published  │
└────────┬─────────┘                              └────────┬─────────┘
         │                                                 │
         ▼                                                 ▼
┌──────────────────┐                              ┌──────────────────┐
│ Task advances to │                              │ Task returns to  │
│ next state       │                              │ previous state   │
└──────────────────┘                              └──────────────────┘
```

### Required Evidence by Gate Type

| Gate | Required Evidence |
|------|------------------|
| HITL_1_BACKLOG | PRD, acceptance criteria, epic definition |
| HITL_2_DESIGN | Architecture doc, component diagram |
| HITL_3_PLAN | Task breakdown, dependency graph |
| HITL_4_CODE | Patch file, test results, review report |
| HITL_5_VALIDATION | Integration tests, security scan, validation report |
| HITL_6_RELEASE | Release notes, deployment plan, rollback plan |

### Integration with State Machine

When gate is requested:
```python
# In Manager Agent
await task_manager.update_state(task_id, TaskState.BLOCKED_HITL)
await hitl_dispatcher.request_gate(task_id, gate_type, evidence_bundle)
```

When gate is approved:
```python
# Event handler for GATE_APPROVED
await task_manager.update_state(task_id, next_state)
# Continue workflow
```

When gate is rejected:
```python
# Event handler for GATE_REJECTED
await task_manager.update_state(task_id, TaskState.IN_PROGRESS)
await task_manager.increment_fail_count(task_id)
# Re-dispatch to agent with feedback
```

### Testing Strategy

1. **Unit tests**: Gate request/decision models, evidence validation
2. **Integration tests**: Full gate flow with Redis
3. **Audit tests**: Verify audit trail completeness

### Files to Create

| File | Action |
|------|--------|
| `src/orchestrator/evidence_bundle.py` | Create |
| `src/orchestrator/hitl_dispatcher.py` | Create |
| `src/orchestrator/decision_logger.py` | Create |
| `tests/unit/test_evidence_bundle.py` | Create |
| `tests/unit/test_hitl_dispatcher.py` | Create |
| `tests/unit/test_decision_logger.py` | Create |
| `tests/integration/test_hitl_workflow.py` | Create |

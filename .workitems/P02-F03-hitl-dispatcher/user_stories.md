# P02-F03: User Stories

## US-01: Gate Request Creation

**As a** Manager Agent
**I want to** create gate requests with evidence
**So that** humans can review and approve workflow progression

### Acceptance Criteria

- [ ] Gate requests are created with unique IDs
- [ ] Requests include task context (task_id, session_id, git_sha)
- [ ] Evidence bundle is attached to request
- [ ] `GATE_REQUESTED` event is published
- [ ] Task state is set to BLOCKED_HITL
- [ ] Optional expiration time is supported

### Test Cases

```python
def test_request_gate_creates_request():
    """Gate request is persisted in Redis."""

def test_request_gate_publishes_event():
    """GATE_REQUESTED event is published."""

def test_request_gate_with_expiry():
    """Request can have expiration time."""
```

---

## US-02: Evidence Bundle Validation

**As a** HITL Dispatcher
**I want to** validate evidence bundles
**So that** gates have required artifacts before review

### Acceptance Criteria

- [ ] Each gate type has required evidence items
- [ ] Missing required evidence fails validation
- [ ] Evidence items have content hashes for integrity
- [ ] Bundle includes summary for reviewers
- [ ] Validation errors are descriptive

### Test Cases

```python
def test_code_gate_requires_patch():
    """HITL_4_CODE gate requires patch file."""

def test_missing_evidence_fails_validation():
    """Bundle without required items is invalid."""

def test_evidence_hash_is_generated():
    """Content hash is computed for each item."""
```

---

## US-03: Gate Decision Recording

**As a** HITL-UI
**I want to** record approval/rejection decisions
**So that** workflow can proceed based on human judgment

### Acceptance Criteria

- [ ] Decisions are recorded with reviewer identity
- [ ] Decision includes reason/explanation
- [ ] Conditional approvals supported (with conditions list)
- [ ] `GATE_APPROVED` or `GATE_REJECTED` event published
- [ ] Request status is updated
- [ ] Decision timestamp is recorded

### Test Cases

```python
def test_approve_decision_updates_status():
    """Approval sets request status to APPROVED."""

def test_reject_decision_includes_reason():
    """Rejection includes reviewer's explanation."""

def test_conditional_approval_records_conditions():
    """Approval can include conditions to satisfy."""
```

---

## US-04: Pending Gate Queries

**As a** HITL-UI
**I want to** query pending gate requests
**So that** reviewers can see work awaiting approval

### Acceptance Criteria

- [ ] List all pending requests
- [ ] Filter by gate type
- [ ] Filter by tenant (multi-tenant mode)
- [ ] Sort by request time or priority
- [ ] Include evidence bundle summaries

### Test Cases

```python
def test_get_pending_returns_pending_only():
    """Completed requests are not returned."""

def test_filter_by_gate_type():
    """Can filter to specific gate type."""

def test_tenant_isolation():
    """Requests are filtered by tenant."""
```

---

## US-05: Decision Audit Trail

**As an** auditor
**I want to** review all gate decisions
**So that** I can verify governance compliance

### Acceptance Criteria

- [ ] All gate requests are logged
- [ ] All decisions are logged with context
- [ ] Logs include who, what, when, why
- [ ] Logs are immutable (append-only stream)
- [ ] Logs can be exported for compliance
- [ ] Logs can be queried by date range, task, gate type

### Test Cases

```python
def test_request_is_logged():
    """Gate request creates audit entry."""

def test_decision_is_logged():
    """Decision creates audit entry with full context."""

def test_audit_trail_is_immutable():
    """Audit entries cannot be modified."""

def test_export_audit_log():
    """Audit log can be exported as JSON."""
```

---

## US-06: Gate Expiration Handling

**As a** Manager Agent
**I want to** handle expired gate requests
**So that** stalled workflows are surfaced

### Acceptance Criteria

- [ ] Requests can have optional TTL
- [ ] Expired requests are marked as EXPIRED
- [ ] Expiration publishes `GATE_EXPIRED` event
- [ ] Expired gates are logged for review
- [ ] Batch check for expired gates supported

### Test Cases

```python
def test_expired_request_is_marked():
    """Request past expiry is set to EXPIRED status."""

def test_expiration_publishes_event():
    """Expired gate publishes GATE_EXPIRED event."""

def test_batch_expiration_check():
    """Multiple expired gates handled in one call."""
```

---

## US-07: Task History Query

**As a** developer
**I want to** see gate history for a task
**So that** I understand the review progression

### Acceptance Criteria

- [ ] All gates for a task are retrievable
- [ ] History includes request and decision details
- [ ] Ordered chronologically
- [ ] Includes evidence bundle references
- [ ] Shows current gate status

### Test Cases

```python
def test_task_history_includes_all_gates():
    """All gate requests for task are returned."""

def test_history_is_chronological():
    """History is sorted by timestamp."""

def test_history_includes_decisions():
    """Each request includes its decision if made."""
```

---

## US-08: Integration with Manager Agent

**As a** Manager Agent
**I want to** seamlessly integrate HITL gates
**So that** workflow pauses and resumes correctly

### Acceptance Criteria

- [ ] Manager Agent calls dispatcher for gates
- [ ] Task state transitions to BLOCKED_HITL
- [ ] GATE_APPROVED event resumes workflow
- [ ] GATE_REJECTED event triggers retry
- [ ] State machine enforces gate requirements

### Test Cases

```python
def test_gate_blocks_task():
    """Task cannot proceed past gate without approval."""

def test_approval_advances_task():
    """GATE_APPROVED allows task to continue."""

def test_rejection_triggers_retry():
    """GATE_REJECTED increments fail_count and retries."""
```

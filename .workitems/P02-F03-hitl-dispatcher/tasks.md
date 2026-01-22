# P02-F03: Tasks

## Task Breakdown

### T01: Create Gate and Evidence Models
**File:** `src/orchestrator/evidence_bundle.py`
**Test:** `tests/unit/test_evidence_bundle.py`

- [x] Define `GateType` enum with all 6 gates
- [x] Define `GateStatus` enum
- [x] Create `EvidenceItem` dataclass
- [x] Create `EvidenceBundle` dataclass with validation
- [x] Implement `create()` factory method
- [x] Implement `validate()` for required evidence by gate type
- [x] Implement serialization (to_dict/from_dict)
- [x] Write unit tests for models and validation

**Estimate:** 1.5h

---

### T02: Create Gate Request and Decision Models
**File:** `src/orchestrator/hitl_dispatcher.py`
**Test:** `tests/unit/test_hitl_dispatcher.py`

- [x] Create `GateRequest` dataclass
- [x] Create `GateDecision` dataclass
- [x] Implement serialization for Redis storage
- [x] Add expiration calculation
- [x] Write unit tests for models

**Estimate:** 1h

---

### T03: Implement HITL Dispatcher - Request Creation
**File:** `src/orchestrator/hitl_dispatcher.py`
**Test:** `tests/unit/test_hitl_dispatcher.py`

- [x] Create `HITLDispatcher` class
- [x] Implement `request_gate()` method
- [x] Store request in Redis hash
- [x] Add to pending gates sorted set
- [x] Publish `GATE_REQUESTED` event
- [x] Support optional TTL
- [x] Add tenant prefix support
- [x] Write unit tests

**Estimate:** 1.5h

---

### T04: Implement HITL Dispatcher - Decision Recording
**File:** `src/orchestrator/hitl_dispatcher.py`
**Test:** `tests/unit/test_hitl_dispatcher.py`

- [x] Implement `record_decision()` method
- [x] Validate request exists and is pending
- [x] Store decision in Redis
- [x] Update request status
- [x] Remove from pending set
- [x] Publish `GATE_APPROVED` or `GATE_REJECTED` event
- [x] Write unit tests

**Estimate:** 1.5h

---

### T05: Implement HITL Dispatcher - Queries
**File:** `src/orchestrator/hitl_dispatcher.py`
**Test:** `tests/unit/test_hitl_dispatcher.py`

- [x] Implement `get_pending_requests()` with filters
- [x] Implement `get_request_by_id()`
- [x] Implement `check_expired()` for TTL handling
- [x] Add pagination support for pending list
- [x] Write unit tests

**Estimate:** 1h

---

### T06: Implement Decision Logger
**File:** `src/orchestrator/decision_logger.py`
**Test:** `tests/unit/test_decision_logger.py`

- [x] Create `DecisionLogger` class
- [x] Implement `log_request()` - append to audit stream
- [x] Implement `log_decision()` - append with full context
- [x] Implement `get_task_history()` - query by task
- [x] Implement `get_audit_trail()` - query with filters
- [x] Implement `export_audit_log()` - JSON export
- [x] Add tenant prefix support
- [x] Write unit tests

**Estimate:** 1.5h

---

### T07: Add Required Evidence Definitions
**File:** `src/orchestrator/evidence_bundle.py`
**Test:** `tests/unit/test_evidence_bundle.py`

- [x] Define required evidence for HITL_1_BACKLOG
- [x] Define required evidence for HITL_2_DESIGN
- [x] Define required evidence for HITL_3_PLAN
- [x] Define required evidence for HITL_4_CODE
- [x] Define required evidence for HITL_5_VALIDATION
- [x] Define required evidence for HITL_6_RELEASE
- [x] Add validation for each gate type
- [x] Write tests for evidence requirements

**Estimate:** 1h

---

### T08: Integration Tests
**File:** `tests/integration/test_hitl_workflow.py`

- [x] Test full gate request → decision flow
- [x] Test audit trail completeness
- [x] Test expiration handling
- [x] Test tenant isolation
- [x] Test integration with task state machine

**Estimate:** 2h

---

## Progress

- Started: 2026-01-22
- Tasks Complete: 8/8
- Percentage: 100%
- Status: COMPLETE
- Blockers: None

## Completion Notes

All tasks implemented:
- [x] T01: Gate and Evidence Models - 9 tests
- [x] T02: Gate Request and Decision Models - 4 tests
- [x] T03: HITL Dispatcher Request Creation - 1 test
- [x] T04: HITL Dispatcher Decision Recording - 1 test
- [x] T05: HITL Dispatcher Queries - 2 tests
- [x] T06: Decision Logger - integrated into HITLDispatcher
- [x] T07: Required Evidence Definitions - 3 tests
- [x] T08: Integration Tests - 5 tests

Total: 25 unit tests + integration tests

## Dependency Notes

- Requires P02-F01 (EventPublisher, ASDLCEvent) - implement first
- Requires P02-F02 (TaskStateMachine) - implement second
- Uses `TenantContext` from P06-F05 (available)
- Uses `HITLError`, `GateApprovalError` from `src/core/exceptions.py` (available)

# P03-F01: Agent Worker Pool Framework - Tasks

## Overview

Task breakdown for implementing the stateless agent worker pool.

## Dependencies

- **P02-F01**: Event consumer and publisher - COMPLETE
- **P02-F02**: Manager Agent and task state - COMPLETE
- **P01-F01**: Redis client and health checks - COMPLETE

## Task List

### T01: Define AgentRole and AgentCluster models

**File:** `src/workers/agent_role.py`
**Test:** `tests/unit/test_agent_role.py`

- [ ] Define `AgentCluster` enum (DISCOVERY, DESIGN, DEVELOPMENT, VALIDATION, DEPLOYMENT)
- [ ] Define `AgentRole` dataclass with name, cluster, system_prompt, allowed_tools, max_tokens
- [ ] Create role registry with predefined roles
- [ ] Implement `get_role()` lookup function
- [ ] Write unit tests for role definitions

**Estimate:** 1h

---

### T02: Define ContextPack and AgentResult models

**File:** `src/workers/models.py`
**Test:** `tests/unit/test_worker_models.py`

- [ ] Define `FileContent` dataclass for context files
- [ ] Define `SymbolInfo` dataclass for code symbols
- [ ] Define `ContextPack` dataclass
- [ ] Define `ToolCall` dataclass
- [ ] Define `TokenUsage` dataclass
- [ ] Define `ArtifactRef` dataclass
- [ ] Define `AgentResult` dataclass
- [ ] Add JSON serialization methods
- [ ] Write unit tests for all models

**Estimate:** 1.5h

---

### T03: Implement ToolRegistry

**File:** `src/workers/tool_registry.py`
**Test:** `tests/unit/test_tool_registry.py`

- [ ] Create `ToolRegistry` class
- [ ] Implement `get_tools_for_role()` with allowlist filtering
- [ ] Implement `execute_tool()` invoking bash wrappers
- [ ] Parse JSON output from tools
- [ ] Handle tool execution errors
- [ ] Add timeout handling
- [ ] Write unit tests with mock tools

**Estimate:** 1.5h

---

### T04: Implement ContextLoader

**File:** `src/workers/context_loader.py`
**Test:** `tests/unit/test_context_loader.py`

- [ ] Create `ContextLoader` class
- [ ] Implement `load_from_path()` to read context pack JSON
- [ ] Validate context pack structure
- [ ] Handle missing files gracefully
- [ ] Support context pack from event payload (inline)
- [ ] Write unit tests with fixtures

**Estimate:** 1h

---

### T05: Implement AgentRunner core

**File:** `src/workers/agent_runner.py`
**Test:** `tests/unit/test_agent_runner.py`

- [ ] Create `AgentRunner` class
- [ ] Inject Anthropic client and ToolRegistry
- [ ] Implement `run()` method with Claude API call
- [ ] Build messages with system prompt and context
- [ ] Handle tool_use responses
- [ ] Dispatch tool calls to ToolRegistry
- [ ] Collect token usage
- [ ] Return AgentResult
- [ ] Write unit tests with mocked Anthropic client

**Estimate:** 2h

---

### T06: Implement AgentRunner error handling

**File:** `src/workers/agent_runner.py`
**Test:** `tests/unit/test_agent_runner.py`

- [ ] Handle API rate limit errors
- [ ] Handle API timeout errors
- [ ] Handle tool execution failures
- [ ] Implement retry logic for transient errors
- [ ] Set execution timeout
- [ ] Cap tool call count
- [ ] Write unit tests for error scenarios

**Estimate:** 1.5h

---

### T07: Implement Worker class

**File:** `src/workers/worker.py`
**Test:** `tests/unit/test_worker.py`

- [ ] Create `Worker` class
- [ ] Inject EventConsumer, AgentRunner, ContextLoader
- [ ] Implement `start()` with event consumption loop
- [ ] Implement `stop()` for graceful shutdown
- [ ] Handle AGENT_STARTED events
- [ ] Publish AGENT_COMPLETED or AGENT_FAILED
- [ ] Add idempotency check for duplicate events
- [ ] Write unit tests

**Estimate:** 2h

---

### T08: Implement WorkerPool

**File:** `src/workers/pool.py`
**Test:** `tests/unit/test_worker_pool.py`

- [ ] Create `WorkerPool` class
- [ ] Implement `start()` to launch workers concurrently
- [ ] Implement `stop()` to shut down all workers
- [ ] Implement `scale()` to adjust worker count
- [ ] Track worker health status
- [ ] Handle worker failures with restart
- [ ] Write unit tests

**Estimate:** 1.5h

---

### T09: Update workers/main.py entry point

**File:** `src/workers/main.py`
**Test:** `tests/unit/test_workers_main.py`

- [ ] Initialize WorkerPool with configuration
- [ ] Start pool on service startup
- [ ] Update health checks to include pool status
- [ ] Handle SIGTERM for graceful shutdown
- [ ] Add structured logging
- [ ] Write unit tests for startup/shutdown

**Estimate:** 1h

---

### T10: Add worker-specific exceptions

**File:** `src/core/exceptions.py`
**Test:** `tests/unit/test_exceptions.py`

- [ ] Add `AgentExecutionError` base class
- [ ] Add `ToolExecutionError`
- [ ] Add `ContextLoadError`
- [ ] Add `RateLimitError`
- [ ] Add `ExecutionTimeoutError`
- [ ] Write unit tests

**Estimate:** 30min

---

### T11: Integration tests for worker execution

**File:** `tests/integration/test_worker_execution.py`

- [ ] Test full event flow: AGENT_STARTED → execution → AGENT_COMPLETED
- [ ] Test tool execution with real bash wrappers
- [ ] Test failure handling with AGENT_FAILED
- [ ] Test idempotent processing
- [ ] Test multiple workers in pool

**Estimate:** 2h

---

### T12: Add worker configuration and documentation

**File:** `src/workers/config.py`

- [ ] Create `WorkerConfig` dataclass
- [ ] Load from environment variables
- [ ] Document all configuration options
- [ ] Add defaults for local development
- [ ] Update design.md with final implementation notes

**Estimate:** 30min

---

## Progress

- **Started**: (not started)
- **Tasks Complete**: 0/12
- **Percentage**: 0%
- **Status**: PENDING
- **Blockers**: None

## Task Summary

| Task | Description | Estimate | Status |
|------|-------------|----------|--------|
| T01 | AgentRole and AgentCluster models | 1h | [ ] |
| T02 | ContextPack and AgentResult models | 1.5h | [ ] |
| T03 | ToolRegistry implementation | 1.5h | [ ] |
| T04 | ContextLoader implementation | 1h | [ ] |
| T05 | AgentRunner core | 2h | [ ] |
| T06 | AgentRunner error handling | 1.5h | [ ] |
| T07 | Worker class | 2h | [ ] |
| T08 | WorkerPool | 1.5h | [ ] |
| T09 | Update main.py entry point | 1h | [ ] |
| T10 | Worker-specific exceptions | 30min | [ ] |
| T11 | Integration tests | 2h | [ ] |
| T12 | Configuration and documentation | 30min | [ ] |

**Total Estimated Time**: 15 hours

## Completion Checklist

- [ ] All tasks in Task List are marked complete
- [ ] All unit tests pass: `./tools/test.sh tests/unit/`
- [ ] All integration tests pass: `./tools/test.sh tests/integration/`
- [ ] E2E tests pass: `./tools/e2e.sh`
- [ ] Linter passes: `./tools/lint.sh src/`
- [ ] No type errors: `mypy src/`
- [ ] Documentation updated
- [ ] Interface contracts verified against design.md
- [ ] Progress marked as 100% in tasks.md

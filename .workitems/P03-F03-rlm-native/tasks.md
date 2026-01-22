# P03-F03: RLM Native Implementation - Tasks

## Overview

Task breakdown for implementing the native RLM (Recursive LLM) exploration system.

## Dependencies

- **P03-F01**: AgentRunner, AgentResult models - (in progress)
- **P03-F02**: RepoMapper for initial context, parsers - (in progress)

## Task List

### T01: Define RLM data models

**File:** `src/workers/rlm/models.py`
**Test:** `tests/unit/test_rlm_models.py`

- [ ] Define `Finding` dataclass
- [ ] Define `Citation` dataclass
- [ ] Define `ExplorationStep` dataclass
- [ ] Define `ExplorationTrajectory` dataclass
- [ ] Define `RLMUsage` dataclass
- [ ] Define `RLMResult` dataclass
- [ ] Define `GrepMatch` dataclass
- [ ] Add JSON serialization methods
- [ ] Write unit tests for all models

**Estimate:** 1h

---

### T02: Implement SubCallBudgetManager

**File:** `src/workers/rlm/budget_manager.py`
**Test:** `tests/unit/test_budget_manager.py`

- [ ] Create `SubCallBudgetManager` class
- [ ] Track total sub-calls used
- [ ] Track per-iteration sub-calls
- [ ] Implement `can_make_call()` check
- [ ] Implement `record_call()` method
- [ ] Implement `reset_iteration()` for new iteration
- [ ] Raise `BudgetExceededError` when exceeded
- [ ] Write unit tests

**Estimate:** 1h

---

### T03: Implement SubCallCache

**File:** `src/workers/rlm/cache.py`
**Test:** `tests/unit/test_subcall_cache.py`

- [ ] Create `SubCallCache` class
- [ ] Implement cache key generation (hash of prompt + context)
- [ ] Implement `get()` method
- [ ] Implement `set()` method
- [ ] Track cache hit statistics
- [ ] Support cache clearing
- [ ] Write unit tests

**Estimate:** 1h

---

### T04: Implement REPLToolSurface - File Operations

**File:** `src/workers/rlm/tools/file_tools.py`
**Test:** `tests/unit/test_rlm_file_tools.py`

- [ ] Implement `list_files()` with glob pattern support
- [ ] Implement `read_file()` with line range support
- [ ] Implement `grep()` with context lines
- [ ] Ensure read-only access (no writes)
- [ ] Validate paths are within repo
- [ ] Write unit tests with file fixtures

**Estimate:** 1.5h

---

### T05: Implement REPLToolSurface - Symbol Operations

**File:** `src/workers/rlm/tools/symbol_tools.py`
**Test:** `tests/unit/test_rlm_symbol_tools.py`

- [ ] Implement `extract_symbols()` using P03-F02 parsers
- [ ] Implement `parse_ast()` using P03-F02 parsers
- [ ] Handle unsupported file types
- [ ] Handle parse errors gracefully
- [ ] Write unit tests

**Estimate:** 1h

---

### T06: Implement REPLToolSurface - LLM Query

**File:** `src/workers/rlm/tools/llm_query.py`
**Test:** `tests/unit/test_rlm_llm_query.py`

- [ ] Implement `llm_query()` invoking Haiku model
- [ ] Enforce token limit per query
- [ ] Integrate with SubCallBudgetManager
- [ ] Integrate with SubCallCache
- [ ] Handle API errors
- [ ] Write unit tests with mocked Anthropic client

**Estimate:** 1.5h

---

### T07: Implement REPLToolSurface Registry

**File:** `src/workers/rlm/tools/__init__.py`
**Test:** `tests/unit/test_repl_tool_surface.py`

- [ ] Create `REPLToolSurface` class aggregating all tools
- [ ] Implement tool dispatch by name
- [ ] Enforce tool allowlist
- [ ] Log all tool invocations
- [ ] Write unit tests

**Estimate:** 30min

---

### T08: Implement RLMAgent

**File:** `src/workers/rlm/agent.py`
**Test:** `tests/unit/test_rlm_agent.py`

- [ ] Create `RLMAgent` class
- [ ] Inject Anthropic client and tool surface
- [ ] Design exploration prompt template
- [ ] Implement single iteration execution
- [ ] Parse agent output for tool calls and thoughts
- [ ] Accumulate findings across iterations
- [ ] Write unit tests with mocked responses

**Estimate:** 2h

---

### T09: Implement RLMOrchestrator

**File:** `src/workers/rlm/orchestrator.py`
**Test:** `tests/unit/test_rlm_orchestrator.py`

- [ ] Create `RLMOrchestrator` class
- [ ] Inject RLMAgent, BudgetManager, Cache
- [ ] Implement `explore()` method with iteration loop
- [ ] Implement timeout handling with asyncio.timeout
- [ ] Handle budget exhaustion gracefully
- [ ] Synthesize final result from findings
- [ ] Generate citations from tool calls
- [ ] Write unit tests

**Estimate:** 2h

---

### T10: Implement Audit Trail Generation

**File:** `src/workers/rlm/audit.py`
**Test:** `tests/unit/test_rlm_audit.py`

- [ ] Create `RLMAuditor` class
- [ ] Implement `save_trajectory()` to telemetry/rlm/
- [ ] Include full exploration steps
- [ ] Include usage metrics
- [ ] Include citations
- [ ] Implement `load_trajectory()` for replay
- [ ] Write unit tests

**Estimate:** 1h

---

### T11: Implement RLM Trigger Detection

**File:** `src/workers/rlm/trigger.py`
**Test:** `tests/unit/test_rlm_trigger.py`

- [ ] Create `RLMTriggerDetector` class
- [ ] Check context size > 100K tokens
- [ ] Check multi-file dependency requirement
- [ ] Check fail_count > 4 for Debugger
- [ ] Check explicit RLM mode request
- [ ] Return trigger reason
- [ ] Write unit tests

**Estimate:** 1h

---

### T12: Integrate RLM with AgentRunner

**File:** `src/workers/agent_runner.py` (update)
**Test:** `tests/unit/test_agent_runner_rlm.py`

- [ ] Add RLM mode support to AgentRunner
- [ ] Use RLMTriggerDetector to decide mode
- [ ] Route to RLMOrchestrator when triggered
- [ ] Format RLM results for agent consumption
- [ ] Write integration tests

**Estimate:** 1.5h

---

### T13: Add RLM exceptions and configuration

**Files:** `src/core/exceptions.py`, `src/workers/rlm/config.py`

- [ ] Add `RLMError` base exception
- [ ] Add `BudgetExceededError`
- [ ] Add `RLMTimeoutError`
- [ ] Create `RLMConfig` dataclass
- [ ] Load from environment variables
- [ ] Document configuration options

**Estimate:** 30min

---

### T14: Integration tests for RLM

**File:** `tests/integration/test_rlm_exploration.py`

- [ ] Test exploration on this repository
- [ ] Test budget enforcement end-to-end
- [ ] Test timeout handling
- [ ] Test cache effectiveness
- [ ] Test audit trail generation
- [ ] Verify findings quality with labeled queries

**Estimate:** 2h

---

## Progress

- **Started**: (not started)
- **Tasks Complete**: 0/14
- **Percentage**: 0%
- **Status**: PENDING
- **Blockers**: Depends on P03-F01 and P03-F02 for models and parsers

## Task Summary

| Task | Description | Estimate | Status |
|------|-------------|----------|--------|
| T01 | RLM data models | 1h | [ ] |
| T02 | SubCallBudgetManager | 1h | [ ] |
| T03 | SubCallCache | 1h | [ ] |
| T04 | File operation tools | 1.5h | [ ] |
| T05 | Symbol operation tools | 1h | [ ] |
| T06 | LLM query tool | 1.5h | [ ] |
| T07 | REPLToolSurface registry | 30min | [ ] |
| T08 | RLMAgent | 2h | [ ] |
| T09 | RLMOrchestrator | 2h | [ ] |
| T10 | Audit trail generation | 1h | [ ] |
| T11 | Trigger detection | 1h | [ ] |
| T12 | AgentRunner integration | 1.5h | [ ] |
| T13 | Exceptions and configuration | 30min | [ ] |
| T14 | Integration tests | 2h | [ ] |

**Total Estimated Time**: 17 hours

## Completion Checklist

- [ ] All tasks in Task List are marked complete
- [ ] All unit tests pass: `./tools/test.sh tests/unit/`
- [ ] All integration tests pass: `./tools/test.sh tests/integration/`
- [ ] Budget enforcement verified
- [ ] Timeout handling verified
- [ ] Audit trails generated correctly
- [ ] Linter passes: `./tools/lint.sh src/`
- [ ] No type errors: `mypy src/`
- [ ] Documentation updated
- [ ] Progress marked as 100% in tasks.md

## Notes

### Dependency Order

P03-F03 depends on components from P03-F01 and P03-F02:
- P03-F01 T02: AgentResult, ToolCall models
- P03-F02 T02-T04: Python and TypeScript parsers

Can start T01-T03 immediately (models, budget, cache).
T04-T07 (tools) can proceed once parsers from P03-F02 are ready.
T08-T12 (orchestrator, agent, integration) after tools are complete.

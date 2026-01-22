# P03-F03: RLM Native Implementation - User Stories

## Overview

User stories for the RLM (Recursive LLM) native implementation that enables iterative exploration for long-context tasks.

## User Stories

### US-01: Basic RLM Exploration

**As** an agent facing a large codebase
**I want** to iteratively explore relevant files
**So that** I can find information beyond my context window

**Acceptance Criteria:**
- [ ] RLM orchestrator accepts exploration queries
- [ ] Agent iteratively explores using REPL tools
- [ ] Findings accumulated across iterations
- [ ] Final synthesis produced from findings

### US-02: Sub-Call Budget Enforcement

**As** the system
**I want** to enforce sub-call budgets
**So that** exploration costs are controlled

**Acceptance Criteria:**
- [ ] Total sub-call budget enforced (default 50)
- [ ] Per-iteration limit enforced (default 8)
- [ ] Budget exceeded triggers graceful stop
- [ ] Remaining budget visible to agent

### US-03: Wall Time Limit

**As** an operator
**I want** hard time limits on exploration
**So that** runaway explorations are stopped

**Acceptance Criteria:**
- [ ] Timeout enforced (default 300s)
- [ ] Timeout triggers graceful synthesis
- [ ] Partial results returned on timeout
- [ ] Timeout logged in audit trail

### US-04: File System Exploration

**As** an RLM agent
**I want** to list and read files
**So that** I can explore the codebase

**Acceptance Criteria:**
- [ ] list_files returns matching paths
- [ ] read_file returns content (full or range)
- [ ] grep searches across files
- [ ] Operations are read-only

### US-05: Symbol Extraction

**As** an RLM agent
**I want** to extract symbols from files
**So that** I can understand code structure

**Acceptance Criteria:**
- [ ] extract_symbols returns functions/classes
- [ ] parse_ast returns structured AST
- [ ] Supports Python and TypeScript
- [ ] Handles parse errors gracefully

### US-06: Sub-Model Queries

**As** an RLM agent
**I want** to make sub-queries with strict budgets
**So that** I can get focused answers

**Acceptance Criteria:**
- [ ] llm_query invokes Haiku model
- [ ] Token limit per sub-query enforced
- [ ] Sub-query counts against budget
- [ ] Response returned to main agent

### US-07: Sub-Call Caching

**As** the system
**I want** to cache identical sub-queries
**So that** repeated explorations are efficient

**Acceptance Criteria:**
- [ ] Cache key based on prompt + context hash
- [ ] Cached results reused within session
- [ ] Cache hits tracked in metrics
- [ ] Cache doesn't affect correctness

### US-08: Exploration Trajectory Recording

**As** an auditor
**I want** full exploration trajectories recorded
**So that** I can understand how conclusions were reached

**Acceptance Criteria:**
- [ ] Each iteration recorded with thought process
- [ ] Tool calls logged with inputs/outputs
- [ ] Findings progression tracked
- [ ] Trajectory saved to `telemetry/rlm/`

### US-09: Citation Generation

**As** a consumer of RLM results
**I want** citations to source files
**So that** I can verify findings

**Acceptance Criteria:**
- [ ] Citations include file path and line range
- [ ] Citations linked to specific findings
- [ ] Content hash verifies citation accuracy
- [ ] Citations in final result

### US-10: Integration with AgentRunner

**As** the worker pool
**I want** RLM to integrate with normal agent execution
**So that** agents can trigger RLM when needed

**Acceptance Criteria:**
- [ ] AgentRunner can invoke RLM mode
- [ ] Trigger conditions detected automatically
- [ ] RLM results formatted for agent consumption
- [ ] Seamless fallback to normal mode

### US-11: Debugger RLM Mode

**As** the Debugger agent
**I want** RLM mode when fail_count > 4
**So that** I can deeply investigate persistent failures

**Acceptance Criteria:**
- [ ] Debugger automatically triggers RLM
- [ ] Exploration focuses on failure patterns
- [ ] Test outputs and stack traces analyzed
- [ ] Root cause findings prioritized

### US-12: Security Restrictions

**As** the system
**I want** RLM tools to be restricted
**So that** exploration cannot cause harm

**Acceptance Criteria:**
- [ ] No network access from tools
- [ ] Filesystem is read-only
- [ ] No shell command execution
- [ ] Tool allowlist enforced

## Definition of Done

- [ ] RLM orchestrator functional
- [ ] All REPL tools implemented
- [ ] Budget enforcement working
- [ ] Caching operational
- [ ] Audit trails generated
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Security restrictions verified

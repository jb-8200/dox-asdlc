# P03-F01: Agent Worker Pool Framework - User Stories

## Overview

User stories for the stateless agent worker pool that executes domain agents with Claude Agent SDK.

## User Stories

### US-01: Worker Pool Startup

**As** the orchestrator
**I want** workers to start and connect to Redis streams
**So that** dispatched tasks are consumed and executed

**Acceptance Criteria:**
- [ ] Workers connect to Redis on startup
- [ ] Workers join the appropriate consumer group
- [ ] Health endpoint reports ready status
- [ ] Startup logged with worker ID and configuration

### US-02: Task Consumption

**As** the orchestrator
**I want** workers to consume AGENT_STARTED events
**So that** dispatched work is picked up for execution

**Acceptance Criteria:**
- [ ] Workers consume events from `asdlc:events` stream
- [ ] Event includes task_id, role, and context_pack_path
- [ ] Event acknowledged only after successful processing
- [ ] Duplicate events handled idempotently

### US-03: Role-Based Execution

**As** the system
**I want** workers to execute agents with role-specific configuration
**So that** each agent type has appropriate tools and prompts

**Acceptance Criteria:**
- [ ] System prompt loaded based on role
- [ ] Tool allowlist enforced per role
- [ ] Token limits respected per role
- [ ] Role configuration is declarative and auditable

### US-04: Context Pack Loading

**As** an agent
**I want** to receive a context pack with relevant code and symbols
**So that** I have the information needed for my task

**Acceptance Criteria:**
- [ ] Context pack loaded from path in event
- [ ] Files, symbols, and dependencies included
- [ ] Context pack validated before use
- [ ] Missing context pack results in graceful failure

### US-05: Tool Execution

**As** an agent
**I want** to call tools during execution
**So that** I can lint code, run tests, and perform analysis

**Acceptance Criteria:**
- [ ] Tools invoked via bash wrapper abstraction
- [ ] Tool output parsed as JSON
- [ ] Tool errors handled gracefully
- [ ] Tool call history recorded for audit

### US-06: Completion Events

**As** the orchestrator
**I want** to receive completion events when agents finish
**So that** I can update task state and apply artifacts

**Acceptance Criteria:**
- [ ] AGENT_COMPLETED published on success
- [ ] AGENT_FAILED published on failure
- [ ] Events include full result details
- [ ] Artifacts referenced in event

### US-07: Graceful Shutdown

**As** an operator
**I want** workers to shut down gracefully
**So that** in-progress work is completed before exit

**Acceptance Criteria:**
- [ ] SIGTERM triggers graceful shutdown
- [ ] In-progress tasks complete before exit
- [ ] Unprocessed events remain in stream
- [ ] Shutdown logged with completion status

### US-08: Horizontal Scaling

**As** an operator
**I want** to scale workers horizontally
**So that** throughput increases with load

**Acceptance Criteria:**
- [ ] Multiple workers share consumer group
- [ ] Work distributed across workers
- [ ] No duplicate processing across workers
- [ ] HPA metrics available (CPU, memory)

### US-09: Error Handling

**As** the system
**I want** agent execution errors to be handled properly
**So that** failures are reported and recoverable

**Acceptance Criteria:**
- [ ] API errors result in AGENT_FAILED event
- [ ] Timeout results in AGENT_FAILED event
- [ ] Error details included in failure event
- [ ] Retryable errors identified

### US-10: Observability

**As** an operator
**I want** to observe worker behavior
**So that** I can monitor and debug issues

**Acceptance Criteria:**
- [ ] Structured logging for all operations
- [ ] Token usage logged per execution
- [ ] Tool call metrics available
- [ ] Error rates trackable

## Definition of Done

- [ ] All unit tests pass
- [ ] Integration tests pass with mock Claude API
- [ ] Health endpoints functional
- [ ] Configuration documented
- [ ] Error handling comprehensive
- [ ] Logging structured and complete

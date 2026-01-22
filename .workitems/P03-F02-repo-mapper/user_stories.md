# P03-F02: Repo Mapper - Context Pack Generation - User Stories

## Overview

User stories for the Repo Mapper that generates deterministic context packs for agent execution.

## User Stories

### US-01: Context Pack Generation

**As** the orchestrator
**I want** to generate a context pack for a task
**So that** agents receive relevant code context

**Acceptance Criteria:**
- [ ] Context pack includes target files
- [ ] Context pack includes relevant dependencies
- [ ] Token count respects budget
- [ ] Pack saved to `context/packs/<task_id>.json`

### US-02: Python AST Parsing

**As** the Repo Mapper
**I want** to parse Python files and extract symbols
**So that** I can build a dependency graph

**Acceptance Criteria:**
- [ ] Functions extracted with signatures
- [ ] Classes extracted with methods
- [ ] Imports parsed (absolute and relative)
- [ ] Type hints included in signatures
- [ ] Docstrings captured

### US-03: TypeScript AST Parsing

**As** the Repo Mapper
**I want** to parse TypeScript files and extract symbols
**So that** I can support frontend code analysis

**Acceptance Criteria:**
- [ ] Functions and arrow functions extracted
- [ ] Classes and interfaces extracted
- [ ] Import/export statements parsed
- [ ] Type annotations captured
- [ ] JSX components identified

### US-04: Dependency Graph Construction

**As** the Repo Mapper
**I want** to build a dependency graph from parsed files
**So that** I can trace relationships between symbols

**Acceptance Criteria:**
- [ ] Import relationships tracked
- [ ] Function call relationships tracked (where determinable)
- [ ] Bidirectional queries supported (deps and dependents)
- [ ] Depth-limited traversal available

### US-05: Relevance-Based Selection

**As** the Repo Mapper
**I want** to select content based on relevance scores
**So that** the most important context is prioritized

**Acceptance Criteria:**
- [ ] Target files scored highest
- [ ] Direct dependencies scored above indirect
- [ ] Interface definitions prioritized
- [ ] Content truncated by relevance when over budget

### US-06: Token Budget Management

**As** the orchestrator
**I want** context packs to respect token budgets
**So that** agents don't exceed context limits

**Acceptance Criteria:**
- [ ] Token count estimated accurately
- [ ] Budget enforced during generation
- [ ] High-relevance content preserved
- [ ] Truncation applied to low-relevance content

### US-07: AST Context Caching

**As** the system
**I want** to cache AST analysis results
**So that** repeated context generation is fast

**Acceptance Criteria:**
- [ ] AST context cached to `context/ast_context.json`
- [ ] Cache invalidated on Git SHA change
- [ ] Cache refresh on demand
- [ ] TTL-based expiration supported

### US-08: Role-Specific Context

**As** an agent
**I want** context tailored to my role
**So that** I receive what's relevant for my task type

**Acceptance Criteria:**
- [ ] Coding role gets implementation details
- [ ] Reviewer role gets full diffs and history
- [ ] Test role gets test fixtures and mocks
- [ ] Debugger role gets stack traces and logs

### US-09: Context Pack Validation

**As** the orchestrator
**I want** context packs to be validated
**So that** malformed packs are caught early

**Acceptance Criteria:**
- [ ] JSON schema validation
- [ ] Required fields verified
- [ ] File references validated
- [ ] Token count verified

### US-10: Incremental Updates

**As** the system
**I want** to update context packs incrementally
**So that** small changes don't require full regeneration

**Acceptance Criteria:**
- [ ] Changed files trigger targeted updates
- [ ] Dependency graph updates incrementally
- [ ] Cache partially invalidated on changes

## Definition of Done

- [ ] Python parser fully functional
- [ ] TypeScript parser fully functional
- [ ] Dependency graph construction working
- [ ] Context packs generated correctly
- [ ] Token budgets respected
- [ ] All unit tests pass
- [ ] Integration tests pass

# P11-F01: Guardrails Configuration System - Tasks

## Overview

This task breakdown covers implementing the Contextually-Conditional Guardrails System. Tasks are organized into 6 phases matching the feature's technical architecture.

## Dependencies

### External Dependencies

- P01-F03: KnowledgeStore interface - COMPLETE
- P02-F04: Elasticsearch backend - COMPLETE
- P05-F01: HITL UI infrastructure - COMPLETE

### Phase Dependencies

```
Phase 1 (ES & Models) ──────┐
                            ├──► Phase 3 (MCP) ──► Phase 6 (Agent Integration)
Phase 2 (Evaluator) ────────┘
                            │
                            └──► Phase 4 (REST API)
                                      │
Phase 5 (UI) ◄────────────────────────┘
```

---

## Phase 1: Elasticsearch Indices and Models (Backend)

### T01: Create Guideline Data Models

**Model**: haiku
**Estimate**: 1.5hr
**Stories**: US-F01-01

**Description**: Define core data models for guidelines, conditions, and actions.

**Subtasks**:
- [ ] Create `src/core/guardrails/__init__.py`
- [ ] Create `src/core/guardrails/models.py` with Guideline, GuidelineCondition, GuidelineAction
- [ ] Create TaskContext dataclass
- [ ] Create GuidelineCategory and ActionType enums
- [ ] Add to_dict() and from_dict() methods
- [ ] Write unit tests for models

**Acceptance Criteria**:
- [ ] All dataclasses are frozen (immutable)
- [ ] Enums cover all required categories and action types
- [ ] JSON serialization round-trips correctly
- [ ] Unit tests verify field validation

**Test Cases**:
- [ ] Test Guideline creation with all fields
- [ ] Test Guideline creation with minimal fields
- [ ] Test GuidelineCondition with various field combinations
- [ ] Test GuidelineAction with different action types
- [ ] Test JSON serialization and deserialization
- [ ] Test enum values

---

### T02: Create Guardrails Exceptions

**Model**: haiku
**Estimate**: 30min
**Stories**: US-F01-01

**Description**: Add guardrails-specific exceptions to the exception hierarchy.

**Subtasks**:
- [ ] Create `src/core/guardrails/exceptions.py`
- [ ] Add GuardrailsError base exception
- [ ] Add GuidelineNotFoundError
- [ ] Add GuidelineValidationError
- [ ] Add GuidelineConflictError (version mismatch)
- [ ] Write unit tests

**Acceptance Criteria**:
- [ ] Exceptions inherit from ASDLCError
- [ ] Exceptions include message and details fields
- [ ] Support to_dict() serialization

**Test Cases**:
- [ ] Test exception instantiation
- [ ] Test exception inheritance chain
- [ ] Test to_dict() output

---

### T03: Create Elasticsearch Index Mappings

**Model**: haiku
**Estimate**: 1hr
**Stories**: US-F01-02

**Description**: Define Elasticsearch index mappings for guardrails-config and guardrails-audit.

**Subtasks**:
- [ ] Create `src/infrastructure/knowledge_store/guardrails_mappings.py`
- [ ] Define GUARDRAILS_CONFIG_MAPPING with all fields
- [ ] Define GUARDRAILS_AUDIT_MAPPING with all fields
- [ ] Add tenant_id field for multi-tenancy
- [ ] Add index settings (shards, replicas)
- [ ] Write unit tests for mapping structure

**Acceptance Criteria**:
- [ ] Mappings support all model fields
- [ ] Keyword fields used for exact matching
- [ ] Text fields used where full-text search needed
- [ ] Object fields with dynamic: false where appropriate

**Test Cases**:
- [ ] Test mapping structure is valid JSON
- [ ] Test all required fields present
- [ ] Test field types are correct

---

### T04: Implement GuardrailsStore Class

**Model**: sonnet
**Estimate**: 2hr
**Stories**: US-F01-02

**Description**: Create Elasticsearch store class for guardrails CRUD operations.

**Subtasks**:
- [ ] Create `src/infrastructure/knowledge_store/guardrails_store.py`
- [ ] Implement __init__ with ES client
- [ ] Implement _ensure_indices_exist()
- [ ] Implement create_guideline()
- [ ] Implement get_guideline()
- [ ] Implement update_guideline() with version check
- [ ] Implement delete_guideline()
- [ ] Implement list_guidelines() with filtering
- [ ] Implement log_audit_entry()
- [ ] Implement list_audit_entries() with filtering
- [ ] Write unit tests with mocked ES client

**Acceptance Criteria**:
- [ ] All CRUD operations work correctly
- [ ] Index creation is idempotent
- [ ] Version conflicts raise GuidelineConflictError
- [ ] Multi-tenancy supported via index prefix
- [ ] Audit logging is append-only

**Test Cases**:
- [ ] Test create and get guideline
- [ ] Test update with correct version
- [ ] Test update with version conflict
- [ ] Test delete existing guideline
- [ ] Test delete non-existent guideline
- [ ] Test list with category filter
- [ ] Test list with enabled filter
- [ ] Test list with pagination
- [ ] Test log and list audit entries

---

## Phase 2: GuardrailsEvaluator Class (Backend)

### T05: Implement Basic Evaluator Structure

**Model**: haiku
**Estimate**: 1hr
**Stories**: US-F01-03

**Description**: Create the GuardrailsEvaluator class skeleton with dependency injection.

**Subtasks**:
- [ ] Create `src/core/guardrails/evaluator.py`
- [ ] Implement __init__ with GuardrailsStore
- [ ] Implement get_context() signature
- [ ] Implement log_decision() signature
- [ ] Create EvaluatedGuideline result dataclass
- [ ] Create GateDecision dataclass
- [ ] Write basic structure tests

**Acceptance Criteria**:
- [ ] Class accepts GuardrailsStore via constructor
- [ ] Public methods have correct signatures
- [ ] Result types are well-defined

**Test Cases**:
- [ ] Test evaluator initialization
- [ ] Test result dataclass creation

---

### T06: Implement Condition Matching Logic

**Model**: sonnet
**Estimate**: 1.5hr
**Stories**: US-F01-03

**Description**: Implement the condition matching algorithm.

**Subtasks**:
- [ ] Implement _condition_matches() method
- [ ] Implement agent matching (list OR logic)
- [ ] Implement domain matching (list OR logic)
- [ ] Implement action matching (list OR logic)
- [ ] Implement path matching with glob patterns
- [ ] Implement event matching
- [ ] Implement gate_type matching
- [ ] Handle None/empty as wildcards
- [ ] Write comprehensive unit tests

**Acceptance Criteria**:
- [ ] All specified fields must match (AND logic)
- [ ] Lists within fields use OR logic
- [ ] Empty fields always match
- [ ] Glob patterns work correctly
- [ ] Edge cases handled

**Test Cases**:
- [ ] Test single agent match
- [ ] Test multiple agents (OR logic)
- [ ] Test agent mismatch
- [ ] Test domain matching
- [ ] Test action matching
- [ ] Test path glob pattern match
- [ ] Test path glob pattern mismatch
- [ ] Test multiple conditions AND logic
- [ ] Test empty condition matches all
- [ ] Test partial condition match

---

### T07: Implement Priority and Conflict Resolution

**Model**: sonnet
**Estimate**: 1.5hr
**Stories**: US-F01-04

**Description**: Implement priority sorting and conflict resolution.

**Subtasks**:
- [ ] Implement _resolve_conflicts() method
- [ ] Sort matching guidelines by priority (highest first)
- [ ] Merge tool_allowed lists (union)
- [ ] Merge tool_denied lists (union)
- [ ] Deny lists override allow lists
- [ ] Merge HITL gates (all required)
- [ ] Concatenate instructions in priority order
- [ ] Write unit tests for conflict scenarios

**Acceptance Criteria**:
- [ ] Higher priority guidelines listed first
- [ ] Tool restrictions properly merged
- [ ] Deny always wins over allow
- [ ] Instructions ordered by priority
- [ ] Resolution is deterministic

**Test Cases**:
- [ ] Test priority sorting
- [ ] Test tool_allowed merge
- [ ] Test tool_denied merge
- [ ] Test deny overrides allow
- [ ] Test instruction concatenation
- [ ] Test HITL gate combination
- [ ] Test same priority handling

---

### T08: Implement Full Evaluation Flow

**Model**: sonnet
**Estimate**: 1hr
**Stories**: US-F01-03, US-F01-05

**Description**: Complete the get_context() and log_decision() implementations.

**Subtasks**:
- [ ] Implement full get_context() flow
- [ ] Fetch enabled guidelines from store
- [ ] Evaluate all conditions
- [ ] Build EvaluatedGuideline results
- [ ] Apply conflict resolution
- [ ] Implement log_decision() with audit logging
- [ ] Add caching for enabled guidelines
- [ ] Write integration tests

**Acceptance Criteria**:
- [ ] Full evaluation flow works end-to-end
- [ ] Caching reduces ES queries
- [ ] Audit logging captures all decisions
- [ ] Integration tests pass

**Test Cases**:
- [ ] Test full evaluation with multiple guidelines
- [ ] Test evaluation with no matches
- [ ] Test evaluation with all matches
- [ ] Test decision logging
- [ ] Test cache invalidation

---

## Phase 3: Knowledge-store MCP Extension (Backend)

### T09: Add guardrails_get_context Tool

**Model**: sonnet
**Estimate**: 1.5hr
**Stories**: US-F01-06

**Description**: Add the guardrails_get_context tool to the MCP server.

**Subtasks**:
- [ ] Add GuardrailsEvaluator to MCP server __init__
- [ ] Implement guardrails_get_context() method
- [ ] Build TaskContext from parameters
- [ ] Call evaluator.get_context()
- [ ] Format response with guidelines and aggregates
- [ ] Add tool schema to get_tool_schemas()
- [ ] Update handle_request() routing
- [ ] Write unit tests

**Acceptance Criteria**:
- [ ] Tool accepts all context parameters
- [ ] Response includes matching guidelines
- [ ] Response includes combined instruction
- [ ] Response includes aggregated tool lists
- [ ] Tool schema is valid MCP format

**Test Cases**:
- [ ] Test tool invocation with full context
- [ ] Test tool with minimal context
- [ ] Test response structure
- [ ] Test with no matching guidelines
- [ ] Test error handling

---

### T10: Add guardrails_log_decision Tool

**Model**: haiku
**Estimate**: 1hr
**Stories**: US-F01-07

**Description**: Add the guardrails_log_decision tool to the MCP server.

**Subtasks**:
- [ ] Implement guardrails_log_decision() method
- [ ] Parse guideline_id and context
- [ ] Build GateDecision from parameters
- [ ] Call evaluator.log_decision()
- [ ] Return audit entry ID
- [ ] Add tool schema
- [ ] Update handle_request()
- [ ] Write unit tests

**Acceptance Criteria**:
- [ ] Tool accepts required parameters
- [ ] Decision logged to audit index
- [ ] Returns audit entry ID
- [ ] Error handling for invalid guideline

**Test Cases**:
- [ ] Test logging approved decision
- [ ] Test logging rejected decision
- [ ] Test logging with user response
- [ ] Test invalid guideline_id

---

### T11: Update MCP Server Configuration

**Model**: haiku
**Estimate**: 30min
**Stories**: US-F01-06, US-F01-07

**Description**: Update MCP server config and initialization for guardrails.

**Subtasks**:
- [ ] Add guardrails config to KnowledgeStoreConfig
- [ ] Update config.py with guardrails_enabled flag
- [ ] Update factory.py to create GuardrailsEvaluator
- [ ] Add lazy initialization in MCP server
- [ ] Update environment variable documentation

**Acceptance Criteria**:
- [ ] Guardrails can be disabled via config
- [ ] Lazy initialization prevents startup overhead
- [ ] Documentation reflects new config options

**Test Cases**:
- [ ] Test config loading
- [ ] Test disabled guardrails skips initialization

---

### T12: Write MCP Integration Tests

**Model**: sonnet
**Estimate**: 1hr
**Stories**: US-F01-06, US-F01-07

**Description**: Create integration tests for guardrails MCP tools.

**Subtasks**:
- [ ] Create test fixtures with sample guidelines
- [ ] Test guardrails_get_context via MCP protocol
- [ ] Test guardrails_log_decision via MCP protocol
- [ ] Test tool discovery via tools/list
- [ ] Test error handling
- [ ] Verify audit log entries created

**Acceptance Criteria**:
- [ ] Integration tests run against real ES
- [ ] Tests clean up after themselves
- [ ] All tools work via MCP protocol

**Test Cases**:
- [ ] Test full MCP flow for get_context
- [ ] Test full MCP flow for log_decision
- [ ] Test tool list includes guardrails tools

---

## Phase 4: Orchestrator REST API (Backend)

### T13: Create Pydantic Models for API

**Model**: haiku
**Estimate**: 1hr
**Stories**: US-F01-08, US-F01-09

**Description**: Create Pydantic models for REST API request/response.

**Subtasks**:
- [ ] Create `src/orchestrator/models/guardrails.py`
- [ ] Define GuidelineCreate model
- [ ] Define GuidelineUpdate model
- [ ] Define GuidelineResponse model
- [ ] Define GuidelinesListResponse model
- [ ] Define AuditLogEntry model
- [ ] Define TaskContextRequest model
- [ ] Define EvaluatedContextResponse model
- [ ] Write unit tests for validation

**Acceptance Criteria**:
- [ ] Models have proper field validation
- [ ] Required vs optional fields correct
- [ ] Enum validation for categories
- [ ] Priority range validation (0-1000)

**Test Cases**:
- [ ] Test valid model creation
- [ ] Test validation errors
- [ ] Test priority out of range
- [ ] Test invalid category

---

### T14: Implement List and Get Endpoints

**Model**: haiku
**Estimate**: 1.5hr
**Stories**: US-F01-08

**Description**: Implement REST endpoints for listing and getting guidelines.

**Subtasks**:
- [ ] Create `src/orchestrator/routes/guardrails_api.py`
- [ ] Implement GET /api/guardrails with filtering
- [ ] Implement GET /api/guardrails/{id}
- [ ] Add pagination parameters
- [ ] Add category and enabled filters
- [ ] Register router in main app
- [ ] Write unit tests

**Acceptance Criteria**:
- [ ] List endpoint returns paginated results
- [ ] Filtering by category works
- [ ] Filtering by enabled works
- [ ] Get endpoint returns 404 for missing
- [ ] Response matches schema

**Test Cases**:
- [ ] Test list all guidelines
- [ ] Test list with category filter
- [ ] Test list with enabled filter
- [ ] Test list with pagination
- [ ] Test get existing guideline
- [ ] Test get non-existent guideline

---

### T15: Implement Create, Update, Delete Endpoints

**Model**: sonnet
**Estimate**: 1.5hr
**Stories**: US-F01-09

**Description**: Implement REST endpoints for guideline management.

**Subtasks**:
- [ ] Implement POST /api/guardrails
- [ ] Implement PUT /api/guardrails/{id}
- [ ] Implement DELETE /api/guardrails/{id}
- [ ] Implement POST /api/guardrails/{id}/toggle
- [ ] Add version check for updates
- [ ] Add validation error responses
- [ ] Write unit tests

**Acceptance Criteria**:
- [ ] Create returns 201 with new guideline
- [ ] Update returns 200 with updated guideline
- [ ] Update returns 409 on version conflict
- [ ] Delete returns 204 on success
- [ ] Delete returns 404 if not found
- [ ] Toggle flips enabled status

**Test Cases**:
- [ ] Test create valid guideline
- [ ] Test create with validation error
- [ ] Test update with correct version
- [ ] Test update with wrong version
- [ ] Test delete existing
- [ ] Test delete non-existent
- [ ] Test toggle enabled to disabled
- [ ] Test toggle disabled to enabled

---

### T16: Implement Audit and Evaluate Endpoints

**Model**: haiku
**Estimate**: 1.5hr
**Stories**: US-F01-10, US-F01-11, US-F01-12

**Description**: Implement endpoints for audit logs, evaluation, and import/export.

**Subtasks**:
- [ ] Implement GET /api/guardrails/audit
- [ ] Add filtering by guideline_id, event_type, dates
- [ ] Implement POST /api/guardrails/evaluate
- [ ] Implement GET /api/guardrails/export
- [ ] Implement POST /api/guardrails/import
- [ ] Write unit tests

**Acceptance Criteria**:
- [ ] Audit endpoint returns filtered entries
- [ ] Evaluate endpoint returns matching guidelines
- [ ] Export returns all guidelines as JSON array
- [ ] Import bulk creates guidelines

**Test Cases**:
- [ ] Test audit list with filters
- [ ] Test evaluate with context
- [ ] Test export all
- [ ] Test export with category filter
- [ ] Test import new guidelines
- [ ] Test import with duplicates

---

## Phase 5: HITL UI Components (Frontend)

### T17: Create TypeScript Types and API Client

**Model**: haiku
**Estimate**: 1.5hr
**Stories**: US-F01-21

**Description**: Create TypeScript types and API client functions.

**Subtasks**:
- [ ] Add guardrails types to `src/api/types.ts`
- [ ] Create `src/api/guardrails.ts`
- [ ] Implement listGuidelines() function
- [ ] Implement getGuideline() function
- [ ] Implement createGuideline() function
- [ ] Implement updateGuideline() function
- [ ] Implement deleteGuideline() function
- [ ] Implement toggleGuideline() function
- [ ] Implement listAuditLogs() function
- [ ] Implement evaluateContext() function
- [ ] Implement exportGuidelines() and importGuidelines()
- [ ] Create React Query hooks
- [ ] Write unit tests

**Acceptance Criteria**:
- [ ] Types match backend models
- [ ] All API functions implemented
- [ ] React Query hooks with proper keys
- [ ] Error handling for API failures

**Test Cases**:
- [ ] Test API function calls
- [ ] Test error handling
- [ ] Test React Query hooks

---

### T18: Create Mock Data and Service

**Model**: haiku
**Estimate**: 1hr
**Stories**: US-F01-25

**Description**: Create mock data and mock service for development.

**Subtasks**:
- [ ] Create `src/api/mocks/guardrails.ts`
- [ ] Define mock guidelines covering all categories
- [ ] Define mock audit log entries
- [ ] Implement mock service with delay
- [ ] Toggle via VITE_USE_MOCKS env var
- [ ] Write unit tests

**Acceptance Criteria**:
- [ ] Mock data is realistic
- [ ] Covers all guideline categories
- [ ] Mock service simulates latency
- [ ] Environment toggle works

**Test Cases**:
- [ ] Test mock data structure
- [ ] Test mock service responses

---

### T19: Create Guardrails Store

**Model**: haiku
**Estimate**: 1hr
**Stories**: US-F01-22

**Description**: Create Zustand store for guardrails state management.

**Subtasks**:
- [ ] Create `src/stores/guardrailsStore.ts`
- [ ] Define state interface
- [ ] Implement setGuidelines action
- [ ] Implement selectGuideline action
- [ ] Implement filter actions
- [ ] Implement editor state actions
- [ ] Implement audit state actions
- [ ] Add localStorage persistence for filters
- [ ] Write unit tests

**Acceptance Criteria**:
- [ ] Store holds all required state
- [ ] Actions update state correctly
- [ ] Filter preferences persisted
- [ ] Tests verify state transitions

**Test Cases**:
- [ ] Test setGuidelines
- [ ] Test selectGuideline
- [ ] Test filter changes
- [ ] Test editor open/close
- [ ] Test persistence

---

### T20: Build GuidelineCard Component

**Model**: haiku
**Estimate**: 1hr
**Stories**: US-F01-14

**Description**: Create the GuidelineCard component for list display.

**Subtasks**:
- [ ] Create `src/components/guardrails/GuidelineCard.tsx`
- [ ] Display name, category badge, priority
- [ ] Show condition summary (agents, domains)
- [ ] Show action type indicator
- [ ] Add toggle button for enabled
- [ ] Style disabled guidelines
- [ ] Add click handler for selection
- [ ] Write unit tests

**Acceptance Criteria**:
- [ ] Card displays all summary info
- [ ] Category badge has appropriate color
- [ ] Toggle works
- [ ] Click selects card
- [ ] Disabled style is distinct

**Test Cases**:
- [ ] Test card rendering
- [ ] Test toggle callback
- [ ] Test click callback
- [ ] Test disabled styling

---

### T21: Build GuidelinesList Component

**Model**: haiku
**Estimate**: 1.5hr
**Stories**: US-F01-13

**Description**: Create the GuidelinesList component.

**Subtasks**:
- [ ] Create `src/components/guardrails/GuidelinesList.tsx`
- [ ] Render list of GuidelineCard components
- [ ] Add search input for filtering
- [ ] Add category dropdown filter
- [ ] Add enabled dropdown filter
- [ ] Add sort controls (priority, name)
- [ ] Show loading skeleton
- [ ] Show empty state
- [ ] Write unit tests

**Acceptance Criteria**:
- [ ] List renders all guidelines
- [ ] Search filters by name/description
- [ ] Category filter works
- [ ] Enabled filter works
- [ ] Sort changes order
- [ ] Loading state shown

**Test Cases**:
- [ ] Test list rendering
- [ ] Test search filtering
- [ ] Test category filtering
- [ ] Test sort order
- [ ] Test loading state
- [ ] Test empty state

---

### T22: Build ConditionBuilder Component

**Model**: sonnet
**Estimate**: 1.5hr
**Stories**: US-F01-16

**Description**: Create visual condition builder component.

**Subtasks**:
- [ ] Create `src/components/guardrails/ConditionBuilder.tsx`
- [ ] Add agent multi-select (checkboxes)
- [ ] Add domain input (tag style)
- [ ] Add action multi-select
- [ ] Add path pattern input
- [ ] Add event type selection
- [ ] Add gate type selection
- [ ] Add JSON editor for custom (advanced)
- [ ] Write unit tests

**Acceptance Criteria**:
- [ ] All condition fields editable
- [ ] Multi-select works correctly
- [ ] Path pattern shows validation
- [ ] Custom JSON editor available
- [ ] Changes emit onChange

**Test Cases**:
- [ ] Test agent selection
- [ ] Test domain input
- [ ] Test path pattern validation
- [ ] Test custom JSON editing
- [ ] Test onChange callback

---

### T23: Build ActionBuilder Component

**Model**: sonnet
**Estimate**: 1.5hr
**Stories**: US-F01-17

**Description**: Create visual action builder component.

**Subtasks**:
- [ ] Create `src/components/guardrails/ActionBuilder.tsx`
- [ ] Add action type dropdown
- [ ] Add instruction textarea (for instruction type)
- [ ] Add tools allowed/denied inputs (for tool_restriction)
- [ ] Add gate type and threshold (for hitl_gate)
- [ ] Add constraint fields (for constraint type)
- [ ] Show/hide fields based on type
- [ ] Write unit tests

**Acceptance Criteria**:
- [ ] Action type changes visible fields
- [ ] All fields editable
- [ ] Validation for required fields
- [ ] Changes emit onChange

**Test Cases**:
- [ ] Test type selection shows correct fields
- [ ] Test instruction editing
- [ ] Test tool list editing
- [ ] Test gate settings
- [ ] Test onChange callback

---

### T24: Build GuidelineEditor Component

**Model**: sonnet
**Estimate**: 2hr
**Stories**: US-F01-15

**Description**: Create the main guideline editor form.

**Subtasks**:
- [ ] Create `src/components/guardrails/GuidelineEditor.tsx`
- [ ] Add name input with validation
- [ ] Add description textarea
- [ ] Add category dropdown
- [ ] Add priority slider with number input
- [ ] Integrate ConditionBuilder
- [ ] Integrate ActionBuilder
- [ ] Add metadata JSON editor (advanced)
- [ ] Add Save and Cancel buttons
- [ ] Handle version conflicts
- [ ] Show loading state during save
- [ ] Write unit tests

**Acceptance Criteria**:
- [ ] All fields editable
- [ ] Validation errors shown inline
- [ ] Save disabled if invalid
- [ ] Cancel restores original state
- [ ] Version conflict shows error

**Test Cases**:
- [ ] Test new guideline creation
- [ ] Test existing guideline editing
- [ ] Test validation errors
- [ ] Test save callback
- [ ] Test cancel callback
- [ ] Test version conflict

---

### T25: Build AuditLogViewer Component

**Model**: haiku
**Estimate**: 1.5hr
**Stories**: US-F01-19

**Description**: Create the audit log viewer component.

**Subtasks**:
- [ ] Create `src/components/guardrails/AuditLogViewer.tsx`
- [ ] Display audit entries in table
- [ ] Add expandable row for details
- [ ] Add guideline filter
- [ ] Add event type filter
- [ ] Add date range filter
- [ ] Add pagination
- [ ] Add export to CSV button
- [ ] Write unit tests

**Acceptance Criteria**:
- [ ] Table shows all audit fields
- [ ] Rows expandable for details
- [ ] Filters work correctly
- [ ] Pagination works
- [ ] CSV export works

**Test Cases**:
- [ ] Test table rendering
- [ ] Test row expansion
- [ ] Test filtering
- [ ] Test pagination
- [ ] Test CSV export

---

### T26: Build GuardrailsPage and Navigation

**Model**: sonnet
**Estimate**: 1.5hr
**Stories**: US-F01-23, US-F01-24

**Description**: Create the main page and add to navigation.

**Subtasks**:
- [ ] Create `src/components/guardrails/GuardrailsPage.tsx`
- [ ] Add header with title and import/export
- [ ] Layout with filters, list, and editor panels
- [ ] Integrate GuidelinesList
- [ ] Integrate GuidelineEditor
- [ ] Add collapsible AuditLogViewer
- [ ] Create `src/pages/GuardrailsPage.tsx` route wrapper
- [ ] Add route to App.tsx
- [ ] Add navigation item to sidebar
- [ ] Write unit tests

**Acceptance Criteria**:
- [ ] Page accessible via /guardrails
- [ ] Navigation item visible in sidebar
- [ ] Three-column layout works
- [ ] Audit log collapsible
- [ ] Responsive layout

**Test Cases**:
- [ ] Test page rendering
- [ ] Test navigation
- [ ] Test layout responsiveness
- [ ] Test audit toggle

---

### T27: Build GuidelinePreview Component

**Model**: haiku
**Estimate**: 1hr
**Stories**: US-F01-18

**Description**: Create component to preview guideline evaluation.

**Subtasks**:
- [ ] Create `src/components/guardrails/GuidelinePreview.tsx`
- [ ] Add context input fields
- [ ] Add Evaluate button
- [ ] Show match/no-match result
- [ ] Show which conditions matched
- [ ] Show effective instruction preview
- [ ] Wire to evaluateContext API
- [ ] Write unit tests

**Acceptance Criteria**:
- [ ] Context inputs work
- [ ] Evaluate calls API
- [ ] Results displayed clearly
- [ ] Matched conditions highlighted

**Test Cases**:
- [ ] Test context input
- [ ] Test evaluate call
- [ ] Test result display

---

### T28: Build ImportExportPanel Component

**Model**: haiku
**Estimate**: 1hr
**Stories**: US-F01-20

**Description**: Create import/export controls.

**Subtasks**:
- [ ] Create `src/components/guardrails/ImportExportPanel.tsx`
- [ ] Add Export button that downloads JSON
- [ ] Add Import button with file picker
- [ ] Show preview of imported guidelines
- [ ] Handle duplicates (option to skip/overwrite)
- [ ] Show progress during import
- [ ] Write unit tests

**Acceptance Criteria**:
- [ ] Export downloads file
- [ ] Import accepts JSON file
- [ ] Preview shown before import
- [ ] Duplicate handling works

**Test Cases**:
- [ ] Test export download
- [ ] Test import file handling
- [ ] Test preview display
- [ ] Test duplicate handling

---

## Phase 6: Agent Integration and Finalization (Backend/Orchestrator)

### T29: Create Bootstrap Script for Default Guidelines

**Model**: sonnet
**Estimate**: 1.5hr
**Stories**: US-F01-26

**Description**: Create script to bootstrap default guidelines from rules.

**Subtasks**:
- [ ] Create `scripts/bootstrap_guardrails.py`
- [ ] Parse existing .claude/rules/*.md files
- [ ] Convert to Guideline objects
- [ ] Create cognitive isolation guidelines per agent
- [ ] Create HITL gate guidelines
- [ ] Create TDD protocol guidelines
- [ ] Implement upsert logic (skip existing)
- [ ] Add CLI interface
- [ ] Write unit tests

**Acceptance Criteria**:
- [ ] Script reads all rules files
- [ ] Converts to valid guidelines
- [ ] Upserts without duplicates
- [ ] Can be run repeatedly safely

**Test Cases**:
- [ ] Test rule file parsing
- [ ] Test guideline conversion
- [ ] Test upsert behavior
- [ ] Test CLI execution

---

### T30: Update Agent Definitions to Use Guardrails

**Model**: haiku
**Estimate**: 1hr
**Stories**: US-F01-27

**Description**: Update agent definitions to call guardrails_get_context.

**Subtasks**:
- [ ] Update .claude/agents/*.md to reference guardrails
- [ ] Add guardrails_get_context call pattern
- [ ] Document context parameters to pass
- [ ] Update agent prompt templates
- [ ] Test with sample agent invocation

**Acceptance Criteria**:
- [ ] Agent definitions reference guardrails
- [ ] Documentation shows usage pattern
- [ ] Agents can invoke tool successfully

**Test Cases**:
- [ ] Test agent with guardrails context
- [ ] Verify correct context passed

---

### T31: Write End-to-End Integration Tests

**Model**: sonnet
**Estimate**: 1.5hr
**Stories**: US-F01-03, US-F01-06, US-F01-27

**Description**: Create comprehensive e2e tests for guardrails system.

**Subtasks**:
- [ ] Create test fixtures with realistic guidelines
- [ ] Test full flow: create guideline -> evaluate -> log decision
- [ ] Test REST API with real ES
- [ ] Test MCP tools with real ES
- [ ] Test UI components with real API (E2E)
- [ ] Verify audit trail

**Acceptance Criteria**:
- [ ] E2E tests pass against real services
- [ ] Full flow tested end-to-end
- [ ] Audit trail verified

**Test Cases**:
- [ ] Test create guideline via API
- [ ] Test evaluate via MCP
- [ ] Test decision logging
- [ ] Test audit log retrieval

---

### T32: Create Documentation

**Model**: haiku
**Estimate**: 1hr
**Stories**: US-F01-28

**Description**: Create documentation for the guardrails system.

**Subtasks**:
- [ ] Create docs/guardrails/README.md overview
- [ ] Document guideline schema reference
- [ ] Add examples for common patterns
- [ ] Create UI user guide
- [ ] Update CLAUDE.md with guardrails section
- [ ] Add API reference

**Acceptance Criteria**:
- [ ] Documentation is comprehensive
- [ ] Examples are accurate
- [ ] Schema reference complete

**Test Cases**:
- [ ] Verify examples work
- [ ] Check links valid

---

## Progress

- **Started**: Not started
- **Tasks Complete**: 0/32
- **Percentage**: 0%
- **Status**: PLANNED
- **Blockers**: None

## Task Summary

| Phase | Tasks | Estimate | Status |
|-------|-------|----------|--------|
| Phase 1: ES & Models | T01-T04 | 5hr | [ ] |
| Phase 2: Evaluator | T05-T08 | 5hr | [ ] |
| Phase 3: MCP | T09-T12 | 4hr | [ ] |
| Phase 4: REST API | T13-T16 | 5.5hr | [ ] |
| Phase 5: UI | T17-T28 | 16hr | [ ] |
| Phase 6: Integration | T29-T32 | 5hr | [ ] |

**Total Estimated Time**: 40.5 hours

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

## Notes

### Task Dependencies

```
T01 ────┐
        ├──► T03 ──► T04 ──► T05 ──► T06 ──► T07 ──► T08
T02 ────┘                                         │
                                                  │
                    ┌─────────────────────────────┘
                    │
                    ├──► T09 ──► T10 ──► T11 ──► T12
                    │
                    └──► T13 ──► T14 ──► T15 ──► T16
                                                  │
                    ┌─────────────────────────────┘
                    │
T18 ──► T17 ──► T19 ──► T20 ──► T21 ──► T22 ──► T23 ──► T24
                    │
                    ├──► T25 ──► T26 ──► T27 ──► T28
                    │
                    └──► T29 ──► T30 ──► T31 ──► T32
```

### Implementation Order

**Week 1: Backend Foundation**
1. T01, T02 (Models, Exceptions) - parallel
2. T03, T04 (ES Indices, Store)
3. T05, T06 (Evaluator structure, Condition matching)
4. T07, T08 (Conflict resolution, Full evaluation)

**Week 2: Backend APIs**
5. T09, T10, T11 (MCP tools)
6. T12 (MCP integration tests)
7. T13, T14 (REST models, List/Get)
8. T15, T16 (REST CRUD, Audit)

**Week 3: Frontend Core**
9. T17, T18 (Types, Mock data)
10. T19 (Store)
11. T20, T21 (Card, List)
12. T22, T23 (Condition, Action builders)

**Week 4: Frontend Complete + Integration**
13. T24, T25 (Editor, Audit viewer)
14. T26, T27, T28 (Page, Preview, Import/Export)
15. T29, T30 (Bootstrap, Agent integration)
16. T31, T32 (E2E tests, Documentation)

### Testing Strategy

- Unit tests mock ES client for fast execution
- Integration tests use real ES in Docker
- UI tests use mock data by default
- E2E tests run against full stack
- Test fixtures provide sample guidelines
- Cleanup ensures test isolation

### Risk Mitigation

1. **UI Complexity**: Start with minimal viable editor, add features incrementally
2. **Performance**: Implement caching early in T08
3. **Migration**: Feature flag guardrails usage initially
4. **Compatibility**: Keep existing rules files as documentation

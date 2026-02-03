# P10-F03: Draft History Manager - Tasks

## Overview

Total estimated time: 24-30 hours
Total tasks: 24

## Phase 1: Backend Infrastructure (T01-T08)

### T01: Create Architect ORM Models

**Estimate:** 1 hour
**Domain:** backend
**Dependencies:** None
**Story:** US-01, US-02

Add ORM models for architect_drafts and architect_exports tables.

**Files:**
- `src/orchestrator/persistence/orm_models.py` (update)

**Acceptance:**
- [ ] ArchitectDraftORM model with all fields
- [ ] ArchitectExportORM model with foreign key
- [ ] Relationships defined correctly
- [ ] Type hints using SQLAlchemy 2.0 Mapped style

---

### T02: Create Alembic Migration

**Estimate:** 45 minutes
**Domain:** backend
**Dependencies:** T01
**Story:** US-01

Create database migration for architect tables.

**Files:**
- `src/orchestrator/alembic/versions/YYYYMMDD_HHMMSS_architect_tables.py` (new)

**Acceptance:**
- [ ] Creates architect_drafts table with indexes
- [ ] Creates architect_exports table with foreign key
- [ ] Downgrade drops tables correctly
- [ ] Migration runs successfully

---

### T03: Create Pydantic Models

**Estimate:** 45 minutes
**Domain:** backend
**Dependencies:** None
**Story:** US-01, US-02

Define Pydantic models for API request/response.

**Files:**
- `src/orchestrator/api/models/architect.py` (new)

**Acceptance:**
- [ ] ArchitectDraftCreate, ArchitectDraftUpdate models
- [ ] ArchitectDraft, ArchitectDraftSummary response models
- [ ] ArchitectExport model
- [ ] All models have proper validation

---

### T04: Create PostgreSQL Repository

**Estimate:** 1.5 hours
**Domain:** backend
**Dependencies:** T01, T03
**Story:** US-01, US-02, US-03

Implement PostgreSQL repository for draft CRUD operations.

**Files:**
- `src/orchestrator/repositories/postgres/architect_repository.py` (new)
- `src/orchestrator/repositories/interfaces.py` (update)

**Acceptance:**
- [ ] create_draft() method
- [ ] get_draft() method
- [ ] list_drafts() method with user filter
- [ ] update_draft() method
- [ ] delete_draft() method
- [ ] get_exports_for_draft() method
- [ ] Unit tests pass

---

### T05: Create Redis Cache Repository

**Estimate:** 1 hour
**Domain:** backend
**Dependencies:** T03
**Story:** US-04

Implement Redis cache layer for draft access optimization.

**Files:**
- `src/orchestrator/repositories/redis/architect_repository.py` (new)

**Acceptance:**
- [ ] cache_draft() method with 1hr TTL
- [ ] get_cached_draft() method
- [ ] invalidate_draft() method
- [ ] cache_user_drafts() for list caching
- [ ] Unit tests pass

---

### T06: Create Architect Service

**Estimate:** 1.5 hours
**Domain:** backend
**Dependencies:** T04, T05
**Story:** US-01, US-02, US-03, US-05

Implement service layer with dual-storage logic.

**Files:**
- `src/orchestrator/services/architect_service.py` (new)

**Acceptance:**
- [ ] save_draft() with write-through cache
- [ ] get_draft() with read-through cache
- [ ] list_drafts() with cache
- [ ] delete_draft() with cache invalidation
- [ ] get_draft_exports() method
- [ ] create_export() for F02 integration
- [ ] Unit tests pass

---

### T07: Create API Routes

**Estimate:** 1.5 hours
**Domain:** backend
**Dependencies:** T06
**Story:** US-01, US-02, US-03, US-04, US-05

Implement FastAPI routes for architect endpoints.

**Files:**
- `src/orchestrator/routes/architect_api.py` (new)
- `src/orchestrator/routes/__init__.py` (update)
- `src/orchestrator/main.py` (update to include router)

**Acceptance:**
- [ ] GET /api/architect/drafts endpoint
- [ ] GET /api/architect/drafts/:id endpoint
- [ ] POST /api/architect/drafts endpoint
- [ ] PUT /api/architect/drafts/:id endpoint
- [ ] DELETE /api/architect/drafts/:id endpoint
- [ ] GET /api/architect/drafts/:id/exports endpoint
- [ ] User ID extraction from request context
- [ ] Integration tests pass

---

### T08: Backend Integration Tests

**Estimate:** 1 hour
**Domain:** backend
**Dependencies:** T07
**Story:** US-01, US-02, US-03

Write integration tests for full backend flow.

**Files:**
- `tests/integration/test_architect_api.py` (new)

**Acceptance:**
- [ ] Test create draft flow
- [ ] Test update draft flow
- [ ] Test delete draft with exports cascade
- [ ] Test list drafts pagination
- [ ] Test cache behavior

---

## Phase 2: Frontend API Layer (T09-T11)

### T09: Update TypeScript Types

**Estimate:** 30 minutes
**Domain:** frontend
**Dependencies:** T03
**Story:** US-01, US-02

Update frontend types to match backend models.

**Files:**
- `docker/hitl-ui/src/api/types/architect.ts` (update)

**Acceptance:**
- [ ] ArchitectDraft type with all fields
- [ ] ArchitectDraftSummary type
- [ ] ArchitectExport type
- [ ] Request/Response types defined
- [ ] ExportFormat union type

---

### T10: Implement API Functions

**Estimate:** 1 hour
**Domain:** frontend
**Dependencies:** T09
**Story:** US-01, US-02, US-03, US-04, US-05

Add API functions for draft CRUD operations.

**Files:**
- `docker/hitl-ui/src/api/architect.ts` (update)

**Acceptance:**
- [ ] getDrafts() function
- [ ] getDraft(id) function
- [ ] createDraft(data) function
- [ ] updateDraft(id, data) function
- [ ] deleteDraft(id) function
- [ ] getDraftExports(id) function
- [ ] Mock mode support
- [ ] Error handling

---

### T11: Create API Mocks

**Estimate:** 45 minutes
**Domain:** frontend
**Dependencies:** T10
**Story:** US-01, US-02, US-03, US-04

Create mock implementations for development.

**Files:**
- `docker/hitl-ui/src/api/mocks/architect.ts` (new)

**Acceptance:**
- [ ] Mock draft list
- [ ] Mock CRUD operations
- [ ] Simulated network delay
- [ ] Mock export data

---

## Phase 3: Store Updates (T12-T13)

### T12: Update Architect Store

**Estimate:** 1.5 hours
**Domain:** frontend
**Dependencies:** T10
**Story:** US-01, US-02, US-03, US-06

Extend store with draft management state and actions.

**Files:**
- `docker/hitl-ui/src/stores/architectStore.ts` (update)

**Acceptance:**
- [ ] currentDraftId state
- [ ] isDirty state with tracking
- [ ] isSaving, isLoading states
- [ ] drafts list state
- [ ] historyModalOpen state
- [ ] saveDraft() action
- [ ] loadDraft() action
- [ ] deleteDraft() action
- [ ] fetchDrafts() action
- [ ] markDirty/markClean actions
- [ ] createNewDraft() action

---

### T13: Store Unit Tests

**Estimate:** 1 hour
**Domain:** frontend
**Dependencies:** T12
**Story:** US-01, US-02, US-03, US-06

Write comprehensive store tests.

**Files:**
- `docker/hitl-ui/src/stores/architectStore.test.ts` (update)

**Acceptance:**
- [ ] Test saveDraft flow
- [ ] Test loadDraft flow
- [ ] Test deleteDraft flow
- [ ] Test dirty tracking
- [ ] Test state consistency

---

## Phase 4: UI Components (T14-T20)

### T14: Create SaveDraftDialog

**Estimate:** 1 hour
**Domain:** frontend
**Dependencies:** T12
**Story:** US-01

Implement save draft dialog with name input.

**Files:**
- `docker/hitl-ui/src/components/architect/SaveDraftDialog.tsx` (new)
- `docker/hitl-ui/src/components/architect/SaveDraftDialog.test.tsx` (new)

**Acceptance:**
- [ ] Name input field with auto-generate default
- [ ] Save and Cancel buttons
- [ ] Loading state during save
- [ ] Validation for empty name
- [ ] Keyboard support (Enter to save)

---

### T15: Create UnsavedChangesDialog

**Estimate:** 45 minutes
**Domain:** frontend
**Dependencies:** T12
**Story:** US-06

Implement warning dialog for unsaved changes.

**Files:**
- `docker/hitl-ui/src/components/architect/UnsavedChangesDialog.tsx` (new)
- `docker/hitl-ui/src/components/architect/UnsavedChangesDialog.test.tsx` (new)

**Acceptance:**
- [ ] Save, Discard, Cancel buttons
- [ ] Warning message with draft name
- [ ] Proper button colors (destructive for Discard)
- [ ] Accessible dialog

---

### T16: Create DraftListItem

**Estimate:** 1 hour
**Domain:** frontend
**Dependencies:** T12
**Story:** US-04, US-05

Implement draft list item component for history.

**Files:**
- `docker/hitl-ui/src/components/architect/DraftListItem.tsx` (new)
- `docker/hitl-ui/src/components/architect/DraftListItem.test.tsx` (new)

**Acceptance:**
- [ ] Thumbnail preview (with fallback)
- [ ] Draft name and timestamp
- [ ] Export count badge
- [ ] Delete button with confirmation
- [ ] Click to load action
- [ ] Hover/focus states

---

### T17: Create HistoryModal

**Estimate:** 1.5 hours
**Domain:** frontend
**Dependencies:** T16, T15
**Story:** US-02, US-03, US-04

Implement history browser modal.

**Files:**
- `docker/hitl-ui/src/components/architect/HistoryModal.tsx` (new)
- `docker/hitl-ui/src/components/architect/HistoryModal.test.tsx` (new)

**Acceptance:**
- [ ] Modal with header and close button
- [ ] Draft list using DraftListItem
- [ ] Empty state when no drafts
- [ ] Loading state during fetch
- [ ] Error state handling
- [ ] Integrates UnsavedChangesDialog

---

### T18: Update ActionBar

**Estimate:** 1 hour
**Domain:** frontend
**Dependencies:** T12, T14, T17
**Story:** US-01, US-02, US-08

Enable save/history buttons and add new button.

**Files:**
- `docker/hitl-ui/src/components/architect/ActionBar.tsx` (update)
- `docker/hitl-ui/src/components/architect/ActionBar.test.tsx` (update)

**Acceptance:**
- [ ] Save Draft button enabled when dirty or has content
- [ ] History button opens HistoryModal
- [ ] New button for creating fresh canvas
- [ ] Loading states on buttons
- [ ] Save indicator (saved time)

---

### T19: Create useArchitectAutoSave Hook

**Estimate:** 1 hour
**Domain:** frontend
**Dependencies:** T12
**Story:** US-07

Implement auto-save hook following useAutoSave pattern.

**Files:**
- `docker/hitl-ui/src/hooks/useArchitectAutoSave.ts` (new)
- `docker/hitl-ui/src/hooks/useArchitectAutoSave.test.ts` (new)

**Acceptance:**
- [ ] 2-minute interval when dirty
- [ ] 500ms debounce
- [ ] Only auto-saves existing drafts (with ID)
- [ ] Resets timer on manual save
- [ ] Returns isSaving, lastSaveTime

---

### T20: Update ArchitectBoardPage

**Estimate:** 1 hour
**Domain:** frontend
**Dependencies:** T17, T18, T19
**Story:** US-02, US-06, US-07

Integrate new components into main page.

**Files:**
- `docker/hitl-ui/src/pages/ArchitectBoardPage.tsx` (update)
- `docker/hitl-ui/src/pages/ArchitectBoardPage.test.tsx` (update)

**Acceptance:**
- [ ] HistoryModal rendered
- [ ] SaveDraftDialog rendered
- [ ] useArchitectAutoSave integrated
- [ ] beforeunload handler for dirty state
- [ ] Navigation guards

---

## Phase 5: Integration and Polish (T21-T24)

### T21: Thumbnail Generation

**Estimate:** 1 hour
**Domain:** frontend
**Dependencies:** T12
**Story:** US-04

Implement thumbnail generation on save.

**Files:**
- `docker/hitl-ui/src/stores/architectStore.ts` (update)
- `docker/hitl-ui/src/utils/thumbnailGenerator.ts` (new)

**Acceptance:**
- [ ] Generate PNG thumbnail (200x150)
- [ ] Convert to base64
- [ ] Include in save payload
- [ ] Handle generation errors gracefully

---

### T22: Export Integration with F02

**Estimate:** 1 hour
**Domain:** frontend
**Dependencies:** T06, T10
**Story:** US-05

Link exports to drafts when translation completes.

**Files:**
- `docker/hitl-ui/src/stores/architectStore.ts` (update)
- `docker/hitl-ui/src/components/architect/OutputPanel.tsx` (update)

**Acceptance:**
- [ ] After translation, call create_export API
- [ ] Store export ID for history view
- [ ] Show export count in history

---

### T23: Component Index and Exports

**Estimate:** 30 minutes
**Domain:** frontend
**Dependencies:** T14, T15, T16, T17

Update component index with new exports.

**Files:**
- `docker/hitl-ui/src/components/architect/index.ts` (update)

**Acceptance:**
- [ ] Export all new components
- [ ] Export hooks

---

### T24: End-to-End Testing

**Estimate:** 1.5 hours
**Domain:** frontend
**Dependencies:** T20, T22
**Story:** All

Write E2E tests for complete draft workflow.

**Files:**
- `docker/hitl-ui/e2e/architect.spec.ts` (new or update)

**Acceptance:**
- [ ] Test save draft flow
- [ ] Test load draft flow
- [ ] Test delete draft flow
- [ ] Test unsaved changes warning
- [ ] Test auto-save behavior

---

## Progress Tracking

### Phase 1: Backend Infrastructure
- [ ] T01: Create Architect ORM Models
- [ ] T02: Create Alembic Migration
- [ ] T03: Create Pydantic Models
- [ ] T04: Create PostgreSQL Repository
- [ ] T05: Create Redis Cache Repository
- [ ] T06: Create Architect Service
- [ ] T07: Create API Routes
- [ ] T08: Backend Integration Tests

**Phase 1 Progress:** 0/8 tasks (0%)

### Phase 2: Frontend API Layer
- [ ] T09: Update TypeScript Types
- [ ] T10: Implement API Functions
- [ ] T11: Create API Mocks

**Phase 2 Progress:** 0/3 tasks (0%)

### Phase 3: Store Updates
- [ ] T12: Update Architect Store
- [ ] T13: Store Unit Tests

**Phase 3 Progress:** 0/2 tasks (0%)

### Phase 4: UI Components
- [ ] T14: Create SaveDraftDialog
- [ ] T15: Create UnsavedChangesDialog
- [ ] T16: Create DraftListItem
- [ ] T17: Create HistoryModal
- [ ] T18: Update ActionBar
- [ ] T19: Create useArchitectAutoSave Hook
- [ ] T20: Update ArchitectBoardPage

**Phase 4 Progress:** 0/7 tasks (0%)

### Phase 5: Integration and Polish
- [ ] T21: Thumbnail Generation
- [ ] T22: Export Integration with F02
- [ ] T23: Component Index and Exports
- [ ] T24: End-to-End Testing

**Phase 5 Progress:** 0/4 tasks (0%)

---

## Overall Progress

**Total Tasks:** 24
**Completed:** 0
**In Progress:** 0
**Remaining:** 24

**Overall Progress:** 0%

## Task Dependencies Graph

```
Phase 1 (Backend):
T01 --> T02
T01 --> T04 --> T06 --> T07 --> T08
T03 --> T04
T03 --> T05 --> T06
T03 --> T06

Phase 2 (Frontend API):
T03 --> T09 --> T10 --> T11

Phase 3 (Store):
T10 --> T12 --> T13

Phase 4 (UI):
T12 --> T14, T15, T16, T19
T16 + T15 --> T17
T12 + T14 + T17 --> T18
T17 + T18 + T19 --> T20

Phase 5 (Integration):
T12 --> T21
T06 + T10 --> T22
T14-T17 --> T23
T20 + T22 --> T24
```

## Notes

- Backend (Phase 1) and Frontend API (Phase 2) can be developed in parallel
- Phase 3 depends on Phase 2 completion
- Phase 4 depends on Phase 3 completion
- Phase 5 integrates all previous work
- All TDD: write tests first, then implementation

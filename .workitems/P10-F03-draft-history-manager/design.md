# P10-F03: Draft History Manager - Technical Design

## Overview

The Draft History Manager enables saving Architect Board drawings as drafts and browsing history of past drawings with their generated diagrams. This feature builds on F01 (canvas) and F02 (translation) to provide persistent storage and retrieval of architectural diagrams.

### Goals

1. Enable draft save/load/delete for Architect Board drawings
2. Provide history browsing with thumbnail previews
3. Link drafts to their generated exports (PNG, MMD, Draw.io from F02)
4. Implement dual-layer storage (PostgreSQL + Redis cache)
5. Add unsaved changes warning before navigation

### Non-Goals (Out of Scope)

- Version history within a single draft (deferred)
- Collaborative editing
- Draft sharing between users
- Export scheduling/automation

## Technical Approach

### Storage Architecture

```
+------------------+     +-----------------+     +------------------+
|   Frontend       |     |   Backend       |     |   Storage        |
|                  |     |                 |     |                  |
| architectStore   |---->| /api/architect/ |---->| PostgreSQL       |
| (Zustand)        |     | routes          |     | (persistent)     |
|                  |     |                 |     |                  |
| useAutoSave      |     | DraftService    |---->| Redis            |
| hook             |     |                 |     | (cache, 1hr TTL) |
+------------------+     +-----------------+     +------------------+
```

**Dual-Layer Strategy:**
- **PostgreSQL**: Primary persistent storage for drafts and exports
- **Redis**: Cache layer for recently accessed drafts (1-hour TTL)
- Write-through: Writes go to both PostgreSQL and Redis
- Read-through: Read from Redis first, fallback to PostgreSQL

### Database Schema

```sql
-- Architect drafts table
CREATE TABLE architect_drafts (
    id          VARCHAR(64) PRIMARY KEY,
    user_id     VARCHAR(64) NOT NULL,
    name        VARCHAR(255) NOT NULL,
    elements    JSONB NOT NULL,           -- Excalidraw elements array
    app_state   JSONB NOT NULL,           -- Excalidraw appState (partial)
    thumbnail   TEXT,                     -- Base64 encoded preview image
    created_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_drafts_user_id ON architect_drafts(user_id);
CREATE INDEX idx_drafts_updated_at ON architect_drafts(updated_at);

-- Architect exports table (linked to drafts)
CREATE TABLE architect_exports (
    id          VARCHAR(64) PRIMARY KEY,
    draft_id    VARCHAR(64) REFERENCES architect_drafts(id) ON DELETE CASCADE,
    format      VARCHAR(16) NOT NULL,     -- 'svg', 'png', 'mmd', 'drawio'
    content     TEXT NOT NULL,            -- Base64 for binary, raw for text
    created_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_exports_draft_id ON architect_exports(draft_id);
CREATE INDEX idx_exports_format ON architect_exports(format);
```

### Redis Cache Schema

```
Key Patterns:
- ARCHITECT:DRAFT:{draft_id}           -> Hash with draft data
- ARCHITECT:USER_DRAFTS:{user_id}      -> Sorted set of draft IDs by updated_at
- ARCHITECT:EXPORTS:{draft_id}         -> List of export IDs for draft

TTL: 1 hour (3600 seconds) for all cached data
```

### Component Architecture

```
docker/hitl-ui/src/
  pages/
    ArchitectBoardPage.tsx              # Updated with save/load

  components/
    architect/
      HistoryModal.tsx                  # NEW: Draft history browser
      HistoryModal.test.tsx
      DraftListItem.tsx                 # NEW: Single draft in list
      DraftListItem.test.tsx
      SaveDraftDialog.tsx               # NEW: Name/save confirmation
      SaveDraftDialog.test.tsx
      UnsavedChangesDialog.tsx          # NEW: Navigation warning
      UnsavedChangesDialog.test.tsx
      ActionBar.tsx                     # Updated: Enable Save button

  stores/
    architectStore.ts                   # Updated with draft CRUD

  api/
    architect.ts                        # Updated with API calls
    types/architect.ts                  # Updated with full types

  hooks/
    useArchitectAutoSave.ts             # NEW: Auto-save hook
    useArchitectAutoSave.test.ts
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/architect/drafts` | List all drafts for user |
| GET | `/api/architect/drafts/:id` | Get single draft with elements |
| POST | `/api/architect/drafts` | Create new draft |
| PUT | `/api/architect/drafts/:id` | Update existing draft |
| DELETE | `/api/architect/drafts/:id` | Delete draft |
| GET | `/api/architect/drafts/:id/exports` | Get exports for draft |

### Backend Service Structure

```
src/orchestrator/
  api/
    models/
      architect.py                      # NEW: Pydantic models

  routes/
    architect_api.py                    # NEW: FastAPI routes

  services/
    architect_service.py                # NEW: Business logic

  persistence/
    orm_models.py                       # Updated with new tables

  repositories/
    postgres/
      architect_repository.py           # NEW: PostgreSQL repo
    redis/
      architect_repository.py           # NEW: Redis cache repo

  alembic/
    versions/
      YYYYMMDD_HHMMSS_architect_tables.py  # NEW: Migration
```

## Interfaces and Dependencies

### TypeScript Types

```typescript
// src/api/types/architect.ts

export interface ArchitectDraft {
  id: string;
  userId: string;
  name: string;
  elements: ExcalidrawElement[];
  appState: Partial<AppState>;
  thumbnail?: string;         // Base64 preview
  createdAt: string;
  updatedAt: string;
}

export interface ArchitectDraftSummary {
  id: string;
  name: string;
  thumbnail?: string;
  updatedAt: string;
  exportCount: number;        // Number of linked exports
}

export interface ArchitectExport {
  id: string;
  draftId: string;
  format: ExportFormat;
  content: string;
  createdAt: string;
}

export type ExportFormat = 'svg' | 'png' | 'mmd' | 'drawio';

export interface CreateDraftRequest {
  name?: string;              // Auto-generates if not provided
  elements: ExcalidrawElement[];
  appState: Partial<AppState>;
  thumbnail?: string;
}

export interface UpdateDraftRequest {
  name?: string;
  elements?: ExcalidrawElement[];
  appState?: Partial<AppState>;
  thumbnail?: string;
}

export interface DraftsListResponse {
  drafts: ArchitectDraftSummary[];
  total: number;
}
```

### Python Models

```python
# src/orchestrator/api/models/architect.py

from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class ArchitectDraftBase(BaseModel):
    name: str
    elements: list[dict[str, Any]]
    app_state: dict[str, Any]
    thumbnail: Optional[str] = None

class ArchitectDraftCreate(ArchitectDraftBase):
    pass

class ArchitectDraftUpdate(BaseModel):
    name: Optional[str] = None
    elements: Optional[list[dict[str, Any]]] = None
    app_state: Optional[dict[str, Any]] = None
    thumbnail: Optional[str] = None

class ArchitectDraft(ArchitectDraftBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

class ArchitectDraftSummary(BaseModel):
    id: str
    name: str
    thumbnail: Optional[str]
    updated_at: datetime
    export_count: int

class ArchitectExport(BaseModel):
    id: str
    draft_id: str
    format: str
    content: str
    created_at: datetime
```

### Store Interface

```typescript
// Updated architectStore interface

interface ArchitectState {
  // Existing from F01
  canvasId: string | null;
  canvasName: string;
  excalidrawElements: ExcalidrawElement[];
  excalidrawState: AppState | null;
  exportedSvg: string | null;
  isExporting: boolean;
  toolsPanelOpen: boolean;
  outputPanelOpen: boolean;

  // New for F03
  currentDraftId: string | null;
  isDirty: boolean;                    // Tracks unsaved changes
  isSaving: boolean;
  isLoading: boolean;
  drafts: ArchitectDraftSummary[];
  historyModalOpen: boolean;

  // Existing actions
  setCanvasName: (name: string) => void;
  updateElements: (elements: ExcalidrawElement[]) => void;
  updateAppState: (state: AppState) => void;
  exportToSvg: () => Promise<void>;
  toggleToolsPanel: () => void;
  toggleOutputPanel: () => void;
  resetCanvas: () => void;

  // New actions for F03
  saveDraft: (name?: string) => Promise<string>;
  loadDraft: (id: string) => Promise<void>;
  deleteDraft: (id: string) => Promise<void>;
  fetchDrafts: () => Promise<void>;
  openHistoryModal: () => void;
  closeHistoryModal: () => void;
  markDirty: () => void;
  markClean: () => void;
  createNewDraft: () => void;
}
```

### Internal Dependencies

| Component | Depends On |
|-----------|------------|
| HistoryModal | architectStore, DraftListItem |
| DraftListItem | architectStore |
| SaveDraftDialog | architectStore |
| UnsavedChangesDialog | architectStore |
| ActionBar (updated) | architectStore |
| useArchitectAutoSave | architectStore, useAutoSave pattern |
| architect_api.py | architect_service.py |
| architect_service.py | architect_repository (postgres + redis) |

### External Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| @excalidraw/excalidraw | (existing) | Canvas API for export |
| zustand | (existing) | State management |
| react-query | (existing) | API data fetching |
| sqlalchemy | (existing) | ORM |
| redis | (existing) | Cache client |

## Architecture Decisions

### AD-1: Dual-Layer Storage Strategy

**Decision:** Use PostgreSQL as primary storage with Redis as write-through cache.

**Rationale:**
- PostgreSQL provides durable, queryable storage for all drafts
- Redis cache reduces database load for frequently accessed drafts
- Write-through ensures cache consistency
- 1-hour TTL balances freshness with memory usage

**Trade-offs:**
- Additional complexity vs single-store approach
- Cache invalidation on delete requires explicit handling
- Network latency doubled on writes (acceptable for save operations)

### AD-2: Thumbnail Generation Strategy

**Decision:** Generate thumbnails client-side using Excalidraw's export API.

**Rationale:**
- Excalidraw provides efficient PNG export
- Thumbnails generated at save time, stored with draft
- Fixed size (200x150) for consistency
- Base64 encoding for simple storage

**Alternative Considered:** Server-side rendering
- Rejected: Requires additional dependencies, slower, more complex

### AD-3: Export Linking via Foreign Key

**Decision:** Use foreign key from exports to drafts with CASCADE delete.

**Rationale:**
- Natural relationship: exports are derived from drafts
- CASCADE delete prevents orphaned exports
- Single query can fetch draft with all exports
- Index on draft_id supports efficient lookups

### AD-4: Auto-Save with Debounce

**Decision:** Implement auto-save with 2-minute interval and 500ms debounce.

**Rationale:**
- Matches existing useAutoSave pattern from ideation feature
- Prevents data loss without excessive API calls
- Debounce handles rapid changes (e.g., drawing)
- User can also save manually at any time

### AD-5: Unsaved Changes Detection

**Decision:** Track dirty state via store flag, set on any element/state change.

**Rationale:**
- Simple boolean flag is sufficient
- Set dirty on updateElements/updateAppState
- Clear dirty after successful save
- Check before navigation or new draft

## File Structure

```
docker/hitl-ui/src/
  components/architect/
    HistoryModal.tsx
    HistoryModal.test.tsx
    DraftListItem.tsx
    DraftListItem.test.tsx
    SaveDraftDialog.tsx
    SaveDraftDialog.test.tsx
    UnsavedChangesDialog.tsx
    UnsavedChangesDialog.test.tsx
    ActionBar.tsx                       # Updated
    index.ts                            # Updated exports

  hooks/
    useArchitectAutoSave.ts
    useArchitectAutoSave.test.ts

  stores/
    architectStore.ts                   # Updated
    architectStore.test.ts              # Updated

  api/
    architect.ts                        # Updated
    types/architect.ts                  # Updated

src/orchestrator/
  api/models/
    architect.py

  routes/
    architect_api.py

  services/
    architect_service.py

  repositories/
    interfaces.py                       # Updated
    postgres/
      architect_repository.py
    redis/
      architect_repository.py

  persistence/
    orm_models.py                       # Updated

  alembic/versions/
    YYYYMMDD_HHMMSS_architect_tables.py
```

## Integration Points

### With F01 (Canvas)

- Extends architectStore with draft persistence
- ActionBar "Save Draft" button becomes enabled
- "History" button opens HistoryModal

### With F02 (Translation)

- When translation completes, store export with draft reference
- History view shows exports linked to each draft
- Export records include format, content, timestamp

### Navigation Guards

Add to App.tsx or ArchitectBoardPage:
```tsx
// Prompt user before leaving with unsaved changes
useEffect(() => {
  const handleBeforeUnload = (e: BeforeUnloadEvent) => {
    if (isDirty) {
      e.preventDefault();
      e.returnValue = '';
    }
  };
  window.addEventListener('beforeunload', handleBeforeUnload);
  return () => window.removeEventListener('beforeunload', handleBeforeUnload);
}, [isDirty]);
```

## Testing Strategy

| Component | Test Focus |
|-----------|------------|
| HistoryModal | Open/close, draft list rendering, load/delete actions |
| DraftListItem | Thumbnail display, click handlers, delete confirmation |
| SaveDraftDialog | Name input, save/cancel, validation |
| UnsavedChangesDialog | Discard/cancel, navigation blocking |
| useArchitectAutoSave | Interval timing, debounce, error handling |
| architectStore | CRUD actions, dirty tracking, state consistency |
| architect_api.py | CRUD endpoints, validation, auth |
| architect_service.py | Business logic, cache handling |
| architect_repository | Database operations, cache operations |

### Test Utilities

```typescript
// Mock draft data for tests
export const mockDraft: ArchitectDraft = {
  id: 'draft-001',
  userId: 'user-001',
  name: 'Test Architecture',
  elements: [],
  appState: {},
  thumbnail: 'data:image/png;base64,...',
  createdAt: '2026-02-01T12:00:00Z',
  updatedAt: '2026-02-01T12:00:00Z',
};
```

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large draft payloads | Slow saves, storage costs | Compress elements, limit element count |
| Cache invalidation issues | Stale data shown | Explicit invalidation on delete, short TTL |
| Thumbnail generation fails | Missing previews | Graceful fallback to placeholder image |
| Concurrent edit conflicts | Data loss | Optimistic locking via version field |
| Auto-save during navigation | Partial save | Complete save before allowing navigation |

## Success Metrics

- Draft save completes within 500ms
- History modal loads within 300ms (cached drafts)
- Auto-save triggers reliably every 2 minutes when dirty
- Unsaved changes warning appears consistently
- All tests pass with >80% coverage

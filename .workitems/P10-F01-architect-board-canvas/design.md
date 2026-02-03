# P10-F01: Architect Board Canvas - Technical Design

## Overview

The Architect Board is a new feature in the HITL UI that provides an interactive canvas for creating and editing diagrams using Excalidraw. This feature (F01) focuses on the core canvas UI, panel layout, and SVG export functionality. LLM-based translation to other formats (PNG via Gemini, Mermaid, Draw.io XML) will be implemented in F02.

### Goals

1. Provide an intuitive drawing canvas using Excalidraw
2. Implement a responsive 3-panel layout (tools | canvas | output)
3. Enable collapsible side panels for maximum canvas space
4. Support SVG export for later LLM processing (F02)
5. Follow existing HITL UI patterns for consistency

### Non-Goals (Deferred to F02/F03)

- LLM translation to PNG/Mermaid/Draw.io (F02)
- Draft persistence to database (F03)
- History browsing (F03)
- Redis caching (F03)

## Technical Approach

### Library Selection

**Excalidraw** (MIT License) is the selected drawing library:
- React-native integration
- Rich drawing tools (shapes, arrows, text, freehand)
- Built-in export to SVG, PNG, JSON
- Active community and maintenance
- Used by major projects (Notion, Obsidian)

Installation:
```bash
npm install @excalidraw/excalidraw
```

### Component Architecture

```
src/
  pages/
    ArchitectBoardPage.tsx         # Main page component
    ArchitectBoardPage.test.tsx    # Page tests

  components/
    architect/
      index.ts                      # Barrel export
      ArchitectCanvas.tsx           # Excalidraw wrapper
      ArchitectCanvas.test.tsx
      ToolsPanel.tsx                # Left collapsible panel
      ToolsPanel.test.tsx
      OutputPanel.tsx               # Right collapsible panel
      OutputPanel.test.tsx
      ActionBar.tsx                 # Bottom toolbar
      ActionBar.test.tsx
      ExportPreview.tsx             # SVG preview in output panel
      ExportPreview.test.tsx

  stores/
    architectStore.ts               # Zustand store for state
    architectStore.test.ts

  api/
    architect.ts                    # API functions (stub for F01)
    types/architect.ts              # TypeScript types
```

### Page Layout

```
+------------------------------------------------------------------+
|  Session Bar: Title | Save Draft* | Translate* | History*         |
+------------------------------------------------------------------+
|        |                                  |                       |
| Tools  |         Canvas                   |    Output Panel       |
| Panel  |      (Excalidraw)                |    - SVG Preview      |
| (coll) |                                  |    - Export tabs      |
|        |                                  |    (coll)             |
|        |                                  |                       |
+------------------------------------------------------------------+
|  Action Bar: Save Draft | History | Translate Dropdown            |
+------------------------------------------------------------------+

* Buttons disabled in F01 (implemented in F02/F03)
```

### Layout Integration with HITL UI

The HITL UI uses `Layout.tsx` which provides a fixed Header, StatusBar, and padded main content area. ArchitectBoardPage requires a full-screen canvas experience without the default padding.

**Approach:** ArchitectBoardPage will be a full-screen page that:

1. Sets `overflow-hidden` on its container to prevent scrolling
2. Uses `h-screen` minus header height for full vertical space
3. Removes default padding by using negative margins or a layout override class

**Implementation pattern:**
```tsx
// ArchitectBoardPage.tsx
function ArchitectBoardPage() {
  return (
    <div className="absolute inset-0 top-16 flex flex-col overflow-hidden">
      {/* Session bar */}
      <div className="h-12 border-b flex items-center px-4">...</div>

      {/* Main 3-panel area */}
      <div className="flex-1 flex overflow-hidden">
        <ToolsPanel />
        <ArchitectCanvas />
        <OutputPanel />
      </div>

      {/* Action bar */}
      <ActionBar />
    </div>
  );
}
```

This pattern is similar to how studio pages (StudioDiscoveryPage, StudioIdeationPage) handle full-canvas experiences within the Layout wrapper.

### Error Boundary Integration

ArchitectBoardPage must be wrapped with the existing ErrorBoundary component to handle runtime errors gracefully, especially from Excalidraw.

**Pattern:**
```tsx
// In App.tsx routes
<Route
  path="architect"
  element={
    <ErrorBoundary fallback={<ErrorFallback />}>
      <Suspense fallback={<LoadingSpinner />}>
        <ArchitectBoardPage />
      </Suspense>
    </ErrorBoundary>
  }
/>
```

The ErrorBoundary catches:
- Excalidraw initialization failures
- Export errors
- State corruption

### Lazy Loading Strategy

Excalidraw is a large library (~500KB+ gzipped). To prevent bundle bloat and improve initial load time, ArchitectBoardPage and its dependencies will be lazy-loaded.

**Implementation:**
```tsx
// In App.tsx
const ArchitectBoardPage = React.lazy(() => import('./pages/ArchitectBoardPage'));

// Route with Suspense
<Route
  path="architect"
  element={
    <Suspense fallback={<LoadingSpinner />}>
      <ArchitectBoardPage />
    </Suspense>
  }
/>
```

**Bundle analysis target:** ArchitectBoardPage chunk should be separate from main bundle, loaded only when user navigates to `/architect`.

### Panel Behavior

**Tools Panel (Left)**
- Default: Collapsed (hamburger icon)
- Width when expanded: 240px
- Width when collapsed: 48px
- Contains: Drawing tool presets, color palette, stroke width

**Output Panel (Right)**
- Default: Collapsed
- Width when expanded: 320px (w-80)
- Width when collapsed: 48px (w-12)
- Contains: SVG preview, future format tabs (PNG, MMD, Draw.io)

**Collapse Pattern** (matches existing UI):
```tsx
<div className={clsx(
  'flex flex-col border-l transition-all duration-300',
  isCollapsed ? 'w-12' : 'w-80'
)}>
```

### State Management

Using Zustand (consistent with existing stores):

```typescript
interface ArchitectState {
  // Canvas state
  canvasId: string | null;
  canvasName: string;
  excalidrawElements: ExcalidrawElement[];
  excalidrawState: AppState | null;

  // Export state
  exportedSvg: string | null;
  isExporting: boolean;

  // Panel state
  toolsPanelOpen: boolean;
  outputPanelOpen: boolean;

  // Actions
  setCanvasName: (name: string) => void;
  updateElements: (elements: ExcalidrawElement[]) => void;
  updateAppState: (state: AppState) => void;
  exportToSvg: () => Promise<void>;
  toggleToolsPanel: () => void;
  toggleOutputPanel: () => void;
  resetCanvas: () => void;
}
```

### State Persistence Decision

**Decision:** Canvas state will NOT persist to localStorage for F01.

**Rationale:**
- F01 focuses on core drawing and export functionality
- Premature persistence adds complexity without clear benefit
- Users expect explicit "Save" action (coming in F03)
- Avoids potential state corruption issues during development

**Behavior:**
- Canvas state is ephemeral (in-memory only)
- Navigating away loses unsaved work
- Warning dialog will prompt before navigation if canvas has content
- Draft persistence (localStorage + backend) is planned for F03

### Excalidraw Integration

The Excalidraw component requires specific handling:

```tsx
import { Excalidraw, exportToSvg } from '@excalidraw/excalidraw';

function ArchitectCanvas() {
  const excalidrawRef = useRef<ExcalidrawImperativeAPI>(null);
  const { updateElements, updateAppState } = useArchitectStore();

  const handleChange = useCallback((
    elements: readonly ExcalidrawElement[],
    appState: AppState
  ) => {
    updateElements([...elements]);
    updateAppState(appState);
  }, [updateElements, updateAppState]);

  return (
    <div className="flex-1 h-full">
      <Excalidraw
        ref={excalidrawRef}
        onChange={handleChange}
        theme="dark"
        langCode="en"
      />
    </div>
  );
}
```

### SVG Export Flow

```
User clicks "Export SVG"
  -> architectStore.exportToSvg()
  -> excalidrawAPI.exportToSvg(elements, appState)
  -> Store SVG string in state
  -> Display in OutputPanel ExportPreview
```

### Types

```typescript
// src/api/types/architect.ts

export interface ArchitectDraft {
  id: string;
  name: string;
  elements: ExcalidrawElement[];
  appState: Partial<AppState>;
  createdAt: string;
  updatedAt: string;
}

export interface ArchitectExport {
  draftId: string;
  format: 'svg' | 'png' | 'mmd' | 'drawio';
  content: string;  // Base64 for PNG, raw string for others
  createdAt: string;
}

export type ExportFormat = 'svg' | 'png' | 'mmd' | 'drawio';
```

## Interfaces and Dependencies

### Internal Dependencies

| Component | Depends On |
|-----------|------------|
| ArchitectBoardPage | ArchitectCanvas, ToolsPanel, OutputPanel, ActionBar |
| ArchitectCanvas | @excalidraw/excalidraw, architectStore |
| ToolsPanel | architectStore |
| OutputPanel | ExportPreview, architectStore |
| ActionBar | architectStore |
| ExportPreview | architectStore |

### External Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| @excalidraw/excalidraw | ^0.17.x | Drawing canvas |
| zustand | (existing) | State management |
| clsx | (existing) | Class composition |
| @heroicons/react | (existing) | Icons |

### API Interfaces (Stub for F01)

```typescript
// These will be implemented in F02/F03
// F01 uses local state only

// GET /api/architect/drafts
export async function getDrafts(): Promise<ArchitectDraft[]>;

// POST /api/architect/drafts
export async function saveDraft(draft: Partial<ArchitectDraft>): Promise<ArchitectDraft>;

// POST /api/architect/translate
export async function translateDiagram(
  draftId: string,
  format: ExportFormat,
  svgContent: string
): Promise<ArchitectExport>;
```

## Architecture Decisions

### AD-1: Excalidraw as Drawing Library

**Decision:** Use Excalidraw for the drawing canvas.

**Rationale:**
- MIT license allows commercial use
- Excellent React integration
- Rich feature set out of the box
- Export capabilities (SVG, PNG, JSON)
- Active maintenance

**Alternatives Considered:**
- Fabric.js: Lower-level, more work to build UI
- Konva: Good but less feature-rich for diagramming
- tldraw: Newer, less mature

### AD-2: SVG as Intermediate Format

**Decision:** Export to SVG for LLM processing.

**Rationale:**
- SVG preserves vector quality
- Can be converted to PNG on backend
- Readable text content for LLM context
- Smaller payload than PNG base64

### AD-3: Zustand for State Management

**Decision:** Use Zustand store (consistent with existing patterns).

**Rationale:**
- Already used throughout HITL UI
- Simpler than Redux
- Good TypeScript support
- Works well with React 18

### AD-4: Panel Collapse Pattern

**Decision:** Follow StudioDiscoveryPage/StudioIdeationPage collapse pattern.

**Rationale:**
- Consistent UX across application
- Users already familiar with the interaction
- Code reuse of existing patterns

### AD-5: No localStorage Persistence in F01

**Decision:** Canvas state is ephemeral until explicit save (F03).

**Rationale:**
- Simpler implementation for F01 scope
- Avoids state corruption edge cases
- Users expect explicit save action for important work
- Draft persistence requires backend coordination (F03)

## File Structure

```
docker/hitl-ui/src/
  pages/
    ArchitectBoardPage.tsx
    ArchitectBoardPage.test.tsx

  components/
    architect/
      index.ts
      ArchitectCanvas.tsx
      ArchitectCanvas.test.tsx
      ToolsPanel.tsx
      ToolsPanel.test.tsx
      OutputPanel.tsx
      OutputPanel.test.tsx
      ActionBar.tsx
      ActionBar.test.tsx
      ExportPreview.tsx
      ExportPreview.test.tsx

  stores/
    architectStore.ts
    architectStore.test.ts

  api/
    architect.ts
    types/
      architect.ts
```

## Integration Points

### Navigation

Add to `Sidebar.tsx` in Workflow section:
```tsx
{ name: 'Architect Board', href: '/architect', icon: PaintBrushIcon },
```

Add to `App.tsx` routes:
```tsx
<Route path="architect" element={<ArchitectBoardPage />} />
```

### Future Integration (F02)

The OutputPanel will need to:
1. Call LLM API with SVG content
2. Display generated PNG/Mermaid/Draw.io
3. Show loading states during generation

Model configuration will be read from admin config "Design Agent" - NOT hardcoded.

## Testing Strategy

| Component | Test Focus |
|-----------|------------|
| ArchitectBoardPage | Integration, layout, panel toggle |
| ArchitectCanvas | Excalidraw mounting, onChange callback |
| ToolsPanel | Collapse/expand, tool selection |
| OutputPanel | Collapse/expand, tab switching |
| ActionBar | Button states, click handlers |
| ExportPreview | SVG rendering, copy functionality |
| architectStore | State mutations, actions |

### Test Utilities

Mock Excalidraw for unit tests:
```typescript
vi.mock('@excalidraw/excalidraw', () => ({
  Excalidraw: ({ onChange }: any) => (
    <div data-testid="mock-excalidraw" onClick={() => onChange([], {})}>
      Mock Canvas
    </div>
  ),
  exportToSvg: vi.fn().mockResolvedValue(new Blob(['<svg></svg>'])),
}));
```

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Excalidraw bundle size | Slow initial load | Code split, lazy load |
| Excalidraw breaking changes | Feature regression | Pin version, test thoroughly |
| State sync issues | Lost work | Debounced auto-save (F03) |
| SVG export failures | Blocked translation | Error handling, retry logic |

## Success Metrics

- Canvas renders within 2s on first load
- Panel toggle animation is smooth (60fps)
- SVG export completes within 500ms
- All tests pass with >80% coverage

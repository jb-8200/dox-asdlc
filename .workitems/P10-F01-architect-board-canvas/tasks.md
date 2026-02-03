# P10-F01: Architect Board Canvas - Task Breakdown

## Overview

Feature: Architect Board Canvas
Total Estimated Time: ~14 hours
Dependencies: None (new feature)

## Phase 1: Foundation Setup (3 hours)

### T01: Install Excalidraw dependency
**Estimate:** 30 min
**Dependencies:** None
**Owner:** frontend

Install @excalidraw/excalidraw package and verify build succeeds.

```bash
cd docker/hitl-ui
npm install @excalidraw/excalidraw
```

**Acceptance:**
- [ ] Package installed in package.json
- [ ] `npm run build` succeeds
- [ ] No TypeScript errors

---

### T02: Create TypeScript types for Architect feature
**Estimate:** 30 min
**Dependencies:** T01
**Owner:** frontend

Create `src/api/types/architect.ts` with all required type definitions.

**Deliverables:**
- [ ] `ArchitectDraft` interface
- [ ] `ArchitectExport` interface
- [ ] `ExportFormat` type
- [ ] Export from `src/api/types/index.ts`

**Acceptance:**
- [ ] Types compile without errors
- [ ] Types exported from barrel file

---

### T03: Create architectStore with Zustand
**Estimate:** 1 hour
**Dependencies:** T02
**Owner:** frontend

Create `src/stores/architectStore.ts` with state management.

**Deliverables:**
- [ ] State interface with canvas, export, and panel state
- [ ] Actions: setCanvasName, updateElements, updateAppState, exportToSvg, togglePanels, resetCanvas
- [ ] Default state values

**Acceptance:**
- [ ] Store creates without errors
- [ ] Actions update state correctly
- [ ] Unit tests pass (architectStore.test.ts)

---

### T04: Write architectStore tests
**Estimate:** 1 hour
**Dependencies:** T03
**Owner:** frontend

Create `src/stores/architectStore.test.ts` with comprehensive tests.

**Test Coverage:**
- [ ] Initial state is correct
- [ ] setCanvasName updates name
- [ ] updateElements updates elements array
- [ ] toggleToolsPanel toggles state
- [ ] toggleOutputPanel toggles state
- [ ] resetCanvas restores defaults

**Acceptance:**
- [ ] All tests pass
- [ ] Coverage >80%

---

## Phase 2: Core Components (5 hours)

### T05: Create ArchitectCanvas component with lazy loading
**Estimate:** 1.5 hours
**Dependencies:** T03
**Owner:** frontend

Create `src/components/architect/ArchitectCanvas.tsx` wrapping Excalidraw.

**Deliverables:**
- [ ] Excalidraw component integration
- [ ] Dark theme configuration
- [ ] onChange handler connected to store
- [ ] Ref for imperative API access
- [ ] Responsive sizing (flex-1, h-full)
- [ ] Component exported for React.lazy() usage

**Lazy Loading Setup (in App.tsx):**
```tsx
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

**Acceptance:**
- [ ] Canvas renders Excalidraw
- [ ] Drawing updates store
- [ ] Theme matches HITL UI dark mode
- [ ] Page chunk is separate from main bundle (verify with build output)

---

### T06: Write ArchitectCanvas tests
**Estimate:** 45 min
**Dependencies:** T05
**Owner:** frontend

Create `src/components/architect/ArchitectCanvas.test.tsx`.

**Test Coverage:**
- [ ] Component mounts
- [ ] Mock Excalidraw renders
- [ ] onChange callback triggers store update

**Acceptance:**
- [ ] All tests pass
- [ ] Excalidraw properly mocked

---

### T07: Create ToolsPanel component
**Estimate:** 1 hour
**Dependencies:** T03
**Owner:** frontend

Create `src/components/architect/ToolsPanel.tsx` with collapse behavior.

**Deliverables:**
- [ ] Collapsible panel (w-12 collapsed, 240px expanded)
- [ ] Toggle button with ChevronLeft/Right icons
- [ ] Header with "Drawing Tools" title
- [ ] Transition animation (300ms)
- [ ] aria-label for accessibility

**Acceptance:**
- [ ] Panel collapses/expands smoothly
- [ ] Toggle updates store state
- [ ] Matches existing panel patterns

---

### T08: Write ToolsPanel tests
**Estimate:** 30 min
**Dependencies:** T07
**Owner:** frontend

Create `src/components/architect/ToolsPanel.test.tsx`.

**Test Coverage:**
- [ ] Renders collapsed by default
- [ ] Toggle expands panel
- [ ] aria-label changes with state

**Acceptance:**
- [ ] All tests pass

---

### T09: Create OutputPanel component
**Estimate:** 1 hour
**Dependencies:** T03
**Owner:** frontend

Create `src/components/architect/OutputPanel.tsx` with collapse behavior.

**Deliverables:**
- [ ] Collapsible panel (w-12 collapsed, w-80 expanded)
- [ ] Toggle button with icons
- [ ] Header with "Output" title
- [ ] Tab structure for future formats (SVG active, PNG/MMD/DrawIO disabled)
- [ ] Placeholder for ExportPreview

**Acceptance:**
- [ ] Panel collapses/expands smoothly
- [ ] Tabs render (only SVG enabled for F01)
- [ ] Matches existing panel patterns

---

### T10: Write OutputPanel tests
**Estimate:** 30 min
**Dependencies:** T09
**Owner:** frontend

Create `src/components/architect/OutputPanel.test.tsx`.

**Test Coverage:**
- [ ] Renders collapsed by default
- [ ] Toggle expands panel
- [ ] SVG tab is active
- [ ] Other tabs are disabled

**Acceptance:**
- [ ] All tests pass

---

## Phase 3: Export and Preview (3 hours)

### T11: Create ExportPreview component
**Estimate:** 1 hour
**Dependencies:** T03
**Owner:** frontend

Create `src/components/architect/ExportPreview.tsx` for SVG display.

**Deliverables:**
- [ ] SVG preview with scaled rendering
- [ ] "No export yet" empty state
- [ ] Copy to clipboard button
- [ ] Download SVG button
- [ ] Loading state during export

**Acceptance:**
- [ ] SVG renders correctly
- [ ] Copy copies SVG string
- [ ] Download triggers file save

---

### T12: Write ExportPreview tests
**Estimate:** 45 min
**Dependencies:** T11
**Owner:** frontend

Create `src/components/architect/ExportPreview.test.tsx`.

**Test Coverage:**
- [ ] Empty state renders
- [ ] SVG preview renders when provided
- [ ] Copy button calls clipboard API
- [ ] Download button creates blob

**Acceptance:**
- [ ] All tests pass
- [ ] Clipboard mocked correctly

---

### T13: Implement exportToSvg action
**Estimate:** 1 hour
**Dependencies:** T05, T11
**Owner:** frontend

Implement the `exportToSvg` action in architectStore using Excalidraw's export API.

**Deliverables:**
- [ ] Call excalidraw `exportToSvg` function
- [ ] Convert blob to string
- [ ] Update store with SVG content
- [ ] Handle loading state
- [ ] Handle errors

**Acceptance:**
- [ ] Export produces valid SVG
- [ ] Loading state works
- [ ] Error handling works

---

### T14: Write export integration test
**Estimate:** 15 min
**Dependencies:** T13
**Owner:** frontend

Add integration test for export flow.

**Test Coverage:**
- [ ] Export action updates store with SVG

**Acceptance:**
- [ ] Test passes with mocked Excalidraw

---

## Phase 4: Page Assembly (2 hours)

### T15: Create ActionBar component
**Estimate:** 45 min
**Dependencies:** T03
**Owner:** frontend

Create `src/components/architect/ActionBar.tsx` with action buttons.

**Deliverables:**
- [ ] Save Draft button (disabled, tooltip "Coming in F03")
- [ ] History button (disabled, tooltip "Coming in F03")
- [ ] Export SVG button (enabled)
- [ ] Translate dropdown (disabled, tooltip "Coming in F02")
- [ ] Fixed bottom positioning

**Acceptance:**
- [ ] Buttons render with correct states
- [ ] Tooltips show on hover
- [ ] Export button triggers export action

---

### T16: Write ActionBar tests
**Estimate:** 15 min
**Dependencies:** T15
**Owner:** frontend

Create `src/components/architect/ActionBar.test.tsx`.

**Test Coverage:**
- [ ] Buttons render
- [ ] Disabled buttons show tooltips
- [ ] Export button click triggers action

**Acceptance:**
- [ ] All tests pass

---

### T17: Create ArchitectBoardPage with layout integration
**Estimate:** 1 hour
**Dependencies:** T05, T07, T09, T11, T15
**Owner:** frontend

Create `src/pages/ArchitectBoardPage.tsx` assembling all components.

**Deliverables:**
- [ ] Session bar with name input
- [ ] 3-panel layout (Tools | Canvas | Output)
- [ ] ActionBar at bottom
- [ ] Keyboard shortcuts (`Ctrl+Shift+E`, `Ctrl+[`, `Ctrl+]`)
- [ ] Full-screen layout with `overflow-hidden` (no Layout padding)
- [ ] Default export for React.lazy() compatibility

**Layout Pattern:**
```tsx
<div className="absolute inset-0 top-16 flex flex-col overflow-hidden">
  {/* Session bar */}
  {/* 3-panel area */}
  {/* Action bar */}
</div>
```

**Acceptance:**
- [ ] Page renders all components
- [ ] Layout matches design (full-screen, no scroll)
- [ ] Keyboard shortcuts work (verify no conflicts with Excalidraw)

---

### T18: Write ArchitectBoardPage tests
**Estimate:** 30 min
**Dependencies:** T17
**Owner:** frontend

Create `src/pages/ArchitectBoardPage.test.tsx`.

**Test Coverage:**
- [ ] Page renders without errors
- [ ] Layout has 3 panels
- [ ] Keyboard shortcuts trigger actions

**Acceptance:**
- [ ] All tests pass

---

## Phase 5: Integration (1 hour)

### T19: Add route and navigation with ErrorBoundary
**Estimate:** 30 min
**Dependencies:** T17
**Owner:** frontend

Update App.tsx and Sidebar.tsx for navigation.

**Deliverables:**
- [ ] Route: `/architect` -> ArchitectBoardPage (lazy loaded)
- [ ] Sidebar link in Workflow section
- [ ] PaintBrushIcon or similar icon
- [ ] ErrorBoundary wrapper around lazy-loaded page
- [ ] Suspense fallback with LoadingSpinner

**Route Setup:**
```tsx
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

**Acceptance:**
- [ ] Navigation works
- [ ] Sidebar link active state works
- [ ] Error boundary catches Excalidraw errors
- [ ] Loading spinner shows while chunk loads

---

### T20: Create barrel export file
**Estimate:** 15 min
**Dependencies:** T05, T07, T09, T11, T15
**Owner:** frontend

Create `src/components/architect/index.ts` with all exports.

**Acceptance:**
- [ ] All components exported
- [ ] No circular dependencies

---

### T21: Final integration test and lint check
**Estimate:** 15 min
**Dependencies:** T19
**Owner:** frontend

Run full test suite and lint.

```bash
npm test
npm run lint
```

**Acceptance:**
- [ ] All tests pass
- [ ] No lint errors
- [ ] Build succeeds

---

## Progress Tracking

### Phase 1: Foundation Setup
- [ ] T01: Install Excalidraw dependency (30 min)
- [ ] T02: Create TypeScript types (30 min)
- [ ] T03: Create architectStore (1 hr)
- [ ] T04: Write architectStore tests (1 hr)

### Phase 2: Core Components
- [ ] T05: Create ArchitectCanvas component with lazy loading (1.5 hr)
- [ ] T06: Write ArchitectCanvas tests (45 min)
- [ ] T07: Create ToolsPanel component (1 hr)
- [ ] T08: Write ToolsPanel tests (30 min)
- [ ] T09: Create OutputPanel component (1 hr)
- [ ] T10: Write OutputPanel tests (30 min)

### Phase 3: Export and Preview
- [ ] T11: Create ExportPreview component (1 hr)
- [ ] T12: Write ExportPreview tests (45 min)
- [ ] T13: Implement exportToSvg action (1 hr)
- [ ] T14: Write export integration test (15 min)

### Phase 4: Page Assembly
- [ ] T15: Create ActionBar component (45 min)
- [ ] T16: Write ActionBar tests (15 min)
- [ ] T17: Create ArchitectBoardPage with layout integration (1 hr)
- [ ] T18: Write ArchitectBoardPage tests (30 min)

### Phase 5: Integration
- [ ] T19: Add route and navigation with ErrorBoundary (30 min)
- [ ] T20: Create barrel export file (15 min)
- [ ] T21: Final integration test and lint check (15 min)

---

## Task Dependencies Diagram

```
T01 (Install)
  |
  v
T02 (Types)
  |
  v
T03 (Store) ----------------+
  |                         |
  v                         v
T04 (Store Tests)     T05 (Canvas + lazy loading)
                        |
         +--------------+--------------+
         |              |              |
         v              v              v
      T06 (Tests)   T07 (Tools)   T09 (Output)
                      |              |
                      v              v
                   T08 (Tests)   T10 (Tests)
                                    |
                                    v
                               T11 (Preview)
                                    |
                                    v
                               T12 (Tests)
                                    |
         +--------------------------+
         |
         v
      T13 (Export Action)
         |
         v
      T14 (Export Test)
         |
         v
      T15 (ActionBar)
         |
         v
      T16 (ActionBar Tests)
         |
         v
      T17 (Page + layout integration)
         |
         v
      T18 (Page Tests)
         |
         v
      T19 (Routes + ErrorBoundary) --> T20 (Barrel) --> T21 (Final)
```

---

## Summary

| Phase | Tasks | Hours | Description |
|-------|-------|-------|-------------|
| 1 | T01-T04 | 3 | Foundation: deps, types, store |
| 2 | T05-T10 | 5 | Core components: Canvas, Panels |
| 3 | T11-T14 | 3 | Export and preview functionality |
| 4 | T15-T18 | 2 | Page assembly and action bar |
| 5 | T19-T21 | 1 | Integration and final testing |
| **Total** | **21** | **14** | |

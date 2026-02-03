# P10-F01: Architect Board Canvas - User Stories

## Epic Summary

**Epic:** P10 - Architect Board
**Feature:** F01 - Architect Board Canvas
**Description:** A drawing canvas page in the HITL UI where users can create diagrams using Excalidraw, with collapsible tool and output panels, and SVG export capability.

## User Stories

### US-01: View Architect Board Page

**As a** developer or architect
**I want** to access a dedicated Architect Board page from the sidebar
**So that** I can create and edit architectural diagrams within the HITL UI

**Acceptance Criteria:**
- [ ] "Architect Board" link appears in Sidebar under Workflow section
- [ ] Clicking the link navigates to `/architect` route
- [ ] Page renders with the expected 3-panel layout
- [ ] Page title displays "Architect Board"
- [ ] Page icon is a paint brush or similar design icon

**Test Cases:**
1. Verify sidebar contains "Architect Board" navigation link
2. Verify clicking link navigates to correct route
3. Verify page component renders without errors
4. Verify page has correct aria-role="main" for accessibility

---

### US-02: Draw on Excalidraw Canvas

**As a** user
**I want** to draw diagrams using familiar drawing tools
**So that** I can visually express architectural concepts

**Acceptance Criteria:**
- [ ] Excalidraw canvas occupies the center panel
- [ ] Canvas fills available space (flex-1)
- [ ] All standard Excalidraw tools are available (rectangle, ellipse, arrow, line, text, freehand)
- [ ] Canvas supports dark theme (matching HITL UI)
- [ ] Drawing state is preserved when toggling side panels
- [ ] Canvas is responsive to window resize

**Test Cases:**
1. Verify Excalidraw component mounts successfully
2. Verify canvas uses dark theme
3. Verify canvas dimensions adjust when panels collapse/expand
4. Verify drawing elements persist after panel toggle
5. Verify onChange callback updates store

---

### US-03: Toggle Tools Panel

**As a** user
**I want** to collapse and expand the left tools panel
**So that** I can maximize canvas space when needed

**Acceptance Criteria:**
- [ ] Tools panel appears on the left side
- [ ] Panel has a collapse/expand toggle button
- [ ] Collapsed width is 48px (w-12), showing only hamburger icon
- [ ] Expanded width is 240px
- [ ] Transition is smooth (300ms duration)
- [ ] Toggle button has appropriate aria-label
- [ ] Panel defaults to collapsed state

**Test Cases:**
1. Verify panel renders in collapsed state by default
2. Verify clicking toggle expands panel to 240px
3. Verify clicking toggle again collapses to 48px
4. Verify aria-label updates based on state
5. Verify CSS transition is applied

---

### US-04: Toggle Output Panel

**As a** user
**I want** to collapse and expand the right output panel
**So that** I can view exports or maximize canvas space

**Acceptance Criteria:**
- [ ] Output panel appears on the right side
- [ ] Panel has a collapse/expand toggle button
- [ ] Collapsed width is 48px (w-12)
- [ ] Expanded width is 320px (w-80)
- [ ] Transition is smooth (300ms duration)
- [ ] Toggle button has appropriate aria-label
- [ ] Panel defaults to collapsed state

**Test Cases:**
1. Verify panel renders in collapsed state by default
2. Verify clicking toggle expands panel to 320px
3. Verify clicking toggle again collapses to 48px
4. Verify aria-label updates based on state
5. Verify CSS transition is applied

---

### US-05: Name Drawing Session

**As a** user
**I want** to give my drawing a name
**So that** I can identify it later when saving or browsing history

**Acceptance Criteria:**
- [ ] Session bar displays editable name field
- [ ] Default name is "Untitled Architecture"
- [ ] Name updates in store on change
- [ ] Name field has character limit indicator (50 chars max)
- [ ] Empty name shows validation warning

**Test Cases:**
1. Verify default name displays "Untitled Architecture"
2. Verify typing updates store state
3. Verify character counter shows remaining chars
4. Verify warning appears when name is empty
5. Verify name persists when navigating away and back (within session)

---

### US-06: Export Drawing to SVG

**As a** user
**I want** to export my drawing as SVG
**So that** it can be processed by the LLM translation feature (F02)

**Acceptance Criteria:**
- [ ] "Export SVG" button appears in action bar
- [ ] Clicking button generates SVG from canvas
- [ ] SVG preview appears in output panel
- [ ] Loading indicator shows during export
- [ ] Error message displays if export fails
- [ ] SVG can be copied to clipboard

**Test Cases:**
1. Verify export button is enabled when canvas has content
2. Verify clicking export calls exportToSvg function
3. Verify loading state displays during export
4. Verify SVG preview renders in output panel
5. Verify copy to clipboard functionality works
6. Verify error toast appears on failure

---

### US-07: View SVG Preview

**As a** user
**I want** to preview the exported SVG
**So that** I can verify it looks correct before translation

**Acceptance Criteria:**
- [ ] SVG preview appears in output panel after export
- [ ] Preview is scaled to fit panel width
- [ ] Preview maintains aspect ratio
- [ ] "Copy SVG" button copies raw SVG to clipboard
- [ ] "Download SVG" button downloads as .svg file
- [ ] Preview updates when canvas changes and re-export occurs

**Test Cases:**
1. Verify SVG renders correctly in preview
2. Verify preview scales to fit container
3. Verify Copy button copies SVG string
4. Verify Download triggers file download
5. Verify preview updates after new export

---

### US-08: View Action Bar

**As a** user
**I want** a consistent action bar at the bottom
**So that** I can quickly access common actions

**Acceptance Criteria:**
- [ ] Action bar spans full width at bottom
- [ ] Contains: Save Draft (disabled), History (disabled), Export SVG, Translate (disabled)
- [ ] Disabled buttons show "Coming soon" tooltip
- [ ] Action bar is fixed and doesn't scroll with content
- [ ] Buttons use consistent styling with rest of UI

**Test Cases:**
1. Verify action bar renders at bottom
2. Verify Save Draft button is disabled with tooltip
3. Verify History button is disabled with tooltip
4. Verify Export SVG button is enabled
5. Verify Translate button is disabled with tooltip

---

### US-09: Handle Empty Canvas State

**As a** user
**I want** clear guidance when the canvas is empty
**So that** I know how to get started

**Acceptance Criteria:**
- [ ] Empty canvas shows helpful prompt
- [ ] Prompt suggests starting to draw
- [ ] Export button is disabled when canvas is empty
- [ ] Output panel shows "No export yet" message

**Test Cases:**
1. Verify empty state message displays
2. Verify Export button is disabled
3. Verify Output panel empty state
4. Verify message disappears when first element drawn

---

### US-10: Keyboard Shortcuts

**As a** a power user
**I want** keyboard shortcuts for common actions
**So that** I can work more efficiently

**Acceptance Criteria:**
- [ ] `Ctrl+Shift+E` / `Cmd+Shift+E` exports to SVG
- [ ] `Ctrl+[` / `Cmd+[` toggles tools panel
- [ ] `Ctrl+]` / `Cmd+]` toggles output panel
- [ ] Excalidraw's built-in shortcuts continue to work
- [ ] Shortcuts do not conflict with Excalidraw shortcuts

**Note:** `Ctrl+Shift+E` is used instead of `Ctrl+E` to avoid conflict with Excalidraw's built-in `E` shortcut for ellipse tool. Verify against Excalidraw's keyboard shortcut reference before implementation.

**Test Cases:**
1. Verify `Ctrl+Shift+E` triggers SVG export
2. Verify `Ctrl+[` toggles tools panel
3. Verify `Ctrl+]` toggles output panel
4. Verify Excalidraw shortcuts (e.g., R for rectangle) still work

---

## Acceptance Test Matrix

| US | Test ID | Description | Priority |
|----|---------|-------------|----------|
| US-01 | AT-01-1 | Sidebar link visible | High |
| US-01 | AT-01-2 | Navigation works | High |
| US-02 | AT-02-1 | Canvas renders | High |
| US-02 | AT-02-2 | Drawing tools work | High |
| US-03 | AT-03-1 | Tools panel toggle | Medium |
| US-04 | AT-04-1 | Output panel toggle | Medium |
| US-05 | AT-05-1 | Name editing | Medium |
| US-06 | AT-06-1 | SVG export | High |
| US-07 | AT-07-1 | SVG preview | High |
| US-08 | AT-08-1 | Action bar renders | Medium |
| US-09 | AT-09-1 | Empty state handling | Low |
| US-10 | AT-10-1 | Keyboard shortcuts | Low |

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All test cases pass
- [ ] Code reviewed and approved
- [ ] No lint errors
- [ ] Responsive design verified (1024px+ width)
- [ ] Dark theme consistent with rest of HITL UI
- [ ] Accessibility: keyboard navigation, aria labels
- [ ] Documentation updated if needed

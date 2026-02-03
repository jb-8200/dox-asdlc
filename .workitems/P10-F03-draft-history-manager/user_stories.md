# P10-F03: Draft History Manager - User Stories

## Epic Summary

As a developer using the Architect Board, I want to save my drawings as drafts and browse my history of past drawings, so that I can resume work on diagrams, track my design iterations, and see which exports were generated from each drawing.

## User Stories

### US-01: Save Current Drawing as Draft

**As a** developer using the Architect Board
**I want** to save my current drawing as a draft
**So that** I can close the browser and resume work later

**Acceptance Criteria:**

1. Save Draft button is enabled in ActionBar when canvas has content
2. Clicking Save Draft opens a dialog with name input field
3. Name field is pre-filled with auto-generated name ("Untitled Draft 1", etc.) if no name exists
4. Existing draft name is shown if editing a previously saved draft
5. Save action persists elements, appState, and thumbnail to database
6. Success toast appears after save completes
7. Dirty flag is cleared after successful save
8. Draft appears in history after save

**Test Scenarios:**

| Scenario | Input | Expected Result |
|----------|-------|-----------------|
| Save new draft with default name | Click Save, accept default | Draft saved as "Untitled Draft 1" |
| Save new draft with custom name | Enter "Auth Flow", click Save | Draft saved as "Auth Flow" |
| Update existing draft | Load draft, modify, save | Same draft ID updated |
| Save empty canvas | No elements drawn | Save button disabled |
| Save with network error | Network offline | Error toast, retry option |

---

### US-02: Load Draft from History

**As a** developer using the Architect Board
**I want** to load a previously saved draft
**So that** I can continue working on an existing diagram

**Acceptance Criteria:**

1. History button in ActionBar opens History modal
2. History modal shows list of saved drafts sorted by updated_at (newest first)
3. Each draft shows: thumbnail preview, name, last updated timestamp
4. Clicking a draft loads it into the canvas
5. Loading a draft updates currentDraftId in store
6. If current canvas has unsaved changes, show UnsavedChangesDialog first
7. Canvas state fully restored including elements and appState

**Test Scenarios:**

| Scenario | Input | Expected Result |
|----------|-------|-----------------|
| Load draft with clean canvas | Click draft | Draft loads immediately |
| Load draft with unsaved changes | Click draft | Warning dialog appears |
| Accept discard changes | Click "Discard" in warning | Draft loads, changes lost |
| Cancel load | Click "Cancel" in warning | Stay on current canvas |
| Load draft with exports | Click draft with exports | Draft loads, exports accessible |

---

### US-03: Delete Draft from History

**As a** developer using the Architect Board
**I want** to delete drafts I no longer need
**So that** my history stays manageable and relevant

**Acceptance Criteria:**

1. Each draft in History modal has a delete button (trash icon)
2. Clicking delete shows confirmation dialog
3. Confirmation dialog shows draft name and warns about export deletion
4. Confirming delete removes draft from database
5. Associated exports are also deleted (CASCADE)
6. Draft disappears from history list after deletion
7. If deleted draft was currently loaded, canvas resets to new state
8. Success toast confirms deletion

**Test Scenarios:**

| Scenario | Input | Expected Result |
|----------|-------|-----------------|
| Delete draft with confirmation | Click delete, confirm | Draft removed from list |
| Cancel delete | Click delete, cancel | Draft remains |
| Delete currently loaded draft | Delete active draft | Canvas resets to empty |
| Delete draft with exports | Delete draft with PNG export | Draft and exports deleted |

---

### US-04: Browse Draft History

**As a** developer using the Architect Board
**I want** to browse all my saved drafts
**So that** I can find and continue working on any previous diagram

**Acceptance Criteria:**

1. History modal displays all user's drafts
2. Drafts show thumbnail preview (200x150 max)
3. Drafts sorted by updated_at descending (newest first)
4. Empty state message when no drafts exist
5. Modal can be closed with X button or clicking outside
6. Each draft shows number of linked exports (badge)
7. Drafts load efficiently from cache when available

**Test Scenarios:**

| Scenario | Input | Expected Result |
|----------|-------|-----------------|
| Open history with drafts | Click History | Modal shows draft list |
| Open history empty | Click History (no drafts) | Empty state message shown |
| View draft thumbnails | Open history | Thumbnails render correctly |
| Close modal | Click X or outside | Modal closes |
| Draft with exports badge | Draft has 3 exports | Badge shows "3 exports" |

---

### US-05: View Exports for Draft

**As a** developer using the Architect Board
**I want** to see which exports were generated from each draft
**So that** I can track my diagram translation history

**Acceptance Criteria:**

1. Drafts in history show export count badge
2. Expanding or clicking draft shows linked exports
3. Exports show: format icon, creation timestamp
4. Export formats: SVG, PNG, Mermaid, Draw.io
5. Clicking export shows preview or downloads content
6. Exports sorted by created_at descending

**Test Scenarios:**

| Scenario | Input | Expected Result |
|----------|-------|-----------------|
| View draft with no exports | Open draft details | "No exports yet" message |
| View draft with PNG export | Open draft details | PNG export shown with icon |
| View draft with multiple exports | Open draft details | All exports listed |
| Download export | Click export | Content downloaded/previewed |

---

### US-06: Unsaved Changes Warning

**As a** developer using the Architect Board
**I want** to be warned before losing unsaved changes
**So that** I don't accidentally lose my work

**Acceptance Criteria:**

1. Any canvas change sets dirty flag (isDirty = true)
2. Warning appears when: loading another draft, creating new, navigating away
3. Warning dialog shows options: Save, Discard, Cancel
4. "Save" saves current work then continues action
5. "Discard" proceeds without saving
6. "Cancel" returns to canvas without action
7. Browser beforeunload event shows native warning when dirty

**Test Scenarios:**

| Scenario | Input | Expected Result |
|----------|-------|-----------------|
| Navigate away dirty | Navigate with unsaved | Browser warning appears |
| Load draft dirty | Click draft with unsaved | UnsavedChangesDialog appears |
| Save then continue | Click "Save" in dialog | Saves, then loads requested draft |
| Discard changes | Click "Discard" | Changes lost, action proceeds |
| Cancel warning | Click "Cancel" | Stay on current canvas |
| No warning if clean | Navigate with saved | No warning, action proceeds |

---

### US-07: Auto-Save Drafts

**As a** developer using the Architect Board
**I want** my work auto-saved periodically
**So that** I don't lose changes if I forget to save manually

**Acceptance Criteria:**

1. Auto-save triggers every 2 minutes when canvas is dirty
2. Auto-save only runs if draft has been saved at least once (has ID)
3. New/unsaved drafts do not auto-save (require explicit first save)
4. Debounce prevents save during rapid changes (500ms quiet period)
5. Auto-save shows subtle indicator (not intrusive toast)
6. Failed auto-save retries on next interval
7. Auto-save clears dirty flag on success

**Test Scenarios:**

| Scenario | Input | Expected Result |
|----------|-------|-----------------|
| Auto-save existing draft | Wait 2 minutes dirty | Draft auto-saved |
| No auto-save for new | New canvas, wait | No auto-save triggered |
| Rapid changes | Draw quickly | Debounce prevents spam saves |
| Auto-save failure | Network error | Retry next interval |
| Manual save resets timer | Save manually | Auto-save timer resets |

---

### US-08: Create New Draft

**As a** developer using the Architect Board
**I want** to start a new blank drawing
**So that** I can create a fresh diagram without loading an old one

**Acceptance Criteria:**

1. "New" button in ActionBar creates blank canvas
2. If current canvas dirty, show UnsavedChangesDialog first
3. Creating new clears currentDraftId (no longer editing existing)
4. Canvas resets: empty elements, default appState
5. Name resets to empty (will auto-generate on first save)
6. Dirty flag cleared after new

**Test Scenarios:**

| Scenario | Input | Expected Result |
|----------|-------|-----------------|
| New from clean canvas | Click New | Canvas clears |
| New from dirty canvas | Click New (unsaved) | Warning dialog appears |
| Save then new | Click Save in warning | Saves, then creates new |
| New clears draft ID | Create new | currentDraftId = null |

---

## Story Dependencies

```
US-01 (Save Draft)
  |
  +---> US-02 (Load Draft) - requires drafts to exist
  |
  +---> US-03 (Delete Draft) - requires drafts to exist
  |
  +---> US-04 (Browse History) - requires drafts to exist
          |
          +---> US-05 (View Exports) - requires history modal

US-06 (Unsaved Warning) - independent, used by US-02, US-08

US-07 (Auto-Save) - depends on US-01 save infrastructure

US-08 (Create New) - depends on US-06 for warning
```

## Priority Order

1. **P0 (Critical):** US-01 Save Draft, US-02 Load Draft - Core functionality
2. **P1 (High):** US-04 Browse History, US-06 Unsaved Warning - Essential UX
3. **P2 (Medium):** US-03 Delete Draft, US-07 Auto-Save - Important features
4. **P3 (Lower):** US-05 View Exports, US-08 Create New - Enhanced UX

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Unit tests written and passing (>80% coverage)
- [ ] Integration tests for API endpoints
- [ ] Manual QA verification
- [ ] Code reviewed and approved
- [ ] No regressions in existing F01/F02 functionality
- [ ] Performance targets met (save <500ms, load <300ms)
- [ ] Accessibility requirements met (keyboard navigation, ARIA labels)

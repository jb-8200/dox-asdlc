# P10-F02: Diagram Translation - Task Breakdown

## Overview

Feature: Diagram Translation for Architect Board
Total Estimated Time: ~16 hours
Dependencies: P10-F01 (Architect Board Canvas) - must be complete

## Phase 1: Backend API Foundation (4 hours)

### T01: Create Pydantic models for architect API
**Estimate:** 30 min
**Dependencies:** None
**Owner:** backend

Create `src/orchestrator/api/models/architect.py` with request/response models.

**Deliverables:**
- [ ] `TranslateRequest` model with svgContent, format, options
- [ ] `TranslateResponse` model with content, format, modelUsed, metadata
- [ ] `TranslateErrorResponse` model with error, code, details
- [ ] `ExportFormat` enum ('png', 'mmd', 'drawio')

**Acceptance:**
- [ ] Models validate correctly
- [ ] All fields have proper types and descriptions

---

### T02: Create architect service with LLM integration
**Estimate:** 1.5 hours
**Dependencies:** T01
**Owner:** backend

Create `src/orchestrator/services/architect_service.py` for translation logic.

**Deliverables:**
- [ ] `ArchitectService` class
- [ ] `translate_to_png()` method using Gemini image generation
- [ ] `translate_to_mermaid()` method using text LLM
- [ ] `translate_to_drawio()` method using text LLM
- [ ] Integration with LLMConfigService to fetch Design Agent config
- [ ] Prompts for Mermaid and Draw.io translation

**Key Implementation:**
```python
async def translate(self, svg_content: str, format: ExportFormat, options: dict = None) -> TranslateResponse:
    # 1. Get Design Agent config
    design_config = await self.llm_config_service.get_agent_config("design")

    # 2. Route to appropriate translation method
    if format == ExportFormat.PNG:
        return await self._translate_to_png(svg_content, design_config, options)
    elif format == ExportFormat.MERMAID:
        return await self._translate_to_mermaid(svg_content, design_config)
    elif format == ExportFormat.DRAWIO:
        return await self._translate_to_drawio(svg_content, design_config)
```

**Acceptance:**
- [ ] Service instantiates without errors
- [ ] Design Agent config is fetched correctly
- [ ] Translation methods handle different providers

---

### T03: Write architect service tests
**Estimate:** 1 hour
**Dependencies:** T02
**Owner:** backend

Create `tests/unit/orchestrator/services/test_architect_service.py`.

**Test Coverage:**
- [ ] translate_to_png with mocked Gemini response
- [ ] translate_to_mermaid with mocked LLM response
- [ ] translate_to_drawio with mocked LLM response
- [ ] Error handling for missing config
- [ ] Error handling for LLM failures

**Acceptance:**
- [ ] All tests pass
- [ ] Mocked responses cover success and error cases

---

### T04: Create architect API route
**Estimate:** 45 min
**Dependencies:** T02
**Owner:** backend

Create `src/orchestrator/routes/architect_api.py` with translation endpoint.

**Deliverables:**
- [ ] `POST /api/architect/translate` endpoint
- [ ] Request validation
- [ ] Error response handling
- [ ] Dependency injection for ArchitectService

**Acceptance:**
- [ ] Endpoint responds to valid requests
- [ ] Invalid requests return 400 with details
- [ ] Server errors return 500 with error code

---

### T05: Write architect API route tests
**Estimate:** 30 min
**Dependencies:** T04
**Owner:** backend

Create `tests/unit/orchestrator/routes/test_architect_api.py`.

**Test Coverage:**
- [ ] Valid translation request returns 200
- [ ] Invalid format returns 400
- [ ] Missing svgContent returns 400
- [ ] Service errors return appropriate status

**Acceptance:**
- [ ] All tests pass
- [ ] Request validation is comprehensive

---

### T06: Register architect router in main.py
**Estimate:** 15 min
**Dependencies:** T04
**Owner:** backend

Update `src/orchestrator/main.py` to include the architect router.

**Deliverables:**
- [ ] Import architect_api router
- [ ] Register with app.include_router
- [ ] Add logging for new endpoint

**Acceptance:**
- [ ] Router is registered
- [ ] Endpoint appears in OpenAPI docs

---

## Phase 2: Frontend API and Types (2 hours)

### T07: Extend architect types for translation
**Estimate:** 30 min
**Dependencies:** P10-F01 complete
**Owner:** frontend

Update `docker/hitl-ui/src/api/types/architect.ts` with translation types.

**Deliverables:**
- [ ] `TranslateRequest` interface
- [ ] `TranslateResponse` interface
- [ ] `TranslateOptions` interface
- [ ] `TranslationError` type with error codes

**Acceptance:**
- [ ] Types compile without errors
- [ ] Types match backend models

---

### T08: Implement architect API client
**Estimate:** 45 min
**Dependencies:** T07
**Owner:** frontend

Update `docker/hitl-ui/src/api/architect.ts` with translation function.

**Deliverables:**
- [ ] `translateDiagram(svgContent, format, options)` function
- [ ] Error handling for API errors
- [ ] Request timeout handling (translations may take time)
- [ ] Mock implementation for development

**Acceptance:**
- [ ] Function calls API endpoint correctly
- [ ] Errors are properly typed and handled

---

### T09: Write architect API client tests
**Estimate:** 30 min
**Dependencies:** T08
**Owner:** frontend

Create `docker/hitl-ui/src/api/architect.test.ts`.

**Test Coverage:**
- [ ] translateDiagram calls correct endpoint
- [ ] Response is correctly typed
- [ ] Errors are handled gracefully
- [ ] Mock mode works

**Acceptance:**
- [ ] All tests pass

---

### T10: Create architect API mock data
**Estimate:** 15 min
**Dependencies:** T08
**Owner:** frontend

Create `docker/hitl-ui/src/api/mocks/architect.ts`.

**Deliverables:**
- [ ] Mock PNG response (base64 placeholder)
- [ ] Mock Mermaid response (sample flowchart)
- [ ] Mock Draw.io XML response (sample structure)
- [ ] Configurable delay for loading state testing

**Acceptance:**
- [ ] Mocks return valid shaped data
- [ ] Delay simulates real API latency

---

## Phase 3: Store Extensions (2 hours)

### T11: Extend architectStore with translation state
**Estimate:** 1 hour
**Dependencies:** T08, P10-F01 complete
**Owner:** frontend

Update `docker/hitl-ui/src/stores/architectStore.ts` with translation state.

**Deliverables:**
- [ ] `isTranslating` state
- [ ] `translationError` state
- [ ] `translatedContent` state (png, mmd, drawio)
- [ ] `activeOutputTab` state
- [ ] `translateTo(format)` action
- [ ] `setActiveOutputTab(tab)` action
- [ ] `clearTranslation(format?)` action

**Acceptance:**
- [ ] State updates correctly during translation flow
- [ ] Error handling resets loading state
- [ ] Tab state persists correctly

---

### T12: Write architectStore translation tests
**Estimate:** 1 hour
**Dependencies:** T11
**Owner:** frontend

Update `docker/hitl-ui/src/stores/architectStore.test.ts` with translation tests.

**Test Coverage:**
- [ ] translateTo sets isTranslating to true
- [ ] Successful translation updates translatedContent
- [ ] Failed translation sets translationError
- [ ] setActiveOutputTab updates state
- [ ] clearTranslation clears specific or all content

**Acceptance:**
- [ ] All tests pass
- [ ] Translation flow coverage is complete

---

## Phase 4: UI Component Updates (5 hours)

### T13: Install react-syntax-highlighter
**Estimate:** 15 min
**Dependencies:** None
**Owner:** frontend

Install syntax highlighting package for Mermaid/XML preview.

```bash
cd docker/hitl-ui
npm install react-syntax-highlighter
npm install -D @types/react-syntax-highlighter
```

**Acceptance:**
- [ ] Package installed
- [ ] Build succeeds
- [ ] No TypeScript errors

---

### T14: Create FormatTabContent component
**Estimate:** 1 hour
**Dependencies:** T13
**Owner:** frontend

Create `docker/hitl-ui/src/components/architect/FormatTabContent.tsx`.

**Deliverables:**
- [ ] Props: content, format, loading, error, onCopy, onDownload
- [ ] PNG rendering with img tag
- [ ] SVG rendering (existing)
- [ ] Mermaid syntax highlighting
- [ ] Draw.io XML syntax highlighting
- [ ] Loading spinner state
- [ ] Error message state
- [ ] Empty state ("Not translated yet")

**Acceptance:**
- [ ] All formats render correctly
- [ ] Loading/error states display appropriately
- [ ] Copy/download buttons work

---

### T15: Write FormatTabContent tests
**Estimate:** 45 min
**Dependencies:** T14
**Owner:** frontend

Create `docker/hitl-ui/src/components/architect/FormatTabContent.test.tsx`.

**Test Coverage:**
- [ ] PNG format renders img tag
- [ ] Mermaid format has syntax highlighting
- [ ] XML format has syntax highlighting
- [ ] Loading state shows spinner
- [ ] Error state shows message
- [ ] Copy button triggers callback

**Acceptance:**
- [ ] All tests pass

---

### T16: Update ExportPreview for multi-format support
**Estimate:** 45 min
**Dependencies:** T14
**Owner:** frontend

Update `docker/hitl-ui/src/components/architect/ExportPreview.tsx`.

**Deliverables:**
- [ ] Use FormatTabContent internally
- [ ] Pass format prop to determine rendering
- [ ] Handle all format types
- [ ] Update copy/download for different formats

**Acceptance:**
- [ ] All formats work through ExportPreview
- [ ] Copy produces correct content type
- [ ] Download produces correct file extension

---

### T17: Write ExportPreview multi-format tests
**Estimate:** 30 min
**Dependencies:** T16
**Owner:** frontend

Update `docker/hitl-ui/src/components/architect/ExportPreview.test.tsx`.

**Test Coverage:**
- [ ] SVG format works (existing)
- [ ] PNG format creates correct download
- [ ] Mermaid format creates .mmd download
- [ ] Draw.io format creates .xml download

**Acceptance:**
- [ ] All tests pass

---

### T18: Update ActionBar with Translate dropdown
**Estimate:** 1 hour
**Dependencies:** T11
**Owner:** frontend

Update `docker/hitl-ui/src/components/architect/ActionBar.tsx`.

**Deliverables:**
- [ ] Remove disabled state from Translate dropdown
- [ ] Add dropdown items: PNG Image, Mermaid, Draw.io XML
- [ ] Connect onSelect to translateTo action
- [ ] Disable dropdown when no SVG exported
- [ ] Disable dropdown during translation (isTranslating)
- [ ] Show loading indicator on button during translation

**Acceptance:**
- [ ] Dropdown works when enabled
- [ ] Disabled states work correctly
- [ ] Translation triggers on selection

---

### T19: Write ActionBar translation tests
**Estimate:** 30 min
**Dependencies:** T18
**Owner:** frontend

Update `docker/hitl-ui/src/components/architect/ActionBar.test.tsx`.

**Test Coverage:**
- [ ] Dropdown enabled when SVG exported
- [ ] Dropdown disabled when no SVG
- [ ] Dropdown disabled during translation
- [ ] Selection triggers translateTo action

**Acceptance:**
- [ ] All tests pass

---

### T20: Update OutputPanel with all format tabs
**Estimate:** 45 min
**Dependencies:** T14, T11
**Owner:** frontend

Update `docker/hitl-ui/src/components/architect/OutputPanel.tsx`.

**Deliverables:**
- [ ] Enable all format tabs (SVG, PNG, Mermaid, Draw.io)
- [ ] Show "Ready" badge on tabs with content
- [ ] Show loading indicator on tab during translation
- [ ] Connect tab selection to setActiveOutputTab
- [ ] Render FormatTabContent for active tab

**Acceptance:**
- [ ] All tabs render and are clickable
- [ ] Tab content switches correctly
- [ ] Badges appear when translations are ready

---

### T21: Write OutputPanel multi-tab tests
**Estimate:** 30 min
**Dependencies:** T20
**Owner:** frontend

Update `docker/hitl-ui/src/components/architect/OutputPanel.test.tsx`.

**Test Coverage:**
- [ ] All tabs render
- [ ] Tab click switches content
- [ ] Ready badge appears after translation
- [ ] Loading state shows during translation

**Acceptance:**
- [ ] All tests pass

---

## Phase 5: Integration and Polish (3 hours)

### T22: Create toast notifications for translation events
**Estimate:** 30 min
**Dependencies:** T11
**Owner:** frontend

Add toast notifications for translation success/error.

**Deliverables:**
- [ ] Success toast when translation completes
- [ ] Error toast with message on failure
- [ ] Toast includes "Retry" action for errors

**Acceptance:**
- [ ] Toasts appear at appropriate times
- [ ] Error toasts are actionable

---

### T23: Add keyboard shortcuts for translation
**Estimate:** 30 min
**Dependencies:** T18
**Owner:** frontend

Update ArchitectBoardPage with translation keyboard shortcuts.

**Deliverables:**
- [ ] `Ctrl+Shift+P` - Translate to PNG
- [ ] `Ctrl+Shift+M` - Translate to Mermaid
- [ ] `Ctrl+Shift+D` - Translate to Draw.io

**Acceptance:**
- [ ] Shortcuts trigger translation
- [ ] Shortcuts documented in UI (tooltip or help)

---

### T24: Backend integration test
**Estimate:** 45 min
**Dependencies:** T01-T06
**Owner:** backend

Create integration test for full translation flow.

**Test Coverage:**
- [ ] POST /api/architect/translate with PNG format
- [ ] POST /api/architect/translate with MMD format
- [ ] POST /api/architect/translate with DrawIO format
- [ ] Error handling for invalid input
- [ ] Design Agent config is used

**Acceptance:**
- [ ] All integration tests pass

---

### T25: Frontend E2E test
**Estimate:** 45 min
**Dependencies:** T18-T21
**Owner:** frontend

Create E2E test for translation user flow.

**Test Coverage:**
- [ ] User draws on canvas
- [ ] User exports to SVG
- [ ] User clicks Translate > PNG
- [ ] PNG tab shows result
- [ ] User downloads PNG

**Acceptance:**
- [ ] E2E test passes

---

### T26: Final lint and build verification
**Estimate:** 30 min
**Dependencies:** All previous tasks
**Owner:** frontend, backend

Run full test suite and build.

```bash
# Backend
pytest tests/ -v

# Frontend
npm test
npm run lint
npm run build
```

**Acceptance:**
- [ ] All tests pass
- [ ] No lint errors
- [ ] Build succeeds

---

## Progress Tracking

### Phase 1: Backend API Foundation
- [ ] T01: Create Pydantic models (30 min)
- [ ] T02: Create architect service (1.5 hr)
- [ ] T03: Write architect service tests (1 hr)
- [ ] T04: Create architect API route (45 min)
- [ ] T05: Write architect API route tests (30 min)
- [ ] T06: Register architect router (15 min)

### Phase 2: Frontend API and Types
- [x] T07: Extend architect types (30 min)
- [x] T08: Implement architect API client (45 min)
- [x] T09: Write architect API client tests (30 min)
- [x] T10: Create architect API mock data (15 min)

### Phase 3: Store Extensions
- [x] T11: Extend architectStore with translation state (1 hr)
- [x] T12: Write architectStore translation tests (1 hr)

### Phase 4: UI Component Updates
- [ ] T13: Install react-syntax-highlighter (15 min) - SKIPPED: Used existing prismjs
- [x] T14: Create FormatTabContent component (1 hr)
- [x] T15: Write FormatTabContent tests (45 min)
- [ ] T16: Update ExportPreview for multi-format (45 min) - SKIPPED: Using FormatTabContent directly
- [ ] T17: Write ExportPreview multi-format tests (30 min) - SKIPPED: Using FormatTabContent tests
- [x] T18: Update ActionBar with Translate dropdown (1 hr)
- [x] T19: Write ActionBar translation tests (30 min)
- [x] T20: Update OutputPanel with all format tabs (45 min)
- [x] T21: Write OutputPanel multi-tab tests (30 min)

### Phase 5: Integration and Polish
- [ ] T22: Create toast notifications (30 min)
- [ ] T23: Add keyboard shortcuts (30 min)
- [ ] T24: Backend integration test (45 min)
- [ ] T25: Frontend E2E test (45 min)
- [ ] T26: Final lint and build verification (30 min)

---

## Task Dependencies Diagram

```
Phase 1 (Backend)
T01 (Models)
  |
  v
T02 (Service) ----------+
  |                     |
  v                     v
T03 (Service Tests)   T04 (API Route)
                        |
                        v
                      T05 (API Tests)
                        |
                        v
                      T06 (Register Router)

Phase 2 (Frontend API)
T07 (Types) --------> T08 (API Client)
                        |
                        v
                      T09 (API Tests)
                        |
                        v
                      T10 (Mocks)

Phase 3 (Store)
T08 (API Client) ---> T11 (Store Extensions)
                        |
                        v
                      T12 (Store Tests)

Phase 4 (UI Components)
T13 (Syntax Highlighter)
  |
  v
T14 (FormatTabContent) ---> T16 (ExportPreview) ---> T17 (Tests)
  |
  v
T15 (Tests)

T11 (Store) ---> T18 (ActionBar) ---> T19 (Tests)
      |
      +-------> T20 (OutputPanel) ---> T21 (Tests)

Phase 5 (Integration)
T11 + T18 ---> T22 (Toast Notifications)
T18 ---------> T23 (Keyboard Shortcuts)
T01-T06 -----> T24 (Backend Integration Test)
T18-T21 -----> T25 (Frontend E2E Test)
All ----------> T26 (Final Verification)
```

---

## Summary

| Phase | Tasks | Hours | Description |
|-------|-------|-------|-------------|
| 1 | T01-T06 | 4 | Backend API: models, service, routes |
| 2 | T07-T10 | 2 | Frontend API: types, client, mocks |
| 3 | T11-T12 | 2 | Store: translation state and actions |
| 4 | T13-T21 | 5 | UI: components for multi-format translation |
| 5 | T22-T26 | 3 | Integration: tests, polish, verification |
| **Total** | **26** | **16** | |

---

## Notes

- **Dependency on F01:** This feature requires P10-F01 (Architect Board Canvas) to be complete, specifically the architectStore and SVG export functionality.

- **LLM Configuration:** Backend MUST use the Design Agent configuration from `/api/llm/agents/design`. Do NOT hardcode model names.

- **Gemini Image Generation:** If the Design Agent is configured with a Google provider and an image-capable model (e.g., gemini-2.5-flash-preview-image-generation), PNG translation will use Gemini. Otherwise, PNG translation may return an error indicating Gemini is required.

- **Testing Strategy:** Use mocked LLM responses for unit tests. Backend integration tests may use real LLM calls if credentials are available in CI environment.

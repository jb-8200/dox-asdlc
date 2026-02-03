# P10-F02: Diagram Translation - User Stories

## Epic Summary

As an architect using the Architect Board, I want to translate my hand-drawn diagrams into professional formats so that I can include them in documentation, share them with colleagues, and import them into other diagramming tools.

## User Stories

### US-01: Translate Drawing to PNG Image

**As a** user creating architecture diagrams,
**I want to** convert my Excalidraw drawing to a polished PNG image,
**So that** I can include it in documentation, presentations, or share via chat.

**Acceptance Criteria:**

1. Given I have an SVG export from my drawing
   When I click Translate > PNG Image
   Then a loading indicator appears while translation is in progress

2. Given translation is in progress
   When the LLM generates the image
   Then the PNG tab shows a "Ready" badge

3. Given the PNG is ready
   When I click the PNG tab
   Then I see a preview of the generated image

4. Given I'm viewing the PNG preview
   When I click "Copy"
   Then the image is copied to my clipboard

5. Given I'm viewing the PNG preview
   When I click "Download"
   Then a PNG file is downloaded to my computer

6. Given the Gemini image model is not configured
   When I attempt PNG translation
   Then I see an error message explaining the configuration requirement

**Test Cases:**
- TC-01.1: PNG translation with valid SVG content
- TC-01.2: PNG copy to clipboard functionality
- TC-01.3: PNG download creates valid image file
- TC-01.4: Error handling when Gemini not configured
- TC-01.5: Loading state during translation

---

### US-02: Translate Drawing to Mermaid Syntax

**As a** developer creating architecture diagrams,
**I want to** convert my drawing to Mermaid diagram syntax,
**So that** I can embed it in Markdown documentation and version control it as text.

**Acceptance Criteria:**

1. Given I have an SVG export from my drawing
   When I click Translate > Mermaid
   Then a loading indicator appears while translation is in progress

2. Given translation completes successfully
   When I click the Mermaid tab
   Then I see syntax-highlighted Mermaid code

3. Given I'm viewing the Mermaid preview
   When I click "Copy"
   Then the Mermaid code is copied to my clipboard

4. Given I'm viewing the Mermaid preview
   When I click "Download"
   Then a .mmd file is downloaded

5. Given the generated Mermaid code
   When I paste it into Mermaid Live Editor
   Then it renders without syntax errors

**Test Cases:**
- TC-02.1: Mermaid translation produces valid syntax
- TC-02.2: Syntax highlighting renders correctly
- TC-02.3: Copy copies correct Mermaid content
- TC-02.4: Download creates .mmd file
- TC-02.5: Complex diagrams translate to appropriate Mermaid type

---

### US-03: Translate Drawing to Draw.io XML

**As a** user who uses Draw.io for diagram editing,
**I want to** convert my Excalidraw drawing to Draw.io XML format,
**So that** I can import it into Draw.io/diagrams.net for further editing.

**Acceptance Criteria:**

1. Given I have an SVG export from my drawing
   When I click Translate > Draw.io XML
   Then a loading indicator appears while translation is in progress

2. Given translation completes successfully
   When I click the Draw.io tab
   Then I see syntax-highlighted XML code

3. Given I'm viewing the Draw.io preview
   When I click "Copy"
   Then the XML code is copied to my clipboard

4. Given I'm viewing the Draw.io preview
   When I click "Download"
   Then a .xml file is downloaded

5. Given the generated Draw.io XML
   When I import it into diagrams.net
   Then it imports without errors and shows the diagram structure

**Test Cases:**
- TC-03.1: Draw.io translation produces valid XML
- TC-03.2: XML syntax highlighting renders correctly
- TC-03.3: Copy copies correct XML content
- TC-03.4: Download creates .xml file
- TC-03.5: XML imports into diagrams.net successfully

---

### US-04: View Translation Loading State

**As a** user waiting for translation,
**I want to** see clear progress indication,
**So that** I know the system is working and approximately how long to wait.

**Acceptance Criteria:**

1. Given I initiate a translation
   When the request is processing
   Then I see a spinner/loading indicator in the output panel

2. Given translation is in progress
   When I switch to the target format tab
   Then I see a loading state in the preview area

3. Given translation is in progress
   When I try to start another translation
   Then the Translate button is disabled

4. Given translation completes
   When I view the result
   Then the loading indicator is replaced with content

**Test Cases:**
- TC-04.1: Loading spinner appears during translation
- TC-04.2: Translate button disabled during active translation
- TC-04.3: Loading state clears on completion
- TC-04.4: Loading state clears on error

---

### US-05: Handle Translation Errors Gracefully

**As a** user experiencing translation issues,
**I want to** see clear error messages and recovery options,
**So that** I can understand what went wrong and try again.

**Acceptance Criteria:**

1. Given a network error during translation
   When the request fails
   Then I see an error message with a "Retry" button

2. Given the LLM returns an error
   When translation fails
   Then I see an error message explaining the issue

3. Given a rate limit is hit
   When translation fails due to rate limiting
   Then I see a message with cooldown information

4. Given I haven't exported SVG first
   When I click Translate
   Then I see a message prompting me to export SVG first

5. Given an error occurred
   When I click "Dismiss"
   Then the error message clears

**Test Cases:**
- TC-05.1: Network error shows retry option
- TC-05.2: LLM error displays error message
- TC-05.3: Rate limit shows cooldown timer
- TC-05.4: Missing SVG shows helpful guidance
- TC-05.5: Error can be dismissed

---

### US-06: Translate Dropdown in ActionBar

**As a** user of the Architect Board,
**I want to** access translation options from a dropdown menu,
**So that** I can easily choose the format I need.

**Acceptance Criteria:**

1. Given I'm on the Architect Board page
   When I look at the ActionBar
   Then I see a "Translate" dropdown button

2. Given I have exported SVG
   When I click the Translate dropdown
   Then I see options: PNG Image, Mermaid, Draw.io XML

3. Given I have not exported SVG yet
   When I view the Translate dropdown
   Then it is disabled with a tooltip "Export SVG first"

4. Given translation is in progress
   When I view the Translate dropdown
   Then it is disabled with a loading indicator

5. Given I select a format from the dropdown
   When the translation starts
   Then the OutputPanel switches to that format's tab

**Test Cases:**
- TC-06.1: Dropdown renders with correct options
- TC-06.2: Dropdown disabled when no SVG exported
- TC-06.3: Dropdown disabled during translation
- TC-06.4: Selecting format initiates translation
- TC-06.5: Tab switches on translation start

---

### US-07: Multi-Format Tab Interface

**As a** user viewing translation results,
**I want to** switch between different format outputs,
**So that** I can compare and use multiple formats from the same drawing.

**Acceptance Criteria:**

1. Given I'm viewing the OutputPanel
   When translations are available
   Then I see tabs for SVG, PNG, Mermaid, Draw.io

2. Given a format has been translated
   When I view that tab
   Then I see a "Ready" badge on the tab

3. Given I click a format tab
   When the tab content loads
   Then I see the appropriate preview for that format

4. Given I switch tabs
   When I return to a previously translated format
   Then the content is still available (cached in store)

**Test Cases:**
- TC-07.1: All format tabs render
- TC-07.2: Ready badge appears after translation
- TC-07.3: Tab content switches correctly
- TC-07.4: Translations are cached in session

---

## Definition of Done

- [ ] All user stories have passing acceptance tests
- [ ] Backend API endpoint implemented and tested
- [ ] Frontend components updated and tested
- [ ] Unit test coverage > 80%
- [ ] Integration tests pass
- [ ] No TypeScript errors
- [ ] Lint passes
- [ ] Design Agent configuration used (not hardcoded models)
- [ ] Error states clearly communicated to user
- [ ] Loading states provide feedback during translation

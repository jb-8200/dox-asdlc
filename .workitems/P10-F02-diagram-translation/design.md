# P10-F02: Diagram Translation - Technical Design

## Overview

P10-F02 enables translating user drawings from the Architect Board (F01) into different formats using LLM services. This feature builds on F01's SVG export capability to provide professional diagram outputs in multiple formats.

### Goals

1. Translate SVG drawings to PNG/JPG images via Gemini image generation
2. Convert SVG drawings to Mermaid diagram syntax via LLM text generation
3. Convert SVG drawings to Draw.io XML format via LLM text generation
4. Provide loading states and error handling during translation
5. Enable the "Translate" dropdown in F01's ActionBar
6. Follow existing HITL UI patterns for API calls and state management

### Non-Goals (Deferred to F03)

- Draft persistence to database
- History browsing and draft management
- Redis caching for translations
- Translation quality feedback/regeneration

## Technical Approach

### Architecture Overview

```
+------------------+     +------------------+     +------------------+
|   ActionBar      |     |  architectStore  |     |  Backend API     |
|   Translate btn  | --> |  translateDiagram| --> |  /api/architect/ |
+------------------+     +------------------+     +------------------+
                                                          |
                         +------------------+             |
                         |  OutputPanel     |             v
                         |  Format tabs     | <--  +------------------+
                         +------------------+      |  LLM Service     |
                                                   |  (Gemini/Claude) |
                                                   +------------------+
```

### LLM Model Configuration

**IMPORTANT:** Model names MUST NOT be hardcoded. The backend reads the configured model from the "Design Agent" admin config via `/api/llm/agents/design`.

**Backend Flow:**
1. Receive translation request with SVG content and target format
2. Fetch Design Agent config from LLM config service
3. Use configured provider/model for translation
4. For PNG: Use Gemini image generation (if configured)
5. For Mermaid/Draw.io: Use configured text model

### Gemini Image Generation

Gemini models support native image generation via the `imagen` capability:

**API Pattern:**
```python
import google.generativeai as genai

# Configure with API key from secrets
genai.configure(api_key=design_agent_config.api_key)

# Use the configured model (e.g., gemini-2.5-flash-preview-image-generation)
model = genai.GenerativeModel(design_agent_config.model)

response = model.generate_content([
    "Create a clean, professional diagram image based on this SVG structure...",
    svg_content,
])

# Response contains base64 image in inline_data.data
image_base64 = response.parts[0].inline_data.data
```

**Key Features:**
- Returns base64-encoded PNG/JPG images
- Supports text-to-image and image editing
- SynthID watermark on all generated images
- Multi-turn conversations for iterative refinement (future)

### Text Generation for Mermaid/Draw.io

**Prompt Strategy - Mermaid:**
```
Analyze this SVG diagram and convert it to Mermaid syntax.

SVG Content:
{svg_content}

Instructions:
1. Identify shapes, connections, and text labels
2. Determine the best Mermaid diagram type (flowchart, sequence, class, etc.)
3. Generate valid Mermaid syntax that reproduces the diagram structure
4. Use appropriate styling and node shapes

Output ONLY the Mermaid code, no explanations.
```

**Prompt Strategy - Draw.io XML:**
```
Analyze this SVG diagram and convert it to Draw.io (mxGraph) XML format.

SVG Content:
{svg_content}

Instructions:
1. Identify all shapes with their positions and dimensions
2. Identify all connections/arrows between shapes
3. Extract text labels
4. Generate valid mxGraph XML structure
5. Preserve relative positioning

Output ONLY the XML code, no explanations.
```

### API Design

**Endpoint:** `POST /api/architect/translate`

**Request:**
```typescript
interface TranslateRequest {
  svgContent: string;           // Raw SVG string from Excalidraw export
  format: 'png' | 'mmd' | 'drawio';
  options?: {
    size?: '2k' | '4k';         // For PNG only
    diagramType?: string;        // Hint for Mermaid (flowchart, sequence, etc.)
  };
}
```

**Response:**
```typescript
interface TranslateResponse {
  content: string;              // Base64 for PNG, raw string for Mermaid/Draw.io
  format: 'png' | 'mmd' | 'drawio';
  modelUsed: string;            // For transparency (e.g., "gemini-2.5-flash")
  metadata?: {
    width?: number;             // For PNG
    height?: number;            // For PNG
    diagramType?: string;       // For Mermaid
  };
}
```

**Error Response:**
```typescript
interface TranslateErrorResponse {
  error: string;
  code: 'MODEL_ERROR' | 'INVALID_FORMAT' | 'SVG_PARSE_ERROR' | 'RATE_LIMIT';
  details?: string;
}
```

### Frontend Integration

**architectStore extensions:**

```typescript
interface ArchitectState {
  // ... existing F01 state ...

  // Translation state
  isTranslating: boolean;
  translationError: string | null;
  translatedContent: {
    png: string | null;         // Base64 image
    mmd: string | null;         // Mermaid syntax
    drawio: string | null;      // Draw.io XML
  };
  activeOutputTab: 'svg' | 'png' | 'mmd' | 'drawio';

  // Actions
  translateTo: (format: ExportFormat) => Promise<void>;
  setActiveOutputTab: (tab: 'svg' | 'png' | 'mmd' | 'drawio') => void;
  clearTranslation: (format?: ExportFormat) => void;
}
```

**API Client:**

```typescript
// src/api/architect.ts

export async function translateDiagram(
  svgContent: string,
  format: ExportFormat,
  options?: TranslateOptions
): Promise<TranslateResponse> {
  const response = await apiClient.post<TranslateResponse>(
    '/architect/translate',
    { svgContent, format, options }
  );
  return response.data;
}
```

### UI Components

**ActionBar Updates:**

```tsx
// Enable Translate dropdown (was disabled in F01)
<Dropdown
  label="Translate"
  items={[
    { label: 'PNG Image', value: 'png', icon: PhotoIcon },
    { label: 'Mermaid', value: 'mmd', icon: DocumentTextIcon },
    { label: 'Draw.io XML', value: 'drawio', icon: Square2StackIcon },
  ]}
  onSelect={(format) => translateTo(format)}
  disabled={!exportedSvg || isTranslating}
/>
```

**OutputPanel Updates:**

```tsx
// Enable all format tabs
<Tabs
  value={activeOutputTab}
  onChange={setActiveOutputTab}
  tabs={[
    { id: 'svg', label: 'SVG', disabled: false },
    { id: 'png', label: 'PNG', disabled: false, badge: translatedContent.png ? 'Ready' : undefined },
    { id: 'mmd', label: 'Mermaid', disabled: false, badge: translatedContent.mmd ? 'Ready' : undefined },
    { id: 'drawio', label: 'Draw.io', disabled: false, badge: translatedContent.drawio ? 'Ready' : undefined },
  ]}
/>

{/* Tab content */}
{activeOutputTab === 'svg' && <ExportPreview content={exportedSvg} format="svg" />}
{activeOutputTab === 'png' && <ExportPreview content={translatedContent.png} format="png" loading={isTranslating} />}
{activeOutputTab === 'mmd' && <ExportPreview content={translatedContent.mmd} format="mmd" loading={isTranslating} />}
{activeOutputTab === 'drawio' && <ExportPreview content={translatedContent.drawio} format="drawio" loading={isTranslating} />}
```

**ExportPreview Updates:**

```tsx
// Support for different formats
interface ExportPreviewProps {
  content: string | null;
  format: 'svg' | 'png' | 'mmd' | 'drawio';
  loading?: boolean;
  error?: string | null;
}

// PNG: <img src={`data:image/png;base64,${content}`} />
// SVG: Direct inline rendering
// Mermaid: Syntax highlighted code block + copy/download
// Draw.io: Syntax highlighted XML + copy/download
```

## Interfaces and Dependencies

### Internal Dependencies

| Component | Depends On |
|-----------|------------|
| architectStore.translateTo | apiClient, exportedSvg |
| ActionBar (Translate) | architectStore |
| OutputPanel (tabs) | architectStore, ExportPreview |
| ExportPreview | architectStore (content, loading, error) |

### External Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| @excalidraw/excalidraw | (from F01) | SVG export |
| react-syntax-highlighter | ^15.x | Mermaid/XML syntax highlighting |
| google-generativeai | ^0.1.x | Gemini API (backend) |
| anthropic | (existing) | Claude API (backend) |

### Backend Service Dependencies

| Service | Purpose |
|---------|---------|
| LLMConfigService | Get Design Agent config |
| SecretsService | Retrieve API keys |
| Redis (optional) | Cache translations (F03) |

## Architecture Decisions

### AD-1: Single Translation Endpoint

**Decision:** Use a single `/api/architect/translate` endpoint for all formats.

**Rationale:**
- Simpler API surface
- Shared validation logic
- Easier to add new formats later
- Format-specific logic handled internally

### AD-2: Design Agent Config for Translation

**Decision:** Use the "Design Agent" LLM configuration for all translation tasks.

**Rationale:**
- Design agent is semantically appropriate for diagram translation
- Admin can configure optimal model for visual/structural tasks
- No need for separate "translation agent" config
- Gemini can be configured as the Design Agent provider for image generation

### AD-3: Lazy Translation (On-Demand)

**Decision:** Translate only when user clicks a specific format, not all at once.

**Rationale:**
- Reduces API costs (user may only need one format)
- Faster initial response
- Better user control
- Translations cached in store for session

### AD-4: Base64 for PNG Transfer

**Decision:** Return PNG as base64 string, not binary blob or URL.

**Rationale:**
- Consistent with existing patterns (same format as API responses)
- No need for separate file storage
- Easy to display inline in img tag
- Works with copy/download functionality

### AD-5: Frontend Syntax Highlighting

**Decision:** Use react-syntax-highlighter for Mermaid/Draw.io preview.

**Rationale:**
- Better UX for code-based outputs
- Already proven library
- Supports XML and Mermaid syntax
- Dark theme compatible

## File Structure

### Backend (New)

```
src/orchestrator/
  routes/
    architect_api.py              # New API route for /api/architect/*
  services/
    architect_service.py          # Translation business logic
  api/models/
    architect.py                  # Pydantic models for architect API
```

### Frontend (Extensions)

```
docker/hitl-ui/src/
  api/
    architect.ts                  # API client (extend stub from F01)
    types/
      architect.ts                # Types (extend from F01)
  stores/
    architectStore.ts             # Extend with translation state/actions
  components/
    architect/
      ExportPreview.tsx           # Extend for multi-format support
      ActionBar.tsx               # Enable Translate dropdown
      OutputPanel.tsx             # Enable all format tabs
      FormatTabContent.tsx        # New: Format-specific preview content
```

## Error Handling

### Frontend Error States

| Error Type | UI Behavior |
|------------|-------------|
| Network error | Toast notification, retry button |
| Model error | Display error in preview area |
| Rate limit | Toast with cooldown timer |
| Invalid SVG | Prompt to export SVG first |

### Backend Error Handling

```python
class TranslationError(Exception):
    """Base class for translation errors."""
    code: str

class ModelUnavailableError(TranslationError):
    """LLM model not configured or unavailable."""
    code = "MODEL_ERROR"

class SVGParseError(TranslationError):
    """Failed to parse input SVG."""
    code = "SVG_PARSE_ERROR"
```

## Testing Strategy

| Component | Test Focus |
|-----------|------------|
| architect_api.py | Request validation, response format |
| architect_service.py | LLM integration, prompt formatting |
| architectStore | Translation state, error handling |
| ActionBar | Translate dropdown, loading states |
| OutputPanel | Tab switching, format badges |
| ExportPreview | Multi-format rendering |

### Mock Strategy

**Backend:** Mock LLM responses for tests
```python
@pytest.fixture
def mock_gemini():
    with patch('google.generativeai.GenerativeModel') as mock:
        mock.return_value.generate_content.return_value.parts = [
            Mock(inline_data=Mock(data="base64encodedpng"))
        ]
        yield mock
```

**Frontend:** Mock API responses
```typescript
vi.mock('../api/architect', () => ({
  translateDiagram: vi.fn().mockResolvedValue({
    content: 'translated content',
    format: 'mmd',
    modelUsed: 'claude-sonnet-4-20250514',
  }),
}));
```

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Gemini not configured | PNG translation fails | Graceful degradation with clear error message |
| LLM rate limits | Slow/failed translations | Implement exponential backoff, show progress |
| Large SVG content | Timeout or token limit | Compress/simplify SVG, chunking strategy |
| Poor translation quality | User frustration | Clear "beta" labeling, feedback mechanism (F03) |
| API key not valid | Translation fails | Validate key on request, clear error message |

## Success Metrics

- Translation completes within 10 seconds for typical diagrams
- PNG generation produces visually similar output
- Mermaid output parses without errors in Mermaid Live
- Draw.io XML imports correctly into diagrams.net
- All tests pass with >80% coverage
- Error states are clearly communicated to user

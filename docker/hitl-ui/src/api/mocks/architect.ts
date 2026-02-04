/**
 * Mock data for Architect Translation API
 * P10-F02 Diagram Translation
 *
 * Provides mock responses for development without a backend.
 * Enable with VITE_USE_MOCKS=true in .env.local
 */

import type {
  TranslationFormat,
  TranslateResponse,
  TranslateOptions,
} from '../types/architect';

/**
 * Configurable delay for simulating API latency
 * @param ms - Milliseconds to delay
 */
export const delay = (ms: number): Promise<void> =>
  new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Random delay between min and max milliseconds
 */
export const randomDelay = (min: number, max: number): Promise<void> =>
  delay(min + Math.random() * (max - min));

/**
 * A small 100x100 transparent PNG as base64 (1x1 pixel scaled)
 * This is a placeholder PNG with a simple blue rectangle pattern
 */
const MOCK_PNG_BASE64 =
  'iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAYAAABw4pVUAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAAhGVYSWZNTQAqAAAACAAFARIAAwAAAAEAAQAAARoABQAAAAEAAABKARsABQAAAAEAAABSASgAAwAAAAEAAgAAh2kABAAAAAEAAABaAAAAAAAAAEgAAAABAAAASAAAAAEAA6ABAAMAAAABAAEAAKACAAQAAAABAAAAZKADAAQAAAABAAAAZAAAAADHbsyZAAAACXBIWXMAAAsTAAALEwEAmpwYAAABWWlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iWE1QIENvcmUgNi4wLjAiPgogICA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPgogICAgICA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIgogICAgICAgICAgICB4bWxuczp0aWZmPSJodHRwOi8vbnMuYWRvYmUuY29tL3RpZmYvMS4wLyI+CiAgICAgICAgIDx0aWZmOk9yaWVudGF0aW9uPjE8L3RpZmY6T3JpZW50YXRpb24+CiAgICAgIDwvcmRmOkRlc2NyaXB0aW9uPgogICA8L3JkZjpSREY+CjwveDp4bXBtZXRhPgoZXuEHAAADNElEQVR4Ae2cS27DMAxE3f0fatfpIkANJbYlkuKQs7LjmPP8NCppO87r+Xw+/gw4YAvYBjVgizMBW8E2qBFbHAnYCrZBjdiisQJbwbaoAVueCNgKt0GN2PJIwFa4jWrElicCtsJtVCO2aCxgK9wGNWKLxgK2wm1QI7Y8ErAVbqMasUVjAVvhNqgRWzQWsBVugxqx5ZGArXAb1YgtnwRshdugRmzRWMBWuA1qxBaNBWyF26BGbNFYwFa4jWrElicCtsJtVCO2PCJgy9sGNWLLIwFb3jaqEVueELDlbYMaseUJAVveNqoRW54QsOVtgxqxRWMBW+E2qBFbNBawFW6DGrHlkYCtcBvViC0aC9gKt0GN2KKxgK1wG9SILZ8EbIXboEZs0VjAVrgNasQWjQVshdugRmzRWMBWuI1qxJYnBGx526BGbHlCwJa3jWrElicEbHnboEZs0VjAVrgNasQWjQVshdugRmzRWMBWuA1qxBaNBWyF26hGbHkkYMvbBjViyyMBW942qhFbnhCw5W2DGrHlCQFb3jaqEVs+CdgKt0GN2PKLX8ZYW8E2qBFbNBawFW6DGrFFYwFb4TaoEVs0FrAVboMasUVjAVvhNqoRWx4J2PK2QY3Y8kjAlreNasSWJwRsedugRmzRWMBWuA1qxBaNBWyF26BGbNFYwFa4jWrElkcCtrxtUCO2PBKw5W2jGrHlCQFb3jaoEVs+CdgKt0GN2PKLb4dcW8E2qBFbNBawFW6DGrFFYwFb4TaoEVs0FrAVboMaseWTgK1wG9SILZ8EbIXboEZs0VjAVrgNasSWJwRsedugRmx5QsCWt41qxJZPArbCbVAjtnwSsBVugxqx5ZOArXAb1YgtGgvYCrdBjdiisgCscBvUiC0qC8AKt0GN2KKyAKxwG9SILRoL2Aq3QY3Y8knAVrgNasQWjQVshdugRmz5JGAr3AY1YovGArbCbVAjtqgsACvcBjViSwwBW+E2qBFbNBawFW6DGrFFYwFb4TaoEVs0FrAVboMaseWRgK1wG9WILRoL2Aq3QY3YorEArHAb1IgtGgvACrdBjdiisQCscBvUiC0aC8AKt0GN/AcYHo8H1yb2PgAAAABJRU5ErkJggg==';

/**
 * Mock Mermaid flowchart response
 */
const MOCK_MERMAID_FLOWCHART = `flowchart TB
    subgraph Client["Client Layer"]
        UI[Web UI]
        CLI[CLI Client]
    end

    subgraph API["API Gateway"]
        GW[API Gateway]
        Auth[Auth Service]
    end

    subgraph Services["Core Services"]
        Orch[Orchestrator]
        Worker[Workers]
        Queue[Message Queue]
    end

    subgraph Data["Data Layer"]
        DB[(Database)]
        Cache[(Redis Cache)]
        Store[(Object Store)]
    end

    UI --> GW
    CLI --> GW
    GW --> Auth
    GW --> Orch
    Orch --> Queue
    Queue --> Worker
    Worker --> DB
    Worker --> Cache
    Orch --> Store

    style Client fill:#e1f5fe
    style API fill:#fff3e0
    style Services fill:#e8f5e9
    style Data fill:#fce4ec`;

/**
 * Mock Draw.io XML response
 */
const MOCK_DRAWIO_XML = `<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" modified="2024-01-15T12:00:00.000Z" agent="aSDLC Architect" version="21.0.0">
  <diagram name="Architecture" id="arch-001">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>

        <!-- Client Layer -->
        <mxCell id="client-group" value="Client Layer" style="swimlane;horizontal=0;fillColor=#e1f5fe;strokeColor=#4fc3f7;" vertex="1" parent="1">
          <mxGeometry x="40" y="40" width="200" height="120" as="geometry"/>
        </mxCell>
        <mxCell id="web-ui" value="Web UI" style="rounded=1;fillColor=#bbdefb;strokeColor=#1976d2;" vertex="1" parent="client-group">
          <mxGeometry x="20" y="30" width="80" height="40" as="geometry"/>
        </mxCell>
        <mxCell id="cli" value="CLI Client" style="rounded=1;fillColor=#bbdefb;strokeColor=#1976d2;" vertex="1" parent="client-group">
          <mxGeometry x="110" y="30" width="80" height="40" as="geometry"/>
        </mxCell>

        <!-- API Layer -->
        <mxCell id="api-group" value="API Gateway" style="swimlane;horizontal=0;fillColor=#fff3e0;strokeColor=#ff9800;" vertex="1" parent="1">
          <mxGeometry x="280" y="40" width="200" height="120" as="geometry"/>
        </mxCell>
        <mxCell id="gateway" value="API Gateway" style="rounded=1;fillColor=#ffe0b2;strokeColor=#f57c00;" vertex="1" parent="api-group">
          <mxGeometry x="20" y="30" width="80" height="40" as="geometry"/>
        </mxCell>
        <mxCell id="auth" value="Auth Service" style="rounded=1;fillColor=#ffe0b2;strokeColor=#f57c00;" vertex="1" parent="api-group">
          <mxGeometry x="110" y="30" width="80" height="40" as="geometry"/>
        </mxCell>

        <!-- Services Layer -->
        <mxCell id="services-group" value="Core Services" style="swimlane;horizontal=0;fillColor=#e8f5e9;strokeColor=#66bb6a;" vertex="1" parent="1">
          <mxGeometry x="520" y="40" width="240" height="120" as="geometry"/>
        </mxCell>
        <mxCell id="orchestrator" value="Orchestrator" style="rounded=1;fillColor=#c8e6c9;strokeColor=#388e3c;" vertex="1" parent="services-group">
          <mxGeometry x="20" y="30" width="80" height="40" as="geometry"/>
        </mxCell>
        <mxCell id="workers" value="Workers" style="rounded=1;fillColor=#c8e6c9;strokeColor=#388e3c;" vertex="1" parent="services-group">
          <mxGeometry x="110" y="30" width="80" height="40" as="geometry"/>
        </mxCell>

        <!-- Data Layer -->
        <mxCell id="data-group" value="Data Layer" style="swimlane;horizontal=0;fillColor=#fce4ec;strokeColor=#ec407a;" vertex="1" parent="1">
          <mxGeometry x="280" y="200" width="300" height="120" as="geometry"/>
        </mxCell>
        <mxCell id="database" value="Database" style="shape=cylinder3;fillColor=#f8bbd0;strokeColor=#c2185b;" vertex="1" parent="data-group">
          <mxGeometry x="20" y="30" width="60" height="60" as="geometry"/>
        </mxCell>
        <mxCell id="redis" value="Redis Cache" style="shape=cylinder3;fillColor=#f8bbd0;strokeColor=#c2185b;" vertex="1" parent="data-group">
          <mxGeometry x="100" y="30" width="60" height="60" as="geometry"/>
        </mxCell>
        <mxCell id="storage" value="Object Store" style="shape=cylinder3;fillColor=#f8bbd0;strokeColor=#c2185b;" vertex="1" parent="data-group">
          <mxGeometry x="180" y="30" width="60" height="60" as="geometry"/>
        </mxCell>

        <!-- Connections -->
        <mxCell id="conn1" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;" edge="1" parent="1" source="web-ui" target="gateway">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="conn2" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;" edge="1" parent="1" source="gateway" target="orchestrator">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="conn3" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;" edge="1" parent="1" source="orchestrator" target="database">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>`;

/**
 * Mock translate diagram function
 * Simulates API latency and returns mock data
 *
 * @param svgContent - The SVG content (not used in mock)
 * @param format - The target format
 * @param options - Optional translation options
 */
export async function mockTranslateDiagram(
  _svgContent: string,
  format: TranslationFormat,
  _options?: TranslateOptions
): Promise<TranslateResponse> {
  // Simulate API latency (1-2 seconds)
  await randomDelay(1000, 2000);

  switch (format) {
    case 'png':
      return {
        content: MOCK_PNG_BASE64,
        format: 'png',
        modelUsed: 'gemini-2.5-flash-preview-image-generation',
        metadata: {
          width: 100,
          height: 100,
        },
      };

    case 'mmd':
      return {
        content: MOCK_MERMAID_FLOWCHART,
        format: 'mmd',
        modelUsed: 'claude-sonnet-4-20250514',
        metadata: {
          diagramType: 'flowchart',
        },
      };

    case 'drawio':
      return {
        content: MOCK_DRAWIO_XML,
        format: 'drawio',
        modelUsed: 'claude-sonnet-4-20250514',
      };

    default:
      throw new Error(`Unknown format: ${format}`);
  }
}

/**
 * Get mock PNG base64 data for testing
 */
export function getMockPngBase64(): string {
  return MOCK_PNG_BASE64;
}

/**
 * Get mock Mermaid content for testing
 */
export function getMockMermaidContent(): string {
  return MOCK_MERMAID_FLOWCHART;
}

/**
 * Get mock Draw.io XML content for testing
 */
export function getMockDrawioContent(): string {
  return MOCK_DRAWIO_XML;
}

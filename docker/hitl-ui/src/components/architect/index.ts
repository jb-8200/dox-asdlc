/**
 * Architect Board Canvas Components
 * P10-F01 - Phase 2-4 Core Components
 */

// Lazy-loadable canvas component (use React.lazy for code splitting)
export { default as ArchitectCanvas } from './ArchitectCanvas';
export type { ArchitectCanvasProps, ArchitectCanvasRef } from './ArchitectCanvas';

// Panel components
export { default as ToolsPanel } from './ToolsPanel';
export type { ToolsPanelProps } from './ToolsPanel';

export { default as OutputPanel } from './OutputPanel';
export type { OutputPanelProps } from './OutputPanel';

// Export preview component
export { default as ExportPreview } from './ExportPreview';
export type { ExportPreviewProps } from './ExportPreview';

// Action bar component
export { default as ActionBar } from './ActionBar';
export type { ActionBarProps } from './ActionBar';

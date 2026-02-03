/**
 * Architect Board Canvas Types (P10-F01)
 * Types for the visual architecture diagramming feature
 */

/**
 * Base Excalidraw element properties (subset of full ExcalidrawElement)
 * This provides a decoupled type definition that matches Excalidraw's structure.
 * The full ExcalidrawElement type from the library is used at runtime.
 */
export interface ArchitectElement {
  id: string;
  type: string;
  x: number;
  y: number;
  width: number;
  height: number;
  strokeColor: string;
  backgroundColor: string;
  fillStyle: string;
  strokeWidth: number;
  strokeStyle: string;
  roughness: number;
  opacity: number;
  seed: number;
  version: number;
  versionNonce: number;
  isDeleted: boolean;
  groupIds: readonly string[];
  boundElements: readonly { id: string; type: string }[] | null;
  updated: number;
  link: string | null;
  locked: boolean;
  // Allow additional properties from Excalidraw
  [key: string]: unknown;
}

/**
 * Excalidraw app state properties relevant for saving/restoring
 */
export interface ArchitectAppState {
  viewBackgroundColor?: string;
  currentItemFontFamily?: number;
  currentItemFontSize?: number;
  currentItemStrokeColor?: string;
  currentItemBackgroundColor?: string;
  currentItemFillStyle?: string;
  currentItemStrokeWidth?: number;
  currentItemStrokeStyle?: string;
  currentItemRoughness?: number;
  currentItemOpacity?: number;
  zoom?: { value: number };
  scrollX?: number;
  scrollY?: number;
  // Allow additional properties from Excalidraw
  [key: string]: unknown;
}

/**
 * Represents a saved architect draft in the system
 */
export interface ArchitectDraft {
  id: string;
  name: string;
  elements: ArchitectElement[];
  appState: ArchitectAppState;
  createdAt: string;
  updatedAt: string;
}

/**
 * Represents an exported artifact from the architect canvas
 */
export interface ArchitectExport {
  draftId: string;
  format: ExportFormat;
  content: string;
  createdAt: string;
}

/**
 * Supported export formats for architect diagrams
 */
export type ExportFormat = 'svg' | 'png' | 'mmd' | 'drawio';

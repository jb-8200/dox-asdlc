import { create } from 'zustand';
import type { ArchitectElement, ArchitectAppState } from '../api/types/architect';

/**
 * Architect Board Canvas store state interface
 */
interface ArchitectState {
  // Canvas identification
  canvasId: string | null;
  canvasName: string;

  // Excalidraw state
  elements: ArchitectElement[];
  appState: ArchitectAppState;

  // Export state
  exportedSvg: string | null;
  isExporting: boolean;

  // Panel visibility
  isToolsPanelOpen: boolean;
  isOutputPanelOpen: boolean;

  // Actions
  setCanvasId: (id: string | null) => void;
  setCanvasName: (name: string) => void;
  updateElements: (elements: ArchitectElement[]) => void;
  updateAppState: (appState: Partial<ArchitectAppState>) => void;
  exportToSvg: (svg: string) => void;
  setIsExporting: (isExporting: boolean) => void;
  toggleToolsPanel: () => void;
  toggleOutputPanel: () => void;
  resetCanvas: () => void;
}

/**
 * Default state values for the architect store
 */
const DEFAULT_STATE = {
  canvasId: null,
  canvasName: 'Untitled Architecture',
  elements: [],
  appState: {
    viewBackgroundColor: '#ffffff',
    zoom: { value: 1 },
    scrollX: 0,
    scrollY: 0,
  },
  exportedSvg: null,
  isExporting: false,
  isToolsPanelOpen: false,
  isOutputPanelOpen: false,
};

/**
 * Zustand store for Architect Board Canvas state management
 */
export const useArchitectStore = create<ArchitectState>((set) => ({
  ...DEFAULT_STATE,

  setCanvasId: (id) => set({ canvasId: id }),

  setCanvasName: (name) => set({ canvasName: name }),

  updateElements: (elements) => set({ elements }),

  updateAppState: (newAppState) =>
    set((state) => ({
      appState: { ...state.appState, ...newAppState },
    })),

  exportToSvg: (svg) => set({ exportedSvg: svg }),

  setIsExporting: (isExporting) => set({ isExporting }),

  toggleToolsPanel: () =>
    set((state) => ({ isToolsPanelOpen: !state.isToolsPanelOpen })),

  toggleOutputPanel: () =>
    set((state) => ({ isOutputPanelOpen: !state.isOutputPanelOpen })),

  resetCanvas: () => set(DEFAULT_STATE),
}));

import { create } from 'zustand';
import { exportToSvg } from '@excalidraw/excalidraw';
import type { ExcalidrawElement } from '@excalidraw/excalidraw/types';
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
  performExport: () => Promise<void>;
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
export const useArchitectStore = create<ArchitectState>((set, get) => ({
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

  /**
   * Perform SVG export using Excalidraw's exportToSvg function
   * Takes elements and appState from store, converts to SVG string
   */
  performExport: async () => {
    const { elements, appState } = get();

    // Skip if no elements to export
    if (!elements.length) {
      return;
    }

    set({ isExporting: true });

    try {
      // Use Excalidraw's exportToSvg
      const svg = await exportToSvg({
        elements: elements as unknown as readonly ExcalidrawElement[],
        appState: {
          ...appState,
          exportWithDarkMode: true,
        },
        files: null,
      });

      // Convert SVG element to string
      const svgString = new XMLSerializer().serializeToString(svg);
      set({ exportedSvg: svgString, isExporting: false });
    } catch (error) {
      console.error('Export failed:', error);
      set({ isExporting: false });
    }
  },

  toggleToolsPanel: () =>
    set((state) => ({ isToolsPanelOpen: !state.isToolsPanelOpen })),

  toggleOutputPanel: () =>
    set((state) => ({ isOutputPanelOpen: !state.isOutputPanelOpen })),

  resetCanvas: () => set(DEFAULT_STATE),
}));

import { create } from 'zustand';
import { exportToSvg } from '@excalidraw/excalidraw';
import type { ExcalidrawElement } from '@excalidraw/excalidraw/types';
import type {
  ArchitectElement,
  ArchitectAppState,
  TranslationFormat,
  ExportFormat,
} from '../api/types/architect';
import { translateDiagram } from '../api/architect';

/**
 * Translated content storage for all formats
 * P10-F02 Diagram Translation
 */
interface TranslatedContent {
  png: string | null;
  mmd: string | null;
  drawio: string | null;
}

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

  // Translation state (P10-F02)
  isTranslating: boolean;
  translationError: string | null;
  translatedContent: TranslatedContent;
  activeOutputTab: ExportFormat;

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

  // Translation actions (P10-F02)
  translateTo: (format: TranslationFormat) => Promise<void>;
  setActiveOutputTab: (tab: ExportFormat) => void;
  clearTranslation: (format?: TranslationFormat) => void;
}

/**
 * Default translated content state
 */
const DEFAULT_TRANSLATED_CONTENT: TranslatedContent = {
  png: null,
  mmd: null,
  drawio: null,
};

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
  // Translation state (P10-F02)
  isTranslating: false,
  translationError: null,
  translatedContent: DEFAULT_TRANSLATED_CONTENT,
  activeOutputTab: 'svg' as ExportFormat,
  // Panel visibility
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

  /**
   * Translate the exported SVG to a different format
   * P10-F02 Diagram Translation
   */
  translateTo: async (format: TranslationFormat) => {
    const { exportedSvg } = get();

    // Cannot translate without SVG content
    if (!exportedSvg) {
      set({ translationError: 'No SVG content to translate. Export to SVG first.' });
      return;
    }

    set({
      isTranslating: true,
      translationError: null,
    });

    try {
      const response = await translateDiagram(exportedSvg, format);

      // Update the translated content for this format
      set((state) => ({
        isTranslating: false,
        translatedContent: {
          ...state.translatedContent,
          [format]: response.content,
        },
        // Auto-switch to the translated format tab
        activeOutputTab: format,
      }));
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Translation failed';
      console.error('Translation failed:', error);
      set({
        isTranslating: false,
        translationError: errorMessage,
      });
    }
  },

  /**
   * Set the active output tab
   * P10-F02 Diagram Translation
   */
  setActiveOutputTab: (tab: ExportFormat) => set({ activeOutputTab: tab }),

  /**
   * Clear translated content for a specific format or all formats
   * P10-F02 Diagram Translation
   */
  clearTranslation: (format?: TranslationFormat) => {
    if (format) {
      // Clear specific format
      set((state) => ({
        translatedContent: {
          ...state.translatedContent,
          [format]: null,
        },
        translationError: null,
      }));
    } else {
      // Clear all translations
      set({
        translatedContent: DEFAULT_TRANSLATED_CONTENT,
        translationError: null,
      });
    }
  },
}));

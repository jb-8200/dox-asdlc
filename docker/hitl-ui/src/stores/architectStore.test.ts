import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock Excalidraw's exportToSvg
vi.mock('@excalidraw/excalidraw', () => ({
  exportToSvg: vi.fn().mockImplementation(async () => {
    // Return a mock SVG element
    const parser = new DOMParser();
    const doc = parser.parseFromString(
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100"/></svg>',
      'image/svg+xml'
    );
    return doc.documentElement;
  }),
}));

import { useArchitectStore } from './architectStore';

describe('architectStore', () => {
  beforeEach(() => {
    useArchitectStore.getState().resetCanvas();
  });

  describe('initial state', () => {
    it('has default canvas name', () => {
      const state = useArchitectStore.getState();
      expect(state.canvasName).toBe('Untitled Architecture');
    });

    it('has empty elements array', () => {
      const state = useArchitectStore.getState();
      expect(state.elements).toEqual([]);
    });

    it('has default appState values', () => {
      const state = useArchitectStore.getState();
      expect(state.appState).toEqual({
        viewBackgroundColor: '#ffffff',
        zoom: { value: 1 },
        scrollX: 0,
        scrollY: 0,
      });
    });

    it('has panels collapsed by default', () => {
      const state = useArchitectStore.getState();
      expect(state.isToolsPanelOpen).toBe(false);
      expect(state.isOutputPanelOpen).toBe(false);
    });

    it('has no exported SVG by default', () => {
      const state = useArchitectStore.getState();
      expect(state.exportedSvg).toBeNull();
    });

    it('is not exporting by default', () => {
      const state = useArchitectStore.getState();
      expect(state.isExporting).toBe(false);
    });
  });

  describe('setCanvasName', () => {
    it('updates the canvas name', () => {
      useArchitectStore.getState().setCanvasName('My Architecture Diagram');
      expect(useArchitectStore.getState().canvasName).toBe('My Architecture Diagram');
    });

    it('allows empty string', () => {
      useArchitectStore.getState().setCanvasName('');
      expect(useArchitectStore.getState().canvasName).toBe('');
    });
  });

  describe('updateElements', () => {
    it('updates elements array', () => {
      const mockElements = [
        {
          id: 'elem-1',
          type: 'rectangle',
          x: 100,
          y: 100,
          width: 200,
          height: 100,
          strokeColor: '#000000',
          backgroundColor: 'transparent',
          fillStyle: 'hachure',
          strokeWidth: 1,
          strokeStyle: 'solid',
          roughness: 1,
          opacity: 100,
          seed: 12345,
          version: 1,
          versionNonce: 1,
          isDeleted: false,
          groupIds: [],
          boundElements: null,
          updated: Date.now(),
          link: null,
          locked: false,
        },
      ];

      useArchitectStore.getState().updateElements(mockElements);
      expect(useArchitectStore.getState().elements).toEqual(mockElements);
    });

    it('replaces existing elements', () => {
      const initialElements = [
        {
          id: 'elem-1',
          type: 'rectangle',
          x: 0,
          y: 0,
          width: 50,
          height: 50,
          strokeColor: '#000000',
          backgroundColor: 'transparent',
          fillStyle: 'hachure',
          strokeWidth: 1,
          strokeStyle: 'solid',
          roughness: 1,
          opacity: 100,
          seed: 1,
          version: 1,
          versionNonce: 1,
          isDeleted: false,
          groupIds: [],
          boundElements: null,
          updated: 1,
          link: null,
          locked: false,
        },
      ];
      const newElements = [
        {
          id: 'elem-2',
          type: 'ellipse',
          x: 200,
          y: 200,
          width: 100,
          height: 100,
          strokeColor: '#ff0000',
          backgroundColor: 'transparent',
          fillStyle: 'solid',
          strokeWidth: 2,
          strokeStyle: 'dashed',
          roughness: 0,
          opacity: 100,
          seed: 2,
          version: 1,
          versionNonce: 2,
          isDeleted: false,
          groupIds: [],
          boundElements: null,
          updated: 2,
          link: null,
          locked: false,
        },
      ];

      useArchitectStore.getState().updateElements(initialElements);
      useArchitectStore.getState().updateElements(newElements);
      expect(useArchitectStore.getState().elements).toEqual(newElements);
    });
  });

  describe('updateAppState', () => {
    it('updates partial appState', () => {
      useArchitectStore.getState().updateAppState({
        viewBackgroundColor: '#f0f0f0',
      });

      const state = useArchitectStore.getState();
      expect(state.appState.viewBackgroundColor).toBe('#f0f0f0');
      expect(state.appState.zoom).toEqual({ value: 1 });
    });

    it('merges with existing appState', () => {
      useArchitectStore.getState().updateAppState({
        viewBackgroundColor: '#eeeeee',
      });
      useArchitectStore.getState().updateAppState({
        zoom: { value: 2 },
      });

      const state = useArchitectStore.getState();
      expect(state.appState.viewBackgroundColor).toBe('#eeeeee');
      expect(state.appState.zoom).toEqual({ value: 2 });
    });
  });

  describe('toggleToolsPanel', () => {
    it('toggles tools panel state', () => {
      expect(useArchitectStore.getState().isToolsPanelOpen).toBe(false);

      useArchitectStore.getState().toggleToolsPanel();
      expect(useArchitectStore.getState().isToolsPanelOpen).toBe(true);

      useArchitectStore.getState().toggleToolsPanel();
      expect(useArchitectStore.getState().isToolsPanelOpen).toBe(false);
    });
  });

  describe('toggleOutputPanel', () => {
    it('toggles output panel state', () => {
      expect(useArchitectStore.getState().isOutputPanelOpen).toBe(false);

      useArchitectStore.getState().toggleOutputPanel();
      expect(useArchitectStore.getState().isOutputPanelOpen).toBe(true);

      useArchitectStore.getState().toggleOutputPanel();
      expect(useArchitectStore.getState().isOutputPanelOpen).toBe(false);
    });
  });

  describe('exportToSvg', () => {
    it('sets exported SVG content', () => {
      const svgContent = '<svg><rect /></svg>';
      useArchitectStore.getState().exportToSvg(svgContent);
      expect(useArchitectStore.getState().exportedSvg).toBe(svgContent);
    });

    it('replaces previous exported SVG', () => {
      useArchitectStore.getState().exportToSvg('<svg>first</svg>');
      useArchitectStore.getState().exportToSvg('<svg>second</svg>');
      expect(useArchitectStore.getState().exportedSvg).toBe('<svg>second</svg>');
    });
  });

  describe('setIsExporting', () => {
    it('sets exporting flag', () => {
      useArchitectStore.getState().setIsExporting(true);
      expect(useArchitectStore.getState().isExporting).toBe(true);

      useArchitectStore.getState().setIsExporting(false);
      expect(useArchitectStore.getState().isExporting).toBe(false);
    });
  });

  describe('resetCanvas', () => {
    it('resets all state to defaults', () => {
      // First modify some state
      useArchitectStore.getState().setCanvasName('Modified Name');
      useArchitectStore.getState().updateElements([
        {
          id: 'test',
          type: 'rectangle',
          x: 0,
          y: 0,
          width: 50,
          height: 50,
          strokeColor: '#000',
          backgroundColor: 'transparent',
          fillStyle: 'hachure',
          strokeWidth: 1,
          strokeStyle: 'solid',
          roughness: 1,
          opacity: 100,
          seed: 1,
          version: 1,
          versionNonce: 1,
          isDeleted: false,
          groupIds: [],
          boundElements: null,
          updated: 1,
          link: null,
          locked: false,
        },
      ]);
      useArchitectStore.getState().toggleToolsPanel();
      useArchitectStore.getState().exportToSvg('<svg>test</svg>');

      // Reset
      useArchitectStore.getState().resetCanvas();

      // Verify defaults
      const state = useArchitectStore.getState();
      expect(state.canvasName).toBe('Untitled Architecture');
      expect(state.elements).toEqual([]);
      expect(state.isToolsPanelOpen).toBe(false);
      expect(state.exportedSvg).toBeNull();
    });
  });

  describe('setCanvasId', () => {
    it('sets the canvas ID', () => {
      useArchitectStore.getState().setCanvasId('canvas-123');
      expect(useArchitectStore.getState().canvasId).toBe('canvas-123');
    });

    it('allows null canvas ID', () => {
      useArchitectStore.getState().setCanvasId('canvas-123');
      useArchitectStore.getState().setCanvasId(null);
      expect(useArchitectStore.getState().canvasId).toBeNull();
    });
  });

  describe('performExport', () => {
    it('does nothing when elements are empty', async () => {
      // Ensure elements are empty
      useArchitectStore.getState().updateElements([]);

      await useArchitectStore.getState().performExport();

      // Should not change exporting state or produce SVG
      expect(useArchitectStore.getState().exportedSvg).toBeNull();
    });

    it('sets isExporting to true during export', async () => {
      const mockElement = {
        id: 'elem-1',
        type: 'rectangle',
        x: 100,
        y: 100,
        width: 200,
        height: 100,
        strokeColor: '#000000',
        backgroundColor: 'transparent',
        fillStyle: 'hachure',
        strokeWidth: 1,
        strokeStyle: 'solid',
        roughness: 1,
        opacity: 100,
        seed: 12345,
        version: 1,
        versionNonce: 1,
        isDeleted: false,
        groupIds: [],
        boundElements: null,
        updated: Date.now(),
        link: null,
        locked: false,
      };

      useArchitectStore.getState().updateElements([mockElement]);

      // Start export but don't await
      const exportPromise = useArchitectStore.getState().performExport();

      // Check isExporting is true during export
      expect(useArchitectStore.getState().isExporting).toBe(true);

      // Wait for completion
      await exportPromise;

      // isExporting should be false after completion
      expect(useArchitectStore.getState().isExporting).toBe(false);
    });

    it('updates exportedSvg on successful export', async () => {
      const mockElement = {
        id: 'elem-1',
        type: 'rectangle',
        x: 100,
        y: 100,
        width: 200,
        height: 100,
        strokeColor: '#000000',
        backgroundColor: 'transparent',
        fillStyle: 'hachure',
        strokeWidth: 1,
        strokeStyle: 'solid',
        roughness: 1,
        opacity: 100,
        seed: 12345,
        version: 1,
        versionNonce: 1,
        isDeleted: false,
        groupIds: [],
        boundElements: null,
        updated: Date.now(),
        link: null,
        locked: false,
      };

      useArchitectStore.getState().updateElements([mockElement]);

      await useArchitectStore.getState().performExport();

      // Should have SVG content (from mock)
      expect(useArchitectStore.getState().exportedSvg).toContain('<svg');
    });
  });
});

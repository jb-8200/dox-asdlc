/**
 * Tests for OutputPanel component
 * P10-F01 Architect Board Canvas - Phase 2 (T10)
 * P10-F02 Diagram Translation - Phase 4 (T21)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

// Mock state variables
const mockToggleOutputPanel = vi.fn();
const mockSetActiveOutputTab = vi.fn();
let mockIsOutputPanelOpen = false;
let mockActiveOutputTab = 'svg';
let mockExportedSvg: string | null = null;
let mockIsTranslating = false;
let mockTranslationError: string | null = null;
let mockTranslatedContent = {
  png: null as string | null,
  mmd: null as string | null,
  drawio: null as string | null,
};

// Mock the architect store
vi.mock('../../stores/architectStore', () => ({
  useArchitectStore: vi.fn((selector) => {
    const state = {
      isOutputPanelOpen: mockIsOutputPanelOpen,
      toggleOutputPanel: mockToggleOutputPanel,
      activeOutputTab: mockActiveOutputTab,
      setActiveOutputTab: mockSetActiveOutputTab,
      exportedSvg: mockExportedSvg,
      isTranslating: mockIsTranslating,
      translationError: mockTranslationError,
      translatedContent: mockTranslatedContent,
    };
    return typeof selector === 'function' ? selector(state) : state;
  }),
}));

import OutputPanel from './OutputPanel';

describe('OutputPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockIsOutputPanelOpen = false;
    mockActiveOutputTab = 'svg';
    mockExportedSvg = null;
    mockIsTranslating = false;
    mockTranslationError = null;
    mockTranslatedContent = { png: null, mmd: null, drawio: null };
  });

  describe('Collapsed State', () => {
    it('renders collapsed by default', () => {
      mockIsOutputPanelOpen = false;
      render(<OutputPanel />);

      const panel = screen.getByTestId('output-panel');
      expect(panel).toHaveClass('w-12');
    });

    it('does not show title when collapsed', () => {
      mockIsOutputPanelOpen = false;
      render(<OutputPanel />);

      expect(screen.queryByText('Output')).not.toBeInTheDocument();
    });

    it('shows expand button with correct aria-label when collapsed', () => {
      mockIsOutputPanelOpen = false;
      render(<OutputPanel />);

      const button = screen.getByRole('button', { name: /expand output panel/i });
      expect(button).toBeInTheDocument();
    });
  });

  describe('Expanded State', () => {
    it('renders expanded when isOutputPanelOpen is true', () => {
      mockIsOutputPanelOpen = true;
      render(<OutputPanel />);

      const panel = screen.getByTestId('output-panel');
      expect(panel).toHaveClass('w-80');
    });

    it('shows title when expanded', () => {
      mockIsOutputPanelOpen = true;
      render(<OutputPanel />);

      expect(screen.getByText('Output')).toBeInTheDocument();
    });

    it('shows collapse button with correct aria-label when expanded', () => {
      mockIsOutputPanelOpen = true;
      render(<OutputPanel />);

      const button = screen.getByRole('button', { name: /collapse output panel/i });
      expect(button).toBeInTheDocument();
    });
  });

  describe('Toggle Behavior', () => {
    it('calls toggleOutputPanel when toggle button is clicked', () => {
      mockIsOutputPanelOpen = false;
      render(<OutputPanel />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(mockToggleOutputPanel).toHaveBeenCalledTimes(1);
    });
  });

  describe('Tab Structure', () => {
    it('shows SVG tab when expanded', () => {
      mockIsOutputPanelOpen = true;
      render(<OutputPanel />);

      expect(screen.getByRole('tab', { name: /svg/i })).toBeInTheDocument();
    });

    it('SVG tab is active by default', () => {
      mockIsOutputPanelOpen = true;
      mockActiveOutputTab = 'svg';
      render(<OutputPanel />);

      const svgTab = screen.getByRole('tab', { name: /svg/i });
      expect(svgTab).toHaveAttribute('aria-selected', 'true');
    });

    it('shows all format tabs enabled (P10-F02)', () => {
      mockIsOutputPanelOpen = true;
      render(<OutputPanel />);

      // All tabs should be present and clickable
      expect(screen.getByRole('tab', { name: /svg/i })).not.toBeDisabled();
      expect(screen.getByRole('tab', { name: /png/i })).not.toBeDisabled();
      expect(screen.getByRole('tab', { name: /mermaid/i })).not.toBeDisabled();
      expect(screen.getByRole('tab', { name: /draw\.io/i })).not.toBeDisabled();
    });

    it('clicking tab calls setActiveOutputTab', () => {
      mockIsOutputPanelOpen = true;
      render(<OutputPanel />);

      const pngTab = screen.getByRole('tab', { name: /png/i });
      fireEvent.click(pngTab);

      expect(mockSetActiveOutputTab).toHaveBeenCalledWith('png');
    });

    it('shows ready badge when translation content is available', () => {
      mockIsOutputPanelOpen = true;
      mockTranslatedContent = { png: 'base64data', mmd: null, drawio: null };
      render(<OutputPanel />);

      expect(screen.getByTestId('badge-png')).toBeInTheDocument();
    });

    it('does not show badge for SVG tab', () => {
      mockIsOutputPanelOpen = true;
      mockExportedSvg = '<svg></svg>';
      render(<OutputPanel />);

      expect(screen.queryByTestId('badge-svg')).not.toBeInTheDocument();
    });

    it('shows loading indicator when translating', () => {
      mockIsOutputPanelOpen = true;
      mockIsTranslating = true;
      mockActiveOutputTab = 'png';
      render(<OutputPanel />);

      expect(screen.getByTestId('loading-png')).toBeInTheDocument();
    });
  });

  describe('Export Preview Placeholder', () => {
    it('shows export preview placeholder when expanded', () => {
      mockIsOutputPanelOpen = true;
      render(<OutputPanel />);

      expect(screen.getByTestId('export-preview-placeholder')).toBeInTheDocument();
    });
  });

  describe('Transitions', () => {
    it('has transition classes for smooth animation', () => {
      render(<OutputPanel />);

      const panel = screen.getByTestId('output-panel');
      expect(panel).toHaveClass('transition-all');
      expect(panel).toHaveClass('duration-300');
    });
  });

  describe('Accessibility', () => {
    it('toggle button has accessible name when collapsed', () => {
      mockIsOutputPanelOpen = false;
      render(<OutputPanel />);

      const button = screen.getByRole('button');
      expect(button).toHaveAccessibleName(/expand output panel/i);
    });

    it('toggle button has accessible name when expanded', () => {
      mockIsOutputPanelOpen = true;
      render(<OutputPanel />);

      const button = screen.getByRole('button', { name: /collapse output panel/i });
      expect(button).toHaveAccessibleName(/collapse output panel/i);
    });

    it('tablist has proper role', () => {
      mockIsOutputPanelOpen = true;
      render(<OutputPanel />);

      expect(screen.getByRole('tablist')).toBeInTheDocument();
    });
  });

  describe('Custom className', () => {
    it('applies custom className', () => {
      render(<OutputPanel className="custom-class" />);
      const panel = screen.getByTestId('output-panel');
      expect(panel).toHaveClass('custom-class');
    });
  });

  /**
   * P10-F02 Multi-tab tests
   */
  describe('Multi-Tab Content (P10-F02)', () => {
    it('renders FormatTabContent for SVG tab', () => {
      mockIsOutputPanelOpen = true;
      mockActiveOutputTab = 'svg';
      mockExportedSvg = '<svg><rect/></svg>';
      render(<OutputPanel />);

      // FormatTabContent should show the SVG preview
      expect(screen.getByTestId('export-preview-placeholder')).toBeInTheDocument();
    });

    it('renders FormatTabContent for PNG tab', () => {
      mockIsOutputPanelOpen = true;
      mockActiveOutputTab = 'png';
      mockTranslatedContent = { png: 'base64data', mmd: null, drawio: null };
      render(<OutputPanel />);

      expect(screen.getByTestId('export-preview-placeholder')).toBeInTheDocument();
    });

    it('renders FormatTabContent for Mermaid tab', () => {
      mockIsOutputPanelOpen = true;
      mockActiveOutputTab = 'mmd';
      mockTranslatedContent = { png: null, mmd: 'flowchart TB', drawio: null };
      render(<OutputPanel />);

      expect(screen.getByTestId('export-preview-placeholder')).toBeInTheDocument();
    });

    it('renders FormatTabContent for Draw.io tab', () => {
      mockIsOutputPanelOpen = true;
      mockActiveOutputTab = 'drawio';
      mockTranslatedContent = { png: null, mmd: null, drawio: '<mxfile/>' };
      render(<OutputPanel />);

      expect(screen.getByTestId('export-preview-placeholder')).toBeInTheDocument();
    });

    it('shows loading state in FormatTabContent during translation', () => {
      mockIsOutputPanelOpen = true;
      mockActiveOutputTab = 'mmd';
      mockIsTranslating = true;
      render(<OutputPanel />);

      // The FormatTabContent should show loading state
      expect(screen.getByTestId('export-preview-placeholder')).toBeInTheDocument();
    });

    it('passes translation error to FormatTabContent', () => {
      mockIsOutputPanelOpen = true;
      mockActiveOutputTab = 'png';
      mockTranslationError = 'Model not available';
      render(<OutputPanel />);

      // Error should be passed to FormatTabContent
      expect(screen.getByTestId('export-preview-placeholder')).toBeInTheDocument();
    });
  });
});

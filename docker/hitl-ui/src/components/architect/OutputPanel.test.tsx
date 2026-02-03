/**
 * Tests for OutputPanel component
 * P10-F01 Architect Board Canvas - Phase 2 (T10)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

// Mock the architect store
const mockToggleOutputPanel = vi.fn();
let mockIsOutputPanelOpen = false;

vi.mock('../../stores/architectStore', () => ({
  useArchitectStore: vi.fn((selector) => {
    const state = {
      isOutputPanelOpen: mockIsOutputPanelOpen,
      toggleOutputPanel: mockToggleOutputPanel,
    };
    return typeof selector === 'function' ? selector(state) : state;
  }),
}));

import OutputPanel from './OutputPanel';

describe('OutputPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockIsOutputPanelOpen = false;
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
      render(<OutputPanel />);

      const svgTab = screen.getByRole('tab', { name: /svg/i });
      expect(svgTab).toHaveAttribute('aria-selected', 'true');
    });

    it('shows PNG tab as disabled', () => {
      mockIsOutputPanelOpen = true;
      render(<OutputPanel />);

      const pngTab = screen.getByRole('tab', { name: /png/i });
      expect(pngTab).toBeDisabled();
    });

    it('shows MMD tab as disabled', () => {
      mockIsOutputPanelOpen = true;
      render(<OutputPanel />);

      const mmdTab = screen.getByRole('tab', { name: /mmd/i });
      expect(mmdTab).toBeDisabled();
    });

    it('shows DrawIO tab as disabled', () => {
      mockIsOutputPanelOpen = true;
      render(<OutputPanel />);

      const drawioTab = screen.getByRole('tab', { name: /drawio/i });
      expect(drawioTab).toBeDisabled();
    });

    it('disabled tabs have "Coming in F02" tooltip', () => {
      mockIsOutputPanelOpen = true;
      render(<OutputPanel />);

      const pngTab = screen.getByRole('tab', { name: /png/i });
      expect(pngTab).toHaveAttribute('title', 'Coming in F02');
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
});

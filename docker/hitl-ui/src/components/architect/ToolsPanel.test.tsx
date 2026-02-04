/**
 * Tests for ToolsPanel component
 * P10-F01 Architect Board Canvas - Phase 2 (T08)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

// Mock the architect store
const mockToggleToolsPanel = vi.fn();
let mockIsToolsPanelOpen = false;

vi.mock('../../stores/architectStore', () => ({
  useArchitectStore: vi.fn((selector) => {
    const state = {
      isToolsPanelOpen: mockIsToolsPanelOpen,
      toggleToolsPanel: mockToggleToolsPanel,
    };
    return typeof selector === 'function' ? selector(state) : state;
  }),
}));

import ToolsPanel from './ToolsPanel';

describe('ToolsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockIsToolsPanelOpen = false;
  });

  describe('Collapsed State', () => {
    it('renders collapsed by default', () => {
      mockIsToolsPanelOpen = false;
      render(<ToolsPanel />);

      const panel = screen.getByTestId('tools-panel');
      expect(panel).toHaveClass('w-12');
    });

    it('does not show title when collapsed', () => {
      mockIsToolsPanelOpen = false;
      render(<ToolsPanel />);

      expect(screen.queryByText('Drawing Tools')).not.toBeInTheDocument();
    });

    it('shows expand button with correct aria-label when collapsed', () => {
      mockIsToolsPanelOpen = false;
      render(<ToolsPanel />);

      const button = screen.getByRole('button', { name: /expand tools panel/i });
      expect(button).toBeInTheDocument();
    });
  });

  describe('Expanded State', () => {
    it('renders expanded when isToolsPanelOpen is true', () => {
      mockIsToolsPanelOpen = true;
      render(<ToolsPanel />);

      const panel = screen.getByTestId('tools-panel');
      expect(panel).toHaveClass('w-60');
    });

    it('shows title when expanded', () => {
      mockIsToolsPanelOpen = true;
      render(<ToolsPanel />);

      expect(screen.getByText('Drawing Tools')).toBeInTheDocument();
    });

    it('shows collapse button with correct aria-label when expanded', () => {
      mockIsToolsPanelOpen = true;
      render(<ToolsPanel />);

      const button = screen.getByRole('button', { name: /collapse tools panel/i });
      expect(button).toBeInTheDocument();
    });
  });

  describe('Toggle Behavior', () => {
    it('calls toggleToolsPanel when toggle button is clicked', () => {
      mockIsToolsPanelOpen = false;
      render(<ToolsPanel />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(mockToggleToolsPanel).toHaveBeenCalledTimes(1);
    });
  });

  describe('Transitions', () => {
    it('has transition classes for smooth animation', () => {
      render(<ToolsPanel />);

      const panel = screen.getByTestId('tools-panel');
      expect(panel).toHaveClass('transition-all');
      expect(panel).toHaveClass('duration-300');
    });
  });

  describe('Accessibility', () => {
    it('toggle button has accessible name when collapsed', () => {
      mockIsToolsPanelOpen = false;
      render(<ToolsPanel />);

      const button = screen.getByRole('button');
      expect(button).toHaveAccessibleName(/expand tools panel/i);
    });

    it('toggle button has accessible name when expanded', () => {
      mockIsToolsPanelOpen = true;
      render(<ToolsPanel />);

      const button = screen.getByRole('button');
      expect(button).toHaveAccessibleName(/collapse tools panel/i);
    });
  });

  describe('Custom className', () => {
    it('applies custom className', () => {
      render(<ToolsPanel className="custom-class" />);
      const panel = screen.getByTestId('tools-panel');
      expect(panel).toHaveClass('custom-class');
    });
  });
});

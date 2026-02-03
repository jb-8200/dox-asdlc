/**
 * Tests for ActionBar component
 * P10-F01 Architect Board Canvas - Phase 4 (T16)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

// Mock the architect store
const mockPerformExport = vi.fn();
let mockIsExporting = false;

vi.mock('../../stores/architectStore', () => ({
  useArchitectStore: vi.fn((selector) => {
    const state = {
      isExporting: mockIsExporting,
      performExport: mockPerformExport,
    };
    return typeof selector === 'function' ? selector(state) : state;
  }),
}));

import ActionBar from './ActionBar';

describe('ActionBar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockIsExporting = false;
  });

  describe('Button Rendering', () => {
    it('renders Save Draft button', () => {
      render(<ActionBar />);
      expect(screen.getByRole('button', { name: /save draft/i })).toBeInTheDocument();
    });

    it('renders History button', () => {
      render(<ActionBar />);
      expect(screen.getByRole('button', { name: /history/i })).toBeInTheDocument();
    });

    it('renders Export SVG button', () => {
      render(<ActionBar />);
      expect(screen.getByRole('button', { name: /export svg/i })).toBeInTheDocument();
    });

    it('renders Translate dropdown button', () => {
      render(<ActionBar />);
      expect(screen.getByRole('button', { name: /translate/i })).toBeInTheDocument();
    });
  });

  describe('Disabled Buttons', () => {
    it('Save Draft button is disabled', () => {
      render(<ActionBar />);
      const button = screen.getByRole('button', { name: /save draft/i });
      expect(button).toBeDisabled();
    });

    it('History button is disabled', () => {
      render(<ActionBar />);
      const button = screen.getByRole('button', { name: /history/i });
      expect(button).toBeDisabled();
    });

    it('Translate button is disabled', () => {
      render(<ActionBar />);
      const button = screen.getByRole('button', { name: /translate/i });
      expect(button).toBeDisabled();
    });

    it('Export SVG button is enabled', () => {
      render(<ActionBar />);
      const button = screen.getByRole('button', { name: /export svg/i });
      expect(button).not.toBeDisabled();
    });
  });

  describe('Tooltips', () => {
    it('Save Draft button has "Coming in F03" tooltip', () => {
      render(<ActionBar />);
      const button = screen.getByRole('button', { name: /save draft/i });
      expect(button).toHaveAttribute('title', 'Coming in F03');
    });

    it('History button has "Coming in F03" tooltip', () => {
      render(<ActionBar />);
      const button = screen.getByRole('button', { name: /history/i });
      expect(button).toHaveAttribute('title', 'Coming in F03');
    });

    it('Translate button has "Coming in F02" tooltip', () => {
      render(<ActionBar />);
      const button = screen.getByRole('button', { name: /translate/i });
      expect(button).toHaveAttribute('title', 'Coming in F02');
    });
  });

  describe('Export Button Behavior', () => {
    it('calls performExport when Export SVG button is clicked', async () => {
      render(<ActionBar />);
      const button = screen.getByRole('button', { name: /export svg/i });
      fireEvent.click(button);

      await waitFor(() => {
        expect(mockPerformExport).toHaveBeenCalledTimes(1);
      });
    });

    it('shows loading state during export', () => {
      mockIsExporting = true;
      render(<ActionBar />);
      const button = screen.getByRole('button', { name: /exporting/i });
      expect(button).toBeInTheDocument();
      expect(button).toBeDisabled();
    });

    it('Export button is disabled during export', () => {
      mockIsExporting = true;
      render(<ActionBar />);
      const button = screen.getByRole('button', { name: /exporting/i });
      expect(button).toBeDisabled();
    });
  });

  describe('Layout and Styling', () => {
    it('renders with action-bar testid', () => {
      render(<ActionBar />);
      expect(screen.getByTestId('action-bar')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      render(<ActionBar className="custom-class" />);
      const actionBar = screen.getByTestId('action-bar');
      expect(actionBar).toHaveClass('custom-class');
    });

    it('has border-top styling', () => {
      render(<ActionBar />);
      const actionBar = screen.getByTestId('action-bar');
      expect(actionBar).toHaveClass('border-t');
    });
  });

  describe('Accessibility', () => {
    it('Export SVG button has accessible name', () => {
      render(<ActionBar />);
      const button = screen.getByRole('button', { name: /export svg/i });
      expect(button).toHaveAccessibleName();
    });

    it('disabled buttons have accessible names', () => {
      render(<ActionBar />);
      expect(screen.getByRole('button', { name: /save draft/i })).toHaveAccessibleName();
      expect(screen.getByRole('button', { name: /history/i })).toHaveAccessibleName();
      expect(screen.getByRole('button', { name: /translate/i })).toHaveAccessibleName();
    });
  });
});

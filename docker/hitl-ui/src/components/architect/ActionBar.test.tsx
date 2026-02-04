/**
 * Tests for ActionBar component
 * P10-F01 Architect Board Canvas - Phase 4 (T16)
 * P10-F02 Diagram Translation - Phase 4 (T19)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

// Mock the architect store
const mockPerformExport = vi.fn();
const mockTranslateTo = vi.fn();
let mockIsExporting = false;
let mockExportedSvg: string | null = null;
let mockIsTranslating = false;

vi.mock('../../stores/architectStore', () => ({
  useArchitectStore: vi.fn((selector) => {
    const state = {
      isExporting: mockIsExporting,
      performExport: mockPerformExport,
      exportedSvg: mockExportedSvg,
      isTranslating: mockIsTranslating,
      translateTo: mockTranslateTo,
    };
    return typeof selector === 'function' ? selector(state) : state;
  }),
}));

import ActionBar from './ActionBar';

describe('ActionBar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockIsExporting = false;
    mockExportedSvg = null;
    mockIsTranslating = false;
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

    it('Translate button is disabled when no SVG exported', () => {
      mockExportedSvg = null;
      render(<ActionBar />);
      const button = screen.getByTestId('translate-button');
      expect(button).toBeDisabled();
    });

    it('Translate button is enabled when SVG is exported', () => {
      mockExportedSvg = '<svg></svg>';
      render(<ActionBar />);
      const button = screen.getByTestId('translate-button');
      expect(button).not.toBeDisabled();
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

    it('Translate button has "Export SVG first" tooltip when no SVG', () => {
      mockExportedSvg = null;
      render(<ActionBar />);
      const button = screen.getByTestId('translate-button');
      expect(button).toHaveAttribute('title', 'Export SVG first');
    });

    it('Translate button has "Translate diagram" tooltip when SVG is available', () => {
      mockExportedSvg = '<svg></svg>';
      render(<ActionBar />);
      const button = screen.getByTestId('translate-button');
      expect(button).toHaveAttribute('title', 'Translate diagram');
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

  /**
   * P10-F02 Translate Dropdown Tests
   */
  describe('Translate Dropdown (P10-F02)', () => {
    it('opens dropdown when clicked with SVG exported', () => {
      mockExportedSvg = '<svg></svg>';
      render(<ActionBar />);

      const button = screen.getByTestId('translate-button');
      fireEvent.click(button);

      expect(screen.getByTestId('translate-dropdown')).toBeInTheDocument();
    });

    it('does not open dropdown when no SVG exported', () => {
      mockExportedSvg = null;
      render(<ActionBar />);

      const button = screen.getByTestId('translate-button');
      fireEvent.click(button);

      expect(screen.queryByTestId('translate-dropdown')).not.toBeInTheDocument();
    });

    it('shows PNG option in dropdown', () => {
      mockExportedSvg = '<svg></svg>';
      render(<ActionBar />);

      fireEvent.click(screen.getByTestId('translate-button'));

      expect(screen.getByTestId('translate-option-png')).toBeInTheDocument();
      // Multiple "PNG" texts may exist (tab label + dropdown), use getAllBy
      expect(screen.getAllByText(/png/i).length).toBeGreaterThan(0);
    });

    it('shows Mermaid option in dropdown', () => {
      mockExportedSvg = '<svg></svg>';
      render(<ActionBar />);

      fireEvent.click(screen.getByTestId('translate-button'));

      expect(screen.getByTestId('translate-option-mmd')).toBeInTheDocument();
      // Multiple "Mermaid" texts may exist (tab label + dropdown), use getAllBy
      expect(screen.getAllByText(/mermaid/i).length).toBeGreaterThan(0);
    });

    it('shows Draw.io option in dropdown', () => {
      mockExportedSvg = '<svg></svg>';
      render(<ActionBar />);

      fireEvent.click(screen.getByTestId('translate-button'));

      expect(screen.getByTestId('translate-option-drawio')).toBeInTheDocument();
      // The dropdown description includes "Draw.io XML"
      expect(screen.getAllByText(/draw\.io/i).length).toBeGreaterThan(0);
    });

    it('calls translateTo with PNG when PNG option clicked', async () => {
      mockExportedSvg = '<svg></svg>';
      render(<ActionBar />);

      fireEvent.click(screen.getByTestId('translate-button'));
      fireEvent.click(screen.getByTestId('translate-option-png'));

      await waitFor(() => {
        expect(mockTranslateTo).toHaveBeenCalledWith('png');
      });
    });

    it('calls translateTo with mmd when Mermaid option clicked', async () => {
      mockExportedSvg = '<svg></svg>';
      render(<ActionBar />);

      fireEvent.click(screen.getByTestId('translate-button'));
      fireEvent.click(screen.getByTestId('translate-option-mmd'));

      await waitFor(() => {
        expect(mockTranslateTo).toHaveBeenCalledWith('mmd');
      });
    });

    it('calls translateTo with drawio when Draw.io option clicked', async () => {
      mockExportedSvg = '<svg></svg>';
      render(<ActionBar />);

      fireEvent.click(screen.getByTestId('translate-button'));
      fireEvent.click(screen.getByTestId('translate-option-drawio'));

      await waitFor(() => {
        expect(mockTranslateTo).toHaveBeenCalledWith('drawio');
      });
    });

    it('closes dropdown after selecting an option', async () => {
      mockExportedSvg = '<svg></svg>';
      render(<ActionBar />);

      fireEvent.click(screen.getByTestId('translate-button'));
      fireEvent.click(screen.getByTestId('translate-option-png'));

      await waitFor(() => {
        expect(screen.queryByTestId('translate-dropdown')).not.toBeInTheDocument();
      });
    });

    it('disables translate button during translation', () => {
      mockExportedSvg = '<svg></svg>';
      mockIsTranslating = true;
      render(<ActionBar />);

      const button = screen.getByTestId('translate-button');
      expect(button).toBeDisabled();
    });

    it('shows loading spinner during translation', () => {
      mockExportedSvg = '<svg></svg>';
      mockIsTranslating = true;
      render(<ActionBar />);

      expect(screen.getByTestId('translate-spinner')).toBeInTheDocument();
    });

    it('shows "Translating..." text during translation', () => {
      mockExportedSvg = '<svg></svg>';
      mockIsTranslating = true;
      render(<ActionBar />);

      expect(screen.getByText(/translating\.\.\./i)).toBeInTheDocument();
    });

    it('has aria-expanded attribute on button', () => {
      mockExportedSvg = '<svg></svg>';
      render(<ActionBar />);

      const button = screen.getByTestId('translate-button');
      expect(button).toHaveAttribute('aria-expanded', 'false');

      fireEvent.click(button);
      expect(button).toHaveAttribute('aria-expanded', 'true');
    });

    it('dropdown has role menu', () => {
      mockExportedSvg = '<svg></svg>';
      render(<ActionBar />);

      fireEvent.click(screen.getByTestId('translate-button'));

      expect(screen.getByRole('menu')).toBeInTheDocument();
    });

    it('dropdown options have role menuitem', () => {
      mockExportedSvg = '<svg></svg>';
      render(<ActionBar />);

      fireEvent.click(screen.getByTestId('translate-button'));

      const menuItems = screen.getAllByRole('menuitem');
      expect(menuItems).toHaveLength(3);
    });
  });
});

/**
 * Tests for ExportPreview component
 * P10-F01 Architect Board Canvas - Phase 3 (T12)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

// Mock the architect store
const mockPerformExport = vi.fn();
let mockExportedSvg: string | null = null;
let mockIsExporting = false;

vi.mock('../../stores/architectStore', () => ({
  useArchitectStore: vi.fn((selector) => {
    const state = {
      exportedSvg: mockExportedSvg,
      isExporting: mockIsExporting,
      performExport: mockPerformExport,
    };
    return typeof selector === 'function' ? selector(state) : state;
  }),
}));

import ExportPreview from './ExportPreview';

describe('ExportPreview', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockExportedSvg = null;
    mockIsExporting = false;

    // Mock URL.createObjectURL and URL.revokeObjectURL
    global.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
    global.URL.revokeObjectURL = vi.fn();

    // Mock navigator.clipboard
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Empty State', () => {
    it('renders empty state when no SVG is exported', () => {
      mockExportedSvg = null;
      render(<ExportPreview />);

      expect(screen.getByText(/no export yet/i)).toBeInTheDocument();
    });

    it('shows export button in empty state', () => {
      mockExportedSvg = null;
      render(<ExportPreview />);

      expect(screen.getByTestId('export-button')).toBeInTheDocument();
    });

    it('calls performExport when export button is clicked', () => {
      mockExportedSvg = null;
      render(<ExportPreview />);

      fireEvent.click(screen.getByTestId('export-button'));
      expect(mockPerformExport).toHaveBeenCalled();
    });
  });

  describe('Loading State', () => {
    it('shows spinner when exporting', () => {
      mockIsExporting = true;
      render(<ExportPreview />);

      expect(screen.getByTestId('export-spinner')).toBeInTheDocument();
    });

    it('disables export button when exporting', () => {
      mockIsExporting = true;
      render(<ExportPreview />);

      expect(screen.getByTestId('export-button')).toBeDisabled();
    });
  });

  describe('SVG Preview', () => {
    const testSvg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100"/></svg>';

    it('renders SVG preview when SVG is available', () => {
      mockExportedSvg = testSvg;
      render(<ExportPreview />);

      expect(screen.getByTestId('svg-preview')).toBeInTheDocument();
    });

    it('SVG preview contains the exported SVG', () => {
      mockExportedSvg = testSvg;
      render(<ExportPreview />);

      const preview = screen.getByTestId('svg-preview');
      expect(preview.innerHTML).toContain('<svg');
    });

    it('SVG preview has max-width styling for scaled rendering', () => {
      mockExportedSvg = testSvg;
      render(<ExportPreview />);

      const preview = screen.getByTestId('svg-preview');
      expect(preview).toHaveClass('max-w-full');
    });
  });

  describe('Copy to Clipboard', () => {
    const testSvg = '<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>';

    it('shows copy button when SVG is available', () => {
      mockExportedSvg = testSvg;
      render(<ExportPreview />);

      expect(screen.getByTestId('copy-button')).toBeInTheDocument();
    });

    it('calls clipboard API when copy button is clicked', async () => {
      mockExportedSvg = testSvg;
      render(<ExportPreview />);

      fireEvent.click(screen.getByTestId('copy-button'));

      await waitFor(() => {
        expect(navigator.clipboard.writeText).toHaveBeenCalledWith(testSvg);
      });
    });

    it('shows success feedback after copying', async () => {
      mockExportedSvg = testSvg;
      render(<ExportPreview />);

      fireEvent.click(screen.getByTestId('copy-button'));

      await waitFor(() => {
        expect(screen.getByTestId('copy-button')).toHaveAttribute('title', 'Copied!');
      });
    });

    it('copy button has accessible label', () => {
      mockExportedSvg = testSvg;
      render(<ExportPreview />);

      expect(screen.getByTestId('copy-button')).toHaveAttribute('aria-label', 'Copy SVG to clipboard');
    });
  });

  describe('Download SVG', () => {
    const testSvg = '<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>';

    beforeEach(() => {
      // Mock document.createElement for anchor
      const originalCreateElement = document.createElement.bind(document);
      vi.spyOn(document, 'createElement').mockImplementation((tagName: string) => {
        const element = originalCreateElement(tagName);
        if (tagName === 'a') {
          element.click = vi.fn();
        }
        return element;
      });
    });

    it('shows download button when SVG is available', () => {
      mockExportedSvg = testSvg;
      render(<ExportPreview />);

      expect(screen.getByTestId('download-button')).toBeInTheDocument();
    });

    it('creates blob and triggers download when download button is clicked', () => {
      mockExportedSvg = testSvg;
      render(<ExportPreview />);

      fireEvent.click(screen.getByTestId('download-button'));

      expect(URL.createObjectURL).toHaveBeenCalled();
    });

    it('download button has accessible label', () => {
      mockExportedSvg = testSvg;
      render(<ExportPreview />);

      expect(screen.getByTestId('download-button')).toHaveAttribute('aria-label', 'Download SVG');
    });

    it('revokes object URL after download', () => {
      mockExportedSvg = testSvg;
      render(<ExportPreview />);

      fireEvent.click(screen.getByTestId('download-button'));

      expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-url');
    });
  });

  describe('Action Buttons Visibility', () => {
    it('hides copy and download buttons when no SVG', () => {
      mockExportedSvg = null;
      render(<ExportPreview />);

      expect(screen.queryByTestId('copy-button')).not.toBeInTheDocument();
      expect(screen.queryByTestId('download-button')).not.toBeInTheDocument();
    });

    it('shows re-export button when SVG is available', () => {
      mockExportedSvg = '<svg/>';
      render(<ExportPreview />);

      expect(screen.getByTestId('export-button')).toBeInTheDocument();
    });
  });

  describe('Custom className', () => {
    it('applies custom className', () => {
      render(<ExportPreview className="custom-class" />);
      expect(screen.getByTestId('export-preview')).toHaveClass('custom-class');
    });
  });

  describe('Accessibility', () => {
    it('export button has accessible label', () => {
      render(<ExportPreview />);
      expect(screen.getByTestId('export-button')).toHaveAccessibleName();
    });

    it('SVG preview has appropriate role', () => {
      mockExportedSvg = '<svg/>';
      render(<ExportPreview />);

      const preview = screen.getByTestId('svg-preview');
      expect(preview).toHaveAttribute('role', 'img');
    });

    it('SVG preview has aria-label', () => {
      mockExportedSvg = '<svg/>';
      render(<ExportPreview />);

      const preview = screen.getByTestId('svg-preview');
      expect(preview).toHaveAttribute('aria-label', 'Exported SVG preview');
    });
  });
});

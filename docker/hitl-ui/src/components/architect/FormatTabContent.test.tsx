/**
 * Tests for FormatTabContent component
 * P10-F02 Diagram Translation - Phase 4 (T15)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import FormatTabContent from './FormatTabContent';

describe('FormatTabContent', () => {
  beforeEach(() => {
    // Mock URL.createObjectURL and URL.revokeObjectURL
    global.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
    global.URL.revokeObjectURL = vi.fn();

    // Mock navigator.clipboard
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });

    // Mock atob for PNG decoding
    global.atob = vi.fn((str) => str);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Loading State', () => {
    it('shows loading spinner when loading is true', () => {
      render(<FormatTabContent content={null} format="png" loading={true} />);

      expect(screen.getByTestId('format-content-loading')).toBeInTheDocument();
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    });

    it('shows translating message when loading', () => {
      render(<FormatTabContent content={null} format="mmd" loading={true} />);

      expect(screen.getByText(/translating diagram/i)).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('shows error message when error is provided', () => {
      render(
        <FormatTabContent
          content={null}
          format="png"
          error="Model not available"
        />
      );

      expect(screen.getByTestId('format-content-error')).toBeInTheDocument();
      expect(screen.getByText(/translation failed/i)).toBeInTheDocument();
      expect(screen.getByText(/model not available/i)).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('shows empty state for SVG format', () => {
      render(<FormatTabContent content={null} format="svg" />);

      expect(screen.getByTestId('format-content-empty')).toBeInTheDocument();
      expect(screen.getByText(/no export yet/i)).toBeInTheDocument();
      expect(screen.getByText(/click export/i)).toBeInTheDocument();
    });

    it('shows empty state for PNG format', () => {
      render(<FormatTabContent content={null} format="png" />);

      expect(screen.getByTestId('format-content-empty')).toBeInTheDocument();
      expect(screen.getByText(/not translated yet/i)).toBeInTheDocument();
      expect(screen.getByText(/click translate/i)).toBeInTheDocument();
    });

    it('shows empty state for Mermaid format', () => {
      render(<FormatTabContent content={null} format="mmd" />);

      expect(screen.getByText(/not translated yet/i)).toBeInTheDocument();
    });

    it('shows empty state for Draw.io format', () => {
      render(<FormatTabContent content={null} format="drawio" />);

      expect(screen.getByText(/not translated yet/i)).toBeInTheDocument();
    });
  });

  describe('SVG Format', () => {
    const testSvg =
      '<svg xmlns="http://www.w3.org/2000/svg"><rect width="100" height="100"/></svg>';

    it('renders SVG content', () => {
      render(<FormatTabContent content={testSvg} format="svg" />);

      expect(screen.getByTestId('svg-preview')).toBeInTheDocument();
    });

    it('SVG preview has proper role and aria-label', () => {
      render(<FormatTabContent content={testSvg} format="svg" />);

      const preview = screen.getByTestId('svg-preview');
      expect(preview).toHaveAttribute('role', 'img');
      expect(preview).toHaveAttribute('aria-label', 'Exported SVG preview');
    });

    it('shows copy and download buttons', () => {
      render(<FormatTabContent content={testSvg} format="svg" />);

      expect(screen.getByTestId('copy-button')).toBeInTheDocument();
      expect(screen.getByTestId('download-button')).toBeInTheDocument();
    });
  });

  describe('PNG Format', () => {
    const testPng = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';

    it('renders PNG as img tag', () => {
      render(<FormatTabContent content={testPng} format="png" />);

      expect(screen.getByTestId('png-preview')).toBeInTheDocument();
      const img = screen.getByRole('img', { name: /translated png/i });
      expect(img).toBeInTheDocument();
    });

    it('PNG img has correct src with base64 data', () => {
      render(<FormatTabContent content={testPng} format="png" />);

      const img = screen.getByRole('img', { name: /translated png/i });
      expect(img).toHaveAttribute('src', `data:image/png;base64,${testPng}`);
    });

    it('shows copy and download buttons', () => {
      render(<FormatTabContent content={testPng} format="png" />);

      expect(screen.getByTestId('copy-button')).toBeInTheDocument();
      expect(screen.getByTestId('download-button')).toBeInTheDocument();
    });
  });

  describe('Mermaid Format', () => {
    const testMermaid = 'flowchart TB\n  A --> B\n  B --> C';

    it('renders Mermaid in code block', () => {
      render(<FormatTabContent content={testMermaid} format="mmd" />);

      expect(screen.getByTestId('mmd-preview')).toBeInTheDocument();
    });

    it('shows Mermaid content text', () => {
      render(<FormatTabContent content={testMermaid} format="mmd" />);

      expect(screen.getByText(/flowchart/i)).toBeInTheDocument();
    });

    it('shows copy and download buttons', () => {
      render(<FormatTabContent content={testMermaid} format="mmd" />);

      expect(screen.getByTestId('copy-button')).toBeInTheDocument();
      expect(screen.getByTestId('download-button')).toBeInTheDocument();
    });
  });

  describe('Draw.io Format', () => {
    const testDrawio = '<?xml version="1.0"?>\n<mxfile><diagram></diagram></mxfile>';

    it('renders Draw.io XML in code block', () => {
      render(<FormatTabContent content={testDrawio} format="drawio" />);

      expect(screen.getByTestId('drawio-preview')).toBeInTheDocument();
    });

    it('shows Draw.io XML content', () => {
      render(<FormatTabContent content={testDrawio} format="drawio" />);

      // Use getAllBy since syntax highlighting creates multiple elements for mxfile
      expect(screen.getAllByText(/mxfile/i).length).toBeGreaterThan(0);
    });

    it('shows copy and download buttons', () => {
      render(<FormatTabContent content={testDrawio} format="drawio" />);

      expect(screen.getByTestId('copy-button')).toBeInTheDocument();
      expect(screen.getByTestId('download-button')).toBeInTheDocument();
    });
  });

  describe('Copy Functionality', () => {
    it('copies content to clipboard', async () => {
      render(
        <FormatTabContent content="test content" format="mmd" />
      );

      fireEvent.click(screen.getByTestId('copy-button'));

      await waitFor(() => {
        expect(navigator.clipboard.writeText).toHaveBeenCalledWith('test content');
      });
    });

    it('shows success feedback after copying', async () => {
      render(
        <FormatTabContent content="test content" format="mmd" />
      );

      fireEvent.click(screen.getByTestId('copy-button'));

      await waitFor(() => {
        expect(screen.getByTestId('copy-button')).toHaveAttribute('title', 'Copied!');
      });
    });

    it('calls onCopy callback when provided', async () => {
      const onCopy = vi.fn();
      render(
        <FormatTabContent content="test content" format="mmd" onCopy={onCopy} />
      );

      fireEvent.click(screen.getByTestId('copy-button'));

      await waitFor(() => {
        expect(onCopy).toHaveBeenCalled();
      });
    });

    it('copy button has correct aria-label', () => {
      render(<FormatTabContent content="test" format="png" />);

      expect(screen.getByTestId('copy-button')).toHaveAttribute(
        'aria-label',
        'Copy PNG to clipboard'
      );
    });
  });

  describe('Download Functionality', () => {
    const originalCreateElement = document.createElement.bind(document);

    beforeEach(() => {
      vi.spyOn(document, 'createElement').mockImplementation((tagName: string) => {
        const element = originalCreateElement(tagName);
        if (tagName === 'a') {
          element.click = vi.fn();
        }
        return element;
      });
    });

    it('triggers download for SVG', () => {
      render(<FormatTabContent content="<svg></svg>" format="svg" />);

      fireEvent.click(screen.getByTestId('download-button'));

      expect(URL.createObjectURL).toHaveBeenCalled();
    });

    it('triggers download for PNG with binary conversion', () => {
      render(<FormatTabContent content="base64data" format="png" />);

      fireEvent.click(screen.getByTestId('download-button'));

      expect(URL.createObjectURL).toHaveBeenCalled();
      expect(atob).toHaveBeenCalledWith('base64data');
    });

    it('triggers download for Mermaid', () => {
      render(<FormatTabContent content="flowchart TB" format="mmd" />);

      fireEvent.click(screen.getByTestId('download-button'));

      expect(URL.createObjectURL).toHaveBeenCalled();
    });

    it('triggers download for Draw.io', () => {
      render(<FormatTabContent content="<mxfile/>" format="drawio" />);

      fireEvent.click(screen.getByTestId('download-button'));

      expect(URL.createObjectURL).toHaveBeenCalled();
    });

    it('revokes object URL after download', () => {
      render(<FormatTabContent content="content" format="mmd" />);

      fireEvent.click(screen.getByTestId('download-button'));

      expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-url');
    });

    it('calls onDownload callback when provided', () => {
      const onDownload = vi.fn();
      render(
        <FormatTabContent content="content" format="mmd" onDownload={onDownload} />
      );

      fireEvent.click(screen.getByTestId('download-button'));

      expect(onDownload).toHaveBeenCalled();
    });

    it('download button has correct aria-label', () => {
      render(<FormatTabContent content="test" format="mmd" />);

      expect(screen.getByTestId('download-button')).toHaveAttribute(
        'aria-label',
        'Download MMD'
      );
    });
  });

  describe('Custom className', () => {
    it('applies custom className to container', () => {
      render(
        <FormatTabContent
          content="test"
          format="mmd"
          className="custom-class"
        />
      );

      expect(screen.getByTestId('format-content')).toHaveClass('custom-class');
    });

    it('applies custom className to loading state', () => {
      render(
        <FormatTabContent
          content={null}
          format="png"
          loading={true}
          className="custom-class"
        />
      );

      expect(screen.getByTestId('format-content-loading')).toHaveClass('custom-class');
    });

    it('applies custom className to error state', () => {
      render(
        <FormatTabContent
          content={null}
          format="png"
          error="Error"
          className="custom-class"
        />
      );

      expect(screen.getByTestId('format-content-error')).toHaveClass('custom-class');
    });

    it('applies custom className to empty state', () => {
      render(
        <FormatTabContent
          content={null}
          format="png"
          className="custom-class"
        />
      );

      expect(screen.getByTestId('format-content-empty')).toHaveClass('custom-class');
    });
  });
});

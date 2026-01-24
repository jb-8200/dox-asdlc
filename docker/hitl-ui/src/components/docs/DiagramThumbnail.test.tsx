/**
 * Tests for DiagramThumbnail component
 *
 * Tests intersection observer lazy loading, loading states,
 * error handling, and render scaling.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import DiagramThumbnail from './DiagramThumbnail';

// Mock mermaid module
vi.mock('mermaid', () => ({
  default: {
    initialize: vi.fn(),
    render: vi.fn(),
  },
}));

// Mock IntersectionObserver
const mockIntersectionObserver = vi.fn();
const mockObserve = vi.fn();
const mockUnobserve = vi.fn();
const mockDisconnect = vi.fn();

// Store callback to trigger intersection
let intersectionCallback: IntersectionObserverCallback;

beforeEach(() => {
  mockIntersectionObserver.mockImplementation((callback: IntersectionObserverCallback) => {
    intersectionCallback = callback;
    return {
      observe: mockObserve,
      unobserve: mockUnobserve,
      disconnect: mockDisconnect,
    };
  });
  window.IntersectionObserver = mockIntersectionObserver as unknown as typeof IntersectionObserver;
});

afterEach(() => {
  vi.clearAllMocks();
});

describe('DiagramThumbnail', () => {
  let mermaidMock: {
    render: ReturnType<typeof vi.fn>;
    initialize: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    const mermaid = await import('mermaid');
    mermaidMock = mermaid.default as typeof mermaidMock;

    // Default successful render
    mermaidMock.render.mockResolvedValue({
      svg: '<svg data-testid="rendered-svg"><g>Test SVG</g></svg>',
    });
  });

  describe('Initial State (Before Intersection)', () => {
    it('renders placeholder before intersection', () => {
      render(<DiagramThumbnail content="graph TD; A-->B" diagramId="test-1" />);
      expect(screen.getByTestId('thumbnail-placeholder')).toBeInTheDocument();
    });

    it('does not render mermaid before intersection', () => {
      render(<DiagramThumbnail content="graph TD; A-->B" diagramId="test-1" />);
      expect(mermaidMock.render).not.toHaveBeenCalled();
    });

    it('sets up IntersectionObserver on mount', () => {
      render(<DiagramThumbnail content="graph TD; A-->B" diagramId="test-1" />);
      expect(mockIntersectionObserver).toHaveBeenCalled();
      expect(mockObserve).toHaveBeenCalled();
    });

    it('shows loading pulse animation in placeholder', () => {
      render(<DiagramThumbnail content="graph TD; A-->B" diagramId="test-1" />);
      const placeholder = screen.getByTestId('thumbnail-placeholder');
      expect(placeholder).toHaveClass('animate-pulse');
    });
  });

  describe('After Intersection', () => {
    const triggerIntersection = () => {
      act(() => {
        intersectionCallback(
          [{ isIntersecting: true } as IntersectionObserverEntry],
          {} as IntersectionObserver
        );
      });
    };

    it('renders mermaid diagram after becoming visible', async () => {
      render(<DiagramThumbnail content="graph TD; A-->B" diagramId="test-1" />);

      triggerIntersection();

      await waitFor(() => {
        expect(mermaidMock.render).toHaveBeenCalled();
      });
    });

    it('shows the rendered SVG', async () => {
      render(<DiagramThumbnail content="graph TD; A-->B" diagramId="test-1" />);

      triggerIntersection();

      await waitFor(() => {
        expect(screen.getByTestId('thumbnail-content')).toBeInTheDocument();
      });
    });

    it('hides placeholder after successful render', async () => {
      render(<DiagramThumbnail content="graph TD; A-->B" diagramId="test-1" />);

      triggerIntersection();

      await waitFor(() => {
        expect(screen.queryByTestId('thumbnail-placeholder')).not.toBeInTheDocument();
      });
    });

    it('unobserves element after intersection', async () => {
      render(<DiagramThumbnail content="graph TD; A-->B" diagramId="test-1" />);

      triggerIntersection();

      await waitFor(() => {
        expect(mockUnobserve).toHaveBeenCalled();
      });
    });
  });

  describe('Scaling', () => {
    const triggerIntersection = () => {
      act(() => {
        intersectionCallback(
          [{ isIntersecting: true } as IntersectionObserverEntry],
          {} as IntersectionObserver
        );
      });
    };

    it('applies scale transform to content', async () => {
      render(<DiagramThumbnail content="graph TD; A-->B" diagramId="test-1" />);

      triggerIntersection();

      await waitFor(() => {
        const content = screen.getByTestId('thumbnail-content');
        expect(content).toHaveStyle({ transform: 'scale(0.5)' });
      });
    });

    it('uses custom scale when provided', async () => {
      render(<DiagramThumbnail content="graph TD; A-->B" diagramId="test-1" scale={0.3} />);

      triggerIntersection();

      await waitFor(() => {
        const content = screen.getByTestId('thumbnail-content');
        expect(content).toHaveStyle({ transform: 'scale(0.3)' });
      });
    });
  });

  describe('Error State', () => {
    const triggerIntersection = () => {
      act(() => {
        intersectionCallback(
          [{ isIntersecting: true } as IntersectionObserverEntry],
          {} as IntersectionObserver
        );
      });
    };

    it('shows fallback icon on render error', async () => {
      mermaidMock.render.mockRejectedValue(new Error('Render failed'));

      render(<DiagramThumbnail content="invalid" diagramId="test-1" />);

      triggerIntersection();

      await waitFor(() => {
        expect(screen.getByTestId('thumbnail-error')).toBeInTheDocument();
      });
    });

    it('calls onError callback on failure', async () => {
      const onError = vi.fn();
      mermaidMock.render.mockRejectedValue(new Error('Render failed'));

      render(<DiagramThumbnail content="invalid" diagramId="test-1" onError={onError} />);

      triggerIntersection();

      await waitFor(() => {
        expect(onError).toHaveBeenCalled();
      });
    });

    it('does not show SVG content on error', async () => {
      mermaidMock.render.mockRejectedValue(new Error('Render failed'));

      render(<DiagramThumbnail content="invalid" diagramId="test-1" />);

      triggerIntersection();

      await waitFor(() => {
        expect(screen.queryByTestId('thumbnail-content')).not.toBeInTheDocument();
      });
    });
  });

  describe('Loading State', () => {
    const triggerIntersection = () => {
      act(() => {
        intersectionCallback(
          [{ isIntersecting: true } as IntersectionObserverEntry],
          {} as IntersectionObserver
        );
      });
    };

    it('shows loading state while rendering', async () => {
      // Make render hang
      mermaidMock.render.mockImplementation(() => new Promise(() => {}));

      render(<DiagramThumbnail content="graph TD; A-->B" diagramId="test-1" />);

      triggerIntersection();

      await waitFor(() => {
        expect(screen.getByTestId('thumbnail-loading')).toBeInTheDocument();
      });
    });

    it('hides loading state after render completes', async () => {
      render(<DiagramThumbnail content="graph TD; A-->B" diagramId="test-1" />);

      triggerIntersection();

      await waitFor(() => {
        expect(screen.queryByTestId('thumbnail-loading')).not.toBeInTheDocument();
      });
    });
  });

  describe('Props', () => {
    it('applies custom className', () => {
      render(
        <DiagramThumbnail
          content="graph TD; A-->B"
          diagramId="test-1"
          className="my-custom-class"
        />
      );
      expect(screen.getByTestId('diagram-thumbnail')).toHaveClass('my-custom-class');
    });

    it('uses unique diagramId for mermaid render', async () => {
      const triggerIntersection = () => {
        act(() => {
          intersectionCallback(
            [{ isIntersecting: true } as IntersectionObserverEntry],
            {} as IntersectionObserver
          );
        });
      };

      render(<DiagramThumbnail content="graph TD; A-->B" diagramId="unique-diagram-123" />);

      triggerIntersection();

      await waitFor(() => {
        expect(mermaidMock.render).toHaveBeenCalled();
        const call = mermaidMock.render.mock.calls[0];
        expect(call[0]).toContain('unique-diagram-123');
      });
    });
  });

  describe('Cleanup', () => {
    it('disconnects observer on unmount', () => {
      const { unmount } = render(<DiagramThumbnail content="graph TD; A-->B" diagramId="test-1" />);

      unmount();

      expect(mockDisconnect).toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    const triggerIntersection = () => {
      act(() => {
        intersectionCallback(
          [{ isIntersecting: true } as IntersectionObserverEntry],
          {} as IntersectionObserver
        );
      });
    };

    it('has appropriate aria-label', async () => {
      render(
        <DiagramThumbnail
          content="graph TD; A-->B"
          diagramId="test-1"
          ariaLabel="System architecture preview"
        />
      );

      triggerIntersection();

      await waitFor(() => {
        const thumbnail = screen.getByTestId('diagram-thumbnail');
        expect(thumbnail).toHaveAttribute('aria-label', 'System architecture preview');
      });
    });

    it('uses default aria-label when not provided', () => {
      render(<DiagramThumbnail content="graph TD; A-->B" diagramId="test-1" />);

      const thumbnail = screen.getByTestId('diagram-thumbnail');
      expect(thumbnail).toHaveAttribute('aria-label', 'Diagram thumbnail');
    });
  });
});

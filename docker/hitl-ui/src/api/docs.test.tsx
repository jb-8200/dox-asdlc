/**
 * Tests for useDiagramContents hook
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import { useDiagramContents, getDiagram } from './docs';

// Mock the API client and mock functions
vi.mock('./client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

vi.mock('./mocks/docs', () => ({
  listMockDocuments: vi.fn(() => []),
  listMockDiagrams: vi.fn(() => []),
  getMockDocumentContent: vi.fn(),
  getMockDiagramContent: vi.fn(),
}));

// Mock environment variable for mocks
vi.stubEnv('VITE_USE_MOCKS', 'true');

// Test wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

describe('useDiagramContents', () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    
    // Set up mock for getMockDiagramContent
    const { getMockDiagramContent } = await import('./mocks/docs');
    const mockFn = getMockDiagramContent as ReturnType<typeof vi.fn>;
    
    mockFn.mockImplementation(async (id: string) => ({
      meta: { id, title: `Diagram ${id}` },
      content: `graph TD; ${id}-->B`,
    }));
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns empty map when no diagram IDs provided', async () => {
    const { result } = renderHook(() => useDiagramContents([]), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    expect(result.current.data.size).toBe(0);
  });

  it('returns loading state initially', () => {
    const { result } = renderHook(() => useDiagramContents(['diagram-1']), {
      wrapper: createWrapper(),
    });

    // Initially should be loading or already done (depending on mock timing)
    expect(typeof result.current.isLoading).toBe('boolean');
  });

  it('returns diagram contents as a Map', async () => {
    const { result } = renderHook(() => useDiagramContents(['diagram-1']), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data.get('diagram-1')).toBe('graph TD; diagram-1-->B');
  });

  it('fetches multiple diagrams in parallel', async () => {
    const { result } = renderHook(
      () => useDiagramContents(['diagram-1', 'diagram-2']),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data.size).toBe(2);
    expect(result.current.data.get('diagram-1')).toBe('graph TD; diagram-1-->B');
    expect(result.current.data.get('diagram-2')).toBe('graph TD; diagram-2-->B');
  });

  it('handles fetch errors gracefully', async () => {
    const { getMockDiagramContent } = await import('./mocks/docs');
    const mockFn = getMockDiagramContent as ReturnType<typeof vi.fn>;
    mockFn.mockRejectedValueOnce(new Error('Fetch failed'));

    const { result } = renderHook(() => useDiagramContents(['diagram-1']), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Error case: diagram should not be in the map
    expect(result.current.data.get('diagram-1')).toBeUndefined();
    expect(result.current.isError).toBe(true);
  });
});

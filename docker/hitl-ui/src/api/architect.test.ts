/**
 * Tests for Architect API Client
 * P10-F02 Diagram Translation - Phase 2 (T09)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { translateDiagram, TranslateApiError } from './architect';
import type { TranslateResponse, TranslationError } from './types/architect';

// Mock the api client
const mockPost = vi.fn();
vi.mock('./client', () => ({
  apiClient: {
    post: (...args: unknown[]) => mockPost(...args),
  },
}));

// Mock the mocks module
vi.mock('./mocks/architect', () => ({
  mockTranslateDiagram: vi.fn().mockResolvedValue({
    content: 'mock-content',
    format: 'mmd',
    modelUsed: 'mock-model',
  }),
}));

describe('architect API client', () => {
  const testSvg = '<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>';

  beforeEach(() => {
    vi.clearAllMocks();
    // Reset env variable
    vi.stubEnv('VITE_USE_MOCKS', 'false');
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  describe('translateDiagram', () => {
    describe('real API mode', () => {
      it('calls the correct endpoint with PNG format', async () => {
        const mockResponse: TranslateResponse = {
          content: 'base64data',
          format: 'png',
          modelUsed: 'gemini-2.5-flash',
          metadata: { width: 1024, height: 768 },
        };

        mockPost.mockResolvedValue({ data: mockResponse });

        const result = await translateDiagram(testSvg, 'png');

        expect(mockPost).toHaveBeenCalledWith(
          '/architect/translate',
          {
            svgContent: testSvg,
            format: 'png',
            options: undefined,
          },
          { timeout: 60000 }
        );
        expect(result).toEqual(mockResponse);
      });

      it('calls the correct endpoint with Mermaid format', async () => {
        const mockResponse: TranslateResponse = {
          content: 'flowchart TB\n  A --> B',
          format: 'mmd',
          modelUsed: 'claude-sonnet-4-20250514',
          metadata: { diagramType: 'flowchart' },
        };

        mockPost.mockResolvedValue({ data: mockResponse });

        const result = await translateDiagram(testSvg, 'mmd');

        expect(mockPost).toHaveBeenCalledWith(
          '/architect/translate',
          {
            svgContent: testSvg,
            format: 'mmd',
            options: undefined,
          },
          { timeout: 60000 }
        );
        expect(result.format).toBe('mmd');
      });

      it('calls the correct endpoint with Draw.io format', async () => {
        const mockResponse: TranslateResponse = {
          content: '<?xml version="1.0"?>',
          format: 'drawio',
          modelUsed: 'claude-sonnet-4-20250514',
        };

        mockPost.mockResolvedValue({ data: mockResponse });

        const result = await translateDiagram(testSvg, 'drawio');

        expect(mockPost).toHaveBeenCalledWith(
          '/architect/translate',
          {
            svgContent: testSvg,
            format: 'drawio',
            options: undefined,
          },
          { timeout: 60000 }
        );
        expect(result.format).toBe('drawio');
      });

      it('passes options when provided', async () => {
        const mockResponse: TranslateResponse = {
          content: 'base64data',
          format: 'png',
          modelUsed: 'gemini-2.5-flash',
        };

        mockPost.mockResolvedValue({ data: mockResponse });

        await translateDiagram(testSvg, 'png', { size: '4k' });

        expect(mockPost).toHaveBeenCalledWith(
          '/architect/translate',
          {
            svgContent: testSvg,
            format: 'png',
            options: { size: '4k' },
          },
          { timeout: 60000 }
        );
      });

      it('passes diagramType hint for Mermaid', async () => {
        const mockResponse: TranslateResponse = {
          content: 'sequenceDiagram',
          format: 'mmd',
          modelUsed: 'claude-sonnet-4-20250514',
        };

        mockPost.mockResolvedValue({ data: mockResponse });

        await translateDiagram(testSvg, 'mmd', { diagramType: 'sequence' });

        expect(mockPost).toHaveBeenCalledWith(
          '/architect/translate',
          {
            svgContent: testSvg,
            format: 'mmd',
            options: { diagramType: 'sequence' },
          },
          { timeout: 60000 }
        );
      });
    });

    describe('error handling', () => {
      it('throws TranslateApiError for API errors with code', async () => {
        const errorResponse: TranslationError = {
          error: 'Model not available',
          code: 'MODEL_ERROR',
          details: 'Gemini API key not configured',
        };

        mockPost.mockRejectedValue({
          response: {
            data: errorResponse,
            status: 500,
          },
        });

        await expect(translateDiagram(testSvg, 'png')).rejects.toThrow(
          TranslateApiError
        );

        try {
          await translateDiagram(testSvg, 'png');
        } catch (error) {
          expect(error).toBeInstanceOf(TranslateApiError);
          const apiError = error as TranslateApiError;
          expect(apiError.code).toBe('MODEL_ERROR');
          expect(apiError.details).toBe('Gemini API key not configured');
        }
      });

      it('throws TranslateApiError for rate limit errors', async () => {
        const errorResponse: TranslationError = {
          error: 'Rate limit exceeded',
          code: 'RATE_LIMIT',
        };

        mockPost.mockRejectedValue({
          response: {
            data: errorResponse,
            status: 429,
          },
        });

        await expect(translateDiagram(testSvg, 'mmd')).rejects.toThrow(
          TranslateApiError
        );
      });

      it('throws TranslateApiError for invalid SVG', async () => {
        const errorResponse: TranslationError = {
          error: 'Invalid SVG content',
          code: 'SVG_PARSE_ERROR',
        };

        mockPost.mockRejectedValue({
          response: {
            data: errorResponse,
            status: 400,
          },
        });

        await expect(translateDiagram('not-svg', 'png')).rejects.toThrow(
          TranslateApiError
        );
      });

      it('re-throws unknown errors', async () => {
        const networkError = new Error('Network error');
        mockPost.mockRejectedValue(networkError);

        await expect(translateDiagram(testSvg, 'png')).rejects.toThrow(
          'Network error'
        );
      });

      it('re-throws errors without response data', async () => {
        mockPost.mockRejectedValue({
          response: { status: 500 },
        });

        await expect(translateDiagram(testSvg, 'png')).rejects.toBeTruthy();
      });
    });

    describe('mock mode', () => {
      beforeEach(() => {
        vi.stubEnv('VITE_USE_MOCKS', 'true');
      });

      it('uses mock implementation when VITE_USE_MOCKS is true', async () => {
        const result = await translateDiagram(testSvg, 'mmd');

        // Real API should not be called
        expect(mockPost).not.toHaveBeenCalled();

        // Mock response should be returned
        expect(result).toBeDefined();
        expect(result.content).toBe('mock-content');
      });
    });
  });

  describe('TranslateApiError', () => {
    it('contains error code and details', () => {
      const errorData: TranslationError = {
        error: 'Test error',
        code: 'INVALID_FORMAT',
        details: 'Additional info',
      };

      const error = new TranslateApiError(errorData);

      expect(error.name).toBe('TranslateApiError');
      expect(error.message).toBe('Test error');
      expect(error.code).toBe('INVALID_FORMAT');
      expect(error.details).toBe('Additional info');
    });

    it('works without details', () => {
      const errorData: TranslationError = {
        error: 'Simple error',
        code: 'MODEL_ERROR',
      };

      const error = new TranslateApiError(errorData);

      expect(error.code).toBe('MODEL_ERROR');
      expect(error.details).toBeUndefined();
    });
  });
});

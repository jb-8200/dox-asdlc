/**
 * Architect API Client
 * P10-F02 Diagram Translation
 *
 * Provides functions for interacting with the architect translation API.
 * Supports mock mode when VITE_USE_MOCKS=true.
 */

import { apiClient } from './client';
import type {
  TranslationFormat,
  TranslateResponse,
  TranslateOptions,
  TranslationError,
} from './types/architect';
import { mockTranslateDiagram } from './mocks/architect';

/**
 * Check if mocks are enabled
 */
function areMocksEnabled(): boolean {
  return import.meta.env.VITE_USE_MOCKS === 'true';
}

/**
 * Error class for translation API errors
 */
export class TranslateApiError extends Error {
  code: string;
  details?: string;

  constructor(error: TranslationError) {
    super(error.error);
    this.name = 'TranslateApiError';
    this.code = error.code;
    this.details = error.details;
  }
}

/**
 * Translate an SVG diagram to a different format using LLM services.
 *
 * @param svgContent - The raw SVG content string from Excalidraw export
 * @param format - Target translation format ('png', 'mmd', or 'drawio')
 * @param options - Optional translation options (size for PNG, diagramType hint for Mermaid)
 * @returns Promise resolving to the translation response
 * @throws TranslateApiError if the translation fails
 *
 * @example
 * ```typescript
 * const result = await translateDiagram(svgContent, 'mmd');
 * console.log(result.content); // Mermaid diagram syntax
 * ```
 */
export async function translateDiagram(
  svgContent: string,
  format: TranslationFormat,
  options?: TranslateOptions
): Promise<TranslateResponse> {
  // Use mock implementation if mocks are enabled
  if (areMocksEnabled()) {
    return mockTranslateDiagram(svgContent, format, options);
  }

  try {
    const response = await apiClient.post<TranslateResponse>(
      '/architect/translate',
      {
        svgContent,
        format,
        options,
      },
      {
        // Longer timeout for LLM translations
        timeout: 60000,
      }
    );

    return response.data;
  } catch (error) {
    // Handle axios errors
    if (error && typeof error === 'object' && 'response' in error) {
      const axiosError = error as {
        response?: { data?: TranslationError; status?: number };
      };
      if (axiosError.response?.data?.code) {
        throw new TranslateApiError(axiosError.response.data);
      }
    }

    // Re-throw unknown errors
    throw error;
  }
}

/**
 * Structure API Client
 *
 * Agent 6: Document Structure Hook Builder
 * Wave 1 - BBox Overlay React Implementation
 *
 * Provides API client for fetching document structure data with bounding boxes.
 * Integrates with the existing API service patterns for consistent error handling.
 *
 * API Endpoint: GET /api/documents/{doc_id}/pages/{page}/structure
 * Backend: src/api/structure.py, src/processing/api/structure_endpoints.py
 */

import type { PageStructure, StructureErrorResponse } from '../types/structure';

// Base configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || '';
const REQUEST_TIMEOUT = 30000; // 30 seconds

/**
 * Custom Structure API Error class
 */
export class StructureAPIError extends Error {
  statusCode: number;
  endpoint: string;
  code?: string;
  details?: Record<string, any>;

  constructor(
    message: string,
    statusCode: number,
    endpoint: string,
    code?: string,
    details?: Record<string, any>
  ) {
    super(message);
    this.name = 'StructureAPIError';
    this.statusCode = statusCode;
    this.endpoint = endpoint;
    this.code = code;
    this.details = details;
  }
}

/**
 * Make fetch request with timeout
 *
 * @param url - Request URL
 * @param options - Fetch options
 * @param timeout - Timeout in milliseconds
 * @returns Fetch response
 * @throws StructureAPIError On timeout or network error
 */
async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeout: number = REQUEST_TIMEOUT
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    if ((error as Error).name === 'AbortError') {
      throw new StructureAPIError('Request timeout', 408, url);
    }
    throw new StructureAPIError(
      'Network request failed',
      0,
      url,
      'NETWORK_ERROR',
      { originalError: error }
    );
  }
}

/**
 * Handle API response
 *
 * @param response - Fetch response
 * @param endpoint - API endpoint
 * @returns Parsed JSON response
 * @throws StructureAPIError On HTTP error
 */
async function handleResponse<T>(response: Response, endpoint: string): Promise<T> {
  if (!response.ok) {
    // Try to parse error response
    let errorData: StructureErrorResponse;
    try {
      const data = await response.json();
      // Handle both direct error format and detail wrapper
      errorData = data.detail || data;
    } catch {
      errorData = {
        error: 'Unknown error',
        code: 'UNKNOWN_ERROR',
        details: {},
      };
    }

    const message = errorData.error || `HTTP ${response.status}`;
    throw new StructureAPIError(
      message,
      response.status,
      endpoint,
      errorData.code,
      errorData.details
    );
  }

  return response.json();
}

/**
 * Fetch page structure with bounding boxes
 *
 * Retrieves document structure elements (headings, tables, pictures, etc.)
 * with bounding box coordinates for a specific page.
 *
 * @param docId - Document ID
 * @param page - Page number (1-indexed)
 * @returns Page structure with elements and bounding boxes
 * @throws StructureAPIError On validation error, not found, or server error
 *
 * @example
 * ```ts
 * const structure = await fetchPageStructure('a1b2c3d4', 1);
 * console.log(`Found ${structure.headings.length} headings`);
 * ```
 */
export async function fetchPageStructure(
  docId: string,
  page: number
): Promise<PageStructure> {
  // Validate inputs
  if (!docId || !/^[a-zA-Z0-9\-]{8,64}$/.test(docId)) {
    throw new StructureAPIError(
      'Invalid document ID format',
      400,
      'fetchPageStructure',
      'INVALID_DOC_ID',
      { docId }
    );
  }

  if (page < 1 || !Number.isInteger(page)) {
    throw new StructureAPIError(
      'Invalid page number (must be integer >= 1)',
      400,
      'fetchPageStructure',
      'INVALID_PAGE',
      { page }
    );
  }

  const url = `${API_BASE_URL}/api/documents/${docId}/pages/${page}/structure`;
  const response = await fetchWithTimeout(url);
  return handleResponse<PageStructure>(response, url);
}

/**
 * Check if error is a StructureAPIError
 */
export function isStructureAPIError(error: unknown): error is StructureAPIError {
  return error instanceof StructureAPIError;
}

/**
 * Check if error is a "not found" error
 */
export function isNotFoundError(error: unknown): boolean {
  return isStructureAPIError(error) && error.statusCode === 404;
}

/**
 * Check if error is a validation error
 */
export function isValidationError(error: unknown): boolean {
  return isStructureAPIError(error) && error.statusCode === 422;
}

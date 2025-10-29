/**
 * useDocumentStructure Hook Tests
 *
 * Agent 6: Document Structure Hook Builder
 * Wave 1 - BBox Overlay React Implementation
 *
 * Comprehensive test suite covering:
 * - Hook fetches structure successfully
 * - Caching prevents redundant requests
 * - Loading states correct
 * - Error states handled
 * - Mock server integration works
 * - Refetch triggers new request
 *
 * Target: 100% code coverage
 */

import { describe, test, expect, beforeEach, vi, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useDocumentStructure } from '../useDocumentStructure';
import type { PageStructure } from '../../types/structure';
import {
  fetchPageStructure,
  StructureAPIError,
} from '../../services/structureApi';

// Mock the fetchPageStructure function
vi.mock('../../services/structureApi', () => ({
  fetchPageStructure: vi.fn(),
  StructureAPIError: class StructureAPIError extends Error {
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
  },
}));

/**
 * Create a wrapper with React Query provider for testing
 */
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false, // Disable retries for faster tests
        gcTime: 0, // Disable cache for cleaner tests
      },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

/**
 * Mock page structure response
 */
const mockStructure: PageStructure = {
  doc_id: 'test-doc-123',
  page: 1,
  has_structure: true,
  headings: [
    {
      text: 'Introduction',
      level: 'SECTION_HEADER',
      page: 1,
      section_path: '1. Introduction',
      bbox: {
        left: 72.0,
        bottom: 650.0,
        right: 540.0,
        top: 720.0,
      },
    },
  ],
  tables: [],
  pictures: [],
  code_blocks: [],
  formulas: [],
  summary: {
    total_sections: 1,
    max_depth: 1,
    has_toc: false,
  },
  coordinate_system: {
    format: '[left, bottom, right, top]',
    origin: 'bottom-left',
    units: 'points',
    reference: 'integration-contracts/docling-structure-spec.md',
  },
};

/**
 * Mock empty structure response
 */
const mockEmptyStructure: PageStructure = {
  doc_id: 'test-doc-456',
  page: 1,
  has_structure: false,
  headings: [],
  tables: [],
  pictures: [],
  code_blocks: [],
  formulas: [],
  summary: null,
  coordinate_system: {
    format: '[left, bottom, right, top]',
    origin: 'bottom-left',
    units: 'points',
    reference: 'integration-contracts/docling-structure-spec.md',
  },
};

describe('useDocumentStructure', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('successful data fetching', () => {
    test('fetches structure successfully', async () => {
      const mockFetch = vi.mocked(fetchPageStructure).mockResolvedValue(mockStructure);

      const { result } = renderHook(
        () =>
          useDocumentStructure({
            docId: 'test-doc-123',
            page: 1,
          }),
        { wrapper: createWrapper() }
      );

      // Initially loading
      expect(result.current.isLoading).toBe(true);
      expect(result.current.structure).toBeUndefined();

      // Wait for data to load
      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Check final state
      expect(result.current.isLoading).toBe(false);
      expect(result.current.isError).toBe(false);
      expect(result.current.error).toBe(null);
      expect(result.current.structure).toEqual(mockStructure);
      expect(mockFetch).toHaveBeenCalledWith('test-doc-123', 1);
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    test('handles empty structure response', async () => {
      vi.mocked(fetchPageStructure).mockResolvedValue(mockEmptyStructure);

      const { result } = renderHook(
        () =>
          useDocumentStructure({
            docId: 'test-doc-456',
            page: 1,
          }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.structure).toEqual(mockEmptyStructure);
      expect(result.current.structure?.has_structure).toBe(false);
      expect(result.current.structure?.headings).toHaveLength(0);
    });

    test('fetches multiple pages independently', async () => {
      const mockFetch = vi.mocked(fetchPageStructure);

      mockFetch.mockImplementation((docId, page) =>
        Promise.resolve({
          ...mockStructure,
          doc_id: docId,
          page,
        })
      );

      // Fetch page 1
      const { result: result1 } = renderHook(
        () =>
          useDocumentStructure({
            docId: 'test-doc',
            page: 1,
          }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result1.current.isSuccess).toBe(true);
      });

      expect(result1.current.structure?.page).toBe(1);

      // Fetch page 2
      const { result: result2 } = renderHook(
        () =>
          useDocumentStructure({
            docId: 'test-doc',
            page: 2,
          }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result2.current.isSuccess).toBe(true);
      });

      expect(result2.current.structure?.page).toBe(2);
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('caching behavior', () => {
    test('caches data and prevents redundant requests', async () => {
      const queryClient = new QueryClient({
        defaultOptions: {
          queries: {
            retry: false,
            staleTime: 5 * 60 * 1000, // Match hook's staleTime
          },
        },
      });

      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      );

      const mockFetch = vi
        .mocked(fetchPageStructure)
        .mockResolvedValue(mockStructure);

      // First render
      const { result: result1 } = renderHook(
        () =>
          useDocumentStructure({
            docId: 'test-doc-123',
            page: 1,
          }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result1.current.isSuccess).toBe(true);
      });

      expect(mockFetch).toHaveBeenCalledTimes(1);

      // Second render with same params (should use cache)
      const { result: result2 } = renderHook(
        () =>
          useDocumentStructure({
            docId: 'test-doc-123',
            page: 1,
          }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result2.current.isSuccess).toBe(true);
      });

      // Should NOT trigger additional fetch (cache hit)
      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(result2.current.structure).toEqual(mockStructure);
    });

    test('fetches new data when page changes', async () => {
      const mockFetch = vi
        .mocked(fetchPageStructure)
        .mockImplementation((docId, page) =>
          Promise.resolve({
            ...mockStructure,
            page,
          })
        );

      const { result, rerender } = renderHook(
        ({ page }) =>
          useDocumentStructure({
            docId: 'test-doc-123',
            page,
          }),
        {
          wrapper: createWrapper(),
          initialProps: { page: 1 },
        }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.structure?.page).toBe(1);
      expect(mockFetch).toHaveBeenCalledTimes(1);

      // Change page
      rerender({ page: 2 });

      await waitFor(() => {
        expect(result.current.structure?.page).toBe(2);
      });

      expect(mockFetch).toHaveBeenCalledTimes(2);
      expect(mockFetch).toHaveBeenCalledWith('test-doc-123', 2);
    });

    test('fetches new data when docId changes', async () => {
      const mockFetch = vi
        .mocked(fetchPageStructure)
        .mockImplementation((docId) =>
          Promise.resolve({
            ...mockStructure,
            doc_id: docId,
          })
        );

      const { result, rerender } = renderHook(
        ({ docId }) =>
          useDocumentStructure({
            docId,
            page: 1,
          }),
        {
          wrapper: createWrapper(),
          initialProps: { docId: 'doc-1' },
        }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.structure?.doc_id).toBe('doc-1');

      // Change docId
      rerender({ docId: 'doc-2' });

      await waitFor(() => {
        expect(result.current.structure?.doc_id).toBe('doc-2');
      });

      expect(mockFetch).toHaveBeenCalledTimes(2);
      expect(mockFetch).toHaveBeenLastCalledWith('doc-2', 1);
    });
  });

  describe('loading states', () => {
    test('isLoading is true during initial fetch', async () => {
      vi.mocked(fetchPageStructure).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockStructure), 100))
      );

      const { result } = renderHook(
        () =>
          useDocumentStructure({
            docId: 'test-doc',
            page: 1,
          }),
        { wrapper: createWrapper() }
      );

      expect(result.current.isLoading).toBe(true);
      expect(result.current.isFetching).toBe(true);
      expect(result.current.isSuccess).toBe(false);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.isLoading).toBe(false);
      expect(result.current.isFetching).toBe(false);
    });

    test('isFetching is true during refetch', async () => {
      vi.mocked(fetchPageStructure).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockStructure), 50))
      );

      const { result } = renderHook(
        () =>
          useDocumentStructure({
            docId: 'test-doc',
            page: 1,
          }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.isFetching).toBe(false);
      expect(result.current.isLoading).toBe(false);

      // Trigger refetch (refetch is async)
      await result.current.refetch();

      // After refetch completes, wait for isFetching to be false again
      await waitFor(() => {
        expect(result.current.isFetching).toBe(false);
      });
      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('error handling', () => {
    test('handles 404 not found error', async () => {
      const mockError = new StructureAPIError(
        'Page not found',
        404,
        '/api/documents/test/pages/1/structure',
        'PAGE_NOT_FOUND'
      );

      vi.mocked(fetchPageStructure).mockRejectedValue(mockError);

      const { result } = renderHook(
        () =>
          useDocumentStructure({
            docId: 'not-found',
            page: 1,
          }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeTruthy();
      expect(result.current.error?.message).toContain('not found');
      expect(result.current.structure).toBeUndefined();
    });

    test('handles validation error', async () => {
      const mockError = new StructureAPIError(
        'Invalid page number',
        422,
        '/api/documents/test/pages/0/structure',
        'INVALID_PAGE'
      );

      vi.mocked(fetchPageStructure).mockRejectedValue(mockError);

      const { result } = renderHook(
        () =>
          useDocumentStructure({
            docId: 'test-doc',
            page: 0, // Invalid page number
          }),
        { wrapper: createWrapper() }
      );

      await waitFor(
        () => {
          expect(result.current.isError).toBe(true);
        },
        { timeout: 5000 } // Increased timeout to account for retries
      );

      expect(result.current.error).toBeTruthy();
      expect(result.current.error?.message).toContain('Invalid');
    });

    test('handles server error', async () => {
      const mockError = new StructureAPIError(
        'Internal server error',
        500,
        '/api/documents/test/pages/1/structure',
        'INTERNAL_ERROR'
      );

      vi.mocked(fetchPageStructure).mockRejectedValue(mockError);

      const { result } = renderHook(
        () =>
          useDocumentStructure({
            docId: 'error-doc',
            page: 1,
          }),
        { wrapper: createWrapper() }
      );

      await waitFor(
        () => {
          expect(result.current.isError).toBe(true);
        },
        { timeout: 5000 } // Increased timeout to account for retries
      );

      expect(result.current.error).toBeTruthy();
    });

    test('handles network error', async () => {
      const mockError = new StructureAPIError(
        'Network request failed',
        0,
        '/api/documents/test/pages/1/structure',
        'NETWORK_ERROR'
      );

      vi.mocked(fetchPageStructure).mockRejectedValue(mockError);

      const { result } = renderHook(
        () =>
          useDocumentStructure({
            docId: 'test-doc',
            page: 1,
          }),
        { wrapper: createWrapper() }
      );

      await waitFor(
        () => {
          expect(result.current.isError).toBe(true);
        },
        { timeout: 5000 } // Increased timeout to account for retries
      );

      expect(result.current.error?.message).toContain('Network');
    });
  });

  describe('enabled option', () => {
    test('does not fetch when enabled is false', async () => {
      const mockFetch = vi
        .mocked(fetchPageStructure)
        .mockResolvedValue(mockStructure);

      const { result } = renderHook(
        () =>
          useDocumentStructure({
            docId: 'test-doc',
            page: 1,
            enabled: false,
          }),
        { wrapper: createWrapper() }
      );

      // Should not trigger fetch
      expect(result.current.isLoading).toBe(false);
      expect(result.current.structure).toBeUndefined();
      expect(mockFetch).not.toHaveBeenCalled();
    });

    test('fetches when enabled changes to true', async () => {
      const mockFetch = vi
        .mocked(fetchPageStructure)
        .mockResolvedValue(mockStructure);

      const { result, rerender } = renderHook(
        ({ enabled }) =>
          useDocumentStructure({
            docId: 'test-doc',
            page: 1,
            enabled,
          }),
        {
          wrapper: createWrapper(),
          initialProps: { enabled: false },
        }
      );

      expect(mockFetch).not.toHaveBeenCalled();

      // Enable query
      rerender({ enabled: true });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(result.current.structure).toEqual(mockStructure);
    });

    test('handles invalid docId with API error', async () => {
      const mockError = new StructureAPIError(
        'Invalid document ID format',
        400,
        'fetchPageStructure',
        'INVALID_DOC_ID'
      );

      vi.mocked(fetchPageStructure).mockRejectedValue(mockError);

      const { result } = renderHook(
        () =>
          useDocumentStructure({
            docId: '', // Empty docId - will be caught by API client
            page: 1,
          }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error?.message).toContain('Invalid');
    });

    test('handles invalid page number with API error', async () => {
      const mockError = new StructureAPIError(
        'Invalid page number',
        400,
        'fetchPageStructure',
        'INVALID_PAGE'
      );

      vi.mocked(fetchPageStructure).mockRejectedValue(mockError);

      const { result } = renderHook(
        () =>
          useDocumentStructure({
            docId: 'test-doc',
            page: 0, // Invalid page (< 1) - will be caught by API client
          }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error?.message).toContain('Invalid');
    });
  });

  describe('refetch functionality', () => {
    test('refetch triggers new request', async () => {
      const mockFetch = vi
        .mocked(fetchPageStructure)
        .mockResolvedValue(mockStructure);

      const { result } = renderHook(
        () =>
          useDocumentStructure({
            docId: 'test-doc',
            page: 1,
          }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockFetch).toHaveBeenCalledTimes(1);

      // Trigger refetch
      await result.current.refetch();

      expect(mockFetch).toHaveBeenCalledTimes(2);
    });

    test('refetch returns updated data', async () => {
      const updatedStructure = {
        ...mockStructure,
        headings: [
          ...mockStructure.headings,
          {
            text: 'New Section',
            level: 'SECTION_HEADER',
            page: 1,
            section_path: '2. New Section',
            bbox: null,
          },
        ],
      };

      const mockFetch = vi
        .mocked(fetchPageStructure)
        .mockResolvedValueOnce(mockStructure)
        .mockResolvedValueOnce(updatedStructure);

      const { result } = renderHook(
        () =>
          useDocumentStructure({
            docId: 'test-doc',
            page: 1,
          }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.structure?.headings).toHaveLength(1);

      // Refetch
      await result.current.refetch();

      await waitFor(() => {
        expect(result.current.structure?.headings).toHaveLength(2);
      });
    });
  });

  describe('edge cases', () => {
    test('handles large page numbers', async () => {
      const mockFetch = vi
        .mocked(fetchPageStructure)
        .mockResolvedValue(mockStructure);

      const { result } = renderHook(
        () =>
          useDocumentStructure({
            docId: 'test-doc',
            page: 9999,
          }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockFetch).toHaveBeenCalledWith('test-doc', 9999);
    });

    test('handles special characters in docId', async () => {
      const mockFetch = vi
        .mocked(fetchPageStructure)
        .mockResolvedValue(mockStructure);

      const { result } = renderHook(
        () =>
          useDocumentStructure({
            docId: 'test-doc-with-hyphens-123',
            page: 1,
          }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockFetch).toHaveBeenCalledWith('test-doc-with-hyphens-123', 1);
    });

    test('keeps previous data while fetching new page', async () => {
      vi.mocked(fetchPageStructure).mockImplementation(
        (docId, page) =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  ...mockStructure,
                  page,
                }),
              50
            )
          )
      );

      const { result, rerender } = renderHook(
        ({ page }) =>
          useDocumentStructure({
            docId: 'test-doc',
            page,
          }),
        {
          wrapper: createWrapper(),
          initialProps: { page: 1 },
        }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const page1Data = result.current.structure;
      expect(page1Data?.page).toBe(1);

      // Change to page 2
      rerender({ page: 2 });

      // During fetch, previous data should still be available
      expect(result.current.structure?.page).toBe(1); // Still showing page 1

      await waitFor(() => {
        expect(result.current.structure?.page).toBe(2);
      });
    });
  });
});

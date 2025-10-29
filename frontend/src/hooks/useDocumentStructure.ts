/**
 * useDocumentStructure Hook - Fetch and cache document structure data
 *
 * Agent 6: Document Structure Hook Builder
 * Wave 1 - BBox Overlay React Implementation
 *
 * React Query wrapper for fetching document structure with bounding boxes.
 * Provides caching, loading states, and error handling for structure data.
 *
 * Features:
 * - 5-minute staleTime for optimal caching
 * - Automatic refetch on page change
 * - Keep previous data while fetching new
 * - Type-safe error handling
 *
 * @example
 * ```tsx
 * function DocumentViewer({ docId, page }) {
 *   const { structure, isLoading, error } = useDocumentStructure({
 *     docId,
 *     page,
 *     enabled: true,
 *   });
 *
 *   if (isLoading) return <Spinner />;
 *   if (error) return <Error message={error.message} />;
 *
 *   return (
 *     <div>
 *       {structure?.headings.map(heading => (
 *         <Heading key={heading.text} data={heading} />
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 */

import { useQuery } from '@tanstack/react-query';
import type { PageStructure } from '../types/structure';
import { fetchPageStructure } from '../services/structureApi';

/**
 * Options for useDocumentStructure hook
 */
export interface UseDocumentStructureOptions {
  /** Document ID */
  docId: string;
  /** Page number (1-indexed) */
  page: number;
  /** Whether the query should run (default: true) */
  enabled?: boolean;
}

/**
 * Result from useDocumentStructure hook
 */
export interface UseDocumentStructureResult {
  /** Page structure data (undefined while loading or on error) */
  structure: PageStructure | undefined;
  /** True while fetching data */
  isLoading: boolean;
  /** True if query encountered an error */
  isError: boolean;
  /** Error object if query failed */
  error: Error | null;
  /** Function to manually refetch the data */
  refetch: () => Promise<void>;
  /** True while refetching data (subsequent fetches) */
  isFetching: boolean;
  /** True if data has been fetched successfully at least once */
  isSuccess: boolean;
}

/**
 * Hook for fetching document structure with bounding boxes
 *
 * Uses React Query for caching and automatic refetching.
 * Cache key: ['documentStructure', docId, page]
 *
 * @param options - Hook options
 * @returns Query result with structure data and loading states
 *
 * @example
 * ```tsx
 * // Basic usage
 * const { structure, isLoading } = useDocumentStructure({
 *   docId: 'abc123',
 *   page: 1,
 * });
 *
 * // Conditional fetching
 * const { structure } = useDocumentStructure({
 *   docId: 'abc123',
 *   page: currentPage,
 *   enabled: isViewerOpen,
 * });
 * ```
 */
export function useDocumentStructure(
  options: UseDocumentStructureOptions
): UseDocumentStructureResult {
  const { docId, page, enabled = true } = options;

  const query = useQuery({
    queryKey: ['documentStructure', docId, page],
    queryFn: () => fetchPageStructure(docId, page),
    enabled: enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (previously cacheTime)
    retry: (failureCount, error) => {
      // Don't retry on 404 (page not found) or validation errors
      if (error instanceof Error) {
        const isNotFound = error.message.includes('not found');
        const isValidation = error.message.includes('Invalid');
        if (isNotFound || isValidation) {
          return false;
        }
      }
      // Retry up to 2 times for other errors
      return failureCount < 2;
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    // Keep previous data while fetching new page
    placeholderData: (previousData) => previousData,
  });

  return {
    structure: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: async () => {
      await query.refetch();
    },
    isFetching: query.isFetching,
    isSuccess: query.isSuccess,
  };
}

/**
 * Export type for external use
 */
export type { PageStructure };

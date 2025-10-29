/**
 * useChunkNavigation Hook
 *
 * Agent 10: URL Parameter Chunk Navigation
 * Wave 1 - BBox Overlay React Implementation
 *
 * React hook for parsing chunk parameters from URLs and navigating to chunks.
 * Integrates with React Router 7 for URL management and provides callbacks
 * for chunk navigation.
 *
 * Features:
 * - Parse chunk parameter on mount
 * - Fire callback when chunk parameter exists
 * - Optional URL updating when navigating
 * - Works seamlessly with React Router
 * - Handles invalid chunk IDs gracefully
 *
 * @example
 * // Basic usage
 * const { initialChunkId, navigateToChunk } = useChunkNavigation({
 *   onChunkNavigate: (chunkId) => {
 *     scrollToChunk(chunkId);
 *     setActiveChunkId(chunkId);
 *   }
 * });
 *
 * // With URL updating
 * const { navigateToChunk } = useChunkNavigation({
 *   onChunkNavigate: handleChunkChange,
 *   updateUrl: true
 * });
 *
 * // Programmatic navigation
 * navigateToChunk('chunk-0-page-1', true); // Updates URL
 */

import { useEffect, useCallback, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { parseChunkFromUrl, updateChunkInUrl } from '../utils/urlParams';

/**
 * Options for useChunkNavigation hook.
 */
export interface UseChunkNavigationOptions {
  /**
   * Callback fired when navigating to a chunk.
   * Called on mount if chunk parameter exists, and when navigateToChunk is called.
   *
   * @param chunkId - ID of the chunk to navigate to
   */
  onChunkNavigate?: (chunkId: string) => void;

  /**
   * Whether to update the URL when navigating to chunks.
   * When true, navigateToChunk will update the URL parameter.
   * Defaults to false.
   */
  updateUrl?: boolean;
}

/**
 * Return value of useChunkNavigation hook.
 */
export interface UseChunkNavigationResult {
  /**
   * Initial chunk ID parsed from URL on mount.
   * Null if no chunk parameter exists or if parameter is invalid.
   */
  initialChunkId: string | null;

  /**
   * Navigate to a specific chunk.
   * Fires onChunkNavigate callback and optionally updates URL.
   *
   * @param chunkId - ID of the chunk to navigate to
   * @param updateUrl - Override the default updateUrl setting for this call
   */
  navigateToChunk: (chunkId: string, updateUrl?: boolean) => void;
}

/**
 * Hook for URL-based chunk navigation.
 *
 * Parses chunk parameters from the URL and provides navigation functionality.
 * Integrates with React Router's useSearchParams for URL management.
 *
 * The hook fires the onChunkNavigate callback on mount if a chunk parameter
 * exists in the URL. This enables deep linking to specific chunks.
 *
 * @param options - Configuration options
 * @returns Chunk navigation state and controls
 *
 * @example
 * // In a document details component
 * const { initialChunkId, navigateToChunk } = useChunkNavigation({
 *   onChunkNavigate: (chunkId) => {
 *     // Scroll to chunk
 *     const element = document.getElementById(chunkId);
 *     element?.scrollIntoView({ behavior: 'smooth' });
 *
 *     // Update active state
 *     setActiveChunkId(chunkId);
 *   },
 *   updateUrl: true
 * });
 *
 * // Use initialChunkId to highlight default chunk
 * useEffect(() => {
 *   if (initialChunkId) {
 *     highlightChunk(initialChunkId);
 *   }
 * }, [initialChunkId]);
 *
 * // Navigate programmatically
 * <button onClick={() => navigateToChunk('chunk-0-page-1')}>
 *   Go to Chunk 1
 * </button>
 */
export function useChunkNavigation(
  options: UseChunkNavigationOptions = {}
): UseChunkNavigationResult {
  const { onChunkNavigate, updateUrl: defaultUpdateUrl = false } = options;

  // Get search params from React Router
  const [searchParams] = useSearchParams();

  // Parse initial chunk ID from URL
  const initialChunkId = parseChunkFromUrl(searchParams.toString());

  // Track if initial navigation has been triggered
  const hasNavigatedRef = useRef(false);

  /**
   * Navigate to a chunk.
   * Fires callback and optionally updates URL.
   */
  const navigateToChunk = useCallback(
    (chunkId: string, updateUrlOverride?: boolean) => {
      // Validate chunk ID
      if (!chunkId || chunkId.trim() === '') {
        console.warn('Cannot navigate to empty chunk ID');
        return;
      }

      const trimmedChunkId = chunkId.trim();

      // Fire callback if provided
      if (onChunkNavigate) {
        try {
          onChunkNavigate(trimmedChunkId);
        } catch (error) {
          console.error('Error in onChunkNavigate callback:', error);
        }
      }

      // Update URL if requested
      const shouldUpdateUrl = updateUrlOverride ?? defaultUpdateUrl;
      if (shouldUpdateUrl) {
        try {
          updateChunkInUrl(trimmedChunkId);
        } catch (error) {
          console.error('Error updating chunk in URL:', error);
        }
      }
    },
    [onChunkNavigate, defaultUpdateUrl]
  );

  /**
   * Handle initial chunk navigation on mount.
   * Only fires once when component mounts with chunk parameter.
   */
  useEffect(() => {
    // Skip if no initial chunk ID
    if (!initialChunkId) {
      return;
    }

    // Skip if already navigated
    if (hasNavigatedRef.current) {
      return;
    }

    // Mark as navigated
    hasNavigatedRef.current = true;

    // Navigate to initial chunk
    // Note: We don't update URL since it already contains the chunk parameter
    if (onChunkNavigate) {
      try {
        onChunkNavigate(initialChunkId);
      } catch (error) {
        console.error('Error in initial chunk navigation:', error);
      }
    }
  }, [initialChunkId, onChunkNavigate]);

  return {
    initialChunkId,
    navigateToChunk,
  };
}

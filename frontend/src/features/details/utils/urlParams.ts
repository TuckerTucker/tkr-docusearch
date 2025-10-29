/**
 * URL Parameter Utilities
 *
 * Agent 10: URL Parameter Chunk Navigation
 * Wave 1 - BBox Overlay React Implementation
 *
 * Utilities for parsing and manipulating chunk parameters in URLs.
 * Supports deep linking to specific chunks within document details views.
 *
 * URL Format: /documents/:id?chunk={chunkId}
 *
 * @example
 * // Parse chunk from URL
 * const chunkId = parseChunkFromUrl('?chunk=chunk-0-page-1');
 * // Returns: 'chunk-0-page-1'
 *
 * // Update URL with chunk
 * updateChunkInUrl('chunk-0-page-1');
 * // URL becomes: /current/path?chunk=chunk-0-page-1
 *
 * // Remove chunk from URL
 * removeChunkFromUrl();
 * // URL becomes: /current/path
 */

/**
 * Parse chunk parameter from URL search string.
 *
 * Extracts the chunk ID from the URL query parameters.
 * Returns null if the parameter is missing or empty.
 *
 * @param search - URL search string (e.g., '?chunk=chunk-0-page-1')
 * @returns Chunk ID or null if not found
 *
 * @example
 * parseChunkFromUrl('?chunk=chunk-0-page-1'); // 'chunk-0-page-1'
 * parseChunkFromUrl('?chunk='); // null
 * parseChunkFromUrl('?other=value'); // null
 * parseChunkFromUrl(''); // null
 */
export function parseChunkFromUrl(search: string): string | null {
  try {
    const params = new URLSearchParams(search);
    const chunk = params.get('chunk');

    // Return null if chunk is missing or empty string
    if (!chunk || chunk.trim() === '') {
      return null;
    }

    return chunk.trim();
  } catch (error) {
    console.error('Error parsing chunk from URL:', error);
    return null;
  }
}

/**
 * Update URL with chunk parameter without page reload.
 *
 * Uses the History API to update the URL with the chunk parameter
 * while preserving other query parameters and the current path.
 * Does not trigger a page reload or navigation.
 *
 * @param chunkId - Chunk ID to add to URL
 *
 * @example
 * // Current URL: /documents/123?foo=bar
 * updateChunkInUrl('chunk-0-page-1');
 * // New URL: /documents/123?foo=bar&chunk=chunk-0-page-1
 */
export function updateChunkInUrl(chunkId: string): void {
  try {
    if (!chunkId || chunkId.trim() === '') {
      console.warn('Cannot update URL with empty chunk ID');
      return;
    }

    const url = new URL(window.location.href);
    url.searchParams.set('chunk', chunkId.trim());

    // Use replaceState to avoid adding to browser history
    window.history.replaceState(null, '', url.toString());
  } catch (error) {
    console.error('Error updating chunk in URL:', error);
  }
}

/**
 * Remove chunk parameter from URL without page reload.
 *
 * Uses the History API to remove the chunk parameter from the URL
 * while preserving other query parameters and the current path.
 * Does not trigger a page reload or navigation.
 *
 * @example
 * // Current URL: /documents/123?chunk=chunk-0-page-1&foo=bar
 * removeChunkFromUrl();
 * // New URL: /documents/123?foo=bar
 */
export function removeChunkFromUrl(): void {
  try {
    const url = new URL(window.location.href);
    url.searchParams.delete('chunk');

    // Use replaceState to avoid adding to browser history
    window.history.replaceState(null, '', url.toString());
  } catch (error) {
    console.error('Error removing chunk from URL:', error);
  }
}

/**
 * Check if URL contains a chunk parameter.
 *
 * Convenience function to check if the current URL has a chunk parameter.
 *
 * @param search - URL search string (defaults to window.location.search)
 * @returns True if chunk parameter exists and is non-empty
 *
 * @example
 * hasChunkInUrl('?chunk=chunk-0-page-1'); // true
 * hasChunkInUrl('?chunk='); // false
 * hasChunkInUrl('?other=value'); // false
 */
export function hasChunkInUrl(search?: string): boolean {
  const searchString = search ?? window.location.search;
  return parseChunkFromUrl(searchString) !== null;
}

/**
 * Build URL with chunk parameter.
 *
 * Utility function to construct a URL string with a chunk parameter.
 * Useful for generating links to specific chunks.
 *
 * @param pathname - Base pathname (e.g., '/documents/123')
 * @param chunkId - Chunk ID to add
 * @param existingParams - Existing URLSearchParams to preserve
 * @returns Complete URL string with chunk parameter
 *
 * @example
 * buildUrlWithChunk('/documents/123', 'chunk-0-page-1');
 * // Returns: '/documents/123?chunk=chunk-0-page-1'
 *
 * const params = new URLSearchParams('?foo=bar');
 * buildUrlWithChunk('/documents/123', 'chunk-0-page-1', params);
 * // Returns: '/documents/123?foo=bar&chunk=chunk-0-page-1'
 */
export function buildUrlWithChunk(
  pathname: string,
  chunkId: string,
  existingParams?: URLSearchParams
): string {
  const params = existingParams ? new URLSearchParams(existingParams) : new URLSearchParams();
  params.set('chunk', chunkId.trim());

  const queryString = params.toString();
  return queryString ? `${pathname}?${queryString}` : pathname;
}

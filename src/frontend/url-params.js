/**
 * URL Parameter Utilities
 *
 * Provides utilities for parsing and building URLs with query parameters
 * for document navigation with optional chunk highlighting.
 *
 * Wave 3 - Agent 9: Details Page Integration
 * Contract: integration-contracts/api-contracts.md Section 5
 */

/**
 * Parse URL query parameters from current page.
 *
 * @returns {Object} Parsed parameters
 * @returns {string|null} .id - Document ID (required)
 * @returns {number|null} .page - Page number (1-indexed, optional)
 * @returns {string|null} .chunk - Chunk ID (optional)
 *
 * @example
 * // URL: /details.html?id=abc123&page=5&chunk=abc123-chunk0012
 * const params = parseURLParams();
 * // Returns: { id: "abc123", page: 5, chunk: "abc123-chunk0012" }
 */
export function parseURLParams() {
    const params = new URLSearchParams(window.location.search);

    const id = params.get('id');
    const pageStr = params.get('page');
    const chunk = params.get('chunk');

    return {
        id: id || null,
        page: pageStr ? parseInt(pageStr, 10) : null,
        chunk: chunk || null,
    };
}

/**
 * Build details page URL with query parameters.
 *
 * @param {string} docId - Document identifier (required)
 * @param {number} [page=null] - Page number (1-indexed, optional)
 * @param {string} [chunkId=null] - Chunk ID for highlighting (optional)
 * @returns {string} Constructed URL
 *
 * @example
 * // Visual search result (page-level)
 * buildDetailsURL("abc123", 5);
 * // Returns: "/frontend/details.html?id=abc123&page=5"
 *
 * @example
 * // Text search result (chunk-level)
 * buildDetailsURL("abc123", 5, "abc123-chunk0012");
 * // Returns: "/frontend/details.html?id=abc123&page=5&chunk=abc123-chunk0012"
 */
export function buildDetailsURL(docId, page = null, chunkId = null) {
    if (!docId) {
        throw new Error('docId is required');
    }

    const params = new URLSearchParams({ id: docId });

    if (page !== null && page !== undefined) {
        params.set('page', page.toString());
    }

    if (chunkId) {
        params.set('chunk', chunkId);
    }

    return `/frontend/details.html?${params.toString()}`;
}

/**
 * Update browser URL without page reload (for state synchronization).
 *
 * Uses History API to update URL, preserving browser history and
 * enabling shareable deep links.
 *
 * @param {string} docId - Document identifier (required)
 * @param {number} [page=null] - Page number (optional)
 * @param {string} [chunkId=null] - Chunk ID (optional)
 *
 * @example
 * // User clicks bbox on page 5
 * updateURL("abc123", 5, "abc123-chunk0012");
 * // URL becomes: /details.html?id=abc123&page=5&chunk=abc123-chunk0012
 */
export function updateURL(docId, page = null, chunkId = null) {
    const url = buildDetailsURL(docId, page, chunkId);
    window.history.pushState({ docId, page, chunkId }, '', url);
}

/**
 * Replace current URL without adding to history.
 *
 * Useful for initial page load navigation to avoid duplicate history entries.
 *
 * @param {string} docId - Document identifier (required)
 * @param {number} [page=null] - Page number (optional)
 * @param {string} [chunkId=null] - Chunk ID (optional)
 */
export function replaceURL(docId, page = null, chunkId = null) {
    const url = buildDetailsURL(docId, page, chunkId);
    window.history.replaceState({ docId, page, chunkId }, '', url);
}

/**
 * Listen for browser back/forward navigation.
 *
 * @param {Function} callback - Called when user navigates with (docId, page, chunkId)
 * @returns {Function} Cleanup function to remove listener
 *
 * @example
 * const cleanup = onURLChange((docId, page, chunkId) => {
 *   navigateToChunk(chunkId);
 * });
 * // Later: cleanup();
 */
export function onURLChange(callback) {
    const handler = (event) => {
        if (event.state) {
            callback(event.state.docId, event.state.page, event.state.chunkId);
        }
    };

    window.addEventListener('popstate', handler);

    return () => window.removeEventListener('popstate', handler);
}

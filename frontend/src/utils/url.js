/**
 * URL Utilities
 *
 * Helper functions for building API and resource URLs.
 *
 * NOTE: Most URL building functions have been removed as they were unused.
 * The backend now provides ready-to-use URLs in API responses (e.g., details_url in SourceInfo).
 * Only navigation-related utilities are kept here.
 *
 * For document detail URLs, use backend-provided details_url from SourceInfo.
 * See: src/utils/url_builder.py (centralized backend URL builder)
 */

/**
 * Build document detail URL
 * @param {string} docId - Document identifier
 * @returns {string} Document detail path
 */
export function buildDocumentUrl(docId) {
    return `/details/${docId}`;
}

/**
 * Build search API URL with query parameters
 * @param {string} query - Search query
 * @param {object} options - Search options (limit, offset, etc.)
 * @returns {string} Search API URL
 */
export function buildSearchUrl(query, options = {}) {
    const params = new URLSearchParams();
    if (query) params.set('query', query);
    if (options.limit) params.set('limit', options.limit);
    if (options.offset) params.set('offset', options.offset);

    return `/api/search?${params.toString()}`;
}

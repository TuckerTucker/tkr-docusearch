/**
 * URL Utilities
 *
 * Helper functions for building API and resource URLs.
 *
 * Wave 1 - Foundation Agent
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
 * Build thumbnail URL for a document
 * @param {string} docId - Document identifier
 * @param {number} page - Optional page number (defaults to first page)
 * @returns {string} Thumbnail URL
 */
export function buildThumbnailUrl(docId, page = 1) {
    return `/api/documents/${docId}/thumbnail?page=${page}`;
}

/**
 * Build page image URL for a specific page
 * @param {string} docId - Document identifier
 * @param {number} page - Page number
 * @returns {string} Page image URL
 */
export function buildPageImageUrl(docId, page) {
    return `/api/documents/${docId}/pages/${page}`;
}

/**
 * Build cover art URL for audio documents
 * @param {string} docId - Document identifier
 * @returns {string} Cover art URL
 */
export function buildCoverArtUrl(docId) {
    return `/api/documents/${docId}/cover-art`;
}

/**
 * Build markdown download URL
 * @param {string} docId - Document identifier
 * @returns {string} Markdown download URL
 */
export function buildMarkdownUrl(docId) {
    return `/documents/${docId}/markdown`;
}

/**
 * Build VTT captions URL
 * @param {string} docId - Document identifier
 * @returns {string} VTT captions URL
 */
export function buildVTTUrl(docId) {
    return `/documents/${docId}/vtt`;
}

/**
 * Build audio source URL
 * @param {string} docId - Document identifier
 * @returns {string} Audio source URL
 */
export function buildAudioUrl(docId) {
    return `/documents/${docId}/audio`;
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

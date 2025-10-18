/**
 * URL Builder Utility
 *
 * Constructs URLs for the details page with optional chunk-level navigation.
 * Supports deep linking to specific document chunks for enhanced research navigation.
 *
 * Wave 7 - Research Navigation Enhancement
 */

/**
 * Build details page URL with optional chunk parameter
 *
 * @param {Object} source - SourceInfo from research API
 * @param {string} source.doc_id - Document ID (required)
 * @param {number} source.page - Page number (required)
 * @param {string} [source.chunk_id] - Optional chunk ID for text search results
 * @returns {string} Details page URL with appropriate query parameters
 *
 * @example
 * // Text search result with chunk
 * buildDetailsURL({
 *   doc_id: "abc123",
 *   page: 5,
 *   chunk_id: "abc123-chunk0045"
 * })
 * // => "/frontend/details.html?id=abc123&page=5&chunk=abc123-chunk0045"
 *
 * @example
 * // Visual search result without chunk
 * buildDetailsURL({
 *   doc_id: "abc123",
 *   page: 5,
 *   chunk_id: null
 * })
 * // => "/frontend/details.html?id=abc123&page=5"
 */
export function buildDetailsURL(source) {
    try {
        // Validate required fields
        if (!source || !source.doc_id) {
            console.warn('[URL Builder] Missing required doc_id:', source);
            return '/frontend/details.html';
        }

        // Build base URL with required parameters
        const params = new URLSearchParams();
        params.set('id', source.doc_id);

        // Add page parameter if available
        if (source.page !== null && source.page !== undefined) {
            params.set('page', String(source.page));
        }

        // Add chunk parameter if available (text search results only)
        if (source.chunk_id) {
            params.set('chunk', source.chunk_id);
        }

        const url = `/frontend/details.html?${params.toString()}`;

        console.debug('[URL Builder] Built URL:', {
            doc_id: source.doc_id,
            page: source.page,
            chunk_id: source.chunk_id,
            url: url
        });

        return url;

    } catch (error) {
        console.error('[URL Builder] Error building URL:', error, source);
        // Fallback to base URL
        return '/frontend/details.html';
    }
}

/**
 * Check if source has chunk-level context
 *
 * @param {Object} source - SourceInfo object
 * @param {string} [source.chunk_id] - Chunk ID if available
 * @returns {boolean} True if chunk_id is present and valid
 *
 * @example
 * hasChunkContext({ chunk_id: "abc123-chunk0045" }) // => true
 * hasChunkContext({ chunk_id: null }) // => false
 * hasChunkContext({}) // => false
 */
export function hasChunkContext(source) {
    return (
        source &&
        source.chunk_id !== null &&
        source.chunk_id !== undefined &&
        source.chunk_id !== ''
    );
}

/**
 * Extract chunk number from chunk_id
 *
 * Parses the standardized chunk_id format to extract the numeric chunk identifier.
 *
 * @param {string} chunkId - Format: "{doc_id}-chunk{NNNN}"
 * @returns {number|null} Chunk number (0-indexed), or null if invalid
 *
 * @example
 * extractChunkNumber("abc123-chunk0045") // => 45
 * extractChunkNumber("abc123-chunk0000") // => 0
 * extractChunkNumber("invalid") // => null
 */
export function extractChunkNumber(chunkId) {
    if (!chunkId || typeof chunkId !== 'string') {
        return null;
    }

    // Match pattern: {doc_id}-chunk{NNNN}
    const match = chunkId.match(/^(.+)-chunk(\d{4})$/);

    if (!match) {
        console.warn('[URL Builder] Invalid chunk_id format:', chunkId);
        return null;
    }

    const chunkNum = parseInt(match[2], 10);

    // Validate chunk number
    if (isNaN(chunkNum)) {
        console.warn('[URL Builder] Invalid chunk number:', match[2]);
        return null;
    }

    return chunkNum;
}

/**
 * Parse URL parameters from current page
 *
 * Utility for extracting navigation parameters from the current URL.
 * Useful for details page initialization.
 *
 * @param {string} [search] - URL search string (defaults to window.location.search)
 * @returns {Object} Parsed parameters
 * @returns {string|null} return.id - Document ID
 * @returns {number|null} return.page - Page number
 * @returns {string|null} return.chunk - Chunk ID
 *
 * @example
 * // URL: /details.html?id=abc123&page=5&chunk=abc123-chunk0045
 * parseURLParams()
 * // => { id: "abc123", page: 5, chunk: "abc123-chunk0045" }
 */
export function parseURLParams(search) {
    const params = new URLSearchParams(search || window.location.search);

    const id = params.get('id');
    const pageStr = params.get('page');
    const chunk = params.get('chunk');

    // Parse page as integer
    const page = pageStr ? parseInt(pageStr, 10) : null;

    return {
        id: id,
        page: !isNaN(page) ? page : null,
        chunk: chunk
    };
}

/**
 * Validate source object for URL building
 *
 * @param {Object} source - Source object to validate
 * @returns {boolean} True if source has required fields
 */
export function isValidSource(source) {
    if (!source || typeof source !== 'object') {
        return false;
    }

    // Required fields
    if (!source.doc_id) {
        return false;
    }

    // Page should be a number if present
    if (source.page !== null && source.page !== undefined) {
        if (typeof source.page !== 'number' || isNaN(source.page)) {
            return false;
        }
    }

    return true;
}

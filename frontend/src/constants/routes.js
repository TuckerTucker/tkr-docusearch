/**
 * Route Constants
 *
 * Centralized route paths and URL builders for application navigation.
 *
 * Wave 1 - Foundation Agent
 */

/**
 * Application route paths
 */
export const ROUTES = {
    LIBRARY: '/',
    DETAILS: '/details/:id',
    RESEARCH: '/research',
};

/**
 * Build document details path
 * @param {string} id - Document identifier
 * @returns {string} Details page path
 */
export function buildDetailsPath(id) {
    return `/details/${id}`;
}

/**
 * Parse document ID from details path
 * @param {string} path - Current path (e.g., "/details/abc123")
 * @returns {string|null} Document ID or null if not a details path
 */
export function parseDetailsPath(path) {
    const match = path.match(/^\/details\/([^/]+)$/);
    return match ? match[1] : null;
}

/**
 * Check if a path is a details path
 * @param {string} path - Path to check
 * @returns {boolean} True if path is a details path
 */
export function isDetailsPath(path) {
    return /^\/details\/[^/]+$/.test(path);
}

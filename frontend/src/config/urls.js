/**
 * Centralized URL configuration for DocuSearch frontend.
 *
 * This module provides a single source of truth for all service URLs and endpoints
 * across the DocuSearch React application. It supports Vite environment variable
 * configuration and provides convenient properties and methods for building
 * service-specific URLs.
 *
 * Environment Variables (Vite):
 *   VITE_WORKER_URL: Processing worker base URL (default: http://localhost:8002)
 *   VITE_CHROMADB_URL: ChromaDB server URL (default: http://localhost:8001)
 *   VITE_RESEARCH_API_URL: Research API base URL (default: http://localhost:8004)
 *   VITE_COPYPARTY_URL: Copyparty file server URL (default: http://localhost:8000)
 *   VITE_FRONTEND_URL: Frontend application URL (default: http://localhost:42007)
 *   VITE_FRONTEND_PORT: Frontend dev server port (default: 42007)
 *   VITE_UI_PORT: UI viewer dev server port (default: 42008)
 *
 * Usage:
 *   import { serviceURLs } from '@/config/urls';
 *   const searchUrl = serviceURLs.worker.search;
 *   const imageUrl = serviceURLs.document.imageUrl('abc123', 'page-5.png');
 *
 * Migration Notes:
 *   - Replaces hardcoded URLs scattered across components
 *   - Centralizes Vite env var usage
 *   - Provides consistent URL building logic
 *   - Mirrors backend src/config/urls.py structure
 *
 * @module config/urls
 */

/**
 * Service base URLs from environment variables
 */
const BASE_URLS = {
  worker: import.meta.env.VITE_WORKER_URL || 'http://localhost:8002',
  chromadb: import.meta.env.VITE_CHROMADB_URL || 'http://localhost:8001',
  researchApi: import.meta.env.VITE_RESEARCH_API_URL || 'http://localhost:8004',
  copyparty: import.meta.env.VITE_COPYPARTY_URL || 'http://localhost:8000',
  frontend: import.meta.env.VITE_FRONTEND_URL || 'http://localhost:42007',
};

/**
 * Join URL path segments safely, handling trailing/leading slashes
 * @param {string} base - Base URL
 * @param {string} path - Path to append
 * @returns {string} Joined URL
 */
const urlJoin = (base, path) => {
  const baseClean = base.endsWith('/') ? base.slice(0, -1) : base;
  const pathClean = path.startsWith('/') ? path : `/${path}`;
  return `${baseClean}${pathClean}`;
};

/**
 * Worker service endpoints
 */
const workerEndpoints = {
  base: BASE_URLS.worker,
  search: urlJoin(BASE_URLS.worker, '/search'),
  status: urlJoin(BASE_URLS.worker, '/status'),
  health: urlJoin(BASE_URLS.worker, '/health'),
  documents: urlJoin(BASE_URLS.worker, '/documents'),
  documentStructure: urlJoin(BASE_URLS.worker, '/document-structure'),
};

/**
 * ChromaDB endpoints
 */
const chromadbEndpoints = {
  base: BASE_URLS.chromadb,
  heartbeat: urlJoin(BASE_URLS.chromadb, '/api/v1/heartbeat'),
  collections: urlJoin(BASE_URLS.chromadb, '/api/v1/collections'),
};

/**
 * Research API endpoints
 */
const researchApiEndpoints = {
  base: BASE_URLS.researchApi,
  ask: urlJoin(BASE_URLS.researchApi, '/api/research/ask'),
  health: urlJoin(BASE_URLS.researchApi, '/api/health'),
  status: urlJoin(BASE_URLS.researchApi, '/api/status'),
};

/**
 * Document asset URL builders
 */
const documentAssets = {
  /**
   * Build URL for a document image (page/chunk image)
   * @param {string} docId - Document ID (SHA-256 hash)
   * @param {string} imageFilename - Image filename (e.g., "page-5.png")
   * @param {boolean} [absolute=true] - Return absolute URL vs relative path
   * @returns {string} URL to document image
   *
   * @example
   * documentAssets.imageUrl('abc123', 'page-5.png')
   * // => 'http://localhost:8000/uploads/abc123/images/page-5.png'
   */
  imageUrl: (docId, imageFilename, absolute = true) => {
    const path = `/uploads/${docId}/images/${imageFilename}`;
    return absolute ? urlJoin(BASE_URLS.copyparty, path) : path;
  },

  /**
   * Build URL for a document thumbnail (cover/first page)
   * @param {string} docId - Document ID (SHA-256 hash)
   * @param {boolean} [absolute=true] - Return absolute URL vs relative path
   * @returns {string} URL to document thumbnail
   *
   * @example
   * documentAssets.thumbnailUrl('abc123')
   * // => 'http://localhost:8000/uploads/abc123/thumbnail.png'
   */
  thumbnailUrl: (docId, absolute = true) => {
    const path = `/uploads/${docId}/thumbnail.png`;
    return absolute ? urlJoin(BASE_URLS.copyparty, path) : path;
  },

  /**
   * Build URL for audio cover art
   * @param {string} docId - Document ID (SHA-256 hash)
   * @param {boolean} [absolute=true] - Return absolute URL vs relative path
   * @returns {string} URL to cover art
   *
   * @example
   * documentAssets.coverArtUrl('abc123')
   * // => 'http://localhost:8000/uploads/abc123/cover-art.png'
   */
  coverArtUrl: (docId, absolute = true) => {
    const path = `/uploads/${docId}/cover-art.png`;
    return absolute ? urlJoin(BASE_URLS.copyparty, path) : path;
  },

  /**
   * Build URL for original uploaded file
   * @param {string} docId - Document ID (SHA-256 hash)
   * @param {string} filename - Original filename
   * @param {boolean} [absolute=true] - Return absolute URL vs relative path
   * @returns {string} URL to original file
   *
   * @example
   * documentAssets.originalFileUrl('abc123', 'document.pdf')
   * // => 'http://localhost:8000/uploads/abc123/document.pdf'
   */
  originalFileUrl: (docId, filename, absolute = true) => {
    const path = `/uploads/${docId}/${filename}`;
    return absolute ? urlJoin(BASE_URLS.copyparty, path) : path;
  },
};

/**
 * Frontend route URL builders
 */
const frontendRoutes = {
  /**
   * Build document details URL with optional navigation parameters
   * @param {string} docId - Document ID (SHA-256 hash)
   * @param {Object} [options={}] - Navigation options
   * @param {number} [options.page] - Page number (1-indexed, for visual documents)
   * @param {string} [options.chunkId] - Chunk ID for navigation
   * @returns {string} Relative URL to document details page
   *
   * @example
   * frontendRoutes.detailsUrl('abc123', { page: 5 })
   * // => '/details/abc123?page=5'
   *
   * frontendRoutes.detailsUrl('abc123', { chunkId: 'abc123-chunk0042' })
   * // => '/details/abc123?chunk=abc123-chunk0042'
   */
  detailsUrl: (docId, options = {}) => {
    if (!docId) {
      throw new Error('docId is required');
    }

    let path = `/details/${docId}`;

    const params = new URLSearchParams();
    if (options.page && typeof options.page === 'number' && options.page > 0) {
      params.set('page', String(options.page));
    }
    if (options.chunkId && typeof options.chunkId === 'string' && options.chunkId.trim()) {
      params.set('chunk', options.chunkId.trim());
    }

    const queryString = params.toString();
    if (queryString) {
      path = `${path}?${queryString}`;
    }

    return path;
  },

  /**
   * Build search results URL with query
   * @param {string} query - Search query
   * @returns {string} Relative URL to search results
   *
   * @example
   * frontendRoutes.searchUrl('machine learning')
   * // => '/search?q=machine+learning'
   */
  searchUrl: (query) => {
    if (!query) {
      return '/search';
    }
    return `/search?q=${encodeURIComponent(query)}`;
  },
};

/**
 * Centralized service URLs configuration
 *
 * Provides organized access to all service endpoints and URL builders.
 *
 * @example
 * import { serviceURLs } from '@/config/urls';
 *
 * // Worker endpoints
 * fetch(serviceURLs.worker.search, { ... });
 *
 * // Document assets
 * const imgSrc = serviceURLs.document.imageUrl(docId, 'page-5.png');
 *
 * // Frontend routes
 * navigate(serviceURLs.frontend.detailsUrl(docId, { page: 5 }));
 */
export const serviceURLs = {
  worker: workerEndpoints,
  chromadb: chromadbEndpoints,
  researchApi: researchApiEndpoints,
  document: documentAssets,
  frontend: frontendRoutes,
  base: BASE_URLS,
};

/**
 * Export individual endpoint groups for convenience
 */
export { workerEndpoints, chromadbEndpoints, researchApiEndpoints, documentAssets, frontendRoutes };

/**
 * Export base URLs for direct access
 */
export { BASE_URLS };

/**
 * Default export for backward compatibility
 */
export default serviceURLs;

/**
 * Lazy Loading Manager for Structure Data
 *
 * Handles on-demand loading of document structure data with intelligent
 * prefetching, request cancellation, and integration with cache manager.
 *
 * Wave 3 - Agent 13: Performance Optimizer
 *
 * @module lazy-loader
 */

import { StructureCache } from './cache-manager.js';

/**
 * Load state for tracking pending requests
 * @typedef {Object} LoadState
 * @property {AbortController} controller - Abort controller for cancellation
 * @property {Promise} promise - Loading promise
 * @property {number} startTime - Request start timestamp
 */

/**
 * Lazy loader for structure data with caching and prefetching.
 *
 * @class
 * @example
 * const loader = new StructureLazyLoader('/api');
 *
 * // Load structure (uses cache if available)
 * const structure = await loader.loadStructure('doc123', 1);
 *
 * // Preload adjacent pages
 * await loader.preloadAdjacentPages('doc123', 1);
 *
 * // Cancel pending requests
 * loader.cancelPendingRequests();
 */
export class StructureLazyLoader {
  /**
   * Create lazy loader.
   *
   * @param {string} apiBaseUrl - Base URL for API (default: '')
   * @param {Object} options - Configuration options
   * @param {number} options.cacheSize - Maximum cache entries (default: 20)
   * @param {number} options.cacheMaxAge - Cache entry max age in ms (default: 5 minutes)
   * @param {number} options.requestTimeout - Request timeout in ms (default: 10 seconds)
   * @param {number} options.preloadRange - Number of pages to preload (default: 1)
   * @param {boolean} options.autoPreload - Auto-preload adjacent pages (default: true)
   * @param {Function} options.onError - Error callback (error, docId, page)
   */
  constructor(apiBaseUrl = '', options = {}) {
    this.apiBaseUrl = apiBaseUrl;
    this.requestTimeout = options.requestTimeout || 10 * 1000;
    this.preloadRange = options.preloadRange !== undefined ? options.preloadRange : 1;
    this.autoPreload = options.autoPreload !== undefined ? options.autoPreload : true;
    this.onError = options.onError;

    // Initialize cache
    this.cache = new StructureCache(
      options.cacheSize || 20,
      options.cacheMaxAge || 5 * 60 * 1000,
      {
        onEvict: (entry, reason) => {
          console.log(`[StructureLazyLoader] Cache eviction: ${reason}`);
        },
      }
    );

    // Track pending requests: Map<string, LoadState>
    this.pendingRequests = new Map();

    console.log('[StructureLazyLoader] Initialized');
  }

  /**
   * Generate cache/request key.
   *
   * @private
   * @param {string} docId - Document identifier
   * @param {number} page - Page number
   * @returns {string} Key
   */
  _getKey(docId, page) {
    return `${docId}:${page}`;
  }

  /**
   * Build API endpoint URL.
   *
   * @private
   * @param {string} docId - Document identifier
   * @param {number} page - Page number
   * @returns {string} API URL
   */
  _buildUrl(docId, page) {
    const base = this.apiBaseUrl || '';
    return `${base}/documents/${docId}/pages/${page}/structure`;
  }

  /**
   * Fetch structure from API.
   *
   * @private
   * @param {string} docId - Document identifier
   * @param {number} page - Page number
   * @param {AbortSignal} signal - Abort signal for cancellation
   * @returns {Promise<Object|null>} Structure data or null
   */
  async _fetchStructure(docId, page, signal) {
    const url = this._buildUrl(docId, page);
    const startTime = Date.now();

    try {
      const response = await fetch(url, {
        signal,
        headers: {
          Accept: 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 404) {
          console.log(`[StructureLazyLoader] No structure available: ${docId}:${page}`);
          return null;
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const structure = await response.json();
      const duration = Date.now() - startTime;

      console.log(`[StructureLazyLoader] Fetched ${docId}:${page} in ${duration}ms`);

      return structure;
    } catch (error) {
      // Don't log abort errors (user-initiated cancellation)
      if (error.name === 'AbortError') {
        console.log(`[StructureLazyLoader] Request cancelled: ${docId}:${page}`);
        return null;
      }

      console.error(`[StructureLazyLoader] Fetch failed for ${docId}:${page}:`, error);

      // Call error callback
      if (this.onError) {
        try {
          this.onError(error, docId, page);
        } catch (callbackError) {
          console.error('[StructureLazyLoader] Error in error callback:', callbackError);
        }
      }

      throw error;
    }
  }

  /**
   * Load structure for a page (with caching).
   * Automatically preloads adjacent pages if enabled.
   *
   * @param {string} docId - Document identifier
   * @param {number} page - Page number
   * @param {Object} options - Load options
   * @param {boolean} options.skipCache - Skip cache and force fetch (default: false)
   * @param {boolean} options.skipPreload - Skip automatic preload (default: false)
   * @returns {Promise<Object|null>} Structure data or null
   */
  async loadStructure(docId, page, options = {}) {
    const key = this._getKey(docId, page);
    const skipCache = options.skipCache || false;
    const skipPreload = options.skipPreload || false;

    // Check cache first (unless skipped)
    if (!skipCache) {
      const cached = this.cache.get(docId, page);
      if (cached) {
        console.log(`[StructureLazyLoader] Cache hit: ${key}`);

        // Trigger preload in background if enabled
        if (this.autoPreload && !skipPreload) {
          this.preloadAdjacentPages(docId, page).catch((error) => {
            console.error('[StructureLazyLoader] Preload failed:', error);
          });
        }

        return cached;
      }
    }

    // Check if request is already pending
    if (this.pendingRequests.has(key)) {
      console.log(`[StructureLazyLoader] Reusing pending request: ${key}`);
      const loadState = this.pendingRequests.get(key);
      return loadState.promise;
    }

    // Create new request
    const controller = new AbortController();

    // Set timeout
    const timeoutId = setTimeout(() => {
      controller.abort();
    }, this.requestTimeout);

    // Create loading promise
    const promise = this._fetchStructure(docId, page, controller.signal)
      .then((structure) => {
        clearTimeout(timeoutId);
        this.pendingRequests.delete(key);

        // Cache if valid
        if (structure) {
          this.cache.set(docId, page, structure);

          // Trigger preload in background if enabled
          if (this.autoPreload && !skipPreload) {
            this.preloadAdjacentPages(docId, page).catch((error) => {
              console.error('[StructureLazyLoader] Preload failed:', error);
            });
          }
        }

        return structure;
      })
      .catch((error) => {
        clearTimeout(timeoutId);
        this.pendingRequests.delete(key);
        throw error;
      });

    // Track pending request
    this.pendingRequests.set(key, {
      controller,
      promise,
      startTime: Date.now(),
    });

    return promise;
  }

  /**
   * Preload structure for adjacent pages.
   * Loads pages within ±range of current page in background.
   *
   * @param {string} docId - Document identifier
   * @param {number} currentPage - Current page number
   * @param {number} range - Pages to load in each direction (default: from options)
   * @returns {Promise<void>}
   */
  async preloadAdjacentPages(docId, currentPage, range = this.preloadRange) {
    const promises = [];

    for (let offset = -range; offset <= range; offset++) {
      if (offset === 0) continue; // Skip current page

      const page = currentPage + offset;
      if (page < 1) continue; // Skip invalid pages

      // Skip if already cached or pending
      const key = this._getKey(docId, page);
      if (this.cache.has(docId, page) || this.pendingRequests.has(key)) {
        continue;
      }

      // Load in background (don't trigger recursive preload)
      const promise = this.loadStructure(docId, page, { skipPreload: true }).catch(
        (error) => {
          // Silently fail - preload is best-effort
          console.log(`[StructureLazyLoader] Preload failed for ${docId}:${page}`);
        }
      );

      promises.push(promise);
    }

    if (promises.length > 0) {
      console.log(
        `[StructureLazyLoader] Preloading ${promises.length} pages for ${docId}:${currentPage}`
      );
    }

    await Promise.all(promises);
  }

  /**
   * Cancel a specific pending request.
   *
   * @param {string} docId - Document identifier
   * @param {number} page - Page number
   * @returns {boolean} True if request was cancelled
   */
  cancelRequest(docId, page) {
    const key = this._getKey(docId, page);
    const loadState = this.pendingRequests.get(key);

    if (!loadState) {
      return false;
    }

    loadState.controller.abort();
    this.pendingRequests.delete(key);

    console.log(`[StructureLazyLoader] Cancelled request: ${key}`);
    return true;
  }

  /**
   * Cancel all pending requests.
   *
   * @returns {number} Number of requests cancelled
   */
  cancelPendingRequests() {
    let count = 0;

    for (const [key, loadState] of this.pendingRequests.entries()) {
      loadState.controller.abort();
      count++;
    }

    this.pendingRequests.clear();

    if (count > 0) {
      console.log(`[StructureLazyLoader] Cancelled ${count} pending requests`);
    }

    return count;
  }

  /**
   * Cancel all pending requests for a specific document.
   *
   * @param {string} docId - Document identifier
   * @returns {number} Number of requests cancelled
   */
  cancelDocumentRequests(docId) {
    let count = 0;

    for (const [key, loadState] of this.pendingRequests.entries()) {
      if (key.startsWith(`${docId}:`)) {
        loadState.controller.abort();
        this.pendingRequests.delete(key);
        count++;
      }
    }

    if (count > 0) {
      console.log(`[StructureLazyLoader] Cancelled ${count} requests for ${docId}`);
    }

    return count;
  }

  /**
   * Get number of pending requests.
   *
   * @returns {number} Number of pending requests
   */
  getPendingCount() {
    return this.pendingRequests.size;
  }

  /**
   * Check if request is pending.
   *
   * @param {string} docId - Document identifier
   * @param {number} page - Page number
   * @returns {boolean} True if request is pending
   */
  isPending(docId, page) {
    const key = this._getKey(docId, page);
    return this.pendingRequests.has(key);
  }

  /**
   * Get cache statistics.
   *
   * @returns {Object} Cache statistics
   */
  getStats() {
    return {
      ...this.cache.getStats(),
      pendingRequests: this.pendingRequests.size,
    };
  }

  /**
   * Clear cache and cancel pending requests.
   */
  clear() {
    this.cancelPendingRequests();
    this.cache.clear();
    console.log('[StructureLazyLoader] Cleared');
  }

  /**
   * Destroy loader and cleanup resources.
   */
  destroy() {
    this.cancelPendingRequests();
    this.cache.destroy();
    console.log('[StructureLazyLoader] Destroyed');
  }
}

/**
 * LRU Cache Manager for Structure Data
 *
 * Implements Least Recently Used (LRU) caching strategy for document structure data.
 * Reduces API calls and improves navigation performance through intelligent caching.
 *
 * Wave 3 - Agent 13: Performance Optimizer
 *
 * @module cache-manager
 */

/**
 * Cache entry with metadata
 * @typedef {Object} CacheEntry
 * @property {*} data - Cached data
 * @property {number} timestamp - Creation timestamp
 * @property {number} accessCount - Number of times accessed
 * @property {number} lastAccess - Last access timestamp
 * @property {number} size - Approximate size in bytes
 */

/**
 * Cache statistics
 * @typedef {Object} CacheStats
 * @property {number} hits - Number of cache hits
 * @property {number} misses - Number of cache misses
 * @property {number} size - Current number of entries
 * @property {number} maxSize - Maximum number of entries
 * @property {number} hitRate - Hit rate percentage (0-100)
 * @property {number} evictions - Number of evictions
 * @property {number} totalSize - Total approximate size in bytes
 */

/**
 * LRU (Least Recently Used) Cache for structure data.
 * Automatically evicts least recently used entries when cache is full.
 *
 * @class
 * @example
 * const cache = new StructureCache(20, 5 * 60 * 1000);
 *
 * // Store structure
 * cache.set('doc123', 1, structureData);
 *
 * // Retrieve structure
 * const structure = cache.get('doc123', 1);
 *
 * // Check statistics
 * const stats = cache.getStats();
 * console.log(`Hit rate: ${stats.hitRate.toFixed(1)}%`);
 */
export class StructureCache {
  /**
   * Create structure cache.
   *
   * @param {number} maxSize - Maximum number of entries (default: 20 pages)
   * @param {number} maxAge - Maximum age in milliseconds (default: 5 minutes)
   * @param {Object} options - Configuration options
   * @param {boolean} options.enableStats - Enable statistics tracking (default: true)
   * @param {Function} options.onEvict - Callback when entry is evicted (entry, reason)
   */
  constructor(maxSize = 20, maxAge = 5 * 60 * 1000, options = {}) {
    this.maxSize = maxSize;
    this.maxAge = maxAge;
    this.enableStats = options.enableStats !== undefined ? options.enableStats : true;
    this.onEvict = options.onEvict;

    // Cache storage: Map<string, CacheEntry>
    // Key format: "docId:page"
    this.cache = new Map();

    // Statistics
    this.stats = {
      hits: 0,
      misses: 0,
      evictions: 0,
      totalSize: 0,
    };

    // Cleanup timer
    this.cleanupInterval = null;
    this.startAutoCleanup();

    console.log(`[StructureCache] Initialized (maxSize: ${maxSize}, maxAge: ${maxAge}ms)`);
  }

  /**
   * Generate cache key from document ID and page number.
   *
   * @private
   * @param {string} docId - Document identifier
   * @param {number} page - Page number
   * @returns {string} Cache key
   */
  _getCacheKey(docId, page) {
    return `${docId}:${page}`;
  }

  /**
   * Estimate size of data in bytes (rough approximation).
   *
   * @private
   * @param {*} data - Data to estimate
   * @returns {number} Approximate size in bytes
   */
  _estimateSize(data) {
    try {
      const json = JSON.stringify(data);
      return json.length * 2; // Rough estimate (UTF-16)
    } catch (error) {
      console.warn('[StructureCache] Failed to estimate size:', error);
      return 1000; // Default estimate
    }
  }

  /**
   * Check if entry is expired.
   *
   * @private
   * @param {CacheEntry} entry - Cache entry
   * @returns {boolean} True if expired
   */
  _isExpired(entry) {
    if (!entry || !entry.timestamp) return true;
    const age = Date.now() - entry.timestamp;
    return age > this.maxAge;
  }

  /**
   * Get structure from cache.
   *
   * @param {string} docId - Document identifier
   * @param {number} page - Page number
   * @returns {*|null} Cached structure or null if not found/expired
   */
  get(docId, page) {
    const key = this._getCacheKey(docId, page);
    const entry = this.cache.get(key);

    // Cache miss
    if (!entry) {
      if (this.enableStats) this.stats.misses++;
      return null;
    }

    // Check expiration
    if (this._isExpired(entry)) {
      this.cache.delete(key);
      this.stats.totalSize -= entry.size;
      if (this.enableStats) this.stats.misses++;
      console.log(`[StructureCache] Expired: ${key}`);
      return null;
    }

    // Cache hit - update access metadata
    entry.accessCount++;
    entry.lastAccess = Date.now();
    if (this.enableStats) this.stats.hits++;

    // Move to end (most recently used)
    this.cache.delete(key);
    this.cache.set(key, entry);

    return entry.data;
  }

  /**
   * Store structure in cache.
   *
   * @param {string} docId - Document identifier
   * @param {number} page - Page number
   * @param {*} structure - Structure data to cache
   */
  set(docId, page, structure) {
    if (!structure) {
      console.warn('[StructureCache] Attempted to cache null/undefined structure');
      return;
    }

    const key = this._getCacheKey(docId, page);
    const now = Date.now();

    // Remove existing entry if present
    if (this.cache.has(key)) {
      const oldEntry = this.cache.get(key);
      this.stats.totalSize -= oldEntry.size;
      this.cache.delete(key);
    }

    // Evict LRU entry if cache is full
    if (this.cache.size >= this.maxSize) {
      this._evictLRU();
    }

    // Create new entry
    const size = this._estimateSize(structure);
    const entry = {
      data: structure,
      timestamp: now,
      accessCount: 1,
      lastAccess: now,
      size,
    };

    this.cache.set(key, entry);
    this.stats.totalSize += size;

    console.log(`[StructureCache] Cached: ${key} (${(size / 1024).toFixed(1)}KB)`);
  }

  /**
   * Evict least recently used entry.
   *
   * @private
   */
  _evictLRU() {
    if (this.cache.size === 0) return;

    // First entry in Map is least recently used (due to reordering on access)
    const [key, entry] = this.cache.entries().next().value;

    this.cache.delete(key);
    this.stats.totalSize -= entry.size;
    this.stats.evictions++;

    console.log(`[StructureCache] Evicted LRU: ${key}`);

    // Call eviction callback
    if (this.onEvict) {
      try {
        this.onEvict(entry, 'lru');
      } catch (error) {
        console.error('[StructureCache] Error in eviction callback:', error);
      }
    }
  }

  /**
   * Check if structure is in cache.
   *
   * @param {string} docId - Document identifier
   * @param {number} page - Page number
   * @returns {boolean} True if cached and not expired
   */
  has(docId, page) {
    const key = this._getCacheKey(docId, page);
    const entry = this.cache.get(key);

    if (!entry) return false;
    if (this._isExpired(entry)) {
      this.cache.delete(key);
      this.stats.totalSize -= entry.size;
      return false;
    }

    return true;
  }

  /**
   * Remove specific entry from cache.
   *
   * @param {string} docId - Document identifier
   * @param {number} page - Page number
   * @returns {boolean} True if entry was removed
   */
  delete(docId, page) {
    const key = this._getCacheKey(docId, page);
    const entry = this.cache.get(key);

    if (!entry) return false;

    this.cache.delete(key);
    this.stats.totalSize -= entry.size;

    console.log(`[StructureCache] Deleted: ${key}`);
    return true;
  }

  /**
   * Remove all entries for a specific document.
   *
   * @param {string} docId - Document identifier
   * @returns {number} Number of entries removed
   */
  deleteDocument(docId) {
    let count = 0;

    for (const [key, entry] of this.cache.entries()) {
      if (key.startsWith(`${docId}:`)) {
        this.cache.delete(key);
        this.stats.totalSize -= entry.size;
        count++;
      }
    }

    if (count > 0) {
      console.log(`[StructureCache] Deleted ${count} entries for document: ${docId}`);
    }

    return count;
  }

  /**
   * Clear all cache entries.
   */
  clear() {
    const size = this.cache.size;
    this.cache.clear();
    this.stats.totalSize = 0;
    console.log(`[StructureCache] Cleared ${size} entries`);
  }

  /**
   * Clean up expired entries.
   *
   * @returns {number} Number of expired entries removed
   */
  cleanup() {
    let count = 0;
    const now = Date.now();

    for (const [key, entry] of this.cache.entries()) {
      if (this._isExpired(entry)) {
        this.cache.delete(key);
        this.stats.totalSize -= entry.size;
        count++;

        // Call eviction callback
        if (this.onEvict) {
          try {
            this.onEvict(entry, 'expired');
          } catch (error) {
            console.error('[StructureCache] Error in eviction callback:', error);
          }
        }
      }
    }

    if (count > 0) {
      console.log(`[StructureCache] Cleaned up ${count} expired entries`);
    }

    return count;
  }

  /**
   * Start automatic cleanup of expired entries.
   *
   * @private
   * @param {number} interval - Cleanup interval in milliseconds (default: 60s)
   */
  startAutoCleanup(interval = 60 * 1000) {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
    }

    this.cleanupInterval = setInterval(() => {
      this.cleanup();
    }, interval);
  }

  /**
   * Stop automatic cleanup.
   */
  stopAutoCleanup() {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
    }
  }

  /**
   * Get cache statistics.
   *
   * @returns {CacheStats} Statistics object
   */
  getStats() {
    const total = this.stats.hits + this.stats.misses;
    const hitRate = total > 0 ? (this.stats.hits / total) * 100 : 0;

    return {
      hits: this.stats.hits,
      misses: this.stats.misses,
      size: this.cache.size,
      maxSize: this.maxSize,
      hitRate,
      evictions: this.stats.evictions,
      totalSize: this.stats.totalSize,
    };
  }

  /**
   * Reset statistics counters.
   */
  resetStats() {
    this.stats.hits = 0;
    this.stats.misses = 0;
    this.stats.evictions = 0;
    // Keep totalSize as it reflects actual cache state
  }

  /**
   * Get all cache keys.
   *
   * @returns {string[]} Array of cache keys
   */
  keys() {
    return Array.from(this.cache.keys());
  }

  /**
   * Get number of cached entries.
   *
   * @returns {number} Number of entries
   */
  size() {
    return this.cache.size;
  }

  /**
   * Preload structure data for adjacent pages.
   * Useful for prefetching pages near the current page.
   *
   * @param {string} docId - Document identifier
   * @param {number} currentPage - Current page number
   * @param {Function} fetcher - Function to fetch structure: (docId, page) => Promise<structure>
   * @param {number} range - Number of pages to preload in each direction (default: 1)
   * @returns {Promise<void>}
   */
  async preloadAdjacentPages(docId, currentPage, fetcher, range = 1) {
    if (typeof fetcher !== 'function') {
      throw new TypeError('Fetcher must be a function');
    }

    const promises = [];

    for (let offset = -range; offset <= range; offset++) {
      if (offset === 0) continue; // Skip current page

      const page = currentPage + offset;
      if (page < 1) continue; // Skip invalid pages

      // Skip if already cached
      if (this.has(docId, page)) {
        continue;
      }

      // Fetch and cache
      const promise = fetcher(docId, page)
        .then((structure) => {
          if (structure) {
            this.set(docId, page, structure);
            console.log(`[StructureCache] Preloaded: ${docId}:${page}`);
          }
        })
        .catch((error) => {
          console.error(`[StructureCache] Preload failed for ${docId}:${page}:`, error);
        });

      promises.push(promise);
    }

    await Promise.all(promises);
  }

  /**
   * Destroy cache and cleanup resources.
   */
  destroy() {
    this.stopAutoCleanup();
    this.clear();
    console.log('[StructureCache] Destroyed');
  }
}

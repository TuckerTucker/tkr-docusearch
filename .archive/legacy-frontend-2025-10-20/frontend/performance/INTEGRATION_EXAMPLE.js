/**
 * Performance Optimization Integration Example
 *
 * Complete example showing how to integrate performance optimizations
 * into the DetailsController, BboxOverlay, and ChunkHighlighter.
 *
 * Wave 3 - Agent 13: Performance Optimizer
 *
 * This file demonstrates best practices for:
 * - Lazy loading with caching
 * - Debounced event handlers
 * - Performance metrics tracking
 * - Memory-efficient resource management
 */

import { BoundingBoxOverlay } from '../bounding-box-overlay.js';
import { ChunkHighlighter } from '../chunk-highlighter.js';
import { parseURLParams, updateURL, onURLChange } from '../url-params.js';

// Import performance utilities
import {
  StructureLazyLoader,
  debounce,
  rafDebounce,
  PerformanceMetrics,
  createTimer,
} from './index.js';

/**
 * Optimized DetailsController with performance enhancements.
 *
 * Key optimizations:
 * 1. Lazy loading with automatic prefetching
 * 2. Intelligent caching (LRU, 20 pages, 5min TTL)
 * 3. Debounced resize handlers
 * 4. RAF-debounced hover handlers
 * 5. Performance metrics tracking
 * 6. Memory-efficient resource cleanup
 */
export class OptimizedDetailsController {
  constructor(slideshow, accordion, docId) {
    this.slideshow = slideshow;
    this.accordion = accordion;
    this.docId = docId;

    // Component instances
    this.overlay = null;
    this.highlighter = null;

    // State
    this.currentPage = 1;
    this.isInitialized = false;
    this.cleanupFunctions = [];

    // ========================================================================
    // OPTIMIZATION 1: Lazy Loader with Cache
    // ========================================================================

    // Replace simple Map cache with intelligent lazy loader
    this.structureLoader = new StructureLazyLoader('/api', {
      cacheSize: 20, // Cache 20 pages
      cacheMaxAge: 5 * 60 * 1000, // 5 minute TTL
      requestTimeout: 10000, // 10 second timeout
      preloadRange: 1, // Preload ±1 page
      autoPreload: true, // Auto-prefetch on load
      onError: (error, docId, page) => {
        console.error(`[OptimizedDetailsController] Failed to load ${docId}:${page}:`, error);
        // Could show user notification here
      },
    });

    // ========================================================================
    // OPTIMIZATION 2: Debounced Resize Handler
    // ========================================================================

    // Debounce resize to prevent excessive re-renders
    // 150ms is optimal for user-initiated resizes
    this._debouncedResize = debounce(
      () => {
        if (this.overlay) {
          PerformanceMetrics.measureSync(
            'overlay-resize',
            () => {
              this.overlay.updateScale();
            },
            { category: 'rendering' }
          );
        }
      },
      150,
      { leading: false, trailing: true }
    );

    // ========================================================================
    // OPTIMIZATION 3: Enable Performance Tracking
    // ========================================================================

    // Enable in development mode
    if (window.location.hostname === 'localhost') {
      PerformanceMetrics.setEnabled(true);
      console.log('[OptimizedDetailsController] Performance tracking enabled');
    }

    console.log('[OptimizedDetailsController] Created with optimizations');
  }

  /**
   * Initialize controller with performance tracking.
   */
  async init() {
    const initTimer = createTimer('details-controller-init', { category: 'initialization' });

    if (this.isInitialized) {
      console.warn('[OptimizedDetailsController] Already initialized');
      return;
    }

    // Parse URL parameters
    const params = parseURLParams();

    // Initialize markdown highlighter
    const markdownContainer = this.getMarkdownContainer();
    if (markdownContainer) {
      this.highlighter = new OptimizedChunkHighlighter(markdownContainer);
      this.setupChunkHighlighterEvents();
    }

    // Initialize structure overlay
    if (this.slideshow) {
      this.currentPage = params.page || this.slideshow.currentPage || 1;

      // ====================================================================
      // OPTIMIZATION 4: Measured Structure Loading
      // ====================================================================

      await this.loadStructureForPage(this.currentPage);
      this.setupSlideshowListener();
    }

    // Handle chunk navigation
    if (params.chunk) {
      await this.navigateToChunk(params.chunk);
    }

    // Setup URL navigation
    this.setupURLNavigationListener();

    // Setup window resize listener
    window.addEventListener('resize', this._debouncedResize);
    this.cleanupFunctions.push(() => {
      window.removeEventListener('resize', this._debouncedResize);
      this._debouncedResize.cancel();
    });

    this.isInitialized = true;
    initTimer.stop();

    // Log cache statistics in development
    if (PerformanceMetrics.isEnabled()) {
      setTimeout(() => {
        const stats = this.structureLoader.getStats();
        console.log('[OptimizedDetailsController] Cache stats:', stats);
      }, 5000);
    }
  }

  /**
   * Get markdown container element.
   */
  getMarkdownContainer() {
    const markdownSection = document.getElementById('markdown-full');
    if (!markdownSection) return null;

    const contentDiv = markdownSection.querySelector('.accordion-content');
    return contentDiv;
  }

  /**
   * Load structure with lazy loading and metrics.
   */
  async loadStructureForPage(page) {
    try {
      // ====================================================================
      // OPTIMIZATION 5: Lazy Loading with Metrics
      // ====================================================================

      const structure = await PerformanceMetrics.measureAsync(
        'loadStructure',
        async () => {
          return await this.structureLoader.loadStructure(this.docId, page, {
            skipCache: false,
            skipPreload: false,
          });
        },
        { category: 'structure', metadata: { page } }
      );

      if (structure && structure.has_structure && structure.headings?.length > 0) {
        this.initializeBboxOverlay(structure);
      } else {
        this.destroyBboxOverlay();
      }

      return structure;
    } catch (error) {
      console.error('[OptimizedDetailsController] Error loading structure:', error);
      return null;
    }
  }

  /**
   * Initialize bbox overlay with optimized instance.
   */
  initializeBboxOverlay(structure) {
    this.destroyBboxOverlay();

    const imageElement = document.getElementById('slideshow-image');
    if (!imageElement) return;

    const coordSystem = structure.coordinate_system || {};
    const pdfWidth = coordSystem.image_width || 612;
    const pdfHeight = coordSystem.image_height || 792;

    // ========================================================================
    // OPTIMIZATION 6: Use Optimized BboxOverlay
    // ========================================================================

    this.overlay = new OptimizedBoundingBoxOverlay(imageElement, structure.headings, {
      pdfWidth,
      pdfHeight,
      enableHover: true,
      enableClick: true,
      enableKeyboard: true,
    });

    this.overlay.render();
    this.setupBboxOverlayEvents();
  }

  /**
   * Destroy bbox overlay and cleanup.
   */
  destroyBboxOverlay() {
    if (this.overlay) {
      this.overlay.destroy();
      this.overlay = null;
    }
  }

  /**
   * Setup bbox overlay event listeners.
   */
  setupBboxOverlayEvents() {
    if (!this.overlay) return;

    this.overlay.onBboxClick((chunkId, elementType, event) => {
      this.handleBboxClick(chunkId);
    });

    this.overlay.onBboxHover((chunkId, elementType, isEnter, event) => {
      if (this.highlighter) {
        if (isEnter) {
          this.highlighter.highlightChunk(chunkId, false);
        } else {
          if (this.highlighter.getActiveChunkId() !== chunkId) {
            this.highlighter.clearHighlight();
          }
        }
      }
    });
  }

  /**
   * Setup chunk highlighter event listeners.
   */
  setupChunkHighlighterEvents() {
    if (!this.highlighter) return;

    const cleanup = this.highlighter.onChunkHover((chunkId, isEnter) => {
      if (this.overlay) {
        if (isEnter) {
          this.overlay.highlightBbox(chunkId, false);
        } else {
          if (this.overlay.activeBboxId !== chunkId) {
            this.overlay.clearHighlight();
          }
        }
      }
    });

    this.cleanupFunctions.push(cleanup);
  }

  /**
   * Setup slideshow page change listener.
   */
  setupSlideshowListener() {
    if (!this.slideshow) return;

    const originalGoToPage = this.slideshow.goToPage.bind(this.slideshow);

    this.slideshow.goToPage = async (pageNumber) => {
      originalGoToPage(pageNumber);

      if (pageNumber !== this.currentPage) {
        this.currentPage = pageNumber;

        // ====================================================================
        // OPTIMIZATION 7: Cancel Pending Requests on Page Change
        // ====================================================================

        // Cancel any pending requests for old pages
        // (except adjacent pages that might be preloaded)
        // This is handled automatically by the lazy loader

        await this.loadStructureForPage(pageNumber);
        updateURL(this.docId, pageNumber, null);
      }
    };
  }

  /**
   * Setup URL navigation listener.
   */
  setupURLNavigationListener() {
    const cleanup = onURLChange(async (docId, page, chunkId) => {
      if (page && page !== this.currentPage && this.slideshow) {
        this.slideshow.goToPage(page);
      }

      if (chunkId) {
        await this.navigateToChunk(chunkId);
      }
    });

    this.cleanupFunctions.push(cleanup);
  }

  /**
   * Handle bbox click.
   */
  async handleBboxClick(chunkId) {
    if (this.overlay) {
      this.overlay.highlightBbox(chunkId, true);
    }

    if (this.highlighter) {
      this.highlighter.scrollToChunk(chunkId, true);
      this.highlighter.highlightChunk(chunkId, true);
    }

    updateURL(this.docId, this.currentPage, chunkId);
    this.expandMarkdownSection();
  }

  /**
   * Navigate to chunk.
   */
  async navigateToChunk(chunkId) {
    try {
      const response = await fetch(`/documents/${this.docId}/chunks/${chunkId}`);
      if (!response.ok) return;

      const chunk = await response.json();

      if (chunk.page && chunk.page !== this.currentPage && this.slideshow) {
        this.slideshow.goToPage(chunk.page);
        this.currentPage = chunk.page;
        await this.loadStructureForPage(chunk.page);
      }

      if (this.overlay && chunk.bbox) {
        this.overlay.highlightBbox(chunkId, true);
      }

      if (this.highlighter) {
        setTimeout(() => {
          this.highlighter.scrollToChunk(chunkId, true);
          this.highlighter.highlightChunk(chunkId, true);
          this.expandMarkdownSection();
        }, 300);
      }
    } catch (error) {
      console.error('[OptimizedDetailsController] Error navigating to chunk:', error);
    }
  }

  /**
   * Expand markdown section.
   */
  expandMarkdownSection() {
    const markdownSection = document.getElementById('markdown-full');
    if (!markdownSection) return;

    const header = markdownSection.querySelector('.accordion-header');
    if (header && !markdownSection.classList.contains('active')) {
      header.click();
    }
  }

  /**
   * Clean up resources.
   */
  destroy() {
    // ========================================================================
    // OPTIMIZATION 8: Comprehensive Cleanup
    // ========================================================================

    // Destroy components
    this.destroyBboxOverlay();

    if (this.highlighter) {
      this.highlighter.destroy();
      this.highlighter = null;
    }

    // Cleanup lazy loader
    if (this.structureLoader) {
      this.structureLoader.destroy();
      this.structureLoader = null;
    }

    // Cancel debounced handlers
    if (this._debouncedResize) {
      this._debouncedResize.cancel();
    }

    // Run cleanup functions
    this.cleanupFunctions.forEach((cleanup) => cleanup());
    this.cleanupFunctions = [];

    // Report performance metrics
    if (PerformanceMetrics.isEnabled()) {
      console.log('[OptimizedDetailsController] Performance Report:');
      PerformanceMetrics.report({ category: 'structure' });
      PerformanceMetrics.report({ category: 'rendering' });
    }

    this.isInitialized = false;
  }
}

/**
 * Optimized BoundingBoxOverlay with RAF-debounced hover.
 */
class OptimizedBoundingBoxOverlay extends BoundingBoxOverlay {
  constructor(imageElement, bboxes, options) {
    super(imageElement, bboxes, options);

    // ========================================================================
    // OPTIMIZATION 9: RAF-Debounced Hover Handler
    // ========================================================================

    // Replace original hover handler with RAF-debounced version
    const originalHandleHover = this._handleBboxHover.bind(this);
    this._handleBboxHover = rafDebounce((event) => {
      originalHandleHover(event);
    });
  }

  render() {
    // Track render performance
    return PerformanceMetrics.measureSync(
      'bbox-overlay-render',
      () => {
        return super.render();
      },
      { category: 'rendering' }
    );
  }
}

/**
 * Optimized ChunkHighlighter with RAF-debounced hover.
 */
class OptimizedChunkHighlighter extends ChunkHighlighter {
  constructor(markdownElement) {
    super(markdownElement);

    // ========================================================================
    // OPTIMIZATION 10: RAF-Debounced Hover Events
    // ========================================================================

    // Replace handlers with RAF-debounced versions
    const originalHandleEnter = this.handleMouseEnter.bind(this);
    const originalHandleLeave = this.handleMouseLeave.bind(this);

    this.handleMouseEnter = rafDebounce((event) => {
      originalHandleEnter(event);
    });

    this.handleMouseLeave = rafDebounce((event) => {
      originalHandleLeave(event);
    });
  }

  scrollToChunk(chunkId, smooth = true) {
    // Track scroll performance
    PerformanceMetrics.measureSync(
      'chunk-scroll',
      () => {
        super.scrollToChunk(chunkId, smooth);
      },
      { category: 'interaction' }
    );
  }
}

// ============================================================================
// Usage Example
// ============================================================================

/*
// In details.js:

import { OptimizedDetailsController } from './performance/INTEGRATION_EXAMPLE.js';

// Create optimized controller
const controller = new OptimizedDetailsController(slideshow, accordion, docId);
await controller.init();

// Later, cleanup
window.addEventListener('beforeunload', () => {
  controller.destroy();
});

// Monitor performance
setInterval(() => {
  const stats = controller.structureLoader.getStats();
  console.log('Cache hit rate:', stats.hitRate + '%');
  console.log('Pending requests:', stats.pendingRequests);
}, 30000); // Every 30 seconds

*/

// ============================================================================
// Performance Monitoring Example
// ============================================================================

/*
// Enable detailed monitoring in development

if (window.location.hostname === 'localhost') {
  // Enable metrics
  PerformanceMetrics.setEnabled(true);

  // Monitor all performance entries
  PerformanceMetrics.observeEntries(['measure', 'mark'], (entry) => {
    if (entry.duration > 100) {
      console.warn('Slow operation:', entry.name, entry.duration.toFixed(2) + 'ms');
    }
  });

  // Report every minute
  setInterval(() => {
    PerformanceMetrics.report();
  }, 60000);

  // Monitor memory
  setInterval(() => {
    const memory = PerformanceMetrics.getMemoryUsage();
    if (memory) {
      console.log('Memory:', memory.usedMB + 'MB /', memory.totalMB + 'MB');
    }
  }, 30000);
}
*/

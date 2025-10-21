/**
 * BoundingBox Overlay Component
 *
 * Renders interactive SVG overlays for document structure bounding boxes.
 * Handles coordinate scaling, Y-axis flip, hover/click interactions, and responsive behavior.
 *
 * Usage:
 * ```javascript
 * const overlay = new BoundingBoxOverlay(imageElement, bboxes, {
 *   pdfWidth: 612,
 *   pdfHeight: 792,
 *   colors: { heading: '#4b5563', table: '#6b7280' },
 *   opacity: 0.2
 * });
 *
 * overlay.render();
 *
 * overlay.onBboxClick((chunkId, elementType) => {
 *   console.log('Clicked:', chunkId);
 * });
 * ```
 *
 * Reference: integration-contracts/docling-structure-spec.md
 */

import {
  scaleBboxToScreen,
  validateBbox,
  calculateScaleFactors
} from './utils/coordinate-scaler.js';

export class BoundingBoxOverlay {
  /**
   * Create a BoundingBox Overlay
   *
   * @param {HTMLElement} imageElement - The page image element
   * @param {Array<Object>} bboxes - Array of bbox objects from Structure API
   * @param {Object} options - Configuration options
   * @param {number} options.pdfWidth - PDF page width in points (required)
   * @param {number} options.pdfHeight - PDF page height in points (required)
   * @param {Object} options.colors - Colors by element type
   * @param {number} options.opacity - Base opacity (0-1)
   * @param {number} options.hoverOpacity - Hover opacity (0-1)
   * @param {number} options.activeOpacity - Active opacity (0-1)
   * @param {number} options.strokeWidth - Border width in pixels
   * @param {boolean} options.enableHover - Enable hover effects
   * @param {boolean} options.enableClick - Enable click events
   * @param {boolean} options.enableKeyboard - Enable keyboard navigation
   * @param {boolean} options.showLabels - Show element type labels
   */
  constructor(imageElement, bboxes, options = {}) {
    // Validate inputs
    if (!(imageElement instanceof HTMLElement)) {
      throw new Error('imageElement must be an HTMLElement');
    }

    if (!Array.isArray(bboxes)) {
      throw new Error('bboxes must be an array');
    }

    // Store references
    this.imageElement = imageElement;
    this.bboxes = bboxes;

    // Default options
    this.options = {
      pdfWidth: options.pdfWidth || 612,  // US Letter default
      pdfHeight: options.pdfHeight || 792,
      colors: {
        heading: '#4b5563',
        table: '#6b7280',
        picture: '#8b5cf6',
        text: '#059669',
        code: '#dc2626',
        formula: '#ea580c',
        default: '#6b7280',
        ...options.colors
      },
      opacity: options.opacity !== undefined ? options.opacity : 0.15,
      hoverOpacity: options.hoverOpacity !== undefined ? options.hoverOpacity : 0.3,
      activeOpacity: options.activeOpacity !== undefined ? options.activeOpacity : 0.4,
      strokeWidth: options.strokeWidth || 2,
      enableHover: options.enableHover !== undefined ? options.enableHover : true,
      enableClick: options.enableClick !== undefined ? options.enableClick : true,
      enableKeyboard: options.enableKeyboard !== undefined ? options.enableKeyboard : true,
      showLabels: options.showLabels !== undefined ? options.showLabels : false
    };

    // State
    this.svgElement = null;
    this.rectElements = new Map(); // chunkId -> rect element
    this.activeBboxId = null;
    this.resizeObserver = null;
    this.clickCallbacks = [];
    this.hoverCallbacks = [];

    // Bind event handlers
    this._handleResize = this._handleResize.bind(this);
    this._handleBboxClick = this._handleBboxClick.bind(this);
    this._handleBboxHover = this._handleBboxHover.bind(this);
    this._handleBboxLeave = this._handleBboxLeave.bind(this);
    this._handleKeydown = this._handleKeydown.bind(this);

    // Track current dimensions for debouncing
    this._lastWidth = 0;
    this._lastHeight = 0;
    this._resizeDebounceTimer = null;
  }

  /**
   * Render the overlay
   * Creates SVG element and draws all bboxes
   */
  render() {
    // Remove existing overlay if present
    this.destroy();

    // Get image dimensions
    const imageWidth = this.imageElement.naturalWidth || this.imageElement.width;
    const imageHeight = this.imageElement.naturalHeight || this.imageElement.height;

    if (imageWidth === 0 || imageHeight === 0) {
      console.warn('BoundingBoxOverlay: Image dimensions are zero, waiting for load');
      this.imageElement.addEventListener('load', () => this.render(), { once: true });
      return;
    }

    // Create SVG container
    this._createSvgContainer(imageWidth, imageHeight);

    // Draw all bboxes
    this._drawBboxes(imageWidth, imageHeight);

    // Set up responsive behavior
    this._setupResponsive();

    // Set up keyboard navigation
    if (this.options.enableKeyboard) {
      this._setupKeyboardNav();
    }

    return this;
  }

  /**
   * Create SVG container element
   * @private
   */
  _createSvgContainer(imageWidth, imageHeight) {
    // Create SVG element
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.classList.add('bbox-overlay');
    svg.setAttribute('viewBox', `0 0 ${imageWidth} ${imageHeight}`);
    svg.setAttribute('preserveAspectRatio', 'none');
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', 'Document structure bounding boxes');

    // Position absolutely over image
    const imageRect = this.imageElement.getBoundingClientRect();
    svg.style.position = 'absolute';
    svg.style.top = '0';
    svg.style.left = '0';
    svg.style.width = '100%';
    svg.style.height = '100%';
    svg.style.pointerEvents = 'none'; // Allow clicks to pass through to image

    // Insert after image (so it overlays)
    const container = this.imageElement.parentElement;
    if (!container) {
      throw new Error('Image element must have a parent');
    }

    // Ensure parent has position: relative
    const containerPosition = window.getComputedStyle(container).position;
    if (containerPosition === 'static') {
      container.style.position = 'relative';
    }

    container.appendChild(svg);
    this.svgElement = svg;
  }

  /**
   * Draw all bounding boxes
   * @private
   */
  _drawBboxes(imageWidth, imageHeight) {
    this.rectElements.clear();

    this.bboxes.forEach((bboxData, index) => {
      try {
        // Validate bbox data
        if (!bboxData.bbox) {
          console.warn('BoundingBoxOverlay: bbox missing for element', bboxData);
          return;
        }

        validateBbox(bboxData.bbox, 'bottom-left');

        // Convert to screen coordinates
        const screenBbox = scaleBboxToScreen(
          bboxData.bbox,
          this.options.pdfWidth,
          this.options.pdfHeight,
          imageWidth,
          imageHeight
        );

        // Create rect element
        const rect = this._createBboxRect(screenBbox, bboxData, index);
        this.svgElement.appendChild(rect);

        // Store reference
        const bboxId = bboxData.chunk_id || `bbox-${index}`;
        this.rectElements.set(bboxId, rect);

      } catch (error) {
        console.error('BoundingBoxOverlay: Error drawing bbox', bboxData, error);
      }
    });
  }

  /**
   * Create a single bbox rectangle element
   * @private
   */
  _createBboxRect(screenBbox, bboxData, index) {
    const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');

    // Set geometry
    rect.setAttribute('x', screenBbox.x);
    rect.setAttribute('y', screenBbox.y);
    rect.setAttribute('width', screenBbox.width);
    rect.setAttribute('height', screenBbox.height);

    // Set styling
    const elementType = bboxData.element_type || 'default';
    const color = this.options.colors[elementType] || this.options.colors.default;

    rect.setAttribute('fill', color);
    rect.setAttribute('fill-opacity', this.options.opacity);
    rect.setAttribute('stroke', color);
    rect.setAttribute('stroke-width', this.options.strokeWidth);
    rect.setAttribute('stroke-opacity', 0.6);

    // Set classes and data attributes
    rect.classList.add('bbox-rect');
    rect.classList.add(`bbox-${elementType}`);

    const bboxId = bboxData.chunk_id || `bbox-${index}`;
    rect.setAttribute('data-chunk-id', bboxId);
    rect.setAttribute('data-element-type', elementType);
    rect.setAttribute('data-bbox-index', index);

    // Accessibility
    rect.setAttribute('role', 'button');
    rect.setAttribute('tabindex', this.options.enableKeyboard ? '0' : '-1');
    rect.setAttribute('aria-label', `${elementType} region ${index + 1}`);

    // Enable pointer events on rects
    rect.style.pointerEvents = 'auto';
    rect.style.cursor = this.options.enableClick ? 'pointer' : 'default';

    // Add event listeners
    if (this.options.enableHover) {
      rect.addEventListener('mouseenter', this._handleBboxHover);
      rect.addEventListener('mouseleave', this._handleBboxLeave);
    }

    if (this.options.enableClick) {
      rect.addEventListener('click', this._handleBboxClick);
    }

    return rect;
  }

  /**
   * Handle bbox click
   * @private
   */
  _handleBboxClick(event) {
    const rect = event.currentTarget;
    const chunkId = rect.getAttribute('data-chunk-id');
    const elementType = rect.getAttribute('data-element-type');

    // Fire callbacks
    this.clickCallbacks.forEach(callback => {
      try {
        callback(chunkId, elementType, event);
      } catch (error) {
        console.error('BoundingBoxOverlay: Error in click callback', error);
      }
    });
  }

  /**
   * Handle bbox hover (mouseenter)
   * @private
   */
  _handleBboxHover(event) {
    const rect = event.currentTarget;
    const chunkId = rect.getAttribute('data-chunk-id');
    const elementType = rect.getAttribute('data-element-type');

    // Add hover class
    rect.classList.add('bbox-hover');
    rect.setAttribute('fill-opacity', this.options.hoverOpacity);

    // Fire callbacks
    this.hoverCallbacks.forEach(callback => {
      try {
        callback(chunkId, elementType, true, event);
      } catch (error) {
        console.error('BoundingBoxOverlay: Error in hover callback', error);
      }
    });
  }

  /**
   * Handle bbox leave (mouseleave)
   * @private
   */
  _handleBboxLeave(event) {
    const rect = event.currentTarget;
    const chunkId = rect.getAttribute('data-chunk-id');
    const elementType = rect.getAttribute('data-element-type');

    // Remove hover class (unless active)
    if (!rect.classList.contains('bbox-active')) {
      rect.classList.remove('bbox-hover');
      rect.setAttribute('fill-opacity', this.options.opacity);
    }

    // Fire callbacks
    this.hoverCallbacks.forEach(callback => {
      try {
        callback(chunkId, elementType, false, event);
      } catch (error) {
        console.error('BoundingBoxOverlay: Error in hover callback', error);
      }
    });
  }

  /**
   * Highlight a specific bbox (permanent until cleared)
   *
   * @param {string} chunkId - Chunk ID to highlight
   * @param {boolean} isPermanent - If true, persists until clearHighlight()
   */
  highlightBbox(chunkId, isPermanent = true) {
    // Clear previous active bbox
    if (this.activeBboxId && this.rectElements.has(this.activeBboxId)) {
      const prevRect = this.rectElements.get(this.activeBboxId);
      prevRect.classList.remove('bbox-active');
      prevRect.setAttribute('fill-opacity', this.options.opacity);
    }

    // Highlight new bbox
    if (this.rectElements.has(chunkId)) {
      const rect = this.rectElements.get(chunkId);
      rect.classList.add('bbox-active');
      rect.setAttribute('fill-opacity', this.options.activeOpacity);

      if (isPermanent) {
        this.activeBboxId = chunkId;
      }

      // Scroll into view if needed
      rect.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }

  /**
   * Clear all highlights
   */
  clearHighlight() {
    if (this.activeBboxId && this.rectElements.has(this.activeBboxId)) {
      const rect = this.rectElements.get(this.activeBboxId);
      rect.classList.remove('bbox-active');
      rect.setAttribute('fill-opacity', this.options.opacity);
      this.activeBboxId = null;
    }
  }

  /**
   * Register click callback
   *
   * @param {Function} callback - (chunkId, elementType, event) => void
   */
  onBboxClick(callback) {
    if (typeof callback !== 'function') {
      throw new Error('Callback must be a function');
    }
    this.clickCallbacks.push(callback);
  }

  /**
   * Register hover callback
   *
   * @param {Function} callback - (chunkId, elementType, isEnter, event) => void
   */
  onBboxHover(callback) {
    if (typeof callback !== 'function') {
      throw new Error('Callback must be a function');
    }
    this.hoverCallbacks.push(callback);
  }

  /**
   * Set up responsive behavior
   * @private
   */
  _setupResponsive() {
    // Use ResizeObserver for efficient resize handling
    if ('ResizeObserver' in window) {
      this.resizeObserver = new ResizeObserver(this._handleResize);
      this.resizeObserver.observe(this.imageElement);
    } else {
      // Fallback to window resize
      window.addEventListener('resize', this._handleResize);
    }
  }

  /**
   * Handle resize events
   * @private
   */
  _handleResize(entries) {
    // Debounce resize to avoid excessive re-renders
    if (this._resizeDebounceTimer) {
      clearTimeout(this._resizeDebounceTimer);
    }

    this._resizeDebounceTimer = setTimeout(() => {
      const imageWidth = this.imageElement.naturalWidth || this.imageElement.width;
      const imageHeight = this.imageElement.naturalHeight || this.imageElement.height;

      // Only re-render if dimensions actually changed
      if (imageWidth !== this._lastWidth || imageHeight !== this._lastHeight) {
        this._lastWidth = imageWidth;
        this._lastHeight = imageHeight;
        this.render();
      }
    }, 100); // 100ms debounce
  }

  /**
   * Set up keyboard navigation
   * @private
   */
  _setupKeyboardNav() {
    this.svgElement.addEventListener('keydown', this._handleKeydown);
  }

  /**
   * Handle keyboard events
   * @private
   */
  _handleKeydown(event) {
    const target = event.target;
    if (!target.classList.contains('bbox-rect')) {
      return;
    }

    // Enter or Space to activate
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      target.click();
    }

    // Arrow keys to navigate between bboxes
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key)) {
      event.preventDefault();
      const index = parseInt(target.getAttribute('data-bbox-index'), 10);
      let nextIndex;

      if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
        nextIndex = (index + 1) % this.bboxes.length;
      } else {
        nextIndex = (index - 1 + this.bboxes.length) % this.bboxes.length;
      }

      // Find and focus next bbox
      const nextRect = this.svgElement.querySelector(`[data-bbox-index="${nextIndex}"]`);
      if (nextRect) {
        nextRect.focus();
      }
    }
  }

  /**
   * Destroy the overlay and clean up resources
   */
  destroy() {
    // Remove SVG element
    if (this.svgElement && this.svgElement.parentElement) {
      this.svgElement.parentElement.removeChild(this.svgElement);
    }

    // Clean up observers
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
      this.resizeObserver = null;
    } else {
      window.removeEventListener('resize', this._handleResize);
    }

    // Clear timers
    if (this._resizeDebounceTimer) {
      clearTimeout(this._resizeDebounceTimer);
    }

    // Clear state
    this.svgElement = null;
    this.rectElements.clear();
    this.activeBboxId = null;
    this.clickCallbacks = [];
    this.hoverCallbacks = [];
  }
}

/**
 * Chunk Highlighter Component
 *
 * Manages highlighting and scrolling for text chunks in markdown content.
 * Supports multiple highlight states (hover, active) and emits events for
 * bidirectional synchronization with bounding box overlay.
 *
 * Wave 3 - Agent 9: Details Page Integration
 * Dependencies: Agent 7 (Markdown Chunking)
 */

/**
 * ChunkHighlighter class manages text chunk highlighting and interaction.
 *
 * @class
 * @example
 * const highlighter = new ChunkHighlighter(markdownContainer);
 * highlighter.onChunkHover((chunkId, isEnter) => {
 *   if (isEnter) overlay.highlightBbox(chunkId, false);
 * });
 * highlighter.highlightChunk("abc123-chunk0012", true);
 * highlighter.scrollToChunk("abc123-chunk0012");
 */
export class ChunkHighlighter {
    /**
     * Create chunk highlighter.
     *
     * @param {HTMLElement} markdownElement - Container element with chunked markdown
     */
    constructor(markdownElement) {
        if (!markdownElement) {
            throw new Error('markdownElement is required');
        }

        this.container = markdownElement;
        this.activeChunkId = null;
        this.hoveredChunkId = null;
        this.hoverCallbacks = [];

        this.init();
    }

    /**
     * Initialize event listeners for chunk interaction.
     *
     * @private
     */
    init() {
        // Add event listeners for hover events on chunk divs
        this.container.addEventListener('mouseenter', this.handleMouseEnter.bind(this), true);
        this.container.addEventListener('mouseleave', this.handleMouseLeave.bind(this), true);

        console.log('[ChunkHighlighter] Initialized');
    }

    /**
     * Handle mouse enter on chunk elements.
     *
     * @private
     * @param {MouseEvent} event
     */
    handleMouseEnter(event) {
        const chunkDiv = event.target.closest('[data-chunk-id]');
        if (!chunkDiv) return;

        const chunkId = chunkDiv.getAttribute('data-chunk-id');
        if (chunkId && chunkId !== this.hoveredChunkId) {
            this.hoveredChunkId = chunkId;
            this.addHoverState(chunkDiv);
            this.emitHoverEvent(chunkId, true);
        }
    }

    /**
     * Handle mouse leave on chunk elements.
     *
     * @private
     * @param {MouseEvent} event
     */
    handleMouseLeave(event) {
        const chunkDiv = event.target.closest('[data-chunk-id]');
        if (!chunkDiv) return;

        const chunkId = chunkDiv.getAttribute('data-chunk-id');
        if (chunkId && chunkId === this.hoveredChunkId) {
            this.removeHoverState(chunkDiv);
            this.emitHoverEvent(chunkId, false);
            this.hoveredChunkId = null;
        }
    }

    /**
     * Find chunk element by chunk ID.
     *
     * @param {string} chunkId - Chunk identifier
     * @returns {HTMLElement|null} Chunk div element or null if not found
     *
     * @example
     * const element = highlighter.findChunkElement("abc123-chunk0012");
     */
    findChunkElement(chunkId) {
        if (!chunkId) return null;
        return this.container.querySelector(`[data-chunk-id="${chunkId}"]`);
    }

    /**
     * Highlight a specific chunk.
     *
     * @param {string} chunkId - Chunk identifier to highlight
     * @param {boolean} [isPermanent=false] - If true, adds active state; if false, adds hover state
     *
     * @example
     * // Temporary hover highlight
     * highlighter.highlightChunk("abc123-chunk0012", false);
     *
     * @example
     * // Permanent active highlight
     * highlighter.highlightChunk("abc123-chunk0012", true);
     */
    highlightChunk(chunkId, isPermanent = false) {
        if (!chunkId) return;

        const chunkDiv = this.findChunkElement(chunkId);
        if (!chunkDiv) {
            console.warn(`[ChunkHighlighter] Chunk not found: ${chunkId}`);
            return;
        }

        if (isPermanent) {
            // Clear previous active highlight
            this.clearActiveHighlight();

            // Add active state
            chunkDiv.classList.add('chunk-active');
            this.activeChunkId = chunkId;

            console.log(`[ChunkHighlighter] Active highlight: ${chunkId}`);
        } else {
            // Add hover state
            this.addHoverState(chunkDiv);
        }
    }

    /**
     * Clear all highlights (both active and hover).
     */
    clearHighlight() {
        this.clearActiveHighlight();
        this.clearHoverHighlight();
    }

    /**
     * Clear active (permanent) highlight.
     *
     * @private
     */
    clearActiveHighlight() {
        if (this.activeChunkId) {
            const prevChunk = this.findChunkElement(this.activeChunkId);
            if (prevChunk) {
                prevChunk.classList.remove('chunk-active');
            }
            this.activeChunkId = null;
        }
    }

    /**
     * Clear hover (temporary) highlight.
     *
     * @private
     */
    clearHoverHighlight() {
        const hovered = this.container.querySelectorAll('.chunk-hover');
        hovered.forEach((el) => el.classList.remove('chunk-hover'));
        this.hoveredChunkId = null;
    }

    /**
     * Add hover state to chunk element.
     *
     * @private
     * @param {HTMLElement} element
     */
    addHoverState(element) {
        if (element && !element.classList.contains('chunk-active')) {
            element.classList.add('chunk-hover');
        }
    }

    /**
     * Remove hover state from chunk element.
     *
     * @private
     * @param {HTMLElement} element
     */
    removeHoverState(element) {
        if (element) {
            element.classList.remove('chunk-hover');
        }
    }

    /**
     * Scroll chunk into view.
     *
     * @param {string} chunkId - Chunk identifier
     * @param {boolean} [smooth=true] - Use smooth scrolling
     *
     * @example
     * highlighter.scrollToChunk("abc123-chunk0012");
     * // Chunk scrolls into center of viewport with smooth animation
     */
    scrollToChunk(chunkId, smooth = true) {
        if (!chunkId) return;

        const chunkDiv = this.findChunkElement(chunkId);
        if (!chunkDiv) {
            console.warn(`[ChunkHighlighter] Cannot scroll to chunk: ${chunkId} not found`);
            return;
        }

        chunkDiv.scrollIntoView({
            behavior: smooth ? 'smooth' : 'auto',
            block: 'center',
            inline: 'nearest',
        });

        console.log(`[ChunkHighlighter] Scrolled to chunk: ${chunkId}`);
    }

    /**
     * Register callback for chunk hover events.
     *
     * @param {Function} callback - Called with (chunkId, isEnter) when chunk hover changes
     * @returns {Function} Cleanup function to remove callback
     *
     * @example
     * const cleanup = highlighter.onChunkHover((chunkId, isEnter) => {
     *   if (isEnter) {
     *     overlay.highlightBbox(chunkId, false);
     *   } else {
     *     overlay.clearHighlight();
     *   }
     * });
     * // Later: cleanup();
     */
    onChunkHover(callback) {
        if (typeof callback !== 'function') {
            throw new Error('Callback must be a function');
        }

        this.hoverCallbacks.push(callback);

        // Return cleanup function
        return () => {
            const index = this.hoverCallbacks.indexOf(callback);
            if (index > -1) {
                this.hoverCallbacks.splice(index, 1);
            }
        };
    }

    /**
     * Emit hover event to all registered callbacks.
     *
     * @private
     * @param {string} chunkId
     * @param {boolean} isEnter
     */
    emitHoverEvent(chunkId, isEnter) {
        this.hoverCallbacks.forEach((callback) => {
            try {
                callback(chunkId, isEnter);
            } catch (error) {
                console.error('[ChunkHighlighter] Error in hover callback:', error);
            }
        });
    }

    /**
     * Get currently active chunk ID.
     *
     * @returns {string|null} Active chunk ID or null
     */
    getActiveChunkId() {
        return this.activeChunkId;
    }

    /**
     * Clean up event listeners.
     */
    destroy() {
        this.container.removeEventListener('mouseenter', this.handleMouseEnter.bind(this), true);
        this.container.removeEventListener('mouseleave', this.handleMouseLeave.bind(this), true);
        this.hoverCallbacks = [];
        this.clearHighlight();
        console.log('[ChunkHighlighter] Destroyed');
    }
}

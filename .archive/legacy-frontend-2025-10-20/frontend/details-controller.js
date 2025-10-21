/**
 * Details Page Controller - Bidirectional Highlighting Integration
 *
 * Orchestrates integration between:
 * - BoundingBoxOverlay (visual structure highlighting)
 * - ChunkHighlighter (text chunk highlighting)
 * - URL-based navigation (deep linking to specific chunks)
 * - Existing slideshow and accordion components
 *
 * Wave 3 - Agent 9: Details Page Integration
 * Dependencies: Agent 8 (BBoxOverlay), Agent 5 (Structure API), Agent 7 (Markdown Chunking)
 */

import { BoundingBoxOverlay } from './bounding-box-overlay.js';
import { ChunkHighlighter } from './chunk-highlighter.js';
import { parseURLParams, updateURL, replaceURL, onURLChange } from './url-params.js';

/**
 * DetailsController manages bidirectional highlighting between page structure
 * and text content.
 *
 * @class
 * @example
 * const controller = new DetailsController(slideshow, accordion, docId);
 * await controller.init();
 */
export class DetailsController {
    /**
     * Create details controller.
     *
     * @param {Slideshow} slideshow - Slideshow instance (can be null for audio documents)
     * @param {Accordion} accordion - Accordion instance
     * @param {string} docId - Document identifier
     */
    constructor(slideshow, accordion, docId) {
        this.slideshow = slideshow;
        this.accordion = accordion;
        this.docId = docId;

        // Component instances
        this.overlay = null;
        this.highlighter = null;

        // State
        this.currentPage = 1;
        this.structureCache = new Map(); // page -> structure data
        this.isInitialized = false;

        // Cleanup functions
        this.cleanupFunctions = [];

        console.log('[DetailsController] Created');
    }

    /**
     * Initialize controller and load initial state from URL.
     */
    async init() {
        if (this.isInitialized) {
            console.warn('[DetailsController] Already initialized');
            return;
        }

        // Parse URL parameters
        const params = parseURLParams();
        console.log('[DetailsController] URL params:', params);

        // Get markdown container for chunk highlighting
        const markdownContainer = this.getMarkdownContainer();
        if (markdownContainer) {
            this.highlighter = new ChunkHighlighter(markdownContainer);
            this.setupChunkHighlighterEvents();
            console.log('[DetailsController] ChunkHighlighter initialized');
        }

        // If slideshow exists, set up structure overlay
        if (this.slideshow) {
            // Get current page from URL or slideshow
            this.currentPage = params.page || this.slideshow.currentPage || 1;

            // Navigate to the page if URL specifies it
            if (params.page && params.page !== this.slideshow.currentPage) {
                console.log(`[DetailsController] Navigating to page ${params.page} from URL`);
                this.slideshow.goToPage(params.page);
            }

            // Load structure for current page
            await this.loadStructureForPage(this.currentPage);

            // Set up slideshow page change listener
            this.setupSlideshowListener();
        }

        // Handle chunk parameter in URL (deep link)
        if (params.chunk) {
            await this.navigateToChunk(params.chunk);
        }

        // Set up browser back/forward navigation
        this.setupURLNavigationListener();

        this.isInitialized = true;
        console.log('[DetailsController] Initialized');
    }

    /**
     * Get markdown container element.
     *
     * @private
     * @returns {HTMLElement|null}
     */
    getMarkdownContainer() {
        // The accordion creates a "Full Document" section with rendered markdown
        const markdownSection = document.getElementById('markdown-full');
        if (!markdownSection) {
            console.warn('[DetailsController] Markdown section not found');
            return null;
        }

        // Find the content div within the section
        const contentDiv = markdownSection.querySelector('.accordion-content');
        if (!contentDiv) {
            console.warn('[DetailsController] Markdown content div not found');
            return null;
        }

        return contentDiv;
    }

    /**
     * Load document structure for a specific page.
     *
     * @param {number} page - Page number (1-indexed)
     * @returns {Promise<Object|null>} Structure data or null if unavailable
     */
    async loadStructureForPage(page) {
        try {
            // Check cache
            if (this.structureCache.has(page)) {
                console.log(`[DetailsController] Using cached structure for page ${page}`);
                return this.structureCache.get(page);
            }

            // Fetch structure from API
            console.log(`[DetailsController] Fetching structure for page ${page}`);
            const response = await fetch(`/documents/${this.docId}/pages/${page}/structure`);

            if (!response.ok) {
                if (response.status === 404) {
                    console.log(`[DetailsController] No structure available for page ${page}`);
                } else {
                    console.error(`[DetailsController] Failed to fetch structure: ${response.status}`);
                }
                return null;
            }

            const structure = await response.json();

            // Cache structure
            this.structureCache.set(page, structure);

            // Initialize overlay if structure has bboxes
            if (structure.has_structure && structure.headings && structure.headings.length > 0) {
                this.initializeBboxOverlay(structure);
            } else {
                console.log(`[DetailsController] No bboxes available for page ${page}`);
                this.destroyBboxOverlay();
            }

            return structure;

        } catch (error) {
            console.error('[DetailsController] Error loading structure:', error);
            return null;
        }
    }

    /**
     * Initialize BoundingBox overlay for current page image.
     *
     * @private
     * @param {Object} structure - Structure data from API
     */
    initializeBboxOverlay(structure) {
        // Destroy existing overlay
        this.destroyBboxOverlay();

        // Get current page image element
        const imageElement = document.getElementById('slideshow-image');
        if (!imageElement) {
            console.warn('[DetailsController] No slideshow image element');
            return;
        }

        // Extract coordinate system info
        const coordSystem = structure.coordinate_system || {};
        const pdfWidth = coordSystem.image_width || 612;
        const pdfHeight = coordSystem.image_height || 792;

        // Create overlay with headings (which contain chunk_ids)
        this.overlay = new BoundingBoxOverlay(imageElement, structure.headings, {
            pdfWidth,
            pdfHeight,
            enableHover: true,
            enableClick: true,
            enableKeyboard: true,
        });

        this.overlay.render();
        this.setupBboxOverlayEvents();

        console.log(`[DetailsController] BboxOverlay initialized with ${structure.headings.length} bboxes`);
    }

    /**
     * Destroy current BoundingBox overlay.
     *
     * @private
     */
    destroyBboxOverlay() {
        if (this.overlay) {
            this.overlay.destroy();
            this.overlay = null;
        }
    }

    /**
     * Set up event listeners for BboxOverlay.
     *
     * @private
     */
    setupBboxOverlayEvents() {
        if (!this.overlay) return;

        // Click: Navigate to chunk
        this.overlay.onBboxClick((chunkId, elementType, event) => {
            console.log(`[DetailsController] Bbox clicked: ${chunkId}`);
            this.handleBboxClick(chunkId);
        });

        // Hover: Highlight corresponding chunk
        this.overlay.onBboxHover((chunkId, elementType, isEnter, event) => {
            if (this.highlighter) {
                if (isEnter) {
                    this.highlighter.highlightChunk(chunkId, false);
                } else {
                    // Only clear if not the active chunk
                    if (this.highlighter.getActiveChunkId() !== chunkId) {
                        this.highlighter.clearHighlight();
                    }
                }
            }
        });
    }

    /**
     * Set up event listeners for ChunkHighlighter.
     *
     * @private
     */
    setupChunkHighlighterEvents() {
        if (!this.highlighter) return;

        // Hover: Highlight corresponding bbox
        const cleanup = this.highlighter.onChunkHover((chunkId, isEnter) => {
            if (this.overlay) {
                if (isEnter) {
                    this.overlay.highlightBbox(chunkId, false);
                } else {
                    // Only clear if not the active bbox
                    if (this.overlay.activeBboxId !== chunkId) {
                        this.overlay.clearHighlight();
                    }
                }
            }
        });

        this.cleanupFunctions.push(cleanup);
    }

    /**
     * Set up slideshow page change listener.
     *
     * @private
     */
    setupSlideshowListener() {
        if (!this.slideshow) return;

        // Store original goToPage method
        const originalGoToPage = this.slideshow.goToPage.bind(this.slideshow);

        // Wrap goToPage to detect page changes
        this.slideshow.goToPage = async (pageNumber) => {
            // Call original method
            originalGoToPage(pageNumber);

            // Handle page change
            if (pageNumber !== this.currentPage) {
                this.currentPage = pageNumber;
                console.log(`[DetailsController] Page changed to ${pageNumber}`);

                // Load structure for new page
                await this.loadStructureForPage(pageNumber);

                // Update URL (without chunk parameter)
                updateURL(this.docId, pageNumber, null);
            }
        };

        console.log('[DetailsController] Slideshow listener set up');
    }

    /**
     * Set up browser navigation listener (back/forward buttons).
     *
     * @private
     */
    setupURLNavigationListener() {
        const cleanup = onURLChange(async (docId, page, chunkId) => {
            console.log('[DetailsController] URL changed:', { docId, page, chunkId });

            // Navigate to page if specified
            if (page && page !== this.currentPage && this.slideshow) {
                this.slideshow.goToPage(page);
            }

            // Navigate to chunk if specified
            if (chunkId) {
                await this.navigateToChunk(chunkId);
            }
        });

        this.cleanupFunctions.push(cleanup);
    }

    /**
     * Handle bbox click event.
     *
     * @private
     * @param {string} chunkId - Chunk identifier
     */
    async handleBboxClick(chunkId) {
        // 1. Highlight bbox permanently
        if (this.overlay) {
            this.overlay.highlightBbox(chunkId, true);
        }

        // 2. Scroll to chunk in markdown
        if (this.highlighter) {
            this.highlighter.scrollToChunk(chunkId, true);
            this.highlighter.highlightChunk(chunkId, true);
        }

        // 3. Update URL with chunk parameter
        updateURL(this.docId, this.currentPage, chunkId);

        // 4. Optionally expand the markdown section
        this.expandMarkdownSection();
    }

    /**
     * Navigate to a specific chunk (from URL or API).
     *
     * @param {string} chunkId - Chunk identifier
     */
    async navigateToChunk(chunkId) {
        console.log(`[DetailsController] Navigating to chunk: ${chunkId}`);

        try {
            // Fetch chunk metadata to get page number
            const response = await fetch(`/documents/${this.docId}/chunks/${chunkId}`);

            if (!response.ok) {
                console.error(`[DetailsController] Chunk not found: ${chunkId}`);
                return;
            }

            const chunk = await response.json();
            console.log('[DetailsController] Chunk data:', chunk);

            // Navigate to correct page if needed
            if (chunk.page && chunk.page !== this.currentPage && this.slideshow) {
                console.log(`[DetailsController] Navigating to page ${chunk.page}`);
                this.slideshow.goToPage(chunk.page);
                this.currentPage = chunk.page;

                // Wait for structure to load
                await this.loadStructureForPage(chunk.page);
            }

            // Highlight bbox if available
            if (this.overlay && chunk.bbox) {
                this.overlay.highlightBbox(chunkId, true);
            }

            // Scroll to and highlight chunk in markdown
            if (this.highlighter) {
                // Small delay to ensure markdown is rendered
                setTimeout(() => {
                    this.highlighter.scrollToChunk(chunkId, true);
                    this.highlighter.highlightChunk(chunkId, true);
                    this.expandMarkdownSection();
                }, 300);
            }

        } catch (error) {
            console.error('[DetailsController] Error navigating to chunk:', error);
        }
    }

    /**
     * Expand the markdown section in accordion.
     *
     * @private
     */
    expandMarkdownSection() {
        const markdownSection = document.getElementById('markdown-full');
        if (!markdownSection) return;

        const header = markdownSection.querySelector('.accordion-header');
        if (header && !markdownSection.classList.contains('active')) {
            header.click(); // Trigger accordion open
        }
    }

    /**
     * Clean up resources and event listeners.
     */
    destroy() {
        console.log('[DetailsController] Destroying');

        // Destroy components
        this.destroyBboxOverlay();

        if (this.highlighter) {
            this.highlighter.destroy();
            this.highlighter = null;
        }

        // Run cleanup functions
        this.cleanupFunctions.forEach((cleanup) => cleanup());
        this.cleanupFunctions = [];

        // Clear cache
        this.structureCache.clear();

        this.isInitialized = false;
    }
}

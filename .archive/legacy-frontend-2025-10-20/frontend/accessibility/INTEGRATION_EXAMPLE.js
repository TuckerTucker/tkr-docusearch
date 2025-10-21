/**
 * Integration Example for Accessibility Modules
 *
 * This file demonstrates how to integrate the accessibility modules
 * into the bidirectional highlighting system.
 *
 * For use by Agent 8 (BBox Overlay), Agent 9 (Details Controller),
 * and Agent 10 (Research Navigation).
 */

// ===== IMPORTS =====

import { enableKeyboardNav, addSkipLinks, trapFocus, saveFocus } from './keyboard-nav.js';
import {
    labelBbox,
    labelChunk,
    labelOverlay,
    labelContextBadge,
    labelCitation,
    updateHighlightState,
    labelNavigationControls,
    labelSearchForm,
    labelModal
} from './aria-labels.js';
import {
    announceChunkNav,
    announceBboxNav,
    announceHighlight,
    announceClearHighlight,
    announceSearchResults,
    announceResearchAnswer,
    announceCitationNav,
    announceLoading,
    announceLoadingComplete,
    announceError,
    announceDocumentLoaded,
    initializeLiveRegions
} from './screen-reader-announce.js';

// ===== EXAMPLE 1: BoundingBoxOverlay Integration (Agent 8) =====

class BoundingBoxOverlay {
    constructor(container, imageElement) {
        this.container = container;
        this.imageElement = imageElement;
        this.bboxes = [];
        this.svgOverlay = null;
    }

    async init(documentName) {
        // Create SVG overlay
        this.svgOverlay = this.createSVGOverlay();

        // Label the overlay for screen readers
        labelOverlay(this.svgOverlay, documentName, this.bboxes.length);

        // Load and render bboxes
        await this.loadBboxes();
        this.renderBboxes();

        // Make bboxes keyboard accessible (handled by enableKeyboardNav)
    }

    renderBboxes() {
        this.bboxes.forEach((bbox, index) => {
            const rectElement = this.createBboxRect(bbox);

            // Label bbox for screen readers
            labelBbox(rectElement, bbox, index, this.bboxes.length);

            // Add to SVG
            this.svgOverlay.appendChild(rectElement);

            // Store reference
            bbox.element = rectElement;
        });
    }

    highlightBbox(bboxId, permanent = false) {
        const bbox = this.bboxes.find(b => b.id === bboxId);
        if (!bbox) return;

        // Visual highlight
        bbox.element.classList.add(permanent ? 'active' : 'hover');

        // Update ARIA state
        updateHighlightState(bbox.element, true, permanent);

        // Announce to screen reader
        if (permanent) {
            announceBboxNav(
                bbox.element_type,
                bbox.parent_heading,
                bbox.page,
                this.bboxes.indexOf(bbox),
                this.bboxes.length
            );
        }
    }

    clearHighlight(bboxId) {
        const bbox = this.bboxes.find(b => b.id === bboxId);
        if (!bbox) return;

        // Remove visual highlight
        bbox.element.classList.remove('hover', 'active');

        // Update ARIA state
        updateHighlightState(bbox.element, false, false);
    }

    // ... rest of BoundingBoxOverlay implementation
}

// ===== EXAMPLE 2: ChunkHighlighter Integration (Agent 9) =====

class ChunkHighlighter {
    constructor(markdownContainer) {
        this.markdownContainer = markdownContainer;
        this.chunks = [];
    }

    init() {
        // Find all chunks in markdown
        this.chunks = this.findChunks();

        // Label chunks for screen readers
        this.chunks.forEach((chunk, index) => {
            labelChunk(chunk.element, chunk, index, this.chunks.length);
        });
    }

    highlightChunk(chunkId, permanent = false) {
        const chunk = this.chunks.find(c => c.id === chunkId);
        if (!chunk) return;

        // Visual highlight
        chunk.element.classList.add(permanent ? 'chunk-active' : 'chunk-hover');

        // Update ARIA state
        updateHighlightState(chunk.element, true, permanent);

        // Announce to screen reader
        if (permanent) {
            announceChunkNav(
                chunk.parent_heading,
                chunk.page,
                this.chunks.indexOf(chunk),
                this.chunks.length
            );

            // Announce highlight action
            announceHighlight(chunkId, chunk.element_type, true);
        }

        // Scroll into view
        if (permanent) {
            chunk.element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    clearHighlight(chunkId) {
        const chunk = this.chunks.find(c => c.id === chunkId);
        if (!chunk) return;

        // Remove visual highlight
        chunk.element.classList.remove('chunk-hover', 'chunk-active');

        // Update ARIA state
        updateHighlightState(chunk.element, false, false);
    }

    // ... rest of ChunkHighlighter implementation
}

// ===== EXAMPLE 3: DetailsController Integration (Agent 9) =====

class DetailsController {
    constructor(config) {
        this.config = config;
        this.highlighter = null;
        this.overlay = null;
        this.chunkContextManager = null;
    }

    async init() {
        // Initialize live regions first
        initializeLiveRegions();

        // Add skip links
        addSkipLinks();

        // Initialize highlighter and overlay
        this.highlighter = new ChunkHighlighter(
            document.querySelector('.markdown-content')
        );
        this.highlighter.init();

        this.overlay = new BoundingBoxOverlay(
            document.querySelector('.bbox-container'),
            document.querySelector('.document-image')
        );
        await this.overlay.init(this.config.documentName);

        // Enable keyboard navigation
        enableKeyboardNav(this.highlighter, this.overlay);

        // Set up bidirectional callbacks
        this.setupBidirectionalHighlighting();

        // Announce document loaded
        announceDocumentLoaded(this.config.documentName, this.config.totalPages);
    }

    setupBidirectionalHighlighting() {
        // Chunk → BBox highlighting
        this.highlighter.onChunkActivate = (chunkId) => {
            const chunk = this.highlighter.chunks.find(c => c.id === chunkId);
            if (chunk && chunk.bboxIds) {
                chunk.bboxIds.forEach(bboxId => {
                    this.overlay.highlightBbox(bboxId, true);
                });
            }
        };

        // BBox → Chunk highlighting
        this.overlay.onBboxActivate = (bboxId) => {
            const bbox = this.overlay.bboxes.find(b => b.id === bboxId);
            if (bbox && bbox.chunkIds) {
                bbox.chunkIds.forEach(chunkId => {
                    this.highlighter.highlightChunk(chunkId, true);
                });
            }
        };
    }

    async navigateToChunk(chunkId) {
        announceLoading('chunk content');

        try {
            const chunk = await this.getChunk(chunkId);

            // Highlight chunk
            this.highlighter.highlightChunk(chunkId, true);

            // Announce navigation
            announceChunkNav(chunk.parent_heading, chunk.page);

            announceLoadingComplete('chunk content');
        } catch (error) {
            announceError(`Failed to load chunk: ${error.message}`);
        }
    }

    clearAllHighlights() {
        // Clear all highlights
        this.highlighter.chunks.forEach(chunk => {
            this.highlighter.clearHighlight(chunk.id);
        });

        this.overlay.bboxes.forEach(bbox => {
            this.overlay.clearHighlight(bbox.id);
        });

        // Announce
        announceClearHighlight(true);
    }

    // ... rest of DetailsController implementation
}

// ===== EXAMPLE 4: ResearchController Integration (Agent 10) =====

class ResearchController {
    constructor() {
        this.queryInput = document.getElementById('research-query');
        this.submitButton = document.getElementById('research-submit');
        this.answerContainer = document.getElementById('research-answer');
        this.referencesContainer = document.getElementById('research-references');
    }

    init() {
        // Initialize live regions
        initializeLiveRegions();

        // Label search form
        labelSearchForm(
            this.queryInput.closest('form'),
            this.queryInput,
            this.submitButton
        );

        // Set up event listeners
        this.submitButton.addEventListener('click', () => this.handleSearch());
    }

    async handleSearch() {
        const query = this.queryInput.value.trim();
        if (!query) return;

        announceLoading('search results');

        try {
            const results = await this.searchDocuments(query);

            // Render results
            this.renderResults(results);

            // Announce results
            announceSearchResults(results.length, query);

            // If research answer, announce it
            if (results.answer) {
                announceResearchAnswer(results.citations.length);
            }

            announceLoadingComplete('search results');
        } catch (error) {
            announceError(`Search failed: ${error.message}`);
        }
    }

    renderResults(results) {
        // Render citations with labels
        results.citations.forEach((citation, index) => {
            const citationElement = this.createCitationLink(citation, index + 1);

            // Label citation for screen readers
            labelCitation(
                citationElement,
                index + 1,
                citation.document,
                citation.page
            );

            // Add click handler
            citationElement.addEventListener('click', (e) => {
                e.preventDefault();
                this.navigateToCitation(citation, index + 1);
            });
        });
    }

    navigateToCitation(citation, citationNumber) {
        // Navigate to document
        this.loadDocument(citation.documentId, citation.page);

        // Announce navigation
        announceCitationNav(citationNumber, citation.document, citation.page);
    }

    // ... rest of ResearchController implementation
}

// ===== EXAMPLE 5: Modal Integration =====

class DocumentModal {
    constructor(modalElement) {
        this.modalElement = modalElement;
        this.restoreFocus = null;
    }

    open(title, content) {
        // Save current focus
        this.restoreFocus = saveFocus();

        // Label modal
        labelModal(this.modalElement, title, 'Document details and metadata');

        // Show modal
        this.modalElement.classList.add('visible');

        // Trap focus
        trapFocus(this.modalElement);

        // Populate content
        this.modalElement.querySelector('.modal-content').innerHTML = content;
    }

    close() {
        // Hide modal
        this.modalElement.classList.remove('visible');

        // Restore focus
        if (this.restoreFocus) {
            this.restoreFocus();
        }
    }
}

// ===== EXAMPLE 6: Complete Page Integration =====

async function initializePage() {
    // 1. Initialize live regions (must be first)
    initializeLiveRegions();

    // 2. Add skip links
    addSkipLinks();

    // 3. Initialize controllers
    const detailsController = new DetailsController({
        documentName: 'Technical Manual',
        totalPages: 42
    });
    await detailsController.init();

    const researchController = new ResearchController();
    researchController.init();

    // 4. Set up global error handling
    window.addEventListener('error', (event) => {
        announceError(`An error occurred: ${event.message}`);
    });

    // 5. Announce page ready
    announceDocumentLoaded('Research Interface', 1);
}

// Initialize on DOMContentLoaded
if (typeof window !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializePage);
    } else {
        initializePage();
    }
}

// ===== EXAMPLE 7: Context Badge Integration =====

class ChunkContextBadge {
    constructor(container) {
        this.container = container;
    }

    show(context) {
        const badge = document.createElement('div');
        badge.className = 'chunk-context-badge';
        badge.textContent = `${context.heading} - Page ${context.page}`;

        // Label for screen readers
        labelContextBadge(badge, context);

        // Make clickable
        badge.addEventListener('click', () => {
            // Navigate to chunk
            window.detailsController?.navigateToChunk(context.chunkId);
        });

        this.container.appendChild(badge);
    }
}

// ===== EXPORT FOR USE BY OTHER AGENTS =====

export {
    // Controllers (for reference)
    BoundingBoxOverlay,
    ChunkHighlighter,
    DetailsController,
    ResearchController,
    DocumentModal,
    ChunkContextBadge,

    // Initialization function
    initializePage
};

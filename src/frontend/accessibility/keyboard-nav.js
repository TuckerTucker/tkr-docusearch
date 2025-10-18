/**
 * Keyboard Navigation Module
 *
 * Provides comprehensive keyboard control for bidirectional highlighting:
 * - Tab/Shift+Tab: Navigate between chunks and bboxes
 * - Enter/Space: Activate chunk (permanent highlight + scroll)
 * - Escape: Clear all highlights
 * - Arrow keys: Navigate chunks/bboxes
 * - /: Focus search (research page)
 *
 * WCAG 2.1 AA Compliant - Full keyboard accessibility
 */

/**
 * Enable keyboard navigation for bidirectional highlighting
 * @param {ChunkHighlighter} highlighter - Chunk highlighter instance
 * @param {BoundingBoxOverlay} overlay - Bbox overlay instance
 */
export function enableKeyboardNav(highlighter, overlay) {
    // Track keyboard navigation mode
    let isKeyboardNavigating = false;

    // Add keyboard navigation class to body when using keyboard
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Tab' || e.key.startsWith('Arrow')) {
            isKeyboardNavigating = true;
            document.body.classList.add('keyboard-navigating');
        }
    });

    document.addEventListener('mousedown', () => {
        isKeyboardNavigating = false;
        document.body.classList.remove('keyboard-navigating');
    });

    // Make components keyboard accessible
    makeChunksFocusable(highlighter);
    makeBoxesFocusable(overlay);

    // Global keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Escape - Clear all highlights
        if (e.key === 'Escape') {
            clearAllHighlights(highlighter, overlay);
            return;
        }

        // / - Focus search (research page)
        if (e.key === '/' && !isInputFocused()) {
            e.preventDefault();
            focusSearch();
            return;
        }
    });
}

/**
 * Make chunks keyboard accessible
 * @param {ChunkHighlighter} highlighter - Chunk highlighter instance
 */
export function makeChunksFocusable(highlighter) {
    const chunkElements = document.querySelectorAll('[data-chunk-id]');

    chunkElements.forEach((chunkEl, index) => {
        // Add tabindex for keyboard focus
        chunkEl.setAttribute('tabindex', '0');

        // Keyboard event handlers
        chunkEl.addEventListener('keydown', (e) => {
            const chunkId = chunkEl.dataset.chunkId;

            switch (e.key) {
                case 'Enter':
                case ' ':
                    e.preventDefault();
                    activateChunk(highlighter, chunkId, chunkEl);
                    break;

                case 'ArrowDown':
                    e.preventDefault();
                    navigateToNextChunk(chunkElements, index);
                    break;

                case 'ArrowUp':
                    e.preventDefault();
                    navigateToPreviousChunk(chunkElements, index);
                    break;
            }
        });

        // Focus event handlers
        chunkEl.addEventListener('focus', () => {
            if (document.body.classList.contains('keyboard-navigating')) {
                highlighter.highlightChunk(chunkEl.dataset.chunkId, false);
            }
        });

        chunkEl.addEventListener('blur', () => {
            if (!chunkEl.classList.contains('chunk-active')) {
                highlighter.clearHighlight(chunkEl.dataset.chunkId);
            }
        });
    });
}

/**
 * Make bboxes keyboard accessible
 * @param {BoundingBoxOverlay} overlay - Bbox overlay instance
 */
export function makeBoxesFocusable(overlay) {
    const bboxElements = overlay.container.querySelectorAll('.bbox-rect');

    bboxElements.forEach((bboxEl, index) => {
        // Add tabindex for keyboard focus
        bboxEl.setAttribute('tabindex', '0');

        // Store bbox data reference
        const bboxId = bboxEl.dataset.bboxId;

        // Keyboard event handlers
        bboxEl.addEventListener('keydown', (e) => {
            switch (e.key) {
                case 'Enter':
                case ' ':
                    e.preventDefault();
                    activateBbox(overlay, bboxId, bboxEl);
                    break;

                case 'ArrowRight':
                    e.preventDefault();
                    navigateToNextBbox(bboxElements, index);
                    break;

                case 'ArrowLeft':
                    e.preventDefault();
                    navigateToPreviousBbox(bboxElements, index);
                    break;
            }
        });

        // Focus event handlers
        bboxEl.addEventListener('focus', () => {
            if (document.body.classList.contains('keyboard-navigating')) {
                overlay.highlightBbox(bboxId, false);
            }
        });

        bboxEl.addEventListener('blur', () => {
            if (!bboxEl.classList.contains('active')) {
                overlay.clearHighlight(bboxId);
            }
        });
    });
}

/**
 * Activate chunk (permanent highlight + scroll)
 * @param {ChunkHighlighter} highlighter - Chunk highlighter instance
 * @param {string} chunkId - Chunk ID to activate
 * @param {HTMLElement} chunkEl - Chunk element
 */
function activateChunk(highlighter, chunkId, chunkEl) {
    // Permanent highlight
    highlighter.highlightChunk(chunkId, true);

    // Add active class
    document.querySelectorAll('[data-chunk-id]').forEach(el => {
        el.classList.remove('chunk-active');
    });
    chunkEl.classList.add('chunk-active');

    // Scroll into view
    chunkEl.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
    });

    // Trigger corresponding bbox highlight
    if (highlighter.onChunkActivate) {
        highlighter.onChunkActivate(chunkId);
    }
}

/**
 * Activate bbox (permanent highlight + scroll to chunk)
 * @param {BoundingBoxOverlay} overlay - Bbox overlay instance
 * @param {string} bboxId - Bbox ID to activate
 * @param {SVGElement} bboxEl - Bbox element
 */
function activateBbox(overlay, bboxId, bboxEl) {
    // Permanent highlight
    overlay.highlightBbox(bboxId, true);

    // Add active class
    overlay.container.querySelectorAll('.bbox-rect').forEach(el => {
        el.classList.remove('active');
    });
    bboxEl.classList.add('active');

    // Trigger corresponding chunk highlight
    if (overlay.onBboxActivate) {
        overlay.onBboxActivate(bboxId);
    }
}

/**
 * Navigate to next chunk
 * @param {NodeList} chunkElements - All chunk elements
 * @param {number} currentIndex - Current chunk index
 */
function navigateToNextChunk(chunkElements, currentIndex) {
    const nextIndex = (currentIndex + 1) % chunkElements.length;
    const nextChunk = chunkElements[nextIndex];

    nextChunk.focus();
    nextChunk.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
    });
}

/**
 * Navigate to previous chunk
 * @param {NodeList} chunkElements - All chunk elements
 * @param {number} currentIndex - Current chunk index
 */
function navigateToPreviousChunk(chunkElements, currentIndex) {
    const prevIndex = currentIndex === 0 ? chunkElements.length - 1 : currentIndex - 1;
    const prevChunk = chunkElements[prevIndex];

    prevChunk.focus();
    prevChunk.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
    });
}

/**
 * Navigate to next bbox
 * @param {NodeList} bboxElements - All bbox elements
 * @param {number} currentIndex - Current bbox index
 */
function navigateToNextBbox(bboxElements, currentIndex) {
    const nextIndex = (currentIndex + 1) % bboxElements.length;
    bboxElements[nextIndex].focus();
}

/**
 * Navigate to previous bbox
 * @param {NodeList} bboxElements - All bbox elements
 * @param {number} currentIndex - Current bbox index
 */
function navigateToPreviousBbox(bboxElements, currentIndex) {
    const prevIndex = currentIndex === 0 ? bboxElements.length - 1 : currentIndex - 1;
    bboxElements[prevIndex].focus();
}

/**
 * Clear all highlights
 * @param {ChunkHighlighter} highlighter - Chunk highlighter instance
 * @param {BoundingBoxOverlay} overlay - Bbox overlay instance
 */
function clearAllHighlights(highlighter, overlay) {
    // Clear chunk highlights
    document.querySelectorAll('[data-chunk-id]').forEach(el => {
        el.classList.remove('chunk-hover', 'chunk-active');
        highlighter.clearHighlight(el.dataset.chunkId);
    });

    // Clear bbox highlights
    overlay.container.querySelectorAll('.bbox-rect').forEach(el => {
        el.classList.remove('active');
        overlay.clearHighlight(el.dataset.bboxId);
    });

    // Return focus to main content
    document.querySelector('[data-chunk-id]')?.focus();
}

/**
 * Focus search input
 */
function focusSearch() {
    const searchInput = document.querySelector('#research-query')
        || document.querySelector('input[type="search"]')
        || document.querySelector('input[type="text"]');

    if (searchInput) {
        searchInput.focus();
        searchInput.select();
    }
}

/**
 * Check if an input element is currently focused
 * @returns {boolean} True if input focused
 */
function isInputFocused() {
    const activeElement = document.activeElement;
    return activeElement && (
        activeElement.tagName === 'INPUT' ||
        activeElement.tagName === 'TEXTAREA' ||
        activeElement.isContentEditable
    );
}

/**
 * Add skip links for navigation
 */
export function addSkipLinks() {
    const skipLinks = document.createElement('div');
    skipLinks.className = 'skip-links';
    skipLinks.innerHTML = `
        <a href="#main-content" class="skip-link">Skip to main content</a>
        <a href="#research-query" class="skip-link">Skip to search</a>
        <a href="#references-list" class="skip-link">Skip to references</a>
    `;

    document.body.insertBefore(skipLinks, document.body.firstChild);
}

/**
 * Handle focus trap in modal dialogs
 * @param {HTMLElement} modal - Modal element
 */
export function trapFocus(modal) {
    const focusableElements = modal.querySelectorAll(
        'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
    );

    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];

    modal.addEventListener('keydown', (e) => {
        if (e.key !== 'Tab') return;

        if (e.shiftKey) {
            // Shift + Tab
            if (document.activeElement === firstFocusable) {
                e.preventDefault();
                lastFocusable.focus();
            }
        } else {
            // Tab
            if (document.activeElement === lastFocusable) {
                e.preventDefault();
                firstFocusable.focus();
            }
        }
    });

    // Focus first element when modal opens
    firstFocusable?.focus();
}

/**
 * Restore focus after modal closes
 * @returns {Function} Restore function
 */
export function saveFocus() {
    const previouslyFocused = document.activeElement;

    return function restore() {
        if (previouslyFocused && previouslyFocused.focus) {
            previouslyFocused.focus();
        }
    };
}

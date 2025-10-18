/**
 * Screen Reader Announcements Module
 *
 * Provides live announcements for screen readers:
 * - Navigation announcements (chunk/bbox changes)
 * - Highlight action announcements
 * - Search result announcements
 * - Error/status announcements
 *
 * Uses ARIA live regions for dynamic content updates.
 * WCAG 2.1 AA Compliant - Screen reader accessible
 */

// Live region cache
let liveRegion = null;
let assertiveRegion = null;

/**
 * Initialize live regions for screen reader announcements
 */
export function initializeLiveRegions() {
    // Polite region for most announcements
    liveRegion = createLiveRegion('sr-announcements', 'polite');

    // Assertive region for important announcements
    assertiveRegion = createLiveRegion('sr-announcements-assertive', 'assertive');
}

/**
 * Create ARIA live region
 * @param {string} id - Element ID
 * @param {string} priority - 'polite' | 'assertive'
 * @returns {HTMLElement} Live region element
 */
function createLiveRegion(id, priority) {
    // Check if already exists
    let region = document.getElementById(id);

    if (!region) {
        region = document.createElement('div');
        region.id = id;
        region.className = 'sr-only';
        region.setAttribute('aria-live', priority);
        region.setAttribute('aria-atomic', 'true');
        region.setAttribute('role', priority === 'assertive' ? 'alert' : 'status');
        document.body.appendChild(region);
    }

    return region;
}

/**
 * Announce chunk navigation
 * @param {string} heading - Parent heading text
 * @param {number} page - Page number
 * @param {number} index - Chunk index (optional)
 * @param {number} total - Total chunks (optional)
 */
export function announceChunkNav(heading, page, index = null, total = null) {
    let message = `Navigated to ${heading} on page ${page}`;

    if (index !== null && total !== null) {
        message += `. Chunk ${index + 1} of ${total}`;
    }

    announceToScreenReader(message, 'polite');
}

/**
 * Announce bbox navigation
 * @param {string} elementType - Element type (section, table, etc.)
 * @param {string} heading - Parent heading text
 * @param {number} page - Page number
 * @param {number} index - Bbox index (optional)
 * @param {number} total - Total bboxes (optional)
 */
export function announceBboxNav(elementType, heading, page, index = null, total = null) {
    let message = `Navigated to ${elementType}: ${heading} on page ${page}`;

    if (index !== null && total !== null) {
        message += `. Region ${index + 1} of ${total}`;
    }

    announceToScreenReader(message, 'polite');
}

/**
 * Announce highlight action
 * @param {string} chunkId - Chunk ID
 * @param {string} elementType - Element type
 * @param {boolean} isPermanent - Whether highlight is permanent
 */
export function announceHighlight(chunkId, elementType, isPermanent = false) {
    const action = isPermanent ? 'Activated' : 'Highlighted';
    const message = `${action} ${elementType} section`;

    announceToScreenReader(message, 'polite');
}

/**
 * Announce highlight cleared
 * @param {boolean} isAll - Whether all highlights cleared
 */
export function announceClearHighlight(isAll = false) {
    const message = isAll ? 'All highlights cleared' : 'Highlight cleared';
    announceToScreenReader(message, 'polite');
}

/**
 * Announce search results
 * @param {number} resultCount - Number of results found
 * @param {string} query - Search query
 */
export function announceSearchResults(resultCount, query) {
    let message;

    if (resultCount === 0) {
        message = `No results found for "${query}"`;
    } else if (resultCount === 1) {
        message = `1 result found for "${query}"`;
    } else {
        message = `${resultCount} results found for "${query}"`;
    }

    announceToScreenReader(message, 'polite');
}

/**
 * Announce research answer received
 * @param {number} citationCount - Number of citations
 */
export function announceResearchAnswer(citationCount) {
    let message = 'Research answer received';

    if (citationCount > 0) {
        message += ` with ${citationCount} citation${citationCount > 1 ? 's' : ''}`;
    }

    announceToScreenReader(message, 'polite');
}

/**
 * Announce citation navigation
 * @param {number} citationNumber - Citation number
 * @param {string} documentName - Document name
 * @param {number} page - Page number
 */
export function announceCitationNav(citationNumber, documentName, page) {
    const message = `Citation ${citationNumber}: Navigated to ${documentName}, page ${page}`;
    announceToScreenReader(message, 'polite');
}

/**
 * Announce loading state
 * @param {string} context - Loading context (e.g., "search results", "document")
 */
export function announceLoading(context) {
    const message = `Loading ${context}...`;
    announceToScreenReader(message, 'polite');
}

/**
 * Announce loading complete
 * @param {string} context - Loading context
 */
export function announceLoadingComplete(context) {
    const message = `${context} loaded`;
    announceToScreenReader(message, 'polite');
}

/**
 * Announce error
 * @param {string} errorMessage - Error message
 */
export function announceError(errorMessage) {
    const message = `Error: ${errorMessage}`;
    announceToScreenReader(message, 'assertive');
}

/**
 * Announce success
 * @param {string} successMessage - Success message
 */
export function announceSuccess(successMessage) {
    announceToScreenReader(successMessage, 'polite');
}

/**
 * Announce page change
 * @param {number} currentPage - Current page number
 * @param {number} totalPages - Total pages
 */
export function announcePageChange(currentPage, totalPages) {
    const message = `Page ${currentPage} of ${totalPages}`;
    announceToScreenReader(message, 'polite');
}

/**
 * Announce document loaded
 * @param {string} documentName - Document name
 * @param {number} totalPages - Total pages
 */
export function announceDocumentLoaded(documentName, totalPages) {
    const message = `Document loaded: ${documentName}. ${totalPages} page${totalPages > 1 ? 's' : ''}.`;
    announceToScreenReader(message, 'polite');
}

/**
 * Announce filter applied
 * @param {string} filterType - Filter type
 * @param {string} filterValue - Filter value
 * @param {number} resultCount - Number of results after filter
 */
export function announceFilterApplied(filterType, filterValue, resultCount) {
    const message = `Filter applied: ${filterType} = ${filterValue}. ${resultCount} result${resultCount !== 1 ? 's' : ''}.`;
    announceToScreenReader(message, 'polite');
}

/**
 * Announce sort applied
 * @param {string} sortBy - Sort criterion
 * @param {string} sortOrder - Sort order ('asc' | 'desc')
 */
export function announceSortApplied(sortBy, sortOrder) {
    const orderText = sortOrder === 'asc' ? 'ascending' : 'descending';
    const message = `Sorted by ${sortBy}, ${orderText}`;
    announceToScreenReader(message, 'polite');
}

/**
 * Announce modal opened
 * @param {string} modalTitle - Modal title
 */
export function announceModalOpened(modalTitle) {
    const message = `Dialog opened: ${modalTitle}`;
    announceToScreenReader(message, 'polite');
}

/**
 * Announce modal closed
 */
export function announceModalClosed() {
    const message = 'Dialog closed';
    announceToScreenReader(message, 'polite');
}

/**
 * Low-level screen reader announcement
 * @param {string} message - Message to announce
 * @param {string} priority - 'polite' | 'assertive'
 */
export function announceToScreenReader(message, priority = 'polite') {
    // Initialize regions if not already done
    if (!liveRegion) {
        initializeLiveRegions();
    }

    const region = priority === 'assertive' ? assertiveRegion : liveRegion;

    // Clear previous announcement
    region.textContent = '';

    // Small delay to ensure announcement is picked up
    setTimeout(() => {
        region.textContent = message;
    }, 100);

    // Clear after delay (screen reader will have read it by then)
    setTimeout(() => {
        region.textContent = '';
    }, 5000);
}

/**
 * Create status message element
 * @param {string} id - Element ID
 * @param {string} message - Status message
 * @param {string} priority - 'polite' | 'assertive'
 * @returns {HTMLElement} Status element
 */
export function createStatusMessage(id, message, priority = 'polite') {
    let statusEl = document.getElementById(id);

    if (!statusEl) {
        statusEl = document.createElement('div');
        statusEl.id = id;
        statusEl.className = 'sr-only';
        statusEl.setAttribute('role', 'status');
        statusEl.setAttribute('aria-live', priority);
        statusEl.setAttribute('aria-atomic', 'true');
        document.body.appendChild(statusEl);
    }

    statusEl.textContent = message;
    return statusEl;
}

/**
 * Update status message
 * @param {string} id - Element ID
 * @param {string} message - New status message
 */
export function updateStatusMessage(id, message) {
    const statusEl = document.getElementById(id);

    if (statusEl) {
        statusEl.textContent = message;
    }
}

/**
 * Remove status message
 * @param {string} id - Element ID
 */
export function removeStatusMessage(id) {
    const statusEl = document.getElementById(id);

    if (statusEl) {
        statusEl.remove();
    }
}

/**
 * Announce progress
 * @param {number} current - Current progress value
 * @param {number} total - Total progress value
 * @param {string} context - Progress context
 */
export function announceProgress(current, total, context) {
    const percentage = Math.round((current / total) * 100);
    const message = `${context}: ${percentage}% complete. ${current} of ${total}.`;
    announceToScreenReader(message, 'polite');
}

// Initialize on module load
if (typeof window !== 'undefined') {
    // Wait for DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeLiveRegions);
    } else {
        initializeLiveRegions();
    }
}

/**
 * Accessibility Module Index
 *
 * Convenience exports for all accessibility modules.
 * Import everything you need from a single entry point.
 *
 * Usage:
 *   import { enableKeyboardNav, labelBbox, announceChunkNav } from './accessibility/index.js';
 */

// Keyboard Navigation
export {
    enableKeyboardNav,
    makeChunksFocusable,
    makeBoxesFocusable,
    addSkipLinks,
    trapFocus,
    saveFocus
} from './keyboard-nav.js';

// ARIA Labels
export {
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

// Screen Reader Announcements
export {
    initializeLiveRegions,
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
    announceSuccess,
    announcePageChange,
    announceDocumentLoaded,
    announceFilterApplied,
    announceSortApplied,
    announceModalOpened,
    announceModalClosed,
    announceToScreenReader,
    createStatusMessage,
    updateStatusMessage,
    removeStatusMessage,
    announceProgress
} from './screen-reader-announce.js';

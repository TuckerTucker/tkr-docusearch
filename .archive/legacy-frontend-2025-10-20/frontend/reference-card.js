/**
 * Reference Card Component
 *
 * Renders reference cards for source documents.
 * Supports detailed and simple view modes.
 *
 * Wave 7 - Enhanced with chunk-level navigation support
 */

import { buildDetailsURL, hasChunkContext } from './utils/url-builder.js';

/**
 * Render reference cards
 * @param {Array} sources - Source documents from API
 * @param {HTMLElement} container - Container element
 * @param {string} variant - 'detailed' or 'simple'
 */
export function renderReferenceCards(sources, container, variant = 'detailed') {
    container.innerHTML = '';
    container.className = 'references-list';

    if (!sources || sources.length === 0) {
        const empty = document.createElement('p');
        empty.textContent = 'No references found.';
        empty.className = 'empty-state';
        container.appendChild(empty);
        return;
    }

    sources.forEach((source, index) => {
        const card = createReferenceCard(source, source.id || (index + 1), variant);
        container.appendChild(card);
    });

    // Attach event listeners for highlighting
    attachReferenceListeners(container);
}

/**
 * Create reference card element
 * @param {Object} source - Source document
 * @param {number} citationNum - Citation number (1-indexed)
 * @param {string} variant - 'detailed' or 'simple'
 * @returns {HTMLElement} Reference card
 */
function createReferenceCard(source, citationNum, variant) {
    const card = document.createElement('div');
    card.className = `reference-card reference-card--${variant}`;
    card.dataset.citationId = citationNum;
    card.setAttribute('role', 'article');
    card.setAttribute(
        'aria-label',
        `Reference ${citationNum}: ${source.filename}, Page ${source.page}`
    );

    // Build URL with chunk support (Wave 7 enhancement)
    const detailsURL = buildDetailsURL(source);
    const hasChunk = hasChunkContext(source);

    if (variant === 'detailed') {
        card.innerHTML = `
            <div class="reference-card__number">${citationNum}</div>
            ${source.thumbnail_path ? `
                <img
                    src="${source.thumbnail_path}"
                    alt="Thumbnail of ${source.filename}"
                    class="reference-card__thumbnail"
                    loading="lazy"
                    onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                />
                <div class="reference-card__thumbnail-placeholder" style="display:none;">
                    ${getFileIcon(source.extension)}
                </div>
            ` : `
                <div class="reference-card__thumbnail-placeholder">
                    ${getFileIcon(source.extension)}
                </div>
            `}
            <div class="reference-card__content">
                <div class="reference-card__badge">
                    ${source.extension.toUpperCase()}
                    ${hasChunk ? '<span class="chunk-indicator" title="Jump to specific section" aria-label="Has chunk-level navigation">📍</span>' : ''}
                </div>
                <div class="reference-card__filename" title="${source.filename}">
                    ${source.filename}
                </div>
                <div class="reference-card__meta">
                    Page ${source.page}${source.date_added ? ` • ${formatDate(source.date_added)}` : ''}
                </div>
            </div>
            <a
                href="${detailsURL}"
                class="reference-card__details-btn"
                aria-label="View details for ${source.filename}${hasChunk ? ' (jump to section)' : ''}"
            >
                Details
            </a>
        `;
    } else {
        // Simple variant
        card.innerHTML = `
            <div class="reference-card__number">${citationNum}</div>
            <div class="reference-card__filename-simple" title="${source.filename}">
                ${source.filename}
                ${hasChunk ? '<span class="chunk-indicator-simple" title="Jump to section">📍</span>' : ''}
            </div>
            <a
                href="${detailsURL}"
                class="reference-card__details-btn-simple"
                aria-label="View details${hasChunk ? ' (jump to section)' : ''}"
            >
                Details
            </a>
        `;
    }

    return card;
}

/**
 * Get file icon SVG based on extension
 * @param {string} extension - File extension
 * @returns {string} SVG markup
 */
function getFileIcon(extension) {
    const icons = {
        pdf: `<svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z"/>
            <path d="M14 2v6h6M9 13h6M9 17h6M9 9h1"/>
        </svg>`,
        docx: `<svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z"/>
            <path d="M14 2v6h6M10 9h4M10 13h4M10 17h4"/>
        </svg>`,
        pptx: `<svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z"/>
            <path d="M14 2v6h6M8 11h8v6H8z"/>
        </svg>`,
        mp3: `<svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
            <path d="M9 18V5l12-2v13M9 13c0 1.66-1.34 3-3 3s-3-1.34-3-3 1.34-3 3-3 3 1.34 3 3zm12 0c0 1.66-1.34 3-3 3s-3-1.34-3-3 1.34-3 3-3 3 1.34 3 3z"/>
        </svg>`,
        wav: `<svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
            <path d="M9 18V5l12-2v13M9 13c0 1.66-1.34 3-3 3s-3-1.34-3-3 1.34-3 3-3 3 1.34 3 3zm12 0c0 1.66-1.34 3-3 3s-3-1.34-3-3 1.34-3 3-3 3 1.34 3 3z"/>
        </svg>`,
        default: `<svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z"/>
        </svg>`
    };

    return icons[extension.toLowerCase()] || icons.default;
}

/**
 * Format date for display
 * @param {string} isoDate - ISO date string
 * @returns {string} Formatted date
 */
function formatDate(isoDate) {
    try {
        const date = new Date(isoDate);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch (e) {
        return isoDate;
    }
}

/**
 * Attach event listeners for reference highlighting
 * @param {HTMLElement} container - References container
 */
function attachReferenceListeners(container) {
    const cards = container.querySelectorAll('.reference-card');

    cards.forEach(card => {
        card.addEventListener('mouseenter', handleReferenceHover);
        card.addEventListener('mouseleave', handleReferenceLeave);
    });
}

/**
 * Handle reference hover (highlight citations)
 * @param {Event} event - Mouse event
 */
function handleReferenceHover(event) {
    const card = event.currentTarget;
    const citationId = card.dataset.citationId;

    // Highlight the reference card itself
    card.classList.add('reference-card--highlighted');

    // Find all citations with this ID
    const citations = document.querySelectorAll(
        `.citation-marker[data-citation-id="${citationId}"]`
    );

    citations.forEach(citation => {
        citation.classList.add('citation-marker--highlighted');

        // Highlight containing sentence
        const sentence = citation.closest('.answer-sentence');
        if (sentence) {
            sentence.classList.add('highlighted-sentence');
        }
    });
}

/**
 * Handle reference leave (remove highlight)
 * @param {Event} event - Mouse event
 */
function handleReferenceLeave(event) {
    const card = event.currentTarget;
    const citationId = card.dataset.citationId;

    // Remove highlight from reference card
    card.classList.remove('reference-card--highlighted');

    const citations = document.querySelectorAll(
        `.citation-marker[data-citation-id="${citationId}"]`
    );

    citations.forEach(citation => {
        citation.classList.remove('citation-marker--highlighted');

        const sentence = citation.closest('.answer-sentence');
        if (sentence) {
            sentence.classList.remove('highlighted-sentence');
        }
    });
}

// Add CSS styles dynamically
const style = document.createElement('style');
style.textContent = `
    .reference-card {
        display: flex;
        align-items: center;
        gap: var(--space-3);
        padding: var(--space-3);
        background: var(--muted);
        border: 1px solid var(--border);
        border-radius: var(--radius-md, 0.5rem);
        margin-bottom: var(--space-3);
        transition: all var(--transition-base, 200ms);
    }

    .reference-card:hover {
        background: var(--card);
        box-shadow: var(--shadow-md);
        cursor: pointer;
    }

    .reference-card.highlighted,
    .reference-card--highlighted {
        background: var(--citation-highlight-bg);
        border-color: var(--primary);
        border-width: 2px;
        box-shadow: var(--shadow-lg);
    }

    .reference-card__number {
        flex-shrink: 0;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--primary);
        color: var(--primary-foreground);
        border-radius: var(--radius-round, 9999px);
        font-weight: 600;
        font-size: var(--font-size-sm, 0.875rem);
    }

    .reference-card__thumbnail {
        flex-shrink: 0;
        max-height: 64px;
        width: auto;
        object-fit: contain;
        border-radius: var(--radius-sm, 0.25rem);
    }

    .reference-card__thumbnail-placeholder {
        flex-shrink: 0;
        width: 64px;
        height: 64px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--muted);
        border-radius: var(--radius-sm, 0.25rem);
        color: var(--muted-foreground);
    }

    .reference-card__content {
        flex: 1;
        min-width: 0;
    }

    .reference-card__badge {
        display: inline-block;
        padding: var(--space-1) var(--space-2);
        background: var(--accent);
        color: var(--primary);
        border-radius: var(--radius-sm, 0.25rem);
        font-size: var(--font-size-xs, 0.75rem);
        font-weight: 600;
        margin-bottom: var(--space-1);
    }

    .reference-card__filename {
        font-weight: 500;
        color: var(--foreground);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        margin-bottom: var(--space-1);
    }

    .reference-card__meta {
        font-size: var(--font-size-sm, 0.875rem);
        color: var(--muted-foreground);
    }

    .reference-card__details-btn {
        flex-shrink: 0;
        padding: var(--space-2) var(--space-4);
        background: var(--primary);
        color: var(--primary-foreground);
        border-radius: var(--radius-md, 0.5rem);
        text-decoration: none;
        font-size: var(--font-size-sm, 0.875rem);
        font-weight: 600;
        transition: all var(--transition-fast, 150ms);
    }

    .reference-card__details-btn:hover {
        background: color-mix(in oklch, var(--primary) 85%, black);
    }

    /* Simple variant */
    .reference-card--simple {
        padding: var(--space-2) var(--space-3);
    }

    .reference-card__filename-simple {
        flex: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-size: var(--font-size-base, 1rem);
        color: var(--foreground);
    }

    .reference-card__details-btn-simple {
        flex-shrink: 0;
        padding: var(--space-1) var(--space-3);
        background: var(--primary);
        color: var(--primary-foreground);
        border-radius: var(--radius-md, 0.5rem);
        text-decoration: none;
        font-size: var(--font-size-sm, 0.875rem);
        font-weight: 600;
    }

    /* Chunk navigation indicators (Wave 7) */
    .chunk-indicator {
        display: inline-block;
        margin-left: var(--space-1, 0.25rem);
        font-size: var(--font-size-xs, 0.75rem);
        opacity: 0.9;
        cursor: help;
        transition: opacity var(--transition-fast, 150ms);
    }

    .chunk-indicator:hover {
        opacity: 1;
    }

    .chunk-indicator-simple {
        display: inline-block;
        margin-left: var(--space-2, 0.5rem);
        font-size: var(--font-size-sm, 0.875rem);
        color: var(--primary);
        opacity: 0.8;
        cursor: help;
        transition: opacity var(--transition-fast, 150ms);
    }

    .chunk-indicator-simple:hover {
        opacity: 1;
    }

    /* Enhanced button styling for chunk links */
    .reference-card:has(.chunk-indicator) .reference-card__details-btn,
    .reference-card:has(.chunk-indicator-simple) .reference-card__details-btn-simple {
        background: color-mix(in oklch, var(--primary) 85%, black);
    }

    .reference-card:has(.chunk-indicator):hover .reference-card__details-btn,
    .reference-card:has(.chunk-indicator-simple):hover .reference-card__details-btn-simple {
        box-shadow: var(--shadow-md);
    }
`;
document.head.appendChild(style);

// Export for use in other modules
export { handleReferenceHover, handleReferenceLeave };

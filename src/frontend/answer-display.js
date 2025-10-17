/**
 * Answer Display Component
 *
 * Renders AI-generated answers with inline citation markers.
 * Handles citation highlighting and interaction.
 */

/**
 * Render answer with citations
 * @param {Object} data - Answer data from API
 * @param {string} data.answer - Answer text with citation markers
 * @param {Array} data.citations - Citation metadata
 * @param {Object} data.citation_map - Citation to sentence mapping
 * @param {HTMLElement} container - Container element
 */
export function renderAnswer(data, container) {
    container.innerHTML = '';
    container.className = 'answer-display';

    // Add title
    const title = document.createElement('h2');
    title.textContent = 'Answer';
    title.style.marginBottom = 'var(--space-4)';
    title.style.fontSize = 'var(--font-size-xl)';
    container.appendChild(title);

    // Parse answer text and create sentence elements
    const sentences = parseSentences(data.answer, data.citations);

    sentences.forEach((sentence, index) => {
        const sentenceEl = createSentenceElement(sentence, index);
        container.appendChild(sentenceEl);
    });

    // Attach event listeners for highlighting
    attachCitationListeners(container);
}

/**
 * Parse answer text into sentences with citations
 * @param {string} text - Full answer text
 * @param {Array} citations - Citation metadata
 * @returns {Array} Array of sentence objects
 */
function parseSentences(text, citations) {
    // Simple sentence splitting (improved regex)
    const sentencePattern = /[^.!?]+[.!?]+/g;
    const matches = text.match(sentencePattern) || [text];

    const sentences = [];
    let currentPos = 0;

    for (const match of matches) {
        const sentenceText = match.trim();
        const sentenceStart = text.indexOf(sentenceText, currentPos);
        const sentenceEnd = sentenceStart + sentenceText.length;

        // Find citations in this sentence
        const sentenceCitations = citations.filter(c =>
            c.start >= sentenceStart && c.end <= sentenceEnd
        );

        sentences.push({
            text: sentenceText,
            start: sentenceStart,
            end: sentenceEnd,
            citations: sentenceCitations
        });

        currentPos = sentenceEnd;
    }

    return sentences;
}

/**
 * Create sentence element with inline citations
 * @param {Object} sentence - Sentence data
 * @param {number} index - Sentence index
 * @returns {HTMLElement} Sentence element
 */
function createSentenceElement(sentence, index) {
    const sentenceEl = document.createElement('p');
    sentenceEl.className = 'answer-sentence';
    sentenceEl.dataset.sentenceIndex = index;

    // Split sentence text around citation markers
    const parts = splitByCitations(sentence.text, sentence.citations, sentence.start);

    parts.forEach(part => {
        if (part.type === 'text') {
            sentenceEl.appendChild(document.createTextNode(part.content));
        } else if (part.type === 'citation') {
            const citationEl = createCitationMarker(part.citation);
            sentenceEl.appendChild(citationEl);
        }
    });

    return sentenceEl;
}

/**
 * Split text by citations
 * @param {string} text - Sentence text
 * @param {Array} citations - Citations in sentence
 * @param {number} sentenceStart - Sentence start position in full text
 * @returns {Array} Array of text/citation parts
 */
function splitByCitations(text, citations, sentenceStart) {
    if (!citations || citations.length === 0) {
        return [{ type: 'text', content: text }];
    }

    const parts = [];
    let currentPos = 0;

    // Sort citations by position
    const sortedCitations = [...citations].sort((a, b) => a.start - b.start);

    for (const citation of sortedCitations) {
        // Calculate position relative to sentence
        const relativeStart = citation.start - sentenceStart;
        const relativeEnd = citation.end - sentenceStart;

        // Add text before citation
        if (relativeStart > currentPos) {
            parts.push({
                type: 'text',
                content: text.substring(currentPos, relativeStart)
            });
        }

        // Add citation
        parts.push({
            type: 'citation',
            citation: citation
        });

        currentPos = relativeEnd;
    }

    // Add remaining text
    if (currentPos < text.length) {
        parts.push({
            type: 'text',
            content: text.substring(currentPos)
        });
    }

    return parts;
}

/**
 * Create citation marker element
 * @param {Object} citation - Citation data
 * @returns {HTMLElement} Citation marker
 */
function createCitationMarker(citation) {
    const marker = document.createElement('span');
    marker.className = 'citation-marker';
    marker.dataset.citationId = citation.id;
    marker.textContent = citation.marker;
    marker.setAttribute('role', 'button');
    marker.setAttribute('tabindex', '0');
    marker.setAttribute('aria-label', `Citation ${citation.id}`);

    // Add styles
    Object.assign(marker.style, {
        display: 'inline-block',
        padding: '0 0.25rem',
        margin: '0 0.125rem',
        background: 'var(--color-primary-light)',
        color: 'var(--color-primary-base)',
        borderRadius: 'var(--radius-sm, 0.25rem)',
        fontSize: 'var(--font-size-sm, 0.875rem)',
        fontWeight: '600',
        cursor: 'pointer',
        transition: 'all var(--trans-fast, 150ms)',
        verticalAlign: 'super',
        fontFamily: 'var(--font-sans)'
    });

    return marker;
}

/**
 * Attach event listeners for citation highlighting
 * @param {HTMLElement} container - Answer container
 */
function attachCitationListeners(container) {
    const citations = container.querySelectorAll('.citation-marker');

    citations.forEach(citation => {
        citation.addEventListener('mouseenter', handleCitationHover);
        citation.addEventListener('mouseleave', handleCitationLeave);
        citation.addEventListener('focus', handleCitationHover);
        citation.addEventListener('blur', handleCitationLeave);
        citation.addEventListener('keydown', handleCitationKeydown);
    });
}

/**
 * Handle citation hover (highlight reference)
 * @param {Event} event - Mouse/focus event
 */
function handleCitationHover(event) {
    const citationId = event.target.dataset.citationId;
    const referenceCard = document.querySelector(
        `.reference-card[data-citation-id="${citationId}"]`
    );

    if (referenceCard) {
        referenceCard.classList.add('highlighted');
        scrollIntoViewIfNeeded(referenceCard);
    }

    // Highlight citation marker
    event.target.style.background = 'var(--color-primary-base)';
    event.target.style.color = 'var(--color-bg-primary)';
}

/**
 * Handle citation leave (remove highlight)
 * @param {Event} event - Mouse/blur event
 */
function handleCitationLeave(event) {
    const citationId = event.target.dataset.citationId;
    const referenceCard = document.querySelector(
        `.reference-card[data-citation-id="${citationId}"]`
    );

    if (referenceCard) {
        referenceCard.classList.remove('highlighted');
    }

    // Reset citation marker style
    event.target.style.background = 'var(--color-primary-light)';
    event.target.style.color = 'var(--color-primary-base)';
}

/**
 * Handle keyboard navigation on citation
 * @param {Event} event - Keyboard event
 */
function handleCitationKeydown(event) {
    if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        // Navigate to reference or toggle highlight
        const citationId = event.target.dataset.citationId;
        const referenceCard = document.querySelector(
            `.reference-card[data-citation-id="${citationId}"]`
        );
        if (referenceCard) {
            referenceCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
}

/**
 * Scroll element into view if needed
 * @param {HTMLElement} element - Element to scroll
 */
function scrollIntoViewIfNeeded(element) {
    const rect = element.getBoundingClientRect();
    const isVisible = (
        rect.top >= 0 &&
        rect.bottom <= window.innerHeight
    );

    if (!isVisible) {
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'nearest'
        });
    }
}

// Add CSS styles dynamically
const style = document.createElement('style');
style.textContent = `
    .answer-display {
        font-family: var(--font-serif, Georgia, serif);
        line-height: 1.8;
        color: var(--color-text-primary);
    }

    .answer-sentence {
        margin-bottom: var(--space-4);
        font-size: var(--font-size-lg, 1.125rem);
    }

    .citation-marker:hover,
    .citation-marker:focus {
        outline: 2px solid var(--color-primary-base);
        outline-offset: 2px;
    }

    .answer-sentence.highlighted-sentence {
        background: var(--color-primary-light);
        padding: var(--space-2);
        margin-left: calc(var(--space-2) * -1);
        margin-right: calc(var(--space-2) * -1);
        border-radius: var(--radius-sm, 0.25rem);
        transition: all var(--trans-base, 200ms);
    }
`;
document.head.appendChild(style);

// Export for use in other modules
export { handleCitationHover, handleCitationLeave };

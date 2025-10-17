# Frontend Components Interface Contract

**Providers:**
- Agent 6 - Research Page Structure
- Agent 7 - Answer Display Component
- Agent 8 - Reference Card Component
- Agent 9 - API Integration & Highlighting

**Consumer:** End Users
**Files:** `src/frontend/research.html`, `src/frontend/answer-display.js`, `src/frontend/reference-card.js`, `src/frontend/research-controller.js`
**Status:** Wave 3 & 4 Frontend Layer
**Version:** 1.0
**Last Updated:** 2025-10-17

---

## Overview

The frontend components create an interactive research page where users submit queries, view AI-generated answers with inline citations, and explore source documents through bidirectional highlighting.

---

## Component Architecture

### File Structure

```
src/frontend/
├── research.html              # Page structure (Agent 6)
├── research-controller.js     # API integration, state management (Agent 9)
├── answer-display.js          # Answer panel with citations (Agent 7)
├── reference-card.js          # Reference panel cards (Agent 8)
└── assets.js                  # Shared assets (existing)
```

---

## 1. Research Page Structure (Agent 6)

**File:** `src/frontend/research.html`

### HTML Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Research - DocuSearch</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body class="kraft-theme">
    <!-- Header -->
    <header class="research-header">
        <div class="header-content">
            <h1>Research</h1>
            <div class="header-actions">
                <button id="theme-toggle" class="theme-toggle" aria-label="Toggle theme">
                    <!-- SVG icon -->
                </button>
            </div>
        </div>
    </header>

    <!-- Query Input -->
    <section class="query-section">
        <form id="research-form" class="query-form">
            <div class="input-group">
                <input
                    type="text"
                    id="query-input"
                    class="query-input"
                    placeholder="Ask a question about your documents..."
                    aria-label="Research question"
                    required
                    minlength="3"
                    maxlength="500"
                />
                <button type="submit" class="ask-button" aria-label="Submit question">
                    Ask
                </button>
            </div>
        </form>
    </section>

    <!-- Main Content (Two-Panel Layout) -->
    <main class="research-main">
        <!-- Left Panel: Answer -->
        <section class="answer-panel" aria-label="Answer">
            <div id="answer-container" class="answer-container">
                <!-- Empty state -->
                <div id="empty-state" class="empty-state">
                    <h2>Start your research</h2>
                    <p>Ask a question about your documents to get started.</p>
                </div>

                <!-- Loading state -->
                <div id="loading-state" class="loading-state hidden">
                    <div class="loading-spinner"></div>
                    <p>Researching your question...</p>
                </div>

                <!-- Answer display (populated by answer-display.js) -->
                <div id="answer-display" class="answer-display hidden">
                    <!-- Dynamic content -->
                </div>

                <!-- Error state -->
                <div id="error-state" class="error-state hidden">
                    <p class="error-message"></p>
                    <button id="retry-button" class="retry-button">Try Again</button>
                </div>
            </div>
        </section>

        <!-- Right Panel: References -->
        <aside class="references-panel" aria-label="References">
            <div class="references-header">
                <h2>References</h2>
                <div class="view-toggle-group" role="group" aria-label="View mode">
                    <button
                        id="detailed-view-btn"
                        class="view-toggle active"
                        data-view="detailed"
                        aria-pressed="true"
                    >
                        Detailed
                    </button>
                    <button
                        id="simple-view-btn"
                        class="view-toggle"
                        data-view="simple"
                        aria-pressed="false"
                    >
                        Simple
                    </button>
                </div>
            </div>

            <div id="references-container" class="references-container">
                <!-- Empty state -->
                <div id="references-empty" class="references-empty">
                    <p>References will appear here after submitting a query.</p>
                </div>

                <!-- Reference cards (populated by reference-card.js) -->
                <div id="references-list" class="references-list hidden">
                    <!-- Dynamic content -->
                </div>
            </div>
        </aside>
    </main>

    <!-- Scripts -->
    <script type="module" src="assets.js"></script>
    <script type="module" src="answer-display.js"></script>
    <script type="module" src="reference-card.js"></script>
    <script type="module" src="research-controller.js"></script>
</body>
</html>
```

### CSS Structure (Kraft Paper Theme)

```css
/* Research Page Layout */
.research-header {
    position: sticky;
    top: 0;
    z-index: var(--z-sticky);
    background: var(--color-bg-primary);
    border-bottom: 1px solid var(--color-border);
    padding: var(--space-4) var(--space-6);
}

.query-section {
    padding: var(--space-6);
    background: var(--color-bg-secondary);
}

.query-input {
    width: 100%;
    max-width: 800px;
    padding: var(--space-3) var(--space-4);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    font-size: var(--font-size-base);
}

.research-main {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-6);
    padding: var(--space-6);
    min-height: calc(100vh - 200px);
}

/* Answer Panel */
.answer-panel {
    background: var(--color-bg-primary);
    border-radius: var(--radius-lg);
    padding: var(--space-6);
    box-shadow: var(--shadow-md);
}

.answer-display {
    font-family: var(--font-serif);
    line-height: var(--line-height);
    color: var(--color-text-primary);
}

/* References Panel */
.references-panel {
    background: var(--color-bg-primary);
    border-radius: var(--radius-lg);
    padding: var(--space-6);
    box-shadow: var(--shadow-md);
}

.view-toggle-group {
    display: flex;
    gap: var(--space-2);
}

.view-toggle {
    padding: var(--space-2) var(--space-4);
    border: 1px solid var(--color-border);
    background: transparent;
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all var(--trans-base);
}

.view-toggle.active {
    background: var(--color-primary-base);
    color: var(--color-bg-primary);
    border-color: var(--color-primary-base);
}

/* States */
.hidden {
    display: none !important;
}

.loading-spinner {
    width: 40px;
    height: 40px;
    border: 3px solid var(--color-border);
    border-top-color: var(--color-primary-base);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Responsive */
@media (max-width: 768px) {
    .research-main {
        grid-template-columns: 1fr;
    }
}
```

---

## 2. Answer Display Component (Agent 7)

**File:** `src/frontend/answer-display.js`

### Module Interface

```javascript
/**
 * Renders AI-generated answer with inline citation markers
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

    // Split answer into sentences
    const sentences = splitIntoSentences(data.answer, data.citations);

    sentences.forEach((sentence, index) => {
        const sentenceEl = createSentenceElement(sentence, index);
        container.appendChild(sentenceEl);
    });

    // Add event listeners for highlighting
    attachCitationListeners(container);
}

/**
 * Split answer text into sentences with citations
 * @param {string} text - Full answer text
 * @param {Array} citations - Citation metadata
 * @returns {Array} Array of sentence objects
 */
function splitIntoSentences(text, citations) {
    // Logic to split text and associate citations
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
    const parts = splitByCitations(sentence.text);

    parts.forEach(part => {
        if (part.type === 'text') {
            sentenceEl.appendChild(document.createTextNode(part.content));
        } else if (part.type === 'citation') {
            const citationEl = createCitationMarker(part.citation_id);
            sentenceEl.appendChild(citationEl);
        }
    });

    return sentenceEl;
}

/**
 * Create citation marker element
 * @param {number} citationId - Citation number
 * @returns {HTMLElement} Citation marker
 */
function createCitationMarker(citationId) {
    const marker = document.createElement('span');
    marker.className = 'citation-marker';
    marker.dataset.citationId = citationId;
    marker.textContent = `[${citationId}]`;
    marker.setAttribute('role', 'button');
    marker.setAttribute('tabindex', '0');
    marker.setAttribute('aria-label', `Citation ${citationId}`);

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
        citation.addEventListener('keydown', handleCitationKeydown);
    });
}

/**
 * Handle citation hover (highlight reference)
 * @param {Event} event - Mouse event
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
}

/**
 * Handle citation leave (remove highlight)
 * @param {Event} event - Mouse event
 */
function handleCitationLeave(event) {
    const citationId = event.target.dataset.citationId;
    const referenceCard = document.querySelector(
        `.reference-card[data-citation-id="${citationId}"]`
    );

    if (referenceCard) {
        referenceCard.classList.remove('highlighted');
    }
}

/**
 * Handle keyboard navigation on citation
 * @param {Event} event - Keyboard event
 */
function handleCitationKeydown(event) {
    if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        // Navigate to reference or toggle highlight
        handleCitationHover(event);
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
```

### CSS (answer-display.js styles)

```css
.answer-sentence {
    margin-bottom: var(--space-4);
    font-size: var(--font-size-lg);
    line-height: 1.8;
}

.citation-marker {
    display: inline-block;
    padding: 0 var(--space-1);
    margin: 0 var(--space-1);
    background: var(--color-primary-light);
    color: var(--color-primary-base);
    border-radius: var(--radius-sm);
    font-size: var(--font-size-sm);
    font-weight: 600;
    cursor: pointer;
    transition: all var(--trans-fast);
    vertical-align: super;
    font-family: var(--font-sans);
}

.citation-marker:hover,
.citation-marker:focus {
    background: var(--color-primary-base);
    color: var(--color-bg-primary);
    outline: 2px solid var(--color-primary-base);
    outline-offset: 2px;
}

.citation-marker.highlighted {
    background: var(--color-primary-hover);
    color: var(--color-bg-primary);
}
```

---

## 3. Reference Card Component (Agent 8)

**File:** `src/frontend/reference-card.js`

### Module Interface

```javascript
/**
 * Renders reference cards for source documents
 */

/**
 * Render reference cards
 * @param {Array} sources - Source documents from API
 * @param {HTMLElement} container - Container element
 * @param {string} variant - 'detailed' or 'simple'
 */
export function renderReferenceCards(sources, container, variant = 'detailed') {
    container.innerHTML = '';

    sources.forEach((source, index) => {
        const card = createReferenceCard(source, index + 1, variant);
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

    if (variant === 'detailed') {
        card.innerHTML = `
            <div class="reference-card__number">${citationNum}</div>
            ${source.thumbnail_path ? `
                <img
                    src="${source.thumbnail_path}"
                    alt="Thumbnail of ${source.filename}"
                    class="reference-card__thumbnail"
                    loading="lazy"
                />
            ` : `
                <div class="reference-card__thumbnail-placeholder">
                    ${getFileIcon(source.extension)}
                </div>
            `}
            <div class="reference-card__content">
                <div class="reference-card__badge">
                    ${source.extension.toUpperCase()}
                </div>
                <div class="reference-card__filename" title="${source.filename}">
                    ${source.filename}
                </div>
                <div class="reference-card__meta">
                    Page ${source.page} • ${formatDate(source.date_added)}
                </div>
            </div>
            <a
                href="/details.html?filename=${encodeURIComponent(source.filename)}"
                class="reference-card__details-btn"
                aria-label="View details for ${source.filename}"
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
            </div>
            <a
                href="/details.html?filename=${encodeURIComponent(source.filename)}"
                class="reference-card__details-btn-simple"
                aria-label="View details"
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
    // Reuse from existing assets.js or document-card.js
    const icons = {
        pdf: '<svg>...</svg>',
        docx: '<svg>...</svg>',
        pptx: '<svg>...</svg>',
        // ... etc
    };

    return icons[extension.toLowerCase()] || icons.default;
}

/**
 * Format date for display
 * @param {string} isoDate - ISO date string
 * @returns {string} Formatted date
 */
function formatDate(isoDate) {
    const date = new Date(isoDate);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
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
    const citationId = event.currentTarget.dataset.citationId;
    const citations = document.querySelectorAll(
        `.citation-marker[data-citation-id="${citationId}"]`
    );

    citations.forEach(citation => {
        citation.classList.add('highlighted');
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
    const citationId = event.currentTarget.dataset.citationId;
    const citations = document.querySelectorAll(
        `.citation-marker[data-citation-id="${citationId}"]`
    );

    citations.forEach(citation => {
        citation.classList.remove('highlighted');
        const sentence = citation.closest('.answer-sentence');
        if (sentence) {
            sentence.classList.remove('highlighted-sentence');
        }
    });
}
```

### CSS (reference-card.js styles)

```css
.reference-card {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-3);
    background: var(--color-bg-secondary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    margin-bottom: var(--space-3);
    transition: all var(--trans-base);
}

.reference-card:hover {
    background: var(--color-bg-primary);
    box-shadow: var(--shadow-md);
}

.reference-card.highlighted {
    background: var(--color-primary-light);
    border-color: var(--color-primary-base);
    box-shadow: var(--shadow-lg);
}

.reference-card__number {
    flex-shrink: 0;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--color-primary-base);
    color: var(--color-bg-primary);
    border-radius: var(--radius-round);
    font-weight: 600;
    font-size: var(--font-size-sm);
}

.reference-card__thumbnail {
    flex-shrink: 0;
    max-height: 64px;
    width: auto;
    object-fit: contain;
    border-radius: var(--radius-sm);
}

.reference-card__thumbnail-placeholder {
    flex-shrink: 0;
    width: 64px;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--color-bg-tertiary);
    border-radius: var(--radius-sm);
}

.reference-card__content {
    flex: 1;
    min-width: 0;
}

.reference-card__badge {
    display: inline-block;
    padding: var(--space-1) var(--space-2);
    background: var(--color-primary-light);
    color: var(--color-primary-base);
    border-radius: var(--radius-sm);
    font-size: var(--font-size-xs);
    font-weight: 600;
    margin-bottom: var(--space-1);
}

.reference-card__filename {
    font-weight: 500;
    color: var(--color-text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.reference-card__meta {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    margin-top: var(--space-1);
}

.reference-card__details-btn {
    flex-shrink: 0;
    padding: var(--space-2) var(--space-4);
    background: var(--color-primary-base);
    color: var(--color-bg-primary);
    border-radius: var(--radius-md);
    text-decoration: none;
    font-size: var(--font-size-sm);
    font-weight: 600;
    transition: all var(--trans-fast);
}

.reference-card__details-btn:hover {
    background: var(--color-primary-hover);
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
    font-size: var(--font-size-base);
}

/* Highlighted sentence */
.highlighted-sentence {
    background: var(--color-primary-light);
    padding: var(--space-2);
    margin: 0 calc(var(--space-2) * -1);
    border-radius: var(--radius-sm);
    transition: all var(--trans-base);
}
```

---

## 4. Research Controller (Agent 9)

**File:** `src/frontend/research-controller.js`

### Module Interface

```javascript
/**
 * Main controller for research page - API integration and state management
 */

import { renderAnswer } from './answer-display.js';
import { renderReferenceCards } from './reference-card.js';

// State
let currentView = 'detailed';
let currentResponse = null;

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    initializeResearchPage();
});

/**
 * Initialize research page
 */
function initializeResearchPage() {
    // Attach event listeners
    const form = document.getElementById('research-form');
    form.addEventListener('submit', handleFormSubmit);

    const detailedBtn = document.getElementById('detailed-view-btn');
    const simpleBtn = document.getElementById('simple-view-btn');

    detailedBtn.addEventListener('click', () => switchView('detailed'));
    simpleBtn.addEventListener('click', () => switchView('simple'));

    const retryBtn = document.getElementById('retry-button');
    retryBtn.addEventListener('click', handleRetry);
}

/**
 * Handle form submission
 * @param {Event} event - Submit event
 */
async function handleFormSubmit(event) {
    event.preventDefault();

    const queryInput = document.getElementById('query-input');
    const query = queryInput.value.trim();

    if (!query) return;

    // Show loading state
    showLoadingState();

    try {
        const response = await submitResearchQuery(query);
        currentResponse = response;

        // Render answer and references
        renderResearchResults(response);

        // Show success state
        showSuccessState();

    } catch (error) {
        console.error('Research query failed:', error);
        showErrorState(error.message);
    }
}

/**
 * Submit research query to API
 * @param {string} query - User's question
 * @returns {Promise<Object>} API response
 */
async function submitResearchQuery(query) {
    const response = await fetch('/api/research/ask', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query: query,
            num_sources: 10,
            search_mode: 'hybrid'
        })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to get research answer');
    }

    return await response.json();
}

/**
 * Render research results
 * @param {Object} response - API response
 */
function renderResearchResults(response) {
    // Render answer
    const answerDisplay = document.getElementById('answer-display');
    renderAnswer(response, answerDisplay);

    // Render references
    const referencesList = document.getElementById('references-list');
    renderReferenceCards(response.sources, referencesList, currentView);
}

/**
 * Switch view mode (detailed/simple)
 * @param {string} view - 'detailed' or 'simple'
 */
function switchView(view) {
    currentView = view;

    // Update button states
    document.querySelectorAll('.view-toggle').forEach(btn => {
        const isActive = btn.dataset.view === view;
        btn.classList.toggle('active', isActive);
        btn.setAttribute('aria-pressed', isActive);
    });

    // Re-render references if we have results
    if (currentResponse) {
        const referencesList = document.getElementById('references-list');
        renderReferenceCards(currentResponse.sources, referencesList, view);
    }
}

/**
 * Show loading state
 */
function showLoadingState() {
    document.getElementById('empty-state').classList.add('hidden');
    document.getElementById('answer-display').classList.add('hidden');
    document.getElementById('error-state').classList.add('hidden');
    document.getElementById('loading-state').classList.remove('hidden');

    document.getElementById('references-empty').classList.add('hidden');
    document.getElementById('references-list').classList.add('hidden');
}

/**
 * Show success state
 */
function showSuccessState() {
    document.getElementById('empty-state').classList.add('hidden');
    document.getElementById('loading-state').classList.add('hidden');
    document.getElementById('error-state').classList.add('hidden');
    document.getElementById('answer-display').classList.remove('hidden');

    document.getElementById('references-empty').classList.add('hidden');
    document.getElementById('references-list').classList.remove('hidden');
}

/**
 * Show error state
 * @param {string} message - Error message
 */
function showErrorState(message) {
    document.getElementById('empty-state').classList.add('hidden');
    document.getElementById('loading-state').classList.add('hidden');
    document.getElementById('answer-display').classList.add('hidden');
    document.getElementById('error-state').classList.remove('hidden');

    const errorMessage = document.querySelector('.error-message');
    errorMessage.textContent = message || 'An error occurred. Please try again.';
}

/**
 * Handle retry button click
 */
function handleRetry() {
    const queryInput = document.getElementById('query-input');
    const form = document.getElementById('research-form');
    form.dispatchEvent(new Event('submit'));
}
```

---

## Integration Contract Summary

### Data Flow

```
User Input
    ↓
research-controller.js (POST /api/research/ask)
    ↓
API Response: { answer, citations, citation_map, sources }
    ↓
answer-display.js (render answer with citations)
    +
reference-card.js (render reference cards)
    ↓
Bidirectional Highlighting Active
```

### Event Communication

| Event Source | Event | Handler | Action |
|--------------|-------|---------|--------|
| Citation marker hover | `mouseenter` | answer-display.js | Highlight reference card |
| Citation marker leave | `mouseleave` | answer-display.js | Remove highlight |
| Reference card hover | `mouseenter` | reference-card.js | Highlight citations + sentence |
| Reference card leave | `mouseleave` | reference-card.js | Remove highlights |
| View toggle click | `click` | research-controller.js | Re-render references |
| Form submit | `submit` | research-controller.js | API call + render results |

---

## Validation Gates (Wave 3 & 4)

### Wave 3 (Components)

- [ ] Research page loads without errors
- [ ] Query input validates correctly
- [ ] Empty/loading/success/error states work
- [ ] Answer displays with citations
- [ ] Reference cards render (detailed & simple)
- [ ] View toggle switches modes

### Wave 4 (Integration & Highlighting)

- [ ] API integration successful
- [ ] Bidirectional highlighting works
- [ ] Hover on citation highlights reference
- [ ] Hover on reference highlights citations
- [ ] Details button navigates correctly
- [ ] Keyboard navigation functional
- [ ] Screen reader accessible
- [ ] Mobile responsive

---

## Notes

- Reuses Kraft Paper theme from existing frontend
- Leverages existing `document-card.js` patterns for thumbnails
- Details button links to existing `/details.html` page
- Max-height: 64px for thumbnails (from planning)
- Accessibility: ARIA labels, keyboard navigation, focus indicators
- Performance: Lazy loading thumbnails, smooth scrolling

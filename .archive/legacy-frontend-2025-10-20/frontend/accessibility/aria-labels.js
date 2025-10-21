/**
 * ARIA Labels Module
 *
 * Adds semantic labels and roles for screen readers:
 * - Bboxes: role="button" with descriptive labels
 * - Chunks: role="article" with section context
 * - Overlay: role="img" with description
 * - Indicators: role="status" for dynamic content
 *
 * WCAG 2.1 AA Compliant - Screen reader accessible
 */

/**
 * Add ARIA labels to bounding boxes
 * @param {SVGElement} bboxElement - SVG rect element
 * @param {Object} bbox - Bbox data
 * @param {number} bbox.page - Page number
 * @param {string} bbox.element_type - Element type (section, table, etc.)
 * @param {string} bbox.parent_heading - Parent heading text
 * @param {number} index - Bbox index in list
 * @param {number} total - Total number of bboxes
 */
export function labelBbox(bboxElement, bbox, index = null, total = null) {
    // Format descriptive label
    const elementType = formatElementType(bbox.element_type);
    const heading = bbox.parent_heading || 'Unlabeled section';
    const page = bbox.page;

    let label = `${elementType}: ${heading}, Page ${page}`;

    if (index !== null && total !== null) {
        label += ` (${index + 1} of ${total})`;
    }

    // Set ARIA attributes
    bboxElement.setAttribute('aria-label', label);
    bboxElement.setAttribute('role', 'button');
    bboxElement.setAttribute('tabindex', '0');
    bboxElement.setAttribute('aria-pressed', 'false');

    // Add description for complex elements
    if (bbox.element_type === 'table' || bbox.element_type === 'figure') {
        const description = generateBboxDescription(bbox);
        bboxElement.setAttribute('aria-describedby', `bbox-desc-${bbox.id || index}`);

        // Create description element (hidden)
        createDescription(`bbox-desc-${bbox.id || index}`, description);
    }
}

/**
 * Add ARIA labels to chunk divs
 * @param {HTMLElement} chunkElement - Chunk div element
 * @param {Object} chunk - Chunk data
 * @param {string} chunk.section_path - Section hierarchy
 * @param {number} chunk.page - Page number
 * @param {number} index - Chunk index in list
 * @param {number} total - Total number of chunks
 */
export function labelChunk(chunkElement, chunk, index = null, total = null) {
    // Format descriptive label
    const section = chunk.section_path || 'Document content';
    const page = chunk.page;

    let label = `Chunk from ${section}, Page ${page}`;

    if (index !== null && total !== null) {
        label += ` (${index + 1} of ${total})`;
    }

    // Set ARIA attributes
    chunkElement.setAttribute('aria-label', label);
    chunkElement.setAttribute('role', 'article');
    chunkElement.setAttribute('tabindex', '0');

    // Add current state attribute
    chunkElement.setAttribute('aria-current', 'false');
}

/**
 * Add ARIA label to overlay container
 * @param {HTMLElement} overlayContainer - Overlay container element
 * @param {string} documentName - Document name
 * @param {number} totalBboxes - Total number of bboxes
 */
export function labelOverlay(overlayContainer, documentName, totalBboxes) {
    const label = `Document structure overlay for ${documentName} with ${totalBboxes} highlighted regions`;

    overlayContainer.setAttribute('role', 'img');
    overlayContainer.setAttribute('aria-label', label);
    overlayContainer.setAttribute('aria-describedby', 'overlay-description');

    // Create detailed description
    const description = `Interactive overlay showing ${totalBboxes} document regions.
        Use Tab to navigate between regions, Enter or Space to activate,
        arrow keys to move between regions, and Escape to clear highlights.`;

    createDescription('overlay-description', description);
}

/**
 * Add ARIA label to chunk context badge
 * @param {HTMLElement} badgeElement - Badge element
 * @param {Object} context - Context information
 * @param {string} context.heading - Section heading
 * @param {number} context.page - Page number
 * @param {string} context.chunkId - Chunk ID
 */
export function labelContextBadge(badgeElement, context) {
    const label = `Context: ${context.heading}, Page ${context.page}. Click to navigate to chunk.`;

    badgeElement.setAttribute('aria-label', label);
    badgeElement.setAttribute('role', 'status');
    badgeElement.setAttribute('aria-live', 'polite');
}

/**
 * Add ARIA label to citation link
 * @param {HTMLElement} citationElement - Citation link element
 * @param {number} citationNumber - Citation number
 * @param {string} documentName - Referenced document name
 * @param {number} page - Page number
 */
export function labelCitation(citationElement, citationNumber, documentName, page) {
    const label = `Citation ${citationNumber}: Reference to ${documentName}, Page ${page}. Click to view document.`;

    citationElement.setAttribute('aria-label', label);
    citationElement.setAttribute('role', 'link');
    citationElement.setAttribute('aria-describedby', `citation-${citationNumber}-desc`);

    // Create description with full context
    const description = `This citation references ${documentName} at page ${page}.
        Clicking will navigate to the document viewer with bidirectional highlighting.`;

    createDescription(`citation-${citationNumber}-desc`, description);
}

/**
 * Update ARIA attributes for highlight state
 * @param {HTMLElement} element - Element to update
 * @param {boolean} isHighlighted - Whether element is highlighted
 * @param {boolean} isPermanent - Whether highlight is permanent
 */
export function updateHighlightState(element, isHighlighted, isPermanent = false) {
    if (element.hasAttribute('role') && element.getAttribute('role') === 'button') {
        // For bbox buttons
        element.setAttribute('aria-pressed', isHighlighted ? 'true' : 'false');
    }

    if (element.hasAttribute('role') && element.getAttribute('role') === 'article') {
        // For chunk articles
        element.setAttribute('aria-current', isHighlighted ? 'true' : 'false');
    }

    // Add permanent state indicator
    if (isPermanent) {
        element.setAttribute('aria-label', element.getAttribute('aria-label') + ' (Active)');
    } else {
        // Remove " (Active)" suffix if present
        const currentLabel = element.getAttribute('aria-label');
        if (currentLabel && currentLabel.endsWith(' (Active)')) {
            element.setAttribute('aria-label', currentLabel.replace(' (Active)', ''));
        }
    }
}

/**
 * Format element type for display
 * @param {string} elementType - Raw element type
 * @returns {string} Formatted element type
 */
function formatElementType(elementType) {
    const typeMap = {
        'section': 'Section',
        'table': 'Table',
        'figure': 'Figure',
        'list': 'List',
        'paragraph': 'Paragraph',
        'heading': 'Heading',
        'caption': 'Caption',
        'code': 'Code block'
    };

    return typeMap[elementType] || elementType.charAt(0).toUpperCase() + elementType.slice(1);
}

/**
 * Generate detailed description for bbox
 * @param {Object} bbox - Bbox data
 * @returns {string} Description text
 */
function generateBboxDescription(bbox) {
    let description = `This is a ${formatElementType(bbox.element_type)}`;

    if (bbox.parent_heading) {
        description += ` within the section "${bbox.parent_heading}"`;
    }

    description += ` on page ${bbox.page}.`;

    if (bbox.element_type === 'table') {
        description += ' Contains tabular data.';
    } else if (bbox.element_type === 'figure') {
        description += ' Contains an image or diagram.';
    }

    description += ' Click or press Enter to highlight the corresponding text.';

    return description;
}

/**
 * Create hidden description element
 * @param {string} id - Element ID
 * @param {string} text - Description text
 */
function createDescription(id, text) {
    // Check if already exists
    let descElement = document.getElementById(id);

    if (!descElement) {
        descElement = document.createElement('div');
        descElement.id = id;
        descElement.className = 'sr-only';
        document.body.appendChild(descElement);
    }

    descElement.textContent = text;
}

/**
 * Label navigation controls
 * @param {HTMLElement} prevButton - Previous button
 * @param {HTMLElement} nextButton - Next button
 * @param {string} context - Navigation context (e.g., "chunk", "page")
 */
export function labelNavigationControls(prevButton, nextButton, context = 'item') {
    if (prevButton) {
        prevButton.setAttribute('aria-label', `Previous ${context}`);
        prevButton.setAttribute('role', 'button');
    }

    if (nextButton) {
        nextButton.setAttribute('aria-label', `Next ${context}`);
        nextButton.setAttribute('role', 'button');
    }
}

/**
 * Label search form
 * @param {HTMLFormElement} formElement - Search form
 * @param {HTMLInputElement} inputElement - Search input
 * @param {HTMLButtonElement} submitButton - Submit button
 */
export function labelSearchForm(formElement, inputElement, submitButton) {
    formElement.setAttribute('role', 'search');
    formElement.setAttribute('aria-label', 'Research query search');

    inputElement.setAttribute('aria-label', 'Enter research question');
    inputElement.setAttribute('aria-describedby', 'search-hint');

    // Create search hint
    const hint = 'Ask a question about your documents. Results will include citations.';
    createDescription('search-hint', hint);

    if (submitButton) {
        submitButton.setAttribute('aria-label', 'Submit research query');
    }
}

/**
 * Label modal dialog
 * @param {HTMLElement} modalElement - Modal element
 * @param {string} title - Modal title
 * @param {string} description - Modal description
 */
export function labelModal(modalElement, title, description) {
    modalElement.setAttribute('role', 'dialog');
    modalElement.setAttribute('aria-modal', 'true');
    modalElement.setAttribute('aria-labelledby', 'modal-title');
    modalElement.setAttribute('aria-describedby', 'modal-description');

    // Create title element if not exists
    let titleElement = modalElement.querySelector('#modal-title');
    if (!titleElement) {
        titleElement = document.createElement('h2');
        titleElement.id = 'modal-title';
        titleElement.className = 'sr-only';
        modalElement.insertBefore(titleElement, modalElement.firstChild);
    }
    titleElement.textContent = title;

    // Create description element if provided
    if (description) {
        let descElement = modalElement.querySelector('#modal-description');
        if (!descElement) {
            descElement = document.createElement('p');
            descElement.id = 'modal-description';
            descElement.className = 'sr-only';
            modalElement.insertBefore(descElement, titleElement.nextSibling);
        }
        descElement.textContent = description;
    }
}

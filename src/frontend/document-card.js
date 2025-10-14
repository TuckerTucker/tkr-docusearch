/**
 * DocumentCard Component
 *
 * Creates document information cards with thumbnail, metadata badge, and details button.
 * Supports both document (tall) and audio (square) variants.
 * Three states: completed, loading, processing
 *
 * Provider: card-agent (Wave 1)
 * Contract: integration-contracts/document-card.contract.md
 */

/**
 * Inline SVG icons (replaces Lucide dependency)
 */
const SVGIcons = {
  document: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><line x1="10" y1="9" x2="8" y2="9"></line></svg>`,

  audio: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path><path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path></svg>`,

  video: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>`
};

/**
 * Icon names for different file types
 */
export const Icons = {
  document: 'file-text',
  audio: 'volume-2',
  video: 'video'
};

/**
 * File type to icon mapping
 */
const fileTypeIcons = {
  // Documents
  pdf: 'document',
  docx: 'document',
  doc: 'document',
  pptx: 'document',
  ppt: 'document',
  xlsx: 'document',
  xls: 'document',
  txt: 'document',
  md: 'document',
  html: 'document',

  // Audio
  mp3: 'audio',
  wav: 'audio',
  flac: 'audio',
  aac: 'audio',
  ogg: 'audio',
  m4a: 'audio',

  // Video
  mp4: 'video',
  avi: 'video',
  mov: 'video',
  wmv: 'video',
  webm: 'video'
};

/**
 * File type to variant mapping
 */
const fileTypeVariants = {
  pdf: 'document',
  docx: 'document',
  doc: 'document',
  pptx: 'document',
  ppt: 'document',
  xlsx: 'document',
  xls: 'document',
  txt: 'document',
  md: 'document',
  html: 'document',

  mp3: 'audio',
  wav: 'audio',
  flac: 'audio',
  aac: 'audio',
  ogg: 'audio',
  m4a: 'audio',

  mp4: 'audio', // Using audio variant for video (square)
  avi: 'audio',
  mov: 'audio',
  wmv: 'audio',
  webm: 'audio'
};

/**
 * Format date for display
 * @param {string|Date} date - Date to format
 * @returns {string} Formatted date string
 */
function formatDate(date) {
  const d = typeof date === 'string' ? new Date(date) : date;
  const options = { month: 'long', day: 'numeric', year: 'numeric' };
  return d.toLocaleDateString('en-US', options);
}

/**
 * Get file extension from filename
 * @param {string} filename - Filename
 * @returns {string} File extension in lowercase
 */
function getFileExtension(filename) {
  const parts = filename.split('.');
  return parts.length > 1 ? parts.pop().toLowerCase() : '';
}

/**
 * Get formatted filename without extension
 * @param {string} filename - Full filename
 * @returns {string} Formatted filename without extension
 */
function getFilenameWithoutExtension(filename) {
  // Remove file extension
  const parts = filename.split('.');
  if (parts.length > 1) {
    parts.pop();
  }
  let name = parts.join('.');

  // Replace underscores with spaces
  name = name.replace(/_/g, ' ');

  // Remove timestamp suffixes (e.g., " 1750130928")
  name = name.replace(/\s+\d{10,}$/, '');

  // Clean up multiple spaces
  name = name.replace(/\s+/g, ' ').trim();

  return name;
}

/**
 * Create a DocumentCard element
 *
 * @param {Object} options - Card configuration
 * @param {string} options.filename - Full filename with extension
 * @param {string} options.thumbnailUrl - URL to thumbnail image
 * @param {string|Date} options.dateAdded - Date the document was added
 * @param {string} options.detailsUrl - URL for the details button
 * @param {string} [options.variant] - 'document' or 'audio' (auto-detected from extension if not provided)
 * @param {string} [options.placeholderColor] - Background color for missing thumbnails
 * @param {string} [options.state] - Card state: 'completed', 'loading', or 'processing'
 * @param {Object} [options.processingStatus] - Status info for processing state
 * @param {string} [options.processingStatus.stage] - Current processing stage
 * @param {number} [options.processingStatus.progress] - Progress 0.0-1.0
 * @returns {HTMLElement} DocumentCard element
 */
export function createDocumentCard(options) {
  const {
    filename,
    thumbnailUrl,
    dateAdded,
    detailsUrl,
    variant: providedVariant,
    placeholderColor = '#E9E9E9',
    state = 'completed',
    processingStatus = null,
    errorMessage = null
  } = options;

  // Get file extension and determine variant
  const extension = getFileExtension(filename);
  const variant = providedVariant || fileTypeVariants[extension] || 'document';
  const iconType = fileTypeIcons[extension] || 'document';
  const title = getFilenameWithoutExtension(filename);
  const formattedDate = typeof dateAdded === 'string' ? dateAdded : formatDate(dateAdded);

  // Create card container
  const card = document.createElement('article');
  const stateClass = state === 'completed' ? '' : `document-card--${state}`;
  card.className = `document-card document-card--${variant} ${stateClass}`.trim();
  card.setAttribute('role', 'article');
  card.setAttribute('aria-label', `Document: ${filename}`);

  // Left column (thumbnail + badge)
  const left = document.createElement('div');
  left.className = 'document-card__left';

  // Thumbnail
  const thumbnail = document.createElement('img');
  thumbnail.className = 'document-card__thumbnail';
  thumbnail.src = thumbnailUrl || '';
  thumbnail.alt = `Thumbnail for ${filename}`;
  thumbnail.loading = 'lazy';
  thumbnail.style.backgroundColor = placeholderColor;

  // Handle missing images
  thumbnail.onerror = function() {
    this.style.backgroundColor = placeholderColor;
    this.alt = `No preview available for ${filename}`;
  };

  // Badge
  const badge = document.createElement('div');
  badge.className = 'document-card__badge';
  badge.setAttribute('aria-label', `Added ${formattedDate}, File type: ${extension.toUpperCase()}`);

  // Filetype container (icon + extension)
  const badgeFiletype = document.createElement('div');
  badgeFiletype.className = 'document-card__badge-filetype';

  // Icon container with dark background
  const badgeIconContainer = document.createElement('div');
  badgeIconContainer.className = 'document-card__badge-icon-container';

  // Create inline SVG icon element
  const badgeIcon = document.createElement('div');
  badgeIcon.className = 'document-card__badge-icon';
  badgeIcon.innerHTML = SVGIcons[iconType];

  const badgeExtension = document.createElement('div');
  badgeExtension.className = 'document-card__badge-extension';
  badgeExtension.textContent = extension.toUpperCase();

  badgeIconContainer.appendChild(badgeIcon);
  badgeIconContainer.appendChild(badgeExtension);

  badgeFiletype.appendChild(badgeIconContainer);

  const badgeDate = document.createElement('div');
  badgeDate.className = 'document-card__badge-date';
  badgeDate.innerHTML = `Added<br>${formattedDate}`;

  badge.appendChild(badgeFiletype);
  badge.appendChild(badgeDate);

  left.appendChild(thumbnail);
  left.appendChild(badge);

  // Right column (title + button OR processing status)
  const right = document.createElement('div');
  right.className = 'document-card__right';

  // Only show title for completed state (not processing or loading)
  if (state === 'completed') {
    const titleEl = document.createElement('h3');
    titleEl.className = 'document-card__title';
    titleEl.textContent = title;
    right.appendChild(titleEl);
  }

  // State-specific content
  if (state === 'loading') {
    // Loading state: spinner and loading message
    const loadingInfo = document.createElement('div');
    loadingInfo.className = 'document-card__processing-info';

    const statusContainer = document.createElement('div');
    statusContainer.className = 'document-card__status';

    const spinner = document.createElement('div');
    spinner.className = 'document-card__spinner';
    spinner.setAttribute('role', 'status');
    spinner.setAttribute('aria-label', 'Loading');

    const statusLabel = document.createElement('div');
    statusLabel.className = 'document-card__status-label';
    statusLabel.textContent = 'Loading document...';

    statusContainer.appendChild(spinner);
    statusContainer.appendChild(statusLabel);
    loadingInfo.appendChild(statusContainer);

    right.appendChild(loadingInfo);

    // Disabled button (stays at bottom)
    const button = document.createElement('button');
    button.className = 'document-card__button';
    button.textContent = 'Details';
    button.disabled = true;
    button.setAttribute('aria-label', 'Loading document - details unavailable');
    right.appendChild(button);
  } else if (state === 'processing' && processingStatus) {
    // Wrap processing info in container to keep it at top
    const processingInfo = document.createElement('div');
    processingInfo.className = 'document-card__processing-info';

    // Processing state: spinner, status label, progress bar
    const statusContainer = document.createElement('div');
    statusContainer.className = 'document-card__status';

    const spinner = document.createElement('div');
    spinner.className = 'document-card__spinner';
    spinner.setAttribute('role', 'status');
    spinner.setAttribute('aria-label', 'Processing');

    const statusLabel = document.createElement('div');
    statusLabel.className = 'document-card__status-label';
    statusLabel.textContent = processingStatus.stage || 'Processing...';

    statusContainer.appendChild(spinner);
    statusContainer.appendChild(statusLabel);
    processingInfo.appendChild(statusContainer);

    // Progress bar and percentage container
    const progressWrapper = document.createElement('div');
    progressWrapper.className = 'document-card__progress-container';

    const progressContainer = document.createElement('div');
    progressContainer.className = 'document-card__progress';
    progressContainer.setAttribute('role', 'progressbar');
    progressContainer.setAttribute('aria-valuenow', Math.round((processingStatus.progress || 0) * 100));
    progressContainer.setAttribute('aria-valuemin', '0');
    progressContainer.setAttribute('aria-valuemax', '100');

    const progressBar = document.createElement('div');
    progressBar.className = 'document-card__progress-bar';
    progressBar.style.width = `${(processingStatus.progress || 0) * 100}%`;

    progressContainer.appendChild(progressBar);

    // Progress text
    const progressText = document.createElement('div');
    progressText.className = 'document-card__progress-text';
    progressText.textContent = `${Math.round((processingStatus.progress || 0) * 100)}%`;

    progressWrapper.appendChild(progressContainer);
    progressWrapper.appendChild(progressText);
    processingInfo.appendChild(progressWrapper);

    right.appendChild(processingInfo);

    // Disabled button (stays at bottom)
    const button = document.createElement('button');
    button.className = 'document-card__button';
    button.textContent = 'Details';
    button.disabled = true;
    button.setAttribute('aria-label', 'Processing document - details unavailable');
    right.appendChild(button);
  } else if (state === 'failed') {
    // Failed state: show error icon and message
    const errorInfo = document.createElement('div');
    errorInfo.className = 'document-card__error-info';

    const statusContainer = document.createElement('div');
    statusContainer.className = 'document-card__status document-card__status--error';

    // Error icon (X in circle)
    const errorIcon = document.createElement('div');
    errorIcon.className = 'document-card__error-icon';
    errorIcon.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <circle cx="12" cy="12" r="10"></circle>
      <line x1="15" y1="9" x2="9" y2="15"></line>
      <line x1="9" y1="9" x2="15" y2="15"></line>
    </svg>`;
    errorIcon.setAttribute('role', 'img');
    errorIcon.setAttribute('aria-label', 'Error');

    const statusLabel = document.createElement('div');
    statusLabel.className = 'document-card__status-label document-card__status-label--error';
    statusLabel.textContent = errorMessage || 'Upload failed';

    statusContainer.appendChild(errorIcon);
    statusContainer.appendChild(statusLabel);
    errorInfo.appendChild(statusContainer);

    right.appendChild(errorInfo);

    // Disabled button (stays at bottom)
    const button = document.createElement('button');
    button.className = 'document-card__button';
    button.textContent = 'Retry';
    button.disabled = true;
    button.setAttribute('aria-label', 'Upload failed - retry unavailable');
    right.appendChild(button);
  } else {
    // Completed state: show active button
    const button = document.createElement('a');
    button.className = 'document-card__button';
    button.href = detailsUrl;
    button.textContent = 'Details';
    button.setAttribute('aria-label', `View details for ${filename}`);

    right.appendChild(button);
  }

  // Assemble card
  card.appendChild(left);
  card.appendChild(right);

  return card;
}

/**
 * Update an existing card's processing state
 *
 * @param {HTMLElement} card - The card element to update
 * @param {Object} status - Processing status
 * @param {string} status.state - 'loading', 'processing', or 'completed'
 * @param {string} [status.stage] - Current processing stage
 * @param {number} [status.progress] - Progress 0.0-1.0
 */
export function updateCardState(card, status) {
  const { state, stage, progress } = status;

  // Update state classes
  card.classList.remove('document-card--loading', 'document-card--processing');
  if (state !== 'completed') {
    card.classList.add(`document-card--${state}`);
  }

  // Update processing-specific elements
  if (state === 'processing') {
    const statusLabel = card.querySelector('.document-card__status-label');
    const progressBar = card.querySelector('.document-card__progress-bar');
    const progressText = card.querySelector('.document-card__progress-text');
    const progressContainer = card.querySelector('.document-card__progress');

    if (statusLabel && stage) {
      statusLabel.textContent = stage;
    }

    if (progressBar && progress !== undefined) {
      progressBar.style.width = `${progress * 100}%`;
    }

    if (progressText && progress !== undefined) {
      progressText.textContent = `${Math.round(progress * 100)}%`;
    }

    if (progressContainer && progress !== undefined) {
      progressContainer.setAttribute('aria-valuenow', Math.round(progress * 100));
    }
  } else if (state === 'completed') {
    // Transition to completed state - would need to rebuild right column
    // For now, just remove processing classes
    // Full implementation would recreate the right column with proper button
  }
}

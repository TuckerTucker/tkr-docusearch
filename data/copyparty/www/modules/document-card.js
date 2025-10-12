/**
 * DocumentCard Component
 *
 * Creates a document information card with thumbnail, metadata badge, and details button
 * Supports both document (tall) and audio (square) variants
 */

/**
 * Lucide icon names for different file types
 */
const Icons = {
  // Document icon (file-text)
  document: 'file-text',

  // Audio icon (volume-2)
  audio: 'volume-2',

  // Video icon (video)
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
 * Get filename without extension
 * @param {string} filename - Full filename
 * @returns {string} Filename without extension
 */
function getFilenameWithoutExtension(filename) {
  const parts = filename.split('.');
  if (parts.length > 1) {
    parts.pop();
  }
  return parts.join('.');
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
 * @returns {HTMLElement} DocumentCard element
 */
export function createDocumentCard(options) {
  const {
    filename,
    thumbnailUrl,
    dateAdded,
    detailsUrl,
    variant: providedVariant,
    placeholderColor = '#E9E9E9'
  } = options;

  // Get file extension and determine variant
  const extension = getFileExtension(filename);
  const variant = providedVariant || fileTypeVariants[extension] || 'document';
  const iconType = fileTypeIcons[extension] || 'document';
  const title = getFilenameWithoutExtension(filename);
  const formattedDate = typeof dateAdded === 'string' ? dateAdded : formatDate(dateAdded);

  // Create card container
  const card = document.createElement('article');
  card.className = `document-card document-card--${variant}`;
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

  // Create Lucide icon element
  const badgeIcon = document.createElement('i');
  badgeIcon.className = 'document-card__badge-icon';
  badgeIcon.setAttribute('data-lucide', Icons[iconType]);

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

  // Right column (title + button)
  const right = document.createElement('div');
  right.className = 'document-card__right';

  const titleEl = document.createElement('h3');
  titleEl.className = 'document-card__title';
  titleEl.textContent = title;

  const button = document.createElement('a');
  button.className = 'document-card__button';
  button.href = detailsUrl;
  button.textContent = 'Details';
  button.setAttribute('aria-label', `View details for ${filename}`);

  right.appendChild(titleEl);
  right.appendChild(button);

  // Assemble card
  card.appendChild(left);
  card.appendChild(right);

  return card;
}

/**
 * Create multiple document cards
 *
 * @param {Array<Object>} documents - Array of document options
 * @returns {DocumentFragment} Fragment containing all cards
 */
export function createDocumentCards(documents) {
  const fragment = document.createDocumentFragment();

  documents.forEach(doc => {
    const card = createDocumentCard(doc);
    fragment.appendChild(card);
  });

  return fragment;
}

/**
 * Render document cards to a container
 *
 * @param {HTMLElement|string} container - Container element or selector
 * @param {Array<Object>} documents - Array of document options
 */
export function renderDocumentCards(container, documents) {
  const el = typeof container === 'string'
    ? document.querySelector(container)
    : container;

  if (!el) {
    console.error('Container not found');
    return;
  }

  const cards = createDocumentCards(documents);
  el.appendChild(cards);

  // Initialize Lucide icons for newly added cards
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }
}

// Export Icons object for external use
export { Icons };

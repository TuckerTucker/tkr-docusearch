/**
 * DocumentCard Component
 *
 * Creates a document information card with thumbnail, metadata badge, and details button
 * Supports both document (tall) and audio (square) variants
 */

/**
 * SVG Icons for different file types
 */
const Icons = {
  // Document icon (bookmark shape)
  document: `
    <svg class="document-card__badge-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M19 21L12 16L5 21V5C5 4.46957 5.21071 3.96086 5.58579 3.58579C5.96086 3.21071 6.46957 3 7 3H17C17.5304 3 18.0391 3.21071 18.4142 3.58579C18.7893 3.96086 19 4.46957 19 5V21Z"
            stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  `,

  // Audio icon (music note)
  audio: `
    <svg class="document-card__badge-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M9 18V5L21 3V16M9 18C9 19.6569 7.65685 21 6 21C4.34315 21 3 19.6569 3 18C3 16.3431 4.34315 15 6 15C7.65685 15 9 16.3431 9 18ZM21 16C21 17.6569 19.6569 19 18 19C16.3431 19 15 17.6569 15 16C15 14.3431 16.3431 13 18 13C19.6569 13 21 14.3431 21 16Z"
            stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  `,

  // Video icon
  video: `
    <svg class="document-card__badge-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M15 10L19.5528 7.72361C20.2177 7.39116 21 7.87465 21 8.61803V15.382C21 16.1253 20.2177 16.6088 19.5528 16.2764L15 14M5 18H13C14.1046 18 15 17.1046 15 16V8C15 6.89543 14.1046 6 13 6H5C3.89543 6 3 6.89543 3 8V16C3 17.1046 3.89543 18 5 18Z"
            stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  `
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

  const badgeIconSvg = document.createElement('div');
  badgeIconSvg.innerHTML = Icons[iconType];

  const badgeExtension = document.createElement('div');
  badgeExtension.className = 'document-card__badge-extension';
  badgeExtension.textContent = extension.toUpperCase();

  badgeIconContainer.appendChild(badgeIconSvg);
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
}

// Export Icons object for external use
export { Icons };

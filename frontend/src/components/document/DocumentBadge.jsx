/**
 * DocumentBadge Component
 *
 * Displays file type icon, extension, and upload date overlay on document thumbnails.
 *
 * Wave 2 - Library Agent
 */

import { formatDate } from '../../utils/formatting.js';

/**
 * File type to icon mapping
 */
const FILE_TYPE_ICONS = {
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
  // Video
  mp4: 'video',
  avi: 'video',
  mov: 'video',
  webm: 'video',
};

/**
 * SVG icons for file types
 */
const SVG_ICONS = {
  document: (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <line x1="10" y1="9" x2="8" y2="9" />
    </svg>
  ),
  audio: (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
      <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
      <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
    </svg>
  ),
  video: (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="23 7 16 12 23 17 23 7" />
      <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
    </svg>
  ),
};

/**
 * Get file extension from filename
 * @param {string} filename - Filename with extension
 * @returns {string} File extension in lowercase
 */
function getFileExtension(filename) {
  const parts = filename.split('.');
  return parts.length > 1 ? parts.pop().toLowerCase() : '';
}

/**
 * DocumentBadge Component
 *
 * @param {Object} props - Component props
 * @param {string} props.filename - Full filename with extension
 * @param {string|Date} props.uploadDate - Date document was uploaded
 * @returns {JSX.Element} Badge component
 */
export default function DocumentBadge({ filename, uploadDate }) {
  const extension = getFileExtension(filename);
  const iconType = FILE_TYPE_ICONS[extension] || 'document';
  const icon = SVG_ICONS[iconType];
  const formattedDate = formatDate(uploadDate);

  return (
    <div
      className="document-card__badge"
      aria-label={`Added ${formattedDate}, File type: ${extension.toUpperCase()}`}
    >
      <div className="document-card__badge-filetype">
        <div className="document-card__badge-icon-container">
          <div className="document-card__badge-icon">{icon}</div>
          <div className="document-card__badge-extension">{extension.toUpperCase()}</div>
        </div>
      </div>
      <div className="document-card__badge-date">
        Added<br />
        {formattedDate}
      </div>
    </div>
  );
}

/**
 * useDocumentCard Hook
 *
 * Custom hook that encapsulates DocumentCard business logic including:
 * - File type variant mapping (document vs audio)
 * - Display name formatting (removes extensions and timestamps)
 * - Delete state management
 * - CSS class building
 *
 * @param {Object} document - Document data
 * @param {string} document.doc_id - Document ID
 * @param {string} document.filename - Original filename
 * @param {string} [document.file_type] - File extension (e.g., 'pdf', 'mp3')
 * @param {string} [document.upload_date] - ISO upload date
 * @param {string} [document.thumbnail_url] - Thumbnail URL for visual docs
 * @param {string} [document.cover_art_url] - Cover art URL for audio
 * @param {string} [document.status='completed'] - Processing status
 * @param {string} [document.error_message] - Error message if failed
 * @param {string} [document.processing_stage] - Current processing stage
 * @param {number} [document.processing_progress] - Progress percentage (0-100)
 * @param {Function} [onDelete] - Delete handler function(docId, filename)
 * @returns {Object} Computed values and handlers
 * @returns {string} returns.doc_id - Document ID
 * @returns {string} returns.filename - Original filename
 * @returns {string} returns.upload_date - Upload date
 * @returns {string} returns.status - Processing status
 * @returns {string} returns.error_message - Error message
 * @returns {string} returns.processing_stage - Processing stage
 * @returns {number} returns.processing_progress - Progress percentage
 * @returns {string} returns.variant - Card variant ('document' or 'audio')
 * @returns {string} returns.displayName - Formatted display name
 * @returns {string} returns.thumbnailSrc - Thumbnail/cover art URL
 * @returns {string} returns.cardClasses - Computed CSS classes
 * @returns {boolean} returns.isDeleting - Delete in progress flag
 * @returns {Function} returns.handleDelete - Delete handler function
 *
 * @example
 * // Basic usage in DocumentCard component
 * function DocumentCard({ document, onDelete }) {
 *   const {
 *     displayName,
 *     variant,
 *     thumbnailSrc,
 *     cardClasses,
 *     isDeleting,
 *     handleDelete,
 *   } = useDocumentCard(document, onDelete);
 *
 *   return (
 *     <div className={cardClasses}>
 *       <img src={thumbnailSrc} alt={displayName} />
 *       <h3>{displayName}</h3>
 *       <button onClick={() => handleDelete(document.doc_id, document.filename)}>
 *         {isDeleting ? 'Deleting...' : 'Delete'}
 *       </button>
 *     </div>
 *   );
 * }
 */

import { useState } from 'react';

const FILE_TYPE_VARIANTS = {
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
  mp4: 'audio',
  avi: 'audio',
  mov: 'audio',
  webm: 'audio',
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
 * Get formatted filename without extension and timestamps
 * @param {string} filename - Full filename
 * @returns {string} Formatted display name
 */
function getDisplayName(filename) {
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
 * Build CSS classes for document card
 * @param {string} variant - Card variant (document or audio)
 * @param {string} status - Processing status
 * @returns {string} Space-separated class names
 */
function buildCardClasses(variant, status) {
  return [
    'document-card',
    `document-card--${variant}`,
    status !== 'completed' && `document-card--${status}`,
  ]
    .filter(Boolean)
    .join(' ');
}

export default function useDocumentCard(document, onDelete) {
  const [isDeleting, setIsDeleting] = useState(false);

  const {
    doc_id,
    filename,
    file_type,
    upload_date,
    thumbnail_url,
    cover_art_url,
    status = 'completed',
    error_message,
    processing_stage,
    processing_progress,
  } = document;

  const extension = file_type || getFileExtension(filename);
  const variant = FILE_TYPE_VARIANTS[extension] || 'document';
  const displayName = getDisplayName(filename);
  const thumbnailSrc = cover_art_url || thumbnail_url;

  const cardClasses = buildCardClasses(variant, status);

  const handleDelete = async (docId, filename) => {
    if (!onDelete) {
      console.warn('No onDelete handler provided to DocumentCard');
      return;
    }

    setIsDeleting(true);
    try {
      await onDelete(docId, filename);
    } catch (error) {
      console.error('Delete error:', error);
      setIsDeleting(false);
    }
  };

  return {
    doc_id,
    filename,
    upload_date,
    status,
    error_message,
    processing_stage,
    processing_progress,
    variant,
    displayName,
    thumbnailSrc,
    cardClasses,
    isDeleting,
    handleDelete,
  };
}

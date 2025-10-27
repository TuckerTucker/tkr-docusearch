/**
 * DocumentCard Component
 *
 * Display document information card with thumbnail, badge, and action button.
 * Supports two variants: document (tall 385x285) and audio (square 300x300).
 * Three states: completed, processing, failed.
 *
 * Wave 2 - Library Agent
 */

import { Link } from 'react-router-dom';
import { useState } from 'react';
import DocumentBadge from './DocumentBadge.jsx';
import DeleteButton from './DeleteButton.jsx';
import LoadingSpinner from '../common/LoadingSpinner.jsx';
import { DEFAULT_ALBUM_ART_SVG } from '../../utils/assets.js';

/**
 * File type to variant mapping
 */
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
  mp4: 'audio', // Use audio variant (square) for video
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
 * Thumbnail Component
 *
 * Renders document or audio file thumbnails with appropriate loading states and fallbacks.
 * Supports lazy loading optimization and handles image load errors gracefully.
 *
 * @param {Object} props - Component props
 * @param {string} [props.url] - Thumbnail image URL
 * @param {string} props.filename - Filename for alt text
 * @param {('document'|'audio')} props.variant - Card variant determining thumbnail dimensions
 * @param {('uploading'|'processing'|'completed'|'failed')} props.status - Document processing status
 * @param {boolean} [props.priority=false] - Whether to load image eagerly with high priority
 * @returns {JSX.Element} Thumbnail image or placeholder
 */
function Thumbnail({ url, filename, variant, status, priority = false }) {
  const extension = getFileExtension(filename);

  // Loading or processing states
  if (status === 'uploading' || status === 'processing') {
    return (
      <div className="document-card__thumbnail document-card__thumbnail--placeholder document-card__thumbnail--loading">
        {variant === 'audio' ? (
          <img
            src={DEFAULT_ALBUM_ART_SVG}
            alt="Audio file placeholder"
            className="document-card__thumbnail"
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          />
        ) : (
          <div className="document-card__thumbnail-icon">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="48"
              height="48"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
              <polyline points="10 9 9 9 8 9" />
            </svg>
          </div>
        )}
      </div>
    );
  }

  // Completed state with real thumbnail
  if (url && status === 'completed') {
    return (
      <img
        src={url}
        alt={`Thumbnail for ${filename}`}
        className="document-card__thumbnail"
        loading={priority ? 'eager' : 'lazy'}
        fetchPriority={priority ? 'high' : 'auto'}
        onError={(e) => {
          e.target.style.backgroundColor = '#E9E9E9';
          e.target.alt = `No preview available for ${filename}`;
        }}
      />
    );
  }

  // Fallback placeholder
  return (
    <div className="document-card__thumbnail document-card__thumbnail--placeholder">
      {variant === 'audio' ? (
        <img
          src={DEFAULT_ALBUM_ART_SVG}
          alt="Audio file placeholder"
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        />
      ) : (
        <div className="document-card__thumbnail-icon">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <polyline points="10 9 9 9 8 9" />
          </svg>
        </div>
      )}
    </div>
  );
}

/**
 * Processing Info Component
 *
 * Displays processing status with optional progress bar for documents being uploaded or processed.
 * Includes loading spinner and accessible ARIA attributes for screen readers.
 *
 * @param {Object} props - Component props
 * @param {string} [props.stage] - Current processing stage label (e.g., "Uploading...", "Generating embeddings...")
 * @param {number} [props.progress] - Progress value between 0 and 1 (e.g., 0.75 = 75%)
 * @returns {JSX.Element} Processing status display with spinner and optional progress bar
 */
function ProcessingInfo({ stage, progress }) {
  return (
    <div className="document-card__processing-info">
      <div className="document-card__status">
        <LoadingSpinner size="small" />
        <div className="document-card__status-label">{stage || 'Processing...'}</div>
      </div>
      {progress !== undefined && (
        <div className="document-card__progress-container">
          <div
            className="document-card__progress"
            role="progressbar"
            aria-valuenow={Math.round(progress * 100)}
            aria-valuemin="0"
            aria-valuemax="100"
          >
            <div
              className="document-card__progress-bar"
              style={{ width: `${progress * 100}%` }}
            />
          </div>
          <div className="document-card__progress-text">{Math.round(progress * 100)}%</div>
        </div>
      )}
    </div>
  );
}

/**
 * Error Info Component
 *
 * Displays error message for failed document uploads or processing.
 * Includes error icon with accessible ARIA label.
 *
 * @param {Object} props - Component props
 * @param {string} [props.message] - Error message to display (defaults to "Upload failed")
 * @returns {JSX.Element} Error status display with icon and message
 */
function ErrorInfo({ message }) {
  return (
    <div className="document-card__error-info">
      <div className="document-card__status document-card__status--error">
        <div className="document-card__error-icon" role="img" aria-label="Error">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="15" y1="9" x2="9" y2="15" />
            <line x1="9" y1="9" x2="15" y2="15" />
          </svg>
        </div>
        <div className="document-card__status-label document-card__status-label--error">
          {message || 'Upload failed'}
        </div>
      </div>
    </div>
  );
}

/**
 * DocumentCard Component
 *
 * Displays a document information card with thumbnail, badge, and action button.
 * Supports two variants (document: tall 385x285, audio: square 300x300) and four states
 * (uploading, processing, completed, failed). Provides delete functionality and navigation
 * to document details page.
 *
 * @param {Object} props - Component props
 * @param {Object} props.document - Document data object
 * @param {string} props.document.doc_id - Unique document identifier
 * @param {string} props.document.filename - Full filename with extension
 * @param {string} props.document.file_type - File type/extension (e.g., 'pdf', 'mp3')
 * @param {string} props.document.upload_date - ISO 8601 upload timestamp
 * @param {string} [props.document.thumbnail_url] - Thumbnail image URL (document files)
 * @param {string} [props.document.cover_art_url] - Cover art URL (audio files, takes precedence)
 * @param {('uploading'|'processing'|'completed'|'failed')} [props.document.status='completed'] - Document processing status
 * @param {string} [props.document.error_message] - Error message displayed when status is 'failed'
 * @param {string} [props.document.processing_stage] - Current processing stage label (e.g., "Generating embeddings...")
 * @param {number} [props.document.processing_progress] - Processing progress (0-1)
 * @param {Function} [props.onDelete] - Delete handler called with (doc_id, filename)
 * @param {Function} [props.onViewDetails] - View details handler (currently unused, navigation via Link)
 * @param {boolean} [props.priority=false] - Whether to prioritize loading this card's image (for above-fold cards)
 * @returns {JSX.Element} Document card article element
 *
 * @example
 * // Completed document card with delete handler
 * import DocumentCard from './components/document/DocumentCard';
 *
 * function Library() {
 *   const handleDelete = async (docId, filename) => {
 *     await fetch(`/api/documents/${docId}`, { method: 'DELETE' });
 *     // Refresh document list
 *   };
 *
 *   return (
 *     <DocumentCard
 *       document={{
 *         doc_id: '123',
 *         filename: 'report.pdf',
 *         file_type: 'pdf',
 *         upload_date: '2025-10-26T12:00:00Z',
 *         thumbnail_url: '/thumbnails/report_page_0.png',
 *         status: 'completed'
 *       }}
 *       onDelete={handleDelete}
 *       priority={true}
 *     />
 *   );
 * }
 *
 * @example
 * // Processing audio file card
 * <DocumentCard
 *   document={{
 *     doc_id: '456',
 *     filename: 'podcast.mp3',
 *     file_type: 'mp3',
 *     upload_date: '2025-10-26T13:00:00Z',
 *     cover_art_url: '/covers/podcast_cover.png',
 *     status: 'processing',
 *     processing_stage: 'Generating embeddings...',
 *     processing_progress: 0.65
 *   }}
 * />
 *
 * @example
 * // Failed upload card
 * <DocumentCard
 *   document={{
 *     doc_id: '789',
 *     filename: 'broken.pdf',
 *     file_type: 'pdf',
 *     upload_date: '2025-10-26T14:00:00Z',
 *     status: 'failed',
 *     error_message: 'File corrupted or unsupported format'
 *   }}
 *   onDelete={handleDelete}
 * />
 */
export default function DocumentCard({ document, onDelete, onViewDetails, priority = false }) {
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

  // Build CSS classes
  const cardClasses = [
    'document-card',
    `document-card--${variant}`,
    status !== 'completed' && `document-card--${status}`,
  ]
    .filter(Boolean)
    .join(' ');

  // Handle delete with loading state
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

  return (
    <article className={cardClasses} role="article" aria-label={`Document: ${filename}`}>
      {/* Left column: Thumbnail + Badge + Delete Button */}
      <div className="document-card__left">
        <Thumbnail
          url={thumbnailSrc}
          filename={filename}
          variant={variant}
          status={status}
          priority={priority}
        />
        <DocumentBadge filename={filename} uploadDate={upload_date} />

        {/* Delete button - only show for completed documents */}
        {status === 'completed' && onDelete && (
          <DeleteButton
            docId={doc_id}
            filename={filename}
            onDelete={handleDelete}
            isDeleting={isDeleting}
          />
        )}
      </div>

      {/* Right column: Title + Status/Button */}
      <div className="document-card__right">
        {/* Only show title for completed documents */}
        {status === 'completed' && <h3 className="document-card__title">{displayName}</h3>}

        {/* Status-specific content */}
        {status === 'uploading' && (
          <>
            <ProcessingInfo stage={processing_stage || 'Uploading...'} progress={processing_progress} />
            <button className="document-card__button" disabled aria-label="Uploading - details unavailable">
              Details
            </button>
          </>
        )}

        {status === 'processing' && (
          <>
            <ProcessingInfo stage={processing_stage} progress={processing_progress} />
            <button className="document-card__button" disabled aria-label="Processing - details unavailable">
              Details
            </button>
          </>
        )}

        {status === 'failed' && (
          <>
            <ErrorInfo message={error_message} />
            <button className="document-card__button" disabled aria-label="Upload failed - retry unavailable">
              Retry
            </button>
          </>
        )}

        {status === 'completed' && (
          <Link
            to={`/details/${doc_id}`}
            className="document-card__button"
            aria-label={`View details for ${filename}`}
          >
            Details
          </Link>
        )}
      </div>
    </article>
  );
}

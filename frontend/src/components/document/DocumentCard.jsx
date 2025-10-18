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
import DocumentBadge from './DocumentBadge.jsx';
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
 */
function Thumbnail({ url, filename, variant, status }) {
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
        loading="lazy"
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
 * @param {Object} props - Component props
 * @param {Object} props.document - Document data
 * @param {string} props.document.doc_id - Document ID
 * @param {string} props.document.filename - Filename
 * @param {string} props.document.file_type - File type/extension
 * @param {string} props.document.upload_date - Upload date
 * @param {string} [props.document.thumbnail_url] - Thumbnail image URL
 * @param {string} [props.document.cover_art_url] - Cover art URL (audio files)
 * @param {string} [props.document.status='completed'] - Document status
 * @param {string} [props.document.error_message] - Error message (if failed)
 * @param {Function} [props.onDelete] - Delete handler
 * @param {Function} [props.onViewDetails] - View details handler
 * @returns {JSX.Element} Document card
 */
export default function DocumentCard({ document, onDelete, onViewDetails }) {
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

  return (
    <article className={cardClasses} role="article" aria-label={`Document: ${filename}`}>
      {/* Left column: Thumbnail + Badge */}
      <div className="document-card__left">
        <Thumbnail
          url={thumbnailSrc}
          filename={filename}
          variant={variant}
          status={status}
        />
        <DocumentBadge filename={filename} uploadDate={upload_date} />
      </div>

      {/* Right column: Title + Status/Button */}
      <div className="document-card__right">
        {/* Only show title for completed documents */}
        {status === 'completed' && <h3 className="document-card__title">{displayName}</h3>}

        {/* Status-specific content */}
        {status === 'uploading' && (
          <>
            <div className="document-card__processing-info">
              <div className="document-card__status">
                <LoadingSpinner size="small" />
                <div className="document-card__status-label">Uploading...</div>
              </div>
            </div>
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
            to={`/document/${doc_id}`}
            className="document-card__button"
            aria-label={`View details for ${filename}`}
            onClick={onViewDetails}
          >
            Details
          </Link>
        )}
      </div>
    </article>
  );
}

/**
 * DocumentThumbnail Component
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

import { DEFAULT_ALBUM_ART_SVG } from '../../utils/assets.js';

const DOCUMENT_ICON = (
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
);

function AudioPlaceholder() {
  return (
    <img
      src={DEFAULT_ALBUM_ART_SVG}
      alt="Audio file placeholder"
      className="document-card__thumbnail"
      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
    />
  );
}

function DocumentPlaceholder() {
  return (
    <div className="document-card__thumbnail-icon">
      {DOCUMENT_ICON}
    </div>
  );
}

function LoadingPlaceholder({ variant }) {
  return (
    <div className="document-card__thumbnail document-card__thumbnail--placeholder document-card__thumbnail--loading">
      {variant === 'audio' ? <AudioPlaceholder /> : <DocumentPlaceholder />}
    </div>
  );
}

function FallbackPlaceholder({ variant }) {
  return (
    <div className="document-card__thumbnail document-card__thumbnail--placeholder">
      {variant === 'audio' ? <AudioPlaceholder /> : <DocumentPlaceholder />}
    </div>
  );
}

function ThumbnailImage({ url, filename, priority }) {
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

export default function DocumentThumbnail({ url, filename, variant, status, priority = false }) {
  // Loading or processing states
  if (status === 'uploading' || status === 'processing') {
    return <LoadingPlaceholder variant={variant} />;
  }

  // Completed state with real thumbnail
  if (url && status === 'completed') {
    return <ThumbnailImage url={url} filename={filename} priority={priority} />;
  }

  // Fallback placeholder
  return <FallbackPlaceholder variant={variant} />;
}

import PropTypes from 'prop-types'

/**
 * ReferenceCard Component - Display source document reference
 *
 * Ported from src/frontend/reference-card.js
 *
 * Features:
 * - Detailed and simple variants
 * - Document metadata, page info, thumbnail
 * - Highlight state when citation hovered/clicked
 * - Link to details page
 */
export default function ReferenceCard({
  reference,
  variant = 'detailed',
  isHighlighted = false,
  onHover,
}) {
  const {
    id,
    filename,
    extension = 'pdf',
    page = 1,
    thumbnail_path,
    date_added,
    doc_id,
  } = reference

  const citationNumber = id || 1

  const handleMouseEnter = () => {
    if (onHover) {
      onHover(citationNumber, true)
    }
  }

  const handleMouseLeave = () => {
    if (onHover) {
      onHover(citationNumber, false)
    }
  }

  // Build details URL
  const detailsURL = doc_id ? `/details/${doc_id}?page=${page}` : '#'

  // Format date
  const formattedDate = date_added ? formatDate(date_added) : null

  if (variant === 'simple') {
    return (
      <div
        className={`reference-card reference-card--simple ${
          isHighlighted ? 'reference-card--highlighted' : ''
        }`}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        data-citation-id={citationNumber}
        role="article"
        aria-label={`Reference ${citationNumber}: ${filename}, Page ${page}`}
      >
        <div className="reference-card__number">{citationNumber}</div>
        <div className="reference-card__filename-simple" title={filename}>
          {filename}
        </div>
        <a
          href={detailsURL}
          className="reference-card__details-btn-simple"
          aria-label="View details"
        >
          Details
        </a>
      </div>
    )
  }

  // Detailed variant (default)
  return (
    <div
      className={`reference-card reference-card--detailed ${
        isHighlighted ? 'reference-card--highlighted' : ''
      }`}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      data-citation-id={citationNumber}
      role="article"
      aria-label={`Reference ${citationNumber}: ${filename}, Page ${page}`}
    >
      <div className="reference-card__number">{citationNumber}</div>

      {thumbnail_path ? (
        <img
          src={thumbnail_path}
          alt={`Thumbnail of ${filename}`}
          className="reference-card__thumbnail"
          loading="lazy"
          onError={(e) => {
            e.target.style.display = 'none'
            e.target.nextElementSibling.style.display = 'flex'
          }}
        />
      ) : null}

      <div
        className="reference-card__thumbnail-placeholder"
        style={{ display: thumbnail_path ? 'none' : 'flex' }}
      >
        <FileIcon extension={extension} />
      </div>

      <div className="reference-card__content">
        <div className="reference-card__badge">{extension.toUpperCase()}</div>
        <div className="reference-card__filename" title={filename}>
          {filename}
        </div>
        <div className="reference-card__meta">
          Page {page}
          {formattedDate ? ` • ${formattedDate}` : ''}
        </div>
      </div>

      <a
        href={detailsURL}
        className="reference-card__details-btn"
        aria-label={`View details for ${filename}`}
      >
        Details
      </a>
    </div>
  )
}

ReferenceCard.propTypes = {
  reference: PropTypes.shape({
    id: PropTypes.number,
    filename: PropTypes.string.isRequired,
    extension: PropTypes.string,
    page: PropTypes.number,
    thumbnail_path: PropTypes.string,
    date_added: PropTypes.string,
    doc_id: PropTypes.string,
  }).isRequired,
  variant: PropTypes.oneOf(['detailed', 'simple']),
  isHighlighted: PropTypes.bool,
  onHover: PropTypes.func,
}

/**
 * FileIcon Component - SVG icon based on file extension
 */
function FileIcon({ extension }) {
  const icons = {
    pdf: (
      <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z" />
        <path d="M14 2v6h6M9 13h6M9 17h6M9 9h1" />
      </svg>
    ),
    docx: (
      <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z" />
        <path d="M14 2v6h6M10 9h4M10 13h4M10 17h4" />
      </svg>
    ),
    pptx: (
      <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z" />
        <path d="M14 2v6h6M8 11h8v6H8z" />
      </svg>
    ),
    mp3: (
      <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
        <path d="M9 18V5l12-2v13M9 13c0 1.66-1.34 3-3 3s-3-1.34-3-3 1.34-3 3-3 3 1.34 3 3zm12 0c0 1.66-1.34 3-3 3s-3-1.34-3-3 1.34-3 3-3 3 1.34 3 3z" />
      </svg>
    ),
    wav: (
      <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
        <path d="M9 18V5l12-2v13M9 13c0 1.66-1.34 3-3 3s-3-1.34-3-3 1.34-3 3-3 3 1.34 3 3zm12 0c0 1.66-1.34 3-3 3s-3-1.34-3-3 1.34-3 3-3 3 1.34 3 3z" />
      </svg>
    ),
  }

  const defaultIcon = (
    <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z" />
    </svg>
  )

  return icons[extension.toLowerCase()] || defaultIcon
}

FileIcon.propTypes = {
  extension: PropTypes.string.isRequired,
}

/**
 * Format date for display
 *
 * @param {string} isoDate - ISO date string
 * @returns {string} Formatted date
 */
function formatDate(isoDate) {
  try {
    const date = new Date(isoDate)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  } catch (e) {
    return isoDate
  }
}

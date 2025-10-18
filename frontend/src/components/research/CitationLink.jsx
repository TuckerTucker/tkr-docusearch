import PropTypes from 'prop-types'

/**
 * CitationLink Component - Inline superscript citation [N]
 *
 * Features:
 * - Click to scroll to reference card + highlight
 * - Hover to highlight reference card
 * - States: default, hover, active
 * - Accessibility: role="button", keyboard navigation
 */
export default function CitationLink({
  citationNumber,
  onCitationClick,
  onCitationHover,
  isActive = false,
}) {
  const handleClick = (e) => {
    e.preventDefault()
    if (onCitationClick) {
      onCitationClick(citationNumber)
    }
  }

  const handleMouseEnter = () => {
    if (onCitationHover) {
      onCitationHover(citationNumber, true)
    }
  }

  const handleMouseLeave = () => {
    if (onCitationHover) {
      onCitationHover(citationNumber, false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      handleClick(e)
    }
  }

  return (
    <button
      type="button"
      className={`citation-link ${isActive ? 'citation-link--active' : ''}`}
      onClick={handleClick}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onKeyDown={handleKeyDown}
      aria-label={`Citation ${citationNumber}`}
      data-citation-number={citationNumber}
    >
      [{citationNumber}]
    </button>
  )
}

CitationLink.propTypes = {
  citationNumber: PropTypes.number.isRequired,
  onCitationClick: PropTypes.func,
  onCitationHover: PropTypes.func,
  isActive: PropTypes.bool,
}

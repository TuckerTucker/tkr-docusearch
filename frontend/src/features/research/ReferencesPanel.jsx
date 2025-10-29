import { useState } from 'react'
import PropTypes from 'prop-types'
import ReferenceCard from '../../components/research/ReferenceCard.jsx'

/**
 * ReferencesPanel Component - Right panel with references list and view toggle
 *
 * Features:
 * - References header + view toggle
 * - Reference list with ReferenceCard components
 * - Detailed / Simple view modes
 * - Empty state
 */
export default function ReferencesPanel({
  references,
  activeReference,
  onReferenceHover,
}) {
  const [view, setView] = useState('detailed')

  const isEmpty = !references || references.length === 0

  return (
    <div className="references-panel">
      <div className="references-panel__header">
        <h2 className="references-panel__title">
          References {references && references.length > 0 && `(${references.length})`}
        </h2>

        {!isEmpty && (
          <div className="references-panel__view-toggle" role="group" aria-label="View mode">
            <button
              type="button"
              className={`view-toggle-btn ${view === 'detailed' ? 'view-toggle-btn--active' : ''}`}
              onClick={() => setView('detailed')}
              aria-pressed={view === 'detailed'}
            >
              Detailed
            </button>
            <button
              type="button"
              className={`view-toggle-btn ${view === 'simple' ? 'view-toggle-btn--active' : ''}`}
              onClick={() => setView('simple')}
              aria-pressed={view === 'simple'}
            >
              Simple
            </button>
          </div>
        )}
      </div>

      <div className="references-panel__content">
        {isEmpty ? (
          <div className="references-panel__empty-state">
            <div className="empty-state">
              <div className="empty-state__icon">
                <svg
                  width="48"
                  height="48"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z" />
                  <path d="M14 2v6h6M9 13h6M9 17h6M9 9h1" />
                </svg>
              </div>
              <p className="empty-state__description">
                Source references will appear here after you submit a query.
              </p>
            </div>
          </div>
        ) : (
          <div className="references-panel__list">
            {references.map((reference, index) => (
              <ReferenceCard
                key={reference.id || index}
                reference={{ ...reference, id: index + 1 }}
                variant={view}
                isHighlighted={activeReference === index + 1}
                onHover={onReferenceHover}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

ReferencesPanel.propTypes = {
  references: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number,
      filename: PropTypes.string,
      extension: PropTypes.string,
      page: PropTypes.number,
      thumbnail_path: PropTypes.string,
      date_added: PropTypes.string,
      doc_id: PropTypes.string,
      chunk_id: PropTypes.string, // Optional: enables precise navigation
    })
  ),
  activeReference: PropTypes.number,
  onReferenceHover: PropTypes.func,
}

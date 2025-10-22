import PropTypes from 'prop-types'
import QueryInput from '../../components/research/QueryInput.jsx'
import AnswerDisplay from '../../components/research/AnswerDisplay.jsx'

/**
 * ResearchPanel Component - Left panel with query input and answer display
 *
 * Features:
 * - QueryInput + AnswerDisplay
 * - Empty, loading, error states
 * - Handles query submission
 */
export default function ResearchPanel({
  query,
  answer,
  references,
  metadata,
  isLoading,
  error,
  onQuerySubmit,
  activeReference,
  onCitationClick,
  onCitationHover,
}) {
  return (
    <div className="research-panel">
      <div className="research-panel__input">
        <QueryInput onSubmit={onQuerySubmit} isLoading={isLoading} />
      </div>

      <div className="research-panel__content">
        {/* Empty state */}
        {!answer && !isLoading && !error && (
          <div className="research-panel__empty-state">
            <div className="empty-state">
              <div className="empty-state__icon">
                <svg
                  width="64"
                  height="64"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <circle cx="11" cy="11" r="8" />
                  <path d="m21 21-4.35-4.35" />
                </svg>
              </div>
              <h2 className="empty-state__title">Start Your Research</h2>
              <p className="empty-state__description">
                Ask a question about your documents and get an AI-generated answer with
                citations.
              </p>
            </div>
          </div>
        )}

        {/* Loading state */}
        {isLoading && (
          <div className="research-panel__loading-state">
            <div className="loading-state">
              <div className="loading-spinner" role="status">
                <svg
                  className="loading-spinner__svg"
                  viewBox="0 0 50 50"
                  aria-hidden="true"
                >
                  <circle
                    className="loading-spinner__circle"
                    cx="25"
                    cy="25"
                    r="20"
                    fill="none"
                    strokeWidth="4"
                  />
                </svg>
                <span className="sr-only">Loading</span>
              </div>
              <p className="loading-state__text">Researching your question...</p>
              <p className="loading-state__subtext">
                Searching documents and generating answer
              </p>
            </div>
          </div>
        )}

        {/* Error state */}
        {error && !isLoading && (
          <div className="research-panel__error-state">
            <div className="error-state">
              <div className="error-state__icon">
                <svg
                  width="48"
                  height="48"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
              </div>
              <h2 className="error-state__title">Research Failed</h2>
              <p className="error-state__message">{error.message || error}</p>
            </div>
          </div>
        )}

        {/* Success state with answer */}
        {answer && !isLoading && !error && (
          <div className="research-panel__answer">
            <AnswerDisplay
              answer={answer}
              references={references}
              metadata={metadata}
              activeReference={activeReference}
              onCitationClick={onCitationClick}
              onCitationHover={onCitationHover}
            />
          </div>
        )}
      </div>
    </div>
  )
}

ResearchPanel.propTypes = {
  query: PropTypes.string,
  answer: PropTypes.string,
  references: PropTypes.array,
  metadata: PropTypes.object,
  isLoading: PropTypes.bool,
  error: PropTypes.object,
  onQuerySubmit: PropTypes.func.isRequired,
  activeReference: PropTypes.number,
  onCitationClick: PropTypes.func,
  onCitationHover: PropTypes.func,
}

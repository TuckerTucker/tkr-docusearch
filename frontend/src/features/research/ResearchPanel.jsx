import PropTypes from 'prop-types'
import QueryInput from '../../components/research/QueryInput.jsx'
import AnswerDisplay from '../../components/research/AnswerDisplay.jsx'
import LiveRegion from '../../components/common/LiveRegion.jsx'

/**
 * ResearchPanel Component
 *
 * The left panel of the research interface that handles user queries and displays AI-generated
 * answers with citations. Manages multiple UI states including empty, loading, error, and success
 * states. Integrates QueryInput for user questions and AnswerDisplay for showing results with
 * inline citation links.
 *
 * Features:
 * - Query input with submission handling
 * - AI-generated answer display with inline citations
 * - Empty state with call-to-action
 * - Loading state with animated spinner
 * - Error state with user-friendly messaging
 * - Bidirectional citation highlighting (click/hover)
 * - Research metadata display (timing, model info)
 *
 * @component
 * @param {Object} props - Component props
 * @param {string} [props.query] - Current research query text
 * @param {string} [props.answer] - AI-generated answer text with citation markers (e.g., "[1]", "[2]")
 * @param {Array<Object>} [props.references] - Array of source document references cited in the answer
 * @param {Object} [props.metadata] - Research metadata including timing and model information
 * @param {number} [props.metadata.total_time] - Total research time in seconds
 * @param {number} [props.metadata.search_time] - Document search time in seconds
 * @param {number} [props.metadata.llm_time] - LLM inference time in seconds
 * @param {string} [props.metadata.model] - LLM model used for generation
 * @param {boolean} [props.isLoading=false] - Whether a research request is in progress
 * @param {Object|string} [props.error] - Error object or message if research failed
 * @param {string} [props.error.message] - Error message text
 * @param {Function} props.onQuerySubmit - Callback when user submits a query
 * @param {number} [props.activeReference] - Currently highlighted reference ID (1-indexed)
 * @param {Function} [props.onCitationClick] - Callback when user clicks a citation link
 * @param {Function} [props.onCitationHover] - Callback when user hovers over a citation link
 *
 * @returns {JSX.Element} The rendered research panel
 *
 * @example
 * // Basic usage with empty state
 * <ResearchPanel
 *   onQuerySubmit={(query) => handleResearch(query)}
 *   isLoading={false}
 * />
 *
 * @example
 * // With research results and citation handlers
 * <ResearchPanel
 *   query="What is ColPali?"
 *   answer="ColPali is a document retrieval model [1] that uses vision transformers [2]."
 *   references={[
 *     {
 *       id: 1,
 *       filename: "colpali_paper.pdf",
 *       page: 1,
 *       thumbnail_path: "/thumbnails/doc1_page1.jpg"
 *     },
 *     {
 *       id: 2,
 *       filename: "vision_transformers.pdf",
 *       page: 3,
 *       thumbnail_path: "/thumbnails/doc2_page3.jpg"
 *     }
 *   ]}
 *   metadata={{
 *     total_time: 2.5,
 *     search_time: 0.239,
 *     llm_time: 2.1,
 *     model: "anthropic/claude-3-5-sonnet-20241022"
 *   }}
 *   isLoading={false}
 *   activeReference={1}
 *   onQuerySubmit={(newQuery) => handleResearch(newQuery)}
 *   onCitationClick={(refId) => scrollToReference(refId)}
 *   onCitationHover={(refId) => setActiveReference(refId)}
 * />
 *
 * @example
 * // Loading state
 * <ResearchPanel
 *   query="What is ColPali?"
 *   isLoading={true}
 *   onQuerySubmit={handleResearch}
 * />
 *
 * @example
 * // Error state
 * <ResearchPanel
 *   error={{ message: "Failed to connect to research API" }}
 *   onQuerySubmit={handleResearch}
 *   isLoading={false}
 * />
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
  onDownloadReport,
}) {
  // Generate live region messages based on state
  const getLiveRegionMessage = () => {
    if (isLoading) {
      return 'Searching documents and generating answer...'
    }
    if (error) {
      return `Research failed: ${error.message || error}`
    }
    if (answer) {
      const refCount = references?.length || 0
      return `Answer ready with ${refCount} ${refCount === 1 ? 'reference' : 'references'}`
    }
    return null
  }

  return (
    <div className="research-panel">
      {/* Live region announcements for screen readers */}
      <LiveRegion
        message={getLiveRegionMessage()}
        politeness={error ? 'assertive' : 'polite'}
        role={error ? 'alert' : 'status'}
      />

      <div className="research-panel__input">
        <QueryInput onSubmit={onQuerySubmit} isLoading={isLoading} />

        {/* Download button - only show when answer exists */}
        {answer && !isLoading && !error && (
          <button
            type="button"
            className="research-panel__download-btn"
            onClick={onDownloadReport}
            title="Download Full Report"
            aria-label="Download research report as markdown file"
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            <span>Download Report</span>
          </button>
        )}
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
  onDownloadReport: PropTypes.func,
}

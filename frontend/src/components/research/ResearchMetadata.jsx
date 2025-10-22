import PropTypes from 'prop-types'
import './ResearchMetadata.css'

/**
 * ResearchMetadata Component - Display preprocessing metrics and research metadata
 *
 * Features:
 * - Preprocessing badge when enabled
 * - Token reduction percentage
 * - Processing latency
 * - Model information
 * - Tooltip explanations
 */
export default function ResearchMetadata({ metadata }) {
  if (!metadata) {
    return null
  }

  const {
    preprocessing_enabled,
    preprocessing_strategy,
    preprocessing_latency_ms,
    token_reduction_percent,
    model_used,
    total_latency_ms,
  } = metadata

  return (
    <div className="research-metadata">
      {/* Preprocessing Section - Only shown if enabled */}
      {preprocessing_enabled && (
        <div className="research-metadata__preprocessing">
          <div className="preprocessing-badge">
            <span className="preprocessing-badge__icon" aria-hidden="true">
              ⚡
            </span>
            <span className="preprocessing-badge__text">
              Preprocessed with {preprocessing_strategy}
            </span>
          </div>

          <div
            className="preprocessing-metrics"
            role="region"
            aria-label="Preprocessing metrics"
          >
            {/* Token Reduction */}
            {token_reduction_percent != null && (
              <div
                className="preprocessing-metric"
                title="Percentage of tokens reduced by local preprocessing"
              >
                <span className="preprocessing-metric__label">Token reduction:</span>
                <span className="preprocessing-metric__value preprocessing-metric__value--success">
                  {token_reduction_percent.toFixed(1)}%
                </span>
              </div>
            )}

            {/* Preprocessing Latency */}
            {preprocessing_latency_ms != null && (
              <div
                className="preprocessing-metric"
                title="Time spent on local preprocessing"
              >
                <span className="preprocessing-metric__label">Preprocessing:</span>
                <span className="preprocessing-metric__value">
                  {preprocessing_latency_ms}ms
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* General Metadata Section */}
      <div className="research-metadata__general">
        {/* Model Used */}
        {model_used && (
          <div className="metadata-item" title="Language model used to generate answer">
            <span className="metadata-item__label">Model:</span>
            <span className="metadata-item__value">{model_used}</span>
          </div>
        )}

        {/* Total Latency */}
        {total_latency_ms != null && (
          <div className="metadata-item" title="Total time to process query">
            <span className="metadata-item__label">Total time:</span>
            <span className="metadata-item__value">{total_latency_ms}ms</span>
          </div>
        )}
      </div>
    </div>
  )
}

ResearchMetadata.propTypes = {
  metadata: PropTypes.shape({
    preprocessing_enabled: PropTypes.bool,
    preprocessing_strategy: PropTypes.string,
    preprocessing_latency_ms: PropTypes.number,
    token_reduction_percent: PropTypes.number,
    original_sources_count: PropTypes.number,
    model_used: PropTypes.string,
    total_latency_ms: PropTypes.number,
  }),
}

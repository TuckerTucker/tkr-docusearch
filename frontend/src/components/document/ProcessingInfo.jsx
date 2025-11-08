/**
 * ProcessingInfo Component
 *
 * Displays processing status with optional progress bar for documents being uploaded or processed.
 * Includes loading spinner and accessible ARIA attributes for screen readers.
 *
 * @param {Object} props - Component props
 * @param {string} [props.stage] - Current processing stage label (e.g., "Uploading...", "Generating embeddings...")
 * @param {number} [props.progress] - Progress value between 0 and 1 (e.g., 0.75 = 75%)
 * @returns {JSX.Element} Processing status display with spinner and optional progress bar
 */

import LoadingSpinner from '../common/LoadingSpinner.jsx';

export default function ProcessingInfo({ stage, progress }) {
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

/**
 * DocumentActions Component
 *
 * Displays status-specific actions (processing info, error info, or details button)
 * for DocumentCard. Handles different states: uploading, processing, failed, completed.
 *
 * @param {Object} props - Component props
 * @param {string} props.status - Document processing status
 * @param {string} [props.stage] - Processing stage label
 * @param {number} [props.progress] - Processing progress (0-1)
 * @param {string} [props.errorMessage] - Error message for failed status
 * @param {string} props.docId - Document ID for navigation link
 * @param {string} props.filename - Filename for aria labels
 * @returns {JSX.Element} Status-specific actions
 */

import { Link } from 'react-router-dom';
import ProcessingInfo from './ProcessingInfo.jsx';
import ErrorInfo from './ErrorInfo.jsx';

export default function DocumentActions({
  status,
  stage,
  progress,
  errorMessage,
  docId,
  filename,
}) {
  if (status === 'uploading') {
    return (
      <>
        <ProcessingInfo stage={stage || 'Uploading...'} progress={progress} />
        <button className="document-card__button" disabled aria-label="Uploading - details unavailable">
          Details
        </button>
      </>
    );
  }

  if (status === 'processing') {
    return (
      <>
        <ProcessingInfo stage={stage} progress={progress} />
        <button className="document-card__button" disabled aria-label="Processing - details unavailable">
          Details
        </button>
      </>
    );
  }

  if (status === 'failed') {
    return (
      <>
        <ErrorInfo message={errorMessage} />
        <button className="document-card__button" disabled aria-label="Upload failed - retry unavailable">
          Retry
        </button>
      </>
    );
  }

  if (status === 'completed') {
    return (
      <Link
        to={`/details/${docId}`}
        className="document-card__button"
        aria-label={`View details for ${filename}`}
      >
        Details
      </Link>
    );
  }

  return null;
}

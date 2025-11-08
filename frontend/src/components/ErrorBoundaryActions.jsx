/**
 * ErrorBoundaryActions Component
 *
 * Displays action buttons (Try Again, Go to Home) for error recovery.
 * Extracted from ErrorBoundary to reduce component complexity.
 *
 * @param {Object} props - Component props
 * @param {Function} props.onReset - Callback for "Try Again" button
 * @returns {JSX.Element} Action buttons section
 */

export default function ErrorBoundaryActions({ onReset }) {
  return (
    <div className="error-actions">
      <button
        onClick={onReset}
        className="btn btn-primary"
        type="button"
      >
        Try Again
      </button>
      <button
        onClick={() => window.location.href = '/'}
        className="btn btn-secondary"
        type="button"
      >
        Go to Home
      </button>
    </div>
  );
}

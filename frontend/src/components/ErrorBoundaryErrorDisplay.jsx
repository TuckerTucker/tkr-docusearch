/**
 * ErrorBoundaryErrorDisplay Component
 *
 * Displays error details in a collapsible details element.
 * Extracted from ErrorBoundary to reduce component complexity.
 *
 * @param {Object} props - Component props
 * @param {Error} [props.error] - Error object to display
 * @param {Object} [props.errorInfo] - Error info with component stack
 * @returns {JSX.Element} Error details section or null
 */

export default function ErrorBoundaryErrorDisplay({ error, errorInfo }) {
  if (!error) return null;

  return (
    <details className="error-details">
      <summary>Error details</summary>
      <pre className="error-stack">
        <strong>{error.toString()}</strong>
        {errorInfo && (
          <>
            {'\n\n'}
            {errorInfo.componentStack}
          </>
        )}
      </pre>
    </details>
  );
}

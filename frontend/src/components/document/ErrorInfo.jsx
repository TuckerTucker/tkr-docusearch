/**
 * ErrorInfo Component
 *
 * Displays error message for failed document uploads or processing.
 * Includes error icon with accessible ARIA label.
 *
 * @param {Object} props - Component props
 * @param {string} [props.message] - Error message to display (defaults to "Upload failed")
 * @returns {JSX.Element} Error status display with icon and message
 */

const ERROR_ICON = (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="20"
    height="20"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
  >
    <circle cx="12" cy="12" r="10" />
    <line x1="15" y1="9" x2="9" y2="15" />
    <line x1="9" y1="9" x2="15" y2="15" />
  </svg>
);

export default function ErrorInfo({ message }) {
  return (
    <div className="document-card__error-info">
      <div className="document-card__status document-card__status--error">
        <div className="document-card__error-icon" role="img" aria-label="Error">
          {ERROR_ICON}
        </div>
        <div className="document-card__status-label document-card__status-label--error">
          {message || 'Upload failed'}
        </div>
      </div>
    </div>
  );
}

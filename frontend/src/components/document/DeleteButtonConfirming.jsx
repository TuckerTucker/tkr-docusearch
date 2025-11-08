/**
 * DeleteButtonConfirming Component
 *
 * Confirmation state with delete and cancel buttons.
 * Extracted sub-component for DeleteButton.
 *
 * @param {Object} props - Component props
 * @param {string} props.filename - Document filename
 * @param {Function} props.onConfirm - Confirm deletion callback
 * @param {Function} props.onCancel - Cancel deletion callback
 * @param {Function} props.onKeyDown - Keyboard handler
 * @param {boolean} props.isDeleting - Loading state during deletion
 * @param {boolean} props.disabled - Disable state
 * @returns {JSX.Element} Confirmation buttons
 */

const DELETE_ICON = (
  <svg
    xmlns="http://www.w3.org/2000/svg"
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
    <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M10 11v6M14 11v6" />
  </svg>
);

const SPINNER_ICON = (
  <svg
    width="20"
    height="20"
    viewBox="0 0 20 20"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className="delete-button__spinner-icon"
  >
    <circle
      cx="10"
      cy="10"
      r="8"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeDasharray="12 38"
    />
  </svg>
);

export default function DeleteButtonConfirming({
  filename,
  onConfirm,
  onCancel,
  onKeyDown,
  isDeleting,
  disabled,
}) {
  return (
    <div
      className="delete-button delete-button--confirming"
      onKeyDown={onKeyDown}
      role="group"
      aria-label="Delete confirmation"
    >
      <button
        className="delete-button__confirm"
        onClick={onConfirm}
        disabled={disabled || isDeleting}
        aria-label={`Confirm delete ${filename}`}
        type="button"
      >
        {isDeleting ? (
          <>
            <span className="delete-button__spinner" role="status" aria-label="Deleting...">
              {SPINNER_ICON}
            </span>
            Deleting...
          </>
        ) : (
          <>
            {DELETE_ICON}
            Delete Permanently
          </>
        )}
      </button>
      <button
        className="delete-button__cancel"
        onClick={onCancel}
        disabled={disabled || isDeleting}
        aria-label="Cancel deletion"
        type="button"
      >
        Cancel
      </button>
    </div>
  );
}

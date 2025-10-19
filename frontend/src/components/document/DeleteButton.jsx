/**
 * DeleteButton Component
 *
 * Two-step delete confirmation button for document cards.
 * Appears on hover, expands on click to show confirm/cancel.
 *
 * States:
 * - hidden: Not visible (default, no hover)
 * - small: Small trash icon (on card hover)
 * - confirming: Large delete/cancel buttons (on delete click)
 */

import { useState } from 'react';
import PropTypes from 'prop-types';

/**
 * DeleteButton Component
 *
 * @param {Object} props - Component props
 * @param {string} props.docId - Document ID to delete
 * @param {string} props.filename - Document filename (for confirmation)
 * @param {Function} props.onDelete - Callback when deletion confirmed
 * @param {boolean} props.isDeleting - Loading state during deletion
 * @param {boolean} props.disabled - Disable all interactions
 */
export default function DeleteButton({ docId, filename, onDelete, isDeleting = false, disabled = false }) {
  const [isConfirming, setIsConfirming] = useState(false);

  const handleDeleteClick = (e) => {
    e.preventDefault();
    e.stopPropagation();

    if (disabled || isDeleting) return;

    setIsConfirming(true);
  };

  const handleConfirm = (e) => {
    e.preventDefault();
    e.stopPropagation();

    if (disabled || isDeleting) return;

    onDelete(docId, filename);
    // Keep confirming state until parent handles deletion
  };

  const handleCancel = (e) => {
    e.preventDefault();
    e.stopPropagation();

    setIsConfirming(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape' && isConfirming) {
      e.preventDefault();
      e.stopPropagation();
      setIsConfirming(false);
    }
  };

  // Small delete button (hover state)
  if (!isConfirming) {
    return (
      <button
        className="delete-button delete-button--small"
        onClick={handleDeleteClick}
        disabled={disabled || isDeleting}
        aria-label={`Delete ${filename}`}
        title={`Delete ${filename}`}
        type="button"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M10 11v6M14 11v6" />
        </svg>
      </button>
    );
  }

  // Confirmation state (delete + cancel buttons)
  return (
    <div
      className="delete-button delete-button--confirming"
      onKeyDown={handleKeyDown}
      role="group"
      aria-label="Delete confirmation"
    >
      <button
        className="delete-button__confirm"
        onClick={handleConfirm}
        disabled={disabled || isDeleting}
        aria-label={`Confirm delete ${filename}`}
        type="button"
      >
        {isDeleting ? (
          <>
            <span className="delete-button__spinner" role="status" aria-label="Deleting...">
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
            </span>
            Deleting...
          </>
        ) : (
          <>
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
            Delete Permanently
          </>
        )}
      </button>
      <button
        className="delete-button__cancel"
        onClick={handleCancel}
        disabled={disabled || isDeleting}
        aria-label="Cancel deletion"
        type="button"
      >
        Cancel
      </button>
    </div>
  );
}

DeleteButton.propTypes = {
  docId: PropTypes.string.isRequired,
  filename: PropTypes.string.isRequired,
  onDelete: PropTypes.func.isRequired,
  isDeleting: PropTypes.bool,
  disabled: PropTypes.bool,
};

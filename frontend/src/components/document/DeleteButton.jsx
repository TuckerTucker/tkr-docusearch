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

import PropTypes from 'prop-types';
import useDeleteConfirmation from '../../hooks/useDeleteConfirmation.js';
import DeleteButtonSmall from './DeleteButtonSmall.jsx';
import DeleteButtonConfirming from './DeleteButtonConfirming.jsx';

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
  const {
    isConfirming,
    handleDeleteClick,
    handleConfirm,
    handleCancel,
    handleKeyDown,
  } = useDeleteConfirmation(docId, filename, onDelete, isDeleting, disabled);

  if (!isConfirming) {
    return (
      <DeleteButtonSmall
        filename={filename}
        onClick={handleDeleteClick}
        disabled={disabled || isDeleting}
      />
    );
  }

  return (
    <DeleteButtonConfirming
      filename={filename}
      onConfirm={handleConfirm}
      onCancel={handleCancel}
      onKeyDown={handleKeyDown}
      isDeleting={isDeleting}
      disabled={disabled}
    />
  );
}

DeleteButton.propTypes = {
  docId: PropTypes.string.isRequired,
  filename: PropTypes.string.isRequired,
  onDelete: PropTypes.func.isRequired,
  isDeleting: PropTypes.bool,
  disabled: PropTypes.bool,
};

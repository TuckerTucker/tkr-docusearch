/**
 * useDeleteConfirmation Hook
 *
 * Custom hook for managing delete confirmation state and handlers.
 * Encapsulates confirmation logic for DeleteButton component.
 *
 * @param {string} docId - Document ID to delete
 * @param {string} filename - Document filename
 * @param {Function} onDelete - Callback when deletion confirmed function(docId, filename)
 * @param {boolean} [isDeleting=false] - Loading state during deletion
 * @param {boolean} [disabled=false] - Disable all interactions
 * @returns {Object} Confirmation state and handlers
 * @returns {boolean} returns.isConfirming - Whether in confirmation state
 * @returns {Function} returns.handleDeleteClick - Click handler for delete button
 * @returns {Function} returns.handleConfirm - Click handler for confirm button
 * @returns {Function} returns.handleCancel - Click handler for cancel button
 * @returns {Function} returns.handleKeyDown - Keydown handler for Escape key
 *
 * @example
 * // Basic usage in DeleteButton component
 * function DeleteButton({ docId, filename, onDelete, isDeleting }) {
 *   const {
 *     isConfirming,
 *     handleDeleteClick,
 *     handleConfirm,
 *     handleCancel,
 *     handleKeyDown,
 *   } = useDeleteConfirmation(docId, filename, onDelete, isDeleting);
 *
 *   if (isConfirming) {
 *     return (
 *       <div onKeyDown={handleKeyDown}>
 *         <button onClick={handleConfirm}>Confirm</button>
 *         <button onClick={handleCancel}>Cancel</button>
 *       </div>
 *     );
 *   }
 *
 *   return (
 *     <button onClick={handleDeleteClick}>
 *       {isDeleting ? 'Deleting...' : 'Delete'}
 *     </button>
 *   );
 * }
 */

import { useState } from 'react';

export default function useDeleteConfirmation(docId, filename, onDelete, isDeleting = false, disabled = false) {
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

  return {
    isConfirming,
    handleDeleteClick,
    handleConfirm,
    handleCancel,
    handleKeyDown,
  };
}

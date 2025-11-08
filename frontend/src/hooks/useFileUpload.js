/**
 * useFileUpload Hook - Centralized file upload state management
 *
 * Consolidates upload modal state (previously 10 separate useState calls) into
 * a single useReducer for better state management, testability, and performance.
 *
 * Wave 7 - DevOps & Standards Lead (Agent-8)
 */

import { useReducer, useRef, useCallback } from 'react';

/**
 * Upload item state object
 * @typedef {Object} UploadItem
 * @property {string} filename - Name of the file
 * @property {number} progress - Upload progress percentage (0-100)
 * @property {string} status - Status of upload (pending|uploading|complete|error|duplicate|cancelled)
 * @property {string} [error] - Error message if status is 'error'
 * @property {boolean} [isDuplicate] - Whether file is a duplicate
 * @property {Object} [existingDoc] - Existing document metadata if duplicate
 * @property {boolean} [forceUpload] - Whether user chose to force upload duplicate
 */

/**
 * Upload state reducer
 *
 * @param {Object} state - Current state
 * @param {string} state.isVisible - Modal visibility
 * @param {boolean} state.isUploading - Whether upload is in progress
 * @param {UploadItem[]} state.uploads - Array of upload items
 * @param {Map} state.fileMap - Map of File objects by filename
 * @param {Object} action - Action to dispatch
 * @returns {Object} New state
 */
function uploadReducer(state, action) {
  switch (action.type) {
    // Modal visibility
    case 'SHOW_MODAL':
      return { ...state, isVisible: true };

    case 'HIDE_MODAL':
      return {
        ...state,
        isVisible: false,
        uploads: [],
        fileMap: new Map(),
      };

    // Upload state management
    case 'SET_UPLOADING':
      return { ...state, isUploading: action.payload };

    case 'SET_UPLOADS':
      return { ...state, uploads: action.payload };

    case 'UPDATE_UPLOAD_PROGRESS':
      return {
        ...state,
        uploads: state.uploads.map((item, idx) =>
          idx === action.payload.index
            ? { ...item, progress: action.payload.progress }
            : item
        ),
      };

    case 'UPDATE_UPLOAD_STATUS':
      return {
        ...state,
        uploads: state.uploads.map((item) =>
          item.filename === action.payload.filename
            ? {
                ...item,
                status: action.payload.status,
                error: action.payload.error,
                progress: action.payload.progress ?? item.progress,
              }
            : item
        ),
      };

    // File management
    case 'SET_FILE_MAP':
      return { ...state, fileMap: action.payload };

    // Batch operations
    case 'RESET':
      return {
        isVisible: false,
        isUploading: false,
        uploads: [],
        fileMap: new Map(),
      };

    default:
      return state;
  }
}

/**
 * Custom hook for file upload state management
 *
 * Consolidates 10 separate useState calls into unified state with useReducer.
 * Provides cleaner API and better performance through memoized actions.
 *
 * @returns {Object} Upload state and actions
 * @returns {boolean} returns.isVisible - Modal visibility
 * @returns {boolean} returns.isUploading - Upload in progress flag
 * @returns {UploadItem[]} returns.uploads - Current uploads array
 * @returns {Map} returns.fileMap - File objects by filename
 * @returns {Function} returns.showModal - Show upload modal
 * @returns {Function} returns.hideModal - Hide upload modal
 * @returns {Function} returns.setUploading - Set uploading state
 * @returns {Function} returns.setUploads - Batch set uploads
 * @returns {Function} returns.updateUploadProgress - Update single file progress
 * @returns {Function} returns.updateUploadStatus - Update single file status
 * @returns {Function} returns.setFileMap - Set file map
 * @returns {Function} returns.reset - Reset all state
 * @example
 * const {
 *   isVisible,
 *   isUploading,
 *   uploads,
 *   showModal,
 *   hideModal,
 *   updateUploadProgress,
 *   updateUploadStatus,
 * } = useFileUpload();
 *
 * // Show modal and set initial uploads
 * showModal();
 * setUploads([
 *   { filename: 'doc.pdf', progress: 0, status: 'pending' }
 * ]);
 *
 * // Update progress
 * updateUploadProgress(0, 45); // First file to 45%
 *
 * // Update status
 * updateUploadStatus('doc.pdf', 'complete', null, 100);
 */
export function useFileUpload() {
  const [state, dispatch] = useReducer(uploadReducer, {
    isVisible: false,
    isUploading: false,
    uploads: [],
    fileMap: new Map(),
  });

  // Memoized action creators for consistent function identity
  const showModal = useCallback(() => {
    dispatch({ type: 'SHOW_MODAL' });
  }, []);

  const hideModal = useCallback(() => {
    dispatch({ type: 'HIDE_MODAL' });
  }, []);

  const setUploading = useCallback((isUploading) => {
    dispatch({ type: 'SET_UPLOADING', payload: isUploading });
  }, []);

  const setUploads = useCallback((uploads) => {
    dispatch({ type: 'SET_UPLOADS', payload: uploads });
  }, []);

  const updateUploadProgress = useCallback((index, progress) => {
    dispatch({
      type: 'UPDATE_UPLOAD_PROGRESS',
      payload: { index, progress },
    });
  }, []);

  const updateUploadStatus = useCallback((filename, status, error = null, progress = null) => {
    dispatch({
      type: 'UPDATE_UPLOAD_STATUS',
      payload: { filename, status, error, progress },
    });
  }, []);

  const setFileMap = useCallback((fileMap) => {
    dispatch({ type: 'SET_FILE_MAP', payload: fileMap });
  }, []);

  const reset = useCallback(() => {
    dispatch({ type: 'RESET' });
  }, []);

  return {
    // State
    isVisible: state.isVisible,
    isUploading: state.isUploading,
    uploads: state.uploads,
    fileMap: state.fileMap,

    // Actions
    showModal,
    hideModal,
    setUploading,
    setUploads,
    updateUploadProgress,
    updateUploadStatus,
    setFileMap,
    reset,
  };
}

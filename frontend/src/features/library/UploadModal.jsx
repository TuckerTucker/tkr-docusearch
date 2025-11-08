/**
 * UploadModal Component
 *
 * Drag-and-drop upload modal with progress tracking and multi-file support.
 * Shows on global drag-over, supports file validation, and provides upload feedback.
 *
 * Wave 2 - Library Agent
 */

import { useEffect, useRef } from 'react';
import { api } from '../../services/api.js';
import { useDocumentStore } from '../../stores/useDocumentStore.js';
import { useFileUpload } from '../../hooks/useFileUpload.js';
import LiveRegion from '../../components/common/LiveRegion.jsx';

/**
 * Supported file types (matches backend file_validator.py)
 */
const SUPPORTED_TYPES = [
  '.pdf',
  '.docx',
  '.doc',
  '.pptx',
  '.ppt',
  '.xlsx',
  '.xls',
  '.html',
  '.xhtml',
  '.md',
  '.asciidoc',
  '.csv',
  '.mp3',
  '.wav',
  '.vtt',
  '.png',
  '.jpg',
  '.jpeg',
  '.tiff',
  '.bmp',
  '.webp',
];

const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB

/**
 * Format file types for display
 * Converts array of file extensions to uppercase comma-separated string
 *
 * @returns {string} Formatted file types (e.g., "PDF, DOCX, MP3")
 * @example
 * formatSupportedTypes()
 * // Returns: "PDF, DOCX, DOC, PPTX, PPT, XLSX, XLS, HTML, XHTML, MD, ASCIIDOC, CSV, MP3, WAV, VTT, PNG, JPG, JPEG, TIFF, BMP, WEBP"
 */
function formatSupportedTypes() {
  return SUPPORTED_TYPES.map((ext) => ext.toUpperCase().replace('.', '')).join(', ');
}

/**
 * Validate file against supported types and size limits
 * Checks file extension and size against MAX_FILE_SIZE (100MB)
 *
 * @param {File} file - File object to validate
 * @returns {{valid: boolean, error?: string, code?: string}} Validation result
 * @returns {boolean} returns.valid - Whether file is valid
 * @returns {string} [returns.error] - Error message if invalid
 * @returns {string} [returns.code] - Error code if invalid (UNSUPPORTED_TYPE | FILE_TOO_LARGE)
 * @example
 * const file = new File(['content'], 'document.pdf', { type: 'application/pdf' });
 * const result = validateFile(file);
 * if (result.valid) {
 *   console.log('File is valid');
 * } else {
 *   console.error(result.error);
 * }
 */
function validateFile(file) {
  const ext = '.' + file.name.split('.').pop().toLowerCase();

  if (!SUPPORTED_TYPES.includes(ext)) {
    return {
      valid: false,
      error: `Unsupported file type: ${ext}`,
      code: 'UNSUPPORTED_TYPE',
    };
  }

  if (file.size > MAX_FILE_SIZE) {
    const maxMB = Math.round(MAX_FILE_SIZE / 1024 / 1024);
    return {
      valid: false,
      error: `File exceeds maximum size of ${maxMB}MB`,
      code: 'FILE_TOO_LARGE',
    };
  }

  return { valid: true };
}

/**
 * Upload Progress Item Component
 * Displays individual file upload progress with status indicators
 * Shows special UI for duplicate files with cancel/continue options
 *
 * @param {Object} props - Component props
 * @param {string} props.filename - Name of file being uploaded
 * @param {number} props.progress - Upload progress percentage (0-100)
 * @param {string} props.status - Upload status (pending | uploading | complete | error | duplicate | cancelled)
 * @param {string} [props.error] - Error message if status is error
 * @param {boolean} [props.isDuplicate] - Whether file is a duplicate
 * @param {Object} [props.existingDoc] - Existing document metadata if duplicate
 * @param {Function} [props.onCancelUpload] - Callback to cancel duplicate upload
 * @param {Function} [props.onContinueUpload] - Callback to continue with duplicate upload
 * @returns {JSX.Element} Upload progress item
 * @example
 * // Regular upload progress
 * <UploadProgressItem
 *   filename="document.pdf"
 *   progress={45}
 *   status="uploading"
 * />
 *
 * @example
 * // Duplicate file with user decision
 * <UploadProgressItem
 *   filename="document.pdf"
 *   progress={0}
 *   status="duplicate"
 *   isDuplicate={true}
 *   existingDoc={{ doc_id: "abc123", title: "document.pdf" }}
 *   onCancelUpload={(filename) => console.log(`Cancelled: ${filename}`)}
 *   onContinueUpload={(filename) => console.log(`Continuing: ${filename}`)}
 * />
 */
function UploadProgressItem({
  filename,
  progress,
  status,
  error,
  isDuplicate,
  existingDoc,
  onCancelUpload,
  onContinueUpload
}) {
  if (status === 'duplicate') {
    return (
      <div className="upload-modal__progress-item upload-modal__progress-item--duplicate">
        <div className="upload-modal__progress-filename">{filename}</div>
        <div className="upload-modal__duplicate-warning">
          This file appears to be in the library already
        </div>
        <div className="upload-modal__duplicate-actions">
          <button
            className="upload-modal__duplicate-btn upload-modal__duplicate-btn--cancel"
            onClick={() => onCancelUpload && onCancelUpload(filename)}
          >
            ✕ Cancel Upload
          </button>
          <button
            className="upload-modal__duplicate-btn upload-modal__duplicate-btn--continue"
            onClick={() => onContinueUpload && onContinueUpload(filename)}
          >
            ✓ Continue Upload
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`upload-modal__progress-item ${
        status === 'complete' ? 'upload-modal__progress-item--complete' : ''
      } ${status === 'error' ? 'upload-modal__progress-item--failed' : ''} ${
        status === 'cancelled' ? 'upload-modal__progress-item--cancelled' : ''
      }`}
    >
      <div className="upload-modal__progress-filename">{filename}</div>
      <div className="upload-modal__progress-bar">
        <div
          className="upload-modal__progress-fill"
          style={{
            width: `${progress}%`,
            backgroundColor: status === 'error' ? '#ef4444' : undefined,
          }}
        />
      </div>
      <div
        className="upload-modal__progress-status"
        style={{
          color:
            status === 'complete' ? '#10b981' :
            status === 'error' ? '#ef4444' :
            status === 'cancelled' ? '#6b7280' :
            undefined,
        }}
      >
        {status === 'complete' && '✓ Complete'}
        {status === 'error' && `✗ ${error || 'Failed'}`}
        {status === 'uploading' && `${progress}%`}
        {status === 'cancelled' && '✗ Cancelled (duplicate)'}
      </div>
    </div>
  );
}

/**
 * UploadModal Component
 *
 * Main upload modal with drag-and-drop support, multi-file upload, progress tracking,
 * and duplicate detection. Automatically shows when files are dragged over the window
 * or when triggered via manual upload button.
 *
 * Features:
 * - Global drag-and-drop detection
 * - Multi-file parallel uploads
 * - Real-time progress tracking
 * - Duplicate file detection with user choice
 * - File validation (type and size)
 * - WebSocket-based pre-registration for instant UI updates
 * - Temporary document creation in store during upload
 *
 * @param {Object} props - Component props
 * @param {Function} [props.onUploadComplete] - Callback when upload completes
 * @param {Object} [props.onUploadComplete.result] - Upload result object
 * @param {number} props.onUploadComplete.result.total - Total files attempted
 * @param {number} props.onUploadComplete.result.successful - Successfully uploaded files
 * @param {number} props.onUploadComplete.result.failed - Failed uploads
 * @param {Function} props.registerUploadBatch - WebSocket function to pre-register uploads
 * @param {File[]} props.registerUploadBatch.files - Files to register
 * @param {boolean} [props.registerUploadBatch.forceUpload=false] - Force upload even if duplicate
 * @param {Promise<Array<{doc_id: string, filename: string, is_duplicate: boolean, existing_doc?: Object}>>} props.registerUploadBatch.returns - Registration results
 * @param {boolean} props.isWebSocketConnected - WebSocket connection status
 * @returns {JSX.Element|null} Upload modal or null if not visible
 * @example
 * // Basic usage with WebSocket support
 * import UploadModal from './features/library/UploadModal';
 * import { useWebSocket } from './hooks/useWebSocket';
 *
 * function App() {
 *   const { registerUploadBatch, isConnected } = useWebSocket();
 *
 *   const handleUploadComplete = ({ total, successful, failed }) => {
 *     console.log(`Uploaded ${successful}/${total} files`);
 *     if (failed > 0) {
 *       alert(`${failed} files failed to upload`);
 *     }
 *     // Refresh document library
 *     fetchDocuments();
 *   };
 *
 *   return (
 *     <UploadModal
 *       onUploadComplete={handleUploadComplete}
 *       registerUploadBatch={registerUploadBatch}
 *       isWebSocketConnected={isConnected}
 *     />
 *   );
 * }
 *
 * @example
 * // Triggering manual upload from button
 * function UploadButton() {
 *   const handleFileSelect = (e) => {
 *     const files = Array.from(e.target.files);
 *     // Dispatch event that UploadModal listens for
 *     window.dispatchEvent(new CustomEvent('manualUpload', {
 *       detail: { files }
 *     }));
 *   };
 *
 *   return (
 *     <input type="file" multiple onChange={handleFileSelect} />
 *   );
 * }
 */
export default function UploadModal({ onUploadComplete, registerUploadBatch, isWebSocketConnected }) {
  // Consolidated state management using useReducer via custom hook
  const {
    isVisible,
    isUploading,
    uploads,
    fileMap,
    showModal,
    hideModal,
    setUploading,
    setUploads,
    updateUploadProgress,
    updateUploadStatus,
    setFileMap,
    reset,
  } = useFileUpload();

  const dragCounterRef = useRef(0);
  const pendingFilesRef = useRef(null); // Store files waiting for WebSocket connection

  const addTempDocument = useDocumentStore((state) => state.addTempDocument);
  const clearAllTempDocuments = useDocumentStore((state) => state.clearAllTempDocuments);

  // Generate live region message for upload progress (for screen readers)
  const getUploadProgressMessage = () => {
    if (!isUploading && uploads.length === 0) return null;

    const totalUploads = uploads.length;
    const completeCount = uploads.filter((u) => u.status === 'complete').length;
    const failedCount = uploads.filter((u) => u.status === 'error').length;
    const inProgressCount = uploads.filter((u) => u.status === 'uploading').length;

    if (inProgressCount > 0) {
      const firstInProgress = uploads.find((u) => u.status === 'uploading');
      return `Uploading ${firstInProgress?.filename}: ${firstInProgress?.progress || 0}%`;
    }

    if (completeCount > 0 && completeCount === totalUploads) {
      return `Upload complete: ${completeCount} file${completeCount !== 1 ? 's' : ''} uploaded successfully`;
    }

    if (failedCount > 0) {
      return `Upload progress: ${completeCount} successful, ${failedCount} failed out of ${totalUploads}`;
    }

    return `Preparing to upload ${totalUploads} file${totalUploads !== 1 ? 's' : ''}`;
  };

  // Global drag-over detection
  useEffect(() => {
    const handleDragEnter = (e) => {
      e.preventDefault();
      dragCounterRef.current++;
      if (dragCounterRef.current === 1) {
        showModal();
      }
    };

    const handleDragLeave = (e) => {
      e.preventDefault();
      dragCounterRef.current--;
      if (dragCounterRef.current === 0) {
        setTimeout(() => {
          if (dragCounterRef.current === 0) {
            hideModal();
          }
        }, 100);
      }
    };

    const handleDragOver = (e) => {
      e.preventDefault();
    };

    const handleDrop = (e) => {
      e.preventDefault();
      dragCounterRef.current = 0;
    };

    document.body.addEventListener('dragenter', handleDragEnter);
    document.body.addEventListener('dragleave', handleDragLeave);
    document.body.addEventListener('dragover', handleDragOver);
    document.body.addEventListener('drop', handleDrop);

    return () => {
      document.body.removeEventListener('dragenter', handleDragEnter);
      document.body.removeEventListener('dragleave', handleDragLeave);
      document.body.removeEventListener('dragover', handleDragOver);
      document.body.removeEventListener('drop', handleDrop);
    };
  }, []);

  // Watch for WebSocket connection and process pending files
  useEffect(() => {
    if (isWebSocketConnected && pendingFilesRef.current) {
      console.log('✅ WebSocket connected, processing pending files');
      const files = pendingFilesRef.current;
      pendingFilesRef.current = null;
      uploadFiles(files);
    }
  }, [isWebSocketConnected]);

  // Listen for manual upload events from Upload button
  useEffect(() => {
    const handleManualUpload = (e) => {
      const files = e.detail?.files;
      if (files && files.length > 0) {
        // Check WebSocket connection before uploading
        if (!isWebSocketConnected) {
          console.warn('⚠️ WebSocket not connected, waiting for connection...');
          // Store files to process once connected
          pendingFilesRef.current = files;
          // Show modal with a "connecting" state
          showModal();
          setUploads([{
            filename: 'Connecting to server...',
            status: 'pending',
            progress: 0
          }]);
        } else {
          showModal();
          uploadFiles(files);
        }
      }
    };

    window.addEventListener('manualUpload', handleManualUpload);

    return () => {
      window.removeEventListener('manualUpload', handleManualUpload);
    };
  }, [isWebSocketConnected, showModal, setUploads]);

  // Hide modal
  const handleClose = () => {
    if (!isUploading) {
      hideModal();
    }
  };

  // Handle file drop
  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();

    // Reset drag counter to ensure modal can show again on next drag
    dragCounterRef.current = 0;

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      await uploadFiles(files);
    }
  };

  // Handle file input change
  const handleFileInputChange = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      await uploadFiles(files);
      e.target.value = ''; // Reset input
    }
  };

  // Upload files with pre-registration and duplicate detection
  const uploadFiles = async (files) => {
    setUploading(true);

    // Store files in map for later access
    const newFileMap = new Map();
    files.forEach(file => {
      newFileMap.set(file.name, file);
    });
    setFileMap(newFileMap);

    // Validate all files first
    const validatedFiles = files.map((file) => ({
      file,
      validation: validateFile(file),
    }));

    const validFiles = validatedFiles.filter((f) => f.validation.valid);
    const invalidFiles = validatedFiles.filter((f) => !f.validation.valid);

    // STEP 1: Pre-register all valid files via WebSocket (single round-trip)
    let registrations = [];
    try {
      console.log(`📋 Pre-registering ${validFiles.length} files...`);
      registrations = await registerUploadBatch(validFiles.map((f) => f.file));
      console.log(`✅ Received ${registrations.length} doc_ids from server`);
    } catch (error) {
      console.error('❌ Failed to register uploads:', error);
      // Initialize with error status
      const initialUploads = files.map((file, i) => ({
        filename: file.name,
        progress: 0,
        status: 'error',
        error: error.message || 'Failed to register upload',
      }));
      setUploads(initialUploads);
      setUploading(false);
      return;
    }

    // STEP 2: Initialize upload progress items with duplicate status
    const initialUploads = files.map((file, i) => {
      const validation = validatedFiles[i].validation;
      const registration = registrations.find(r => r.filename === file.name);

      if (!validation.valid) {
        return {
          filename: file.name,
          progress: 0,
          status: 'error',
          error: validation.error,
        };
      }

      if (registration && registration.is_duplicate) {
        return {
          filename: file.name,
          progress: 0,
          status: 'duplicate',
          isDuplicate: true,
          existingDoc: registration.existing_doc,
        };
      }

      return {
        filename: file.name,
        progress: 0,
        status: 'pending',
      };
    });
    setUploads(initialUploads);

    // Check if there are any duplicates - if so, wait for user decisions
    const hasDuplicates = initialUploads.some(u => u.status === 'duplicate');
    if (hasDuplicates) {
      console.log(`⚠️  Found ${initialUploads.filter(u => u.status === 'duplicate').length} duplicate files`);
      setUploading(false);
      // Don't proceed - wait for user to click Cancel or Continue on each file
      return;
    }

    // No duplicates - proceed with upload
    await proceedWithUpload(validFiles, registrations, files);
  };

  // Proceed with actual upload after duplicate check
  const proceedWithUpload = async (validFiles, registrations, allFiles, successCount = 0, failCount = 0) => {
    setUploading(true);

    // Get skipped files from uploads state (files marked as duplicate that user chose to skip)
    const skippedFiles = new Set(
      uploads
        .filter(u => u.status === 'duplicate' && !u.forceUpload)
        .map(u => u.filename)
    );

    // Filter out skipped files
    const filesToUpload = validFiles.filter((vf) => !skippedFiles.has(vf.file.name));
    const regsToUpload = registrations.filter((reg) => !skippedFiles.has(reg.filename));

    // STEP 2: Create temp documents immediately with real doc_ids
    regsToUpload.forEach((reg) => {
      console.log(`💾 Creating temp doc: ${reg.filename} → ${reg.doc_id.slice(0, 8)}...`);
      addTempDocument(reg.doc_id, reg.filename);
    });

    // STEP 3: Upload all files in parallel
    const uploadPromises = filesToUpload.map(async ({ file }, i) => {
      const registration = regsToUpload[i];
      const fileIndex = allFiles.indexOf(file);

      try {
        // Upload file with progress tracking
        await api.upload.uploadFile(file, (progress) => {
          updateUploadProgress(fileIndex, progress);
        });

        // Mark as complete
        updateUploadStatus(file.name, 'complete', null, 100);

        return { success: true, file: file.name };
      } catch (error) {
        // Mark as failed
        updateUploadStatus(file.name, 'error', error.message, 100);

        return { success: false, file: file.name, error: error.message };
      }
    });

    // Mark skipped files
    skippedFiles.forEach((filename) => {
      updateUploadStatus(filename, 'complete', 'Skipped (duplicate)', 100);
    });

    // Wait for all uploads to complete
    const results = await Promise.all(uploadPromises);
    successCount = results.filter((r) => r.success).length;
    failCount += results.filter((r) => !r.success).length;

    setUploading(false);

    // Call completion callback
    if (onUploadComplete) {
      onUploadComplete({ total: allFiles.length, successful: successCount, failed: failCount });
    }

    // Auto-hide after 0.5 seconds if all successful
    if (failCount === 0) {
      setTimeout(() => {
        hideModal();
      }, 500);
    }
  };

  // Handle cancel upload for duplicate file
  const handleCancelUpload = (filename) => {
    console.log(`❌ User cancelled duplicate: ${filename}`);
    updateUploadStatus(filename, 'cancelled', null, 100);
  };

  // Handle continue upload for duplicate file
  const handleContinueUpload = async (filename) => {
    console.log(`✅ User continuing with duplicate: ${filename}`);

    // Get the file object from the map
    const file = fileMap.get(filename);

    if (!file) {
      console.error(`Could not find file in map: ${filename}`);
      return;
    }

    setUploading(true);

    // Update status to uploading
    updateUploadStatus(filename, 'uploading', null, 0);

    try {
      // Clear any stale temp documents first
      clearAllTempDocuments();

      // Re-register with force_upload=true
      const registration = await registerUploadBatch([file], true);
      const reg = registration[0];

      // Create temp document
      console.log(`💾 Creating temp doc for forced upload: ${reg.filename} → ${reg.doc_id}`);
      addTempDocument(reg.doc_id, reg.filename);

      // Upload file with progress tracking
      await api.upload.uploadFile(file, (progress) => {
        updateUploadStatus(filename, 'uploading', null, progress);
      });

      // Mark as complete
      updateUploadStatus(filename, 'complete', null, 100);

      console.log(`✅ Upload complete: ${filename}`);

      // Trigger library refresh
      if (onUploadComplete) {
        onUploadComplete({ total: 1, successful: 1, failed: 0 });
      }
    } catch (error) {
      console.error(`❌ Upload failed: ${filename}`, error);
      updateUploadStatus(filename, 'error', error.message, 100);
    } finally {
      setUploading(false);

      // Check if all files are done
      const allDone = uploads.every(u =>
        ['complete', 'error', 'cancelled'].includes(u.status) ||
        u.filename === filename
      );

      if (allDone) {
        setTimeout(() => {
          hideModal();
        }, 500);
      }
    }
  };

  if (!isVisible) {
    return null;
  }

  return (
    <>
        <div
          className="upload-modal"
          role="dialog"
          aria-modal="true"
          aria-labelledby="upload-modal-title"
          style={{ display: 'flex' }}
        >
          <div className="upload-modal__backdrop" onClick={handleClose} />
          <div className="upload-modal__container">
            <div className="upload-modal__content">
              <h2 id="upload-modal-title" className="upload-modal__title">
                Drop files to upload
              </h2>

              {/* Drop zone (show when not uploading) */}
              {!isUploading && uploads.length === 0 && (
                <div
                  className="upload-modal__drop-zone"
                  onDrop={handleDrop}
                  onDragOver={(e) => e.preventDefault()}
                >
                  <svg
                    className="upload-modal__icon"
                    xmlns="http://www.w3.org/2000/svg"
                    width="48"
                    height="48"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                  </svg>
                  <p className="upload-modal__message">Drop your documents here</p>
                  <p className="upload-modal__hint">or</p>

                  <input
                    type="file"
                    id="upload-modal-file-input"
                    className="upload-modal__file-input"
                    multiple
                    accept={SUPPORTED_TYPES.join(',')}
                    onChange={handleFileInputChange}
                    aria-label="Select files to upload"
                  />
                  <label htmlFor="upload-modal-file-input" className="upload-modal__file-button">
                    Choose Files
                  </label>

                  <p className="upload-modal__hint">Supported: {formatSupportedTypes()} (max 100MB)</p>
                </div>
              )}

              {/* Progress list (show during/after upload) */}
              {uploads.length > 0 && (
                <div className="upload-modal__progress" style={{ display: 'block' }}>
                  <div className="upload-modal__progress-list" id="progress-list">
                    {uploads.map((upload, idx) => (
                      <UploadProgressItem
                        key={idx}
                        {...upload}
                        onCancelUpload={handleCancelUpload}
                        onContinueUpload={handleContinueUpload}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Close button */}
              <button
                className="upload-modal__close"
                onClick={handleClose}
                disabled={isUploading}
                aria-label="Cancel upload"
              >
                {isUploading ? 'Uploading...' : 'Cancel'}
              </button>
            </div>
          </div>
        </div>
    </>
  );
}

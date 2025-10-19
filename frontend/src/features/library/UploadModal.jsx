/**
 * UploadModal Component
 *
 * Drag-and-drop upload modal with progress tracking and multi-file support.
 * Shows on global drag-over, supports file validation, and provides upload feedback.
 *
 * Wave 2 - Library Agent
 */

import { useState, useEffect, useRef } from 'react';
import { api } from '../../services/api.js';
import { useDocumentStore } from '../../stores/useDocumentStore.js';

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
 */
function formatSupportedTypes() {
  return SUPPORTED_TYPES.map((ext) => ext.toUpperCase().replace('.', '')).join(', ');
}

/**
 * Validate file
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
 * @param {Object} props - Component props
 * @param {Function} [props.onUploadComplete] - Upload completion callback
 * @returns {JSX.Element} Upload modal
 */
export default function UploadModal({ onUploadComplete, registerUploadBatch }) {
  const [isVisible, setIsVisible] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploads, setUploads] = useState([]);
  const [fileMap, setFileMap] = useState(new Map()); // Store File objects by filename
  const dragCounterRef = useRef(0);

  const addTempDocument = useDocumentStore((state) => state.addTempDocument);
  const updateTempDocumentProgress = useDocumentStore(
    (state) => state.updateTempDocumentProgress
  );
  const setTempDocumentStatus = useDocumentStore((state) => state.setTempDocumentStatus);
  const clearAllTempDocuments = useDocumentStore((state) => state.clearAllTempDocuments);

  // Global drag-over detection
  useEffect(() => {
    const handleDragEnter = (e) => {
      e.preventDefault();
      dragCounterRef.current++;
      if (dragCounterRef.current === 1) {
        setIsVisible(true);
      }
    };

    const handleDragLeave = (e) => {
      e.preventDefault();
      dragCounterRef.current--;
      if (dragCounterRef.current === 0) {
        setTimeout(() => {
          if (dragCounterRef.current === 0) {
            setIsVisible(false);
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

  // Hide modal
  const handleClose = () => {
    if (!isUploading) {
      setIsVisible(false);
      setUploads([]);
      setFileMap(new Map()); // Clear file map
    }
  };

  // Handle file drop
  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();

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
    setIsUploading(true);

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
      setIsUploading(false);
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
      setIsUploading(false);
      // Don't proceed - wait for user to click Cancel or Continue on each file
      return;
    }

    // No duplicates - proceed with upload
    await proceedWithUpload(validFiles, registrations, files);
  };

  // Proceed with actual upload after duplicate check
  const proceedWithUpload = async (validFiles, registrations, allFiles, successCount, failCount) => {
    setIsUploading(true);

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
          setUploads((prev) =>
            prev.map((item, idx) => (idx === fileIndex ? { ...item, progress } : item))
          );
        });

        // Mark as complete
        setUploads((prev) =>
          prev.map((item, idx) =>
            idx === fileIndex ? { ...item, status: 'complete', progress: 100 } : item
          )
        );

        return { success: true, file: file.name };
      } catch (error) {
        // Mark as failed
        setUploads((prev) =>
          prev.map((item, idx) =>
            idx === fileIndex
              ? { ...item, status: 'error', error: error.message, progress: 100 }
              : item
          )
        );

        return { success: false, file: file.name, error: error.message };
      }
    });

    // Mark skipped files
    skippedFiles.forEach((filename) => {
      const fileIndex = allFiles.findIndex((f) => f.name === filename);
      if (fileIndex !== -1) {
        setUploads((prev) =>
          prev.map((item, idx) =>
            idx === fileIndex ? { ...item, status: 'complete', progress: 100, error: 'Skipped (duplicate)' } : item
          )
        );
      }
    });

    // Wait for all uploads to complete
    const results = await Promise.all(uploadPromises);
    successCount = results.filter((r) => r.success).length;
    failCount += results.filter((r) => !r.success).length;

    setIsUploading(false);

    // Call completion callback
    if (onUploadComplete) {
      onUploadComplete({ total: allFiles.length, successful: successCount, failed: failCount });
    }

    // Auto-hide after 0.5 seconds if all successful
    if (failCount === 0) {
      setTimeout(() => {
        setIsVisible(false);
        setUploads([]);
        setSkippedFiles(new Set());
        setForcedFiles(new Set());
      }, 500);
    }
  };

  // Handle cancel upload for duplicate file
  const handleCancelUpload = (filename) => {
    console.log(`❌ User cancelled duplicate: ${filename}`);
    setUploads((prev) =>
      prev.map((item) =>
        item.filename === filename
          ? { ...item, status: 'cancelled', progress: 100 }
          : item
      )
    );
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

    setIsUploading(true);

    // Update status to uploading
    setUploads((prev) =>
      prev.map((item) =>
        item.filename === filename
          ? { ...item, status: 'uploading', progress: 0 }
          : item
      )
    );

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
        setUploads((prev) =>
          prev.map((item) =>
            item.filename === filename ? { ...item, progress } : item
          )
        );
      });

      // Mark as complete
      setUploads((prev) =>
        prev.map((item) =>
          item.filename === filename
            ? { ...item, status: 'complete', progress: 100 }
            : item
        )
      );

      console.log(`✅ Upload complete: ${filename}`);

      // Trigger library refresh
      if (onUploadComplete) {
        onUploadComplete({ total: 1, successful: 1, failed: 0 });
      }
    } catch (error) {
      console.error(`❌ Upload failed: ${filename}`, error);
      setUploads((prev) =>
        prev.map((item) =>
          item.filename === filename
            ? { ...item, status: 'error', error: error.message, progress: 100 }
            : item
        )
      );
    } finally {
      setIsUploading(false);

      // Check if all files are done
      const allDone = uploads.every(u =>
        ['complete', 'error', 'cancelled'].includes(u.status) ||
        u.filename === filename
      );

      if (allDone) {
        setTimeout(() => {
          setIsVisible(false);
          setUploads([]);
          setFileMap(new Map());
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

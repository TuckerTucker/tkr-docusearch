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
function UploadProgressItem({ filename, progress, status, error }) {
  return (
    <div
      className={`upload-modal__progress-item ${
        status === 'complete' ? 'upload-modal__progress-item--complete' : ''
      } ${status === 'error' ? 'upload-modal__progress-item--failed' : ''}`}
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
            status === 'complete' ? '#10b981' : status === 'error' ? '#ef4444' : undefined,
        }}
      >
        {status === 'complete' && '✓ Complete'}
        {status === 'error' && `✗ ${error || 'Failed'}`}
        {status === 'uploading' && `${progress}%`}
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
export default function UploadModal({ onUploadComplete }) {
  const [isVisible, setIsVisible] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploads, setUploads] = useState([]);
  const dragCounterRef = useRef(0);

  const addTempDocument = useDocumentStore((state) => state.addTempDocument);
  const updateTempDocumentProgress = useDocumentStore(
    (state) => state.updateTempDocumentProgress
  );
  const setTempDocumentStatus = useDocumentStore((state) => state.setTempDocumentStatus);

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

  // Upload files
  const uploadFiles = async (files) => {
    setIsUploading(true);

    // Initialize upload progress items
    const initialUploads = files.map((file) => ({
      filename: file.name,
      progress: 0,
      status: 'uploading',
      error: null,
    }));
    setUploads(initialUploads);

    let successCount = 0;
    let failCount = 0;

    for (let i = 0; i < files.length; i++) {
      const file = files[i];

      // Validate file
      const validation = validateFile(file);
      if (!validation.valid) {
        setUploads((prev) =>
          prev.map((item, idx) =>
            idx === i
              ? { ...item, status: 'error', error: validation.error, progress: 100 }
              : item
          )
        );
        failCount++;
        continue;
      }

      try {
        // Upload file with progress tracking
        const result = await api.upload.uploadFile(file, (progress) => {
          setUploads((prev) =>
            prev.map((item, idx) => (idx === i ? { ...item, progress } : item))
          );
        });

        // Add to temp documents for optimistic UI
        addTempDocument(result.temp_id, file.name);

        // Mark as complete
        setUploads((prev) =>
          prev.map((item, idx) => (idx === i ? { ...item, status: 'complete', progress: 100 } : item))
        );

        successCount++;
      } catch (error) {
        // Mark as failed
        setUploads((prev) =>
          prev.map((item, idx) =>
            idx === i
              ? { ...item, status: 'error', error: error.message, progress: 100 }
              : item
          )
        );
        failCount++;
      }
    }

    setIsUploading(false);

    // Call completion callback
    if (onUploadComplete) {
      onUploadComplete({ total: files.length, successful: successCount, failed: failCount });
    }

    // Auto-hide after 2 seconds if all successful
    if (failCount === 0) {
      setTimeout(() => {
        setIsVisible(false);
        setUploads([]);
      }, 2000);
    }
  };

  if (!isVisible) {
    return null;
  }

  return (
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
                  <UploadProgressItem key={idx} {...upload} />
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
  );
}

/**
 * DuplicateConfirmationModal - Modal for handling duplicate file uploads
 *
 * Displays when files with matching filenames are detected during upload registration.
 * Allows users to skip duplicates or force upload anyway.
 *
 * Wave 2 - Upload Agent
 */

import { useState } from 'react';
import { formatDate, formatFileSize } from '../../utils/formatting.js';

/**
 * Duplicate confirmation modal component
 *
 * @param {Object} props
 * @param {Array<{filename: string, doc_id: string, is_duplicate: boolean, existing_doc?: Object}>} props.duplicates - Duplicate file registrations
 * @param {Function} props.onSkip - Callback when user skips a duplicate
 * @param {Function} props.onUploadAnyway - Callback when user forces upload
 * @param {Function} props.onCancel - Callback when user cancels all
 * @param {Function} props.onProceed - Callback when user proceeds with decisions
 * @param {boolean} props.isOpen - Whether modal is open
 */
export default function DuplicateConfirmationModal({
  duplicates = [],
  onSkip,
  onUploadAnyway,
  onCancel,
  onProceed,
  isOpen
}) {
  // Track user decisions for each duplicate
  const [decisions, setDecisions] = useState({});

  if (!isOpen || duplicates.length === 0) {
    return null;
  }

  // Handle individual file decision
  const handleFileDecision = (filename, decision) => {
    setDecisions(prev => ({
      ...prev,
      [filename]: decision
    }));
  };

  // Handle skip all
  const handleSkipAll = () => {
    duplicates.forEach(dup => {
      if (onSkip) {
        onSkip(dup.filename);
      }
    });
    setDecisions({});
  };

  // Handle upload all anyway
  const handleUploadAllAnyway = () => {
    duplicates.forEach(dup => {
      if (onUploadAnyway) {
        onUploadAnyway(dup.filename);
      }
    });
    setDecisions({});
  };

  // Handle cancel
  const handleCancel = () => {
    setDecisions({});
    if (onCancel) {
      onCancel();
    }
  };

  // Handle apply decisions and proceed
  const handleProceedClick = () => {
    // Apply any pending decisions
    duplicates.forEach(dup => {
      const decision = decisions[dup.filename];
      if (decision === 'skip' && onSkip) {
        onSkip(dup.filename);
      } else if (decision === 'upload' && onUploadAnyway) {
        onUploadAnyway(dup.filename);
      }
    });
    setDecisions({});

    // Notify parent to proceed with upload
    if (onProceed) {
      onProceed();
    }
  };

  // Check if all decisions are made
  const allDecisionsMade = duplicates.every(dup => decisions[dup.filename]);

  return (
    <div className="modal-overlay" onClick={handleCancel}>
      <div className="modal duplicate-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Duplicate Files Detected</h2>
          <button
            className="modal-close"
            onClick={handleCancel}
            aria-label="Close modal"
          >
            ×
          </button>
        </div>

        <div className="modal-body">
          <p className="duplicate-warning">
            {duplicates.length === 1
              ? 'This file already exists in your library.'
              : `${duplicates.length} files already exist in your library.`}
          </p>

          <div className="duplicate-list">
            {duplicates.map((dup) => {
              const existing = dup.existing_doc || {};
              const userDecision = decisions[dup.filename];

              return (
                <div key={dup.filename} className="duplicate-item">
                  <div className="duplicate-info">
                    <h3 className="duplicate-filename">{dup.filename}</h3>

                    {existing.date_added && (
                      <p className="duplicate-existing">
                        Already uploaded on {formatDate(existing.date_added)}
                      </p>
                    )}

                    {existing.file_type && (
                      <p className="duplicate-type">
                        File type: {existing.file_type.toUpperCase()}
                      </p>
                    )}

                    {dup.expected_size && (
                      <p className="duplicate-size">
                        Size: {formatFileSize(dup.expected_size)}
                      </p>
                    )}
                  </div>

                  <div className="duplicate-actions">
                    <button
                      className={`btn-secondary ${userDecision === 'skip' ? 'active' : ''}`}
                      onClick={() => handleFileDecision(dup.filename, 'skip')}
                    >
                      Skip
                    </button>
                    <button
                      className={`btn-outline ${userDecision === 'upload' ? 'active' : ''}`}
                      onClick={() => handleFileDecision(dup.filename, 'upload')}
                    >
                      Upload Anyway
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="modal-footer">
          <div className="modal-footer-left">
            <button className="btn-secondary" onClick={handleSkipAll}>
              Skip All
            </button>
            <button className="btn-outline" onClick={handleUploadAllAnyway}>
              Upload All Anyway
            </button>
          </div>

          <div className="modal-footer-right">
            <button className="btn-secondary" onClick={handleCancel}>
              Cancel
            </button>
            <button className="btn-primary" onClick={handleProceedClick}>
              Proceed
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Upload Logic Module
 *
 * Handles file upload functionality including drag-and-drop, validation, and
 * Copyparty upload client.
 *
 * Provider: upload-logic-agent (Wave 3)
 * Contract: ui-html.contract.md
 */

import { validateFile, getFormatType, estimateProcessingTime, formatFileSize, getFormatName, initializeValidator, getSupportedFormats } from './modules/file-validator.js';
import { uploadToCopyparty, uploadMultipleFiles, isTempDocId, resolveDocId } from './modules/copyparty-client.js';
import { initializeHealthMonitoring } from './modules/worker-health.js';
import { startMonitoring } from './monitor.js';

/**
 * Initialize upload functionality.
 */
export async function initializeUpload() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');

    if (!dropZone || !fileInput) {
        console.error('Upload UI elements not found');
        return;
    }

    // Initialize file validator with worker config
    await initializeValidator();

    // Update HTML accept attribute with dynamic formats
    updateFileInputAccept(fileInput);

    // Initialize drag-and-drop
    setupDragAndDrop(dropZone, fileInput);

    // Initialize file input
    setupFileInput(fileInput);

    // Initialize worker health monitoring
    initializeHealthMonitoring();

    console.log('Upload module initialized');
}

/**
 * Update file input accept attribute with supported formats from worker config.
 *
 * @param {HTMLInputElement} fileInput - File input element
 */
function updateFileInputAccept(fileInput) {
    const formats = getSupportedFormats();
    const acceptString = formats.map(ext => `.${ext}`).join(',');
    fileInput.setAttribute('accept', acceptString);
    console.log(`Updated file input accept attribute with ${formats.length} formats`);
}

/**
 * Setup drag-and-drop functionality.
 *
 * @param {HTMLElement} dropZone - Drop zone element
 * @param {HTMLInputElement} fileInput - File input element
 */
function setupDragAndDrop(dropZone, fileInput) {
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    // Highlight drop zone when dragging over
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add('drop-zone--active');
        }, false);
    });

    // Remove highlight when dragging away
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('drop-zone--active');
        }, false);
    });

    // Handle dropped files
    dropZone.addEventListener('drop', (e) => {
        const files = Array.from(e.dataTransfer.files);
        handleFiles(files);
    }, false);

    // Handle click to trigger file input
    dropZone.addEventListener('click', (e) => {
        // Don't trigger if clicking the label (it handles the input itself)
        if (e.target.tagName !== 'LABEL') {
            fileInput.click();
        }
    });
}

/**
 * Setup file input functionality.
 *
 * @param {HTMLInputElement} fileInput - File input element
 */
function setupFileInput(fileInput) {
    fileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        handleFiles(files);
        // Clear input so same file can be selected again
        fileInput.value = '';
    });
}

/**
 * Prevent default drag behaviors.
 *
 * @param {Event} e - Event object
 */
function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

/**
 * Handle selected/dropped files.
 *
 * @param {File[]} files - Array of files to process
 */
async function handleFiles(files) {
    if (files.length === 0) {
        return;
    }

    console.log(`Processing ${files.length} file(s)`);

    // Validate all files
    const validationResults = files.map(file => ({
        file,
        validation: validateFile(file)
    }));

    // Separate valid and invalid files
    const validFiles = validationResults
        .filter(r => r.validation.valid)
        .map(r => r.file);

    const invalidFiles = validationResults
        .filter(r => !r.validation.valid);

    // Show errors for invalid files
    invalidFiles.forEach(({ file, validation }) => {
        showToast('error', `${file.name}: ${validation.error}`);
    });

    // Show warnings for large files
    validationResults
        .filter(r => r.validation.valid && r.validation.warning)
        .forEach(({ file, validation }) => {
            showToast('warning', `${file.name}: ${validation.warning}`);
        });

    // Upload valid files
    if (validFiles.length > 0) {
        uploadFiles(validFiles);
    }
}

/**
 * Upload files to Copyparty.
 *
 * @param {File[]} files - Array of files to upload
 */
async function uploadFiles(files) {
    const abortController = new AbortController();

    try {
        const results = await uploadMultipleFiles(files, {
            onFileProgress: (file, percentage, loaded, total) => {
                updateFileUploadProgress(file, percentage, loaded, total);
            },
            onOverallProgress: (completed, total, percentage) => {
                console.log(`Overall progress: ${completed}/${total} (${percentage.toFixed(1)}%)`);
            },
            maxConcurrent: 3,
            signal: abortController.signal
        });

        // Process results
        results.forEach(result => {
            if (result.success) {
                handleUploadSuccess(result.file, result.doc_id);
            } else {
                handleUploadError(result.file, result.error);
            }
        });

    } catch (error) {
        console.error('Upload error:', error);
        showToast('error', `Upload failed: ${error.message}`);
    }
}

/**
 * Update file upload progress in UI.
 *
 * @param {File} file - File being uploaded
 * @param {number} percentage - Upload percentage (0-100)
 * @param {number} loaded - Bytes uploaded
 * @param {number} total - Total bytes
 */
function updateFileUploadProgress(file, percentage, loaded, total) {
    // This will be enhanced when we integrate with queue manager
    console.log(`${file.name}: ${percentage.toFixed(1)}% (${formatFileSize(loaded)} / ${formatFileSize(total)})`);

    // Find or create queue item for this file
    const queueItem = findOrCreateQueueItem(file);

    // Update progress UI
    updateQueueItemProgress(queueItem, {
        status: 'uploading',
        progress: percentage / 100,
        message: `Uploading... ${formatFileSize(loaded)} / ${formatFileSize(total)}`
    });
}

/**
 * Handle successful upload.
 *
 * @param {File} file - Uploaded file
 * @param {string} docId - Document ID (may be temporary)
 */
async function handleUploadSuccess(file, docId) {
    console.log(`Upload successful: ${file.name} (doc_id: ${docId})`);

    // Find queue item
    const queueItem = findOrCreateQueueItem(file);

    // If doc_id is temporary, mark as "queued" and let monitor.js resolve it
    if (isTempDocId(docId)) {
        updateQueueItemProgress(queueItem, {
            status: 'queued',
            progress: 0,
            message: 'Queued for processing...',
            doc_id: docId,
            filename: file.name
        });

        // Start monitoring - will timeout after 30s if not found
        startMonitoring(docId, file.name);
    } else {
        // Real doc_id received
        updateQueueItemProgress(queueItem, {
            status: 'processing',
            progress: 0,
            message: 'Processing started...',
            doc_id: docId,
            filename: file.name
        });

        // Start monitoring for status updates
        startMonitoring(docId, file.name);
    }

    showToast('success', `${file.name} uploaded successfully`);
}

/**
 * Handle upload error.
 *
 * @param {File} file - File that failed to upload
 * @param {string} error - Error message
 */
function handleUploadError(file, error) {
    console.error(`Upload failed: ${file.name}`, error);

    // Find queue item
    const queueItem = findOrCreateQueueItem(file);

    // Update to failed state
    updateQueueItemProgress(queueItem, {
        status: 'failed',
        progress: 0,
        message: `Upload failed: ${error}`
    });

    showToast('error', `Failed to upload ${file.name}: ${error}`);
}

/**
 * Find or create queue item for a file.
 *
 * @param {File} file - File object
 * @returns {HTMLElement} Queue item element
 */
function findOrCreateQueueItem(file) {
    const queueItems = document.getElementById('queue-items');
    const queueEmpty = document.getElementById('queue-empty');

    if (!queueItems) {
        console.error('Queue items container not found');
        return null;
    }

    // Try to find existing item by filename
    const existingItem = Array.from(queueItems.children).find(item => {
        const filenameEl = item.querySelector('.queue-item-filename');
        return filenameEl && filenameEl.textContent === file.name;
    });

    if (existingItem) {
        return existingItem;
    }

    // Hide empty state
    if (queueEmpty) {
        queueEmpty.style.display = 'none';
    }

    // Show queue section
    const queueSection = document.getElementById('queue-section');
    if (queueSection) {
        queueSection.style.display = 'block';
    }

    // Create new queue item
    const item = document.createElement('article');
    item.className = 'queue-item queue-item--processing';

    // Get file metadata
    const formatType = getFormatType(file);
    const formatName = getFormatName(file);
    const fileSize = formatFileSize(file.size);
    const estimatedTime = estimateProcessingTime(file);

    item.innerHTML = `
        <div class="queue-item-header">
            <span class="queue-item-filename">${escapeHtml(file.name)}</span>
            <span class="queue-item-status">Preparing...</span>
        </div>
        <div class="queue-item-progress">
            <div class="progress-bar">
                <div class="progress-fill" style="width: 0%"></div>
            </div>
            <span class="progress-text">0%</span>
        </div>
        <div class="queue-item-details">
            <span class="queue-item-detail">${formatName}</span>
            <span class="queue-item-detail">${fileSize}</span>
            <span class="queue-item-detail">Est. ${Math.ceil(estimatedTime)}s</span>
        </div>
    `;

    queueItems.insertBefore(item, queueItems.firstChild);

    return item;
}

/**
 * Update queue item progress.
 *
 * @param {HTMLElement} queueItem - Queue item element
 * @param {Object} data - Progress data
 * @param {string} data.status - Status ('uploading', 'queued', 'processing', 'completed', 'failed')
 * @param {number} data.progress - Progress (0-1)
 * @param {string} data.message - Status message
 * @param {string} [data.doc_id] - Document ID
 * @param {string} [data.filename] - Filename
 */
function updateQueueItemProgress(queueItem, data) {
    if (!queueItem) {
        return;
    }

    const { status, progress, message, doc_id, filename } = data;

    // Update status class
    queueItem.className = 'queue-item';
    if (status === 'uploading' || status === 'queued' || status === 'processing') {
        queueItem.classList.add('queue-item--processing');
    } else if (status === 'completed') {
        queueItem.classList.add('queue-item--completed');
    } else if (status === 'failed') {
        queueItem.classList.add('queue-item--failed');
    }

    // Update status text
    const statusEl = queueItem.querySelector('.queue-item-status');
    if (statusEl) {
        statusEl.textContent = message || status;
    }

    // Update progress bar
    const progressFill = queueItem.querySelector('.progress-fill');
    const progressText = queueItem.querySelector('.progress-text');
    if (progressFill && progressText) {
        const percentage = Math.round(progress * 100);
        progressFill.style.width = `${percentage}%`;
        progressText.textContent = `${percentage}%`;
    }

    // Store doc_id and filename as data attributes for monitor.js
    if (doc_id) {
        queueItem.setAttribute('data-doc-id', doc_id);
    }
    if (filename) {
        queueItem.setAttribute('data-filename', filename);
    }
}

/**
 * Show toast notification.
 *
 * @param {string} type - Toast type ('success', 'error', 'warning')
 * @param {string} message - Toast message
 */
function showToast(type, message) {
    const container = document.getElementById('toast-container');
    if (!container) {
        console.warn('Toast container not found');
        return;
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;

    const messageEl = document.createElement('div');
    messageEl.className = 'toast-message';
    messageEl.textContent = message;

    toast.appendChild(messageEl);
    container.appendChild(toast);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        toast.classList.add('toast--hiding');
        setTimeout(() => {
            container.removeChild(toast);
        }, 300); // Match CSS transition duration
    }, 5000);
}

/**
 * Escape HTML to prevent XSS.
 *
 * @param {string} str - String to escape
 * @returns {string} Escaped string
 */
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeUpload);
} else {
    initializeUpload();
}

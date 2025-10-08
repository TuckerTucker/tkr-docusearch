/**
 * Copyparty Upload Client Module
 *
 * Handles file uploads to Copyparty server with progress tracking.
 *
 * Provider: upload-logic-agent
 * Contract: ui-html.contract.md
 */

/**
 * Configuration for Copyparty upload.
 */
const COPYPARTY_CONFIG = {
    // Copyparty upload endpoint
    uploadUrl: 'http://localhost:8000',
    // Upload path (relative to Copyparty root) - leave empty to upload to root
    // The volume mapping in Docker determines the actual directory
    uploadPath: '',
    // Chunk size for upload progress tracking (1MB)
    chunkSize: 1024 * 1024,
    // Maximum retries on upload failure
    maxRetries: 3,
    // Retry delay in milliseconds
    retryDelay: 1000,
    // Authentication credentials
    // Format: {username: 'user', password: 'pass'} or null for anonymous
    auth: {
        username: 'admin',
        password: 'admin'
    }
};

/**
 * Upload a file to Copyparty server.
 *
 * @param {File} file - File object to upload
 * @param {Object} options - Upload options
 * @param {Function} options.onProgress - Progress callback (percentage, bytes uploaded, total bytes)
 * @param {AbortSignal} options.signal - Abort signal for cancellation
 * @returns {Promise<{success: boolean, doc_id?: string, error?: string}>} Upload result
 */
export async function uploadToCopyparty(file, options = {}) {
    const { onProgress, signal } = options;

    // Create FormData for multipart upload
    // Copyparty expects "act=bput" for basic PUT uploads
    const formData = new FormData();
    formData.append('act', 'bput');
    formData.append('f', file);

    // Build upload URL
    const uploadUrl = COPYPARTY_CONFIG.uploadPath
        ? `${COPYPARTY_CONFIG.uploadUrl}/${COPYPARTY_CONFIG.uploadPath}`
        : COPYPARTY_CONFIG.uploadUrl;

    // Attempt upload with retries
    let lastError = null;
    for (let attempt = 1; attempt <= COPYPARTY_CONFIG.maxRetries; attempt++) {
        try {
            const result = await attemptUpload(uploadUrl, formData, {
                onProgress,
                signal,
                attempt,
                maxRetries: COPYPARTY_CONFIG.maxRetries
            });

            return { success: true, doc_id: result.doc_id };
        } catch (error) {
            lastError = error;

            // Check if upload was aborted
            if (error.name === 'AbortError') {
                return {
                    success: false,
                    error: 'Upload cancelled'
                };
            }

            // Check if this is the last retry
            if (attempt === COPYPARTY_CONFIG.maxRetries) {
                break;
            }

            // Wait before retrying
            await sleep(COPYPARTY_CONFIG.retryDelay * attempt);
        }
    }

    // All retries failed
    return {
        success: false,
        error: lastError?.message || 'Upload failed after multiple retries'
    };
}

/**
 * Attempt a single upload.
 *
 * @private
 * @param {string} url - Upload URL
 * @param {FormData} formData - Form data with file
 * @param {Object} options - Upload options
 * @returns {Promise<{doc_id: string}>} Upload result
 * @throws {Error} Upload error
 */
async function attemptUpload(url, formData, options = {}) {
    const { onProgress, signal, attempt, maxRetries } = options;

    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        // Track upload progress
        if (onProgress) {
            xhr.upload.addEventListener('progress', (event) => {
                if (event.lengthComputable) {
                    const percentage = (event.loaded / event.total) * 100;
                    onProgress(percentage, event.loaded, event.total);
                }
            });
        }

        // Handle successful upload
        xhr.addEventListener('load', () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    // Parse response to extract doc_id
                    const response = parseUploadResponse(xhr.responseText);
                    resolve(response);
                } catch (error) {
                    reject(new Error(`Failed to parse upload response: ${error.message}`));
                }
            } else {
                reject(new Error(`Upload failed with status ${xhr.status}: ${xhr.statusText}`));
            }
        });

        // Handle upload error
        xhr.addEventListener('error', () => {
            const attemptInfo = maxRetries > 1 ? ` (attempt ${attempt}/${maxRetries})` : '';
            reject(new Error(`Network error during upload${attemptInfo}`));
        });

        // Handle upload abort
        xhr.addEventListener('abort', () => {
            const error = new Error('Upload aborted');
            error.name = 'AbortError';
            reject(error);
        });

        // Handle timeout
        xhr.addEventListener('timeout', () => {
            const attemptInfo = maxRetries > 1 ? ` (attempt ${attempt}/${maxRetries})` : '';
            reject(new Error(`Upload timeout${attemptInfo}`));
        });

        // Set timeout (30 seconds per 10MB, minimum 30s)
        const file = formData.get('f');
        const timeoutMs = Math.max(30000, Math.ceil(file.size / (10 * 1024 * 1024)) * 30000);
        xhr.timeout = timeoutMs;

        // Link abort signal
        if (signal) {
            signal.addEventListener('abort', () => {
                xhr.abort();
            });
        }

        // Send request
        xhr.open('POST', url);

        // Add HTTP Basic Authentication if configured
        if (COPYPARTY_CONFIG.auth) {
            const credentials = btoa(`${COPYPARTY_CONFIG.auth.username}:${COPYPARTY_CONFIG.auth.password}`);
            xhr.setRequestHeader('Authorization', `Basic ${credentials}`);
        }

        xhr.send(formData);
    });
}

/**
 * Parse Copyparty upload response to extract doc_id.
 *
 * Copyparty webhook will trigger processing and create a doc_id.
 * This function handles different response formats.
 *
 * @private
 * @param {string} responseText - Raw response text from Copyparty
 * @returns {Object} Parsed response with doc_id
 * @throws {Error} Parse error
 */
function parseUploadResponse(responseText) {
    // Copyparty returns different response formats depending on configuration
    // Try JSON first
    try {
        const json = JSON.parse(responseText);
        if (json.doc_id) {
            return { doc_id: json.doc_id };
        }
    } catch (e) {
        // Not JSON, try other formats
    }

    // If no doc_id in response, generate one from filename + timestamp
    // The webhook will create the actual doc_id, but we need a temporary ID
    // for UI tracking until we poll the status API
    const tempId = generateTempDocId();

    return { doc_id: tempId };
}

/**
 * Generate a temporary document ID for tracking uploads.
 *
 * This is used when Copyparty doesn't return a doc_id immediately.
 * The UI will poll the status API to get the real doc_id once processing starts.
 *
 * @private
 * @returns {string} Temporary document ID (prefixed with 'temp-')
 */
function generateTempDocId() {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 15);
    return `temp-${timestamp}-${random}`;
}

/**
 * Check if a doc_id is temporary.
 *
 * @param {string} docId - Document ID to check
 * @returns {boolean} True if doc_id is temporary
 */
export function isTempDocId(docId) {
    return docId.startsWith('temp-');
}

/**
 * Poll the status API to resolve a temporary doc_id to a real one.
 *
 * @param {string} filename - Original filename
 * @param {Object} options - Polling options
 * @param {number} options.maxAttempts - Maximum polling attempts (default: 30)
 * @param {number} options.interval - Polling interval in ms (default: 1000)
 * @param {AbortSignal} options.signal - Abort signal for cancellation
 * @returns {Promise<{doc_id: string}>} Real document ID
 * @throws {Error} If polling times out or fails
 */
export async function resolveDocId(filename, options = {}) {
    const {
        maxAttempts = 30,
        interval = 1000,
        signal
    } = options;

    // Poll the queue endpoint to find the document by filename
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        // Check if aborted
        if (signal?.aborted) {
            throw new Error('Polling cancelled');
        }

        try {
            const response = await fetch('http://localhost:8002/status/queue');
            if (!response.ok) {
                throw new Error(`Queue endpoint returned ${response.status}`);
            }

            const data = await response.json();

            // Find document by filename
            const allItems = [
                ...(data.active || []),
                ...(data.completed || [])
            ];

            const item = allItems.find(i => i.filename === filename);
            if (item && item.doc_id && !isTempDocId(item.doc_id)) {
                return { doc_id: item.doc_id };
            }
        } catch (error) {
            console.warn(`Polling attempt ${attempt} failed:`, error);
        }

        // Wait before next attempt
        await sleep(interval);
    }

    throw new Error(`Failed to resolve doc_id for ${filename} after ${maxAttempts} attempts`);
}

/**
 * Sleep for a specified duration.
 *
 * @private
 * @param {number} ms - Milliseconds to sleep
 * @returns {Promise<void>}
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Upload multiple files concurrently with progress tracking.
 *
 * @param {File[]} files - Array of files to upload
 * @param {Object} options - Upload options
 * @param {Function} options.onFileProgress - Per-file progress callback (file, percentage, bytes, total)
 * @param {Function} options.onOverallProgress - Overall progress callback (completed, total, percentage)
 * @param {number} options.maxConcurrent - Maximum concurrent uploads (default: 3)
 * @param {AbortSignal} options.signal - Abort signal for cancellation
 * @returns {Promise<Array<{file: File, success: boolean, doc_id?: string, error?: string}>>} Upload results
 */
export async function uploadMultipleFiles(files, options = {}) {
    const {
        onFileProgress,
        onOverallProgress,
        maxConcurrent = 3,
        signal
    } = options;

    const results = [];
    let completed = 0;

    // Create upload queue
    const queue = [...files];
    const activeUploads = new Set();

    return new Promise((resolve, reject) => {
        // Check if already aborted
        if (signal?.aborted) {
            reject(new Error('Upload cancelled'));
            return;
        }

        // Process next file in queue
        const processNext = async () => {
            if (queue.length === 0 && activeUploads.size === 0) {
                // All uploads complete
                resolve(results);
                return;
            }

            if (queue.length === 0 || activeUploads.size >= maxConcurrent) {
                // Queue empty or max concurrent reached
                return;
            }

            const file = queue.shift();
            activeUploads.add(file);

            try {
                const result = await uploadToCopyparty(file, {
                    onProgress: (percentage, loaded, total) => {
                        if (onFileProgress) {
                            onFileProgress(file, percentage, loaded, total);
                        }
                    },
                    signal
                });

                results.push({
                    file,
                    success: result.success,
                    doc_id: result.doc_id,
                    error: result.error
                });
            } catch (error) {
                results.push({
                    file,
                    success: false,
                    error: error.message
                });
            } finally {
                activeUploads.delete(file);
                completed++;

                // Update overall progress
                if (onOverallProgress) {
                    const percentage = (completed / files.length) * 100;
                    onOverallProgress(completed, files.length, percentage);
                }

                // Process next file
                processNext();
            }
        };

        // Handle abort
        if (signal) {
            signal.addEventListener('abort', () => {
                reject(new Error('Upload cancelled'));
            });
        }

        // Start initial batch
        for (let i = 0; i < maxConcurrent; i++) {
            processNext();
        }
    });
}

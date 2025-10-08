/**
 * Processing Monitor Module
 *
 * Monitors document processing status via status API and emits updates.
 *
 * Provider: monitoring-logic-agent
 * Contract: status-api.contract.md
 */

/**
 * ProcessingMonitor class.
 *
 * Monitors processing status for documents and provides real-time updates.
 */
export class ProcessingMonitor {
    /**
     * Create a new ProcessingMonitor instance.
     *
     * @param {Object} options - Monitor options
     * @param {string} options.apiBaseUrl - Base URL for status API (default: http://localhost:8002)
     * @param {number} options.pollInterval - Polling interval in ms (default: 2000)
     * @param {Function} options.onStatusUpdate - Callback for status updates (doc_id, status)
     * @param {Function} options.onError - Callback for errors (error)
     * @param {Object} options.queueManager - QueueManager instance for UI updates
     */
    constructor(options = {}) {
        this.apiBaseUrl = options.apiBaseUrl || 'http://localhost:8002';
        this.pollInterval = options.pollInterval || 2000; // 2 seconds
        this.onStatusUpdate = options.onStatusUpdate || (() => {});
        this.onError = options.onError || ((error) => console.error('Monitor error:', error));
        this.queueManager = options.queueManager || null;

        // Tracked documents: Map<doc_id, {status, lastUpdate, startTime}>
        this.trackedDocs = new Map();

        // Timeout for temp doc_id resolution (30 seconds)
        this.tempDocIdTimeout = 30000;

        // Polling state
        this.isPolling = false;
        this.pollTimer = null;
        this.abortController = null;
    }

    /**
     * Start monitoring a document.
     *
     * @param {string} docId - Document ID to monitor
     * @param {string} [filename] - Optional filename for temp doc_id resolution
     */
    startMonitoring(docId, filename = null) {
        if (!docId) {
            console.warn('Cannot monitor document without doc_id');
            return;
        }

        // Add to tracked documents
        this.trackedDocs.set(docId, {
            status: 'unknown',
            lastUpdate: Date.now(),
            startTime: Date.now(),
            filename: filename
        });

        // Start polling if not already running
        if (!this.isPolling) {
            this.startPolling();
        }
    }

    /**
     * Stop monitoring a document.
     *
     * @param {string} docId - Document ID to stop monitoring
     */
    stopMonitoring(docId) {
        this.trackedDocs.delete(docId);

        // Stop polling if no more documents to track
        if (this.trackedDocs.size === 0) {
            this.stopPolling();
        }
    }

    /**
     * Start polling for status updates.
     */
    startPolling() {
        if (this.isPolling) {
            return;
        }

        this.isPolling = true;
        this.abortController = new AbortController();

        // Initial poll
        this.pollStatus();

        // Schedule periodic polling
        this.pollTimer = setInterval(() => {
            this.pollStatus();
        }, this.pollInterval);

        console.log('Processing monitor started');
    }

    /**
     * Stop polling for status updates.
     */
    stopPolling() {
        if (!this.isPolling) {
            return;
        }

        this.isPolling = false;

        // Cancel any in-flight requests
        if (this.abortController) {
            this.abortController.abort();
            this.abortController = null;
        }

        // Clear polling timer
        if (this.pollTimer) {
            clearInterval(this.pollTimer);
            this.pollTimer = null;
        }

        console.log('Processing monitor stopped');
    }

    /**
     * Poll status API for all tracked documents.
     */
    async pollStatus() {
        if (!this.isPolling || this.trackedDocs.size === 0) {
            return;
        }

        try {
            // Check for timed out temp doc_ids
            this.checkTimeouts();

            // Fetch queue status
            const queueData = await this.fetchQueueStatus();

            // Update tracked documents with queue data
            this.updateFromQueue(queueData);

            // For documents not in queue, fetch individual status
            await this.updateMissingDocs();

        } catch (error) {
            // Only report errors that aren't from abort
            if (error.name !== 'AbortError') {
                this.onError(error);
            }
        }
    }

    /**
     * Check for timed out temp doc_ids.
     *
     * If a temp doc_id hasn't been resolved within the timeout period,
     * mark it as failed (likely rejected by webhook).
     */
    checkTimeouts() {
        const now = Date.now();

        for (const [docId, tracking] of this.trackedDocs.entries()) {
            // Check if this is a temp doc_id
            if (docId.startsWith('temp-')) {
                const elapsed = now - tracking.startTime;

                // If timeout exceeded and still unknown/queued
                if (elapsed > this.tempDocIdTimeout &&
                    (tracking.status === 'unknown' || tracking.status === 'queued')) {

                    console.warn(`Temp doc_id timeout: ${docId} (${elapsed}ms)`);

                    // Mark as failed - likely unsupported file type
                    this.onStatusUpdate(docId, {
                        status: 'failed',
                        progress: 0,
                        stage: 'Upload rejected',
                        error: 'File type not supported or upload rejected by worker',
                        elapsed_time: elapsed / 1000
                    });

                    // Stop tracking this document
                    this.stopMonitoring(docId);
                }
            }
        }
    }

    /**
     * Fetch queue status from API.
     *
     * @returns {Promise<Object>} Queue data {active: [], completed: []}
     */
    async fetchQueueStatus() {
        const url = `${this.apiBaseUrl}/status/queue`;
        const response = await fetch(url, {
            signal: this.abortController?.signal
        });

        if (!response.ok) {
            throw new Error(`Queue endpoint returned ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }

    /**
     * Fetch individual document status.
     *
     * @param {string} docId - Document ID
     * @returns {Promise<Object|null>} Status data or null if not found
     */
    async fetchDocStatus(docId) {
        const url = `${this.apiBaseUrl}/status/${docId}`;

        try {
            const response = await fetch(url, {
                signal: this.abortController?.signal
            });

            if (response.status === 404) {
                return null; // Document not found
            }

            if (!response.ok) {
                throw new Error(`Status endpoint returned ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            if (error.name === 'AbortError') {
                throw error; // Re-throw abort errors
            }
            console.warn(`Failed to fetch status for ${docId}:`, error);
            return null;
        }
    }

    /**
     * Update tracked documents from queue data.
     *
     * @param {Object} queueData - Queue data {queue: [], total: number, active: number, completed: number, failed: number}
     */
    updateFromQueue(queueData) {
        const { queue = [] } = queueData;

        console.log(`[DEBUG] Queue has ${queue.length} items, tracking ${this.trackedDocs.size} docs`);

        // Update each tracked document if found in queue
        for (const [docId, trackedData] of this.trackedDocs.entries()) {
            let queueItem = queue.find(item => item.doc_id === docId);

            // If not found by doc_id and this is a temp doc_id, try matching by filename
            if (!queueItem && docId.startsWith('temp-') && trackedData.filename) {
                console.log(`[DEBUG] Looking for temp doc_id ${docId} with filename: ${trackedData.filename}`);
                console.log(`[DEBUG] Queue filenames:`, queue.map(item => item.filename));

                // Try exact match first
                queueItem = queue.find(item => item.filename === trackedData.filename);

                // If no exact match, try prefix match (Copyparty appends timestamp suffix)
                if (!queueItem) {
                    queueItem = queue.find(item => item.filename.startsWith(trackedData.filename));
                    if (queueItem) {
                        console.log(`Resolved temp doc_id ${docId} to real doc_id ${queueItem.doc_id} via prefix match (Copyparty renamed file)`);
                    }
                } else {
                    console.log(`Resolved temp doc_id ${docId} to real doc_id ${queueItem.doc_id} via exact filename match`);
                }

                if (queueItem) {
                    // Remove temp doc_id from queue UI
                    // Note: Upload.js creates queue items with direct DOM manipulation,
                    // so they're not in queueManager.items. We need to find and remove manually.
                    console.log(`[DEBUG] Removing temp doc_id entry from UI: ${docId}`);

                    // Find the queue item by looking for the filename in the DOM
                    const queueItemsContainer = document.getElementById('queue-items');
                    if (queueItemsContainer) {
                        const items = Array.from(queueItemsContainer.children);
                        // Find item with matching filename and "Queued for processing" status
                        const tempItem = items.find(item => {
                            const filenameEl = item.querySelector('.queue-item-filename');
                            const statusEl = item.querySelector('.queue-item-status');
                            return filenameEl &&
                                   filenameEl.textContent === trackedData.filename &&
                                   statusEl &&
                                   statusEl.textContent.includes('Queued for processing');
                        });

                        if (tempItem) {
                            console.log(`[DEBUG] Found and removing temp queue item for: ${trackedData.filename}`);
                            tempItem.remove();
                        } else {
                            console.log(`[DEBUG] Could not find temp queue item in DOM for: ${trackedData.filename}`);
                        }
                    }

                    // Switch to tracking the real doc_id
                    this.trackedDocs.delete(docId);
                    this.trackedDocs.set(queueItem.doc_id, {
                        status: 'resolving', // Different status to force UI update
                        lastUpdate: Date.now(),
                        startTime: trackedData.startTime,
                        filename: trackedData.filename
                    });

                    // Update UI with real doc_id (will trigger because status differs)
                    this.updateDocStatus(queueItem.doc_id, queueItem);

                    // Continue with this doc_id for the rest of the loop
                    continue;
                } else {
                    console.log(`[DEBUG] No filename match found for ${trackedData.filename}`);
                }
            }

            if (queueItem) {
                this.updateDocStatus(docId, queueItem);
            }
        }
    }

    /**
     * Update documents not found in queue (fetch individually).
     */
    async updateMissingDocs() {
        const promises = [];

        for (const [docId, trackedData] of this.trackedDocs.entries()) {
            // Only fetch if we haven't updated recently (avoid duplicate fetches)
            const timeSinceUpdate = Date.now() - trackedData.lastUpdate;
            if (timeSinceUpdate > this.pollInterval) {
                promises.push(this.fetchAndUpdateDoc(docId));
            }
        }

        await Promise.all(promises);
    }

    /**
     * Fetch and update a single document's status.
     *
     * @param {string} docId - Document ID
     */
    async fetchAndUpdateDoc(docId) {
        const statusData = await this.fetchDocStatus(docId);

        if (statusData) {
            this.updateDocStatus(docId, statusData);
        } else {
            // Document not found - mark as unknown
            this.updateDocStatus(docId, {
                doc_id: docId,
                status: 'not_found',
                progress: 0,
                error: 'Document not found in queue'
            });
        }
    }

    /**
     * Update a document's status and notify listeners.
     *
     * @param {string} docId - Document ID
     * @param {Object} statusData - Status data from API
     */
    updateDocStatus(docId, statusData) {
        const trackedData = this.trackedDocs.get(docId);
        if (!trackedData) {
            return; // No longer tracking this document
        }

        const oldStatus = trackedData.status;
        const newStatus = statusData.status;

        // Update tracked data
        trackedData.status = newStatus;
        trackedData.lastUpdate = Date.now();

        // Notify listener if status changed
        if (oldStatus !== newStatus) {
            console.log(`Status update: ${docId} -> ${newStatus}`);
            this.onStatusUpdate(docId, statusData);
        }

        // Stop monitoring completed/failed documents after a delay
        if (newStatus === 'completed' || newStatus === 'failed') {
            setTimeout(() => {
                this.stopMonitoring(docId);
            }, 5000); // Keep monitoring for 5s after completion
        }
    }

    /**
     * Get current status for a document.
     *
     * @param {string} docId - Document ID
     * @returns {Object|null} Tracked data or null
     */
    getStatus(docId) {
        return this.trackedDocs.get(docId) || null;
    }

    /**
     * Get all tracked documents.
     *
     * @returns {Map} Map of doc_id -> tracked data
     */
    getAllTracked() {
        return new Map(this.trackedDocs);
    }

    /**
     * Stop monitoring all documents and cleanup.
     */
    destroy() {
        this.stopPolling();
        this.trackedDocs.clear();
    }
}

/**
 * Format status for display.
 *
 * @param {string} status - Status string from API
 * @returns {string} Human-readable status
 */
export function formatStatus(status) {
    const statusMap = {
        'queued': 'Queued',
        'parsing': 'Parsing document',
        'extracting_structure': 'Extracting structure',
        'chunking': 'Creating chunks',
        'processing_visual': 'Processing images',
        'embedding_visual': 'Generating visual embeddings',
        'processing_text': 'Processing text',
        'embedding_text': 'Generating text embeddings',
        'storing': 'Storing in database',
        'completed': 'Completed',
        'failed': 'Failed',
        'not_found': 'Not found',
        'unknown': 'Unknown'
    };

    return statusMap[status] || status;
}

/**
 * Format progress percentage.
 *
 * @param {number} progress - Progress (0-1)
 * @returns {string} Formatted percentage (e.g., "65%")
 */
export function formatProgress(progress) {
    return `${Math.round(progress * 100)}%`;
}

/**
 * Format elapsed time.
 *
 * @param {number} milliseconds - Elapsed time in milliseconds
 * @returns {string} Formatted time (e.g., "2m 30s", "45s")
 */
export function formatElapsedTime(milliseconds) {
    const seconds = Math.floor(milliseconds / 1000);

    if (seconds < 60) {
        return `${seconds}s`;
    }

    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;

    if (minutes < 60) {
        return `${minutes}m ${remainingSeconds}s`;
    }

    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;

    return `${hours}h ${remainingMinutes}m`;
}

/**
 * Calculate elapsed time from timestamps.
 *
 * @param {string} startTime - ISO 8601 start time
 * @param {string} [endTime] - ISO 8601 end time (default: now)
 * @returns {number} Elapsed milliseconds
 */
export function calculateElapsedTime(startTime, endTime = null) {
    const start = new Date(startTime).getTime();
    const end = endTime ? new Date(endTime).getTime() : Date.now();

    return end - start;
}

/**
 * Format error message for display.
 *
 * @param {string} error - Error message
 * @returns {string} Formatted error
 */
export function formatError(error) {
    if (!error) {
        return '';
    }

    // Truncate very long errors
    const maxLength = 100;
    if (error.length > maxLength) {
        return error.substring(0, maxLength) + '...';
    }

    return error;
}

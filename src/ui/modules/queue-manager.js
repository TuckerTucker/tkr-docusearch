/**
 * Queue Manager Module
 *
 * Manages queue UI display and updates from processing monitor.
 *
 * Provider: monitoring-logic-agent
 * Contract: ui-html.contract.md
 */

import { formatStatus, formatProgress, formatElapsedTime, calculateElapsedTime, formatError } from './processing-monitor.js';

/**
 * QueueManager class.
 *
 * Manages the queue UI and handles status updates from ProcessingMonitor.
 */
export class QueueManager {
    /**
     * Create a new QueueManager instance.
     *
     * @param {Object} options - Manager options
     * @param {string} options.queueItemsId - ID of queue items container (default: 'queue-items')
     * @param {string} options.queueEmptyId - ID of empty state element (default: 'queue-empty')
     * @param {string} options.queueSectionId - ID of queue section (default: 'queue-section')
     * @param {string} options.activeCountId - ID of active count element (default: 'queue-active-count')
     * @param {string} options.completedCountId - ID of completed count element (default: 'queue-completed-count')
     */
    constructor(options = {}) {
        this.queueItemsId = options.queueItemsId || 'queue-items';
        this.queueEmptyId = options.queueEmptyId || 'queue-empty';
        this.queueSectionId = options.queueSectionId || 'queue-section';
        this.activeCountId = options.activeCountId || 'queue-active-count';
        this.completedCountId = options.completedCountId || 'queue-completed-count';

        // Get DOM elements
        this.queueItems = document.getElementById(this.queueItemsId);
        this.queueEmpty = document.getElementById(this.queueEmptyId);
        this.queueSection = document.getElementById(this.queueSectionId);
        this.activeCount = document.getElementById(this.activeCountId);
        this.completedCount = document.getElementById(this.completedCountId);

        // Track queue items: Map<doc_id, HTMLElement>
        this.items = new Map();

        // Stats
        this.stats = {
            active: 0,
            completed: 0
        };
    }

    /**
     * Handle status update from ProcessingMonitor.
     *
     * @param {string} docId - Document ID
     * @param {Object} statusData - Status data from API
     */
    handleStatusUpdate(docId, statusData) {
        const item = this.items.get(docId);

        if (item) {
            // Update existing item
            this.updateQueueItem(item, statusData);
        } else {
            // Create new item (shouldn't happen often - upload.js creates items)
            this.addQueueItem(docId, statusData);
        }

        // Update stats
        this.updateStats();
    }

    /**
     * Add a new queue item.
     *
     * @param {string} docId - Document ID
     * @param {Object} statusData - Status data
     * @returns {HTMLElement} Created queue item element
     */
    addQueueItem(docId, statusData) {
        // Check if item already exists
        if (this.items.has(docId)) {
            return this.items.get(docId);
        }

        // Hide empty state
        if (this.queueEmpty) {
            this.queueEmpty.style.display = 'none';
        }

        // Show queue section
        if (this.queueSection) {
            this.queueSection.style.display = 'block';
        }

        // Create queue item element
        const item = document.createElement('article');
        item.className = 'queue-item queue-item--processing';
        item.setAttribute('data-doc-id', docId);

        // Get metadata
        const filename = statusData.filename || 'Unknown file';
        const status = formatStatus(statusData.status || 'unknown');
        const progress = statusData.progress || 0;

        item.innerHTML = `
            <div class="queue-item-header">
                <span class="queue-item-filename">${this.escapeHtml(filename)}</span>
                <span class="queue-item-status">${this.escapeHtml(status)}</span>
            </div>
            <div class="queue-item-progress">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${progress * 100}%"></div>
                </div>
                <span class="progress-text">${formatProgress(progress)}</span>
            </div>
            <div class="queue-item-details">
                <span class="queue-item-detail queue-item-detail--elapsed">Elapsed: 0s</span>
                <span class="queue-item-detail queue-item-detail--page" style="display: none;"></span>
                <span class="queue-item-detail queue-item-detail--error" style="display: none;"></span>
            </div>
        `;

        // Add to container (newest first)
        if (this.queueItems) {
            this.queueItems.insertBefore(item, this.queueItems.firstChild);
        }

        // Track item
        this.items.set(docId, item);

        return item;
    }

    /**
     * Update an existing queue item.
     *
     * @param {HTMLElement} item - Queue item element
     * @param {Object} statusData - Status data
     */
    updateQueueItem(item, statusData) {
        const {
            status,
            progress = 0,
            page,
            total_pages,
            chunk,
            total_chunks,
            error,
            started_at,
            completed_at
        } = statusData;

        // Update status class
        item.className = 'queue-item';
        if (status === 'completed') {
            item.classList.add('queue-item--completed');
        } else if (status === 'failed') {
            item.classList.add('queue-item--failed');
        } else {
            item.classList.add('queue-item--processing');
        }

        // Update status text
        const statusEl = item.querySelector('.queue-item-status');
        if (statusEl) {
            statusEl.textContent = formatStatus(status);
        }

        // Update progress bar
        const progressFill = item.querySelector('.progress-fill');
        const progressText = item.querySelector('.progress-text');
        if (progressFill && progressText) {
            const percentage = Math.round(progress * 100);
            progressFill.style.width = `${percentage}%`;
            progressText.textContent = formatProgress(progress);
        }

        // Update elapsed time
        const elapsedEl = item.querySelector('.queue-item-detail--elapsed');
        if (elapsedEl && started_at) {
            const elapsed = calculateElapsedTime(started_at, completed_at);
            elapsedEl.textContent = `Elapsed: ${formatElapsedTime(elapsed)}`;
        }

        // Update page/chunk progress
        const pageEl = item.querySelector('.queue-item-detail--page');
        if (pageEl) {
            if (page && total_pages) {
                pageEl.textContent = `Page ${page}/${total_pages}`;
                pageEl.style.display = '';
            } else if (chunk && total_chunks) {
                pageEl.textContent = `Chunk ${chunk}/${total_chunks}`;
                pageEl.style.display = '';
            } else {
                pageEl.style.display = 'none';
            }
        }

        // Update error message
        const errorEl = item.querySelector('.queue-item-detail--error');
        if (errorEl) {
            if (error) {
                errorEl.textContent = formatError(error);
                errorEl.style.display = '';
            } else {
                errorEl.style.display = 'none';
            }
        }
    }

    /**
     * Remove a queue item.
     *
     * @param {string} docId - Document ID
     */
    removeQueueItem(docId) {
        const item = this.items.get(docId);
        if (!item) {
            return;
        }

        // Remove from DOM
        if (this.queueItems && item.parentNode === this.queueItems) {
            this.queueItems.removeChild(item);
        }

        // Untrack item
        this.items.delete(docId);

        // Show empty state if no items
        if (this.items.size === 0 && this.queueEmpty) {
            this.queueEmpty.style.display = 'block';
        }

        // Update stats
        this.updateStats();
    }

    /**
     * Get queue item element by doc_id.
     *
     * @param {string} docId - Document ID
     * @returns {HTMLElement|null} Queue item element or null
     */
    getQueueItem(docId) {
        return this.items.get(docId) || null;
    }

    /**
     * Update queue statistics.
     */
    updateStats() {
        let active = 0;
        let completed = 0;

        // Count active and completed items
        for (const item of this.items.values()) {
            if (item.classList.contains('queue-item--completed')) {
                completed++;
            } else if (item.classList.contains('queue-item--processing')) {
                active++;
            }
        }

        this.stats.active = active;
        this.stats.completed = completed;

        // Update UI
        if (this.activeCount) {
            this.activeCount.textContent = active;
        }
        if (this.completedCount) {
            this.completedCount.textContent = completed;
        }
    }

    /**
     * Clear all completed items.
     */
    clearCompleted() {
        const completedItems = Array.from(this.items.entries())
            .filter(([_, item]) => item.classList.contains('queue-item--completed'))
            .map(([docId, _]) => docId);

        completedItems.forEach(docId => this.removeQueueItem(docId));
    }

    /**
     * Clear all failed items.
     */
    clearFailed() {
        const failedItems = Array.from(this.items.entries())
            .filter(([_, item]) => item.classList.contains('queue-item--failed'))
            .map(([docId, _]) => docId);

        failedItems.forEach(docId => this.removeQueueItem(docId));
    }

    /**
     * Clear all items.
     */
    clearAll() {
        const allItems = Array.from(this.items.keys());
        allItems.forEach(docId => this.removeQueueItem(docId));
    }

    /**
     * Get all queue items.
     *
     * @returns {Map} Map of doc_id -> HTMLElement
     */
    getAllItems() {
        return new Map(this.items);
    }

    /**
     * Get queue statistics.
     *
     * @returns {Object} Stats {active, completed}
     */
    getStats() {
        return { ...this.stats };
    }

    /**
     * Escape HTML to prevent XSS.
     *
     * @private
     * @param {string} str - String to escape
     * @returns {string} Escaped string
     */
    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    /**
     * Load queue state from API.
     *
     * This is useful for initializing the queue on page load (e.g., status.html).
     *
     * @param {string} apiBaseUrl - Base URL for status API (default: http://localhost:8002)
     * @returns {Promise<void>}
     */
    async loadFromApi(apiBaseUrl = 'http://localhost:8002') {
        try {
            const response = await fetch(`${apiBaseUrl}/status/queue`);

            if (!response.ok) {
                throw new Error(`Queue endpoint returned ${response.status}`);
            }

            const data = await response.json();

            // Add active items
            if (data.active) {
                data.active.forEach(item => {
                    const docId = item.doc_id;
                    this.addQueueItem(docId, item);
                });
            }

            // Add completed items
            if (data.completed) {
                data.completed.forEach(item => {
                    const docId = item.doc_id;
                    this.addQueueItem(docId, item);
                });
            }

            // Update stats
            this.updateStats();

        } catch (error) {
            console.error('Failed to load queue from API:', error);
            throw error;
        }
    }
}

/**
 * Create status badge HTML.
 *
 * @param {string} status - Status string
 * @returns {string} HTML for status badge
 */
export function createStatusBadge(status) {
    const badgeClass = status === 'completed' ? 'badge--success' :
                       status === 'failed' ? 'badge--error' :
                       'badge--info';

    return `<span class="badge ${badgeClass}">${formatStatus(status)}</span>`;
}

/**
 * Create progress bar HTML.
 *
 * @param {number} progress - Progress (0-1)
 * @returns {string} HTML for progress bar
 */
export function createProgressBar(progress) {
    const percentage = Math.round(progress * 100);

    return `
        <div class="progress-bar">
            <div class="progress-fill" style="width: ${percentage}%"></div>
        </div>
        <span class="progress-text">${percentage}%</span>
    `;
}

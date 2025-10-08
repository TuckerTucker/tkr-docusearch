/**
 * Monitor Logic Module
 *
 * Handles real-time processing status monitoring and queue display.
 *
 * Provider: monitoring-logic-agent (Wave 3)
 * Contract: ui-html.contract.md
 */

import { ProcessingMonitor } from './modules/processing-monitor.js';
import { QueueManager } from './modules/queue-manager.js';

// Global instances
let monitor = null;
let queueManager = null;

/**
 * Initialize monitoring functionality.
 */
export function initializeMonitoring() {
    console.log('Initializing monitoring module...');

    // Create queue manager
    queueManager = new QueueManager({
        queueItemsId: 'queue-items',
        queueEmptyId: 'queue-empty',
        queueSectionId: 'queue-section',
        activeCountId: 'queue-active-count',
        completedCountId: 'queue-completed-count'
    });

    // Create processing monitor
    monitor = new ProcessingMonitor({
        apiBaseUrl: 'http://localhost:8002',
        pollInterval: 2000, // Poll every 2 seconds
        onStatusUpdate: handleStatusUpdate,
        onError: handleMonitorError,
        queueManager: queueManager
    });

    // Check if we're on status.html (load existing queue)
    if (isStatusPage()) {
        loadExistingQueue();
    }

    // Start monitoring any items that already have doc_ids
    startMonitoringExistingItems();

    // Setup clear queue button
    setupClearQueueButton();

    console.log('Monitor module initialized');
}

/**
 * Setup clear queue button event listener.
 */
function setupClearQueueButton() {
    const clearBtn = document.getElementById('clear-queue-btn');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            // Confirm before clearing
            if (confirm('Are you sure you want to clear the entire queue? This will remove all items and reset localStorage.')) {
                clearQueue();
            }
        });
        console.log('Clear queue button initialized');
    }
}

/**
 * Check if current page is status.html.
 *
 * @returns {boolean} True if on status.html
 */
function isStatusPage() {
    return window.location.pathname.includes('status.html');
}

/**
 * Load existing queue from API (for status.html).
 */
async function loadExistingQueue() {
    try {
        await queueManager.loadFromApi('http://localhost:8002');
        console.log('Loaded existing queue from API');

        // Start monitoring all loaded items
        const items = queueManager.getAllItems();
        for (const [docId, _] of items.entries()) {
            monitor.startMonitoring(docId);
        }
    } catch (error) {
        console.error('Failed to load queue:', error);
    }
}

/**
 * Start monitoring items that already exist in DOM.
 */
function startMonitoringExistingItems() {
    const queueItems = document.getElementById('queue-items');
    if (!queueItems) {
        return;
    }

    // Find all queue items with doc_id attribute
    const items = queueItems.querySelectorAll('[data-doc-id]');
    items.forEach(item => {
        const docId = item.getAttribute('data-doc-id');
        if (docId && !docId.startsWith('temp-')) {
            // Start monitoring this document
            monitor.startMonitoring(docId);

            // Add to queue manager tracking
            queueManager.items.set(docId, item);
        }
    });

    // Update stats
    queueManager.updateStats();
}

/**
 * Handle status update from ProcessingMonitor.
 *
 * @param {string} docId - Document ID
 * @param {Object} statusData - Status data from API
 */
function handleStatusUpdate(docId, statusData) {
    // Update queue UI via QueueManager
    queueManager.handleStatusUpdate(docId, statusData);

    // Handle completion
    if (statusData.status === 'completed') {
        handleCompletion(docId, statusData);
    }

    // Handle failure
    if (statusData.status === 'failed') {
        handleFailure(docId, statusData);
    }
}

/**
 * Handle document processing completion.
 *
 * @param {string} docId - Document ID
 * @param {Object} statusData - Status data
 */
function handleCompletion(docId, statusData) {
    console.log(`Document completed: ${docId}`);

    // Show success notification
    showNotification('success', `${statusData.filename} processed successfully`);
}

/**
 * Handle document processing failure.
 *
 * @param {string} docId - Document ID
 * @param {Object} statusData - Status data
 */
function handleFailure(docId, statusData) {
    console.error(`Document failed: ${docId}`, statusData.error);

    // Show error notification
    const message = statusData.error || 'Processing failed';
    showNotification('error', `${statusData.filename}: ${message}`);
}

/**
 * Handle monitor errors.
 *
 * @param {Error} error - Error object
 */
function handleMonitorError(error) {
    console.error('Monitor error:', error);
    // Don't show toast for every polling error (too noisy)
}

/**
 * Show toast notification.
 *
 * @param {string} type - Notification type ('success', 'error', 'warning')
 * @param {string} message - Notification message
 */
function showNotification(type, message) {
    const container = document.getElementById('toast-container');
    if (!container) {
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
            if (container.contains(toast)) {
                container.removeChild(toast);
            }
        }, 300); // Match CSS transition duration
    }, 5000);
}

/**
 * Start monitoring a document.
 *
 * This is called by upload.js when a file is uploaded.
 *
 * @param {string} docId - Document ID to monitor
 * @param {string} filename - Filename for display
 */
export function startMonitoring(docId, filename) {
    if (!monitor) {
        console.error('Monitor not initialized');
        return;
    }

    console.log(`Starting monitoring for ${docId} (${filename})`);
    monitor.startMonitoring(docId, filename);
}

/**
 * Stop monitoring a document.
 *
 * @param {string} docId - Document ID to stop monitoring
 */
export function stopMonitoring(docId) {
    if (!monitor) {
        return;
    }

    monitor.stopMonitoring(docId);
}

/**
 * Get current monitor instance.
 *
 * @returns {ProcessingMonitor|null} Monitor instance
 */
export function getMonitor() {
    return monitor;
}

/**
 * Get current queue manager instance.
 *
 * @returns {QueueManager|null} Queue manager instance
 */
export function getQueueManager() {
    return queueManager;
}

/**
 * Update a queue item (called by upload.js).
 *
 * @param {string} docId - Document ID
 * @param {Object} data - Update data
 */
export function updateQueueItem(docId, data) {
    if (!queueManager) {
        console.error('Queue manager not initialized');
        return;
    }

    const item = queueManager.getQueueItem(docId);
    if (item) {
        queueManager.updateQueueItem(item, data);
    }
}

/**
 * Clear completed items from queue.
 */
export function clearCompleted() {
    if (!queueManager) {
        return;
    }

    queueManager.clearCompleted();
}

/**
 * Clear failed items from queue.
 */
export function clearFailed() {
    if (!queueManager) {
        return;
    }

    queueManager.clearFailed();
}

/**
 * Clear all items from queue.
 */
export function clearAll() {
    if (!queueManager) {
        return;
    }

    queueManager.clearAll();
}

/**
 * Get queue statistics.
 *
 * @returns {Object} Stats {active, completed}
 */
export function getQueueStats() {
    if (!queueManager) {
        return { active: 0, completed: 0 };
    }

    return queueManager.getStats();
}

/**
 * Clear all queue items and localStorage.
 */
export function clearQueue() {
    if (!queueManager) {
        console.warn('Queue manager not initialized');
        return;
    }

    // Stop monitoring all documents
    if (monitor) {
        const trackedDocs = monitor.getAllTracked();
        for (const [docId, _] of trackedDocs.entries()) {
            monitor.stopMonitoring(docId);
        }
    }

    // Clear queue items
    queueManager.clearAll();

    // Clear localStorage
    queueManager.clearStorage();

    console.log('Queue cleared');
    showNotification('success', 'Queue cleared successfully');
}

/**
 * Cleanup monitoring (called on page unload).
 */
export function cleanup() {
    if (monitor) {
        monitor.destroy();
        monitor = null;
    }

    queueManager = null;
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeMonitoring);
} else {
    initializeMonitoring();
}

// Cleanup on page unload
window.addEventListener('beforeunload', cleanup);

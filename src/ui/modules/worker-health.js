/**
 * Worker Health Monitor Module
 *
 * Monitors worker health status and updates UI indicator.
 *
 * Provider: ui-monitoring-agent
 * Contract: ui-html.contract.md
 */

/**
 * Configuration for health monitoring.
 */
const HEALTH_CONFIG = {
    // Worker health endpoint
    healthUrl: 'http://localhost:8002/health',
    // Check interval in milliseconds (30 seconds)
    checkInterval: 30000,
    // Initial check delay (1 second after page load)
    initialDelay: 1000
};

/**
 * Health monitor state.
 */
let healthCheckTimer = null;
let statusIndicator = null;
let statusText = null;

/**
 * Initialize worker health monitoring.
 *
 * Sets up periodic health checks and updates the UI indicator.
 */
export function initializeHealthMonitoring() {
    // Get DOM elements
    statusIndicator = document.querySelector('.status-indicator');
    statusText = document.querySelector('.status-text');

    if (!statusIndicator || !statusText) {
        console.error('Worker health: Status elements not found');
        return;
    }

    // Perform initial health check
    setTimeout(checkWorkerHealth, HEALTH_CONFIG.initialDelay);

    // Set up periodic health checks
    healthCheckTimer = setInterval(checkWorkerHealth, HEALTH_CONFIG.checkInterval);

    console.log('Worker health monitoring initialized');
}

/**
 * Stop health monitoring.
 *
 * Cleans up timer when page is unloaded.
 */
export function stopHealthMonitoring() {
    if (healthCheckTimer) {
        clearInterval(healthCheckTimer);
        healthCheckTimer = null;
    }
}

/**
 * Check worker health status.
 *
 * Makes a request to the health endpoint and updates UI.
 *
 * @private
 */
async function checkWorkerHealth() {
    try {
        const response = await fetch(HEALTH_CONFIG.healthUrl, {
            method: 'GET',
            signal: AbortSignal.timeout(5000) // 5 second timeout
        });

        if (response.ok) {
            const data = await response.json();
            updateHealthStatus('healthy', 'Worker healthy');
        } else {
            updateHealthStatus('error', `Worker error (${response.status})`);
        }
    } catch (error) {
        // Network error or timeout
        if (error.name === 'TimeoutError') {
            updateHealthStatus('error', 'Worker timeout');
        } else if (error.name === 'TypeError' || error.message.includes('fetch')) {
            updateHealthStatus('error', 'Worker offline');
        } else {
            updateHealthStatus('error', 'Worker error');
        }
        console.error('Worker health check failed:', error);
    }
}

/**
 * Update health status UI.
 *
 * @private
 * @param {string} status - Status type: 'checking', 'healthy', 'error'
 * @param {string} message - Status message to display
 */
function updateHealthStatus(status, message) {
    if (!statusIndicator || !statusText) return;

    // Remove all status classes
    statusIndicator.classList.remove(
        'status-indicator--checking',
        'status-indicator--healthy',
        'status-indicator--error'
    );

    // Add new status class
    statusIndicator.classList.add(`status-indicator--${status}`);

    // Update text
    statusText.textContent = message;
}

/**
 * Manually trigger a health check.
 *
 * @returns {Promise<void>}
 */
export async function checkHealth() {
    await checkWorkerHealth();
}

// Clean up on page unload
window.addEventListener('beforeunload', stopHealthMonitoring);

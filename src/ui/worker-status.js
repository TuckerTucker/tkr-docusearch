/**
 * Worker Status Initializer
 *
 * Shared script to initialize worker health monitoring on all pages.
 * This ensures the worker status indicator persists across navigation.
 */

import { initializeHealthMonitoring } from './modules/worker-health.js';

// Initialize health monitoring when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeHealthMonitoring);
} else {
    initializeHealthMonitoring();
}

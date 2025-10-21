/**
 * Performance Optimization Module Index
 *
 * Central export point for all performance optimization utilities.
 *
 * Wave 3 - Agent 13: Performance Optimizer
 *
 * @module performance
 */

// Debounce utilities
export { debounce, throttle, rafDebounce, idleDebounce } from './debounce.js';

// Cache management
export { StructureCache } from './cache-manager.js';

// Lazy loading
export { StructureLazyLoader } from './lazy-loader.js';

// Performance metrics
export { PerformanceMetrics, createTimer } from './metrics.js';

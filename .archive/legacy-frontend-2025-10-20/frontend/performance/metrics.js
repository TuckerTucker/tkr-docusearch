/**
 * Performance Measurement and Metrics
 *
 * Utilities for measuring and reporting performance metrics across
 * the bidirectional highlighting feature. Uses Performance API,
 * User Timing API, and custom instrumentation.
 *
 * Wave 3 - Agent 13: Performance Optimizer
 *
 * @module metrics
 */

/**
 * Performance metric entry
 * @typedef {Object} MetricEntry
 * @property {string} name - Metric name
 * @property {number} duration - Duration in milliseconds
 * @property {number} timestamp - Start timestamp
 * @property {string} category - Metric category
 * @property {Object} metadata - Additional metadata
 */

/**
 * Performance summary
 * @typedef {Object} PerformanceSummary
 * @property {string} name - Metric name
 * @property {number} count - Number of measurements
 * @property {number} total - Total duration
 * @property {number} mean - Mean duration
 * @property {number} min - Minimum duration
 * @property {number} max - Maximum duration
 * @property {number} p50 - 50th percentile
 * @property {number} p95 - 95th percentile
 * @property {number} p99 - 99th percentile
 */

/**
 * Performance metrics collector and reporter.
 *
 * @class
 * @example
 * // Measure function execution
 * const result = await PerformanceMetrics.measure('loadStructure', async () => {
 *   return await fetch('/api/structure/1');
 * });
 *
 * // Manual timing
 * PerformanceMetrics.mark('bbox-render-start');
 * renderBboxes();
 * PerformanceMetrics.mark('bbox-render-end');
 * PerformanceMetrics.measure('bbox-render', 'bbox-render-start', 'bbox-render-end');
 *
 * // Get metrics
 * const metrics = PerformanceMetrics.getMetrics();
 * console.log(metrics);
 *
 * // Report to console
 * PerformanceMetrics.report();
 */
export class PerformanceMetrics {
  static _metrics = new Map(); // Map<string, MetricEntry[]>
  static _enabled = true;
  static _categories = new Set();

  /**
   * Enable or disable metrics collection.
   *
   * @param {boolean} enabled - Enable metrics
   */
  static setEnabled(enabled) {
    PerformanceMetrics._enabled = enabled;
    console.log(`[PerformanceMetrics] ${enabled ? 'Enabled' : 'Disabled'}`);
  }

  /**
   * Check if metrics collection is enabled.
   *
   * @returns {boolean} True if enabled
   */
  static isEnabled() {
    return PerformanceMetrics._enabled;
  }

  /**
   * Create a performance mark (timestamp).
   *
   * @param {string} name - Mark name
   * @returns {PerformanceMark|null} Performance mark or null if disabled
   */
  static mark(name) {
    if (!PerformanceMetrics._enabled) return null;

    try {
      if (performance.mark) {
        return performance.mark(name);
      }
    } catch (error) {
      console.warn('[PerformanceMetrics] Failed to create mark:', error);
    }

    return null;
  }

  /**
   * Measure duration between two marks.
   *
   * @param {string} name - Measurement name
   * @param {string} startMark - Start mark name
   * @param {string} endMark - End mark name
   * @param {Object} options - Options
   * @param {string} options.category - Metric category (default: 'custom')
   * @param {Object} options.metadata - Additional metadata
   * @returns {number|null} Duration in milliseconds or null if failed
   */
  static measure(name, startMark, endMark, options = {}) {
    if (!PerformanceMetrics._enabled) return null;

    try {
      // Use Performance API if available
      if (performance.measure) {
        const measure = performance.measure(name, startMark, endMark);
        const duration = measure.duration;

        PerformanceMetrics._recordMetric(name, duration, options.category, options.metadata);

        return duration;
      }

      // Fallback: manual calculation from marks
      const marks = performance.getEntriesByType('mark');
      const start = marks.find((m) => m.name === startMark);
      const end = marks.find((m) => m.name === endMark);

      if (start && end) {
        const duration = end.startTime - start.startTime;
        PerformanceMetrics._recordMetric(name, duration, options.category, options.metadata);
        return duration;
      }
    } catch (error) {
      console.warn('[PerformanceMetrics] Failed to measure:', error);
    }

    return null;
  }

  /**
   * Measure async function execution time.
   *
   * @param {string} name - Measurement name
   * @param {Function} fn - Async function to measure
   * @param {Object} options - Options
   * @param {string} options.category - Metric category (default: 'function')
   * @param {Object} options.metadata - Additional metadata
   * @returns {Promise<*>} Function result
   */
  static async measureAsync(name, fn, options = {}) {
    if (!PerformanceMetrics._enabled) {
      return await fn();
    }

    const startTime = performance.now();

    try {
      const result = await fn();
      const duration = performance.now() - startTime;

      PerformanceMetrics._recordMetric(
        name,
        duration,
        options.category || 'function',
        options.metadata
      );

      return result;
    } catch (error) {
      const duration = performance.now() - startTime;

      PerformanceMetrics._recordMetric(
        name,
        duration,
        options.category || 'function',
        { ...options.metadata, error: error.message }
      );

      throw error;
    }
  }

  /**
   * Measure synchronous function execution time.
   *
   * @param {string} name - Measurement name
   * @param {Function} fn - Function to measure
   * @param {Object} options - Options
   * @param {string} options.category - Metric category (default: 'function')
   * @param {Object} options.metadata - Additional metadata
   * @returns {*} Function result
   */
  static measureSync(name, fn, options = {}) {
    if (!PerformanceMetrics._enabled) {
      return fn();
    }

    const startTime = performance.now();

    try {
      const result = fn();
      const duration = performance.now() - startTime;

      PerformanceMetrics._recordMetric(
        name,
        duration,
        options.category || 'function',
        options.metadata
      );

      return result;
    } catch (error) {
      const duration = performance.now() - startTime;

      PerformanceMetrics._recordMetric(
        name,
        duration,
        options.category || 'function',
        { ...options.metadata, error: error.message }
      );

      throw error;
    }
  }

  /**
   * Record a metric entry.
   *
   * @private
   * @param {string} name - Metric name
   * @param {number} duration - Duration in milliseconds
   * @param {string} category - Metric category
   * @param {Object} metadata - Additional metadata
   */
  static _recordMetric(name, duration, category = 'custom', metadata = {}) {
    const entry = {
      name,
      duration,
      timestamp: Date.now(),
      category,
      metadata,
    };

    if (!PerformanceMetrics._metrics.has(name)) {
      PerformanceMetrics._metrics.set(name, []);
    }

    PerformanceMetrics._metrics.get(name).push(entry);
    PerformanceMetrics._categories.add(category);
  }

  /**
   * Record a custom metric value.
   *
   * @param {string} name - Metric name
   * @param {number} value - Metric value
   * @param {Object} options - Options
   * @param {string} options.category - Metric category (default: 'custom')
   * @param {Object} options.metadata - Additional metadata
   */
  static record(name, value, options = {}) {
    if (!PerformanceMetrics._enabled) return;

    PerformanceMetrics._recordMetric(
      name,
      value,
      options.category || 'custom',
      options.metadata
    );
  }

  /**
   * Get all recorded metrics.
   *
   * @param {Object} options - Filter options
   * @param {string} options.name - Filter by metric name
   * @param {string} options.category - Filter by category
   * @returns {Map<string, MetricEntry[]>} Metrics map
   */
  static getMetrics(options = {}) {
    if (!options.name && !options.category) {
      return new Map(PerformanceMetrics._metrics);
    }

    const filtered = new Map();

    for (const [name, entries] of PerformanceMetrics._metrics.entries()) {
      // Filter by name
      if (options.name && name !== options.name) continue;

      // Filter by category
      if (options.category) {
        const categoryEntries = entries.filter((e) => e.category === options.category);
        if (categoryEntries.length > 0) {
          filtered.set(name, categoryEntries);
        }
      } else {
        filtered.set(name, entries);
      }
    }

    return filtered;
  }

  /**
   * Calculate summary statistics for a metric.
   *
   * @param {string} name - Metric name
   * @returns {PerformanceSummary|null} Summary statistics or null if no data
   */
  static getSummary(name) {
    const entries = PerformanceMetrics._metrics.get(name);
    if (!entries || entries.length === 0) return null;

    const durations = entries.map((e) => e.duration).sort((a, b) => a - b);
    const count = durations.length;
    const total = durations.reduce((sum, d) => sum + d, 0);

    return {
      name,
      count,
      total,
      mean: total / count,
      min: durations[0],
      max: durations[count - 1],
      p50: PerformanceMetrics._percentile(durations, 0.5),
      p95: PerformanceMetrics._percentile(durations, 0.95),
      p99: PerformanceMetrics._percentile(durations, 0.99),
    };
  }

  /**
   * Calculate percentile from sorted array.
   *
   * @private
   * @param {number[]} sortedValues - Sorted values
   * @param {number} p - Percentile (0-1)
   * @returns {number} Percentile value
   */
  static _percentile(sortedValues, p) {
    const index = Math.ceil(sortedValues.length * p) - 1;
    return sortedValues[Math.max(0, index)];
  }

  /**
   * Get summaries for all metrics.
   *
   * @param {Object} options - Filter options
   * @param {string} options.category - Filter by category
   * @returns {PerformanceSummary[]} Array of summaries
   */
  static getAllSummaries(options = {}) {
    const summaries = [];
    const metrics = PerformanceMetrics.getMetrics(options);

    for (const [name, entries] of metrics.entries()) {
      const summary = PerformanceMetrics.getSummary(name);
      if (summary) {
        summaries.push(summary);
      }
    }

    return summaries.sort((a, b) => b.total - a.total);
  }

  /**
   * Report metrics to console (formatted table).
   *
   * @param {Object} options - Report options
   * @param {string} options.category - Filter by category
   * @param {boolean} options.detailed - Show detailed entries (default: false)
   */
  static report(options = {}) {
    if (!PerformanceMetrics._enabled) {
      console.log('[PerformanceMetrics] Disabled');
      return;
    }

    console.group('[PerformanceMetrics] Report');

    const summaries = PerformanceMetrics.getAllSummaries(options);

    if (summaries.length === 0) {
      console.log('No metrics recorded');
      console.groupEnd();
      return;
    }

    // Summary table
    console.log('\n📊 Performance Summary:');
    console.table(
      summaries.map((s) => ({
        Name: s.name,
        Count: s.count,
        'Total (ms)': s.total.toFixed(2),
        'Mean (ms)': s.mean.toFixed(2),
        'Min (ms)': s.min.toFixed(2),
        'Max (ms)': s.max.toFixed(2),
        'P95 (ms)': s.p95.toFixed(2),
      }))
    );

    // Detailed entries if requested
    if (options.detailed) {
      console.log('\n📝 Detailed Entries:');
      for (const summary of summaries) {
        const entries = PerformanceMetrics._metrics.get(summary.name);
        console.group(summary.name);
        console.table(
          entries.map((e) => ({
            Duration: e.duration.toFixed(2),
            Category: e.category,
            Timestamp: new Date(e.timestamp).toLocaleTimeString(),
            Metadata: JSON.stringify(e.metadata),
          }))
        );
        console.groupEnd();
      }
    }

    console.groupEnd();
  }

  /**
   * Export metrics as JSON.
   *
   * @returns {Object} Metrics data
   */
  static export() {
    const data = {
      enabled: PerformanceMetrics._enabled,
      timestamp: Date.now(),
      categories: Array.from(PerformanceMetrics._categories),
      metrics: {},
      summaries: {},
    };

    for (const [name, entries] of PerformanceMetrics._metrics.entries()) {
      data.metrics[name] = entries;
      data.summaries[name] = PerformanceMetrics.getSummary(name);
    }

    return data;
  }

  /**
   * Clear all metrics.
   */
  static clear() {
    PerformanceMetrics._metrics.clear();
    PerformanceMetrics._categories.clear();

    // Clear Performance API marks and measures
    if (performance.clearMarks) {
      performance.clearMarks();
    }
    if (performance.clearMeasures) {
      performance.clearMeasures();
    }

    console.log('[PerformanceMetrics] Cleared');
  }

  /**
   * Get current memory usage (if available).
   *
   * @returns {Object|null} Memory info or null if not available
   */
  static getMemoryUsage() {
    if (performance.memory) {
      return {
        usedJSHeapSize: performance.memory.usedJSHeapSize,
        totalJSHeapSize: performance.memory.totalJSHeapSize,
        jsHeapSizeLimit: performance.memory.jsHeapSizeLimit,
        usedMB: (performance.memory.usedJSHeapSize / 1024 / 1024).toFixed(2),
        totalMB: (performance.memory.totalJSHeapSize / 1024 / 1024).toFixed(2),
      };
    }

    return null;
  }

  /**
   * Get navigation timing metrics.
   *
   * @returns {Object|null} Navigation timing or null if not available
   */
  static getNavigationTiming() {
    if (!performance.timing) return null;

    const timing = performance.timing;
    const nav = {
      dns: timing.domainLookupEnd - timing.domainLookupStart,
      tcp: timing.connectEnd - timing.connectStart,
      request: timing.responseStart - timing.requestStart,
      response: timing.responseEnd - timing.responseStart,
      dom: timing.domComplete - timing.domLoading,
      load: timing.loadEventEnd - timing.loadEventStart,
      total: timing.loadEventEnd - timing.navigationStart,
    };

    return nav;
  }

  /**
   * Monitor performance observer entries.
   *
   * @param {string[]} entryTypes - Entry types to observe (e.g., ['measure', 'mark'])
   * @param {Function} callback - Callback for each entry
   * @returns {PerformanceObserver|null} Observer or null if not supported
   */
  static observeEntries(entryTypes, callback) {
    if (!('PerformanceObserver' in window)) {
      console.warn('[PerformanceMetrics] PerformanceObserver not supported');
      return null;
    }

    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          callback(entry);
        }
      });

      observer.observe({ entryTypes });
      return observer;
    } catch (error) {
      console.error('[PerformanceMetrics] Failed to create observer:', error);
      return null;
    }
  }
}

/**
 * Create a performance timer for manual timing.
 *
 * @param {string} name - Timer name
 * @param {Object} options - Options
 * @param {string} options.category - Metric category
 * @returns {Object} Timer object with stop() method
 *
 * @example
 * const timer = createTimer('render-overlay');
 * renderOverlay();
 * timer.stop();
 */
export function createTimer(name, options = {}) {
  const startTime = performance.now();
  let stopped = false;

  return {
    stop() {
      if (stopped) {
        console.warn(`[Timer] Timer "${name}" already stopped`);
        return null;
      }

      const duration = performance.now() - startTime;
      stopped = true;

      PerformanceMetrics.record(name, duration, options);

      return duration;
    },
  };
}

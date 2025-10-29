/**
 * Performance Utilities
 *
 * Agent 12: Performance Optimizer
 * Wave 3 - BBox Overlay React Implementation
 *
 * Collection of performance monitoring and optimization utilities.
 * Provides helpers for tracking metrics, profiling operations, and
 * measuring render performance.
 *
 * Features:
 * - Performance marks and measures
 * - FPS tracking
 * - Memory monitoring
 * - Slow operation detection
 * - Development-only overhead
 */

const IS_DEV = process.env.NODE_ENV === 'development';

/**
 * Creates a performance mark with optional metadata.
 *
 * @param name - Name of the performance mark
 * @param metadata - Optional metadata to log
 */
export function mark(name: string, metadata?: Record<string, any>): void {
  if (!IS_DEV) return;

  if (typeof performance !== 'undefined' && performance.mark) {
    try {
      performance.mark(name);
      if (metadata) {
        console.debug(`[Performance] Mark: ${name}`, metadata);
      }
    } catch (e) {
      // Silently fail
    }
  }
}

/**
 * Measures duration between two performance marks.
 *
 * @param name - Name of the performance measure
 * @param startMark - Name of start mark
 * @param endMark - Name of end mark
 * @returns Duration in milliseconds, or null if measurement failed
 */
export function measure(
  name: string,
  startMark: string,
  endMark: string
): number | null {
  if (!IS_DEV) return null;

  if (typeof performance !== 'undefined' && performance.measure) {
    try {
      performance.measure(name, startMark, endMark);
      const entries = performance.getEntriesByName(name, 'measure');
      if (entries.length > 0) {
        const duration = entries[entries.length - 1].duration;
        console.debug(`[Performance] Measure: ${name} = ${duration.toFixed(2)}ms`);
        return duration;
      }
    } catch (e) {
      // Silently fail
    }
  }

  return null;
}

/**
 * Executes a function and measures its execution time.
 *
 * @param fn - Function to measure
 * @param label - Label for the measurement
 * @returns Result of the function and duration in milliseconds
 */
export function measureSync<T>(
  fn: () => T,
  label: string
): { result: T; duration: number } {
  const start = performance.now();
  const result = fn();
  const duration = performance.now() - start;

  if (IS_DEV) {
    console.debug(`[Performance] ${label} took ${duration.toFixed(2)}ms`);
  }

  return { result, duration };
}

/**
 * Executes an async function and measures its execution time.
 *
 * @param fn - Async function to measure
 * @param label - Label for the measurement
 * @returns Result of the function and duration in milliseconds
 */
export async function measureAsync<T>(
  fn: () => Promise<T>,
  label: string
): Promise<{ result: T; duration: number }> {
  const start = performance.now();
  const result = await fn();
  const duration = performance.now() - start;

  if (IS_DEV) {
    console.debug(`[Performance] ${label} took ${duration.toFixed(2)}ms`);
  }

  return { result, duration };
}

/**
 * Warns if an operation exceeds a time threshold.
 *
 * @param operation - Name of the operation
 * @param duration - Duration in milliseconds
 * @param threshold - Warning threshold in milliseconds (default: 16.67ms for 60fps)
 */
export function warnIfSlow(
  operation: string,
  duration: number,
  threshold: number = 16.67
): void {
  if (!IS_DEV) return;

  if (duration > threshold) {
    console.warn(
      `[Performance] ⚠️ ${operation} took ${duration.toFixed(2)}ms (threshold: ${threshold}ms)`
    );
  }
}

/**
 * Tracks frames per second over a period.
 *
 * @param duration - Duration to track in milliseconds (default: 1000ms)
 * @returns Promise that resolves to average FPS
 */
export function trackFPS(duration: number = 1000): Promise<number> {
  return new Promise((resolve) => {
    let frameCount = 0;
    const startTime = performance.now();

    function countFrame() {
      frameCount++;
      const elapsed = performance.now() - startTime;

      if (elapsed < duration) {
        requestAnimationFrame(countFrame);
      } else {
        const fps = (frameCount / elapsed) * 1000;
        if (IS_DEV) {
          console.debug(`[Performance] Average FPS: ${fps.toFixed(2)}`);
        }
        resolve(fps);
      }
    }

    requestAnimationFrame(countFrame);
  });
}

/**
 * Gets memory usage information (Chrome only).
 *
 * @returns Memory usage info or null if not available
 */
export function getMemoryInfo(): {
  usedJSHeapSize: number;
  totalJSHeapSize: number;
  jsHeapSizeLimit: number;
} | null {
  if (!IS_DEV) return null;

  // @ts-ignore - Chrome-specific API
  if (performance.memory) {
    // @ts-ignore
    const { usedJSHeapSize, totalJSHeapSize, jsHeapSizeLimit } = performance.memory;
    return {
      usedJSHeapSize,
      totalJSHeapSize,
      jsHeapSizeLimit,
    };
  }

  return null;
}

/**
 * Logs memory usage in a readable format.
 */
export function logMemoryUsage(): void {
  if (!IS_DEV) return;

  const memory = getMemoryInfo();
  if (memory) {
    const usedMB = (memory.usedJSHeapSize / 1024 / 1024).toFixed(2);
    const totalMB = (memory.totalJSHeapSize / 1024 / 1024).toFixed(2);
    const limitMB = (memory.jsHeapSizeLimit / 1024 / 1024).toFixed(2);

    console.debug(
      `[Performance] Memory: ${usedMB}MB used / ${totalMB}MB total (limit: ${limitMB}MB)`
    );
  }
}

/**
 * Creates a performance profiler for a specific operation.
 *
 * @param operation - Name of the operation
 * @returns Profiler object with start and end methods
 *
 * @example
 * ```typescript
 * const profiler = createProfiler('render-bboxes');
 * profiler.start();
 * // ... perform operation
 * const duration = profiler.end(); // Returns duration and logs if slow
 * ```
 */
export function createProfiler(operation: string) {
  let startTime: number | null = null;
  let endTime: number | null = null;

  return {
    start(): void {
      startTime = performance.now();
      mark(`${operation}:start`);
    },

    end(threshold: number = 16.67): number {
      if (startTime === null) {
        console.warn(`[Performance] Profiler for "${operation}" was not started`);
        return 0;
      }

      endTime = performance.now();
      mark(`${operation}:end`);

      const duration = endTime - startTime;
      measure(operation, `${operation}:start`, `${operation}:end`);
      warnIfSlow(operation, duration, threshold);

      return duration;
    },

    reset(): void {
      startTime = null;
      endTime = null;
    },
  };
}

/**
 * Monitors long tasks (> 50ms) using PerformanceObserver.
 *
 * @param callback - Callback fired when long task detected
 * @returns Cleanup function to stop monitoring
 */
export function monitorLongTasks(
  callback: (duration: number, name: string) => void
): () => void {
  if (!IS_DEV || typeof PerformanceObserver === 'undefined') {
    return () => {};
  }

  try {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.duration > 50) {
          callback(entry.duration, entry.name);
          console.warn(
            `[Performance] ⚠️ Long task detected: ${entry.name} (${entry.duration.toFixed(2)}ms)`
          );
        }
      }
    });

    observer.observe({ entryTypes: ['measure', 'longtask'] });

    return () => observer.disconnect();
  } catch (e) {
    console.warn('[Performance] PerformanceObserver not supported');
    return () => {};
  }
}

/**
 * Clears all performance marks and measures.
 */
export function clearPerformanceData(): void {
  if (!IS_DEV) return;

  if (typeof performance !== 'undefined') {
    try {
      performance.clearMarks();
      performance.clearMeasures();
      console.debug('[Performance] Cleared all marks and measures');
    } catch (e) {
      // Silently fail
    }
  }
}

/**
 * Gets all performance entries of a specific type.
 *
 * @param type - Entry type ('mark', 'measure', 'navigation', etc.)
 * @returns Array of performance entries
 */
export function getPerformanceEntries(
  type: string
): PerformanceEntry[] {
  if (!IS_DEV) return [];

  if (typeof performance !== 'undefined' && performance.getEntriesByType) {
    try {
      return performance.getEntriesByType(type);
    } catch (e) {
      // Silently fail
    }
  }

  return [];
}

/**
 * Logs a summary of all performance measures.
 */
export function logPerformanceSummary(): void {
  if (!IS_DEV) return;

  const measures = getPerformanceEntries('measure');

  if (measures.length === 0) {
    console.debug('[Performance] No performance measures recorded');
    return;
  }

  console.group('[Performance] Summary');
  measures.forEach((entry) => {
    console.debug(`  ${entry.name}: ${entry.duration.toFixed(2)}ms`);
  });
  console.groupEnd();
}

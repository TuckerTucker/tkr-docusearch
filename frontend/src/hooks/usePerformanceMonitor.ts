/**
 * usePerformanceMonitor Hook
 *
 * Agent 12: Performance Optimizer
 * Wave 3 - BBox Overlay React Implementation
 *
 * React hook for monitoring component performance metrics.
 * Tracks render times, event handler latency, and custom marks.
 *
 * Features:
 * - Automatic render time tracking
 * - Custom performance marks and measures
 * - Event handler latency tracking
 * - Development-only monitoring (no overhead in production)
 * - Integration with browser Performance API
 *
 * @example
 * ```typescript
 * const { mark, measure, logRenderTime } = usePerformanceMonitor('BoundingBoxOverlay');
 *
 * const handleClick = () => {
 *   mark('click-start');
 *   // ... handle click
 *   mark('click-end');
 *   measure('click-handler', 'click-start', 'click-end');
 * };
 * ```
 */

import { useEffect, useRef, useCallback } from 'react';

export interface PerformanceMetrics {
  renderTime: number;
  marks: Map<string, number>;
  measures: Map<string, number>;
}

export interface UsePerformanceMonitorOptions {
  /**
   * Component name for logging
   */
  componentName: string;
  /**
   * Whether to enable monitoring
   * @default process.env.NODE_ENV === 'development'
   */
  enabled?: boolean;
  /**
   * Whether to log render times automatically
   * @default false
   */
  logRenders?: boolean;
  /**
   * Threshold in ms for logging slow operations
   * @default 16.67 (60fps)
   */
  slowThreshold?: number;
}

export interface UsePerformanceMonitorResult {
  /**
   * Create a performance mark
   */
  mark: (markName: string) => void;
  /**
   * Measure duration between two marks
   */
  measure: (measureName: string, startMark: string, endMark: string) => number | null;
  /**
   * Log render time
   */
  logRenderTime: (label?: string) => void;
  /**
   * Track event handler execution time
   */
  trackHandler: <T extends (...args: any[]) => any>(
    handler: T,
    handlerName: string
  ) => T;
  /**
   * Get current metrics
   */
  getMetrics: () => PerformanceMetrics;
  /**
   * Clear all marks and measures
   */
  clear: () => void;
}

const IS_DEV = process.env.NODE_ENV === 'development';

/**
 * Hook for monitoring component performance.
 *
 * Provides utilities to track render times, event handlers, and custom operations.
 * Only active in development mode by default to avoid production overhead.
 *
 * @param options - Performance monitoring options
 * @returns Performance monitoring utilities
 */
export function usePerformanceMonitor(
  options: UsePerformanceMonitorOptions
): UsePerformanceMonitorResult {
  const {
    componentName,
    enabled = IS_DEV,
    logRenders = false,
    slowThreshold = 16.67, // 60fps = 16.67ms per frame
  } = options;

  const renderStartRef = useRef<number>(0);
  const renderCountRef = useRef<number>(0);
  const metricsRef = useRef<PerformanceMetrics>({
    renderTime: 0,
    marks: new Map(),
    measures: new Map(),
  });

  // Track render start
  renderStartRef.current = performance.now();
  renderCountRef.current += 1;

  /**
   * Create a performance mark
   */
  const mark = useCallback(
    (markName: string): void => {
      if (!enabled) return;

      const timestamp = performance.now();
      const fullMarkName = `${componentName}:${markName}`;

      // Store in our metrics
      metricsRef.current.marks.set(fullMarkName, timestamp);

      // Also use Performance API if available
      if (typeof performance !== 'undefined' && performance.mark) {
        try {
          performance.mark(fullMarkName);
        } catch (e) {
          // Silently fail if marks not supported
        }
      }
    },
    [enabled, componentName]
  );

  /**
   * Measure duration between two marks
   */
  const measure = useCallback(
    (measureName: string, startMark: string, endMark: string): number | null => {
      if (!enabled) return null;

      const fullMeasureName = `${componentName}:${measureName}`;
      const fullStartMark = `${componentName}:${startMark}`;
      const fullEndMark = `${componentName}:${endMark}`;

      const startTime = metricsRef.current.marks.get(fullStartMark);
      const endTime = metricsRef.current.marks.get(fullEndMark);

      if (startTime === undefined || endTime === undefined) {
        console.warn(
          `[PerformanceMonitor] Missing marks for measure "${measureName}"`
        );
        return null;
      }

      const duration = endTime - startTime;
      metricsRef.current.measures.set(fullMeasureName, duration);

      // Log if slow
      if (duration > slowThreshold) {
        console.warn(
          `[PerformanceMonitor] ${fullMeasureName} took ${duration.toFixed(2)}ms (threshold: ${slowThreshold}ms)`
        );
      }

      // Use Performance API if available
      if (typeof performance !== 'undefined' && performance.measure) {
        try {
          performance.measure(fullMeasureName, fullStartMark, fullEndMark);
        } catch (e) {
          // Silently fail if measures not supported
        }
      }

      return duration;
    },
    [enabled, componentName, slowThreshold]
  );

  /**
   * Log render time
   */
  const logRenderTime = useCallback(
    (label: string = 'render'): void => {
      if (!enabled) return;

      const renderEnd = performance.now();
      const duration = renderEnd - renderStartRef.current;

      metricsRef.current.renderTime = duration;

      if (logRenders || duration > slowThreshold) {
        console.log(
          `[PerformanceMonitor] ${componentName} ${label} #${renderCountRef.current} took ${duration.toFixed(2)}ms`
        );
      }
    },
    [enabled, componentName, logRenders, slowThreshold]
  );

  /**
   * Track event handler execution time
   */
  const trackHandler = useCallback(
    <T extends (...args: any[]) => any>(handler: T, handlerName: string): T => {
      if (!enabled) return handler;

      return ((...args: Parameters<T>) => {
        const startTime = performance.now();
        const result = handler(...args);
        const duration = performance.now() - startTime;

        const fullHandlerName = `${componentName}:handler:${handlerName}`;
        metricsRef.current.measures.set(fullHandlerName, duration);

        if (duration > slowThreshold) {
          console.warn(
            `[PerformanceMonitor] ${fullHandlerName} took ${duration.toFixed(2)}ms`
          );
        }

        return result;
      }) as T;
    },
    [enabled, componentName, slowThreshold]
  );

  /**
   * Get current metrics
   */
  const getMetrics = useCallback((): PerformanceMetrics => {
    return {
      ...metricsRef.current,
      marks: new Map(metricsRef.current.marks),
      measures: new Map(metricsRef.current.measures),
    };
  }, []);

  /**
   * Clear all marks and measures
   */
  const clear = useCallback((): void => {
    metricsRef.current.marks.clear();
    metricsRef.current.measures.clear();

    // Clear Performance API marks/measures for this component
    if (typeof performance !== 'undefined' && performance.clearMarks) {
      try {
        performance.clearMarks(componentName);
        performance.clearMeasures(componentName);
      } catch (e) {
        // Silently fail
      }
    }
  }, [componentName]);

  // Log render time on mount/unmount if enabled
  useEffect(() => {
    if (enabled && logRenders) {
      logRenderTime('effect-complete');
    }

    return () => {
      if (enabled && logRenders) {
        console.log(
          `[PerformanceMonitor] ${componentName} unmounting after ${renderCountRef.current} renders`
        );
      }
    };
  }, [enabled, logRenders, logRenderTime, componentName]);

  return {
    mark,
    measure,
    logRenderTime,
    trackHandler,
    getMetrics,
    clear,
  };
}

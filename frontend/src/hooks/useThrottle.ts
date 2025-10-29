/**
 * useThrottle Hook
 *
 * Agent 12: Performance Optimizer
 * Wave 3 - BBox Overlay React Implementation
 *
 * Generic throttle hook for limiting callback execution frequency.
 * Ensures function is called at most once per specified time period.
 *
 * Features:
 * - TypeScript generics for type safety
 * - Automatic cleanup on unmount
 * - Configurable interval
 * - Leading/trailing edge options
 *
 * @example
 * ```typescript
 * const handleResize = useThrottle((dimensions: Dimensions) => {
 *   setDimensions(dimensions);
 * }, 100);
 * ```
 */

import { useCallback, useRef, useEffect } from 'react';

export interface UseThrottleOptions {
  /**
   * Interval in milliseconds
   * @default 100
   */
  interval?: number;
  /**
   * Call function on leading edge
   * @default true
   */
  leading?: boolean;
  /**
   * Call function on trailing edge
   * @default false
   */
  trailing?: boolean;
}

/**
 * Hook that throttles a callback function.
 *
 * Limits the rate at which a function can fire. The function will be called
 * at most once per specified interval.
 *
 * @param callback - The function to throttle
 * @param interval - Interval in milliseconds (default: 100ms)
 * @param options - Additional throttle options
 * @returns Throttled function
 */
export function useThrottle<T extends (...args: any[]) => void>(
  callback: T,
  interval: number = 100,
  options: Omit<UseThrottleOptions, 'interval'> = {}
): T {
  const { leading = true, trailing = false } = options;
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastCallRef = useRef<number>(0);
  const lastArgsRef = useRef<Parameters<T> | null>(null);
  const callbackRef = useRef(callback);

  // Keep callback ref up to date
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return useCallback(
    ((...args: Parameters<T>) => {
      const now = Date.now();
      const timeSinceLastCall = now - lastCallRef.current;

      // Store arguments for potential trailing call
      lastArgsRef.current = args;

      // Call immediately if leading edge and enough time has passed
      if (leading && timeSinceLastCall >= interval) {
        lastCallRef.current = now;
        callbackRef.current(...args);
      } else if (trailing && !timeoutRef.current) {
        // Setup trailing edge call
        const remainingTime = interval - timeSinceLastCall;
        timeoutRef.current = setTimeout(() => {
          lastCallRef.current = Date.now();
          if (lastArgsRef.current) {
            callbackRef.current(...lastArgsRef.current);
          }
          timeoutRef.current = null;
        }, remainingTime > 0 ? remainingTime : interval);
      }
    }) as T,
    [interval, leading, trailing]
  );
}

/**
 * Hook that throttles with requestAnimationFrame for 60fps performance.
 *
 * Ideal for scroll and resize handlers that update visual elements.
 * Ensures callbacks run at most once per animation frame.
 *
 * @param callback - The function to throttle
 * @returns Throttled function that runs on animation frames
 *
 * @example
 * ```typescript
 * const handleScroll = useThrottleRAF(() => {
 *   updateScrollPosition(window.scrollY);
 * });
 *
 * useEffect(() => {
 *   window.addEventListener('scroll', handleScroll);
 *   return () => window.removeEventListener('scroll', handleScroll);
 * }, [handleScroll]);
 * ```
 */
export function useThrottleRAF<T extends (...args: any[]) => void>(
  callback: T
): T {
  const rafIdRef = useRef<number | null>(null);
  const lastArgsRef = useRef<Parameters<T> | null>(null);
  const callbackRef = useRef(callback);

  // Keep callback ref up to date
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  // Cleanup RAF on unmount
  useEffect(() => {
    return () => {
      if (rafIdRef.current !== null) {
        cancelAnimationFrame(rafIdRef.current);
      }
    };
  }, []);

  return useCallback(
    ((...args: Parameters<T>) => {
      // Store latest arguments
      lastArgsRef.current = args;

      // Skip if already scheduled
      if (rafIdRef.current !== null) {
        return;
      }

      // Schedule on next animation frame
      rafIdRef.current = requestAnimationFrame(() => {
        if (lastArgsRef.current) {
          callbackRef.current(...lastArgsRef.current);
        }
        rafIdRef.current = null;
      });
    }) as T,
    []
  );
}

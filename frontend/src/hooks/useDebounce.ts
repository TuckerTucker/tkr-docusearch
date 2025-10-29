/**
 * useDebounce Hook
 *
 * Agent 12: Performance Optimizer
 * Wave 3 - BBox Overlay React Implementation
 *
 * Generic debounce hook for delaying callback execution until after
 * a specified delay has passed without new calls.
 *
 * Features:
 * - TypeScript generics for type safety
 * - Automatic cleanup on unmount
 * - Configurable delay
 * - Leading/trailing edge options
 *
 * @example
 * ```typescript
 * const handleHover = useDebounce((chunkId: string | null) => {
 *   setHoveredChunkId(chunkId);
 * }, 50);
 * ```
 */

import { useCallback, useRef, useEffect } from 'react';

export interface UseDebounceOptions {
  /**
   * Delay in milliseconds
   * @default 300
   */
  delay?: number;
  /**
   * Call function on leading edge
   * @default false
   */
  leading?: boolean;
  /**
   * Call function on trailing edge
   * @default true
   */
  trailing?: boolean;
}

/**
 * Hook that debounces a callback function.
 *
 * Delays executing the callback until after the specified delay has passed
 * since the last time the debounced function was invoked.
 *
 * @param callback - The function to debounce
 * @param delay - Delay in milliseconds (default: 300ms)
 * @param options - Additional debounce options
 * @returns Debounced function
 */
export function useDebounce<T extends (...args: any[]) => void>(
  callback: T,
  delay: number = 300,
  options: Omit<UseDebounceOptions, 'delay'> = {}
): T {
  const { leading = false, trailing = true } = options;
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastCallRef = useRef<number>(0);
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

      // Clear existing timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      // Call immediately if leading edge and first call or after delay
      if (leading && (lastCallRef.current === 0 || timeSinceLastCall >= delay)) {
        lastCallRef.current = now;
        callbackRef.current(...args);
      }

      // Setup trailing edge call
      if (trailing) {
        timeoutRef.current = setTimeout(() => {
          lastCallRef.current = Date.now();
          callbackRef.current(...args);
          timeoutRef.current = null;
        }, delay);
      }
    }) as T,
    [delay, leading, trailing]
  );
}

/**
 * Hook that debounces a value.
 *
 * Returns a debounced version of the value that only updates after
 * the specified delay has passed without the value changing.
 *
 * @param value - The value to debounce
 * @param delay - Delay in milliseconds (default: 300ms)
 * @returns Debounced value
 *
 * @example
 * ```typescript
 * const [searchTerm, setSearchTerm] = useState('');
 * const debouncedSearchTerm = useDebouncedValue(searchTerm, 500);
 *
 * useEffect(() => {
 *   // Only runs 500ms after user stops typing
 *   performSearch(debouncedSearchTerm);
 * }, [debouncedSearchTerm]);
 * ```
 */
export function useDebouncedValue<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timeout = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timeout);
    };
  }, [value, delay]);

  return debouncedValue;
}

// Import useState for useDebouncedValue
import { useState } from 'react';

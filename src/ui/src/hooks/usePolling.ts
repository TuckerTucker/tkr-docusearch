/**
 * Generic Polling Hook - DocuSearch UI
 * Provider: Agent 2 (Design System Engineer)
 * Consumers: Agent 3, Agent 4 (for useDocumentStatus)
 */

import { useEffect, useRef } from 'react';

/**
 * Options for polling behavior
 */
export interface PollingOptions {
  /** Polling interval in milliseconds */
  interval: number;
  /** Whether polling is enabled */
  enabled?: boolean;
  /** Callback on error */
  onError?: (error: Error) => void;
}

/**
 * Generic polling hook for periodic data fetching
 *
 * @param callback - Async function to call on each interval
 * @param options - Polling configuration
 *
 * @example
 * usePolling(
 *   async () => await fetchStatus(),
 *   { interval: 2000, enabled: isProcessing }
 * );
 */
export function usePolling(
  callback: () => Promise<void>,
  options: PollingOptions
): void {
  const { interval, enabled = true, onError } = options;
  const savedCallback = useRef(callback);
  const savedOnError = useRef(onError);

  // Update refs to latest callback
  useEffect(() => {
    savedCallback.current = callback;
    savedOnError.current = onError;
  }, [callback, onError]);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    // Execute immediately
    const executeCallback = async () => {
      try {
        await savedCallback.current();
      } catch (error) {
        if (savedOnError.current) {
          savedOnError.current(error as Error);
        } else {
          console.error('Polling error:', error);
        }
      }
    };

    executeCallback();

    // Set up interval
    const intervalId = setInterval(executeCallback, interval);

    return () => {
      clearInterval(intervalId);
    };
  }, [interval, enabled]);
}

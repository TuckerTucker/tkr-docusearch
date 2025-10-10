/**
 * useProcessingTimeout Hook - DocuSearch UI
 * Provider: Task 8 (Processing Timeout Detection)
 *
 * Monitors document processing time and triggers timeout after 5 minutes
 */

import { useEffect, useRef } from 'react';
import type { DocumentStatus } from '../lib/types';

/**
 * Processing timeout threshold (5 minutes in milliseconds)
 */
const PROCESSING_TIMEOUT = 5 * 60 * 1000; // 300,000ms

/**
 * Options for useProcessingTimeout hook
 */
export interface UseProcessingTimeoutOptions {
  /** Document ID being monitored */
  documentId: string;
  /** Current document status */
  status: DocumentStatus;
  /** ISO timestamp when processing started */
  startedAt?: string;
  /** Callback triggered on timeout */
  onTimeout: () => void;
}

/**
 * Custom hook to detect processing timeouts
 *
 * Monitors documents in processing/uploading state and triggers a callback
 * if processing exceeds 5 minutes. Automatically clears timeout when status changes.
 *
 * @param options - Hook configuration
 *
 * @example
 * useProcessingTimeout({
 *   documentId: doc.id,
 *   status: doc.status,
 *   startedAt: doc.started_at,
 *   onTimeout: () => handleProcessingTimeout(doc.id),
 * });
 */
export function useProcessingTimeout({
  documentId,
  status,
  startedAt,
  onTimeout,
}: UseProcessingTimeoutOptions): void {
  const timeoutRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    // Only track processing/uploading documents
    if (status !== 'processing' && status !== 'uploading') {
      // Clear timeout if status changes to completed/error
      if (timeoutRef.current !== undefined) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = undefined;
      }
      return;
    }

    // Calculate time already elapsed
    const startTime = startedAt ? new Date(startedAt).getTime() : Date.now();
    const elapsed = Date.now() - startTime;
    const remaining = Math.max(0, PROCESSING_TIMEOUT - elapsed);

    // Set timeout for remaining time
    timeoutRef.current = window.setTimeout(() => {
      console.warn(`Processing timeout for document: ${documentId}`);
      onTimeout();
    }, remaining);

    // Cleanup
    return () => {
      if (timeoutRef.current !== undefined) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [documentId, status, startedAt, onTimeout]);
}

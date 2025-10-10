/**
 * Document Status Polling Hook - DocuSearch UI
 * Provider: Agent 2 (Design System Engineer)
 * Consumers: Agent 4 (DocumentCard), Agent 5 (App)
 */

import { useState, useCallback } from 'react';
import { usePolling } from './usePolling';
import type { DocumentCardProps, DocumentStatus } from '../lib/types';
import { API_CONFIG } from '../lib/constants';

/**
 * Options for document status polling
 */
export interface DocumentStatusOptions {
  /** Document ID to poll */
  documentId: string;
  /** Whether to enable polling (default: true) */
  enabled?: boolean;
  /** Callback when document status changes */
  onStatusChange?: (status: DocumentStatus) => void;
  /** Callback when processing completes */
  onComplete?: (document: DocumentCardProps) => void;
  /** Callback on error */
  onError?: (error: Error) => void;
}

/**
 * Hook for polling document processing status
 *
 * Automatically polls the document status endpoint at the configured interval
 * and updates local state. Polling stops when document reaches 'completed' or 'error' state.
 *
 * @param options - Polling configuration
 * @returns Current document data and loading state
 *
 * @example
 * const { document, isLoading } = useDocumentStatus({
 *   documentId: 'doc-123',
 *   onComplete: (doc) => console.log('Processing complete!', doc),
 * });
 */
export function useDocumentStatus(options: DocumentStatusOptions) {
  const {
    documentId,
    enabled = true,
    onStatusChange,
    onComplete,
    onError,
  } = options;

  const [document, setDocument] = useState<DocumentCardProps | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  // Determine if we should continue polling
  const shouldPoll =
    enabled &&
    (!document ||
      (document.status !== 'completed' && document.status !== 'error'));

  const fetchStatus = useCallback(async () => {
    try {
      setIsLoading(true);

      // Mock API call - Will be replaced with real API in Wave 4
      // const response = await fetch(
      //   `${API_CONFIG.baseURL}/api/document/${documentId}`
      // );
      // const data = await response.json();

      // For Wave 1-3: Return mock data
      // This will be replaced by real API service in Wave 4
      const mockDocument: DocumentCardProps = {
        id: documentId,
        title: 'Mock Document',
        status: 'processing',
        fileType: 'PDF',
        progress: 50,
        stages: [
          { label: 'Upload', status: 'completed' },
          { label: 'Transcribe Audio', status: 'in-progress' },
          { label: 'Embeddings', status: 'pending' },
          { label: 'Finalizing', status: 'pending' },
        ],
      };

      const previousStatus = document?.status;
      setDocument(mockDocument);
      setError(null);

      // Call status change callback
      if (onStatusChange && previousStatus !== mockDocument.status) {
        onStatusChange(mockDocument.status);
      }

      // Call completion callback
      if (onComplete && mockDocument.status === 'completed') {
        onComplete(mockDocument);
      }
    } catch (err) {
      const error = err as Error;
      setError(error);
      if (onError) {
        onError(error);
      }
    } finally {
      setIsLoading(false);
    }
  }, [documentId, document?.status, onStatusChange, onComplete, onError]);

  // Set up polling
  usePolling(fetchStatus, {
    interval: API_CONFIG.pollingInterval,
    enabled: shouldPoll,
    onError,
  });

  return {
    /** Current document data */
    document,
    /** Whether initial fetch is in progress */
    isLoading,
    /** Last error encountered */
    error,
    /** Manual refresh function */
    refresh: fetchStatus,
  };
}

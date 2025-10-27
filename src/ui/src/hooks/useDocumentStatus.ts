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

      // Fetch real document status from API
      const response = await fetch(
        `${API_CONFIG.baseURL}/api/document/${documentId}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          signal: AbortSignal.timeout(API_CONFIG.timeout),
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch document status: ${response.status}`);
      }

      const data = await response.json();

      // Transform API response to DocumentCardProps format
      const fetchedDocument: DocumentCardProps = {
        id: data.id,
        title: data.title,
        status: data.status,
        fileType: data.file_type,
        thumbnail: data.thumbnail_url,
        progress: data.processing?.progress,
        errorMessage: data.processing?.error_message,
        author: data.metadata?.author,
        published: data.metadata?.published,
        pages: data.metadata?.pages,
        size: data.metadata?.size_bytes ? `${(data.metadata.size_bytes / 1024 / 1024).toFixed(1)} MB` : undefined,
        visualEmbeddings: data.embeddings?.visual_count,
        textEmbeddings: data.embeddings?.text_count,
        textChunks: data.embeddings?.chunk_count,
        dateProcessed: data.processed_at,
      };

      const previousStatus = document?.status;
      setDocument(fetchedDocument);
      setError(null);

      // Call status change callback
      if (onStatusChange && previousStatus !== fetchedDocument.status) {
        onStatusChange(fetchedDocument.status);
      }

      // Call completion callback
      if (onComplete && fetchedDocument.status === 'completed') {
        onComplete(fetchedDocument);
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

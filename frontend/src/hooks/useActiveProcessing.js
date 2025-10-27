/**
 * useActiveProcessing Hook - Fetch and hydrate active processing documents
 *
 * Fetches documents currently being processed from the server and hydrates
 * them into the temp documents store. This enables cross-browser/tab
 * synchronization - when a new tab opens, it can see documents being
 * processed in other tabs.
 *
 * Architecture: Option 1 - Server-Side Processing Queue
 * - On mount: Fetch /status/queue to get active processing documents
 * - Hydrate temp documents from server state
 * - WebSocket updates keep state synchronized
 * - Single source of truth: backend /status/queue endpoint
 */

import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api.js';
import { useDocumentStore } from '../stores/useDocumentStore.js';

/**
 * Fetch active processing queue and hydrate temp documents
 *
 * @param {Object} options - Hook options
 * @param {boolean} [options.enabled=true] - Enable/disable the query
 * @param {number} [options.refetchInterval=5000] - Polling interval in ms (0 to disable)
 * @returns {Object} Query result with active processing documents
 */
export function useActiveProcessing(options = {}) {
  const { enabled = true, refetchInterval = 5000 } = options;

  const addTempDocument = useDocumentStore((state) => state.addTempDocument);
  const updateTempDocument = useDocumentStore((state) => state.updateTempDocument);

  // Fetch active processing queue
  const query = useQuery({
    queryKey: ['processing', 'active'],
    queryFn: async () => {
      const response = await api.status.getActiveQueue({ limit: 100 });
      return response;
    },
    enabled,
    refetchInterval, // Poll every 5 seconds as backup to WebSocket
    refetchOnMount: true,
    refetchOnWindowFocus: true,
    staleTime: 3000, // Consider data stale after 3 seconds
  });

  // Hydrate temp documents when query data changes
  useEffect(() => {
    if (!query.data?.queue) {
      return;
    }

    const activeDocuments = query.data.queue;

    console.log(`[useActiveProcessing] Hydrating ${activeDocuments.length} active documents`);

    activeDocuments.forEach((doc) => {
      const {
        doc_id,
        filename,
        status,
        progress,
        stage,
      } = doc;

      // Skip completed or failed documents (they'll appear in the main list)
      if (status === 'completed' || status === 'failed') {
        return;
      }

      // Get current temp document to check if it already exists
      const existingTempDoc = useDocumentStore.getState().tempDocuments.get(doc_id);

      if (!existingTempDoc) {
        // Add new temp document with initial state
        console.log(`[useActiveProcessing] Adding temp doc: ${filename} (${doc_id.slice(0, 8)}...)`);
        addTempDocument(doc_id, filename);

        // Only set initial state for newly added documents
        // Don't overwrite existing documents - WebSocket provides fresher updates
        const normalizedProgress = Math.round((progress || 0) * 100);
        const updates = {
          status,
          ...(stage && { stage }),
          progress: normalizedProgress,
        };
        updateTempDocument(doc_id, updates);
      }
      // If document already exists, don't update it - WebSocket has fresher data
    });
  }, [query.data, addTempDocument, updateTempDocument]);

  return {
    activeDocuments: query.data?.queue || [],
    activeCount: query.data?.active || 0,
    totalCount: query.data?.total || 0,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}

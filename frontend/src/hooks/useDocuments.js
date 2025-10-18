/**
 * useDocuments Hook - Fetch and cache document list
 *
 * React Query wrapper for document list with optimistic delete mutation.
 *
 * Provider: infrastructure-agent (Wave 1)
 * Contract: integration-contracts/hooks.contract.md
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api.js';

/**
 * Hook for fetching document list with filters
 *
 * @param {Object} filters - Query filters
 * @returns {Object} Query result with documents and delete mutation
 */
export function useDocuments(filters = {}) {
  const queryClient = useQueryClient();

  // Query for documents list
  const query = useQuery({
    queryKey: ['documents', filters],
    queryFn: () => api.documents.list(filters),
    staleTime: 30000, // 30 seconds
  });

  // Mutation for delete with optimistic updates
  const deleteMutation = useMutation({
    mutationFn: (docId) => api.documents.delete(docId),
    onMutate: async (docId) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['documents'] });

      // Snapshot the previous value
      const previousData = queryClient.getQueryData(['documents', filters]);

      // Optimistically update to remove the document
      queryClient.setQueryData(['documents', filters], (old) => {
        if (!old) return old;
        return {
          ...old,
          documents: old.documents.filter((doc) => doc.doc_id !== docId),
          total: old.total - 1,
        };
      });

      // Return context for rollback
      return { previousData };
    },
    onError: (err, docId, context) => {
      // Rollback on error
      if (context?.previousData) {
        queryClient.setQueryData(['documents', filters], context.previousData);
      }
    },
    onSettled: () => {
      // Refetch to sync with server
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  return {
    documents: query.data?.documents || [],
    totalCount: query.data?.total || 0,
    limit: query.data?.limit || filters.limit || 50,
    offset: query.data?.offset || filters.offset || 0,
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
    deleteDocument: deleteMutation.mutateAsync,
    isDeleting: deleteMutation.isPending,
  };
}

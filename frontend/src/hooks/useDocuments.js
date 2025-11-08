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
 * @param {Object} [filters={}] - Query filters
 * @param {number} [filters.limit] - Maximum documents per page
 * @param {number} [filters.offset] - Number of documents to skip
 * @param {string} [filters.search] - Search term filter
 * @returns {Object} Query result with documents and delete mutation
 * @returns {Array} returns.documents - Array of document objects
 * @returns {number} returns.totalCount - Total number of documents
 * @returns {number} returns.limit - Current limit value
 * @returns {number} returns.offset - Current offset value
 * @returns {boolean} returns.isLoading - Loading state for initial fetch
 * @returns {Error|null} returns.error - Error object if query failed
 * @returns {Function} returns.refetch - Function to manually refetch documents
 * @returns {Function} returns.deleteDocument - Function to delete a document (async)
 * @returns {boolean} returns.isDeleting - Loading state for delete mutation
 *
 * @example
 * // Basic usage with pagination
 * const { documents, totalCount, isLoading } = useDocuments({
 *   limit: 50,
 *   offset: 0,
 * });
 *
 * @example
 * // Delete a document with optimistic updates
 * const { documents, deleteDocument, isDeleting } = useDocuments();
 *
 * const handleDelete = async (docId) => {
 *   try {
 *     await deleteDocument(docId);
 *     console.log('Document deleted successfully');
 *   } catch (error) {
 *     console.error('Delete failed:', error);
 *   }
 * };
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

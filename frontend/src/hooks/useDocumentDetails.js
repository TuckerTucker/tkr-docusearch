/**
 * useDocumentDetails Hook - Fetch document metadata and markdown
 *
 * Fetches document and markdown in parallel using React Query.
 *
 * Provider: infrastructure-agent (Wave 1)
 * Contract: integration-contracts/hooks.contract.md
 */

import { useQueries } from '@tanstack/react-query';
import { api } from '../services/api.js';

/**
 * Hook for fetching document details (metadata + markdown)
 *
 * @param {string} docId - Document ID
 * @returns {Object} Combined query result
 */
export function useDocumentDetails(docId) {
  const queries = useQueries({
    queries: [
      {
        queryKey: ['document', docId],
        queryFn: () => api.documents.get(docId),
        enabled: !!docId,
        staleTime: 5 * 60 * 1000, // 5 minutes
      },
      {
        queryKey: ['markdown', docId],
        queryFn: () => api.documents.getMarkdown(docId),
        enabled: !!docId,
        staleTime: 5 * 60 * 1000, // 5 minutes
      },
    ],
  });

  const [documentQuery, markdownQuery] = queries;

  return {
    document: documentQuery.data || null,
    markdown: markdownQuery.data || null,
    isLoading: documentQuery.isLoading || markdownQuery.isLoading,
    error: documentQuery.error || markdownQuery.error,
    refetch: () => {
      documentQuery.refetch();
      markdownQuery.refetch();
    },
  };
}

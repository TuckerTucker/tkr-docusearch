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
 * Fetches document metadata and markdown content in parallel using React Query.
 * Both queries are cached with 5-minute staleTime for optimal performance.
 *
 * @param {string} docId - Document ID
 * @returns {Object} Combined query result
 * @returns {Object|null} returns.document - Document metadata object
 * @returns {string|null} returns.markdown - Markdown content of document
 * @returns {boolean} returns.isLoading - Loading state (true if either query loading)
 * @returns {Error|null} returns.error - Error object if either query failed
 * @returns {Function} returns.refetch - Function to refetch both queries
 *
 * @example
 * // Basic usage
 * const { document, markdown, isLoading, error } = useDocumentDetails(docId);
 *
 * if (isLoading) return <Spinner />;
 * if (error) return <Error message={error.message} />;
 *
 * return (
 *   <div>
 *     <h1>{document.filename}</h1>
 *     <Markdown content={markdown} />
 *   </div>
 * );
 *
 * @example
 * // Manual refetch
 * const { document, markdown, refetch } = useDocumentDetails(docId);
 *
 * const handleRefresh = () => {
 *   refetch(); // Refetches both metadata and markdown
 * };
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

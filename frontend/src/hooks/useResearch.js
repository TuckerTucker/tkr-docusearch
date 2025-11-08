/**
 * useResearch Hook - Submit research queries with caching
 *
 * React Query mutation for research API with query caching.
 *
 * Provider: infrastructure-agent (Wave 1)
 * Contract: integration-contracts/hooks.contract.md
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api.js';

/**
 * Hook for research queries
 *
 * Submits research questions and receives AI-generated answers with inline citations.
 * Caches results using React Query for efficient re-renders.
 *
 * @returns {Object} Mutation interface for research
 * @returns {Function} returns.ask - Async function to submit research query
 * @returns {string|null} returns.answer - AI-generated answer text
 * @returns {Array} returns.references - Array of source documents with metadata
 * @returns {string|null} returns.query - The submitted query text
 * @returns {Object|null} returns.metadata - Full metadata object from API
 * @returns {string|null} returns.model - Model used for generation (e.g., 'gpt-4o-mini')
 * @returns {boolean} returns.isLoading - Loading state during query processing
 * @returns {Error|null} returns.error - Error object if query failed
 * @returns {Function} returns.reset - Function to reset mutation state
 *
 * @example
 * // Basic research query
 * const { ask, answer, references, isLoading } = useResearch();
 *
 * const handleAsk = async () => {
 *   try {
 *     await ask('What are the main findings of this document?');
 *   } catch (error) {
 *     console.error('Research failed:', error);
 *   }
 * };
 *
 * @example
 * // Display results with references
 * const { answer, references, isLoading, model } = useResearch();
 *
 * if (isLoading) return <Spinner />;
 *
 * return (
 *   <div>
 *     <p>{answer}</p>
 *     <ul>
 *       {references.map(ref => (
 *         <li key={ref.chunk_id}>{ref.text}</li>
 *       ))}
 *     </ul>
 *     <small>Model: {model}</small>
 *   </div>
 * );
 */
export function useResearch() {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (query) => api.research.ask(query),
    onSuccess: (data, query) => {
      // Cache the result
      queryClient.setQueryData(['research', query], data);
    },
  });

  return {
    ask: mutation.mutateAsync,
    answer: mutation.data?.answer || null,
    references: mutation.data?.sources || [], // API returns 'sources' not 'references'
    query: mutation.variables || mutation.data?.query || null, // Use submitted query (mutation.variables) as fallback
    metadata: mutation.data?.metadata || null, // Full metadata object
    model: mutation.data?.metadata?.model_used || null, // Backward compatibility
    isLoading: mutation.isPending,
    error: mutation.error,
    reset: mutation.reset,
  };
}

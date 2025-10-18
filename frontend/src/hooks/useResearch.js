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
 * @returns {Object} Mutation interface for research
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
    query: mutation.data?.query || null,
    model: mutation.data?.metadata?.model_used || null,
    isLoading: mutation.isPending,
    error: mutation.error,
    reset: mutation.reset,
  };
}

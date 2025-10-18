/**
 * Research Service - Wrapper for research API
 *
 * Provides convenient interface for research operations, primarily wraps
 * the API service but allows for future client-side processing.
 *
 * Provider: infrastructure-agent (Wave 1)
 * Contract: integration-contracts/api-service.contract.md
 */

import { api } from './api.js';

/**
 * Research service interface
 */
export const researchService = {
  /**
   * Submit a research question
   *
   * @param {string} query - User's question
   * @returns {Promise<Object>} Answer with citations
   */
  async ask(query) {
    return api.research.ask(query);
  },

  /**
   * Check research API health
   *
   * @returns {Promise<Object>} Health status
   */
  async checkHealth() {
    return api.research.getHealth();
  },

  /**
   * Parse citation format [N] from text
   *
   * @param {string} text - Text with inline citations
   * @returns {Array<{number: number, position: number}>} Citation positions
   */
  parseCitations(text) {
    const citations = [];
    const regex = /\[(\d+)\]/g;
    let match;

    while ((match = regex.exec(text)) !== null) {
      citations.push({
        number: parseInt(match[1], 10),
        position: match.index,
      });
    }

    return citations;
  },

  /**
   * Validate query before submission
   *
   * @param {string} query - Query to validate
   * @returns {Object} Validation result
   */
  validateQuery(query) {
    if (!query || typeof query !== 'string') {
      return { valid: false, error: 'Query is required' };
    }

    const trimmed = query.trim();

    if (trimmed.length < 3) {
      return { valid: false, error: 'Query must be at least 3 characters' };
    }

    if (trimmed.length > 500) {
      return { valid: false, error: 'Query must be less than 500 characters' };
    }

    return { valid: true, query: trimmed };
  },
};

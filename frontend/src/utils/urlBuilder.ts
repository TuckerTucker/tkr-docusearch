/**
 * URL Builder Utility
 *
 * Agent 9: Research Navigation Enhancer
 * Wave 1 - BBox Overlay React Implementation
 *
 * Provides utilities for building URLs with optional chunk_id parameters
 * to enable direct navigation to specific text locations in documents.
 */

/**
 * Parameters for building details page links
 */
export interface DetailsLinkParams {
  /** Document ID */
  docId: string;
  /** Page number (1-indexed) */
  page: number;
  /** Optional chunk ID for direct navigation to specific text location */
  chunkId?: string;
}

/**
 * Source information structure (matches backend SourceInfo model)
 */
export interface SourceInfo {
  id: number;
  doc_id: string;
  filename: string;
  page: number;
  extension: string;
  thumbnail_path?: string;
  date_added: string;
  relevance_score: number;
  chunk_id?: string;
}

/**
 * Build a details page URL with optional chunk_id parameter
 *
 * @param params - Link parameters (docId, page, optional chunkId)
 * @returns URL string in format: /details/{docId}?page={page}[&chunk={chunkId}]
 *
 * @example
 * // Without chunk_id
 * buildDetailsUrl({ docId: 'abc123', page: 5 })
 * // => '/details/abc123?page=5'
 *
 * @example
 * // With chunk_id
 * buildDetailsUrl({ docId: 'abc123', page: 5, chunkId: 'abc123-chunk0042' })
 * // => '/details/abc123?page=5&chunk=abc123-chunk0042'
 */
export function buildDetailsUrl(params: DetailsLinkParams): string {
  const { docId, page, chunkId } = params;

  // Validate inputs
  if (!docId || typeof docId !== 'string') {
    throw new Error('docId is required and must be a string');
  }

  if (!page || typeof page !== 'number' || page < 1) {
    throw new Error('page is required and must be a positive number');
  }

  // Build base URL
  const baseUrl = `/details/${docId}`;
  const searchParams = new URLSearchParams();
  searchParams.set('page', page.toString());

  // Add chunk_id if provided
  if (chunkId && typeof chunkId === 'string' && chunkId.trim()) {
    searchParams.set('chunk', chunkId.trim());
  }

  return `${baseUrl}?${searchParams.toString()}`;
}

/**
 * Check if a source has chunk context available
 *
 * @param source - Source information object
 * @returns true if source has a valid chunk_id, false otherwise
 *
 * @example
 * hasChunkContext({ chunk_id: 'abc123-chunk0042', ... })
 * // => true
 *
 * @example
 * hasChunkContext({ chunk_id: undefined, ... })
 * // => false
 */
export function hasChunkContext(source: SourceInfo): boolean {
  return !!(source.chunk_id && typeof source.chunk_id === 'string' && source.chunk_id.trim());
}

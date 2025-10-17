/**
 * DocumentsAPIClient - Documents API wrapper
 *
 * Provides wrapper for Documents API endpoints with query building,
 * error handling, and response parsing.
 *
 * Provider: library-agent (Wave 1)
 * Contract: integration-contracts/documents-api.contract.md
 */

/**
 * Documents API Client
 * Wraps GET /documents and GET /documents/{doc_id} endpoints
 */
export class DocumentsAPIClient {
  /**
   * Create API client
   * @param {string} baseUrl - Base URL (default: http://localhost:8002)
   */
  constructor(baseUrl = 'http://localhost:8002') {
    this.baseUrl = baseUrl;
  }

  /**
   * List documents with filtering and pagination
   *
   * @param {Object} options - Query options
   * @param {number} [options.limit=50] - Results per page (1-100)
   * @param {number} [options.offset=0] - Pagination offset
   * @param {string} [options.search=null] - Filename filter (case-insensitive)
   * @param {string} [options.sort_by='date_added'] - Sort field (date_added, filename, page_count)
   * @returns {Promise<Object>} Response with documents array, total, limit, offset
   */
  async listDocuments({ limit = 50, offset = 0, search = null, sort_by = 'date_added' } = {}) {
    // Build query string
    const params = new URLSearchParams();
    params.set('limit', Math.min(Math.max(limit, 1), 100).toString());
    params.set('offset', Math.max(offset, 0).toString());

    if (search) {
      params.set('search', search);
    }

    if (sort_by && ['date_added', 'filename', 'page_count'].includes(sort_by)) {
      params.set('sort_by', sort_by);
    }

    const url = `${this.baseUrl}/documents?${params.toString()}`;

    try {
      const response = await fetch(url);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(error.error || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to list documents:', error);
      throw error;
    }
  }

  /**
   * Get detailed document information
   *
   * @param {string} docId - Document ID (SHA-256 hash)
   * @returns {Promise<Object>} Document details with pages, chunks, metadata
   */
  async getDocument(docId) {
    // Validate doc_id format
    if (!docId || !/^[a-zA-Z0-9\-]{8,64}$/.test(docId)) {
      throw new Error('Invalid document ID format');
    }

    const url = `${this.baseUrl}/documents/${docId}`;

    try {
      const response = await fetch(url);

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Document not found');
        }
        const error = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(error.error || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Failed to get document ${docId}:`, error);
      throw error;
    }
  }

  /**
   * Get image URL
   *
   * @param {string} docId - Document ID
   * @param {string} filename - Image filename (e.g., page001.png, page001_thumb.jpg)
   * @returns {string} Full image URL
   */
  getImageUrl(docId, filename) {
    return `${this.baseUrl}/images/${docId}/${filename}`;
  }

  /**
   * Get processing queue
   *
   * @param {Object} options - Query options
   * @param {string} [options.status=null] - Filter by status (queued, parsing, embedding_visual, etc.)
   * @param {number} [options.limit=100] - Maximum results (1-1000)
   * @returns {Promise<Object>} Response with queue items and statistics
   */
  async getProcessingQueue({ status = null, limit = 100 } = {}) {
    const params = new URLSearchParams();
    params.set('limit', Math.min(Math.max(limit, 1), 1000).toString());

    if (status) {
      params.set('status', status);
    }

    const url = `${this.baseUrl}/status/queue?${params.toString()}`;

    try {
      const response = await fetch(url);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(error.error || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to get processing queue:', error);
      throw error;
    }
  }

  /**
   * Get detailed processing status for a document
   *
   * @param {string} docId - Document ID (SHA-256 hash)
   * @returns {Promise<Object>} Full processing status with stage description
   */
  async getProcessingStatus(docId) {
    const url = `${this.baseUrl}/status/${docId}`;

    try {
      const response = await fetch(url);

      if (!response.ok) {
        if (response.status === 404) {
          return null; // Document not found in processing queue
        }
        const error = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(error.error || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Failed to get status for ${docId}:`, error);
      return null; // Return null on error to allow graceful degradation
    }
  }
}

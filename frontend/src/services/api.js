/**
 * API Service - Centralized HTTP client for backend API
 *
 * Provides consistent interface for all REST API requests with
 * standardized error handling, timeouts, and request/response formatting.
 *
 * Provider: infrastructure-agent (Wave 1)
 * Contract: integration-contracts/api-service.contract.md
 */

// Base configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || '';
const REQUEST_TIMEOUT = 30000; // 30 seconds
const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
};

/**
 * Custom API Error class
 */
export class APIError extends Error {
  constructor(message, statusCode, endpoint, originalError = null) {
    super(message);
    this.name = 'APIError';
    this.statusCode = statusCode;
    this.endpoint = endpoint;
    this.originalError = originalError;
  }
}

/**
 * Make fetch request with timeout
 *
 * @param {string} url - Request URL
 * @param {Object} options - Fetch options
 * @param {number} timeout - Timeout in milliseconds
 * @returns {Promise<Response>} Fetch response
 * @throws {APIError} On timeout or network error
 */
async function fetchWithTimeout(url, options = {}, timeout = REQUEST_TIMEOUT) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new APIError('Request timeout', 408, url);
    }
    throw new APIError('Network request failed', 0, url, error);
  }
}

/**
 * Handle API response
 *
 * @param {Response} response - Fetch response
 * @param {string} endpoint - API endpoint
 * @returns {Promise<any>} Parsed JSON response
 * @throws {APIError} On HTTP error
 */
async function handleResponse(response, endpoint) {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
    const message = errorData.error || errorData.message || `HTTP ${response.status}`;
    throw new APIError(message, response.status, endpoint);
  }
  return response.json();
}

// ============================================================================
// Documents API
// ============================================================================

const documents = {
  /**
   * Fetch paginated list of documents with optional filters
   *
   * @param {Object} filters - Query filters
   * @param {string} [filters.search] - Search query
   * @param {string} [filters.sort_by] - Sort order
   * @param {string} [filters.file_type_group] - File type group filter
   * @param {number} [filters.limit=50] - Page size
   * @param {number} [filters.offset=0] - Pagination offset
   * @returns {Promise<Object>} Documents list response
   */
  async list(filters = {}) {
    const {
      search,
      sort_by = 'newest_first',
      file_type_group = 'all',
      limit = 50,
      offset = 0,
    } = filters;

    const params = new URLSearchParams();
    params.set('limit', Math.min(Math.max(limit, 1), 100).toString());
    params.set('offset', Math.max(offset, 0).toString());

    if (search) {
      params.set('search', search);
    }

    if (sort_by) {
      params.set('sort_by', sort_by);
    }

    if (file_type_group && file_type_group !== 'all') {
      params.set('file_type_group', file_type_group);
    }

    const url = `${API_BASE_URL}/documents?${params.toString()}`;
    const response = await fetchWithTimeout(url);
    const data = await handleResponse(response, url);

    // Transform documents: fix field names and make thumbnail URLs absolute
    if (data.documents) {
      data.documents = data.documents.map((doc) => ({
        ...doc,
        // Rename date_added to upload_date for consistency with frontend
        upload_date: doc.date_added,
        // Make thumbnail URL absolute
        thumbnail_url: doc.first_page_thumb?.startsWith('/')
          ? `${API_BASE_URL}${doc.first_page_thumb}`
          : doc.first_page_thumb,
      }));
    }

    return data;
  },

  /**
   * Fetch detailed metadata for a single document
   *
   * @param {string} docId - Document ID
   * @returns {Promise<Object>} Document metadata
   */
  async get(docId) {
    if (!docId || !/^[a-zA-Z0-9\-]{8,64}$/.test(docId)) {
      throw new APIError('Invalid document ID format', 400, 'documents.get');
    }

    const url = `${API_BASE_URL}/documents/${docId}`;
    const response = await fetchWithTimeout(url);
    return handleResponse(response, url);
  },

  /**
   * Fetch extracted markdown content for a document
   *
   * @param {string} docId - Document ID
   * @returns {Promise<string>} Markdown content as text
   */
  async getMarkdown(docId) {
    if (!docId || !/^[a-zA-Z0-9\-]{8,64}$/.test(docId)) {
      throw new APIError('Invalid document ID format', 400, 'documents.getMarkdown');
    }

    const url = `${API_BASE_URL}/documents/${docId}/markdown`;
    const response = await fetchWithTimeout(url);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
      const message = errorData.error || errorData.message || `HTTP ${response.status}`;
      throw new APIError(message, response.status, url);
    }

    // Markdown endpoint returns plain text, not JSON
    return response.text();
  },

  /**
   * Delete a document and all associated files
   *
   * @param {string} docId - Document ID
   * @returns {Promise<Object>} Deletion result
   */
  async delete(docId) {
    if (!docId || !/^[a-zA-Z0-9\-]{8,64}$/.test(docId)) {
      throw new APIError('Invalid document ID format', 400, 'documents.delete');
    }

    const url = `${API_BASE_URL}/documents/${docId}`;
    const response = await fetchWithTimeout(url, {
      method: 'DELETE',
      headers: DEFAULT_HEADERS,
    });
    return handleResponse(response, url);
  },

  /**
   * Fetch server-supported file types and groupings
   *
   * @returns {Promise<Object>} Supported formats configuration
   */
  async getSupportedFormats() {
    const url = `${API_BASE_URL}/documents/supported-formats`;
    const response = await fetchWithTimeout(url);
    return handleResponse(response, url);
  },
};

// ============================================================================
// Upload API
// ============================================================================

const upload = {
  /**
   * Upload a single file to Copyparty
   *
   * @param {File} file - File object from input
   * @param {Function} [onProgress] - Progress callback (0-100)
   * @returns {Promise<Object>} Upload result with temp_id
   */
  async uploadFile(file, onProgress = null) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const formData = new FormData();

      // Copyparty expects "act=bput" for basic PUT uploads
      formData.append('act', 'bput');
      formData.append('f', file);

      // Track upload progress
      if (onProgress) {
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            const progress = Math.round((e.loaded / e.total) * 100);
            onProgress(progress);
          }
        });
      }

      // Handle completion
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve({
            success: true,
            filename: file.name,
          });
        } else {
          reject(
            new APIError(
              `Upload failed: ${xhr.statusText}`,
              xhr.status,
              '/uploads/'
            )
          );
        }
      });

      // Handle errors
      xhr.addEventListener('error', () => {
        reject(
          new APIError(
            'Upload failed: Network error',
            0,
            '/uploads/'
          )
        );
      });

      xhr.addEventListener('timeout', () => {
        reject(
          new APIError(
            'Upload failed: Timeout',
            408,
            '/uploads/'
          )
        );
      });

      // Configure and send
      // Use relative URL to work through Vite proxy in dev and direct in prod
      xhr.open('POST', '/uploads/');

      // Add Basic Authentication for Copyparty uploader account
      // Credentials are loaded from environment variables (VITE_UPLOAD_USERNAME/PASSWORD)
      const username = import.meta.env.VITE_UPLOAD_USERNAME || 'uploader';
      const password = import.meta.env.VITE_UPLOAD_PASSWORD || 'docusearch2024';
      const credentials = btoa(`${username}:${password}`);
      xhr.setRequestHeader('Authorization', `Basic ${credentials}`);

      xhr.timeout = REQUEST_TIMEOUT;
      xhr.send(formData);
    });
  },
};

// ============================================================================
// Research API
// ============================================================================

const research = {
  /**
   * Submit a research question and get AI-generated answer with citations
   *
   * @param {string} query - User's question (3-500 chars)
   * @returns {Promise<Object>} Answer with citations and references
   */
  async ask(query) {
    if (!query || query.length < 3 || query.length > 500) {
      throw new APIError('Query must be between 3 and 500 characters', 400, 'research.ask');
    }

    const url = `${API_BASE_URL}/research/ask`;
    const response = await fetchWithTimeout(url, {
      method: 'POST',
      headers: DEFAULT_HEADERS,
      body: JSON.stringify({ query }),
    });
    return handleResponse(response, url);
  },

  /**
   * Check if research API is available
   *
   * @returns {Promise<Object>} Health status
   */
  async getHealth() {
    const url = `${API_BASE_URL}/research/health`;
    const response = await fetchWithTimeout(url);
    return handleResponse(response, url);
  },
};

// ============================================================================
// Status API
// ============================================================================

const status = {
  /**
   * Get processing worker status
   *
   * @returns {Promise<Object>} Worker status and statistics
   */
  async get() {
    const url = `${API_BASE_URL}/status`;
    const response = await fetchWithTimeout(url);
    return handleResponse(response, url);
  },
};

// ============================================================================
// Exports
// ============================================================================

export const api = {
  documents,
  upload,
  research,
  status,
};

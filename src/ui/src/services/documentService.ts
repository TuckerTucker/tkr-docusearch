/**
 * Document Service - DocuSearch UI
 * Provider: Agent 6 (Services)
 * Consumers: Agent 5 (App), Agent 4 (DocumentCard)
 * Contract: integration-contracts/api-services-contract.md
 *
 * Wave 4: Real API implementation
 */

import type { DocumentCardProps, DocumentFilters, DocumentAPIResponse } from '../lib/types';
import { API_CONFIG } from '../lib/constants';
import { formatBytes } from '../lib/utils';

/**
 * Transform backend API response to frontend DocumentCardProps
 */
function transformDocument(apiDoc: DocumentAPIResponse): DocumentCardProps {
  return {
    id: apiDoc.id,
    title: apiDoc.title,
    status: apiDoc.status,
    fileType: apiDoc.file_type,
    thumbnail: apiDoc.thumbnail_url,
    progress: apiDoc.processing?.progress,
    errorMessage: apiDoc.processing?.error_message,
    author: apiDoc.metadata?.author,
    published: apiDoc.metadata?.published,
    pages: apiDoc.metadata?.pages,
    size: apiDoc.metadata?.size_bytes
      ? formatBytes(apiDoc.metadata.size_bytes)
      : undefined,
    visualEmbeddings: apiDoc.embeddings?.visual_count,
    textEmbeddings: apiDoc.embeddings?.text_count,
    textChunks: apiDoc.embeddings?.chunk_count,
    dateProcessed: apiDoc.processed_at,
  };
}

/**
 * Fetch all documents with optional filters
 *
 * @param filters - Optional filtering and pagination options
 * @returns Promise resolving to array of documents
 *
 * @example
 * const docs = await documentService.listDocuments({ status: ['completed'] });
 */
export async function listDocuments(
  filters?: DocumentFilters
): Promise<DocumentCardProps[]> {
  try {
    // Build query parameters
    const params = new URLSearchParams();
    if (filters?.status) {
      params.append('status', filters.status.join(','));
    }
    if (filters?.fileType) {
      params.append('file_type', filters.fileType.join(','));
    }
    if (filters?.sortBy) {
      params.append('sort_by', filters.sortBy);
    }
    if (filters?.sortOrder) {
      params.append('sort_order', filters.sortOrder);
    }
    if (filters?.limit) {
      params.append('limit', filters.limit.toString());
    }
    if (filters?.offset) {
      params.append('offset', filters.offset.toString());
    }

    const url = `${API_CONFIG.baseURL}/api/documents${params.toString() ? `?${params}` : ''}`;

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      signal: AbortSignal.timeout(API_CONFIG.timeout),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch documents: ${response.status}`);
    }

    const data: DocumentAPIResponse[] = await response.json();
    return data.map(transformDocument);
  } catch (error) {
    console.error('Failed to fetch documents:', error);
    // Return empty array on error rather than crashing
    return [];
  }
}

/**
 * Fetch a single document by ID
 *
 * @param documentId - Document ID
 * @returns Promise resolving to document or undefined
 *
 * @example
 * const doc = await documentService.getDocument('doc-123');
 */
export async function getDocument(
  documentId: string
): Promise<DocumentCardProps | undefined> {
  try {
    const response = await fetch(`${API_CONFIG.baseURL}/api/document/${documentId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      signal: AbortSignal.timeout(API_CONFIG.timeout),
    });

    if (!response.ok) {
      if (response.status === 404) {
        return undefined;
      }
      throw new Error(`Failed to fetch document: ${response.status}`);
    }

    const data: DocumentAPIResponse = await response.json();
    return transformDocument(data);
  } catch (error) {
    console.error(`Failed to fetch document ${documentId}:`, error);
    return undefined;
  }
}

/**
 * Delete a document by ID
 *
 * @param documentId - Document ID to delete
 * @returns Promise resolving to success boolean
 *
 * @example
 * const success = await documentService.deleteDocument('doc-123');
 */
export async function deleteDocument(documentId: string): Promise<boolean> {
  try {
    const response = await fetch(`${API_CONFIG.baseURL}/api/document/${documentId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
      signal: AbortSignal.timeout(API_CONFIG.timeout),
    });

    return response.ok;
  } catch (error) {
    console.error(`Failed to delete document ${documentId}:`, error);
    return false;
  }
}

/**
 * Trigger re-processing of a document
 *
 * @param documentId - Document ID to re-process
 * @returns Promise resolving to success boolean
 *
 * @example
 * const success = await documentService.reprocessDocument('doc-123');
 */
export async function reprocessDocument(documentId: string): Promise<boolean> {
  try {
    const response = await fetch(`${API_CONFIG.baseURL}/api/document/${documentId}/reprocess`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      signal: AbortSignal.timeout(API_CONFIG.timeout),
    });

    return response.ok;
  } catch (error) {
    console.error(`Failed to reprocess document ${documentId}:`, error);
    return false;
  }
}

/**
 * Download document in specified format
 *
 * @param documentId - Document ID
 * @param format - Download format
 * @returns Promise resolving to blob URL
 *
 * @example
 * const url = await documentService.downloadDocument('doc-123', 'markdown');
 * window.open(url, '_blank');
 */
export async function downloadDocument(
  documentId: string,
  format: 'original' | 'markdown' | 'vtt' | 'srt'
): Promise<string> {
  try {
    const endpoint = format === 'markdown'
      ? `${API_CONFIG.baseURL}/api/document/${documentId}/markdown`
      : `${API_CONFIG.baseURL}/api/document/${documentId}/download?format=${format}`;

    const response = await fetch(endpoint, {
      method: 'GET',
      signal: AbortSignal.timeout(API_CONFIG.timeout),
    });

    if (!response.ok) {
      throw new Error(`Download failed: ${response.status}`);
    }

    const blob = await response.blob();
    return URL.createObjectURL(blob);
  } catch (error) {
    console.error(`Failed to download document ${documentId} as ${format}:`, error);
    throw error;
  }
}

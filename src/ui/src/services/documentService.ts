/**
 * Document Service - DocuSearch UI
 * Provider: Agent 6 (Services)
 * Consumers: Agent 5 (App), Agent 4 (DocumentCard)
 * Contract: integration-contracts/api-services-contract.md
 *
 * Wave 1-3: Mock implementation with delays
 * Wave 4: Replace with real API calls
 */

import type { DocumentCardProps, DocumentFilters } from '../lib/types';
import { getMockDocuments, getMockDocument } from '../lib/mockData';
import { delay } from '../lib/utils';

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
  // Simulate network delay
  await delay(300);

  let documents = getMockDocuments();

  // Apply filters
  if (filters) {
    if (filters.status) {
      documents = documents.filter(doc =>
        filters.status!.includes(doc.status)
      );
    }

    if (filters.fileType) {
      documents = documents.filter(doc =>
        filters.fileType!.includes(doc.fileType)
      );
    }

    if (filters.sortBy === 'name') {
      documents = documents.sort((a, b) => {
        const order = filters.sortOrder === 'desc' ? -1 : 1;
        return a.title.localeCompare(b.title) * order;
      });
    }

    if (filters.sortBy === 'date' && documents[0].dateProcessed) {
      documents = documents.sort((a, b) => {
        const order = filters.sortOrder === 'desc' ? -1 : 1;
        const dateA = new Date(a.dateProcessed || 0).getTime();
        const dateB = new Date(b.dateProcessed || 0).getTime();
        return (dateA - dateB) * order;
      });
    }

    // Pagination
    if (filters.offset !== undefined || filters.limit !== undefined) {
      const offset = filters.offset || 0;
      const limit = filters.limit || documents.length;
      documents = documents.slice(offset, offset + limit);
    }
  }

  return documents;
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
  // Simulate network delay
  await delay(200);

  return getMockDocument(documentId);
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
  // Simulate network delay
  await delay(500);

  // Mock implementation - always succeeds
  console.log(`[Mock] Deleting document: ${documentId}`);
  return true;
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
  // Simulate network delay
  await delay(400);

  // Mock implementation - always succeeds
  console.log(`[Mock] Re-processing document: ${documentId}`);
  return true;
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
  // Simulate network delay
  await delay(300);

  // Mock implementation - return fake blob URL
  console.log(`[Mock] Downloading document ${documentId} as ${format}`);

  // In Wave 4, this will be:
  // const response = await fetch(`/api/document/${documentId}/download?format=${format}`);
  // const blob = await response.blob();
  // return URL.createObjectURL(blob);

  return `blob:mock-${documentId}-${format}`;
}

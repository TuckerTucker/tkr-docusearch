/**
 * Upload Service - DocuSearch UI
 * Provider: Agent 6 (Services)
 * Consumers: Agent 5 (App)
 * Contract: integration-contracts/api-services-contract.md
 *
 * Wave 1-3: Mock implementation with simulated progress
 * Wave 4: Replace with real upload API
 */

import type { UploadResponse } from '../lib/types';
import { delay } from '../lib/utils';

/**
 * Upload progress callback
 */
export type UploadProgressCallback = (progress: number) => void;

/**
 * Upload a file to the server
 *
 * @param file - File to upload
 * @param onProgress - Optional progress callback (0-100)
 * @returns Promise resolving to upload response
 *
 * @example
 * const response = await uploadService.uploadFile(
 *   file,
 *   (progress) => console.log(`Upload: ${progress}%`)
 * );
 * console.log('Document ID:', response.document_id);
 */
export async function uploadFile(
  file: File,
  onProgress?: UploadProgressCallback
): Promise<UploadResponse> {
  // Mock implementation - simulate upload progress
  const totalSteps = 10;

  for (let i = 1; i <= totalSteps; i++) {
    await delay(200); // Simulate chunk upload

    const progress = Math.round((i / totalSteps) * 100);
    if (onProgress) {
      onProgress(progress);
    }
  }

  // Mock successful response
  const mockDocumentId = `doc-${Date.now()}`;

  console.log(`[Mock] Uploaded file: ${file.name} (${file.size} bytes)`);
  console.log(`[Mock] Assigned document ID: ${mockDocumentId}`);

  // In Wave 4, this will be:
  // const formData = new FormData();
  // formData.append('file', file);
  //
  // const xhr = new XMLHttpRequest();
  // xhr.upload.addEventListener('progress', (e) => {
  //   if (e.lengthComputable && onProgress) {
  //     const progress = Math.round((e.loaded / e.total) * 100);
  //     onProgress(progress);
  //   }
  // });
  //
  // const response = await fetch('/api/upload', {
  //   method: 'POST',
  //   body: formData,
  // });
  //
  // return await response.json();

  return {
    success: true,
    document_id: mockDocumentId,
    message: 'Upload successful',
  };
}

/**
 * Cancel an ongoing upload
 *
 * @param documentId - Document ID to cancel
 * @returns Promise resolving to success boolean
 *
 * @example
 * const success = await uploadService.cancelUpload('doc-123');
 */
export async function cancelUpload(documentId: string): Promise<boolean> {
  // Simulate network delay
  await delay(100);

  // Mock implementation
  console.log(`[Mock] Cancelling upload: ${documentId}`);

  // In Wave 4, this will use AbortController to cancel the fetch request

  return true;
}

/**
 * Validate file before upload
 *
 * Checks file size, type, and other constraints
 *
 * @param file - File to validate
 * @returns Validation result with error message if invalid
 *
 * @example
 * const validation = validateFile(file);
 * if (!validation.valid) {
 *   alert(validation.error);
 * }
 */
export function validateFile(file: File): {
  valid: boolean;
  error?: string;
} {
  // Max file size: 100MB
  const maxSize = 100 * 1024 * 1024;
  if (file.size > maxSize) {
    return {
      valid: false,
      error: 'File size exceeds 100MB limit',
    };
  }

  // Allowed MIME types
  const allowedTypes = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'text/plain',
    'text/markdown',
  ];

  if (!allowedTypes.includes(file.type)) {
    return {
      valid: false,
      error: 'File type not supported. Allowed: PDF, DOCX, PPTX, TXT, MD',
    };
  }

  return { valid: true };
}

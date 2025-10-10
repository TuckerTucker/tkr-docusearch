/**
 * Upload Service - DocuSearch UI
 * Provider: Agent 6 (Services)
 * Consumers: Agent 5 (App)
 * Contract: integration-contracts/api-services-contract.md
 *
 * Wave 4: Real upload implementation via Copyparty
 */

import type { UploadResponse } from '../lib/types';

/**
 * Upload progress callback
 */
export type UploadProgressCallback = (progress: number) => void;

/**
 * Copyparty upload URL
 */
const COPYPARTY_URL = 'http://localhost:8000';

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
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append('file', file);

    const xhr = new XMLHttpRequest();

    // Track upload progress
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable && onProgress) {
        const progress = Math.round((e.loaded / e.total) * 100);
        onProgress(progress);
      }
    });

    // Handle completion
    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        // Copyparty uploads successfully
        // The webhook will trigger worker processing
        // Document ID will be assigned by the backend
        resolve({
          success: true,
          document_id: file.name, // Temporary - will be updated by backend
          message: 'Upload successful',
        });
      } else {
        reject(new Error(`Upload failed: ${xhr.status} ${xhr.statusText}`));
      }
    });

    // Handle errors
    xhr.addEventListener('error', () => {
      reject(new Error('Upload failed: Network error'));
    });

    xhr.addEventListener('abort', () => {
      reject(new Error('Upload cancelled'));
    });

    // Send to Copyparty
    xhr.open('POST', `${COPYPARTY_URL}/`);
    xhr.send(formData);
  });
}

/**
 * Cancel an ongoing upload
 *
 * Note: Actual cancellation requires tracking XHR instances.
 * For now, this is a placeholder that would need to be implemented
 * with proper upload tracking state management.
 *
 * @param documentId - Document ID to cancel
 * @returns Promise resolving to success boolean
 *
 * @example
 * const success = await uploadService.cancelUpload('doc-123');
 */
export async function cancelUpload(documentId: string): Promise<boolean> {
  console.log(`Cancel upload requested for: ${documentId}`);
  // TODO: Implement XHR cancellation with upload tracking
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

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
 * Upload cancellation function
 */
export type CancelUploadFn = () => void;

/**
 * Upload result with cancellation function
 */
export interface UploadResult {
  promise: Promise<UploadResponse>;
  cancel: CancelUploadFn;
}

/**
 * Copyparty upload URL - from centralized configuration
 */
const getCopypartyUrl = () => {
  return import.meta.env.VITE_COPYPARTY_URL || 'http://localhost:8000';
};

/**
 * Active XHR instances tracked by temporary upload ID
 */
const activeUploads = new Map<string, XMLHttpRequest>();

/**
 * Upload a file to the server
 *
 * @param file - File to upload
 * @param onProgress - Optional progress callback (0-100)
 * @returns UploadResult with promise and cancel function
 *
 * @example
 * const { promise, cancel } = uploadFile(
 *   file,
 *   (progress) => console.log(`Upload: ${progress}%`)
 * );
 *
 * // Cancel if needed
 * setTimeout(() => cancel(), 5000);
 *
 * try {
 *   const response = await promise;
 *   console.log('Document ID:', response.document_id);
 * } catch (error) {
 *   console.error('Upload failed or cancelled:', error);
 * }
 */
export function uploadFile(
  file: File,
  onProgress?: UploadProgressCallback
): UploadResult {
  // Generate temporary upload ID
  const uploadId = `${file.name}-${Date.now()}`;

  const promise = new Promise<UploadResponse>((resolve, reject) => {
    const formData = new FormData();
    formData.append('file', file);

    const xhr = new XMLHttpRequest();

    // Track this upload
    activeUploads.set(uploadId, xhr);

    // Track upload progress
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable && onProgress) {
        const progress = Math.round((e.loaded / e.total) * 100);
        onProgress(progress);
      }
    });

    // Handle completion
    xhr.addEventListener('load', () => {
      // Remove from active uploads
      activeUploads.delete(uploadId);

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
      activeUploads.delete(uploadId);
      reject(new Error('Upload failed: Network error'));
    });

    xhr.addEventListener('abort', () => {
      activeUploads.delete(uploadId);
      reject(new Error('Upload cancelled'));
    });

    // Send to Copyparty with password parameter
    // Copyparty accepts auth via URL param: ?pw=password
    xhr.open('POST', `${getCopypartyUrl()}/?pw=admin`);

    xhr.send(formData);
  });

  // Return promise and cancel function
  return {
    promise,
    cancel: () => {
      const xhr = activeUploads.get(uploadId);
      if (xhr) {
        xhr.abort();
        activeUploads.delete(uploadId);
      }
    },
  };
}

/**
 * Cancel an ongoing upload by document ID
 *
 * @param uploadId - Upload ID to cancel
 * @returns Success boolean
 *
 * @example
 * const success = cancelUpload('doc-123-1234567890');
 */
export function cancelUpload(uploadId: string): boolean {
  const xhr = activeUploads.get(uploadId);
  if (xhr) {
    xhr.abort();
    activeUploads.delete(uploadId);
    return true;
  }
  return false;
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

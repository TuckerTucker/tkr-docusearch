/**
 * DocumentCard Component - DocuSearch UI
 * Provider: Agent 4 (DocumentCard)
 * Consumers: Agent 5 (App)
 *
 * Wave 1: Stub with correct signature and basic structure
 * Wave 2: Full implementation with all states and animations
 */

import React from 'react';
import type { DocumentCardProps } from '../../lib/types';
import { ProcessingStages } from '../ProcessingStages/ProcessingStages';
import { DocumentMetadata } from '../DocumentMetadata/DocumentMetadata';
import { cn } from '../../lib/utils';

/**
 * Main document card component
 *
 * Displays document in various states:
 * - uploading: Shows progress bar and processing stages
 * - processing: Shows progress bar and processing stages
 * - completed: Shows metadata and embedding statistics
 * - error: Shows error message and retry options
 *
 * Supports multiple view modes:
 * - list: Horizontal layout (610×305px)
 * - grid: Square layout (305×305px)
 * - compact: Minimal layout
 *
 * @param props - DocumentCardProps
 *
 * @example
 * <DocumentCard
 *   id="doc-1"
 *   title="Neural Networks and Deep Learning"
 *   status="uploading"
 *   progress={45}
 *   stages={[...]}
 *   onCancel={() => console.log('Cancel upload')}
 * />
 */
export function DocumentCard(props: DocumentCardProps): React.ReactElement {
  const {
    id,
    title,
    status,
    fileType,
    thumbnail,
    progress,
    stages,
    errorMessage,
    view = 'list',
    onCancel,
    onDelete,
    onProcessAgain,
    onDownload,
    // onExpand - Wave 2: Will be used for expand/collapse functionality
  } = props;

  // Wave 1 stub - basic structure with status-based rendering
  return (
    <div
      className={cn(
        'rounded-lg border bg-card p-4 transition-all',
        'hover:shadow-md',
        view === 'list' && 'w-[610px] h-auto',
        view === 'grid' && 'w-[305px] h-[305px]',
        view === 'compact' && 'w-full h-auto'
      )}
      data-component="document-card"
      data-status={status}
      data-view={view}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-lg truncate" title={title}>
            {title}
          </h3>
          <p className="text-sm text-muted-foreground">
            {fileType} • ID: {id.slice(0, 8)}...
          </p>
        </div>
        {/* Placeholder for action buttons */}
        <div className="flex gap-2 ml-2">
          {status === 'uploading' && onCancel && (
            <button
              onClick={onCancel}
              className="text-xs px-2 py-1 rounded bg-red-100 text-red-800 hover:bg-red-200"
            >
              Cancel
            </button>
          )}
          {status === 'error' && onProcessAgain && (
            <button
              onClick={onProcessAgain}
              className="text-xs px-2 py-1 rounded bg-blue-100 text-blue-800 hover:bg-blue-200"
            >
              Retry
            </button>
          )}
          {status === 'completed' && onDelete && (
            <button
              onClick={onDelete}
              className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-800 hover:bg-gray-200"
            >
              Delete
            </button>
          )}
        </div>
      </div>

      {/* Thumbnail placeholder */}
      {thumbnail && (
        <div className="mb-3">
          <img
            src={thumbnail}
            alt={title}
            className="w-full h-32 object-cover rounded"
          />
        </div>
      )}

      {/* Error state */}
      {status === 'error' && errorMessage && (
        <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-800">
          <strong>Error:</strong> {errorMessage}
        </div>
      )}

      {/* Processing/Uploading state */}
      {(status === 'uploading' || status === 'processing') && (
        <div className="space-y-3">
          {/* Progress bar */}
          {progress !== undefined && (
            <div className="space-y-1">
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Progress</span>
                <span>{progress}%</span>
              </div>
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 transition-all duration-500"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {/* Processing stages */}
          {stages && <ProcessingStages stages={stages} />}
        </div>
      )}

      {/* Completed state */}
      {status === 'completed' && (
        <div className="space-y-3">
          <DocumentMetadata document={props} />

          {/* Download buttons placeholder */}
          {onDownload && (
            <div className="flex gap-2 pt-3 border-t">
              <button
                onClick={() => onDownload('original')}
                className="text-xs px-3 py-1 rounded bg-blue-100 text-blue-800 hover:bg-blue-200"
              >
                Download Original
              </button>
              <button
                onClick={() => onDownload('markdown')}
                className="text-xs px-3 py-1 rounded bg-green-100 text-green-800 hover:bg-green-200"
              >
                Markdown
              </button>
            </div>
          )}
        </div>
      )}

      {/* Wave 2: Full implementation with */}
      {/* - Proper animations */}
      {/* - Expand/collapse functionality */}
      {/* - Better thumbnail handling */}
      {/* - Accessibility improvements */}
      {/* - Touch interactions */}
      {/* - Loading states */}
    </div>
  );
}

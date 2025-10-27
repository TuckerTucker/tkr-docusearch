/**
 * DocumentCard Component - DocuSearch UI
 * Provider: Agent 4 (DocumentCard)
 * Consumers: Agent 5 (App)
 *
 * Wave 2: Full implementation with all states and animations
 */

import React, { useState, useRef, useEffect } from 'react';
import type { DocumentCardProps, DownloadFormat } from '../../lib/types';
import { ProcessingStages } from '../ProcessingStages/ProcessingStages';
import { DocumentMetadata } from '../DocumentMetadata/DocumentMetadata';
import { cn } from '../../lib/utils';
import { useToggle } from '../../hooks/useToggle';
import { useProcessingTimeout } from '../../hooks/useProcessingTimeout';

/**
 * Action button icons
 */
const ActionIcons = {
  cancel: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
  retry: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  ),
  delete: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
    </svg>
  ),
  download: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
    </svg>
  ),
  expand: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
    </svg>
  ),
  collapse: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
    </svg>
  ),
  spinner: (
    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
    </svg>
  ),
};

/**
 * File type placeholder icons
 */
const FileTypeIcons = {
  FileText: (
    <svg className="w-16 h-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  ),
  Presentation: (
    <svg className="w-16 h-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
    </svg>
  ),
  File: (
    <svg className="w-16 h-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
    </svg>
  ),
};

/**
 * Thumbnail placeholder component for documents without thumbnails
 */
const ThumbnailPlaceholder = ({ fileType }: { fileType: string }) => {
  const IconComponent = {
    PDF: FileTypeIcons.FileText,
    DOCX: FileTypeIcons.FileText,
    PPTX: FileTypeIcons.Presentation,
    TXT: FileTypeIcons.FileText,
    MD: FileTypeIcons.FileText,
  }[fileType] || FileTypeIcons.File;

  return (
    <div className="relative aspect-video bg-muted rounded-md overflow-hidden flex items-center justify-center">
      <div className="text-muted-foreground/40">
        {IconComponent}
      </div>
      <span className="absolute bottom-2 right-2 px-2 py-1 bg-background/90 text-xs font-semibold rounded border border-border">
        {fileType}
      </span>
    </div>
  );
};

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
 * - list: Horizontal layout (610×305px, expandable)
 * - grid: Square layout (305×305px)
 * - compact: Minimal layout
 *
 * Features:
 * - Smooth animations for state transitions
 * - Expand/collapse for completed documents
 * - Keyboard accessible
 * - Touch-friendly action buttons
 * - Progress indicators
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
    onExpand,
    onProcessingTimeout,
    started_at,
  } = props;

  // Expand/collapse state for completed documents
  const [isExpanded, toggleExpanded] = useToggle(false);

  // Download loading state
  const [downloadingFormat, setDownloadingFormat] = useState<DownloadFormat | null>(null);

  // Title truncation detection
  const titleRef = useRef<HTMLHeadingElement>(null);
  const [isTitleTruncated, setIsTitleTruncated] = useState(false);

  // Check if title is truncated
  useEffect(() => {
    if (titleRef.current) {
      setIsTitleTruncated(
        titleRef.current.scrollHeight > titleRef.current.clientHeight
      );
    }
  }, [title]);

  // Track processing timeout
  useProcessingTimeout({
    documentId: id,
    status,
    startedAt: started_at,
    onTimeout: () => {
      if (onProcessingTimeout) {
        onProcessingTimeout();
      }
    },
  });

  // Handle expand/collapse
  const handleToggleExpand = () => {
    const newExpanded = !isExpanded;
    toggleExpanded();
    onExpand?.(newExpanded);
  };

  // Handle download with loading state
  const handleDownload = async (format: DownloadFormat) => {
    if (!onDownload || downloadingFormat) return;

    setDownloadingFormat(format);
    try {
      await onDownload(format);
    } finally {
      setDownloadingFormat(null);
    }
  };

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Only handle keyboard on completed documents that can expand
    if (!canExpand) return;

    // Enter or Space: Toggle expand/collapse
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleToggleExpand();
    }

    // Escape: Collapse if expanded
    if (e.key === 'Escape' && isExpanded) {
      e.preventDefault();
      toggleExpanded();
      onExpand?.(false);
    }
  };

  // Download format options
  const downloadFormats: { value: DownloadFormat; label: string }[] = [
    { value: 'original', label: 'Original' },
    { value: 'markdown', label: 'Markdown' },
    { value: 'vtt', label: 'VTT Captions' },
    { value: 'srt', label: 'SRT Captions' },
  ];

  const canExpand = status === 'completed' && view === 'list';

  // ARIA labels
  const statusText = {
    uploading: 'uploading',
    processing: 'processing',
    completed: 'completed',
    error: 'failed to process',
  }[status];

  const ariaLabel = `${title}, ${fileType} document, ${statusText}`;
  const metadataId = `doc-meta-${id}`;
  const contentId = `doc-content-${id}`;

  return (
    <article
      className={cn(
        'relative rounded-lg border bg-card overflow-hidden',
        'transition-all duration-300 ease-in-out',
        'hover:shadow-lg hover:border-border/80',
        // Keyboard focus styling
        'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
        // View mode dimensions
        view === 'list' && !isExpanded && 'w-full max-w-[610px]',
        view === 'list' && isExpanded && 'w-full max-w-[610px]',
        view === 'grid' && 'w-[305px] h-[305px]',
        view === 'compact' && 'w-full',
        // Status-based styling
        status === 'error' && 'border-red-300',
        status === 'uploading' && 'border-blue-300',
        status === 'processing' && 'border-blue-300'
      )}
      role="article"
      tabIndex={canExpand ? 0 : -1}
      aria-label={ariaLabel}
      aria-describedby={status === 'completed' ? metadataId : undefined}
      onKeyDown={handleKeyDown}
      data-component="document-card"
      data-status={status}
      data-view={view}
      data-expanded={isExpanded}
    >
      <div className="p-4 space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <h3
              ref={titleRef}
              className="font-semibold text-base leading-tight line-clamp-3"
              title={isTitleTruncated ? title : undefined}
            >
              {title}
            </h3>
            <p className="text-xs text-muted-foreground mt-1">
              {fileType}
              {view !== 'compact' && ` • ${id.slice(0, 8)}...`}
            </p>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-1 flex-shrink-0">
            {/* Cancel upload */}
            {status === 'uploading' && onCancel && (
              <button
                onClick={onCancel}
                className={cn(
                  'p-2 rounded-md transition-colors',
                  'hover:bg-red-100 text-red-600 hover:text-red-700',
                  'focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2'
                )}
                aria-label="Cancel upload"
                title="Cancel upload"
              >
                {ActionIcons.cancel}
              </button>
            )}

            {/* Retry processing */}
            {status === 'error' && onProcessAgain && (
              <button
                onClick={onProcessAgain}
                className={cn(
                  'p-2 rounded-md transition-colors',
                  'hover:bg-blue-100 text-blue-600 hover:text-blue-700',
                  'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
                )}
                aria-label="Retry processing"
                title="Retry processing"
              >
                {ActionIcons.retry}
              </button>
            )}

            {/* Delete document */}
            {status === 'completed' && onDelete && (
              <button
                onClick={onDelete}
                className={cn(
                  'p-2 rounded-md transition-colors',
                  'hover:bg-red-100 text-muted-foreground hover:text-red-600',
                  'focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2'
                )}
                aria-label="Delete document"
                title="Delete document"
              >
                {ActionIcons.delete}
              </button>
            )}

            {/* Expand/collapse toggle */}
            {canExpand && (
              <button
                onClick={handleToggleExpand}
                className={cn(
                  'p-2 rounded-md transition-all',
                  'hover:bg-accent text-muted-foreground hover:text-foreground',
                  'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2'
                )}
                aria-label={isExpanded ? 'Collapse document details' : 'Expand document details'}
                aria-expanded={isExpanded}
                aria-controls={contentId}
              >
                <div className={isExpanded ? 'rotate-collapse' : 'rotate-expand'}>
                  {ActionIcons.expand}
                </div>
              </button>
            )}
          </div>
        </div>

        {/* Thumbnail */}
        {view !== 'compact' && (
          thumbnail ? (
            <div className="relative aspect-video bg-muted rounded-md overflow-hidden">
              <img
                src={thumbnail}
                alt={title}
                className="w-full h-full object-cover"
                loading="lazy"
              />
            </div>
          ) : (
            <ThumbnailPlaceholder fileType={fileType} />
          )
        )}

        {/* Error state */}
        {status === 'error' && errorMessage && (
          <div
            className="p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-800 animate-shake"
            role="alert"
          >
            <div className="flex gap-2">
              <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <div>
                <strong className="font-medium">Processing failed</strong>
                <p className="mt-1">{errorMessage}</p>
              </div>
            </div>
          </div>
        )}

        {/* Processing/Uploading state */}
        {(status === 'uploading' || status === 'processing') && (
          <div className="space-y-3">
            {/* Progress bar */}
            {progress !== undefined && (
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-muted-foreground">
                    {status === 'uploading' ? 'Uploading' : 'Processing'}
                  </span>
                  <span className="text-foreground">{progress}%</span>
                </div>
                <div className="h-2 bg-secondary rounded-full overflow-hidden">
                  <div
                    className={cn(
                      'h-full transition-progress',
                      'bg-gradient-to-r from-blue-500 to-blue-600'
                    )}
                    style={{ width: `${progress}%` }}
                    role="progressbar"
                    aria-valuenow={progress}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-valuetext={`${progress}% ${status === 'uploading' ? 'uploaded' : 'processed'}`}
                    aria-label={`${status === 'uploading' ? 'Upload' : 'Processing'} progress`}
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
          <div id={contentId} className="space-y-3">
            <div id={metadataId}>
              <DocumentMetadata
                document={props}
                mode={isExpanded ? 'full' : 'compact'}
              />
            </div>

            {/* Download buttons */}
            {onDownload && (isExpanded || view !== 'list') && (
              <div className="pt-3 border-t border-border">
                <p className="text-xs font-medium text-muted-foreground mb-2">Download as:</p>
                <div className="flex flex-wrap gap-2" role="group" aria-label="Download options">
                  {downloadFormats.map((format) => (
                    <button
                      key={format.value}
                      onClick={() => handleDownload(format.value)}
                      disabled={downloadingFormat === format.value}
                      className={cn(
                        'inline-flex items-center gap-1.5 px-3 py-1.5',
                        'text-xs font-medium rounded-md',
                        'border border-border',
                        'hover:bg-accent hover:border-accent-foreground/20',
                        'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
                        'transition-colors',
                        downloadingFormat === format.value && 'opacity-50 cursor-not-allowed'
                      )}
                      aria-label={`Download as ${format.label}`}
                    >
                      {downloadingFormat === format.value ? (
                        <>
                          {ActionIcons.spinner}
                          Downloading...
                        </>
                      ) : (
                        <>
                          {ActionIcons.download}
                          {format.label}
                        </>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </article>
  );
}

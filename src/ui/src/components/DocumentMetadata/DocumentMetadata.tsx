/**
 * DocumentMetadata Component - DocuSearch UI
 * Provider: Agent 3 (Feature Components)
 * Contract: integration-contracts/document-metadata-contract.md
 *
 * Wave 1: Stub with correct signature
 * Wave 2: Full implementation with icons and formatting
 */

import React from 'react';
import type { DocumentCardProps } from '../../lib/types';
import { formatDate } from '../../lib/utils';

/**
 * Props for DocumentMetadata component
 */
export interface DocumentMetadataProps {
  /** Document data containing metadata */
  document: DocumentCardProps;
  /** Optional CSS class name */
  className?: string;
}

/**
 * Document metadata display component
 *
 * Shows document metadata including:
 * - Author (fallback: "Unknown")
 * - Published date
 * - Page count
 * - File size
 * - Embedding statistics (for completed documents)
 *
 * @param props - Component props
 *
 * @example
 * <DocumentMetadata
 *   document={{
 *     author: 'Dr. Jane Smith',
 *     published: '2024-01-02',
 *     pages: 42,
 *     size: '3.8 MB',
 *     visualEmbeddings: 42,
 *     textEmbeddings: 1247,
 *   }}
 * />
 */
export function DocumentMetadata({
  document,
  className,
}: DocumentMetadataProps): React.ReactElement {
  const {
    author,
    published,
    pages,
    size,
    visualEmbeddings,
    textEmbeddings,
    textChunks,
  } = document;

  // Wave 1 stub - basic rendering
  return (
    <div className={className} data-component="document-metadata">
      <div className="space-y-2 text-sm text-muted-foreground">
        {/* Author */}
        {author && (
          <div className="flex items-center gap-2">
            <span className="font-medium">Author:</span>
            <span>{author}</span>
          </div>
        )}

        {/* Published date */}
        {published && (
          <div className="flex items-center gap-2">
            <span className="font-medium">Published:</span>
            <span>{formatDate(published)}</span>
          </div>
        )}

        {/* Pages and size */}
        <div className="flex items-center gap-4">
          {pages && (
            <span>
              <span className="font-medium">Pages:</span> {pages}
            </span>
          )}
          {size && (
            <span>
              <span className="font-medium">Size:</span> {size}
            </span>
          )}
        </div>

        {/* Embedding statistics */}
        {document.status === 'completed' && (
          <div className="pt-2 border-t space-y-1">
            {visualEmbeddings !== undefined && (
              <div>
                <span className="font-medium">Visual embeddings:</span>{' '}
                {visualEmbeddings}
              </div>
            )}
            {textEmbeddings !== undefined && (
              <div>
                <span className="font-medium">Text embeddings:</span>{' '}
                {textEmbeddings}
              </div>
            )}
            {textChunks !== undefined && (
              <div>
                <span className="font-medium">Text chunks:</span> {textChunks}
              </div>
            )}
          </div>
        )}
      </div>
      {/* Wave 2: Add icons, better formatting, accessibility */}
    </div>
  );
}

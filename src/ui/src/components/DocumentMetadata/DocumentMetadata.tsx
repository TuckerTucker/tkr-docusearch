/**
 * DocumentMetadata Component - DocuSearch UI
 * Provider: Agent 3 (Feature Components)
 * Contract: integration-contracts/document-metadata-contract.md
 *
 * Wave 2: Full implementation with icons and formatting
 */

import React from 'react';
import type { DocumentCardProps } from '../../lib/types';
import { formatDate, pluralize } from '../../lib/utils';
import { cn } from '../../lib/utils';

/**
 * Props for DocumentMetadata component
 */
export interface DocumentMetadataProps {
  /** Document data containing metadata */
  document: DocumentCardProps;
  /** Optional CSS class name */
  className?: string;
  /** Display mode: full or compact */
  mode?: 'full' | 'compact';
}

/**
 * Metadata icons
 */
const MetadataIcons = {
  author: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
      />
    </svg>
  ),
  calendar: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
      />
    </svg>
  ),
  document: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
      />
    </svg>
  ),
  database: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"
      />
    </svg>
  ),
  image: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
      />
    </svg>
  ),
  text: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4 6h16M4 12h16m-7 6h7"
      />
    </svg>
  ),
};

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
 * Features:
 * - Icons for each metadata type
 * - Responsive layout
 * - Accessible labels
 * - Compact and full display modes
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
  mode = 'full',
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

  const MetadataRow = ({
    icon,
    label,
    value,
  }: {
    icon: React.ReactNode;
    label: string;
    value: string | number;
  }) => (
    <div className="flex items-center gap-2 text-sm">
      <div className="text-muted-foreground flex-shrink-0" aria-hidden="true">
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <span className="sr-only">{label}: </span>
        <span className="truncate">{value}</span>
      </div>
    </div>
  );

  const hasEmbeddings = visualEmbeddings !== undefined || textEmbeddings !== undefined;
  const showStats = document.status === 'completed' && hasEmbeddings;

  return (
    <div
      className={cn('space-y-3', className)}
      data-component="document-metadata"
      data-mode={mode}
    >
      {/* Basic metadata */}
      <div className="space-y-2">
        {/* Author */}
        {author && (
          <MetadataRow
            icon={MetadataIcons.author}
            label="Author"
            value={author}
          />
        )}

        {/* Published date */}
        {published && (
          <MetadataRow
            icon={MetadataIcons.calendar}
            label="Published"
            value={formatDate(published)}
          />
        )}

        {/* Document info */}
        {(pages || size) && (
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            {pages && (
              <div className="flex items-center gap-1.5">
                <div className="flex-shrink-0" aria-hidden="true">
                  {MetadataIcons.document}
                </div>
                <span>{pluralize(pages, 'page')}</span>
              </div>
            )}
            {size && (
              <div className="flex items-center gap-1.5">
                <div className="flex-shrink-0" aria-hidden="true">
                  {MetadataIcons.database}
                </div>
                <span>{size}</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Embedding statistics */}
      {showStats && mode === 'full' && (
        <div className="pt-3 border-t border-border space-y-2">
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Embeddings
          </div>

          <div className="space-y-1.5">
            {visualEmbeddings !== undefined && (
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <div className="flex-shrink-0" aria-hidden="true">
                    {MetadataIcons.image}
                  </div>
                  <span>Visual</span>
                </div>
                <span className={cn(
                  'font-medium',
                  visualEmbeddings === 0 ? 'text-amber-600' : 'text-foreground'
                )}>
                  {visualEmbeddings.toLocaleString()}
                </span>
              </div>
            )}

            {textEmbeddings !== undefined && (
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <div className="flex-shrink-0" aria-hidden="true">
                    {MetadataIcons.text}
                  </div>
                  <span>Text</span>
                </div>
                <span className="font-medium text-foreground">
                  {textEmbeddings.toLocaleString()}
                </span>
              </div>
            )}

            {textChunks !== undefined && (
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <div className="flex-shrink-0" aria-hidden="true">
                    {MetadataIcons.database}
                  </div>
                  <span>Chunks</span>
                </div>
                <span className="font-medium text-foreground">
                  {textChunks.toLocaleString()}
                </span>
              </div>
            )}
          </div>

          {/* Warning for zero visual embeddings */}
          {visualEmbeddings === 0 && (
            <div className="mt-2 p-2 bg-amber-50 border border-amber-200 rounded text-xs text-amber-800">
              No visual embeddings found
            </div>
          )}
        </div>
      )}
    </div>
  );
}

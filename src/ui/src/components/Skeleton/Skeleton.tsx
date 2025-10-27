/**
 * Skeleton Component - DocuSearch UI
 * Provider: Wave 3 (Polish & Refinement)
 *
 * Loading skeleton for placeholder content
 */

import React from 'react';
import { cn } from '../../lib/utils';

export interface SkeletonProps {
  /** CSS class name */
  className?: string;
  /** Skeleton variant */
  variant?: 'default' | 'circular' | 'rectangular';
}

/**
 * Skeleton loading placeholder
 *
 * Shows an animated pulse effect while content is loading
 *
 * @example
 * <Skeleton className="h-4 w-32" />
 * <Skeleton variant="circular" className="h-12 w-12" />
 */
export function Skeleton({
  className,
  variant = 'default',
}: SkeletonProps): React.ReactElement {
  return (
    <div
      className={cn(
        'animate-pulse bg-muted',
        variant === 'circular' && 'rounded-full',
        variant === 'rectangular' && 'rounded-md',
        variant === 'default' && 'rounded',
        className
      )}
      aria-busy="true"
      aria-live="polite"
    />
  );
}

/**
 * Document card skeleton
 */
export function DocumentCardSkeleton({
  view = 'list',
}: {
  view?: 'list' | 'grid';
}): React.ReactElement {
  return (
    <div
      className={cn(
        'rounded-lg border bg-card p-4',
        view === 'list' && 'w-full max-w-[610px]',
        view === 'grid' && 'w-[305px] h-[305px]'
      )}
    >
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 space-y-2">
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-3 w-24" />
          </div>
          <Skeleton variant="circular" className="h-8 w-8" />
        </div>

        {/* Thumbnail */}
        {view !== 'grid' && (
          <Skeleton variant="rectangular" className="w-full aspect-video" />
        )}

        {/* Metadata rows */}
        <div className="space-y-2">
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-2/3" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      </div>
    </div>
  );
}

/**
 * Multiple document card skeletons
 */
export function DocumentListSkeleton({
  count = 3,
  view = 'list',
}: {
  count?: number;
  view?: 'list' | 'grid';
}): React.ReactElement {
  return (
    <div
      className={cn(
        'gap-4',
        view === 'grid'
          ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'
          : 'flex flex-col'
      )}
    >
      {Array.from({ length: count }).map((_, i) => (
        <DocumentCardSkeleton key={i} view={view} />
      ))}
    </div>
  );
}

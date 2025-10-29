/**
 * BBoxController Component
 *
 * Agent 8: BBoxController Integration Layer
 * Wave 1 - BBox Overlay React Implementation
 * Agent 12: Performance Optimizer - Wave 3
 *
 * Orchestration layer that coordinates bidirectional highlighting between
 * document page images (BoundingBoxOverlay) and text chunks (ChunkHighlighter).
 *
 * This component:
 * - Fetches document structure data with bounding boxes
 * - Manages shared highlighting state (active and hovered chunks)
 * - Coordinates events between BoundingBoxOverlay and markdown content
 * - Handles URL-based chunk navigation
 * - Provides smooth scrolling to chunks on interaction
 *
 * Features:
 * - Bidirectional highlighting (bbox ↔ chunk)
 * - URL parameter navigation (?chunk=...)
 * - Smooth scrolling with configurable offset
 * - Loading and error state handling
 * - Performance optimized with useCallback, useMemo, React.memo
 * - Optimized React Query cache configuration
 *
 * @example
 * ```tsx
 * <BBoxController
 *   docId={document.doc_id}
 *   currentPage={currentPage}
 *   imageElement={imageRef.current}
 *   markdownContainerRef={markdownRef}
 * />
 * ```
 */

import React, { useState, useCallback, RefObject, useMemo, useEffect } from 'react';
import { BoundingBoxOverlay } from '../../../../components/BoundingBoxOverlay';
import { useDocumentStructure } from '../../../../hooks/useDocumentStructure';
import { useChunkNavigation } from '../../hooks/useChunkNavigation';
import { useChunkHighlight } from '../../../../components/ChunkHighlighter/useChunkHighlight';
import { announceToScreenReader } from '../../../../utils/accessibility';
import {
  transformStructureToBboxes,
  getOriginalDimensions,
  hasAnyBboxes,
} from './structureTransform';
import type { BBox } from '../../../../types/bbox';

/**
 * Props for BBoxController component
 */
export interface BBoxControllerProps {
  /**
   * Document ID
   */
  docId: string;

  /**
   * Current page number (1-indexed)
   */
  currentPage: number;

  /**
   * Reference to the image element to overlay bboxes on
   */
  imageElement: HTMLImageElement | null;

  /**
   * Reference to the markdown container for chunk highlighting
   */
  markdownContainerRef: RefObject<HTMLElement>;

  /**
   * Whether to automatically scroll to active chunk
   * @default true
   */
  autoScroll?: boolean;

  /**
   * Offset from top for scrolling (useful for fixed headers)
   * @default 0
   */
  scrollOffset?: number;

  /**
   * Scroll behavior
   * @default 'smooth'
   */
  scrollBehavior?: ScrollBehavior;

  /**
   * Callback fired when bbox is clicked (optional)
   */
  onBboxClick?: (chunkId: string, bbox: BBox) => void;

  /**
   * Callback fired when chunk hover state changes (optional)
   */
  onChunkHover?: (chunkId: string | null) => void;

  /**
   * Whether to enable URL parameter navigation
   * @default true
   */
  enableUrlNavigation?: boolean;
}

/**
 * BBoxController - Orchestration layer for bidirectional highlighting.
 *
 * Coordinates interactions between:
 * 1. BoundingBoxOverlay (visual overlays on page images)
 * 2. ChunkHighlighter (text highlighting in markdown)
 * 3. URL navigation (deep linking to chunks)
 *
 * Event Flow:
 * - Bbox click → setActiveChunkId → scroll to chunk in markdown
 * - Bbox hover → setHoveredChunkId → highlight chunk in markdown
 * - Chunk hover → setHoveredChunkId → highlight bbox on image
 * - Chunk click → setActiveChunkId → highlight bbox on image
 * - URL parameter → navigate to chunk on mount
 */
export const BBoxController: React.FC<BBoxControllerProps> = React.memo(({
  docId,
  currentPage,
  imageElement,
  markdownContainerRef,
  autoScroll = true,
  scrollOffset = 0,
  scrollBehavior = 'smooth',
  onBboxClick,
  onChunkHover,
  enableUrlNavigation = true,
}) => {
  // Shared highlighting state
  const [activeChunkId, setActiveChunkId] = useState<string | null>(null);
  const [hoveredChunkId, setHoveredChunkId] = useState<string | null>(null);

  // Fetch document structure with bounding boxes
  // Already optimized in useDocumentStructure hook with 5min staleTime, 10min gcTime
  const { structure, isLoading, isError, error } = useDocumentStructure({
    docId,
    page: currentPage,
    enabled: true,
  });

  // Setup chunk highlighting in markdown container
  const { scrollToChunk } = useChunkHighlight({
    containerRef: markdownContainerRef,
    activeChunkId,
    hoveredChunkId,
    onChunkHover: (chunkId) => {
      setHoveredChunkId(chunkId);
      if (onChunkHover) {
        onChunkHover(chunkId);
      }
    },
    scrollBehavior,
    scrollOffset,
    autoScrollToActive: autoScroll,
  });

  // Handle URL-based chunk navigation
  useChunkNavigation({
    onChunkNavigate: useCallback(
      (chunkId: string) => {
        setActiveChunkId(chunkId);
        scrollToChunk(chunkId);
      },
      [scrollToChunk]
    ),
  });

  /**
   * Handle bounding box click.
   * Sets chunk as active and scrolls to it in markdown.
   */
  const handleBboxClick = useCallback(
    (chunkId: string, bbox: BBox) => {
      setActiveChunkId(chunkId);
      scrollToChunk(chunkId);

      // Fire optional callback
      if (onBboxClick) {
        onBboxClick(chunkId, bbox);
      }
    },
    [scrollToChunk, onBboxClick]
  );

  /**
   * Handle bounding box hover.
   * Updates hovered state for bidirectional highlighting.
   */
  const handleBboxHover = useCallback(
    (chunkId: string | null) => {
      setHoveredChunkId(chunkId);

      // Fire optional callback
      if (onChunkHover) {
        onChunkHover(chunkId);
      }
    },
    [onChunkHover]
  );

  /**
   * Announce loading state to screen readers
   */
  useEffect(() => {
    if (isLoading) {
      announceToScreenReader('Loading document structure...', 'polite');
    }
  }, [isLoading]);

  /**
   * Announce error state to screen readers
   */
  useEffect(() => {
    if (isError) {
      console.error('[BBoxController] Error fetching structure:', error);
      announceToScreenReader('Error loading document structure. Please try again.', 'assertive');
    }
  }, [isError, error]);

  /**
   * Announce successful load to screen readers
   */
  useEffect(() => {
    if (structure && hasAnyBboxes(structure)) {
      const bboxCount = transformStructureToBboxes(structure).length;
      announceToScreenReader(`Document structure loaded with ${bboxCount} interactive elements.`, 'polite');
    }
  }, [structure]);

  // Transform structure to flat bbox array - memoized
  // Must be called before any conditional returns (hooks rules)
  const bboxes = useMemo(() => structure ? transformStructureToBboxes(structure) : [], [structure]);

  // Extract original dimensions - memoized
  // Must be called before any conditional returns (hooks rules)
  const { width: originalWidth, height: originalHeight } = useMemo(
    () => structure ? getOriginalDimensions(structure) : { width: 0, height: 0 },
    [structure]
  );

  // Don't render if still loading
  if (isLoading) {
    return (
      <div
        role="status"
        aria-busy="true"
        aria-live="polite"
        style={{ position: 'absolute', left: '-10000px', width: '1px', height: '1px', overflow: 'hidden' }}
      >
        Loading document structure...
      </div>
    );
  }

  // Don't render if error occurred
  if (isError) {
    return (
      <div
        role="alert"
        aria-live="assertive"
        style={{ position: 'absolute', left: '-10000px', width: '1px', height: '1px', overflow: 'hidden' }}
      >
        Error loading document structure. Please try again.
      </div>
    );
  }

  // Don't render if no structure available
  if (!structure) {
    return null;
  }

  // Don't render if structure has no bboxes
  if (!hasAnyBboxes(structure)) {
    return null;
  }

  return (
    <BoundingBoxOverlay
      imageElement={imageElement}
      bboxes={bboxes}
      originalWidth={originalWidth}
      originalHeight={originalHeight}
      onBboxClick={handleBboxClick}
      onBboxHover={handleBboxHover}
      activeChunkId={activeChunkId}
      hoveredChunkId={hoveredChunkId}
    />
  );
});

BBoxController.displayName = 'BBoxController';

export default BBoxController;

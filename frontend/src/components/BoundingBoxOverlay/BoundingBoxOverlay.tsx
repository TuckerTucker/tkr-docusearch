/**
 * BoundingBoxOverlay Component
 *
 * Agent 5: BoundingBoxOverlay Component
 * Wave 1 - BBox Overlay React Implementation
 *
 * Renders SVG overlays on document page images showing bounding boxes
 * for document elements (headings, tables, pictures, etc.).
 *
 * Features:
 * - Responsive scaling using ResizeObserver
 * - Interactive hover and click states
 * - Active chunk highlighting
 * - Proper z-index layering
 * - Accessible keyboard navigation
 * - Performance optimized (60fps)
 *
 * @example
 * <BoundingBoxOverlay
 *   imageElement={imageRef.current}
 *   bboxes={documentBboxes}
 *   originalWidth={612}
 *   originalHeight={792}
 *   onBboxClick={(chunkId, bbox) => console.log('Clicked:', chunkId)}
 *   onBboxHover={(chunkId) => console.log('Hovered:', chunkId)}
 *   activeChunkId="doc1_page1_chunk3"
 * />
 */

import React, { useMemo, useCallback, useRef } from 'react';
import { scaleBboxForDisplay } from '../../utils/coordinateScaler';
import { useBboxScaling } from './useBboxScaling';
import { useDebounce } from '../../hooks/useDebounce';
import { usePerformanceMonitor } from '../../hooks/usePerformanceMonitor';
import { useAccessibleNavigation } from '../../hooks/useAccessibleNavigation';
import { generateBBoxLabel } from '../../utils/accessibility';
import type { BoundingBoxOverlayProps, BBoxWithMetadata } from './types';
import type { BBox } from '../../types/bbox';
import styles from './BoundingBoxOverlay.module.css';

/**
 * BoundingBoxOverlay component.
 *
 * Renders an SVG overlay with interactive bounding boxes positioned
 * over a document page image.
 */
export const BoundingBoxOverlay: React.FC<BoundingBoxOverlayProps> = React.memo(({
  imageElement,
  bboxes,
  originalWidth,
  originalHeight,
  onBboxClick,
  onBboxHover,
  activeChunkId = null,
  hoveredChunkId = null,
  className = '',
}) => {
  // Performance monitoring (dev only)
  const { mark, measure } = usePerformanceMonitor({
    componentName: 'BoundingBoxOverlay',
    enabled: process.env.NODE_ENV === 'development',
  });

  // Reference to the SVG container for keyboard navigation
  const containerRef = useRef<SVGSVGElement>(null);

  // Track displayed image dimensions with ResizeObserver
  const displayedDimensions = useBboxScaling(imageElement);

  // Scale all bboxes for current display dimensions
  const scaledBboxes = useMemo(() => {
    mark('scale-bboxes-start');

    // No scaling if image not yet rendered or has zero dimensions
    if (
      !displayedDimensions.width ||
      !displayedDimensions.height ||
      !originalWidth ||
      !originalHeight
    ) {
      return [];
    }

    const result = bboxes.map((bbox) => {
      const scaled = scaleBboxForDisplay(
        bbox,
        originalWidth,
        originalHeight,
        displayedDimensions.width,
        displayedDimensions.height,
        {
          minSize: 10,
          enforceMinimum: true,
          clampToBounds: true,
        }
      );

      return {
        ...bbox,
        scaled,
      };
    });

    mark('scale-bboxes-end');
    measure('scale-bboxes', 'scale-bboxes-start', 'scale-bboxes-end');

    return result;
  }, [bboxes, originalWidth, originalHeight, displayedDimensions, mark, measure]);

  // Handle bbox click (memoized)
  const handleBboxClick = useCallback((chunkId: string, bbox: BBox) => {
    if (onBboxClick) {
      onBboxClick(chunkId, bbox);
    }
  }, [onBboxClick]);

  // Debounced hover handlers for smoother interaction
  const debouncedHoverCallback = useCallback((chunkId: string | null) => {
    if (onBboxHover) {
      onBboxHover(chunkId);
    }
  }, [onBboxHover]);

  const handleBboxHover = useDebounce(debouncedHoverCallback, 50);

  // Handle bbox mouse enter
  const handleBboxMouseEnter = useCallback((chunkId: string) => {
    handleBboxHover(chunkId);
  }, [handleBboxHover]);

  // Handle bbox mouse leave
  const handleBboxMouseLeave = useCallback(() => {
    handleBboxHover(null);
  }, [handleBboxHover]);

  // Handle keyboard interaction (Enter/Space) - memoized
  const handleBboxKeyDown = useCallback((
    e: React.KeyboardEvent,
    chunkId: string,
    bbox: BBox
  ) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleBboxClick(chunkId, bbox);
    }
  }, [handleBboxClick]);

  // Setup accessible keyboard navigation
  useAccessibleNavigation({
    containerRef: containerRef as any, // SVG element is compatible with HTMLElement for our purposes
    enabled: true,
    onActivate: useCallback(
      (index: number, element: HTMLElement) => {
        const chunkId = element.getAttribute('data-chunk-id');
        const x1 = parseFloat(element.getAttribute('x') || '0');
        const y1 = parseFloat(element.getAttribute('y') || '0');
        const width = parseFloat(element.getAttribute('width') || '0');
        const height = parseFloat(element.getAttribute('height') || '0');

        if (chunkId) {
          const bbox: BBox = {
            x1,
            y1,
            x2: x1 + width,
            y2: y1 + height,
          };
          handleBboxClick(chunkId, bbox);
        }
      },
      [handleBboxClick]
    ),
    onEscape: useCallback(() => {
      // Clear active selection by clicking with empty chunk ID
      if (onBboxClick) {
        onBboxClick('', { x1: 0, y1: 0, x2: 0, y2: 0 });
      }
    }, [onBboxClick]),
    elementSelector: '[role="button"]',
    announceNavigation: true,
    generateAnnouncement: useCallback(
      (element: HTMLElement, index: number, action: 'navigate' | 'activate') => {
        const elementType = element.getAttribute('data-element-type') || 'element';
        const actionText = action === 'activate' ? 'Activated' : 'Navigated to';
        return `${actionText} ${generateBBoxLabel(elementType, index)}`;
      },
      []
    ),
  });

  // Don't render overlay if no image or dimensions
  if (
    !imageElement ||
    !displayedDimensions.width ||
    !displayedDimensions.height
  ) {
    return null;
  }

  return (
    <svg
      ref={containerRef}
      className={`${styles.overlay} ${className}`}
      width={displayedDimensions.width}
      height={displayedDimensions.height}
      viewBox={`0 0 ${displayedDimensions.width} ${displayedDimensions.height}`}
      xmlns="http://www.w3.org/2000/svg"
      role="region"
      aria-label="Document structure overlay with navigable elements"
    >
      {/* Announce navigation instructions for screen readers */}
      <desc>
        Use arrow keys to navigate between document elements. Press Enter or Space to select. Press Escape to clear selection.
      </desc>
      {scaledBboxes.map(({ chunk_id, element_type, scaled }, index) => (
        <BBoxRect
          key={chunk_id}
          chunkId={chunk_id}
          elementType={element_type}
          scaled={scaled}
          index={index}
          isActive={chunk_id === activeChunkId}
          isHovered={chunk_id === hoveredChunkId}
          onBboxClick={handleBboxClick}
          onBboxMouseEnter={handleBboxMouseEnter}
          onBboxMouseLeave={handleBboxMouseLeave}
          onBboxKeyDown={handleBboxKeyDown}
        />
      ))}
    </svg>
  );
});

BoundingBoxOverlay.displayName = 'BoundingBoxOverlay';

/**
 * Individual BBox rectangle component - memoized for performance.
 * Only re-renders when its specific props change.
 */
interface BBoxRectProps {
  chunkId: string;
  elementType?: string;
  scaled: { x1: number; y1: number; x2: number; y2: number; width: number; height: number };
  index: number;
  isActive: boolean;
  isHovered: boolean;
  onBboxClick: (chunkId: string, bbox: BBox) => void;
  onBboxMouseEnter: (chunkId: string) => void;
  onBboxMouseLeave: () => void;
  onBboxKeyDown: (e: React.KeyboardEvent, chunkId: string, bbox: BBox) => void;
}

const BBoxRect: React.FC<BBoxRectProps> = React.memo(({
  chunkId,
  elementType,
  scaled,
  index,
  isActive,
  isHovered,
  onBboxClick,
  onBboxMouseEnter,
  onBboxMouseLeave,
  onBboxKeyDown,
}) => {
  // Determine CSS class for visual state
  const bboxClass = [
    styles.bbox,
    isActive && styles.active,
    isHovered && styles.hovered,
    elementType && styles[`type-${elementType}`],
  ]
    .filter(Boolean)
    .join(' ');

  const bbox: BBox = {
    x1: scaled.x1,
    y1: scaled.y1,
    x2: scaled.x2,
    y2: scaled.y2,
  };

  // Generate accessible label
  const ariaLabel = generateBBoxLabel(elementType || 'element', index);

  return (
    <rect
      className={bboxClass}
      x={scaled.x1}
      y={scaled.y1}
      width={scaled.width}
      height={scaled.height}
      onClick={() => onBboxClick(chunkId, bbox)}
      onMouseEnter={() => onBboxMouseEnter(chunkId)}
      onMouseLeave={onBboxMouseLeave}
      onKeyDown={(e) => onBboxKeyDown(e, chunkId, bbox)}
      tabIndex={0}
      role="button"
      aria-label={ariaLabel}
      aria-pressed={isActive}
      aria-describedby={isActive ? `bbox-active-${chunkId}` : undefined}
      data-chunk-id={chunkId}
      data-element-type={elementType || 'unknown'}
    >
      {/* Provide context for active element */}
      {isActive && (
        <title id={`bbox-active-${chunkId}`}>
          Currently selected. Press Escape to deselect.
        </title>
      )}
    </rect>
  );
});

BBoxRect.displayName = 'BBoxRect';

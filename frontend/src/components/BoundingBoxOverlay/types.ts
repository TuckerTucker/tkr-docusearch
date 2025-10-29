/**
 * BoundingBoxOverlay Type Definitions
 *
 * Agent 5: BoundingBoxOverlay Component
 * Wave 1 - BBox Overlay React Implementation
 *
 * These types define the props and data structures for rendering
 * bounding box overlays on document page images.
 */

import type { BBox } from '../../types/bbox';

/**
 * Bounding box with associated metadata.
 *
 * Extends the base BBox with metadata needed for rendering,
 * interaction, and identification.
 *
 * @example
 * const bbox: BBoxWithMetadata = {
 *   x1: 72,
 *   y1: 100,
 *   x2: 540,
 *   y2: 150,
 *   chunk_id: 'doc1_page1_chunk3',
 *   element_type: 'heading',
 *   confidence: 0.95
 * };
 */
export interface BBoxWithMetadata extends BBox {
  /** Unique identifier for the chunk this bbox represents */
  chunk_id: string;

  /** Type of document element (heading, table, picture, text, etc.) */
  element_type?: string;

  /** Confidence score from detection model (0-1) */
  confidence?: number;

  /** Additional metadata for display or interaction */
  metadata?: Record<string, unknown>;
}

/**
 * Props for the BoundingBoxOverlay component.
 */
export interface BoundingBoxOverlayProps {
  /** Reference to the image element to overlay */
  imageElement: HTMLImageElement | null;

  /** Array of bounding boxes to render */
  bboxes: BBoxWithMetadata[];

  /** Original image width in pixels */
  originalWidth: number;

  /** Original image height in pixels */
  originalHeight: number;

  /** Callback fired when a bbox is clicked */
  onBboxClick?: (chunkId: string, bbox: BBox) => void;

  /** Callback fired when a bbox is hovered or unhovered */
  onBboxHover?: (chunkId: string | null) => void;

  /** ID of the currently active chunk (highlighted) */
  activeChunkId?: string | null;

  /** ID of the currently hovered chunk */
  hoveredChunkId?: string | null;

  /** Additional CSS class name for the overlay container */
  className?: string;
}

/**
 * Dimensions of the displayed image.
 *
 * Used internally by the scaling hook to track image size changes.
 */
export interface DisplayedDimensions {
  /** Displayed width in pixels */
  width: number;

  /** Displayed height in pixels */
  height: number;
}

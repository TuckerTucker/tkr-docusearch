/**
 * BoundingBox Type Definitions
 *
 * Agent 3: Coordinate Scaling Utility Builder
 * Wave 1 - BBox Overlay React Implementation
 *
 * These types define the structure of bounding boxes used throughout the application.
 * All coordinates use a top-left origin coordinate system with pixel units.
 *
 * Coordinate System:
 * - Origin: top-left (0, 0)
 * - X-axis: left to right
 * - Y-axis: top to bottom
 * - Format: [x1, y1, x2, y2] where (x1,y1) = top-left, (x2,y2) = bottom-right
 */

/**
 * Bounding box coordinates in pixel space.
 *
 * Represents a rectangular region with top-left origin coordinates.
 * This is the base format received from the API and stored in ChromaDB.
 *
 * @example
 * const bbox: BBox = {
 *   x1: 72,   // left edge
 *   y1: 100,  // top edge
 *   x2: 540,  // right edge
 *   y2: 150   // bottom edge
 * };
 */
export interface BBox {
  /** Left edge x-coordinate (must be >= 0) */
  x1: number;
  /** Top edge y-coordinate (must be >= 0) */
  y1: number;
  /** Right edge x-coordinate (must be > x1) */
  x2: number;
  /** Bottom edge y-coordinate (must be > y1) */
  y2: number;
}

/**
 * Scaled bounding box with calculated dimensions.
 *
 * Extends BBox with computed width and height for display purposes.
 * This format is used for rendering overlays in the UI.
 *
 * @example
 * const scaledBbox: ScaledBBox = {
 *   x1: 120,
 *   y1: 200,
 *   x2: 900,
 *   y2: 300,
 *   width: 780,   // x2 - x1
 *   height: 100   // y2 - y1
 * };
 */
export interface ScaledBBox extends BBox {
  /** Width of the bounding box (x2 - x1) */
  width: number;
  /** Height of the bounding box (y2 - y1) */
  height: number;
}

/**
 * Validation result for bounding box checks.
 *
 * Provides detailed information about bbox validation failures.
 */
export interface BBoxValidationResult {
  /** Whether the bbox is valid */
  valid: boolean;
  /** Error message if invalid, null otherwise */
  error: string | null;
}

/**
 * Options for bbox scaling operations.
 */
export interface ScalingOptions {
  /** Minimum size in pixels for width and height (default: 10) */
  minSize?: number;
  /** Whether to enforce minimum size (default: true) */
  enforceMinimum?: boolean;
  /** Whether to clamp coordinates to image bounds (default: true) */
  clampToBounds?: boolean;
}

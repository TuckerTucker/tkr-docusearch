/**
 * Coordinate Scaling Utility
 *
 * Agent 3: Coordinate Scaling Utility Builder
 * Wave 1 - BBox Overlay React Implementation
 *
 * This module provides utilities for scaling bounding box coordinates from original
 * image dimensions to displayed dimensions. All coordinates use top-left origin.
 *
 * Key Functions:
 * - scaleBboxForDisplay: Scale bbox from original to display dimensions
 * - validateBbox: Validate bbox meets specification requirements
 * - ensureMinimumSize: Ensure bbox meets minimum size for usability
 *
 * Coordinate System:
 * - Origin: top-left (0, 0)
 * - X-axis: left to right (increases rightward)
 * - Y-axis: top to bottom (increases downward)
 * - Format: [x1, y1, x2, y2] where (x1,y1) = top-left, (x2,y2) = bottom-right
 *
 * Performance:
 * - Zero dependencies (pure functions)
 * - No DOM manipulation
 * - Safe for server-side rendering
 * - Optimized for 60fps interactions
 */

import type { BBox, ScaledBBox, BBoxValidationResult, ScalingOptions } from '../types/bbox';

/**
 * Default minimum size for bounding boxes (in pixels).
 * Ensures interactive elements are large enough to be usable.
 */
const DEFAULT_MIN_SIZE = 10;

/**
 * Scale a bounding box from original image dimensions to displayed dimensions.
 *
 * This function handles responsive scaling for bounding boxes as images resize
 * in the viewport. It maintains aspect ratio and correctly scales all coordinates.
 *
 * The coordinate system remains top-left origin throughout the transformation:
 * - (x1, y1) represents the top-left corner
 * - (x2, y2) represents the bottom-right corner
 *
 * @param bbox - Original bounding box in source image coordinates
 * @param originalWidth - Original image width in pixels
 * @param originalHeight - Original image height in pixels
 * @param displayedWidth - Displayed image width in pixels
 * @param displayedHeight - Displayed image height in pixels
 * @param options - Optional scaling configuration
 * @returns Scaled bounding box with width and height calculated
 *
 * @example
 * // Original image: 612x792, displayed at 1020x1320
 * const bbox = { x1: 72, y1: 100, x2: 540, y2: 150 };
 * const scaled = scaleBboxForDisplay(bbox, 612, 792, 1020, 1320);
 * // Result: { x1: 120, y1: 167, x2: 900, y2: 250, width: 780, height: 83 }
 *
 * @throws {Error} If dimensions are invalid (zero or negative)
 */
export function scaleBboxForDisplay(
  bbox: BBox,
  originalWidth: number,
  originalHeight: number,
  displayedWidth: number,
  displayedHeight: number,
  options: ScalingOptions = {}
): ScaledBBox {
  // Validate input dimensions
  if (originalWidth <= 0 || originalHeight <= 0) {
    throw new Error(
      `Invalid original dimensions: ${originalWidth}x${originalHeight}. Dimensions must be positive.`
    );
  }
  if (displayedWidth <= 0 || displayedHeight <= 0) {
    throw new Error(
      `Invalid displayed dimensions: ${displayedWidth}x${displayedHeight}. Dimensions must be positive.`
    );
  }

  // Extract options with defaults
  const {
    minSize = DEFAULT_MIN_SIZE,
    enforceMinimum = true,
    clampToBounds = true,
  } = options;

  // Calculate scale factors
  const scaleX = displayedWidth / originalWidth;
  const scaleY = displayedHeight / originalHeight;

  // Scale coordinates
  // Note: Y-axis direction is the same (both top-left origin)
  let x1 = bbox.x1 * scaleX;
  let y1 = bbox.y1 * scaleY;
  let x2 = bbox.x2 * scaleX;
  let y2 = bbox.y2 * scaleY;

  // Clamp to bounds if requested
  if (clampToBounds) {
    x1 = Math.max(0, Math.min(x1, displayedWidth));
    y1 = Math.max(0, Math.min(y1, displayedHeight));
    x2 = Math.max(0, Math.min(x2, displayedWidth));
    y2 = Math.max(0, Math.min(y2, displayedHeight));
  }

  // Calculate dimensions
  let width = x2 - x1;
  let height = y2 - y1;

  // Create scaled bbox
  let scaled: ScaledBBox = { x1, y1, x2, y2, width, height };

  // Enforce minimum size if requested
  if (enforceMinimum) {
    scaled = ensureMinimumSize(scaled, minSize);
  }

  return scaled;
}

/**
 * Validate that a bounding box meets specification requirements.
 *
 * Checks:
 * - All coordinates are finite numbers
 * - Coordinates are non-negative
 * - x2 > x1 (positive width)
 * - y2 > y1 (positive height)
 * - Bbox is within image bounds
 *
 * @param bbox - Bounding box to validate
 * @param imageWidth - Image width for bounds checking
 * @param imageHeight - Image height for bounds checking
 * @returns Validation result with error message if invalid
 *
 * @example
 * const bbox = { x1: 72, y1: 100, x2: 540, y2: 150 };
 * const result = validateBbox(bbox, 612, 792);
 * if (!result.valid) {
 *   console.error(result.error);
 * }
 */
export function validateBbox(
  bbox: BBox,
  imageWidth: number,
  imageHeight: number
): BBoxValidationResult {
  // Check for null/undefined
  if (!bbox) {
    return { valid: false, error: 'Bbox is null or undefined' };
  }

  // Check all coordinates are numbers
  const { x1, y1, x2, y2 } = bbox;
  if (!Number.isFinite(x1) || !Number.isFinite(y1) || !Number.isFinite(x2) || !Number.isFinite(y2)) {
    return { valid: false, error: 'Bbox coordinates must be finite numbers' };
  }

  // Check non-negative
  if (x1 < 0 || y1 < 0 || x2 < 0 || y2 < 0) {
    return { valid: false, error: 'Bbox coordinates must be non-negative' };
  }

  // Check positive dimensions
  if (x2 <= x1) {
    return { valid: false, error: `Invalid width: x2 (${x2}) must be > x1 (${x1})` };
  }
  if (y2 <= y1) {
    return { valid: false, error: `Invalid height: y2 (${y2}) must be > y1 (${y1})` };
  }

  // Check image dimensions are valid
  if (imageWidth <= 0 || imageHeight <= 0) {
    return { valid: false, error: 'Image dimensions must be positive' };
  }

  // Check bounds
  if (x1 >= imageWidth || y1 >= imageHeight) {
    return { valid: false, error: 'Bbox starts outside image bounds' };
  }
  if (x2 > imageWidth || y2 > imageHeight) {
    return { valid: false, error: 'Bbox extends outside image bounds' };
  }

  return { valid: true, error: null };
}

/**
 * Ensure bounding box meets minimum size requirements for usability.
 *
 * This function expands bboxes that are too small to be interactive,
 * while maintaining their center point. This improves UX by ensuring
 * clickable/hoverable regions are large enough.
 *
 * @param bbox - Bounding box to check
 * @param minSize - Minimum size in pixels (default: 10)
 * @returns Bbox with minimum size enforced, or original if already large enough
 *
 * @example
 * // Tiny bbox (2x3 pixels)
 * const tiny = { x1: 100, y1: 100, x2: 102, y2: 103, width: 2, height: 3 };
 * const expanded = ensureMinimumSize(tiny, 10);
 * // Result: { x1: 96, y1: 96.5, x2: 106, y2: 106.5, width: 10, height: 10 }
 */
export function ensureMinimumSize(
  bbox: ScaledBBox,
  minSize: number = DEFAULT_MIN_SIZE
): ScaledBBox {
  if (minSize <= 0) {
    return bbox;
  }

  let { x1, y1, x2, y2, width, height } = bbox;
  let modified = false;

  // Expand width if needed
  if (width < minSize) {
    const center = (x1 + x2) / 2;
    const halfMin = minSize / 2;
    x1 = center - halfMin;
    x2 = center + halfMin;
    width = minSize;
    modified = true;
  }

  // Expand height if needed
  if (height < minSize) {
    const center = (y1 + y2) / 2;
    const halfMin = minSize / 2;
    y1 = center - halfMin;
    y2 = center + halfMin;
    height = minSize;
    modified = true;
  }

  return modified ? { x1, y1, x2, y2, width, height } : bbox;
}

/**
 * Calculate the area of a bounding box.
 *
 * @param bbox - Bounding box
 * @returns Area in square pixels
 *
 * @example
 * const bbox = { x1: 0, y1: 0, x2: 100, y2: 50 };
 * const area = calculateBboxArea(bbox); // 5000
 */
export function calculateBboxArea(bbox: BBox): number {
  return (bbox.x2 - bbox.x1) * (bbox.y2 - bbox.y1);
}

/**
 * Check if a point is inside a bounding box.
 *
 * @param bbox - Bounding box
 * @param x - Point x-coordinate
 * @param y - Point y-coordinate
 * @returns True if point is inside bbox
 *
 * @example
 * const bbox = { x1: 0, y1: 0, x2: 100, y2: 100 };
 * isPointInBbox(bbox, 50, 50); // true
 * isPointInBbox(bbox, 150, 50); // false
 */
export function isPointInBbox(bbox: BBox, x: number, y: number): boolean {
  return x >= bbox.x1 && x <= bbox.x2 && y >= bbox.y1 && y <= bbox.y2;
}

/**
 * Calculate the intersection area of two bounding boxes.
 *
 * @param bbox1 - First bounding box
 * @param bbox2 - Second bounding box
 * @returns Intersection area in square pixels (0 if no intersection)
 *
 * @example
 * const bbox1 = { x1: 0, y1: 0, x2: 100, y2: 100 };
 * const bbox2 = { x1: 50, y1: 50, x2: 150, y2: 150 };
 * const area = calculateIntersectionArea(bbox1, bbox2); // 2500 (50x50 overlap)
 */
export function calculateIntersectionArea(bbox1: BBox, bbox2: BBox): number {
  const xOverlap = Math.max(0, Math.min(bbox1.x2, bbox2.x2) - Math.max(bbox1.x1, bbox2.x1));
  const yOverlap = Math.max(0, Math.min(bbox1.y2, bbox2.y2) - Math.max(bbox1.y1, bbox2.y1));
  return xOverlap * yOverlap;
}

/**
 * Calculate Intersection over Union (IoU) for two bounding boxes.
 *
 * IoU is a common metric for measuring bbox overlap, used in computer vision.
 * Returns a value between 0 (no overlap) and 1 (perfect overlap).
 *
 * @param bbox1 - First bounding box
 * @param bbox2 - Second bounding box
 * @returns IoU score (0-1)
 *
 * @example
 * const bbox1 = { x1: 0, y1: 0, x2: 100, y2: 100 };
 * const bbox2 = { x1: 50, y1: 50, x2: 150, y2: 150 };
 * const iou = calculateIoU(bbox1, bbox2); // ~0.14
 */
export function calculateIoU(bbox1: BBox, bbox2: BBox): number {
  const intersection = calculateIntersectionArea(bbox1, bbox2);
  if (intersection === 0) return 0;

  const area1 = calculateBboxArea(bbox1);
  const area2 = calculateBboxArea(bbox2);
  const union = area1 + area2 - intersection;

  return union > 0 ? intersection / union : 0;
}

/**
 * Structure Transformation Utilities
 *
 * Agent 8: BBoxController Integration Layer
 * Wave 1 - BBox Overlay React Implementation
 *
 * Transforms PageStructure data from the API into flat BBoxWithMetadata array
 * suitable for rendering in BoundingBoxOverlay component.
 *
 * The API returns structured elements (headings, tables, pictures, etc.) each
 * with their own bbox. This module flattens them into a single array and assigns
 * chunk IDs based on element type and position.
 */

import type { PageStructure } from '../../../../types/structure';
import type { BBoxWithMetadata } from '../../../../components/BoundingBoxOverlay/types';
import type { BBox } from '../../../../types/bbox';

/**
 * Convert Docling bounding box (bottom-left origin) to frontend format (top-left origin).
 *
 * Docling format: [left, bottom, right, top] with bottom-left origin
 * Frontend format: {x1, y1, x2, y2} with top-left origin
 *
 * @param doclingBbox - Bounding box in Docling format
 * @param pageHeight - Page height in points (for coordinate conversion)
 * @returns Bounding box in frontend format
 */
function convertDoclingBbox(
  doclingBbox: { left: number; bottom: number; right: number; top: number },
  pageHeight: number
): BBox {
  // Convert from bottom-left origin to top-left origin
  // y1 (top in frontend) = pageHeight - top (from bottom)
  // y2 (bottom in frontend) = pageHeight - bottom (from bottom)
  return {
    x1: doclingBbox.left,
    y1: pageHeight - doclingBbox.top,
    x2: doclingBbox.right,
    y2: pageHeight - doclingBbox.bottom,
  };
}

/**
 * Transform PageStructure to flat array of BBoxWithMetadata.
 *
 * Extracts all structural elements (headings, tables, pictures, code blocks, formulas)
 * from the PageStructure response and converts them to a flat array suitable for
 * rendering in BoundingBoxOverlay.
 *
 * Each element gets:
 * - A unique chunk_id based on element type and index
 * - Converted bbox coordinates (bottom-left → top-left origin)
 * - Element type for visual styling
 * - Optional metadata for additional context
 *
 * @param structure - Page structure from API
 * @returns Array of bounding boxes with metadata
 *
 * @example
 * ```ts
 * const structure = await fetchPageStructure('doc123', 1);
 * const bboxes = transformStructureToBboxes(structure);
 * // Returns: [
 * //   { chunk_id: 'heading-0', element_type: 'heading', x1: 72, y1: 72, ... },
 * //   { chunk_id: 'table-0', element_type: 'table', x1: 100, y1: 200, ... },
 * //   ...
 * // ]
 * ```
 */
export function transformStructureToBboxes(
  structure: PageStructure
): BBoxWithMetadata[] {
  const bboxes: BBoxWithMetadata[] = [];

  // Determine page height for coordinate conversion
  // Use image_dimensions if available, otherwise use standard US Letter size (11" × 8.5" = 792pt × 612pt)
  const pageHeight = structure.image_dimensions?.height || 792;

  // Extract headings
  structure.headings.forEach((heading, index) => {
    if (heading.bbox) {
      const convertedBbox = convertDoclingBbox(heading.bbox, pageHeight);
      bboxes.push({
        ...convertedBbox,
        chunk_id: `heading-${index}`,
        element_type: 'heading',
        metadata: {
          text: heading.text,
          level: heading.level,
          section_path: heading.section_path,
        },
      });
    }
  });

  // Extract tables
  structure.tables.forEach((table, index) => {
    if (table.bbox) {
      const convertedBbox = convertDoclingBbox(table.bbox, pageHeight);
      bboxes.push({
        ...convertedBbox,
        chunk_id: `table-${index}`,
        element_type: 'table',
        metadata: {
          caption: table.caption,
          rows: table.rows,
          cols: table.cols,
          has_header: table.has_header,
          table_id: table.table_id,
        },
      });
    }
  });

  // Extract pictures
  structure.pictures.forEach((picture, index) => {
    if (picture.bbox) {
      const convertedBbox = convertDoclingBbox(picture.bbox, pageHeight);
      bboxes.push({
        ...convertedBbox,
        chunk_id: `picture-${index}`,
        element_type: 'picture',
        confidence: picture.confidence,
        metadata: {
          type: picture.type,
          caption: picture.caption,
          picture_id: picture.picture_id,
        },
      });
    }
  });

  // Extract code blocks
  structure.code_blocks.forEach((codeBlock, index) => {
    if (codeBlock.bbox) {
      const convertedBbox = convertDoclingBbox(codeBlock.bbox, pageHeight);
      bboxes.push({
        ...convertedBbox,
        chunk_id: `code-${index}`,
        element_type: 'code',
        metadata: {
          language: codeBlock.language,
          lines: codeBlock.lines,
        },
      });
    }
  });

  // Extract formulas
  structure.formulas.forEach((formula, index) => {
    if (formula.bbox) {
      const convertedBbox = convertDoclingBbox(formula.bbox, pageHeight);
      bboxes.push({
        ...convertedBbox,
        chunk_id: `formula-${index}`,
        element_type: 'formula',
        metadata: {
          latex: formula.latex,
        },
      });
    }
  });

  return bboxes;
}

/**
 * Get coordinate system dimensions from PageStructure.
 *
 * Returns the original image dimensions needed for coordinate scaling
 * in BoundingBoxOverlay component.
 *
 * @param structure - Page structure from API
 * @returns Original image width and height in points
 */
export function getOriginalDimensions(structure: PageStructure): {
  width: number;
  height: number;
} {
  // Use image_dimensions if available
  if (structure.image_dimensions) {
    return {
      width: structure.image_dimensions.width,
      height: structure.image_dimensions.height,
    };
  }

  // Fallback to standard US Letter size (8.5" × 11" = 612pt × 792pt)
  return {
    width: 612,
    height: 792,
  };
}

/**
 * Check if structure has any bounding boxes to display.
 *
 * Useful for conditionally rendering the overlay only when there are bboxes.
 *
 * @param structure - Page structure from API
 * @returns True if structure contains at least one bbox
 */
export function hasAnyBboxes(structure: PageStructure): boolean {
  return (
    structure.headings.some((h) => h.bbox !== null) ||
    structure.tables.some((t) => t.bbox !== null) ||
    structure.pictures.some((p) => p.bbox !== null) ||
    structure.code_blocks.some((c) => c.bbox !== null) ||
    structure.formulas.some((f) => f.bbox !== null)
  );
}

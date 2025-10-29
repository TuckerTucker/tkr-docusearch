/**
 * Document Structure Type Definitions
 *
 * Agent 2: TypeScript Types for BoundingBox Overlay
 * Agent 6: Document Structure Hook Builder
 * Wave 1 - BBox Overlay React Implementation
 *
 * These types define the structure of document elements (headings, tables, pictures, etc.)
 * returned by the Structure API endpoint.
 *
 * API Endpoint: GET /api/documents/{doc_id}/pages/{page}/structure
 * Backend Source: src/api/structure.py, src/processing/api/structure_endpoints.py
 */

/**
 * Bounding box coordinates in Docling format (bottom-left origin).
 *
 * Format: [left, bottom, right, top]
 * Units: Points (1/72 inch)
 * Origin: Bottom-left corner of page
 *
 * Note: Frontend must convert to top-left origin for browser rendering.
 * See: integration-contracts/docling-structure-spec.md
 */
export interface BoundingBox {
  /** Left edge (x1) */
  left: number;
  /** Bottom edge (y1) - measured from bottom of page */
  bottom: number;
  /** Right edge (x2) */
  right: number;
  /** Top edge (y2) - measured from bottom of page */
  top: number;
}

/**
 * Document heading information with position and hierarchy.
 */
export interface HeadingInfo {
  /** Heading text content */
  text: string;
  /** Heading level (TITLE, SECTION_HEADER, etc.) */
  level: string;
  /** Page number where heading appears (1-indexed) */
  page: number;
  /** Hierarchical section path (e.g., "1. Introduction > 1.1 Background") */
  section_path: string;
  /** Bounding box if available (null if not extracted) */
  bbox: BoundingBox | null;
}

/**
 * Document table information with metadata.
 */
export interface TableInfo {
  /** Page number where table appears (1-indexed) */
  page: number;
  /** Table caption if available */
  caption: string | null;
  /** Number of rows */
  rows: number;
  /** Number of columns */
  cols: number;
  /** Whether table has header row */
  has_header: boolean;
  /** Unique table identifier */
  table_id: string;
  /** Bounding box if available */
  bbox: BoundingBox | null;
}

/**
 * Document picture/image information with classification.
 */
export interface PictureInfo {
  /** Page number where picture appears (1-indexed) */
  page: number;
  /** Picture type (chart, diagram, photo, etc.) */
  type: string;
  /** Picture caption if available */
  caption: string | null;
  /** Classification confidence (0-1) */
  confidence: number;
  /** Unique picture identifier */
  picture_id: string;
  /** Bounding box if available */
  bbox: BoundingBox | null;
}

/**
 * Code block information with language detection.
 */
export interface CodeBlockInfo {
  /** Page number where code appears (1-indexed) */
  page: number;
  /** Detected programming language (e.g., "python", "javascript") */
  language: string | null;
  /** Number of lines */
  lines: number;
  /** Bounding box if available */
  bbox: BoundingBox | null;
}

/**
 * Mathematical formula information.
 */
export interface FormulaInfo {
  /** Page number where formula appears (1-indexed) */
  page: number;
  /** LaTeX representation */
  latex: string | null;
  /** Bounding box if available */
  bbox: BoundingBox | null;
}

/**
 * Document structure summary statistics.
 */
export interface StructureSummary {
  /** Total number of sections */
  total_sections: number;
  /** Maximum heading nesting depth */
  max_depth: number;
  /** Whether document has table of contents */
  has_toc: boolean;
}

/**
 * Coordinate system metadata for bounding boxes.
 */
export interface CoordinateSystemInfo {
  /** Bounding box coordinate format */
  format: string;
  /** Coordinate system origin */
  origin: string;
  /** Coordinate units */
  units: string;
  /** Full specification reference */
  reference: string;
}

/**
 * Page structure response from API.
 *
 * Contains all structural elements (headings, tables, pictures, etc.)
 * for a specific page with bounding box coordinates.
 */
export interface PageStructure {
  /** Document identifier */
  doc_id: string;
  /** Page number (1-indexed) */
  page: number;
  /** True if structure metadata exists */
  has_structure: boolean;
  /** Headings on this page */
  headings: HeadingInfo[];
  /** Tables on this page */
  tables: TableInfo[];
  /** Pictures on this page */
  pictures: PictureInfo[];
  /** Code blocks on this page */
  code_blocks: CodeBlockInfo[];
  /** Formulas on this page */
  formulas: FormulaInfo[];
  /** Summary statistics (null if no structure) */
  summary: StructureSummary | null;
  /** Coordinate system metadata */
  coordinate_system: CoordinateSystemInfo;
  /** Image dimensions for coordinate conversion (optional) */
  image_dimensions?: {
    width: number;
    height: number;
  };
}

/**
 * Error response from structure API.
 */
export interface StructureErrorResponse {
  /** Human-readable error message */
  error: string;
  /** Machine-readable error code */
  code: string;
  /** Additional error details */
  details: Record<string, any>;
}

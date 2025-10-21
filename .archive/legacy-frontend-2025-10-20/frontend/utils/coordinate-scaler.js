/**
 * Coordinate Scaler Utility
 *
 * Handles conversion between PDF coordinate space and screen/SVG coordinate space.
 *
 * CRITICAL: PDF uses BOTTOM-LEFT origin, SVG/Screen uses TOP-LEFT origin
 * Y-axis flip is required for correct display.
 *
 * Reference: integration-contracts/docling-structure-spec.md
 *
 * PDF Coordinate System:
 * - Origin: Bottom-left corner (0, 0)
 * - X-axis: Left to right (increases →)
 * - Y-axis: Bottom to top (increases ↑)
 * - Units: Points (1pt = 1/72 inch)
 * - Bbox format: [left, bottom, right, top]
 *
 * SVG/Screen Coordinate System:
 * - Origin: Top-left corner (0, 0)
 * - X-axis: Left to right (increases →)
 * - Y-axis: Top to bottom (increases ↓)
 * - Units: Pixels
 * - Bbox format: {x, y, width, height}
 */

/**
 * Scale PDF bbox to screen coordinates with Y-axis flip
 *
 * @param {Object} pdfBbox - PDF bbox with bottom-left origin
 * @param {number} pdfBbox.left - Left edge (x1)
 * @param {number} pdfBbox.bottom - Bottom edge (y1, lower Y value)
 * @param {number} pdfBbox.right - Right edge (x2)
 * @param {number} pdfBbox.top - Top edge (y2, higher Y value)
 * @param {number} pdfWidth - Original PDF page width in points
 * @param {number} pdfHeight - Original PDF page height in points
 * @param {number} imageWidth - Displayed image width in pixels
 * @param {number} imageHeight - Displayed image height in pixels
 * @returns {Object} Screen bbox {x, y, width, height}
 *
 * @example
 * // PDF bbox: {left: 100, bottom: 600, right: 250, top: 650}
 * // PDF page: 612 x 792 points (US Letter)
 * // Image: 1020 x 1320 pixels
 * const screenBbox = scaleBboxToScreen(
 *   {left: 100, bottom: 600, right: 250, top: 650},
 *   612, 792, 1020, 1320
 * );
 * // Result: {x: 166.67, y: 1113.64, width: 250, height: 83.33}
 */
export function scaleBboxToScreen(pdfBbox, pdfWidth, pdfHeight, imageWidth, imageHeight) {
  // Validate inputs
  if (!pdfBbox || typeof pdfBbox !== 'object') {
    throw new Error('Invalid PDF bbox: must be an object');
  }

  const { left, bottom, right, top } = pdfBbox;

  if ([left, bottom, right, top, pdfWidth, pdfHeight, imageWidth, imageHeight].some(v => typeof v !== 'number' || isNaN(v))) {
    throw new Error('All bbox and dimension parameters must be valid numbers');
  }

  if (left >= right) {
    throw new Error(`Invalid bbox: left (${left}) must be < right (${right})`);
  }

  if (bottom >= top) {
    throw new Error(`Invalid bbox: bottom (${bottom}) must be < top (${top})`);
  }

  if (pdfWidth <= 0 || pdfHeight <= 0) {
    throw new Error('PDF dimensions must be positive');
  }

  if (imageWidth <= 0 || imageHeight <= 0) {
    throw new Error('Image dimensions must be positive');
  }

  // Calculate scale factors
  const scaleX = imageWidth / pdfWidth;
  const scaleY = imageHeight / pdfHeight;

  // Convert to screen coordinates with Y-axis flip
  // CRITICAL: PDF Y increases upward, Screen Y increases downward
  // PDF top (higher Y) → Screen top (lower Y)
  // PDF bottom (lower Y) → Screen bottom (higher Y)

  const screenLeft = left * scaleX;
  const screenTop = imageHeight - (top * scaleY);      // FLIP: PDF top → Screen top
  const screenRight = right * scaleX;
  const screenBottom = imageHeight - (bottom * scaleY);  // FLIP: PDF bottom → Screen bottom

  // Calculate width and height
  const width = screenRight - screenLeft;
  const height = screenBottom - screenTop;  // Note: screenBottom > screenTop after flip

  return {
    x: screenLeft,
    y: screenTop,
    width: width,
    height: height
  };
}

/**
 * Convert PDF coordinates to SVG coordinates
 *
 * This is the core transformation that handles the Y-axis flip.
 *
 * @param {Object} pdfBbox - PDF bbox {left, bottom, right, top}
 * @param {number} pdfHeight - PDF page height in points
 * @param {number} imageHeight - Image height in pixels
 * @param {number} scale - Scale factor (imageHeight / pdfHeight)
 * @returns {Object} SVG rect {x, y, width, height}
 */
export function pdfToSvgCoordinates(pdfBbox, pdfHeight, imageHeight, scale) {
  const { left, bottom, right, top } = pdfBbox;

  // Scale X coordinates (no flip needed)
  const x = left * scale;
  const width = (right - left) * scale;

  // Scale and flip Y coordinates
  // PDF: Y increases upward from bottom
  // SVG: Y increases downward from top
  const svgTop = imageHeight - (top * scale);
  const svgBottom = imageHeight - (bottom * scale);
  const y = svgTop;
  const height = svgBottom - svgTop;

  return { x, y, width, height };
}

/**
 * Validate bbox format and constraints
 *
 * @param {Object} bbox - Bbox to validate
 * @param {string} origin - Coordinate origin ('bottom-left' or 'top-left')
 * @returns {boolean} True if valid
 * @throws {Error} If validation fails
 */
export function validateBbox(bbox, origin = 'bottom-left') {
  if (!bbox || typeof bbox !== 'object') {
    throw new Error('Bbox must be an object');
  }

  if (origin === 'bottom-left') {
    const { left, bottom, right, top } = bbox;

    if ([left, bottom, right, top].some(v => typeof v !== 'number' || isNaN(v))) {
      throw new Error('All bbox coordinates must be valid numbers');
    }

    if (left < 0 || bottom < 0) {
      throw new Error('Coordinates must be non-negative');
    }

    if (left >= right) {
      throw new Error(`left (${left}) must be < right (${right})`);
    }

    if (bottom >= top) {
      throw new Error(`bottom (${bottom}) must be < top (${top})`);
    }
  } else if (origin === 'top-left') {
    const { x, y, width, height } = bbox;

    if ([x, y, width, height].some(v => typeof v !== 'number' || isNaN(v))) {
      throw new Error('All bbox coordinates must be valid numbers');
    }

    if (x < 0 || y < 0) {
      throw new Error('Coordinates must be non-negative');
    }

    if (width <= 0 || height <= 0) {
      throw new Error('Width and height must be positive');
    }
  } else {
    throw new Error(`Unknown origin: ${origin}`);
  }

  return true;
}

/**
 * Calculate scale factors for responsive scaling
 *
 * @param {number} pdfWidth - PDF page width in points
 * @param {number} pdfHeight - PDF page height in points
 * @param {number} imageWidth - Image width in pixels
 * @param {number} imageHeight - Image height in pixels
 * @returns {Object} Scale factors {scaleX, scaleY}
 */
export function calculateScaleFactors(pdfWidth, pdfHeight, imageWidth, imageHeight) {
  if ([pdfWidth, pdfHeight, imageWidth, imageHeight].some(v => v <= 0)) {
    throw new Error('All dimensions must be positive');
  }

  return {
    scaleX: imageWidth / pdfWidth,
    scaleY: imageHeight / pdfHeight
  };
}

/**
 * Batch convert multiple PDF bboxes to screen coordinates
 *
 * @param {Array<Object>} pdfBboxes - Array of PDF bboxes
 * @param {number} pdfWidth - PDF page width
 * @param {number} pdfHeight - PDF page height
 * @param {number} imageWidth - Image width
 * @param {number} imageHeight - Image height
 * @returns {Array<Object>} Array of screen bboxes
 */
export function batchScaleBboxes(pdfBboxes, pdfWidth, pdfHeight, imageWidth, imageHeight) {
  if (!Array.isArray(pdfBboxes)) {
    throw new Error('pdfBboxes must be an array');
  }

  return pdfBboxes.map(bbox =>
    scaleBboxToScreen(bbox, pdfWidth, pdfHeight, imageWidth, imageHeight)
  );
}

/**
 * Get common PDF page dimensions (for reference/testing)
 *
 * @param {string} pageSize - Page size name ('letter', 'a4', 'legal')
 * @returns {Object} Page dimensions {width, height} in points
 */
export function getStandardPageDimensions(pageSize) {
  const dimensions = {
    'letter': { width: 612, height: 792 },
    'a4': { width: 595.3, height: 841.9 },
    'legal': { width: 612, height: 1008 }
  };

  const size = pageSize.toLowerCase();
  if (!dimensions[size]) {
    throw new Error(`Unknown page size: ${pageSize}. Use 'letter', 'a4', or 'legal'`);
  }

  return dimensions[size];
}

/**
 * Coordinate Scaler Tests
 *
 * Agent 3: Coordinate Scaling Utility Builder
 * Wave 1 - BBox Overlay React Implementation
 *
 * Comprehensive test suite covering:
 * - Basic scaling operations
 * - Edge cases (zero dimensions, tiny bboxes, huge bboxes)
 * - Validation logic
 * - Minimum size enforcement
 * - Error handling (null, undefined, negative values)
 * - Helper functions (area, intersection, IoU)
 *
 * Target: 100% code coverage
 */

import { describe, test, expect } from 'vitest';
import type { BBox, ScaledBBox } from '../../types/bbox';
import {
  scaleBboxForDisplay,
  validateBbox,
  ensureMinimumSize,
  calculateBboxArea,
  isPointInBbox,
  calculateIntersectionArea,
  calculateIoU,
} from '../coordinateScaler';

// ============================================================================
// scaleBboxForDisplay Tests
// ============================================================================

describe('scaleBboxForDisplay', () => {
  describe('basic scaling', () => {
    test('scales bbox to larger dimensions', () => {
      const bbox: BBox = { x1: 72, y1: 100, x2: 540, y2: 150 };
      const result = scaleBboxForDisplay(bbox, 612, 792, 1020, 1320);

      // Scale factors: 1020/612 = 1.6667, 1320/792 = 1.6667
      expect(result.x1).toBeCloseTo(120, 0);
      expect(result.y1).toBeCloseTo(166.67, 1);
      expect(result.x2).toBeCloseTo(900, 0);
      expect(result.y2).toBeCloseTo(250, 0);
      expect(result.width).toBeCloseTo(780, 0);
      expect(result.height).toBeCloseTo(83.33, 1);
    });

    test('scales bbox to smaller dimensions', () => {
      const bbox: BBox = { x1: 120, y1: 200, x2: 900, y2: 300 };
      const result = scaleBboxForDisplay(bbox, 1020, 1320, 612, 792);

      // Scale factors: 612/1020 = 0.6, 792/1320 = 0.6
      expect(result.x1).toBeCloseTo(72, 0);
      expect(result.y1).toBeCloseTo(120, 0);
      expect(result.x2).toBeCloseTo(540, 0);
      expect(result.y2).toBeCloseTo(180, 0);
      expect(result.width).toBeCloseTo(468, 0);
      expect(result.height).toBeCloseTo(60, 0);
    });

    test('handles same dimensions (no scaling)', () => {
      const bbox: BBox = { x1: 10, y1: 20, x2: 100, y2: 200 };
      const result = scaleBboxForDisplay(bbox, 612, 792, 612, 792);

      expect(result.x1).toBe(10);
      expect(result.y1).toBe(20);
      expect(result.x2).toBe(100);
      expect(result.y2).toBe(200);
      expect(result.width).toBe(90);
      expect(result.height).toBe(180);
    });

    test('scales with different aspect ratio', () => {
      const bbox: BBox = { x1: 0, y1: 0, x2: 100, y2: 100 };
      const result = scaleBboxForDisplay(bbox, 100, 100, 200, 400);

      // X scaled by 2, Y scaled by 4
      expect(result.x1).toBe(0);
      expect(result.y1).toBe(0);
      expect(result.x2).toBe(200);
      expect(result.y2).toBe(400);
      expect(result.width).toBe(200);
      expect(result.height).toBe(400);
    });
  });

  describe('edge cases', () => {
    test('handles tiny bbox (1x1 pixel)', () => {
      const bbox: BBox = { x1: 50, y1: 50, x2: 51, y2: 51 };
      const result = scaleBboxForDisplay(bbox, 100, 100, 200, 200, {
        enforceMinimum: false,
      });

      expect(result.x1).toBe(100);
      expect(result.y1).toBe(100);
      expect(result.x2).toBe(102);
      expect(result.y2).toBe(102);
      expect(result.width).toBe(2);
      expect(result.height).toBe(2);
    });

    test('handles bbox at origin', () => {
      const bbox: BBox = { x1: 0, y1: 0, x2: 50, y2: 50 };
      const result = scaleBboxForDisplay(bbox, 100, 100, 200, 200);

      expect(result.x1).toBe(0);
      expect(result.y1).toBe(0);
      expect(result.x2).toBe(100);
      expect(result.y2).toBe(100);
    });

    test('handles bbox at far corner', () => {
      const bbox: BBox = { x1: 550, y1: 750, x2: 600, y2: 790 };
      const result = scaleBboxForDisplay(bbox, 600, 800, 300, 400);

      expect(result.x1).toBeCloseTo(275, 0);
      expect(result.y1).toBeCloseTo(375, 0);
      expect(result.x2).toBeCloseTo(300, 0);
      expect(result.y2).toBeCloseTo(395, 0);
    });

    test('handles very large bbox', () => {
      const bbox: BBox = { x1: 10, y1: 10, x2: 5990, y2: 7990 };
      const result = scaleBboxForDisplay(bbox, 6000, 8000, 600, 800);

      expect(result.x1).toBe(1);
      expect(result.y1).toBe(1);
      expect(result.x2).toBeCloseTo(599, 0);
      expect(result.y2).toBeCloseTo(799, 0);
    });

    test('handles fractional scaling', () => {
      const bbox: BBox = { x1: 33, y1: 33, x2: 66, y2: 66 };
      const result = scaleBboxForDisplay(bbox, 100, 100, 300, 300);

      expect(result.x1).toBe(99);
      expect(result.y1).toBe(99);
      expect(result.x2).toBe(198);
      expect(result.y2).toBe(198);
      expect(result.width).toBe(99);
      expect(result.height).toBe(99);
    });
  });

  describe('minimum size enforcement', () => {
    test('expands tiny bbox to minimum size by default', () => {
      const bbox: BBox = { x1: 100, y1: 100, x2: 102, y2: 103 };
      const result = scaleBboxForDisplay(bbox, 1000, 1000, 1000, 1000);

      // Minimum size is 10px by default
      expect(result.width).toBeGreaterThanOrEqual(10);
      expect(result.height).toBeGreaterThanOrEqual(10);
    });

    test('respects custom minimum size', () => {
      const bbox: BBox = { x1: 100, y1: 100, x2: 102, y2: 103 };
      const result = scaleBboxForDisplay(bbox, 1000, 1000, 1000, 1000, {
        minSize: 20,
      });

      expect(result.width).toBeGreaterThanOrEqual(20);
      expect(result.height).toBeGreaterThanOrEqual(20);
    });

    test('does not expand when enforceMinimum is false', () => {
      const bbox: BBox = { x1: 100, y1: 100, x2: 102, y2: 103 };
      const result = scaleBboxForDisplay(bbox, 1000, 1000, 1000, 1000, {
        enforceMinimum: false,
      });

      expect(result.width).toBe(2);
      expect(result.height).toBe(3);
    });

    test('leaves large bbox unchanged', () => {
      const bbox: BBox = { x1: 0, y1: 0, x2: 100, y2: 100 };
      const result = scaleBboxForDisplay(bbox, 1000, 1000, 1000, 1000);

      expect(result.width).toBe(100);
      expect(result.height).toBe(100);
    });
  });

  describe('clamping to bounds', () => {
    test('clamps bbox that exceeds displayed bounds', () => {
      const bbox: BBox = { x1: 580, y1: 760, x2: 620, y2: 800 };
      const result = scaleBboxForDisplay(bbox, 612, 792, 600, 800, {
        clampToBounds: true,
      });

      expect(result.x1).toBeGreaterThanOrEqual(0);
      expect(result.y1).toBeGreaterThanOrEqual(0);
      expect(result.x2).toBeLessThanOrEqual(600);
      expect(result.y2).toBeLessThanOrEqual(800);
    });

    test('allows bbox to exceed bounds when clamping disabled', () => {
      const bbox: BBox = { x1: 580, y1: 760, x2: 620, y2: 800 };
      const result = scaleBboxForDisplay(bbox, 612, 792, 600, 800, {
        clampToBounds: false,
      });

      // Should scale without clamping
      expect(result.x2).toBeGreaterThan(600);
      expect(result.y2).toBeGreaterThan(800);
    });

    test('clamps negative coordinates to zero', () => {
      // This would happen if bbox is partially off-image
      const bbox: BBox = { x1: 0, y1: 0, x2: 100, y2: 100 };
      const result = scaleBboxForDisplay(bbox, 100, 100, 50, 50);

      expect(result.x1).toBeGreaterThanOrEqual(0);
      expect(result.y1).toBeGreaterThanOrEqual(0);
    });
  });

  describe('error handling', () => {
    test('throws on zero original width', () => {
      const bbox: BBox = { x1: 0, y1: 0, x2: 100, y2: 100 };
      expect(() => scaleBboxForDisplay(bbox, 0, 100, 200, 200)).toThrow(
        'Invalid original dimensions'
      );
    });

    test('throws on zero original height', () => {
      const bbox: BBox = { x1: 0, y1: 0, x2: 100, y2: 100 };
      expect(() => scaleBboxForDisplay(bbox, 100, 0, 200, 200)).toThrow(
        'Invalid original dimensions'
      );
    });

    test('throws on negative original dimensions', () => {
      const bbox: BBox = { x1: 0, y1: 0, x2: 100, y2: 100 };
      expect(() => scaleBboxForDisplay(bbox, -100, 100, 200, 200)).toThrow(
        'Invalid original dimensions'
      );
    });

    test('throws on zero displayed width', () => {
      const bbox: BBox = { x1: 0, y1: 0, x2: 100, y2: 100 };
      expect(() => scaleBboxForDisplay(bbox, 100, 100, 0, 200)).toThrow(
        'Invalid displayed dimensions'
      );
    });

    test('throws on zero displayed height', () => {
      const bbox: BBox = { x1: 0, y1: 0, x2: 100, y2: 100 };
      expect(() => scaleBboxForDisplay(bbox, 100, 100, 200, 0)).toThrow(
        'Invalid displayed dimensions'
      );
    });

    test('throws on negative displayed dimensions', () => {
      const bbox: BBox = { x1: 0, y1: 0, x2: 100, y2: 100 };
      expect(() => scaleBboxForDisplay(bbox, 100, 100, -200, 200)).toThrow(
        'Invalid displayed dimensions'
      );
    });
  });

  describe('real-world scenarios', () => {
    test('handles typical PDF page at 150 DPI', () => {
      // PDF: 612x792 pts, Image: 1275x1650 px (150 DPI)
      const bbox: BBox = { x1: 72, y1: 72, x2: 144, y2: 144 };
      const result = scaleBboxForDisplay(bbox, 612, 792, 1275, 1650);

      // Scale factor = 150/72 = 2.0833...
      expect(result.width).toBeCloseTo(150, 0);
      expect(result.height).toBeCloseTo(150, 0);
    });

    test('handles heading at top of page', () => {
      const bbox: BBox = { x1: 72, y1: 650, x2: 540, y2: 720 };
      const result = scaleBboxForDisplay(bbox, 612, 792, 1020, 1320);

      // High Y values should remain high (top-left origin)
      expect(result.y1).toBeGreaterThan(1000);
      expect(result.y2).toBeGreaterThan(1100);
    });

    test('handles picture at bottom of page', () => {
      const bbox: BBox = { x1: 150, y1: 100, x2: 462, y2: 300 };
      const result = scaleBboxForDisplay(bbox, 612, 792, 1020, 1320);

      // Low Y values should remain low (near top)
      expect(result.y1).toBeLessThan(300);
      expect(result.y2).toBeLessThan(600);
    });

    test('handles table spanning middle of page', () => {
      const bbox: BBox = { x1: 100, y1: 350, x2: 512, y2: 600 };
      const result = scaleBboxForDisplay(bbox, 612, 792, 1020, 1320);

      // Middle Y values should be in middle range
      expect(result.y1).toBeGreaterThan(500);
      expect(result.y1).toBeLessThan(700);
      expect(result.y2).toBeGreaterThan(900);
      expect(result.y2).toBeLessThan(1100);
    });

    test('handles responsive resize from desktop to mobile', () => {
      const bbox: BBox = { x1: 100, y1: 100, x2: 500, y2: 300 };
      const desktop = scaleBboxForDisplay(bbox, 612, 792, 1200, 1600);
      const mobile = scaleBboxForDisplay(bbox, 612, 792, 400, 533);

      // Mobile should be smaller than desktop
      expect(mobile.width).toBeLessThan(desktop.width);
      expect(mobile.height).toBeLessThan(desktop.height);

      // But proportions should be maintained
      const desktopRatio = desktop.width / desktop.height;
      const mobileRatio = mobile.width / mobile.height;
      expect(mobileRatio).toBeCloseTo(desktopRatio, 1);
    });
  });
});

// ============================================================================
// validateBbox Tests
// ============================================================================

describe('validateBbox', () => {
  describe('valid bboxes', () => {
    test('accepts valid bbox', () => {
      const bbox: BBox = { x1: 10, y1: 20, x2: 100, y2: 200 };
      const result = validateBbox(bbox, 612, 792);

      expect(result.valid).toBe(true);
      expect(result.error).toBe(null);
    });

    test('accepts bbox at origin', () => {
      const bbox: BBox = { x1: 0, y1: 0, x2: 100, y2: 100 };
      const result = validateBbox(bbox, 612, 792);

      expect(result.valid).toBe(true);
    });

    test('accepts bbox at far corner', () => {
      const bbox: BBox = { x1: 500, y1: 700, x2: 612, y2: 792 };
      const result = validateBbox(bbox, 612, 792);

      expect(result.valid).toBe(true);
    });

    test('accepts tiny 1x1 bbox', () => {
      const bbox: BBox = { x1: 50, y1: 50, x2: 51, y2: 51 };
      const result = validateBbox(bbox, 612, 792);

      expect(result.valid).toBe(true);
    });
  });

  describe('invalid bboxes', () => {
    test('rejects null bbox', () => {
      const result = validateBbox(null as any, 612, 792);

      expect(result.valid).toBe(false);
      expect(result.error).toContain('null or undefined');
    });

    test('rejects undefined bbox', () => {
      const result = validateBbox(undefined as any, 612, 792);

      expect(result.valid).toBe(false);
      expect(result.error).toContain('null or undefined');
    });

    test('rejects non-finite coordinates (NaN)', () => {
      const bbox: BBox = { x1: NaN, y1: 20, x2: 100, y2: 200 };
      const result = validateBbox(bbox, 612, 792);

      expect(result.valid).toBe(false);
      expect(result.error).toContain('finite numbers');
    });

    test('rejects non-finite coordinates (Infinity)', () => {
      const bbox: BBox = { x1: 10, y1: Infinity, x2: 100, y2: 200 };
      const result = validateBbox(bbox, 612, 792);

      expect(result.valid).toBe(false);
      expect(result.error).toContain('finite numbers');
    });

    test('rejects negative x1', () => {
      const bbox: BBox = { x1: -10, y1: 20, x2: 100, y2: 200 };
      const result = validateBbox(bbox, 612, 792);

      expect(result.valid).toBe(false);
      expect(result.error).toContain('non-negative');
    });

    test('rejects negative y1', () => {
      const bbox: BBox = { x1: 10, y1: -20, x2: 100, y2: 200 };
      const result = validateBbox(bbox, 612, 792);

      expect(result.valid).toBe(false);
      expect(result.error).toContain('non-negative');
    });

    test('rejects x2 <= x1 (zero width)', () => {
      const bbox: BBox = { x1: 100, y1: 20, x2: 100, y2: 200 };
      const result = validateBbox(bbox, 612, 792);

      expect(result.valid).toBe(false);
      expect(result.error).toContain('Invalid width');
    });

    test('rejects x2 < x1 (negative width)', () => {
      const bbox: BBox = { x1: 100, y1: 20, x2: 50, y2: 200 };
      const result = validateBbox(bbox, 612, 792);

      expect(result.valid).toBe(false);
      expect(result.error).toContain('Invalid width');
    });

    test('rejects y2 <= y1 (zero height)', () => {
      const bbox: BBox = { x1: 10, y1: 200, x2: 100, y2: 200 };
      const result = validateBbox(bbox, 612, 792);

      expect(result.valid).toBe(false);
      expect(result.error).toContain('Invalid height');
    });

    test('rejects y2 < y1 (negative height)', () => {
      const bbox: BBox = { x1: 10, y1: 200, x2: 100, y2: 100 };
      const result = validateBbox(bbox, 612, 792);

      expect(result.valid).toBe(false);
      expect(result.error).toContain('Invalid height');
    });

    test('rejects bbox starting outside image (x)', () => {
      const bbox: BBox = { x1: 700, y1: 20, x2: 800, y2: 200 };
      const result = validateBbox(bbox, 612, 792);

      expect(result.valid).toBe(false);
      expect(result.error).toContain('outside image bounds');
    });

    test('rejects bbox starting outside image (y)', () => {
      const bbox: BBox = { x1: 10, y1: 800, x2: 100, y2: 900 };
      const result = validateBbox(bbox, 612, 792);

      expect(result.valid).toBe(false);
      expect(result.error).toContain('outside image bounds');
    });

    test('rejects bbox extending outside image (x)', () => {
      const bbox: BBox = { x1: 10, y1: 20, x2: 700, y2: 200 };
      const result = validateBbox(bbox, 612, 792);

      expect(result.valid).toBe(false);
      expect(result.error).toContain('outside image bounds');
    });

    test('rejects bbox extending outside image (y)', () => {
      const bbox: BBox = { x1: 10, y1: 20, x2: 100, y2: 800 };
      const result = validateBbox(bbox, 612, 792);

      expect(result.valid).toBe(false);
      expect(result.error).toContain('outside image bounds');
    });

    test('rejects invalid image width', () => {
      const bbox: BBox = { x1: 10, y1: 20, x2: 100, y2: 200 };
      const result = validateBbox(bbox, 0, 792);

      expect(result.valid).toBe(false);
      expect(result.error).toContain('Image dimensions must be positive');
    });

    test('rejects invalid image height', () => {
      const bbox: BBox = { x1: 10, y1: 20, x2: 100, y2: 200 };
      const result = validateBbox(bbox, 612, -1);

      expect(result.valid).toBe(false);
      expect(result.error).toContain('Image dimensions must be positive');
    });
  });
});

// ============================================================================
// ensureMinimumSize Tests
// ============================================================================

describe('ensureMinimumSize', () => {
  test('expands tiny bbox to minimum size', () => {
    const bbox: ScaledBBox = { x1: 100, y1: 100, x2: 102, y2: 103, width: 2, height: 3 };
    const result = ensureMinimumSize(bbox, 10);

    expect(result.width).toBe(10);
    expect(result.height).toBe(10);
  });

  test('maintains center point when expanding', () => {
    const bbox: ScaledBBox = { x1: 100, y1: 100, x2: 102, y2: 103, width: 2, height: 3 };
    const originalCenterX = (bbox.x1 + bbox.x2) / 2;
    const originalCenterY = (bbox.y1 + bbox.y2) / 2;

    const result = ensureMinimumSize(bbox, 10);
    const newCenterX = (result.x1 + result.x2) / 2;
    const newCenterY = (result.y1 + result.y2) / 2;

    expect(newCenterX).toBeCloseTo(originalCenterX, 5);
    expect(newCenterY).toBeCloseTo(originalCenterY, 5);
  });

  test('leaves large bbox unchanged', () => {
    const bbox: ScaledBBox = { x1: 0, y1: 0, x2: 100, y2: 100, width: 100, height: 100 };
    const result = ensureMinimumSize(bbox, 10);

    expect(result).toEqual(bbox);
  });

  test('expands only width if height is sufficient', () => {
    const bbox: ScaledBBox = { x1: 100, y1: 100, x2: 102, y2: 150, width: 2, height: 50 };
    const result = ensureMinimumSize(bbox, 10);

    expect(result.width).toBe(10);
    expect(result.height).toBe(50); // unchanged
  });

  test('expands only height if width is sufficient', () => {
    const bbox: ScaledBBox = { x1: 100, y1: 100, x2: 150, y2: 102, width: 50, height: 2 };
    const result = ensureMinimumSize(bbox, 10);

    expect(result.width).toBe(50); // unchanged
    expect(result.height).toBe(10);
  });

  test('handles zero minimum size (no change)', () => {
    const bbox: ScaledBBox = { x1: 100, y1: 100, x2: 102, y2: 103, width: 2, height: 3 };
    const result = ensureMinimumSize(bbox, 0);

    expect(result).toEqual(bbox);
  });

  test('handles negative minimum size (no change)', () => {
    const bbox: ScaledBBox = { x1: 100, y1: 100, x2: 102, y2: 103, width: 2, height: 3 };
    const result = ensureMinimumSize(bbox, -5);

    expect(result).toEqual(bbox);
  });

  test('uses default minimum size when not specified', () => {
    const bbox: ScaledBBox = { x1: 100, y1: 100, x2: 102, y2: 103, width: 2, height: 3 };
    const result = ensureMinimumSize(bbox);

    // Default is 10px
    expect(result.width).toBe(10);
    expect(result.height).toBe(10);
  });

  test('handles bbox at origin', () => {
    const bbox: ScaledBBox = { x1: 0, y1: 0, x2: 2, y2: 3, width: 2, height: 3 };
    const result = ensureMinimumSize(bbox, 10);

    // Center at (1, 1.5), expanded to 10x10
    expect(result.x1).toBeCloseTo(-4, 0);
    expect(result.y1).toBeCloseTo(-3.5, 1);
    expect(result.x2).toBeCloseTo(6, 0);
    expect(result.y2).toBeCloseTo(6.5, 1);
  });

  test('handles very large minimum size', () => {
    const bbox: ScaledBBox = { x1: 100, y1: 100, x2: 110, y2: 120, width: 10, height: 20 };
    const result = ensureMinimumSize(bbox, 100);

    expect(result.width).toBe(100);
    expect(result.height).toBe(100);
  });
});

// ============================================================================
// Helper Functions Tests
// ============================================================================

describe('calculateBboxArea', () => {
  test('calculates area for square bbox', () => {
    const bbox: BBox = { x1: 0, y1: 0, x2: 100, y2: 100 };
    expect(calculateBboxArea(bbox)).toBe(10000);
  });

  test('calculates area for rectangular bbox', () => {
    const bbox: BBox = { x1: 0, y1: 0, x2: 200, y2: 50 };
    expect(calculateBboxArea(bbox)).toBe(10000);
  });

  test('calculates area for tiny bbox', () => {
    const bbox: BBox = { x1: 10, y1: 10, x2: 11, y2: 11 };
    expect(calculateBboxArea(bbox)).toBe(1);
  });

  test('handles bbox not at origin', () => {
    const bbox: BBox = { x1: 50, y1: 50, x2: 150, y2: 100 };
    expect(calculateBboxArea(bbox)).toBe(5000); // 100 * 50
  });

  test('handles fractional coordinates', () => {
    const bbox: BBox = { x1: 10.5, y1: 20.5, x2: 30.5, y2: 40.5 };
    expect(calculateBboxArea(bbox)).toBe(400); // 20 * 20
  });
});

describe('isPointInBbox', () => {
  const bbox: BBox = { x1: 10, y1: 20, x2: 100, y2: 200 };

  test('returns true for point inside bbox', () => {
    expect(isPointInBbox(bbox, 50, 100)).toBe(true);
  });

  test('returns true for point at top-left corner', () => {
    expect(isPointInBbox(bbox, 10, 20)).toBe(true);
  });

  test('returns true for point at bottom-right corner', () => {
    expect(isPointInBbox(bbox, 100, 200)).toBe(true);
  });

  test('returns true for point on left edge', () => {
    expect(isPointInBbox(bbox, 10, 100)).toBe(true);
  });

  test('returns true for point on right edge', () => {
    expect(isPointInBbox(bbox, 100, 100)).toBe(true);
  });

  test('returns true for point on top edge', () => {
    expect(isPointInBbox(bbox, 50, 20)).toBe(true);
  });

  test('returns true for point on bottom edge', () => {
    expect(isPointInBbox(bbox, 50, 200)).toBe(true);
  });

  test('returns false for point left of bbox', () => {
    expect(isPointInBbox(bbox, 5, 100)).toBe(false);
  });

  test('returns false for point right of bbox', () => {
    expect(isPointInBbox(bbox, 105, 100)).toBe(false);
  });

  test('returns false for point above bbox', () => {
    expect(isPointInBbox(bbox, 50, 15)).toBe(false);
  });

  test('returns false for point below bbox', () => {
    expect(isPointInBbox(bbox, 50, 205)).toBe(false);
  });
});

describe('calculateIntersectionArea', () => {
  test('calculates intersection for overlapping bboxes', () => {
    const bbox1: BBox = { x1: 0, y1: 0, x2: 100, y2: 100 };
    const bbox2: BBox = { x1: 50, y1: 50, x2: 150, y2: 150 };
    expect(calculateIntersectionArea(bbox1, bbox2)).toBe(2500); // 50x50
  });

  test('returns 0 for non-overlapping bboxes', () => {
    const bbox1: BBox = { x1: 0, y1: 0, x2: 100, y2: 100 };
    const bbox2: BBox = { x1: 200, y1: 200, x2: 300, y2: 300 };
    expect(calculateIntersectionArea(bbox1, bbox2)).toBe(0);
  });

  test('calculates full area when one bbox contains another', () => {
    const bbox1: BBox = { x1: 0, y1: 0, x2: 100, y2: 100 };
    const bbox2: BBox = { x1: 25, y1: 25, x2: 75, y2: 75 };
    expect(calculateIntersectionArea(bbox1, bbox2)).toBe(2500); // 50x50 (bbox2 area)
  });

  test('returns 0 for edge-touching bboxes', () => {
    const bbox1: BBox = { x1: 0, y1: 0, x2: 100, y2: 100 };
    const bbox2: BBox = { x1: 100, y1: 0, x2: 200, y2: 100 };
    expect(calculateIntersectionArea(bbox1, bbox2)).toBe(0);
  });

  test('handles partial overlap (horizontal)', () => {
    const bbox1: BBox = { x1: 0, y1: 0, x2: 100, y2: 50 };
    const bbox2: BBox = { x1: 50, y1: 0, x2: 150, y2: 50 };
    expect(calculateIntersectionArea(bbox1, bbox2)).toBe(2500); // 50x50
  });

  test('handles partial overlap (vertical)', () => {
    const bbox1: BBox = { x1: 0, y1: 0, x2: 50, y2: 100 };
    const bbox2: BBox = { x1: 0, y1: 50, x2: 50, y2: 150 };
    expect(calculateIntersectionArea(bbox1, bbox2)).toBe(2500); // 50x50
  });

  test('handles identical bboxes', () => {
    const bbox1: BBox = { x1: 0, y1: 0, x2: 100, y2: 100 };
    const bbox2: BBox = { x1: 0, y1: 0, x2: 100, y2: 100 };
    expect(calculateIntersectionArea(bbox1, bbox2)).toBe(10000); // full area
  });
});

describe('calculateIoU', () => {
  test('returns 1.0 for identical bboxes', () => {
    const bbox1: BBox = { x1: 0, y1: 0, x2: 100, y2: 100 };
    const bbox2: BBox = { x1: 0, y1: 0, x2: 100, y2: 100 };
    expect(calculateIoU(bbox1, bbox2)).toBe(1.0);
  });

  test('returns 0 for non-overlapping bboxes', () => {
    const bbox1: BBox = { x1: 0, y1: 0, x2: 100, y2: 100 };
    const bbox2: BBox = { x1: 200, y1: 200, x2: 300, y2: 300 };
    expect(calculateIoU(bbox1, bbox2)).toBe(0);
  });

  test('calculates IoU for 50% overlap', () => {
    const bbox1: BBox = { x1: 0, y1: 0, x2: 100, y2: 100 };
    const bbox2: BBox = { x1: 50, y1: 50, x2: 150, y2: 150 };
    // Intersection: 2500, Union: 10000 + 10000 - 2500 = 17500
    expect(calculateIoU(bbox1, bbox2)).toBeCloseTo(2500 / 17500, 5);
  });

  test('calculates IoU when one bbox contains another', () => {
    const bbox1: BBox = { x1: 0, y1: 0, x2: 100, y2: 100 };
    const bbox2: BBox = { x1: 25, y1: 25, x2: 75, y2: 75 };
    // Intersection: 2500, Union: 10000
    expect(calculateIoU(bbox1, bbox2)).toBeCloseTo(0.25, 5);
  });

  test('returns 0 for edge-touching bboxes', () => {
    const bbox1: BBox = { x1: 0, y1: 0, x2: 100, y2: 100 };
    const bbox2: BBox = { x1: 100, y1: 0, x2: 200, y2: 100 };
    expect(calculateIoU(bbox1, bbox2)).toBe(0);
  });

  test('handles tiny overlap', () => {
    const bbox1: BBox = { x1: 0, y1: 0, x2: 100, y2: 100 };
    const bbox2: BBox = { x1: 99, y1: 99, x2: 199, y2: 199 };
    // Intersection: 1, Union: 10000 + 10000 - 1 = 19999
    expect(calculateIoU(bbox1, bbox2)).toBeCloseTo(1 / 19999, 5);
  });

  test('handles large overlap', () => {
    const bbox1: BBox = { x1: 0, y1: 0, x2: 100, y2: 100 };
    const bbox2: BBox = { x1: 10, y1: 10, x2: 110, y2: 110 };
    // Intersection: 90x90 = 8100
    // Union: 10000 + 10000 - 8100 = 11900
    expect(calculateIoU(bbox1, bbox2)).toBeCloseTo(8100 / 11900, 5);
  });
});

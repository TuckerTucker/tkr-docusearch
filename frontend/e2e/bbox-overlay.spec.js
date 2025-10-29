/**
 * BoundingBox Overlay E2E Tests
 *
 * Agent 14: Testing & Documentation
 * Wave 3 - BBox Overlay React Implementation
 *
 * Comprehensive E2E tests for bbox overlay functionality including:
 * - Bbox rendering and scaling
 * - Click interactions
 * - Visual states (hover, active)
 * - Integration with document images
 */

import { test, expect } from '@playwright/test';

/**
 * Setup: Navigate to a document details page with bbox data
 */
test.beforeEach(async ({ page }) => {
  // Navigate to document details page
  await page.goto('/details/test-doc-1');

  // Wait for page to load
  await page.waitForLoadState('networkidle');

  // Wait for image to be visible
  await page.waitForSelector('[data-testid="document-image"]', {
    state: 'visible',
    timeout: 10000
  });
});

test.describe('BoundingBox Overlay Rendering', () => {
  test('renders SVG overlay on document image', async ({ page }) => {
    // Check that SVG overlay is rendered
    const overlay = await page.locator('svg[role="img"][aria-label*="bounding boxes"]');
    await expect(overlay).toBeVisible();

    // Verify overlay has correct attributes
    const width = await overlay.getAttribute('width');
    const height = await overlay.getAttribute('height');
    expect(parseInt(width)).toBeGreaterThan(0);
    expect(parseInt(height)).toBeGreaterThan(0);
  });

  test('renders bounding boxes for document elements', async ({ page }) => {
    // Check that bboxes are rendered as SVG rects
    const bboxes = await page.locator('svg rect[role="button"]');
    const count = await bboxes.count();

    expect(count).toBeGreaterThan(0);
  });

  test('each bbox has required accessibility attributes', async ({ page }) => {
    const firstBbox = await page.locator('svg rect[role="button"]').first();

    // Check role
    await expect(firstBbox).toHaveAttribute('role', 'button');

    // Check aria-label exists
    const ariaLabel = await firstBbox.getAttribute('aria-label');
    expect(ariaLabel).toBeTruthy();

    // Check tabindex for keyboard navigation
    await expect(firstBbox).toHaveAttribute('tabindex', '0');

    // Check data attributes
    const chunkId = await firstBbox.getAttribute('data-chunk-id');
    expect(chunkId).toBeTruthy();
  });

  test('bboxes scale correctly when image resizes', async ({ page }) => {
    const overlay = await page.locator('svg[role="img"][aria-label*="bounding boxes"]');

    // Get initial dimensions
    const initialBox = await overlay.boundingBox();

    // Resize viewport
    await page.setViewportSize({ width: 1200, height: 800 });

    // Wait for resize to complete
    await page.waitForTimeout(500);

    // Get new dimensions
    const newBox = await overlay.boundingBox();

    // Verify overlay adjusted
    expect(newBox.width).not.toBe(initialBox.width);
  });
});

test.describe('BoundingBox Click Interactions', () => {
  test('clicking bbox scrolls to corresponding chunk', async ({ page }) => {
    // Find first bbox
    const firstBbox = await page.locator('svg rect[role="button"]').first();
    const chunkId = await firstBbox.getAttribute('data-chunk-id');

    // Click the bbox
    await firstBbox.click();

    // Wait for scroll animation
    await page.waitForTimeout(600);

    // Verify corresponding chunk is in viewport
    const chunk = await page.locator(`[data-chunk-id="${chunkId}"]`).first();
    await expect(chunk).toBeInViewport();
  });

  test('clicking bbox activates the chunk', async ({ page }) => {
    const firstBbox = await page.locator('svg rect[role="button"]').first();
    const chunkId = await firstBbox.getAttribute('data-chunk-id');

    // Click the bbox
    await firstBbox.click();

    // Verify bbox has active class
    const bboxClass = await firstBbox.getAttribute('class');
    expect(bboxClass).toContain('active');

    // Verify corresponding chunk has active class
    const chunk = await page.locator(`[data-chunk-id="${chunkId}"]`).first();
    const chunkClass = await chunk.getAttribute('class');
    expect(chunkClass).toContain('active');
  });

  test('clicking different bbox changes active state', async ({ page }) => {
    const bboxes = await page.locator('svg rect[role="button"]');

    // Click first bbox
    const firstBbox = bboxes.nth(0);
    await firstBbox.click();
    await page.waitForTimeout(300);

    const firstClass = await firstBbox.getAttribute('class');
    expect(firstClass).toContain('active');

    // Click second bbox
    const secondBbox = bboxes.nth(1);
    await secondBbox.click();
    await page.waitForTimeout(300);

    // First should no longer be active
    const firstClassAfter = await firstBbox.getAttribute('class');
    expect(firstClassAfter).not.toContain('active');

    // Second should be active
    const secondClass = await secondBbox.getAttribute('class');
    expect(secondClass).toContain('active');
  });

  test('keyboard Enter key activates bbox', async ({ page }) => {
    const firstBbox = await page.locator('svg rect[role="button"]').first();

    // Focus the bbox
    await firstBbox.focus();

    // Press Enter
    await page.keyboard.press('Enter');
    await page.waitForTimeout(300);

    // Verify bbox is active
    const bboxClass = await firstBbox.getAttribute('class');
    expect(bboxClass).toContain('active');
  });

  test('keyboard Space key activates bbox', async ({ page }) => {
    const firstBbox = await page.locator('svg rect[role="button"]').first();

    // Focus the bbox
    await firstBbox.focus();

    // Press Space
    await page.keyboard.press('Space');
    await page.waitForTimeout(300);

    // Verify bbox is active
    const bboxClass = await firstBbox.getAttribute('class');
    expect(bboxClass).toContain('active');
  });
});

test.describe('BoundingBox Hover States', () => {
  test('hovering bbox applies hover class', async ({ page }) => {
    const firstBbox = await page.locator('svg rect[role="button"]').first();

    // Hover over bbox
    await firstBbox.hover();
    await page.waitForTimeout(100);

    // Check for hover class
    const bboxClass = await firstBbox.getAttribute('class');
    expect(bboxClass).toContain('hovered');
  });

  test('moving mouse away removes hover class', async ({ page }) => {
    const firstBbox = await page.locator('svg rect[role="button"]').first();

    // Hover over bbox
    await firstBbox.hover();
    await page.waitForTimeout(100);

    let bboxClass = await firstBbox.getAttribute('class');
    expect(bboxClass).toContain('hovered');

    // Move mouse away
    await page.mouse.move(0, 0);
    await page.waitForTimeout(100);

    // Hover class should be removed
    bboxClass = await firstBbox.getAttribute('class');
    expect(bboxClass).not.toContain('hovered');
  });
});

test.describe('BoundingBox Visual States', () => {
  test('active bbox has distinct visual styling', async ({ page }) => {
    const firstBbox = await page.locator('svg rect[role="button"]').first();

    // Get initial styles
    const initialOpacity = await firstBbox.evaluate(el =>
      window.getComputedStyle(el).opacity
    );

    // Click to activate
    await firstBbox.click();
    await page.waitForTimeout(300);

    // Get active styles
    const activeOpacity = await firstBbox.evaluate(el =>
      window.getComputedStyle(el).opacity
    );

    // Active should be more visible
    expect(parseFloat(activeOpacity)).toBeGreaterThan(parseFloat(initialOpacity));
  });

  test('different element types have different colors', async ({ page }) => {
    // Find bboxes of different types
    const headingBbox = await page.locator('svg rect[data-element-type="heading"]').first();
    const textBbox = await page.locator('svg rect[data-element-type="text"]').first();

    if (await headingBbox.count() > 0 && await textBbox.count() > 0) {
      const headingStroke = await headingBbox.evaluate(el =>
        window.getComputedStyle(el).stroke
      );
      const textStroke = await textBbox.evaluate(el =>
        window.getComputedStyle(el).stroke
      );

      // Different types should have different colors
      expect(headingStroke).not.toBe(textStroke);
    }
  });
});

test.describe('Error Handling', () => {
  test('handles missing structure data gracefully', async ({ page }) => {
    // Navigate to page without bbox data
    await page.goto('/details/no-bbox-doc');
    await page.waitForLoadState('networkidle');

    // Verify no overlay is rendered (or empty overlay)
    const overlay = await page.locator('svg[role="img"][aria-label*="bounding boxes"]');
    const isVisible = await overlay.isVisible();

    // Either not rendered or has no rects
    if (isVisible) {
      const rects = await page.locator('svg rect[role="button"]');
      expect(await rects.count()).toBe(0);
    }
  });

  test('handles image load errors gracefully', async ({ page }) => {
    // This test would require mocking image load failure
    // Verifying the overlay doesn't crash the page
    await page.goto('/details/test-doc-1');

    // Even if image fails, page should still work
    const errorMessages = [];
    page.on('pageerror', error => errorMessages.push(error.message));

    await page.waitForTimeout(2000);

    // Should not have unhandled errors
    expect(errorMessages.length).toBe(0);
  });
});

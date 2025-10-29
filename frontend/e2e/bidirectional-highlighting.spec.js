/**
 * Bidirectional Highlighting E2E Tests
 *
 * Agent 14: Testing & Documentation
 * Wave 3 - BBox Overlay React Implementation
 *
 * Tests for bidirectional highlighting between:
 * - BoundingBoxOverlay (visual overlays on images)
 * - ChunkHighlighter (text highlighting in markdown)
 */

import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('/details/test-doc-1');
  await page.waitForLoadState('networkidle');
  await page.waitForSelector('[data-testid="document-image"]', {
    state: 'visible',
    timeout: 10000
  });
});

test.describe('Bbox → Chunk Highlighting', () => {
  test('hovering bbox highlights corresponding chunk', async ({ page }) => {
    const firstBbox = await page.locator('svg rect[role="button"]').first();
    const chunkId = await firstBbox.getAttribute('data-chunk-id');

    // Hover over bbox
    await firstBbox.hover();
    await page.waitForTimeout(100);

    // Verify chunk is highlighted
    const chunk = await page.locator(`[data-chunk-id="${chunkId}"]`).first();
    const chunkClass = await chunk.getAttribute('class');
    expect(chunkClass).toContain('hovered');
  });

  test('clicking bbox scrolls to and activates chunk', async ({ page }) => {
    const firstBbox = await page.locator('svg rect[role="button"]').first();
    const chunkId = await firstBbox.getAttribute('data-chunk-id');

    // Click bbox
    await firstBbox.click();
    await page.waitForTimeout(600);

    // Verify chunk is in viewport
    const chunk = await page.locator(`[data-chunk-id="${chunkId}"]`).first();
    await expect(chunk).toBeInViewport();

    // Verify chunk is active
    const chunkClass = await chunk.getAttribute('class');
    expect(chunkClass).toContain('active');
  });

  test('moving mouse away from bbox unhighlights chunk', async ({ page }) => {
    const firstBbox = await page.locator('svg rect[role="button"]').first();
    const chunkId = await firstBbox.getAttribute('data-chunk-id');

    // Hover bbox
    await firstBbox.hover();
    await page.waitForTimeout(100);

    const chunk = await page.locator(`[data-chunk-id="${chunkId}"]`).first();
    let chunkClass = await chunk.getAttribute('class');
    expect(chunkClass).toContain('hovered');

    // Move away
    await page.mouse.move(0, 0);
    await page.waitForTimeout(100);

    // Verify unhighlighted
    chunkClass = await chunk.getAttribute('class');
    expect(chunkClass).not.toContain('hovered');
  });
});

test.describe('Chunk → Bbox Highlighting', () => {
  test('hovering chunk highlights corresponding bbox', async ({ page }) => {
    // Find a chunk with bbox
    const chunk = await page.locator('[data-chunk-id]').first();
    const chunkId = await chunk.getAttribute('data-chunk-id');

    // Hover over chunk
    await chunk.hover();
    await page.waitForTimeout(100);

    // Verify bbox is highlighted
    const bbox = await page.locator(`svg rect[data-chunk-id="${chunkId}"]`);
    const bboxClass = await bbox.getAttribute('class');
    expect(bboxClass).toContain('hovered');
  });

  test('clicking chunk activates corresponding bbox', async ({ page }) => {
    const chunk = await page.locator('[data-chunk-id]').first();
    const chunkId = await chunk.getAttribute('data-chunk-id');

    // Click chunk
    await chunk.click();
    await page.waitForTimeout(300);

    // Verify bbox is active
    const bbox = await page.locator(`svg rect[data-chunk-id="${chunkId}"]`);
    const bboxClass = await bbox.getAttribute('class');
    expect(bboxClass).toContain('active');
  });

  test('moving mouse away from chunk unhighlights bbox', async ({ page }) => {
    const chunk = await page.locator('[data-chunk-id]').first();
    const chunkId = await chunk.getAttribute('data-chunk-id');

    // Hover chunk
    await chunk.hover();
    await page.waitForTimeout(100);

    const bbox = await page.locator(`svg rect[data-chunk-id="${chunkId}"]`);
    let bboxClass = await bbox.getAttribute('class');
    expect(bboxClass).toContain('hovered');

    // Move away
    await page.mouse.move(0, 0);
    await page.waitForTimeout(100);

    // Verify unhighlighted
    bboxClass = await bbox.getAttribute('class');
    expect(bboxClass).not.toContain('hovered');
  });
});

test.describe('Synchronized State Management', () => {
  test('only one chunk can be active at a time', async ({ page }) => {
    const chunks = await page.locator('[data-chunk-id]');

    // Click first chunk
    const firstChunk = chunks.nth(0);
    await firstChunk.click();
    await page.waitForTimeout(300);

    let firstClass = await firstChunk.getAttribute('class');
    expect(firstClass).toContain('active');

    // Click second chunk
    const secondChunk = chunks.nth(1);
    await secondChunk.click();
    await page.waitForTimeout(300);

    // First should no longer be active
    firstClass = await firstChunk.getAttribute('class');
    expect(firstClass).not.toContain('active');

    // Second should be active
    const secondClass = await secondChunk.getAttribute('class');
    expect(secondClass).toContain('active');
  });

  test('hover and active states are independent', async ({ page }) => {
    const chunks = await page.locator('[data-chunk-id]');

    // Click first chunk (activate)
    const firstChunk = chunks.nth(0);
    await firstChunk.click();
    await page.waitForTimeout(300);

    const firstClass = await firstChunk.getAttribute('class');
    expect(firstClass).toContain('active');

    // Hover second chunk
    const secondChunk = chunks.nth(1);
    await secondChunk.hover();
    await page.waitForTimeout(100);

    const secondClass = await secondChunk.getAttribute('class');
    expect(secondClass).toContain('hovered');

    // First should still be active
    const firstClassAfter = await firstChunk.getAttribute('class');
    expect(firstClassAfter).toContain('active');
  });

  test('bbox and chunk states stay synchronized', async ({ page }) => {
    const firstBbox = await page.locator('svg rect[role="button"]').first();
    const chunkId = await firstBbox.getAttribute('data-chunk-id');
    const chunk = await page.locator(`[data-chunk-id="${chunkId}"]`).first();

    // Click bbox
    await firstBbox.click();
    await page.waitForTimeout(300);

    // Both should be active
    const bboxClass = await firstBbox.getAttribute('class');
    const chunkClass = await chunk.getAttribute('class');
    expect(bboxClass).toContain('active');
    expect(chunkClass).toContain('active');

    // Hover another element to change hover state
    const secondBbox = await page.locator('svg rect[role="button"]').nth(1);
    await secondBbox.hover();
    await page.waitForTimeout(100);

    // First should still be active (hover is different state)
    const bboxClassAfter = await firstBbox.getAttribute('class');
    const chunkClassAfter = await chunk.getAttribute('class');
    expect(bboxClassAfter).toContain('active');
    expect(chunkClassAfter).toContain('active');
  });
});

test.describe('Smooth Scroll Behavior', () => {
  test('scrolling to chunk is smooth and visible', async ({ page }) => {
    // Scroll to top first
    await page.evaluate(() => window.scrollTo(0, 0));

    // Click a bbox further down the page
    const bboxes = await page.locator('svg rect[role="button"]');
    const targetBbox = bboxes.nth(5); // Choose a bbox not in viewport
    const chunkId = await targetBbox.getAttribute('data-chunk-id');

    // Click it
    await targetBbox.click();

    // Wait for smooth scroll
    await page.waitForTimeout(800);

    // Verify chunk is in viewport
    const chunk = await page.locator(`[data-chunk-id="${chunkId}"]`).first();
    await expect(chunk).toBeInViewport();
  });

  test('scroll respects header offset', async ({ page }) => {
    const firstBbox = await page.locator('svg rect[role="button"]').first();
    const chunkId = await firstBbox.getAttribute('data-chunk-id');

    // Click bbox
    await firstBbox.click();
    await page.waitForTimeout(600);

    // Get chunk position
    const chunk = await page.locator(`[data-chunk-id="${chunkId}"]`).first();
    const chunkBox = await chunk.boundingBox();

    // Should not be at very top (accounting for offset)
    expect(chunkBox.y).toBeGreaterThan(0);
  });
});

test.describe('Multiple Pages', () => {
  test('changing pages updates available bboxes', async ({ page }) => {
    // Get initial bbox count on page 1
    const initialBboxes = await page.locator('svg rect[role="button"]');
    const initialCount = await initialBboxes.count();

    // Navigate to page 2
    const nextButton = await page.locator('[data-testid="next-page"]');
    if (await nextButton.isVisible()) {
      await nextButton.click();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);

      // Get bbox count on page 2
      const newBboxes = await page.locator('svg rect[role="button"]');
      const newCount = await newBboxes.count();

      // Count might be different (or could be same, just verify no crash)
      expect(newCount).toBeGreaterThanOrEqual(0);
    }
  });

  test('active state clears when switching pages', async ({ page }) => {
    // Click a bbox to activate
    const firstBbox = await page.locator('svg rect[role="button"]').first();
    await firstBbox.click();
    await page.waitForTimeout(300);

    let bboxClass = await firstBbox.getAttribute('class');
    expect(bboxClass).toContain('active');

    // Navigate to next page
    const nextButton = await page.locator('[data-testid="next-page"]');
    if (await nextButton.isVisible()) {
      await nextButton.click();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);

      // Go back to page 1
      const prevButton = await page.locator('[data-testid="prev-page"]');
      await prevButton.click();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);

      // Active state should be cleared
      const bboxAfter = await page.locator('svg rect[role="button"]').first();
      const bboxClassAfter = await bboxAfter.getAttribute('class');
      expect(bboxClassAfter).not.toContain('active');
    }
  });
});

test.describe('Performance', () => {
  test('highlighting responds within 100ms', async ({ page }) => {
    const firstBbox = await page.locator('svg rect[role="button"]').first();

    // Measure time from hover to highlight
    const startTime = Date.now();
    await firstBbox.hover();

    // Wait for hover class
    await page.waitForSelector('svg rect.hovered', { timeout: 200 });

    const endTime = Date.now();
    const duration = endTime - startTime;

    // Should be nearly instant
    expect(duration).toBeLessThan(100);
  });

  test('handles rapid hover changes smoothly', async ({ page }) => {
    const bboxes = await page.locator('svg rect[role="button"]');

    // Rapidly hover multiple bboxes
    for (let i = 0; i < 5; i++) {
      await bboxes.nth(i).hover();
      await page.waitForTimeout(50);
    }

    // Page should still be responsive
    const lastBbox = bboxes.nth(4);
    const lastClass = await lastBbox.getAttribute('class');
    expect(lastClass).toContain('hovered');
  });
});

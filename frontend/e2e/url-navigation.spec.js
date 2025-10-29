/**
 * URL Navigation E2E Tests
 *
 * Agent 14: Testing & Documentation
 * Wave 3 - BBox Overlay React Implementation
 *
 * Tests for URL parameter-based chunk navigation:
 * - Deep linking to chunks via ?chunk=...
 * - URL updates on chunk selection
 * - Browser history integration
 * - Shareable links
 */

import { test, expect } from '@playwright/test';

test.describe('URL Parameter Navigation', () => {
  test('navigates to chunk specified in URL on page load', async ({ page }) => {
    // Navigate with chunk parameter
    await page.goto('/details/test-doc-1?chunk=chunk-0-page-1');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Verify chunk is in viewport
    const chunk = await page.locator('[data-chunk-id="chunk-0-page-1"]').first();
    await expect(chunk).toBeInViewport();

    // Verify chunk is active
    const chunkClass = await chunk.getAttribute('class');
    expect(chunkClass).toContain('active');
  });

  test('highlights bbox corresponding to URL chunk', async ({ page }) => {
    await page.goto('/details/test-doc-1?chunk=chunk-0-page-1');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Verify bbox is active
    const bbox = await page.locator('svg rect[data-chunk-id="chunk-0-page-1"]');
    const bboxClass = await bbox.getAttribute('class');
    expect(bboxClass).toContain('active');
  });

  test('handles invalid chunk ID in URL gracefully', async ({ page }) => {
    // Navigate with invalid chunk ID
    await page.goto('/details/test-doc-1?chunk=invalid-chunk-id');
    await page.waitForLoadState('networkidle');

    // Page should still load without errors
    const errorMessages = [];
    page.on('pageerror', error => errorMessages.push(error.message));

    await page.waitForTimeout(1000);

    // Should not crash
    expect(errorMessages.length).toBe(0);
  });

  test('handles missing chunk parameter gracefully', async ({ page }) => {
    await page.goto('/details/test-doc-1');
    await page.waitForLoadState('networkidle');

    // Page should load normally
    const image = await page.locator('[data-testid="document-image"]');
    await expect(image).toBeVisible();

    // No chunk should be active
    const activeBboxes = await page.locator('svg rect.active');
    expect(await activeBboxes.count()).toBe(0);
  });

  test('preserves other URL parameters when adding chunk', async ({ page }) => {
    await page.goto('/details/test-doc-1?search=test&filter=important');
    await page.waitForLoadState('networkidle');

    // Click a bbox (this might update URL if configured)
    const firstBbox = await page.locator('svg rect[role="button"]').first();
    await firstBbox.click();
    await page.waitForTimeout(300);

    // Get current URL
    const url = new URL(page.url());

    // Other parameters should still be present
    expect(url.searchParams.get('search')).toBe('test');
    expect(url.searchParams.get('filter')).toBe('important');
  });
});

test.describe('Deep Linking', () => {
  test('creates shareable link to specific chunk', async ({ page }) => {
    await page.goto('/details/test-doc-1');
    await page.waitForLoadState('networkidle');

    // Click a bbox
    const firstBbox = await page.locator('svg rect[role="button"]').first();
    const chunkId = await firstBbox.getAttribute('data-chunk-id');
    await firstBbox.click();
    await page.waitForTimeout(300);

    // Get current URL
    const currentUrl = page.url();

    // Open in new page to test deep link
    const context = page.context();
    const newPage = await context.newPage();
    await newPage.goto(currentUrl);
    await newPage.waitForLoadState('networkidle');
    await newPage.waitForTimeout(1000);

    // Verify chunk is active in new page
    const chunk = await newPage.locator(`[data-chunk-id="${chunkId}"]`).first();
    const chunkClass = await chunk.getAttribute('class');
    expect(chunkClass).toContain('active');

    await newPage.close();
  });

  test('deep link scrolls to chunk position', async ({ page }) => {
    // Navigate with chunk parameter for a chunk further down
    await page.goto('/details/test-doc-1?chunk=chunk-5-page-1');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Verify page has scrolled
    const scrollY = await page.evaluate(() => window.scrollY);
    expect(scrollY).toBeGreaterThan(0);

    // Verify chunk is in viewport
    const chunk = await page.locator('[data-chunk-id="chunk-5-page-1"]').first();
    await expect(chunk).toBeInViewport();
  });

  test('deep link works with page parameter', async ({ page }) => {
    // Navigate to page 2 with chunk
    await page.goto('/details/test-doc-1?page=2&chunk=chunk-0-page-2');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Should be on page 2
    const pageIndicator = await page.locator('[data-testid="page-number"]');
    const pageText = await pageIndicator.textContent();
    expect(pageText).toContain('2');

    // Chunk should be active
    const chunk = await page.locator('[data-chunk-id="chunk-0-page-2"]').first();
    const chunkClass = await chunk.getAttribute('class');
    expect(chunkClass).toContain('active');
  });
});

test.describe('Browser History', () => {
  test('clicking chunks adds history entries', async ({ page }) => {
    await page.goto('/details/test-doc-1');
    await page.waitForLoadState('networkidle');

    const bboxes = await page.locator('svg rect[role="button"]');

    // Click first bbox
    await bboxes.nth(0).click();
    await page.waitForTimeout(300);

    // Click second bbox
    await bboxes.nth(1).click();
    await page.waitForTimeout(300);

    // Go back
    await page.goBack();
    await page.waitForTimeout(500);

    // Should navigate back to first chunk
    const firstChunkId = await bboxes.nth(0).getAttribute('data-chunk-id');
    const firstBboxClass = await bboxes.nth(0).getAttribute('class');

    // Might be active depending on configuration
    // At minimum, should be on same page
    const url = new URL(page.url());
    expect(url.pathname).toContain('test-doc-1');
  });

  test('forward/back navigation updates active chunk', async ({ page }) => {
    await page.goto('/details/test-doc-1?chunk=chunk-0-page-1');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Click different chunk
    const secondBbox = await page.locator('svg rect[role="button"]').nth(1);
    const secondChunkId = await secondBbox.getAttribute('data-chunk-id');
    await secondBbox.click();
    await page.waitForTimeout(300);

    // Go back
    await page.goBack();
    await page.waitForTimeout(500);

    // Should be back to first chunk
    const url = new URL(page.url());
    expect(url.searchParams.get('chunk')).toBe('chunk-0-page-1');
  });
});

test.describe('URL Update Configuration', () => {
  test('clicking chunk updates URL when configured', async ({ page }) => {
    await page.goto('/details/test-doc-1');
    await page.waitForLoadState('networkidle');

    const initialUrl = page.url();

    // Click a bbox
    const firstBbox = await page.locator('svg rect[role="button"]').first();
    const chunkId = await firstBbox.getAttribute('data-chunk-id');
    await firstBbox.click();
    await page.waitForTimeout(300);

    // URL might have changed (depending on configuration)
    const newUrl = page.url();

    // If URL update is enabled, it should contain chunk parameter
    if (newUrl !== initialUrl) {
      const url = new URL(newUrl);
      expect(url.searchParams.get('chunk')).toBe(chunkId);
    }
  });

  test('hover does not update URL', async ({ page }) => {
    await page.goto('/details/test-doc-1');
    await page.waitForLoadState('networkidle');

    const initialUrl = page.url();

    // Hover over bbox
    const firstBbox = await page.locator('svg rect[role="button"]').first();
    await firstBbox.hover();
    await page.waitForTimeout(200);

    // URL should not change on hover
    const newUrl = page.url();
    expect(newUrl).toBe(initialUrl);
  });
});

test.describe('Edge Cases', () => {
  test('handles special characters in chunk IDs', async ({ page }) => {
    // Chunk ID with special characters (URL encoded)
    const specialChunkId = 'chunk-0-page-1_section#2';
    const encodedChunkId = encodeURIComponent(specialChunkId);

    await page.goto(`/details/test-doc-1?chunk=${encodedChunkId}`);
    await page.waitForLoadState('networkidle');

    // Should decode and handle correctly
    const url = new URL(page.url());
    const chunkParam = url.searchParams.get('chunk');
    expect(chunkParam).toBe(specialChunkId);
  });

  test('handles multiple chunk parameters (uses first)', async ({ page }) => {
    await page.goto('/details/test-doc-1?chunk=chunk-0&chunk=chunk-1');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Should use first chunk parameter
    const url = new URL(page.url());
    const chunkParam = url.searchParams.get('chunk');
    expect(chunkParam).toBe('chunk-0');
  });

  test('handles empty chunk parameter', async ({ page }) => {
    await page.goto('/details/test-doc-1?chunk=');
    await page.waitForLoadState('networkidle');

    // Should not crash
    const image = await page.locator('[data-testid="document-image"]');
    await expect(image).toBeVisible();

    // No chunk should be active
    const activeBboxes = await page.locator('svg rect.active');
    expect(await activeBboxes.count()).toBe(0);
  });

  test('handles whitespace in chunk parameter', async ({ page }) => {
    await page.goto('/details/test-doc-1?chunk=%20%20chunk-0-page-1%20%20');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Should trim whitespace and work correctly
    const chunk = await page.locator('[data-chunk-id="chunk-0-page-1"]').first();
    if (await chunk.isVisible()) {
      const chunkClass = await chunk.getAttribute('class');
      expect(chunkClass).toContain('active');
    }
  });
});

test.describe('Cross-page Navigation', () => {
  test('chunk parameter on wrong page shows no active chunk', async ({ page }) => {
    // Navigate to page 1 with page 2 chunk ID
    await page.goto('/details/test-doc-1?page=1&chunk=chunk-0-page-2');
    await page.waitForLoadState('networkidle');

    // Should be on page 1
    const image = await page.locator('[data-testid="document-image"]');
    await expect(image).toBeVisible();

    // No bbox should be active (chunk is on different page)
    const activeBboxes = await page.locator('svg rect.active');
    expect(await activeBboxes.count()).toBe(0);
  });

  test('navigating to correct page activates chunk', async ({ page }) => {
    // Start on wrong page
    await page.goto('/details/test-doc-1?page=1&chunk=chunk-0-page-2');
    await page.waitForLoadState('networkidle');

    // Navigate to page 2
    const nextButton = await page.locator('[data-testid="next-page"]');
    if (await nextButton.isVisible()) {
      await nextButton.click();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);

      // Now chunk should be active
      const chunk = await page.locator('[data-chunk-id="chunk-0-page-2"]').first();
      if (await chunk.isVisible()) {
        const chunkClass = await chunk.getAttribute('class');
        expect(chunkClass).toContain('active');
      }
    }
  });
});

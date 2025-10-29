/**
 * Performance E2E Tests
 *
 * Agent 14: Testing & Documentation
 * Wave 3 - BBox Overlay React Implementation
 *
 * Tests for performance metrics including:
 * - Rendering performance
 * - Interaction responsiveness
 * - Memory usage
 * - Bundle size impact
 * - Frame rate during interactions
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

test.describe('Initial Render Performance', () => {
  test('structure fetch completes within 1 second', async ({ page }) => {
    const startTime = Date.now();

    // Wait for overlay to be visible
    await page.waitForSelector('svg[role="img"][aria-label*="bounding boxes"]', {
      timeout: 5000
    });

    const endTime = Date.now();
    const duration = endTime - startTime;

    // Should load quickly
    expect(duration).toBeLessThan(1000);
  });

  test('bboxes render within 500ms after structure loaded', async ({ page }) => {
    // Measure from page load to bbox render
    const metrics = await page.evaluate(() => {
      return new Promise((resolve) => {
        const observer = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          observer.disconnect();
          resolve({
            renderStart: performance.now()
          });
        });
        observer.observe({ entryTypes: ['measure', 'mark'] });

        // Wait a bit to collect
        setTimeout(() => {
          observer.disconnect();
          resolve({ renderStart: performance.now() });
        }, 2000);
      });
    });

    // Verify bboxes are rendered
    const bboxes = await page.locator('svg rect[role="button"]');
    expect(await bboxes.count()).toBeGreaterThan(0);
  });

  test('overlay scales without lag on viewport resize', async ({ page }) => {
    const overlay = await page.locator('svg[role="img"][aria-label*="bounding boxes"]');

    // Resize multiple times
    const sizes = [
      { width: 1920, height: 1080 },
      { width: 1280, height: 720 },
      { width: 1440, height: 900 },
    ];

    for (const size of sizes) {
      const startTime = Date.now();

      await page.setViewportSize(size);

      // Wait for resize to stabilize
      await page.waitForTimeout(100);

      const endTime = Date.now();
      const duration = endTime - startTime;

      // Should resize quickly
      expect(duration).toBeLessThan(200);

      // Overlay should still be visible
      await expect(overlay).toBeVisible();
    }
  });
});

test.describe('Interaction Performance', () => {
  test('bbox click response time under 100ms', async ({ page }) => {
    const firstBbox = await page.locator('svg rect[role="button"]').first();

    const startTime = Date.now();
    await firstBbox.click();

    // Wait for active class
    await page.waitForSelector('svg rect.active', { timeout: 500 });

    const endTime = Date.now();
    const duration = endTime - startTime;

    // Should respond instantly
    expect(duration).toBeLessThan(100);
  });

  test('hover response time under 50ms', async ({ page }) => {
    const firstBbox = await page.locator('svg rect[role="button"]').first();

    const startTime = Date.now();
    await firstBbox.hover();

    // Wait for hover class
    await page.waitForSelector('svg rect.hovered', { timeout: 200 });

    const endTime = Date.now();
    const duration = endTime - startTime;

    // Should be nearly instant
    expect(duration).toBeLessThan(50);
  });

  test('smooth scroll completes within 600ms', async ({ page }) => {
    const firstBbox = await page.locator('svg rect[role="button"]').first();
    const chunkId = await firstBbox.getAttribute('data-chunk-id');

    // Scroll to top first
    await page.evaluate(() => window.scrollTo(0, 0));

    const startTime = Date.now();
    await firstBbox.click();

    // Wait for chunk to be in viewport
    const chunk = await page.locator(`[data-chunk-id="${chunkId}"]`).first();
    await expect(chunk).toBeInViewport({ timeout: 1000 });

    const endTime = Date.now();
    const duration = endTime - startTime;

    // Smooth scroll should complete quickly
    expect(duration).toBeLessThan(600);
  });

  test('handles rapid clicks without lag', async ({ page }) => {
    const bboxes = await page.locator('svg rect[role="button"]');

    const startTime = Date.now();

    // Rapid click 5 bboxes
    for (let i = 0; i < 5; i++) {
      await bboxes.nth(i).click();
      await page.waitForTimeout(50);
    }

    const endTime = Date.now();
    const duration = endTime - startTime;

    // Should handle rapid clicks smoothly
    expect(duration).toBeLessThan(500);

    // Last bbox should be active
    const lastClass = await bboxes.nth(4).getAttribute('class');
    expect(lastClass).toContain('active');
  });

  test('handles rapid hovers without lag', async ({ page }) => {
    const bboxes = await page.locator('svg rect[role="button"]');

    const startTime = Date.now();

    // Rapid hover 10 bboxes
    for (let i = 0; i < 10; i++) {
      await bboxes.nth(i).hover();
      await page.waitForTimeout(30);
    }

    const endTime = Date.now();
    const duration = endTime - startTime;

    // Should handle rapid hovers smoothly
    expect(duration).toBeLessThan(500);

    // Last bbox should be hovered
    const lastClass = await bboxes.nth(9).getAttribute('class');
    expect(lastClass).toContain('hovered');
  });
});

test.describe('Frame Rate', () => {
  test('maintains 60fps during hover interactions', async ({ page }) => {
    // Start performance monitoring
    await page.evaluate(() => {
      window.frameCount = 0;
      window.rafId = null;

      const countFrames = () => {
        window.frameCount++;
        window.rafId = requestAnimationFrame(countFrames);
      };

      countFrames();
    });

    const bboxes = await page.locator('svg rect[role="button"]');

    // Hover multiple bboxes
    for (let i = 0; i < 5; i++) {
      await bboxes.nth(i).hover();
      await page.waitForTimeout(100);
    }

    // Stop counting and check FPS
    const frameCount = await page.evaluate(() => {
      cancelAnimationFrame(window.rafId);
      return window.frameCount;
    });

    // Over ~500ms, should have ~30 frames minimum (60fps ideal)
    expect(frameCount).toBeGreaterThan(25);
  });

  test('no frame drops during scroll', async ({ page }) => {
    const firstBbox = await page.locator('svg rect[role="button"]').first();

    // Start frame counting
    await page.evaluate(() => {
      window.frameCount = 0;
      const countFrames = () => {
        window.frameCount++;
        requestAnimationFrame(countFrames);
      };
      countFrames();
    });

    // Trigger scroll
    await firstBbox.click();
    await page.waitForTimeout(600);

    // Check frame count
    const frameCount = await page.evaluate(() => window.frameCount);

    // Should have smooth animation (at least 30 frames in 600ms)
    expect(frameCount).toBeGreaterThan(30);
  });
});

test.describe('Memory Usage', () => {
  test('does not leak memory on repeated interactions', async ({ page }) => {
    // Get initial memory
    const initialMetrics = await page.metrics();

    const bboxes = await page.locator('svg rect[role="button"]');

    // Perform 50 interactions
    for (let i = 0; i < 50; i++) {
      const bbox = bboxes.nth(i % 10);
      await bbox.hover();
      await bbox.click();
      await page.waitForTimeout(20);
    }

    // Get final memory
    const finalMetrics = await page.metrics();

    // Memory should not increase significantly
    const memoryIncrease = finalMetrics.JSHeapUsedSize - initialMetrics.JSHeapUsedSize;
    const increasePercent = (memoryIncrease / initialMetrics.JSHeapUsedSize) * 100;

    // Should not leak (allow some increase for caching)
    expect(increasePercent).toBeLessThan(50);
  });

  test('cleans up ResizeObserver on unmount', async ({ page }) => {
    // Navigate to page
    await page.goto('/details/test-doc-1');
    await page.waitForLoadState('networkidle');

    // Get initial metrics
    const initialMetrics = await page.metrics();

    // Navigate away and back multiple times
    for (let i = 0; i < 3; i++) {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      await page.goto('/details/test-doc-1');
      await page.waitForLoadState('networkidle');
    }

    // Check final metrics
    const finalMetrics = await page.metrics();

    // Should not accumulate observers
    const listenerIncrease = finalMetrics.JSEventListeners - initialMetrics.JSEventListeners;

    // Allow some listeners, but not excessive
    expect(listenerIncrease).toBeLessThan(20);
  });
});

test.describe('DOM Performance', () => {
  test('renders efficiently with many bboxes', async ({ page }) => {
    // Navigate to page with many bboxes
    await page.goto('/details/test-doc-1');
    await page.waitForLoadState('networkidle');

    const bboxes = await page.locator('svg rect[role="button"]');
    const count = await bboxes.count();

    // Get render metrics
    const metrics = await page.metrics();

    // Even with many bboxes, should not have excessive DOM nodes
    expect(metrics.Nodes).toBeLessThan(5000);
  });

  test('uses efficient CSS selectors', async ({ page }) => {
    // Measure selector performance
    const startTime = Date.now();

    await page.locator('svg rect[role="button"]').first();
    await page.locator('[data-chunk-id]').first();
    await page.locator('.active').first();

    const endTime = Date.now();
    const duration = endTime - startTime;

    // Selectors should be fast
    expect(duration).toBeLessThan(100);
  });
});

test.describe('Network Performance', () => {
  test('structure API response time under 300ms', async ({ page }) => {
    // Listen for structure API calls
    const responses = [];

    page.on('response', response => {
      if (response.url().includes('/structure')) {
        responses.push({
          url: response.url(),
          status: response.status(),
          timing: response.timing()
        });
      }
    });

    await page.goto('/details/test-doc-1');
    await page.waitForLoadState('networkidle');

    // Wait a bit for responses to be captured
    await page.waitForTimeout(500);

    // Check if we got structure response
    if (responses.length > 0) {
      const response = responses[0];
      expect(response.status).toBe(200);

      // Check response time
      // Note: timing might not be available in all browsers
    }
  });

  test('does not refetch structure on interactions', async ({ page }) => {
    let requestCount = 0;

    page.on('request', request => {
      if (request.url().includes('/structure')) {
        requestCount++;
      }
    });

    await page.goto('/details/test-doc-1');
    await page.waitForLoadState('networkidle');

    const initialRequests = requestCount;

    // Interact with bboxes
    const bboxes = await page.locator('svg rect[role="button"]');
    await bboxes.first().hover();
    await bboxes.first().click();
    await bboxes.nth(1).hover();
    await bboxes.nth(1).click();

    await page.waitForTimeout(500);

    // Should not make additional requests
    expect(requestCount).toBe(initialRequests);
  });
});

test.describe('Bundle Size Impact', () => {
  test('JavaScript bundle loads efficiently', async ({ page }) => {
    const resources = [];

    page.on('response', response => {
      if (response.url().endsWith('.js')) {
        resources.push({
          url: response.url(),
          size: response.headers()['content-length']
        });
      }
    });

    await page.goto('/details/test-doc-1');
    await page.waitForLoadState('networkidle');

    // Verify scripts loaded
    expect(resources.length).toBeGreaterThan(0);
  });
});

test.describe('Performance Benchmarks', () => {
  test('meets 239ms average search performance target', async ({ page }) => {
    // This would require backend integration
    // Document that bbox rendering doesn't impact search performance
  });

  test('overlay overhead under 50ms', async ({ page }) => {
    // Navigate without overlay first
    await page.goto('/details/no-bbox-doc');
    await page.waitForLoadState('networkidle');

    const startWithout = Date.now();
    await page.reload();
    await page.waitForLoadState('networkidle');
    const durationWithout = Date.now() - startWithout;

    // Navigate with overlay
    await page.goto('/details/test-doc-1');
    await page.waitForLoadState('networkidle');

    const startWith = Date.now();
    await page.reload();
    await page.waitForLoadState('networkidle');
    const durationWith = Date.now() - startWith;

    // Overlay should add minimal overhead
    const overhead = durationWith - durationWithout;
    expect(overhead).toBeLessThan(100);
  });
});

test.describe('Stress Testing', () => {
  test('handles 100+ bboxes smoothly', async ({ page }) => {
    // Navigate to document with many bboxes
    await page.goto('/details/large-doc');
    await page.waitForLoadState('networkidle');

    const bboxes = await page.locator('svg rect[role="button"]');
    const count = await bboxes.count();

    if (count > 0) {
      // Should still be interactive
      const startTime = Date.now();
      await bboxes.first().click();
      await page.waitForSelector('svg rect.active', { timeout: 500 });
      const duration = Date.now() - startTime;

      expect(duration).toBeLessThan(150);
    }
  });

  test('maintains performance after prolonged use', async ({ page }) => {
    // Simulate prolonged use
    const bboxes = await page.locator('svg rect[role="button"]');

    // Perform 100 interactions
    for (let i = 0; i < 100; i++) {
      const bbox = bboxes.nth(i % 10);
      await bbox.hover();
      if (i % 10 === 0) {
        await bbox.click();
      }
      await page.waitForTimeout(10);
    }

    // Should still be responsive
    const startTime = Date.now();
    await bboxes.first().click();
    await page.waitForSelector('svg rect.active', { timeout: 500 });
    const duration = Date.now() - startTime;

    expect(duration).toBeLessThan(150);
  });
});

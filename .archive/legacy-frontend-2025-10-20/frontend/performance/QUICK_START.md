# Performance Optimization Quick Start

**5-Minute Integration Guide**

## Step 1: Include CSS (30 seconds)

Add to your HTML `<head>`:

```html
<link rel="stylesheet" href="styles/performance-optimizations.css">
```

## Step 2: Update DetailsController (2 minutes)

Replace existing controller initialization:

```javascript
// OLD CODE:
import { DetailsController } from './details-controller.js';
const controller = new DetailsController(slideshow, accordion, docId);
await controller.init();

// NEW CODE:
import { OptimizedDetailsController } from './performance/INTEGRATION_EXAMPLE.js';
const controller = new OptimizedDetailsController(slideshow, accordion, docId);
await controller.init();

// Add cleanup
window.addEventListener('beforeunload', () => {
  controller.destroy();
});
```

## Step 3: Enable Metrics (Optional, 1 minute)

For development/staging only:

```javascript
import { PerformanceMetrics } from './performance/index.js';

if (window.location.hostname === 'localhost') {
  PerformanceMetrics.setEnabled(true);

  // Report every minute
  setInterval(() => {
    PerformanceMetrics.report();
  }, 60000);
}
```

## Step 4: Monitor Cache (Optional, 1 minute)

```javascript
// Log cache stats every 30 seconds
setInterval(() => {
  const stats = controller.structureLoader.getStats();
  console.log(`Cache: ${stats.hitRate.toFixed(1)}% hit rate, ${stats.size} pages cached`);
}, 30000);
```

## Step 5: Test (30 seconds)

1. Open DevTools Console
2. Navigate between pages
3. Look for:
   - `[StructureCache] Cache hit:` messages
   - Smooth 60fps interactions
   - Lower network requests

## Done! 🎉

You should immediately see:
- Faster page navigation
- Smoother hover interactions
- Fewer structure API calls
- Performance metrics in console (if enabled)

## Verify Performance

Run benchmarks:

```bash
node scripts/benchmark_performance.js
```

Expected output:
```
📊 Performance Summary:
  Structure API: ~239ms mean
  Cache Hit Rate: 65-80%
  Memory Usage: ~8MB
```

## Troubleshooting

### Cache not working?

Check console for:
```
[StructureLazyLoader] Initialized
[StructureCache] Initialized (maxSize: 20, maxAge: 300000ms)
```

### Performance metrics not showing?

Verify metrics are enabled:
```javascript
console.log('Metrics enabled:', PerformanceMetrics.isEnabled());
```

### High memory usage?

Check cache stats:
```javascript
const stats = controller.structureLoader.getStats();
console.log('Cache size:', stats.totalSize / 1024 / 1024, 'MB');
```

If >10MB, reduce cache size:
```javascript
const controller = new OptimizedDetailsController(slideshow, accordion, docId, {
  cacheSize: 10  // Reduce from default 20
});
```

## Need More Details?

- **Full Documentation:** `README.md`
- **API Reference:** `README.md#api-reference`
- **Integration Examples:** `INTEGRATION_EXAMPLE.js`
- **Performance Report:** `PERFORMANCE_REPORT.md`

#!/usr/bin/env node
/**
 * Performance Benchmark Script
 *
 * Automated performance testing for bidirectional highlighting feature.
 * Measures structure API response time, rendering performance, and
 * interaction latency across various document sizes.
 *
 * Wave 3 - Agent 13: Performance Optimizer
 *
 * Usage:
 *   node scripts/benchmark_performance.js
 *   node scripts/benchmark_performance.js --scenario=small
 *   node scripts/benchmark_performance.js --output=json
 *
 * Requirements:
 *   - Node.js 18+
 *   - Server running on localhost:8000
 *   - Test documents uploaded
 */

const http = require('http');
const { performance } = require('perf_hooks');

// ============================================================================
// Configuration
// ============================================================================

const CONFIG = {
  baseUrl: process.env.API_BASE_URL || 'http://localhost:8000',
  iterations: 10,
  warmupIterations: 2,
  timeout: 10000,
  scenarios: {
    small: {
      name: 'Small Document',
      pages: 10,
      elementsPerPage: 5,
    },
    medium: {
      name: 'Medium Document',
      pages: 50,
      elementsPerPage: 20,
    },
    large: {
      name: 'Large Document',
      pages: 200,
      elementsPerPage: 50,
    },
  },
};

// Parse command-line arguments
const args = process.argv.slice(2).reduce((acc, arg) => {
  const [key, value] = arg.replace(/^--/, '').split('=');
  acc[key] = value || true;
  return acc;
}, {});

const outputFormat = args.output || 'table';
const scenarioFilter = args.scenario || null;

// ============================================================================
// Utilities
// ============================================================================

/**
 * Fetch JSON from URL
 */
async function fetchJSON(url) {
  return new Promise((resolve, reject) => {
    const startTime = performance.now();

    http
      .get(url, (res) => {
        let data = '';

        res.on('data', (chunk) => {
          data += chunk;
        });

        res.on('end', () => {
          const duration = performance.now() - startTime;

          try {
            const json = JSON.parse(data);
            resolve({ json, duration, status: res.statusCode });
          } catch (error) {
            reject(new Error(`Failed to parse JSON: ${error.message}`));
          }
        });
      })
      .on('error', (error) => {
        reject(error);
      })
      .setTimeout(CONFIG.timeout, () => {
        reject(new Error('Request timeout'));
      });
  });
}

/**
 * Measure async function execution
 */
async function measure(name, fn) {
  const startTime = performance.now();
  const result = await fn();
  const duration = performance.now() - startTime;

  return { result, duration, name };
}

/**
 * Calculate statistics from array of measurements
 */
function calculateStats(measurements) {
  const sorted = [...measurements].sort((a, b) => a - b);
  const count = sorted.length;
  const sum = sorted.reduce((a, b) => a + b, 0);

  return {
    count,
    min: sorted[0],
    max: sorted[count - 1],
    mean: sum / count,
    median: sorted[Math.floor(count / 2)],
    p95: sorted[Math.floor(count * 0.95)],
    p99: sorted[Math.floor(count * 0.99)],
  };
}

/**
 * Format duration in milliseconds
 */
function formatDuration(ms) {
  if (ms < 1) return `${(ms * 1000).toFixed(0)}μs`;
  if (ms < 1000) return `${ms.toFixed(2)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

/**
 * Format statistics object
 */
function formatStats(stats) {
  return {
    count: stats.count,
    min: formatDuration(stats.min),
    max: formatDuration(stats.max),
    mean: formatDuration(stats.mean),
    median: formatDuration(stats.median),
    p95: formatDuration(stats.p95),
    p99: formatDuration(stats.p99),
  };
}

// ============================================================================
// Benchmarks
// ============================================================================

/**
 * Benchmark: Structure API response time
 */
async function benchmarkStructureAPI(docId = 'test-doc', pages = 10) {
  console.log(`\n📡 Benchmarking Structure API (${pages} pages)...`);

  const measurements = [];

  // Warmup
  for (let i = 0; i < CONFIG.warmupIterations; i++) {
    await fetchJSON(`${CONFIG.baseUrl}/documents/${docId}/pages/1/structure`);
  }

  // Benchmark
  for (let i = 0; i < CONFIG.iterations; i++) {
    const page = (i % pages) + 1;
    const url = `${CONFIG.baseUrl}/documents/${docId}/pages/${page}/structure`;

    try {
      const { duration, status } = await fetchJSON(url);

      if (status === 200) {
        measurements.push(duration);
        process.stdout.write('.');
      } else {
        process.stdout.write('x');
      }
    } catch (error) {
      process.stdout.write('E');
      console.error(`\nError fetching page ${page}:`, error.message);
    }
  }

  console.log(''); // Newline after progress dots

  if (measurements.length === 0) {
    console.error('❌ No successful measurements');
    return null;
  }

  const stats = calculateStats(measurements);
  return {
    name: 'Structure API Response',
    stats,
    formatted: formatStats(stats),
  };
}

/**
 * Benchmark: Structure decompression
 */
async function benchmarkDecompression(docId = 'test-doc', pages = 10) {
  console.log(`\n🗜️  Benchmarking Structure Decompression (${pages} pages)...`);

  const measurements = [];

  // Fetch structure data first
  const structures = [];
  for (let i = 1; i <= Math.min(pages, 10); i++) {
    try {
      const { json } = await fetchJSON(
        `${CONFIG.baseUrl}/documents/${docId}/pages/${i}/structure`
      );
      structures.push(json);
    } catch (error) {
      console.warn(`Failed to fetch page ${i}:`, error.message);
    }
  }

  if (structures.length === 0) {
    console.error('❌ No structures to test');
    return null;
  }

  // Warmup
  for (let i = 0; i < CONFIG.warmupIterations; i++) {
    JSON.stringify(structures[0]);
    JSON.parse(JSON.stringify(structures[0]));
  }

  // Benchmark JSON serialization/parsing
  for (let i = 0; i < CONFIG.iterations; i++) {
    const structure = structures[i % structures.length];

    const startTime = performance.now();
    const serialized = JSON.stringify(structure);
    const parsed = JSON.parse(serialized);
    const duration = performance.now() - startTime;

    measurements.push(duration);
    process.stdout.write('.');
  }

  console.log('');

  const stats = calculateStats(measurements);
  return {
    name: 'Structure Decompression',
    stats,
    formatted: formatStats(stats),
  };
}

/**
 * Benchmark: Cache performance simulation
 */
async function benchmarkCachePerformance(docId = 'test-doc', pages = 50) {
  console.log(`\n💾 Benchmarking Cache Performance (${pages} pages)...`);

  // Simulate LRU cache
  const cache = new Map();
  const maxCacheSize = 20;
  const measurements = {
    hits: [],
    misses: [],
  };

  // Simulate typical navigation pattern
  const pageSequence = [];
  let currentPage = 1;

  // Generate realistic page navigation sequence
  for (let i = 0; i < CONFIG.iterations * 10; i++) {
    pageSequence.push(currentPage);

    // Random navigation: 60% next, 20% prev, 20% random jump
    const rand = Math.random();
    if (rand < 0.6) {
      currentPage = Math.min(pages, currentPage + 1);
    } else if (rand < 0.8) {
      currentPage = Math.max(1, currentPage - 1);
    } else {
      currentPage = Math.floor(Math.random() * pages) + 1;
    }
  }

  // Simulate cache lookups
  for (const page of pageSequence) {
    const startTime = performance.now();

    if (cache.has(page)) {
      // Cache hit - instant
      const value = cache.get(page);
      cache.delete(page);
      cache.set(page, value); // Move to end (LRU)

      const duration = performance.now() - startTime;
      measurements.hits.push(duration);
      process.stdout.write('✓');
    } else {
      // Cache miss - simulate fetch
      const fetchStart = performance.now();
      await new Promise((resolve) => setTimeout(resolve, 50)); // Simulate 50ms fetch
      const fetchDuration = performance.now() - fetchStart;

      // Add to cache
      if (cache.size >= maxCacheSize) {
        const firstKey = cache.keys().next().value;
        cache.delete(firstKey);
      }
      cache.set(page, { page });

      measurements.misses.push(fetchDuration);
      process.stdout.write('×');
    }
  }

  console.log('');

  const hitRate = (measurements.hits.length / pageSequence.length) * 100;

  return {
    name: 'Cache Performance',
    hitRate: hitRate.toFixed(1) + '%',
    hits: measurements.hits.length,
    misses: measurements.misses.length,
    hitStats: calculateStats(measurements.hits),
    missStats: calculateStats(measurements.misses),
    formatted: {
      hitRate: hitRate.toFixed(1) + '%',
      avgHitTime: formatDuration(calculateStats(measurements.hits).mean),
      avgMissTime: formatDuration(calculateStats(measurements.misses).mean),
    },
  };
}

/**
 * Benchmark: Memory usage estimation
 */
async function benchmarkMemoryUsage(docId = 'test-doc', pages = 20) {
  console.log(`\n🧠 Benchmarking Memory Usage (${pages} pages)...`);

  const structures = [];
  let totalSize = 0;

  for (let i = 1; i <= Math.min(pages, 20); i++) {
    try {
      const { json } = await fetchJSON(
        `${CONFIG.baseUrl}/documents/${docId}/pages/${i}/structure`
      );
      structures.push(json);

      const size = JSON.stringify(json).length * 2; // UTF-16 estimate
      totalSize += size;

      process.stdout.write('.');
    } catch (error) {
      process.stdout.write('x');
    }
  }

  console.log('');

  const avgSize = structures.length > 0 ? totalSize / structures.length : 0;
  const maxCacheSize = 20;
  const estimatedCacheMemory = avgSize * maxCacheSize;

  return {
    name: 'Memory Usage',
    structures: structures.length,
    avgSizeKB: (avgSize / 1024).toFixed(2),
    totalSizeKB: (totalSize / 1024).toFixed(2),
    estimatedCacheMB: (estimatedCacheMemory / 1024 / 1024).toFixed(2),
  };
}

// ============================================================================
// Report Generation
// ============================================================================

/**
 * Generate console report
 */
function generateConsoleReport(results) {
  console.log('\n' + '='.repeat(80));
  console.log('📊 PERFORMANCE BENCHMARK REPORT');
  console.log('='.repeat(80));

  for (const result of results) {
    console.log(`\n${result.name}:`);
    console.log('-'.repeat(80));

    if (result.formatted) {
      for (const [key, value] of Object.entries(result.formatted)) {
        console.log(`  ${key.padEnd(20)}: ${value}`);
      }
    }

    if (result.hitRate) {
      console.log(`  Cache Hit Rate      : ${result.hitRate}`);
      console.log(`  Cache Hits          : ${result.hits}`);
      console.log(`  Cache Misses        : ${result.misses}`);
    }

    if (result.avgSizeKB) {
      console.log(`  Structures Tested   : ${result.structures}`);
      console.log(`  Avg Size (KB)       : ${result.avgSizeKB}`);
      console.log(`  Total Size (KB)     : ${result.totalSizeKB}`);
      console.log(`  Cache Memory (MB)   : ${result.estimatedCacheMB}`);
    }
  }

  console.log('\n' + '='.repeat(80));
}

/**
 * Generate JSON report
 */
function generateJSONReport(results) {
  const report = {
    timestamp: new Date().toISOString(),
    config: CONFIG,
    results,
  };

  console.log(JSON.stringify(report, null, 2));
}

// ============================================================================
// Main
// ============================================================================

async function main() {
  console.log('🚀 Starting Performance Benchmarks...');
  console.log(`Base URL: ${CONFIG.baseUrl}`);
  console.log(`Iterations: ${CONFIG.iterations}`);
  console.log(`Output Format: ${outputFormat}\n`);

  const results = [];

  // Run benchmarks
  try {
    // Structure API
    const apiResult = await benchmarkStructureAPI('test-doc', 50);
    if (apiResult) results.push(apiResult);

    // Decompression
    const decompResult = await benchmarkDecompression('test-doc', 10);
    if (decompResult) results.push(decompResult);

    // Cache performance
    const cacheResult = await benchmarkCachePerformance('test-doc', 50);
    if (cacheResult) results.push(cacheResult);

    // Memory usage
    const memResult = await benchmarkMemoryUsage('test-doc', 20);
    if (memResult) results.push(memResult);
  } catch (error) {
    console.error('\n❌ Benchmark failed:', error);
    process.exit(1);
  }

  // Generate report
  if (outputFormat === 'json') {
    generateJSONReport(results);
  } else {
    generateConsoleReport(results);
  }

  console.log('\n✅ Benchmarks complete!');
}

// Run
main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});

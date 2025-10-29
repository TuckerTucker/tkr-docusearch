/**
 * usePerformanceMonitor Hook Tests
 *
 * Agent 12: Performance Optimizer
 * Wave 3 - BBox Overlay React Implementation
 *
 * Tests cover:
 * - Performance mark creation
 * - Performance measurement
 * - Handler tracking
 * - Development vs production mode
 */

import { describe, test, expect, beforeEach, vi, afterEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { usePerformanceMonitor } from '../usePerformanceMonitor';

describe('usePerformanceMonitor', () => {
  let originalNodeEnv: string | undefined;

  beforeEach(() => {
    originalNodeEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'development';
    vi.spyOn(performance, 'now').mockReturnValue(0);
    vi.spyOn(performance, 'mark').mockImplementation(() => ({} as PerformanceMark));
    vi.spyOn(performance, 'measure').mockImplementation(() => ({} as PerformanceMeasure));
  });

  afterEach(() => {
    process.env.NODE_ENV = originalNodeEnv;
    vi.restoreAllMocks();
  });

  test('creates performance marks', () => {
    const { result } = renderHook(() =>
      usePerformanceMonitor({ componentName: 'TestComponent' })
    );

    result.current.mark('test-mark');

    expect(performance.mark).toHaveBeenCalledWith('TestComponent:test-mark');
  });

  test('measures between marks', () => {
    const { result } = renderHook(() =>
      usePerformanceMonitor({ componentName: 'TestComponent' })
    );

    result.current.mark('start');
    result.current.mark('end');
    const duration = result.current.measure('operation', 'start', 'end');

    expect(performance.measure).toHaveBeenCalledWith(
      'TestComponent:operation',
      'TestComponent:start',
      'TestComponent:end'
    );
    expect(duration).not.toBeNull();
  });

  test('returns null for invalid measure', () => {
    const { result } = renderHook(() =>
      usePerformanceMonitor({ componentName: 'TestComponent' })
    );

    const duration = result.current.measure('operation', 'nonexistent-start', 'nonexistent-end');

    expect(duration).toBeNull();
  });

  test('tracks handler execution time', () => {
    const { result } = renderHook(() =>
      usePerformanceMonitor({ componentName: 'TestComponent' })
    );

    const handler = vi.fn((x: number) => x * 2);
    const trackedHandler = result.current.trackHandler(handler, 'testHandler');

    const returnValue = trackedHandler(5);

    expect(returnValue).toBe(10);
    expect(handler).toHaveBeenCalledWith(5);
  });

  test('warns on slow operations', () => {
    const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    let currentTime = 0;
    vi.spyOn(performance, 'now').mockImplementation(() => currentTime);

    const { result } = renderHook(() =>
      usePerformanceMonitor({
        componentName: 'TestComponent',
        slowThreshold: 10,
      })
    );

    result.current.mark('start');
    currentTime = 20; // Slow operation
    result.current.mark('end');
    result.current.measure('slow-operation', 'start', 'end');

    expect(consoleWarn).toHaveBeenCalledWith(
      expect.stringContaining('slow-operation')
    );

    consoleWarn.mockRestore();
  });

  test('disabled when enabled is false', () => {
    const { result } = renderHook(() =>
      usePerformanceMonitor({ componentName: 'TestComponent', enabled: false })
    );

    result.current.mark('test-mark');

    expect(performance.mark).not.toHaveBeenCalled();
  });

  test('gets current metrics', () => {
    const { result } = renderHook(() =>
      usePerformanceMonitor({ componentName: 'TestComponent' })
    );

    result.current.mark('test');
    const metrics = result.current.getMetrics();

    expect(metrics).toHaveProperty('renderTime');
    expect(metrics).toHaveProperty('marks');
    expect(metrics).toHaveProperty('measures');
    expect(metrics.marks.size).toBeGreaterThan(0);
  });

  test('clears marks and measures', () => {
    vi.spyOn(performance, 'clearMarks').mockImplementation(() => {});
    vi.spyOn(performance, 'clearMeasures').mockImplementation(() => {});

    const { result } = renderHook(() =>
      usePerformanceMonitor({ componentName: 'TestComponent' })
    );

    result.current.mark('test');
    result.current.clear();

    const metrics = result.current.getMetrics();
    expect(metrics.marks.size).toBe(0);
    expect(metrics.measures.size).toBe(0);
  });

  test('does not run in production by default', () => {
    process.env.NODE_ENV = 'production';

    const { result } = renderHook(() =>
      usePerformanceMonitor({ componentName: 'TestComponent' })
    );

    result.current.mark('test');

    // Should not call performance API in production
    expect(performance.mark).not.toHaveBeenCalled();
  });
});

/**
 * useThrottle Hook Tests
 *
 * Agent 12: Performance Optimizer
 * Wave 3 - BBox Overlay React Implementation
 *
 * Tests cover:
 * - Basic throttling functionality
 * - Leading/trailing edge options
 * - RAF-based throttling
 * - Cleanup on unmount
 */

import { describe, test, expect, beforeEach, vi, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useThrottle, useThrottleRAF } from '../useThrottle';

describe('useThrottle', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  test('throttles function calls', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useThrottle(callback, 100));

    // Call multiple times rapidly
    act(() => {
      result.current('first');
    });
    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledWith('first');

    act(() => {
      result.current('second');
      result.current('third');
    });
    // Should not call again within interval
    expect(callback).toHaveBeenCalledTimes(1);

    // Advance past interval
    act(() => {
      vi.advanceTimersByTime(100);
    });

    act(() => {
      result.current('fourth');
    });
    // Should call again now
    expect(callback).toHaveBeenCalledTimes(2);
  });

  test('respects custom interval', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useThrottle(callback, 500));

    act(() => {
      result.current('test');
    });
    expect(callback).toHaveBeenCalledTimes(1);

    act(() => {
      vi.advanceTimersByTime(400);
      result.current('blocked');
    });
    expect(callback).toHaveBeenCalledTimes(1);

    act(() => {
      vi.advanceTimersByTime(100);
      result.current('allowed');
    });
    expect(callback).toHaveBeenCalledTimes(2);
  });

  test('leading edge option enabled by default', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useThrottle(callback, 100, { leading: true }));

    act(() => {
      result.current('test');
    });

    // Should be called immediately with leading edge
    expect(callback).toHaveBeenCalledTimes(1);
  });

  test('trailing edge option works', () => {
    const callback = vi.fn();
    const { result } = renderHook(() =>
      useThrottle(callback, 100, { leading: false, trailing: true })
    );

    act(() => {
      result.current('test');
    });

    // Should not be called immediately
    expect(callback).not.toHaveBeenCalled();

    // Advance to trailing edge
    act(() => {
      vi.advanceTimersByTime(100);
    });

    expect(callback).toHaveBeenCalledTimes(1);
  });

  test('cleanup cancels pending calls', () => {
    const callback = vi.fn();
    const { result, unmount } = renderHook(() =>
      useThrottle(callback, 100, { leading: false, trailing: true })
    );

    act(() => {
      result.current('test');
    });

    unmount();

    act(() => {
      vi.advanceTimersByTime(100);
    });

    // Should not have been called after unmount
    expect(callback).not.toHaveBeenCalled();
  });
});

describe('useThrottleRAF', () => {
  let rafCallback: FrameRequestCallback | null = null;

  beforeEach(() => {
    rafCallback = null;
    vi.spyOn(window, 'requestAnimationFrame').mockImplementation((cb) => {
      rafCallback = cb;
      return 1;
    });
    vi.spyOn(window, 'cancelAnimationFrame').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  test('throttles using requestAnimationFrame', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useThrottleRAF(callback));

    act(() => {
      result.current('first');
      result.current('second');
      result.current('third');
    });

    // Should not have been called yet
    expect(callback).not.toHaveBeenCalled();
    expect(window.requestAnimationFrame).toHaveBeenCalledTimes(1);

    // Execute RAF callback
    act(() => {
      rafCallback?.(0);
    });

    // Should have been called once with last arguments
    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledWith('third');
  });

  test('only schedules one RAF at a time', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useThrottleRAF(callback));

    act(() => {
      result.current('first');
      result.current('second');
    });

    // Should only have requested one frame
    expect(window.requestAnimationFrame).toHaveBeenCalledTimes(1);
  });

  test('cleanup cancels pending RAF', () => {
    const callback = vi.fn();
    const { result, unmount } = renderHook(() => useThrottleRAF(callback));

    act(() => {
      result.current('test');
    });

    unmount();

    expect(window.cancelAnimationFrame).toHaveBeenCalled();

    // Execute RAF callback after unmount
    act(() => {
      rafCallback?.(0);
    });

    // Should not have been called
    expect(callback).not.toHaveBeenCalled();
  });
});

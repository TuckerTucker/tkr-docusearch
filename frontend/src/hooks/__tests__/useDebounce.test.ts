/**
 * useDebounce Hook Tests
 *
 * Agent 12: Performance Optimizer
 * Wave 3 - BBox Overlay React Implementation
 *
 * Tests cover:
 * - Basic debouncing functionality
 * - Leading/trailing edge options
 * - Cleanup on unmount
 */

import { describe, test, expect, beforeEach, vi, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useDebounce, useDebouncedValue } from '../useDebounce';

describe('useDebounce', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  test('debounces function calls', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useDebounce(callback, 100));

    // Call multiple times rapidly
    act(() => {
      result.current('first');
      result.current('second');
      result.current('third');
    });

    // Should not have been called yet
    expect(callback).not.toHaveBeenCalled();

    // Advance timers past delay
    act(() => {
      vi.advanceTimersByTime(100);
    });

    // Should have been called once with last argument
    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledWith('third');
  });

  test('respects custom delay', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useDebounce(callback, 500));

    act(() => {
      result.current('test');
    });

    act(() => {
      vi.advanceTimersByTime(400);
    });
    expect(callback).not.toHaveBeenCalled();

    act(() => {
      vi.advanceTimersByTime(100);
    });
    expect(callback).toHaveBeenCalledTimes(1);
  });

  test('leading edge option calls immediately', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useDebounce(callback, 100, { leading: true }));

    act(() => {
      result.current('test');
    });

    // Should be called immediately with leading edge
    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledWith('test');
  });

  test('trailing edge option calls after delay', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useDebounce(callback, 100, { trailing: true }));

    act(() => {
      result.current('test');
    });

    expect(callback).not.toHaveBeenCalled();

    act(() => {
      vi.advanceTimersByTime(100);
    });

    expect(callback).toHaveBeenCalledTimes(1);
  });

  test('cleanup cancels pending calls', () => {
    const callback = vi.fn();
    const { result, unmount } = renderHook(() => useDebounce(callback, 100));

    act(() => {
      result.current('test');
    });

    // Unmount before delay expires
    unmount();

    act(() => {
      vi.advanceTimersByTime(100);
    });

    // Should not have been called
    expect(callback).not.toHaveBeenCalled();
  });
});

describe('useDebouncedValue', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  test('debounces value updates', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebouncedValue(value, 100),
      { initialProps: { value: 'initial' } }
    );

    expect(result.current).toBe('initial');

    // Update value rapidly
    rerender({ value: 'updated1' });
    rerender({ value: 'updated2' });
    rerender({ value: 'final' });

    // Value should still be initial
    expect(result.current).toBe('initial');

    // Advance timers
    act(() => {
      vi.advanceTimersByTime(100);
    });

    // Value should now be final
    expect(result.current).toBe('final');
  });

  test('respects custom delay', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebouncedValue(value, 500),
      { initialProps: { value: 'initial' } }
    );

    rerender({ value: 'updated' });

    act(() => {
      vi.advanceTimersByTime(400);
    });
    expect(result.current).toBe('initial');

    act(() => {
      vi.advanceTimersByTime(100);
    });
    expect(result.current).toBe('updated');
  });
});

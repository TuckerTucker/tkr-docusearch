/**
 * useChunkNavigation Hook Tests
 *
 * Agent 10: URL Parameter Chunk Navigation
 * Wave 1 - BBox Overlay React Implementation
 *
 * Comprehensive test suite covering:
 * - Initial chunk parsing from URL
 * - Navigation callback triggering
 * - URL updating functionality
 * - React Router integration
 * - Edge cases and error handling
 * - Mount and unmount behavior
 *
 * Target: 100% code coverage
 */

import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { useChunkNavigation } from './useChunkNavigation';
import type { UseChunkNavigationOptions } from './useChunkNavigation';
import * as urlParamsModule from '../utils/urlParams';

// ============================================================================
// Test Setup
// ============================================================================

// Mock the urlParams module
vi.mock('../utils/urlParams', () => ({
  parseChunkFromUrl: vi.fn(),
  updateChunkInUrl: vi.fn(),
}));

/**
 * Wrapper component for testing hooks with React Router.
 */
function createWrapper(initialPath = '/documents/123') {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route path="/documents/:id" element={<>{children}</>} />
        </Routes>
      </MemoryRouter>
    );
  };
}

describe('useChunkNavigation', () => {
  // Store original window methods
  const originalLocation = window.location;

  beforeEach(() => {
    // Reset all mocks
    vi.clearAllMocks();

    // Mock window.location
    delete (window as any).location;
    (window as any).location = {
      href: 'http://localhost:3000/documents/123',
      search: '',
      pathname: '/documents/123',
    };

    // Default mock implementations
    vi.mocked(urlParamsModule.parseChunkFromUrl).mockReturnValue(null);
    vi.mocked(urlParamsModule.updateChunkInUrl).mockImplementation(() => {});
  });

  afterEach(() => {
    // Restore original location
    window.location = originalLocation;
    vi.restoreAllMocks();
  });

  // ============================================================================
  // Basic Functionality
  // ============================================================================

  describe('basic functionality', () => {
    test('returns null initialChunkId when no chunk in URL', () => {
      vi.mocked(urlParamsModule.parseChunkFromUrl).mockReturnValue(null);

      const { result } = renderHook(() => useChunkNavigation(), {
        wrapper: createWrapper('/documents/123'),
      });

      expect(result.current.initialChunkId).toBe(null);
    });

    test('returns initialChunkId when chunk in URL', () => {
      vi.mocked(urlParamsModule.parseChunkFromUrl).mockReturnValue('chunk-0-page-1');

      const { result } = renderHook(() => useChunkNavigation(), {
        wrapper: createWrapper('/documents/123?chunk=chunk-0-page-1'),
      });

      expect(result.current.initialChunkId).toBe('chunk-0-page-1');
    });

    test('provides navigateToChunk function', () => {
      const { result } = renderHook(() => useChunkNavigation(), {
        wrapper: createWrapper('/documents/123'),
      });

      expect(typeof result.current.navigateToChunk).toBe('function');
    });

    test('navigateToChunk is stable across renders', () => {
      const { result, rerender } = renderHook(() => useChunkNavigation(), {
        wrapper: createWrapper('/documents/123'),
      });

      const firstNavigate = result.current.navigateToChunk;
      rerender();
      const secondNavigate = result.current.navigateToChunk;

      expect(firstNavigate).toBe(secondNavigate);
    });
  });

  // ============================================================================
  // Initial Navigation on Mount
  // ============================================================================

  describe('initial navigation on mount', () => {
    test('fires onChunkNavigate callback on mount when chunk in URL', async () => {
      vi.mocked(urlParamsModule.parseChunkFromUrl).mockReturnValue('chunk-0-page-1');
      const onChunkNavigate = vi.fn();

      renderHook(
        () =>
          useChunkNavigation({
            onChunkNavigate,
          }),
        {
          wrapper: createWrapper('/documents/123?chunk=chunk-0-page-1'),
        }
      );

      await waitFor(() => {
        expect(onChunkNavigate).toHaveBeenCalledWith('chunk-0-page-1');
        expect(onChunkNavigate).toHaveBeenCalledTimes(1);
      });
    });

    test('does not fire callback on mount when no chunk in URL', () => {
      vi.mocked(urlParamsModule.parseChunkFromUrl).mockReturnValue(null);
      const onChunkNavigate = vi.fn();

      renderHook(
        () =>
          useChunkNavigation({
            onChunkNavigate,
          }),
        {
          wrapper: createWrapper('/documents/123'),
        }
      );

      expect(onChunkNavigate).not.toHaveBeenCalled();
    });

    test('does not fire callback on mount when no callback provided', () => {
      vi.mocked(urlParamsModule.parseChunkFromUrl).mockReturnValue('chunk-0-page-1');

      // Should not throw
      expect(() => {
        renderHook(() => useChunkNavigation(), {
          wrapper: createWrapper('/documents/123?chunk=chunk-0-page-1'),
        });
      }).not.toThrow();
    });

    test('only fires initial navigation once', async () => {
      vi.mocked(urlParamsModule.parseChunkFromUrl).mockReturnValue('chunk-0-page-1');
      const onChunkNavigate = vi.fn();

      const { rerender } = renderHook(
        () =>
          useChunkNavigation({
            onChunkNavigate,
          }),
        {
          wrapper: createWrapper('/documents/123?chunk=chunk-0-page-1'),
        }
      );

      await waitFor(() => {
        expect(onChunkNavigate).toHaveBeenCalledTimes(1);
      });

      // Rerender multiple times
      rerender();
      rerender();
      rerender();

      // Should still only be called once
      expect(onChunkNavigate).toHaveBeenCalledTimes(1);
    });

    test('handles error in initial navigation callback', async () => {
      vi.mocked(urlParamsModule.parseChunkFromUrl).mockReturnValue('chunk-0-page-1');
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const onChunkNavigate = vi.fn().mockImplementation(() => {
        throw new Error('Navigation error');
      });

      renderHook(
        () =>
          useChunkNavigation({
            onChunkNavigate,
          }),
        {
          wrapper: createWrapper('/documents/123?chunk=chunk-0-page-1'),
        }
      );

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          'Error in initial chunk navigation:',
          expect.any(Error)
        );
      });

      consoleSpy.mockRestore();
    });
  });

  // ============================================================================
  // Programmatic Navigation
  // ============================================================================

  describe('programmatic navigation', () => {
    test('navigateToChunk fires onChunkNavigate callback', () => {
      const onChunkNavigate = vi.fn();

      const { result } = renderHook(
        () =>
          useChunkNavigation({
            onChunkNavigate,
          }),
        {
          wrapper: createWrapper('/documents/123'),
        }
      );

      result.current.navigateToChunk('chunk-0-page-1');

      expect(onChunkNavigate).toHaveBeenCalledWith('chunk-0-page-1');
      expect(onChunkNavigate).toHaveBeenCalledTimes(1);
    });

    test('navigateToChunk trims whitespace from chunk ID', () => {
      const onChunkNavigate = vi.fn();

      const { result } = renderHook(
        () =>
          useChunkNavigation({
            onChunkNavigate,
          }),
        {
          wrapper: createWrapper('/documents/123'),
        }
      );

      result.current.navigateToChunk('  chunk-0-page-1  ');

      expect(onChunkNavigate).toHaveBeenCalledWith('chunk-0-page-1');
    });

    test('navigateToChunk does not update URL by default', () => {
      const onChunkNavigate = vi.fn();

      const { result } = renderHook(
        () =>
          useChunkNavigation({
            onChunkNavigate,
          }),
        {
          wrapper: createWrapper('/documents/123'),
        }
      );

      result.current.navigateToChunk('chunk-0-page-1');

      expect(urlParamsModule.updateChunkInUrl).not.toHaveBeenCalled();
    });

    test('navigateToChunk updates URL when updateUrl option is true', () => {
      const onChunkNavigate = vi.fn();

      const { result } = renderHook(
        () =>
          useChunkNavigation({
            onChunkNavigate,
            updateUrl: true,
          }),
        {
          wrapper: createWrapper('/documents/123'),
        }
      );

      result.current.navigateToChunk('chunk-0-page-1');

      expect(urlParamsModule.updateChunkInUrl).toHaveBeenCalledWith('chunk-0-page-1');
    });

    test('navigateToChunk updates URL when override parameter is true', () => {
      const onChunkNavigate = vi.fn();

      const { result } = renderHook(
        () =>
          useChunkNavigation({
            onChunkNavigate,
            updateUrl: false, // Default is false
          }),
        {
          wrapper: createWrapper('/documents/123'),
        }
      );

      result.current.navigateToChunk('chunk-0-page-1', true); // Override to true

      expect(urlParamsModule.updateChunkInUrl).toHaveBeenCalledWith('chunk-0-page-1');
    });

    test('navigateToChunk does not update URL when override parameter is false', () => {
      const onChunkNavigate = vi.fn();

      const { result } = renderHook(
        () =>
          useChunkNavigation({
            onChunkNavigate,
            updateUrl: true, // Default is true
          }),
        {
          wrapper: createWrapper('/documents/123'),
        }
      );

      result.current.navigateToChunk('chunk-0-page-1', false); // Override to false

      expect(urlParamsModule.updateChunkInUrl).not.toHaveBeenCalled();
    });

    test('navigateToChunk works without callback', () => {
      const { result } = renderHook(() => useChunkNavigation(), {
        wrapper: createWrapper('/documents/123'),
      });

      // Should not throw
      expect(() => {
        result.current.navigateToChunk('chunk-0-page-1');
      }).not.toThrow();
    });

    test('navigateToChunk can be called multiple times', () => {
      const onChunkNavigate = vi.fn();

      const { result } = renderHook(
        () =>
          useChunkNavigation({
            onChunkNavigate,
          }),
        {
          wrapper: createWrapper('/documents/123'),
        }
      );

      result.current.navigateToChunk('chunk-0-page-1');
      result.current.navigateToChunk('chunk-1-page-2');
      result.current.navigateToChunk('chunk-2-page-3');

      expect(onChunkNavigate).toHaveBeenCalledTimes(3);
      expect(onChunkNavigate).toHaveBeenNthCalledWith(1, 'chunk-0-page-1');
      expect(onChunkNavigate).toHaveBeenNthCalledWith(2, 'chunk-1-page-2');
      expect(onChunkNavigate).toHaveBeenNthCalledWith(3, 'chunk-2-page-3');
    });
  });

  // ============================================================================
  // Error Handling
  // ============================================================================

  describe('error handling', () => {
    test('warns when navigating to empty chunk ID', () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      const onChunkNavigate = vi.fn();

      const { result } = renderHook(
        () =>
          useChunkNavigation({
            onChunkNavigate,
          }),
        {
          wrapper: createWrapper('/documents/123'),
        }
      );

      result.current.navigateToChunk('');

      expect(consoleSpy).toHaveBeenCalledWith('Cannot navigate to empty chunk ID');
      expect(onChunkNavigate).not.toHaveBeenCalled();

      consoleSpy.mockRestore();
    });

    test('warns when navigating to whitespace-only chunk ID', () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      const onChunkNavigate = vi.fn();

      const { result } = renderHook(
        () =>
          useChunkNavigation({
            onChunkNavigate,
          }),
        {
          wrapper: createWrapper('/documents/123'),
        }
      );

      result.current.navigateToChunk('   ');

      expect(consoleSpy).toHaveBeenCalledWith('Cannot navigate to empty chunk ID');
      expect(onChunkNavigate).not.toHaveBeenCalled();

      consoleSpy.mockRestore();
    });

    test('handles error in onChunkNavigate callback', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const onChunkNavigate = vi.fn().mockImplementation(() => {
        throw new Error('Navigation error');
      });

      const { result } = renderHook(
        () =>
          useChunkNavigation({
            onChunkNavigate,
          }),
        {
          wrapper: createWrapper('/documents/123'),
        }
      );

      result.current.navigateToChunk('chunk-0-page-1');

      expect(consoleSpy).toHaveBeenCalledWith(
        'Error in onChunkNavigate callback:',
        expect.any(Error)
      );

      consoleSpy.mockRestore();
    });

    test('handles error when updating URL', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      vi.mocked(urlParamsModule.updateChunkInUrl).mockImplementation(() => {
        throw new Error('URL update error');
      });

      const { result } = renderHook(
        () =>
          useChunkNavigation({
            updateUrl: true,
          }),
        {
          wrapper: createWrapper('/documents/123'),
        }
      );

      result.current.navigateToChunk('chunk-0-page-1');

      expect(consoleSpy).toHaveBeenCalledWith('Error updating chunk in URL:', expect.any(Error));

      consoleSpy.mockRestore();
    });
  });

  // ============================================================================
  // React Router Integration
  // ============================================================================

  describe('React Router integration', () => {
    test('parses chunk from React Router search params', () => {
      const parseSpy = vi.mocked(urlParamsModule.parseChunkFromUrl);
      parseSpy.mockReturnValue('chunk-0-page-1');

      renderHook(() => useChunkNavigation(), {
        wrapper: createWrapper('/documents/123?chunk=chunk-0-page-1&foo=bar'),
      });

      // parseChunkFromUrl should be called with the search params string
      expect(parseSpy).toHaveBeenCalled();
      const callArg = parseSpy.mock.calls[0][0];
      expect(callArg).toContain('chunk=chunk-0-page-1');
    });

    test('works with nested routes', () => {
      vi.mocked(urlParamsModule.parseChunkFromUrl).mockReturnValue('chunk-0-page-1');
      const onChunkNavigate = vi.fn();

      function NestedWrapper({ children }: { children: React.ReactNode }) {
        return (
          <MemoryRouter initialEntries={['/documents/123/details?chunk=chunk-0-page-1']}>
            <Routes>
              <Route path="/documents/:id/details" element={<>{children}</>} />
            </Routes>
          </MemoryRouter>
        );
      }

      renderHook(
        () =>
          useChunkNavigation({
            onChunkNavigate,
          }),
        {
          wrapper: NestedWrapper,
        }
      );

      expect(onChunkNavigate).toHaveBeenCalledWith('chunk-0-page-1');
    });

    test('works with multiple search parameters', () => {
      vi.mocked(urlParamsModule.parseChunkFromUrl).mockReturnValue('chunk-0-page-1');

      const { result } = renderHook(() => useChunkNavigation(), {
        wrapper: createWrapper('/documents/123?search=test&chunk=chunk-0-page-1&page=1'),
      });

      expect(result.current.initialChunkId).toBe('chunk-0-page-1');
    });
  });

  // ============================================================================
  // Options Configuration
  // ============================================================================

  describe('options configuration', () => {
    test('works with no options provided', () => {
      const { result } = renderHook(() => useChunkNavigation(), {
        wrapper: createWrapper('/documents/123'),
      });

      expect(result.current.initialChunkId).toBe(null);
      expect(typeof result.current.navigateToChunk).toBe('function');
    });

    test('works with empty options object', () => {
      const { result } = renderHook(() => useChunkNavigation({}), {
        wrapper: createWrapper('/documents/123'),
      });

      expect(result.current.initialChunkId).toBe(null);
      expect(typeof result.current.navigateToChunk).toBe('function');
    });

    test('respects onChunkNavigate option', async () => {
      vi.mocked(urlParamsModule.parseChunkFromUrl).mockReturnValue('chunk-0-page-1');
      const onChunkNavigate = vi.fn();

      renderHook(
        () =>
          useChunkNavigation({
            onChunkNavigate,
          }),
        {
          wrapper: createWrapper('/documents/123?chunk=chunk-0-page-1'),
        }
      );

      await waitFor(() => {
        expect(onChunkNavigate).toHaveBeenCalled();
      });
    });

    test('respects updateUrl option', () => {
      const { result } = renderHook(
        () =>
          useChunkNavigation({
            updateUrl: true,
          }),
        {
          wrapper: createWrapper('/documents/123'),
        }
      );

      result.current.navigateToChunk('chunk-0-page-1');

      expect(urlParamsModule.updateChunkInUrl).toHaveBeenCalled();
    });

    test('callback can be updated between renders', async () => {
      vi.mocked(urlParamsModule.parseChunkFromUrl).mockReturnValue(null);
      const firstCallback = vi.fn();
      const secondCallback = vi.fn();

      const { result, rerender } = renderHook(
        (props: UseChunkNavigationOptions) => useChunkNavigation(props),
        {
          wrapper: createWrapper('/documents/123'),
          initialProps: { onChunkNavigate: firstCallback },
        }
      );

      result.current.navigateToChunk('chunk-0-page-1');
      expect(firstCallback).toHaveBeenCalledWith('chunk-0-page-1');
      expect(secondCallback).not.toHaveBeenCalled();

      // Update the callback
      rerender({ onChunkNavigate: secondCallback });

      result.current.navigateToChunk('chunk-1-page-2');
      expect(secondCallback).toHaveBeenCalledWith('chunk-1-page-2');
      expect(firstCallback).toHaveBeenCalledTimes(1); // Still only called once
    });
  });

  // ============================================================================
  // Real-World Scenarios
  // ============================================================================

  describe('real-world scenarios', () => {
    test('handles complete workflow: mount with chunk, navigate to new chunk', async () => {
      vi.mocked(urlParamsModule.parseChunkFromUrl).mockReturnValue('chunk-0-page-1');
      const onChunkNavigate = vi.fn();

      const { result } = renderHook(
        () =>
          useChunkNavigation({
            onChunkNavigate,
            updateUrl: true,
          }),
        {
          wrapper: createWrapper('/documents/123?chunk=chunk-0-page-1'),
        }
      );

      // Initial navigation should fire
      await waitFor(() => {
        expect(onChunkNavigate).toHaveBeenCalledWith('chunk-0-page-1');
      });

      // Navigate to new chunk
      result.current.navigateToChunk('chunk-1-page-2');

      expect(onChunkNavigate).toHaveBeenCalledWith('chunk-1-page-2');
      expect(urlParamsModule.updateChunkInUrl).toHaveBeenCalledWith('chunk-1-page-2');
      expect(onChunkNavigate).toHaveBeenCalledTimes(2);
    });

    test('handles scroll and highlight use case', async () => {
      vi.mocked(urlParamsModule.parseChunkFromUrl).mockReturnValue('chunk-0-page-1');
      const scrollToChunk = vi.fn();
      const setActiveChunk = vi.fn();

      const { result } = renderHook(
        () =>
          useChunkNavigation({
            onChunkNavigate: (chunkId) => {
              scrollToChunk(chunkId);
              setActiveChunk(chunkId);
            },
            updateUrl: true,
          }),
        {
          wrapper: createWrapper('/documents/123?chunk=chunk-0-page-1'),
        }
      );

      // Initial chunk should trigger scroll and highlight
      await waitFor(() => {
        expect(scrollToChunk).toHaveBeenCalledWith('chunk-0-page-1');
        expect(setActiveChunk).toHaveBeenCalledWith('chunk-0-page-1');
      });

      // User clicks on different chunk
      result.current.navigateToChunk('chunk-2-page-3');

      expect(scrollToChunk).toHaveBeenCalledWith('chunk-2-page-3');
      expect(setActiveChunk).toHaveBeenCalledWith('chunk-2-page-3');
      expect(urlParamsModule.updateChunkInUrl).toHaveBeenCalledWith('chunk-2-page-3');
    });

    test('handles deep linking from external source', async () => {
      vi.mocked(urlParamsModule.parseChunkFromUrl).mockReturnValue('chunk-5-page-10');
      const onChunkNavigate = vi.fn();

      renderHook(
        () =>
          useChunkNavigation({
            onChunkNavigate,
          }),
        {
          wrapper: createWrapper('/documents/123?chunk=chunk-5-page-10&source=email'),
        }
      );

      await waitFor(() => {
        expect(onChunkNavigate).toHaveBeenCalledWith('chunk-5-page-10');
      });
    });

    test('handles navigation with URL update off, then on', () => {
      const onChunkNavigate = vi.fn();

      const { result } = renderHook(
        () =>
          useChunkNavigation({
            onChunkNavigate,
            updateUrl: false,
          }),
        {
          wrapper: createWrapper('/documents/123'),
        }
      );

      // First navigation without URL update
      result.current.navigateToChunk('chunk-0-page-1');
      expect(urlParamsModule.updateChunkInUrl).not.toHaveBeenCalled();

      // Second navigation with URL update override
      result.current.navigateToChunk('chunk-1-page-2', true);
      expect(urlParamsModule.updateChunkInUrl).toHaveBeenCalledWith('chunk-1-page-2');
    });
  });
});

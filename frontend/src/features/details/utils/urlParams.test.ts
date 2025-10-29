/**
 * URL Parameter Utilities Tests
 *
 * Agent 10: URL Parameter Chunk Navigation
 * Wave 1 - BBox Overlay React Implementation
 *
 * Comprehensive test suite covering:
 * - URL parsing with various formats
 * - Parameter extraction and validation
 * - URL manipulation (add, update, remove)
 * - History API integration
 * - Edge cases and error handling
 *
 * Target: 100% code coverage
 */

import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  parseChunkFromUrl,
  updateChunkInUrl,
  removeChunkFromUrl,
  hasChunkInUrl,
  buildUrlWithChunk,
} from './urlParams';

// ============================================================================
// Test Setup
// ============================================================================

describe('urlParams', () => {
  // Store original location and history
  const originalLocation = window.location;
  const originalHistory = window.history;

  beforeEach(() => {
    // Mock window.location
    delete (window as any).location;
    (window as any).location = {
      href: 'http://localhost:3000/documents/123',
      search: '',
      pathname: '/documents/123',
      origin: 'http://localhost:3000',
    };

    // Mock window.history
    window.history.replaceState = vi.fn();
    window.history.pushState = vi.fn();

    // Clear console spies
    vi.clearAllMocks();
  });

  afterEach(() => {
    // Restore original location and history
    window.location = originalLocation;
    window.history = originalHistory;
  });

  // ============================================================================
  // parseChunkFromUrl Tests
  // ============================================================================

  describe('parseChunkFromUrl', () => {
    describe('valid chunk parameters', () => {
      test('parses chunk parameter from URL', () => {
        const result = parseChunkFromUrl('?chunk=chunk-0-page-1');
        expect(result).toBe('chunk-0-page-1');
      });

      test('parses chunk with complex ID format', () => {
        const result = parseChunkFromUrl('?chunk=doc-123-chunk-5-page-10');
        expect(result).toBe('doc-123-chunk-5-page-10');
      });

      test('parses chunk with numeric ID', () => {
        const result = parseChunkFromUrl('?chunk=42');
        expect(result).toBe('42');
      });

      test('parses chunk with UUID format', () => {
        const result = parseChunkFromUrl('?chunk=550e8400-e29b-41d4-a716-446655440000');
        expect(result).toBe('550e8400-e29b-41d4-a716-446655440000');
      });

      test('parses chunk with underscores', () => {
        const result = parseChunkFromUrl('?chunk=chunk_0_page_1');
        expect(result).toBe('chunk_0_page_1');
      });

      test('parses chunk with special characters', () => {
        const result = parseChunkFromUrl('?chunk=chunk-0_page.1');
        expect(result).toBe('chunk-0_page.1');
      });

      test('trims whitespace from chunk ID', () => {
        const result = parseChunkFromUrl('?chunk=  chunk-0-page-1  ');
        expect(result).toBe('chunk-0-page-1');
      });
    });

    describe('chunk parameter with other parameters', () => {
      test('extracts chunk when first parameter', () => {
        const result = parseChunkFromUrl('?chunk=chunk-0-page-1&foo=bar');
        expect(result).toBe('chunk-0-page-1');
      });

      test('extracts chunk when last parameter', () => {
        const result = parseChunkFromUrl('?foo=bar&chunk=chunk-0-page-1');
        expect(result).toBe('chunk-0-page-1');
      });

      test('extracts chunk when middle parameter', () => {
        const result = parseChunkFromUrl('?foo=bar&chunk=chunk-0-page-1&baz=qux');
        expect(result).toBe('chunk-0-page-1');
      });

      test('ignores other parameters', () => {
        const result = parseChunkFromUrl('?search=test&page=1&chunk=chunk-0-page-1&sort=asc');
        expect(result).toBe('chunk-0-page-1');
      });
    });

    describe('missing or invalid chunk parameters', () => {
      test('returns null when chunk parameter missing', () => {
        const result = parseChunkFromUrl('?foo=bar');
        expect(result).toBe(null);
      });

      test('returns null for empty search string', () => {
        const result = parseChunkFromUrl('');
        expect(result).toBe(null);
      });

      test('returns null when chunk parameter is empty', () => {
        const result = parseChunkFromUrl('?chunk=');
        expect(result).toBe(null);
      });

      test('returns null when chunk parameter is whitespace only', () => {
        const result = parseChunkFromUrl('?chunk=   ');
        expect(result).toBe(null);
      });

      test('returns null for search string with only question mark', () => {
        const result = parseChunkFromUrl('?');
        expect(result).toBe(null);
      });

      test('handles URL without question mark', () => {
        const result = parseChunkFromUrl('foo=bar');
        expect(result).toBe(null);
      });
    });

    describe('edge cases and error handling', () => {
      test('handles malformed URL parameters gracefully', () => {
        const result = parseChunkFromUrl('?chunk=value&&&foo=bar');
        expect(result).toBe('value');
      });

      test('handles duplicate chunk parameters (uses first)', () => {
        const result = parseChunkFromUrl('?chunk=first&chunk=second');
        expect(result).toBe('first');
      });

      test('handles URL-encoded chunk ID', () => {
        const result = parseChunkFromUrl('?chunk=chunk%2D0%2Dpage%2D1');
        expect(result).toBe('chunk-0-page-1');
      });

      test('handles chunk with spaces (URL-encoded)', () => {
        const result = parseChunkFromUrl('?chunk=chunk%200%20page%201');
        expect(result).toBe('chunk 0 page 1');
      });

      test('handles very long chunk ID', () => {
        const longId = 'a'.repeat(1000);
        const result = parseChunkFromUrl(`?chunk=${longId}`);
        expect(result).toBe(longId);
      });
    });
  });

  // ============================================================================
  // updateChunkInUrl Tests
  // ============================================================================

  describe('updateChunkInUrl', () => {
    describe('basic URL updates', () => {
      test('adds chunk parameter to URL without existing params', () => {
        window.location.search = '';
        updateChunkInUrl('chunk-0-page-1');

        expect(window.history.replaceState).toHaveBeenCalledWith(
          null,
          '',
          'http://localhost:3000/documents/123?chunk=chunk-0-page-1'
        );
      });

      test('adds chunk parameter to URL with existing params', () => {
        window.location.href = 'http://localhost:3000/documents/123?foo=bar';
        window.location.search = '?foo=bar';
        updateChunkInUrl('chunk-0-page-1');

        expect(window.history.replaceState).toHaveBeenCalledWith(
          null,
          '',
          'http://localhost:3000/documents/123?foo=bar&chunk=chunk-0-page-1'
        );
      });

      test('updates existing chunk parameter', () => {
        window.location.href = 'http://localhost:3000/documents/123?chunk=old-chunk';
        window.location.search = '?chunk=old-chunk';
        updateChunkInUrl('new-chunk');

        expect(window.history.replaceState).toHaveBeenCalledWith(
          null,
          '',
          'http://localhost:3000/documents/123?chunk=new-chunk'
        );
      });

      test('preserves other parameters when updating chunk', () => {
        window.location.href = 'http://localhost:3000/documents/123?foo=bar&chunk=old&baz=qux';
        window.location.search = '?foo=bar&chunk=old&baz=qux';
        updateChunkInUrl('new-chunk');

        expect(window.history.replaceState).toHaveBeenCalledWith(
          null,
          '',
          'http://localhost:3000/documents/123?foo=bar&chunk=new-chunk&baz=qux'
        );
      });

      test('trims whitespace from chunk ID', () => {
        updateChunkInUrl('  chunk-0-page-1  ');

        expect(window.history.replaceState).toHaveBeenCalledWith(
          null,
          '',
          'http://localhost:3000/documents/123?chunk=chunk-0-page-1'
        );
      });
    });

    describe('preserves URL structure', () => {
      test('preserves pathname', () => {
        window.location.pathname = '/documents/456/details';
        window.location.href = 'http://localhost:3000/documents/456/details';
        updateChunkInUrl('chunk-0-page-1');

        expect(window.history.replaceState).toHaveBeenCalledWith(
          null,
          '',
          'http://localhost:3000/documents/456/details?chunk=chunk-0-page-1'
        );
      });

      test('preserves hash fragment', () => {
        window.location.href = 'http://localhost:3000/documents/123#section';
        updateChunkInUrl('chunk-0-page-1');

        const callArgs = (window.history.replaceState as any).mock.calls[0];
        expect(callArgs[2]).toContain('chunk=chunk-0-page-1');
        expect(callArgs[2]).toContain('#section');
      });

      test('preserves complex query parameters', () => {
        window.location.href = 'http://localhost:3000/documents/123?search=test&page=1&sort=asc';
        window.location.search = '?search=test&page=1&sort=asc';
        updateChunkInUrl('chunk-0-page-1');

        const callArgs = (window.history.replaceState as any).mock.calls[0];
        expect(callArgs[2]).toContain('search=test');
        expect(callArgs[2]).toContain('page=1');
        expect(callArgs[2]).toContain('sort=asc');
        expect(callArgs[2]).toContain('chunk=chunk-0-page-1');
      });
    });

    describe('error handling', () => {
      test('does not update URL with empty chunk ID', () => {
        const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

        updateChunkInUrl('');

        expect(window.history.replaceState).not.toHaveBeenCalled();
        expect(consoleSpy).toHaveBeenCalledWith('Cannot update URL with empty chunk ID');

        consoleSpy.mockRestore();
      });

      test('does not update URL with whitespace-only chunk ID', () => {
        const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

        updateChunkInUrl('   ');

        expect(window.history.replaceState).not.toHaveBeenCalled();
        expect(consoleSpy).toHaveBeenCalledWith('Cannot update URL with empty chunk ID');

        consoleSpy.mockRestore();
      });

      test('handles error during URL update', () => {
        const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
        window.history.replaceState = vi.fn().mockImplementation(() => {
          throw new Error('History API error');
        });

        updateChunkInUrl('chunk-0-page-1');

        expect(consoleSpy).toHaveBeenCalled();
        consoleSpy.mockRestore();
      });
    });

    describe('uses replaceState (not pushState)', () => {
      test('uses replaceState to avoid adding to history', () => {
        updateChunkInUrl('chunk-0-page-1');

        expect(window.history.replaceState).toHaveBeenCalled();
        expect(window.history.pushState).not.toHaveBeenCalled();
      });
    });
  });

  // ============================================================================
  // removeChunkFromUrl Tests
  // ============================================================================

  describe('removeChunkFromUrl', () => {
    describe('basic removal', () => {
      test('removes chunk parameter from URL', () => {
        window.location.href = 'http://localhost:3000/documents/123?chunk=chunk-0-page-1';
        window.location.search = '?chunk=chunk-0-page-1';
        removeChunkFromUrl();

        expect(window.history.replaceState).toHaveBeenCalledWith(
          null,
          '',
          'http://localhost:3000/documents/123'
        );
      });

      test('removes chunk while preserving other parameters', () => {
        window.location.href = 'http://localhost:3000/documents/123?foo=bar&chunk=chunk-0-page-1&baz=qux';
        window.location.search = '?foo=bar&chunk=chunk-0-page-1&baz=qux';
        removeChunkFromUrl();

        expect(window.history.replaceState).toHaveBeenCalledWith(
          null,
          '',
          'http://localhost:3000/documents/123?foo=bar&baz=qux'
        );
      });

      test('handles URL without chunk parameter (no-op)', () => {
        window.location.href = 'http://localhost:3000/documents/123?foo=bar';
        window.location.search = '?foo=bar';
        removeChunkFromUrl();

        expect(window.history.replaceState).toHaveBeenCalledWith(
          null,
          '',
          'http://localhost:3000/documents/123?foo=bar'
        );
      });

      test('handles URL without any parameters (no-op)', () => {
        removeChunkFromUrl();

        expect(window.history.replaceState).toHaveBeenCalledWith(
          null,
          '',
          'http://localhost:3000/documents/123'
        );
      });
    });

    describe('preserves URL structure', () => {
      test('preserves pathname', () => {
        window.location.pathname = '/documents/456/details';
        window.location.href = 'http://localhost:3000/documents/456/details?chunk=chunk-0-page-1';
        window.location.search = '?chunk=chunk-0-page-1';
        removeChunkFromUrl();

        expect(window.history.replaceState).toHaveBeenCalledWith(
          null,
          '',
          'http://localhost:3000/documents/456/details'
        );
      });

      test('preserves hash fragment', () => {
        window.location.href = 'http://localhost:3000/documents/123?chunk=chunk-0-page-1#section';
        window.location.search = '?chunk=chunk-0-page-1';
        removeChunkFromUrl();

        const callArgs = (window.history.replaceState as any).mock.calls[0];
        expect(callArgs[2]).toContain('#section');
        expect(callArgs[2]).not.toContain('chunk=');
      });

      test('preserves other query parameters', () => {
        window.location.href = 'http://localhost:3000/documents/123?search=test&chunk=chunk-0-page-1&page=1';
        window.location.search = '?search=test&chunk=chunk-0-page-1&page=1';
        removeChunkFromUrl();

        const callArgs = (window.history.replaceState as any).mock.calls[0];
        expect(callArgs[2]).toContain('search=test');
        expect(callArgs[2]).toContain('page=1');
        expect(callArgs[2]).not.toContain('chunk=');
      });
    });

    describe('error handling', () => {
      test('handles error during URL update', () => {
        const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
        window.history.replaceState = vi.fn().mockImplementation(() => {
          throw new Error('History API error');
        });

        removeChunkFromUrl();

        expect(consoleSpy).toHaveBeenCalled();
        consoleSpy.mockRestore();
      });
    });

    describe('uses replaceState (not pushState)', () => {
      test('uses replaceState to avoid adding to history', () => {
        removeChunkFromUrl();

        expect(window.history.replaceState).toHaveBeenCalled();
        expect(window.history.pushState).not.toHaveBeenCalled();
      });
    });
  });

  // ============================================================================
  // hasChunkInUrl Tests
  // ============================================================================

  describe('hasChunkInUrl', () => {
    describe('with explicit search parameter', () => {
      test('returns true when chunk parameter exists', () => {
        expect(hasChunkInUrl('?chunk=chunk-0-page-1')).toBe(true);
      });

      test('returns true when chunk exists with other parameters', () => {
        expect(hasChunkInUrl('?foo=bar&chunk=chunk-0-page-1')).toBe(true);
      });

      test('returns false when chunk parameter missing', () => {
        expect(hasChunkInUrl('?foo=bar')).toBe(false);
      });

      test('returns false when chunk parameter is empty', () => {
        expect(hasChunkInUrl('?chunk=')).toBe(false);
      });

      test('returns false for empty search string', () => {
        expect(hasChunkInUrl('')).toBe(false);
      });
    });

    describe('using window.location.search', () => {
      test('returns true when chunk in current URL', () => {
        window.location.search = '?chunk=chunk-0-page-1';
        expect(hasChunkInUrl()).toBe(true);
      });

      test('returns false when no chunk in current URL', () => {
        window.location.search = '?foo=bar';
        expect(hasChunkInUrl()).toBe(false);
      });

      test('returns false when URL has no parameters', () => {
        window.location.search = '';
        expect(hasChunkInUrl()).toBe(false);
      });
    });
  });

  // ============================================================================
  // buildUrlWithChunk Tests
  // ============================================================================

  describe('buildUrlWithChunk', () => {
    describe('basic URL construction', () => {
      test('builds URL with chunk parameter', () => {
        const result = buildUrlWithChunk('/documents/123', 'chunk-0-page-1');
        expect(result).toBe('/documents/123?chunk=chunk-0-page-1');
      });

      test('builds URL without leading slash', () => {
        const result = buildUrlWithChunk('documents/123', 'chunk-0-page-1');
        expect(result).toBe('documents/123?chunk=chunk-0-page-1');
      });

      test('builds URL with nested path', () => {
        const result = buildUrlWithChunk('/documents/123/details', 'chunk-0-page-1');
        expect(result).toBe('/documents/123/details?chunk=chunk-0-page-1');
      });

      test('trims whitespace from chunk ID', () => {
        const result = buildUrlWithChunk('/documents/123', '  chunk-0-page-1  ');
        expect(result).toBe('/documents/123?chunk=chunk-0-page-1');
      });
    });

    describe('with existing parameters', () => {
      test('adds chunk to existing parameters', () => {
        const params = new URLSearchParams('?foo=bar');
        const result = buildUrlWithChunk('/documents/123', 'chunk-0-page-1', params);

        expect(result).toContain('foo=bar');
        expect(result).toContain('chunk=chunk-0-page-1');
      });

      test('preserves multiple existing parameters', () => {
        const params = new URLSearchParams('?foo=bar&baz=qux');
        const result = buildUrlWithChunk('/documents/123', 'chunk-0-page-1', params);

        expect(result).toContain('foo=bar');
        expect(result).toContain('baz=qux');
        expect(result).toContain('chunk=chunk-0-page-1');
      });

      test('updates existing chunk parameter', () => {
        const params = new URLSearchParams('?chunk=old-chunk&foo=bar');
        const result = buildUrlWithChunk('/documents/123', 'new-chunk', params);

        expect(result).toContain('chunk=new-chunk');
        expect(result).not.toContain('chunk=old-chunk');
        expect(result).toContain('foo=bar');
      });

      test('handles empty URLSearchParams', () => {
        const params = new URLSearchParams();
        const result = buildUrlWithChunk('/documents/123', 'chunk-0-page-1', params);

        expect(result).toBe('/documents/123?chunk=chunk-0-page-1');
      });
    });

    describe('edge cases', () => {
      test('handles root pathname', () => {
        const result = buildUrlWithChunk('/', 'chunk-0-page-1');
        expect(result).toBe('/?chunk=chunk-0-page-1');
      });

      test('handles empty pathname', () => {
        const result = buildUrlWithChunk('', 'chunk-0-page-1');
        expect(result).toBe('?chunk=chunk-0-page-1');
      });

      test('handles pathname with trailing slash', () => {
        const result = buildUrlWithChunk('/documents/123/', 'chunk-0-page-1');
        expect(result).toBe('/documents/123/?chunk=chunk-0-page-1');
      });

      test('handles complex chunk ID', () => {
        const result = buildUrlWithChunk('/documents/123', 'doc-456-chunk-7-page-12');
        expect(result).toBe('/documents/123?chunk=doc-456-chunk-7-page-12');
      });

      test('handles chunk ID with special characters', () => {
        const result = buildUrlWithChunk('/documents/123', 'chunk_0-page.1');
        expect(result).toBe('/documents/123?chunk=chunk_0-page.1');
      });
    });
  });
});

/**
 * URL Builder Tests
 *
 * Agent 9: Research Navigation Enhancer
 * Wave 1 - BBox Overlay React Implementation
 */

import { describe, it, expect } from 'vitest';
import { buildDetailsUrl, hasChunkContext, DetailsLinkParams, SourceInfo } from '../urlBuilder';

describe('urlBuilder', () => {
  describe('buildDetailsUrl', () => {
    describe('basic functionality', () => {
      it('should build URL without chunk_id', () => {
        const params: DetailsLinkParams = {
          docId: 'abc123',
          page: 5,
        };

        const url = buildDetailsUrl(params);

        expect(url).toBe('/details/abc123?page=5');
      });

      it('should build URL with chunk_id', () => {
        const params: DetailsLinkParams = {
          docId: 'abc123',
          page: 5,
          chunkId: 'abc123-chunk0042',
        };

        const url = buildDetailsUrl(params);

        expect(url).toBe('/details/abc123?page=5&chunk=abc123-chunk0042');
      });

      it('should handle page 1', () => {
        const params: DetailsLinkParams = {
          docId: 'doc456',
          page: 1,
        };

        const url = buildDetailsUrl(params);

        expect(url).toBe('/details/doc456?page=1');
      });

      it('should handle large page numbers', () => {
        const params: DetailsLinkParams = {
          docId: 'doc789',
          page: 9999,
        };

        const url = buildDetailsUrl(params);

        expect(url).toBe('/details/doc789?page=9999');
      });
    });

    describe('chunk_id handling', () => {
      it('should trim whitespace from chunk_id', () => {
        const params: DetailsLinkParams = {
          docId: 'abc123',
          page: 5,
          chunkId: '  abc123-chunk0042  ',
        };

        const url = buildDetailsUrl(params);

        expect(url).toBe('/details/abc123?page=5&chunk=abc123-chunk0042');
      });

      it('should ignore empty chunk_id', () => {
        const params: DetailsLinkParams = {
          docId: 'abc123',
          page: 5,
          chunkId: '',
        };

        const url = buildDetailsUrl(params);

        expect(url).toBe('/details/abc123?page=5');
      });

      it('should ignore whitespace-only chunk_id', () => {
        const params: DetailsLinkParams = {
          docId: 'abc123',
          page: 5,
          chunkId: '   ',
        };

        const url = buildDetailsUrl(params);

        expect(url).toBe('/details/abc123?page=5');
      });

      it('should ignore undefined chunk_id', () => {
        const params: DetailsLinkParams = {
          docId: 'abc123',
          page: 5,
          chunkId: undefined,
        };

        const url = buildDetailsUrl(params);

        expect(url).toBe('/details/abc123?page=5');
      });

      it('should handle various chunk_id formats', () => {
        const testCases = [
          'abc123-chunk0001',
          'doc-id-with-dashes-chunk9999',
          'simple_chunk_format',
          'chunk-with-special_chars123',
        ];

        testCases.forEach((chunkId) => {
          const params: DetailsLinkParams = {
            docId: 'test-doc',
            page: 1,
            chunkId,
          };

          const url = buildDetailsUrl(params);

          expect(url).toContain(`chunk=${chunkId}`);
        });
      });
    });

    describe('special characters in docId', () => {
      it('should handle docId with dashes', () => {
        const params: DetailsLinkParams = {
          docId: 'doc-with-dashes-123',
          page: 1,
        };

        const url = buildDetailsUrl(params);

        expect(url).toBe('/details/doc-with-dashes-123?page=1');
      });

      it('should handle docId with underscores', () => {
        const params: DetailsLinkParams = {
          docId: 'doc_with_underscores_456',
          page: 1,
        };

        const url = buildDetailsUrl(params);

        expect(url).toBe('/details/doc_with_underscores_456?page=1');
      });

      it('should handle alphanumeric docId', () => {
        const params: DetailsLinkParams = {
          docId: 'AbC123XyZ789',
          page: 1,
        };

        const url = buildDetailsUrl(params);

        expect(url).toBe('/details/AbC123XyZ789?page=1');
      });
    });

    describe('validation and error cases', () => {
      it('should throw error for missing docId', () => {
        const params = {
          docId: '',
          page: 5,
        } as DetailsLinkParams;

        expect(() => buildDetailsUrl(params)).toThrow('docId is required and must be a string');
      });

      it('should throw error for non-string docId', () => {
        const params = {
          docId: 123 as any,
          page: 5,
        };

        expect(() => buildDetailsUrl(params)).toThrow('docId is required and must be a string');
      });

      it('should throw error for missing page', () => {
        const params = {
          docId: 'abc123',
          page: undefined as any,
        };

        expect(() => buildDetailsUrl(params)).toThrow('page is required and must be a positive number');
      });

      it('should throw error for non-number page', () => {
        const params = {
          docId: 'abc123',
          page: '5' as any,
        };

        expect(() => buildDetailsUrl(params)).toThrow('page is required and must be a positive number');
      });

      it('should throw error for zero page', () => {
        const params = {
          docId: 'abc123',
          page: 0,
        };

        expect(() => buildDetailsUrl(params)).toThrow('page is required and must be a positive number');
      });

      it('should throw error for negative page', () => {
        const params = {
          docId: 'abc123',
          page: -5,
        };

        expect(() => buildDetailsUrl(params)).toThrow('page is required and must be a positive number');
      });
    });

    describe('backward compatibility', () => {
      it('should work exactly like old format when chunk_id not provided', () => {
        const oldUrl = '/details/test-doc?page=10';
        const newUrl = buildDetailsUrl({ docId: 'test-doc', page: 10 });

        expect(newUrl).toBe(oldUrl);
      });

      it('should maintain query param format', () => {
        const url = buildDetailsUrl({ docId: 'doc123', page: 5 });

        // Should use query params, not path params for page
        expect(url).toContain('?page=');
        expect(url).not.toContain('/5');
      });
    });
  });

  describe('hasChunkContext', () => {
    const createSource = (overrides: Partial<SourceInfo> = {}): SourceInfo => ({
      id: 1,
      doc_id: 'test-doc',
      filename: 'test.pdf',
      page: 1,
      extension: 'pdf',
      date_added: '2024-10-28T00:00:00Z',
      relevance_score: 0.95,
      ...overrides,
    });

    describe('positive cases', () => {
      it('should return true for source with chunk_id', () => {
        const source = createSource({ chunk_id: 'abc123-chunk0042' });

        expect(hasChunkContext(source)).toBe(true);
      });

      it('should return true for various chunk_id formats', () => {
        const testCases = [
          'simple-chunk',
          'doc_id_chunk_0001',
          'complex-doc-id-123-chunk9999',
          'a', // single character
          'very-long-chunk-id-with-many-segments-and-numbers-12345',
        ];

        testCases.forEach((chunk_id) => {
          const source = createSource({ chunk_id });
          expect(hasChunkContext(source)).toBe(true);
        });
      });

      it('should return true after trimming whitespace', () => {
        const source = createSource({ chunk_id: '  valid-chunk  ' });

        expect(hasChunkContext(source)).toBe(true);
      });
    });

    describe('negative cases', () => {
      it('should return false for source without chunk_id', () => {
        const source = createSource({ chunk_id: undefined });

        expect(hasChunkContext(source)).toBe(false);
      });

      it('should return false for empty chunk_id', () => {
        const source = createSource({ chunk_id: '' });

        expect(hasChunkContext(source)).toBe(false);
      });

      it('should return false for whitespace-only chunk_id', () => {
        const source = createSource({ chunk_id: '   ' });

        expect(hasChunkContext(source)).toBe(false);
      });

      it('should return false for null chunk_id', () => {
        const source = createSource({ chunk_id: null as any });

        expect(hasChunkContext(source)).toBe(false);
      });
    });

    describe('type safety', () => {
      it('should handle sources from API correctly', () => {
        // Simulate API response
        const apiSource: SourceInfo = {
          id: 1,
          doc_id: 'abc123',
          filename: 'document.pdf',
          page: 5,
          extension: 'pdf',
          date_added: '2024-10-28T12:00:00Z',
          relevance_score: 0.92,
          chunk_id: 'abc123-chunk0042',
        };

        expect(hasChunkContext(apiSource)).toBe(true);
      });

      it('should handle sources without optional fields', () => {
        const minimalSource: SourceInfo = {
          id: 1,
          doc_id: 'abc123',
          filename: 'document.pdf',
          page: 5,
          extension: 'pdf',
          date_added: '2024-10-28T12:00:00Z',
          relevance_score: 0.92,
          // chunk_id omitted (undefined)
        };

        expect(hasChunkContext(minimalSource)).toBe(false);
      });
    });
  });

  describe('integration scenarios', () => {
    it('should work together for navigation flow', () => {
      const source: SourceInfo = {
        id: 1,
        doc_id: 'test-doc-123',
        filename: 'research-paper.pdf',
        page: 15,
        extension: 'pdf',
        date_added: '2024-10-28T12:00:00Z',
        relevance_score: 0.95,
        chunk_id: 'test-doc-123-chunk0042',
      };

      // Check if chunk context available
      const hasContext = hasChunkContext(source);
      expect(hasContext).toBe(true);

      // Build URL with chunk_id
      const url = buildDetailsUrl({
        docId: source.doc_id,
        page: source.page,
        chunkId: source.chunk_id,
      });

      expect(url).toBe('/details/test-doc-123?page=15&chunk=test-doc-123-chunk0042');
    });

    it('should handle fallback for sources without chunk_id', () => {
      const source: SourceInfo = {
        id: 1,
        doc_id: 'visual-doc',
        filename: 'image-heavy.pdf',
        page: 3,
        extension: 'pdf',
        date_added: '2024-10-28T12:00:00Z',
        relevance_score: 0.88,
        // No chunk_id for visual search results
      };

      // Check if chunk context available
      const hasContext = hasChunkContext(source);
      expect(hasContext).toBe(false);

      // Build URL without chunk_id
      const url = buildDetailsUrl({
        docId: source.doc_id,
        page: source.page,
        chunkId: source.chunk_id,
      });

      expect(url).toBe('/details/visual-doc?page=3');
    });
  });
});

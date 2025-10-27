/**
 * URL Utilities Tests
 *
 * Coverage-Gap-Agent - Wave 4, Task 23
 * Testing URL building functions for API and resources
 */

import { describe, test, expect } from 'vitest'
import {
  buildDocumentUrl,
  buildThumbnailUrl,
  buildPageImageUrl,
  buildCoverArtUrl,
  buildMarkdownUrl,
  buildVTTUrl,
  buildAudioUrl,
  buildSearchUrl,
} from '../url'

describe('buildDocumentUrl', () => {
  test('builds correct document detail URL', () => {
    expect(buildDocumentUrl('abc123')).toBe('/details/abc123')
  })

  test('handles document IDs with special characters', () => {
    expect(buildDocumentUrl('doc-123-abc_DEF')).toBe('/details/doc-123-abc_DEF')
  })

  test('handles empty document ID', () => {
    expect(buildDocumentUrl('')).toBe('/details/')
  })
})

describe('buildThumbnailUrl', () => {
  test('builds thumbnail URL with default page', () => {
    expect(buildThumbnailUrl('doc123')).toBe('/api/documents/doc123/thumbnail?page=1')
  })

  test('builds thumbnail URL with specific page', () => {
    expect(buildThumbnailUrl('doc123', 5)).toBe('/api/documents/doc123/thumbnail?page=5')
  })

  test('builds thumbnail URL with page 0', () => {
    expect(buildThumbnailUrl('doc123', 0)).toBe('/api/documents/doc123/thumbnail?page=0')
  })

  test('handles large page numbers', () => {
    expect(buildThumbnailUrl('doc123', 999)).toBe('/api/documents/doc123/thumbnail?page=999')
  })
})

describe('buildPageImageUrl', () => {
  test('builds page image URL correctly', () => {
    expect(buildPageImageUrl('doc123', 1)).toBe('/api/documents/doc123/pages/1')
  })

  test('builds page image URL for different pages', () => {
    expect(buildPageImageUrl('doc456', 10)).toBe('/api/documents/doc456/pages/10')
  })

  test('handles page 0', () => {
    expect(buildPageImageUrl('doc789', 0)).toBe('/api/documents/doc789/pages/0')
  })
})

describe('buildCoverArtUrl', () => {
  test('builds cover art URL correctly', () => {
    expect(buildCoverArtUrl('audio123')).toBe('/api/documents/audio123/cover-art')
  })

  test('handles different document IDs', () => {
    expect(buildCoverArtUrl('podcast-ep-01')).toBe('/api/documents/podcast-ep-01/cover-art')
  })
})

describe('buildMarkdownUrl', () => {
  test('builds markdown download URL correctly', () => {
    expect(buildMarkdownUrl('doc123')).toBe('/documents/doc123/markdown')
  })

  test('handles different document IDs', () => {
    expect(buildMarkdownUrl('report-2025')).toBe('/documents/report-2025/markdown')
  })
})

describe('buildVTTUrl', () => {
  test('builds VTT captions URL correctly', () => {
    expect(buildVTTUrl('audio123')).toBe('/documents/audio123/vtt')
  })

  test('handles different document IDs', () => {
    expect(buildVTTUrl('lecture-recording')).toBe('/documents/lecture-recording/vtt')
  })
})

describe('buildAudioUrl', () => {
  test('builds audio source URL correctly', () => {
    expect(buildAudioUrl('audio123')).toBe('/documents/audio123/audio')
  })

  test('handles different document IDs', () => {
    expect(buildAudioUrl('podcast-001')).toBe('/documents/podcast-001/audio')
  })
})

describe('buildSearchUrl', () => {
  test('builds search URL with query only', () => {
    const url = buildSearchUrl('test query')
    expect(url).toBe('/api/search?query=test+query')
  })

  test('builds search URL with query and limit', () => {
    const url = buildSearchUrl('test', { limit: 10 })
    expect(url).toContain('query=test')
    expect(url).toContain('limit=10')
  })

  test('builds search URL with query and offset', () => {
    const url = buildSearchUrl('test', { offset: 20 })
    expect(url).toContain('query=test')
    expect(url).toContain('offset=20')
  })

  test('builds search URL with all options', () => {
    const url = buildSearchUrl('test query', { limit: 50, offset: 100 })
    expect(url).toContain('query=test+query')
    expect(url).toContain('limit=50')
    expect(url).toContain('offset=100')
  })

  test('handles empty query', () => {
    const url = buildSearchUrl('', { limit: 10 })
    expect(url).toBe('/api/search?limit=10')
  })

  test('handles null query', () => {
    const url = buildSearchUrl(null, { limit: 10 })
    expect(url).toBe('/api/search?limit=10')
  })

  test('handles undefined query', () => {
    const url = buildSearchUrl(undefined, { limit: 10 })
    expect(url).toBe('/api/search?limit=10')
  })

  test('encodes special characters in query', () => {
    const url = buildSearchUrl('test&query=value', { limit: 10 })
    expect(url).toContain('query=test%26query%3Dvalue')
  })

  test('handles empty options object', () => {
    const url = buildSearchUrl('test')
    expect(url).toBe('/api/search?query=test')
  })

  test('ignores invalid option properties', () => {
    const url = buildSearchUrl('test', { invalid: 'value', limit: 10 })
    expect(url).toContain('query=test')
    expect(url).toContain('limit=10')
    expect(url).not.toContain('invalid')
  })

  test('handles zero values for limit and offset', () => {
    const url = buildSearchUrl('test', { limit: 0, offset: 0 })
    expect(url).not.toContain('limit')
    expect(url).not.toContain('offset')
  })
})

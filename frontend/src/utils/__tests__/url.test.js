/**
 * URL Utilities Tests
 *
 * NOTE: Most URL building functions removed as they were unused.
 * Backend now provides ready-to-use URLs in API responses.
 * Only navigation-related utilities remain.
 */

import { describe, test, expect } from 'vitest'
import {
  buildDocumentUrl,
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

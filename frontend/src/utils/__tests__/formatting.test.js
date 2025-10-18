/**
 * Formatting Utilities Tests
 *
 * Wave 1 - Foundation Agent
 */

import { describe, test, expect } from 'vitest'
import {
  formatDate,
  formatFileSize,
  formatDuration,
  formatTimestamp,
  formatRelativeTime
} from '../formatting'

describe('formatDate', () => {
  test('formats date string correctly', () => {
    const result = formatDate('2025-01-15T10:30:00Z')
    expect(result).toBe('Jan 15, 2025')
  })

  test('handles invalid date', () => {
    expect(formatDate('invalid')).toBe('')
  })

  test('handles null/undefined', () => {
    expect(formatDate(null)).toBe('')
    expect(formatDate(undefined)).toBe('')
  })
})

describe('formatFileSize', () => {
  test('formats bytes correctly', () => {
    expect(formatFileSize(0)).toBe('0 B')
    expect(formatFileSize(500)).toBe('500 B')
    expect(formatFileSize(1024)).toBe('1.0 KB')
    expect(formatFileSize(1048576)).toBe('1.0 MB')
    expect(formatFileSize(1572864)).toBe('1.5 MB')
    expect(formatFileSize(1073741824)).toBe('1.0 GB')
  })

  test('handles null/undefined', () => {
    expect(formatFileSize(null)).toBe('0 B')
    expect(formatFileSize(undefined)).toBe('0 B')
  })
})

describe('formatDuration', () => {
  test('formats short durations (< 1 hour)', () => {
    expect(formatDuration(30)).toBe('0:30')
    expect(formatDuration(90)).toBe('1:30')
    expect(formatDuration(600)).toBe('10:00')
  })

  test('formats long durations (>= 1 hour)', () => {
    expect(formatDuration(3600)).toBe('1:00:00')
    expect(formatDuration(9255)).toBe('2:34:15')
  })

  test('handles invalid input', () => {
    expect(formatDuration(0)).toBe('0:00')
    expect(formatDuration(null)).toBe('0:00')
    expect(formatDuration(undefined)).toBe('0:00')
  })
})

describe('formatTimestamp', () => {
  test('always formats with hours', () => {
    expect(formatTimestamp(30)).toBe('00:00:30')
    expect(formatTimestamp(90)).toBe('00:01:30')
    expect(formatTimestamp(3600)).toBe('01:00:00')
    expect(formatTimestamp(5025)).toBe('01:23:45')
  })

  test('handles invalid input', () => {
    expect(formatTimestamp(0)).toBe('00:00:00')
    expect(formatTimestamp(null)).toBe('00:00:00')
  })
})

describe('formatRelativeTime', () => {
  test('formats recent times', () => {
    const now = new Date()
    const justNow = new Date(now.getTime() - 30 * 1000)
    expect(formatRelativeTime(justNow.toISOString())).toBe('just now')
  })

  test('handles invalid date', () => {
    expect(formatRelativeTime('invalid')).toBe('')
    expect(formatRelativeTime(null)).toBe('')
  })
})

/**
 * Vitest global test setup
 *
 * This file runs before each test file and sets up the testing environment.
 * It configures jsdom, imports global test utilities, and sets up custom matchers.
 */

import { expect, afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import '@testing-library/jest-dom'

// Cleanup after each test case (e.g., clearing jsdom)
afterEach(() => {
  cleanup()
})

// Mock window.matchMedia (used by some components for responsive behavior)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock IntersectionObserver (used for lazy loading)
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() {
    return []
  }
  unobserve() {}
}

// Mock ResizeObserver (used for responsive components)
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
}

// Mock scrollTo for HTMLElement (used for smooth scrolling)
if (typeof Element !== 'undefined' && !Element.prototype.scrollTo) {
  Element.prototype.scrollTo = vi.fn()
}
if (typeof Window !== 'undefined' && !window.scrollTo) {
  window.scrollTo = vi.fn()
}

// Mock fetch if not available in test environment
if (typeof global.fetch === 'undefined') {
  global.fetch = vi.fn()
}

// Suppress console errors during tests (optional - uncomment if needed)
// const originalError = console.error
// beforeAll(() => {
//   console.error = (...args) => {
//     if (
//       typeof args[0] === 'string' &&
//       args[0].includes('Warning: ReactDOM.render')
//     ) {
//       return
//     }
//     originalError.call(console, ...args)
//   }
// })
//
// afterAll(() => {
//   console.error = originalError
// })

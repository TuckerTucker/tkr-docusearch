/**
 * Frontend test utilities for tkr-docusearch.
 *
 * This module provides reusable test utilities including:
 * - Custom render functions with providers
 * - Mock data factories
 * - Async utilities
 * - Common assertions
 *
 * @module tests/utils/testHelpers
 */

import { render } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { vi } from 'vitest'

/**
 * Custom render function that wraps component with all necessary providers.
 *
 * Includes:
 * - React Router (BrowserRouter)
 * - React Query (QueryClientProvider)
 *
 * @param {React.ReactElement} ui - Component to render
 * @param {Object} options - Render options
 * @param {Object} options.initialEntries - Initial router entries
 * @param {Object} options.queryClientConfig - Query client configuration
 * @param {Object} options.renderOptions - Additional render options
 * @returns {Object} Render result with additional utilities
 *
 * @example
 * const { getByText } = renderWithProviders(<MyComponent />)
 * expect(getByText('Hello')).toBeInTheDocument()
 */
export function renderWithProviders(
  ui,
  {
    initialEntries = ['/'],
    queryClientConfig = {},
    ...renderOptions
  } = {}
) {
  // Create a new QueryClient for each test to ensure isolation
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false, // Disable retries in tests
        cacheTime: 0, // Disable cache
        staleTime: 0,
        ...queryClientConfig?.queries,
      },
      mutations: {
        retry: false,
        ...queryClientConfig?.mutations,
      },
    },
    ...queryClientConfig,
  })

  /**
   * Wrapper component with all providers
   */
  function Wrapper({ children }) {
    return (
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </BrowserRouter>
    )
  }

  const result = render(ui, { wrapper: Wrapper, ...renderOptions })

  return {
    ...result,
    queryClient, // Expose query client for assertions
  }
}

/**
 * Create mock document data for testing.
 *
 * @param {Object} overrides - Properties to override
 * @returns {Object} Mock document object
 *
 * @example
 * const doc = createMockDocument({ filename: 'custom.pdf', pages: 10 })
 */
export function createMockDocument(overrides = {}) {
  return {
    id: 'doc001',
    filename: 'sample-document.pdf',
    uploadDate: new Date('2023-10-01').toISOString(),
    pages: 5,
    size: 1024 * 500, // 500 KB
    status: 'processed',
    thumbnail: '/data/thumbnails/doc001/page_001.jpg',
    metadata: {
      author: 'Test Author',
      title: 'Sample Document',
      createdDate: '2023-10-01',
    },
    ...overrides,
  }
}

/**
 * Create mock search result data for testing.
 *
 * @param {Object} overrides - Properties to override
 * @returns {Object} Mock search result object
 *
 * @example
 * const result = createMockSearchResult({ score: 0.95, page: 3 })
 */
export function createMockSearchResult(overrides = {}) {
  return {
    id: 'doc001-page001',
    docId: 'doc001',
    filename: 'sample-document.pdf',
    page: 1,
    score: 0.85,
    type: 'visual',
    thumbnail: '/data/thumbnails/doc001/page_001.jpg',
    imagePath: '/data/images/doc001/page_001.png',
    metadata: {
      uploadDate: '2023-10-01T00:00:00Z',
      fileSize: 512000,
    },
    ...overrides,
  }
}

/**
 * Create multiple mock search results.
 *
 * @param {number} count - Number of results to create
 * @param {Object} baseOverrides - Base properties to apply to all results
 * @returns {Array<Object>} Array of mock search results
 *
 * @example
 * const results = createMockSearchResults(10)
 * expect(results).toHaveLength(10)
 */
export function createMockSearchResults(count = 10, baseOverrides = {}) {
  return Array.from({ length: count }, (_, i) => {
    const docNum = Math.floor(i / 3) + 1
    const page = (i % 3) + 1
    const score = Math.max(0.5, 0.95 - i * 0.05)

    return createMockSearchResult({
      id: `doc${docNum.toString().padStart(3, '0')}-page${page.toString().padStart(3, '0')}`,
      docId: `doc${docNum.toString().padStart(3, '0')}`,
      filename: `document-${docNum}.pdf`,
      page,
      score,
      ...baseOverrides,
    })
  })
}

/**
 * Create mock research report data.
 *
 * @param {Object} overrides - Properties to override
 * @returns {Object} Mock research report object
 *
 * @example
 * const report = createMockResearchReport({ question: 'Custom question?' })
 */
export function createMockResearchReport(overrides = {}) {
  return {
    question: 'What are the quarterly earnings?',
    answer: 'The quarterly earnings showed significant growth...',
    sources: [
      {
        id: 'doc001-page001',
        filename: 'Q3-2023-Earnings.pdf',
        page: 1,
        relevance: 0.95,
        thumbnail: '/data/thumbnails/doc001/page_001.jpg',
      },
      {
        id: 'doc001-page002',
        filename: 'Q3-2023-Earnings.pdf',
        page: 2,
        relevance: 0.88,
        thumbnail: '/data/thumbnails/doc001/page_002.jpg',
      },
    ],
    confidence: 0.92,
    processingTime: 2500,
    timestamp: new Date().toISOString(),
    ...overrides,
  }
}

/**
 * Wait for async operations to complete.
 *
 * @param {number} ms - Milliseconds to wait (default: 0)
 * @returns {Promise<void>}
 *
 * @example
 * await waitForAsync()
 * // or with custom delay
 * await waitForAsync(100)
 */
export function waitForAsync(ms = 0) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms)
  })
}

/**
 * Mock fetch responses for testing.
 *
 * @param {Object} response - Response data
 * @param {Object} options - Fetch options
 * @param {number} options.status - HTTP status code
 * @param {boolean} options.ok - Success status
 * @param {number} options.delay - Delay in ms before resolving
 * @returns {Promise<Response>} Mock fetch response
 *
 * @example
 * global.fetch = vi.fn(() => mockFetch({ data: 'test' }))
 */
export function mockFetch(response, { status = 200, ok = true, delay = 0 } = {}) {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        ok,
        status,
        json: async () => response,
        text: async () => JSON.stringify(response),
        headers: new Headers({ 'content-type': 'application/json' }),
      })
    }, delay)
  })
}

/**
 * Mock fetch error for testing error scenarios.
 *
 * @param {string} message - Error message
 * @param {number} status - HTTP status code
 * @returns {Promise<never>} Rejected promise
 *
 * @example
 * global.fetch = vi.fn(() => mockFetchError('Network error', 500))
 */
export function mockFetchError(message = 'Network error', status = 500) {
  return Promise.reject(new Error(message))
}

/**
 * Create mock API endpoints for testing.
 *
 * @returns {Object} Object with mock fetch functions
 *
 * @example
 * const api = createMockApi()
 * global.fetch = vi.fn((url) => {
 *   if (url.includes('/search')) return api.search()
 *   if (url.includes('/documents')) return api.documents()
 * })
 */
export function createMockApi() {
  return {
    search: (results = createMockSearchResults()) =>
      mockFetch({
        results,
        total: results.length,
        processingTime: 250,
      }),

    documents: (documents = [createMockDocument()]) =>
      mockFetch({
        documents,
        total: documents.length,
      }),

    research: (report = createMockResearchReport()) =>
      mockFetch({
        report,
      }),

    upload: (document = createMockDocument({ status: 'uploading' })) =>
      mockFetch({
        document,
        message: 'Upload successful',
      }),

    delete: (success = true) =>
      mockFetch({
        success,
        message: 'Document deleted successfully',
      }),
  }
}

/**
 * Assert that an element has accessible name.
 *
 * @param {HTMLElement} element - Element to check
 * @param {string} expectedName - Expected accessible name
 *
 * @example
 * const button = getByRole('button')
 * assertAccessibleName(button, 'Submit')
 */
export function assertAccessibleName(element, expectedName) {
  const accessibleName = element.getAttribute('aria-label') || element.textContent
  expect(accessibleName).toBe(expectedName)
}

/**
 * Assert that a list is sorted by a specific property.
 *
 * @param {Array} list - List to check
 * @param {string} property - Property to sort by
 * @param {string} order - Sort order ('asc' or 'desc')
 *
 * @example
 * assertSortedBy(results, 'score', 'desc')
 */
export function assertSortedBy(list, property, order = 'asc') {
  for (let i = 1; i < list.length; i++) {
    const prev = list[i - 1][property]
    const curr = list[i][property]

    if (order === 'asc') {
      expect(prev <= curr).toBe(true)
    } else {
      expect(prev >= curr).toBe(true)
    }
  }
}

/**
 * Create a spy for console methods.
 *
 * @param {string} method - Console method to spy on (log, warn, error)
 * @returns {Object} Spy object
 *
 * @example
 * const errorSpy = createConsoleSpy('error')
 * // do something that logs error
 * expect(errorSpy).toHaveBeenCalledWith(expect.stringContaining('Error'))
 * errorSpy.mockRestore()
 */
export function createConsoleSpy(method = 'log') {
  return vi.spyOn(console, method).mockImplementation(() => {})
}

/**
 * Wait for element to be removed from DOM.
 *
 * @param {Function} queryFn - Query function to check element
 * @param {Object} options - Wait options
 * @param {number} options.timeout - Timeout in ms
 * @param {number} options.interval - Check interval in ms
 * @returns {Promise<void>}
 *
 * @example
 * await waitForElementToBeRemoved(() => getByText('Loading...'))
 */
export async function waitForElementToBeRemoved(
  queryFn,
  { timeout = 3000, interval = 50 } = {}
) {
  const startTime = Date.now()

  while (Date.now() - startTime < timeout) {
    if (!queryFn()) {
      return
    }
    await waitForAsync(interval)
  }

  throw new Error('Element was not removed within timeout')
}

/**
 * Create a mock ResizeObserver.
 *
 * @returns {Object} Mock ResizeObserver class
 *
 * @example
 * global.ResizeObserver = createMockResizeObserver()
 */
export function createMockResizeObserver() {
  return class MockResizeObserver {
    observe = vi.fn()
    unobserve = vi.fn()
    disconnect = vi.fn()
  }
}

/**
 * Create a mock IntersectionObserver.
 *
 * @returns {Object} Mock IntersectionObserver class
 *
 * @example
 * global.IntersectionObserver = createMockIntersectionObserver()
 */
export function createMockIntersectionObserver() {
  return class MockIntersectionObserver {
    constructor(callback) {
      this.callback = callback
    }
    observe = vi.fn()
    unobserve = vi.fn()
    disconnect = vi.fn()
    takeRecords = vi.fn(() => [])
  }
}

/**
 * Simulate user typing with realistic delay.
 *
 * @param {HTMLElement} element - Input element
 * @param {string} text - Text to type
 * @param {number} delay - Delay between keystrokes in ms
 * @returns {Promise<void>}
 *
 * @example
 * await simulateTyping(input, 'search query', 50)
 */
export async function simulateTyping(element, text, delay = 10) {
  for (const char of text) {
    element.value += char
    element.dispatchEvent(new Event('input', { bubbles: true }))
    await waitForAsync(delay)
  }
}

// Export all utilities
export default {
  renderWithProviders,
  createMockDocument,
  createMockSearchResult,
  createMockSearchResults,
  createMockResearchReport,
  waitForAsync,
  mockFetch,
  mockFetchError,
  createMockApi,
  assertAccessibleName,
  assertSortedBy,
  createConsoleSpy,
  waitForElementToBeRemoved,
  createMockResizeObserver,
  createMockIntersectionObserver,
  simulateTyping,
}

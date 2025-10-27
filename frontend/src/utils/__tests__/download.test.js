/**
 * Download Utilities Tests
 *
 * Coverage-Gap-Agent - Wave 4, Task 23
 * Testing file download functions with DOM manipulation
 */

import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  downloadMarkdown,
  downloadVTT,
  downloadTextAsFile,
  downloadFile,
} from '../download'

describe('downloadMarkdown', () => {
  let mockButton
  let mockLink
  let appendChildSpy
  let removeChildSpy

  beforeEach(() => {
    // Mock button element
    mockButton = {
      innerHTML: 'Download',
      classList: {
        add: vi.fn(),
        remove: vi.fn(),
      },
    }

    // Mock link element
    mockLink = {
      href: '',
      download: '',
      click: vi.fn(),
    }

    // Spy on document methods
    appendChildSpy = vi.spyOn(document.body, 'appendChild').mockReturnValue(undefined)
    removeChildSpy = vi.spyOn(document.body, 'removeChild').mockReturnValue(undefined)
    vi.spyOn(document, 'createElement').mockReturnValue(mockLink)

    // Mock setTimeout
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  test('creates download link with correct URL', async () => {
    await downloadMarkdown('doc123', mockButton)

    expect(document.createElement).toHaveBeenCalledWith('a')
    expect(mockLink.href).toBe('/documents/doc123/markdown')
  })

  test('triggers download click', async () => {
    await downloadMarkdown('doc123', mockButton)

    expect(mockLink.click).toHaveBeenCalled()
  })

  test('appends and removes link from DOM', async () => {
    await downloadMarkdown('doc123', mockButton)

    expect(appendChildSpy).toHaveBeenCalledWith(mockLink)
    expect(removeChildSpy).toHaveBeenCalledWith(mockLink)
  })

  test('shows success feedback on button', async () => {
    await downloadMarkdown('doc123', mockButton)

    expect(mockButton.innerHTML).toBe('✓ Downloaded!')
    expect(mockButton.classList.add).toHaveBeenCalledWith('success')
  })

  test('resets button after 2 seconds', async () => {
    const originalText = mockButton.innerHTML
    await downloadMarkdown('doc123', mockButton)

    expect(mockButton.innerHTML).toBe('✓ Downloaded!')

    vi.advanceTimersByTime(2000)

    expect(mockButton.innerHTML).toBe(originalText)
    expect(mockButton.classList.remove).toHaveBeenCalledWith('success')
  })

  test('handles null button gracefully', async () => {
    await expect(downloadMarkdown('doc123', null)).resolves.toBeUndefined()
    expect(mockLink.click).toHaveBeenCalled()
  })

  test('handles errors and shows failure feedback', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    mockLink.click.mockImplementation(() => {
      throw new Error('Download failed')
    })

    await downloadMarkdown('doc123', mockButton)

    expect(consoleErrorSpy).toHaveBeenCalled()
    expect(mockButton.innerHTML).toBe('✗ Failed')

    vi.advanceTimersByTime(2000)
    expect(mockButton.innerHTML).toBe('Download')

    consoleErrorSpy.mockRestore()
  })
})

describe('downloadVTT', () => {
  let mockButton
  let mockLink
  let appendChildSpy
  let removeChildSpy

  beforeEach(() => {
    mockButton = {
      innerHTML: 'Download Captions',
      classList: {
        add: vi.fn(),
        remove: vi.fn(),
      },
    }

    mockLink = {
      href: '',
      download: '',
      click: vi.fn(),
    }

    appendChildSpy = vi.spyOn(document.body, 'appendChild').mockReturnValue(undefined)
    removeChildSpy = vi.spyOn(document.body, 'removeChild').mockReturnValue(undefined)
    vi.spyOn(document, 'createElement').mockReturnValue(mockLink)

    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  test('creates download link with correct VTT URL', async () => {
    await downloadVTT('audio123', mockButton)

    expect(mockLink.href).toBe('/documents/audio123/vtt')
  })

  test('triggers download click', async () => {
    await downloadVTT('audio123', mockButton)

    expect(mockLink.click).toHaveBeenCalled()
  })

  test('shows success feedback', async () => {
    await downloadVTT('audio123', mockButton)

    expect(mockButton.innerHTML).toBe('✓ Downloaded!')
    expect(mockButton.classList.add).toHaveBeenCalledWith('success')
  })

  test('handles errors gracefully', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    mockLink.click.mockImplementation(() => {
      throw new Error('VTT download failed')
    })

    await downloadVTT('audio123', mockButton)

    expect(consoleErrorSpy).toHaveBeenCalled()
    expect(mockButton.innerHTML).toBe('✗ Failed')

    consoleErrorSpy.mockRestore()
  })
})

describe('downloadTextAsFile', () => {
  let mockLink
  let appendChildSpy
  let removeChildSpy
  let createObjectURLSpy
  let revokeObjectURLSpy

  beforeEach(() => {
    mockLink = {
      href: '',
      download: '',
      click: vi.fn(),
    }

    appendChildSpy = vi.spyOn(document.body, 'appendChild').mockReturnValue(undefined)
    removeChildSpy = vi.spyOn(document.body, 'removeChild').mockReturnValue(undefined)
    vi.spyOn(document, 'createElement').mockReturnValue(mockLink)

    createObjectURLSpy = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:mock-url')
    revokeObjectURLSpy = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  test('creates blob with correct text content', () => {
    const text = 'Test content'
    downloadTextAsFile(text, 'test.txt')

    expect(createObjectURLSpy).toHaveBeenCalled()
    const blob = createObjectURLSpy.mock.calls[0][0]
    expect(blob).toBeInstanceOf(Blob)
    expect(blob.type).toBe('text/plain')
  })

  test('sets correct filename on download link', () => {
    downloadTextAsFile('content', 'myfile.txt')

    expect(mockLink.download).toBe('myfile.txt')
  })

  test('uses custom MIME type when provided', () => {
    downloadTextAsFile('content', 'data.json', 'application/json')

    const blob = createObjectURLSpy.mock.calls[0][0]
    expect(blob.type).toBe('application/json')
  })

  test('triggers download click', () => {
    downloadTextAsFile('content', 'file.txt')

    expect(mockLink.click).toHaveBeenCalled()
  })

  test('cleans up object URL', () => {
    downloadTextAsFile('content', 'file.txt')

    expect(revokeObjectURLSpy).toHaveBeenCalledWith('blob:mock-url')
  })

  test('appends and removes link from DOM', () => {
    downloadTextAsFile('content', 'file.txt')

    expect(appendChildSpy).toHaveBeenCalledWith(mockLink)
    expect(removeChildSpy).toHaveBeenCalledWith(mockLink)
  })

  test('handles empty text content', () => {
    downloadTextAsFile('', 'empty.txt')

    expect(mockLink.click).toHaveBeenCalled()
  })

  test('handles large text content', () => {
    const largeText = 'x'.repeat(1000000) // 1MB of text
    downloadTextAsFile(largeText, 'large.txt')

    expect(mockLink.click).toHaveBeenCalled()
    expect(revokeObjectURLSpy).toHaveBeenCalled()
  })

  test('handles special characters in text', () => {
    const specialText = '!@#$%^&*()_+-={}[]|\\:";\'<>?,./`~\n\t'
    downloadTextAsFile(specialText, 'special.txt')

    expect(mockLink.click).toHaveBeenCalled()
  })
})

describe('downloadFile', () => {
  let mockLink
  let appendChildSpy
  let removeChildSpy

  beforeEach(() => {
    mockLink = {
      href: '',
      download: '',
      click: vi.fn(),
    }

    appendChildSpy = vi.spyOn(document.body, 'appendChild').mockReturnValue(undefined)
    removeChildSpy = vi.spyOn(document.body, 'removeChild').mockReturnValue(undefined)
    vi.spyOn(document, 'createElement').mockReturnValue(mockLink)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  test('creates link with correct URL', () => {
    downloadFile('http://example.com/file.pdf')

    expect(mockLink.href).toBe('http://example.com/file.pdf')
  })

  test('sets filename when provided', () => {
    downloadFile('http://example.com/file.pdf', 'mydoc.pdf')

    expect(mockLink.download).toBe('mydoc.pdf')
  })

  test('does not set download attribute when filename not provided', () => {
    downloadFile('http://example.com/file.pdf')

    // download property should remain as empty string (initial value)
    expect(mockLink.download).toBe('')
  })

  test('triggers download click', () => {
    downloadFile('http://example.com/file.pdf')

    expect(mockLink.click).toHaveBeenCalled()
  })

  test('appends and removes link from DOM', () => {
    downloadFile('http://example.com/file.pdf')

    expect(appendChildSpy).toHaveBeenCalledWith(mockLink)
    expect(removeChildSpy).toHaveBeenCalledWith(mockLink)
  })

  test('handles relative URLs', () => {
    downloadFile('/documents/123/download')

    expect(mockLink.href).toBe('/documents/123/download')
    expect(mockLink.click).toHaveBeenCalled()
  })

  test('handles data URLs', () => {
    const dataUrl = 'data:text/plain;base64,SGVsbG8gV29ybGQ='
    downloadFile(dataUrl, 'hello.txt')

    expect(mockLink.href).toBe(dataUrl)
    expect(mockLink.click).toHaveBeenCalled()
  })
})

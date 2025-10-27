/**
 * Clipboard Utilities Tests
 *
 * Coverage-Gap-Agent - Wave 4, Task 23
 * Testing clipboard operations and frontmatter stripping
 */

import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest'
import { copyToClipboard, stripFrontmatter } from '../clipboard'

describe('copyToClipboard', () => {
  let mockClipboard
  let mockButton

  beforeEach(() => {
    // Mock clipboard API
    mockClipboard = {
      writeText: vi.fn().mockResolvedValue(undefined),
    }
    Object.assign(navigator, {
      clipboard: mockClipboard,
    })

    // Create mock button element
    mockButton = {
      innerHTML: 'Copy',
      classList: {
        add: vi.fn(),
        remove: vi.fn(),
      },
    }

    // Mock setTimeout to execute immediately
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  test('copies text to clipboard successfully', async () => {
    const text = 'Hello, world!'
    const result = await copyToClipboard(text, mockButton)

    expect(result).toBe(true)
    expect(mockClipboard.writeText).toHaveBeenCalledWith(text)
    expect(mockClipboard.writeText).toHaveBeenCalledTimes(1)
  })

  test('shows success feedback on button', async () => {
    const text = 'Test text'
    await copyToClipboard(text, mockButton)

    expect(mockButton.innerHTML).toBe('✓ Copied!')
    expect(mockButton.classList.add).toHaveBeenCalledWith('success')
  })

  test('resets button after 2 seconds', async () => {
    const originalText = mockButton.innerHTML
    await copyToClipboard('Test', mockButton)

    expect(mockButton.innerHTML).toBe('✓ Copied!')

    // Fast-forward time
    vi.advanceTimersByTime(2000)

    expect(mockButton.innerHTML).toBe(originalText)
    expect(mockButton.classList.remove).toHaveBeenCalledWith('success')
  })

  test('handles null button gracefully', async () => {
    const result = await copyToClipboard('Test', null)

    expect(result).toBe(true)
    expect(mockClipboard.writeText).toHaveBeenCalled()
  })

  test('handles undefined button gracefully', async () => {
    const result = await copyToClipboard('Test', undefined)

    expect(result).toBe(true)
    expect(mockClipboard.writeText).toHaveBeenCalled()
  })

  test('handles clipboard API failure', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const error = new Error('Clipboard write failed')
    mockClipboard.writeText.mockRejectedValue(error)

    const result = await copyToClipboard('Test', mockButton)

    expect(result).toBe(false)
    expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to copy to clipboard:', error)
    consoleErrorSpy.mockRestore()
  })

  test('shows failure feedback on button when copy fails', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    mockClipboard.writeText.mockRejectedValue(new Error('Failed'))

    const originalText = mockButton.innerHTML
    await copyToClipboard('Test', mockButton)

    expect(mockButton.innerHTML).toBe('✗ Failed')

    // Fast-forward time
    vi.advanceTimersByTime(2000)

    expect(mockButton.innerHTML).toBe(originalText)
    consoleErrorSpy.mockRestore()
  })

  test('copies empty string successfully', async () => {
    const result = await copyToClipboard('', mockButton)

    expect(result).toBe(true)
    expect(mockClipboard.writeText).toHaveBeenCalledWith('')
  })

  test('copies multiline text correctly', async () => {
    const multilineText = 'Line 1\nLine 2\nLine 3'
    const result = await copyToClipboard(multilineText, mockButton)

    expect(result).toBe(true)
    expect(mockClipboard.writeText).toHaveBeenCalledWith(multilineText)
  })

  test('copies special characters', async () => {
    const specialText = '!@#$%^&*()_+-={}[]|\\:";\'<>?,./`~'
    const result = await copyToClipboard(specialText, mockButton)

    expect(result).toBe(true)
    expect(mockClipboard.writeText).toHaveBeenCalledWith(specialText)
  })
})

describe('stripFrontmatter', () => {
  test('removes YAML frontmatter from markdown', () => {
    const markdown = `---
title: Test Document
author: John Doe
date: 2025-01-15
---

# Main Content

This is the actual content.`

    const result = stripFrontmatter(markdown)

    expect(result).toBe('# Main Content\n\nThis is the actual content.')
  })

  test('handles markdown without frontmatter', () => {
    const markdown = '# Heading\n\nContent without frontmatter.'

    const result = stripFrontmatter(markdown)

    expect(result).toBe(markdown)
  })

  test('handles empty string', () => {
    const result = stripFrontmatter('')

    expect(result).toBe('')
  })

  test('handles frontmatter with multiple delimiters in content', () => {
    const markdown = `---
title: Test
---

Content with --- in it

Another --- line`

    const result = stripFrontmatter(markdown)

    expect(result).toBe('Content with --- in it\n\nAnother --- line')
  })

  test('handles frontmatter without closing delimiter', () => {
    const markdown = `---
title: Test
author: John

# Content without closing delimiter`

    const result = stripFrontmatter(markdown)

    // No closing delimiter found, returns original
    expect(result).toBe(markdown)
  })

  test('trims whitespace after removing frontmatter', () => {
    const markdown = `---
title: Test
---


# Content with leading newlines`

    const result = stripFrontmatter(markdown)

    expect(result).toBe('# Content with leading newlines')
  })

  test('handles frontmatter only', () => {
    const markdown = `---
title: Test
---`

    const result = stripFrontmatter(markdown)

    expect(result).toBe('')
  })

  test('handles markdown that starts with triple dash but no closing', () => {
    const markdown = '---\n\nSome content\n\nMore content'

    const result = stripFrontmatter(markdown)

    // No closing delimiter, returns original
    expect(result).toBe(markdown)
  })

  test('preserves content structure after frontmatter', () => {
    const markdown = `---
key: value
---

# Title

## Subtitle

- List item 1
- List item 2

\`\`\`code
block
\`\`\``

    const result = stripFrontmatter(markdown)

    expect(result).toContain('# Title')
    expect(result).toContain('## Subtitle')
    expect(result).toContain('- List item 1')
    expect(result).toContain('```code')
  })
})

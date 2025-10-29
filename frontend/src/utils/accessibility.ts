/**
 * Accessibility Utilities
 *
 * Agent 11: Accessibility Specialist
 * Wave 3 - BBox Overlay React Implementation
 *
 * Utility functions for accessibility enhancements including screen reader
 * announcements, focus management, and keyboard navigation helpers.
 *
 * Features:
 * - Screen reader announcements via aria-live regions
 * - Focus trap management
 * - Keyboard event helpers
 * - WCAG 2.1 AA compliance utilities
 */

/**
 * Creates or retrieves a live region for screen reader announcements
 */
let liveRegion: HTMLDivElement | null = null;

/**
 * Announces a message to screen readers using an aria-live region.
 *
 * @param message - The message to announce
 * @param priority - Announcement priority ('polite' or 'assertive')
 * @param delay - Delay before announcement (ms) to ensure screen readers pick it up
 *
 * @example
 * ```typescript
 * announceToScreenReader('Navigated to heading 3', 'polite');
 * announceToScreenReader('Error occurred', 'assertive');
 * ```
 */
export function announceToScreenReader(
  message: string,
  priority: 'polite' | 'assertive' = 'polite',
  delay: number = 100
): void {
  // Create live region if it doesn't exist
  if (!liveRegion) {
    liveRegion = document.createElement('div');
    liveRegion.setAttribute('role', 'status');
    liveRegion.setAttribute('aria-live', priority);
    liveRegion.setAttribute('aria-atomic', 'true');
    liveRegion.className = 'sr-only';
    // Position off-screen but still accessible to screen readers
    Object.assign(liveRegion.style, {
      position: 'absolute',
      left: '-10000px',
      width: '1px',
      height: '1px',
      overflow: 'hidden',
    });
    document.body.appendChild(liveRegion);
  }

  // Update priority if different
  if (liveRegion.getAttribute('aria-live') !== priority) {
    liveRegion.setAttribute('aria-live', priority);
  }

  // Clear and set message with delay to ensure screen readers notice the change
  liveRegion.textContent = '';
  setTimeout(() => {
    if (liveRegion) {
      liveRegion.textContent = message;
    }
  }, delay);
}

/**
 * Clears the screen reader announcement
 */
export function clearScreenReaderAnnouncement(): void {
  if (liveRegion) {
    liveRegion.textContent = '';
  }
}

/**
 * Gets all focusable elements within a container
 *
 * @param container - The container element to search within
 * @returns Array of focusable HTMLElements
 */
export function getFocusableElements(container: HTMLElement): HTMLElement[] {
  const focusableSelectors = [
    'a[href]',
    'button:not([disabled])',
    'textarea:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
    '[contenteditable="true"]',
  ].join(', ');

  return Array.from(
    container.querySelectorAll<HTMLElement>(focusableSelectors)
  ).filter((element) => {
    // Filter out elements that are not visible
    return (
      element.offsetWidth > 0 &&
      element.offsetHeight > 0 &&
      getComputedStyle(element).visibility !== 'hidden'
    );
  });
}

/**
 * Creates a focus trap within a container
 *
 * @param container - The container to trap focus within
 * @returns Function to remove the focus trap
 *
 * @example
 * ```typescript
 * const removeTrap = trapFocus(overlayElement);
 * // Later...
 * removeTrap();
 * ```
 */
export function trapFocus(container: HTMLElement): () => void {
  const focusableElements = getFocusableElements(container);
  const firstFocusable = focusableElements[0];
  const lastFocusable = focusableElements[focusableElements.length - 1];

  const handleKeyDown = (event: KeyboardEvent): void => {
    if (event.key !== 'Tab') return;

    if (event.shiftKey) {
      // Shift + Tab: Moving backwards
      if (document.activeElement === firstFocusable) {
        event.preventDefault();
        lastFocusable?.focus();
      }
    } else {
      // Tab: Moving forwards
      if (document.activeElement === lastFocusable) {
        event.preventDefault();
        firstFocusable?.focus();
      }
    }
  };

  container.addEventListener('keydown', handleKeyDown);

  // Return cleanup function
  return () => {
    container.removeEventListener('keydown', handleKeyDown);
  };
}

/**
 * Moves focus to an element with proper error handling
 *
 * @param element - The element to focus
 * @param options - Focus options
 * @returns Whether focus was successful
 */
export function moveFocusToElement(
  element: HTMLElement | null,
  options?: FocusOptions
): boolean {
  if (!element) return false;

  try {
    // Make element focusable if it isn't already
    if (!element.hasAttribute('tabindex')) {
      element.setAttribute('tabindex', '-1');
    }

    element.focus(options);
    return document.activeElement === element;
  } catch (error) {
    console.warn('[Accessibility] Failed to move focus:', error);
    return false;
  }
}

/**
 * Restores focus to a previously focused element
 *
 * @param element - The element to restore focus to
 */
export function restoreFocus(element: HTMLElement | null): void {
  if (element && document.body.contains(element)) {
    moveFocusToElement(element);
  }
}

/**
 * Checks if an element is currently in the viewport
 *
 * @param element - The element to check
 * @param threshold - Percentage of element that must be visible (0-1)
 * @returns Whether the element is in viewport
 */
export function isElementInViewport(
  element: HTMLElement,
  threshold: number = 0.5
): boolean {
  const rect = element.getBoundingClientRect();
  const windowHeight =
    window.innerHeight || document.documentElement.clientHeight;
  const windowWidth =
    window.innerWidth || document.documentElement.clientWidth;

  const vertInView =
    rect.top <= windowHeight - rect.height * threshold &&
    rect.bottom >= rect.height * threshold;
  const horInView =
    rect.left <= windowWidth - rect.width * threshold &&
    rect.right >= rect.width * threshold;

  return vertInView && horInView;
}

/**
 * Scrolls an element into view with smooth behavior and proper offset
 *
 * @param element - The element to scroll to
 * @param options - Scroll options
 */
export interface ScrollIntoViewOptions {
  behavior?: ScrollBehavior;
  block?: ScrollLogicalPosition;
  inline?: ScrollLogicalPosition;
  offset?: number;
}

export function scrollIntoViewWithOffset(
  element: HTMLElement,
  options: ScrollIntoViewOptions = {}
): void {
  const {
    behavior = 'smooth',
    block = 'center',
    inline = 'nearest',
    offset = 0,
  } = options;

  // First scroll element into view
  element.scrollIntoView({ behavior, block, inline });

  // Then apply offset if needed
  if (offset !== 0) {
    const scrolledY = window.scrollY;
    window.scrollTo({
      top: scrolledY - offset,
      behavior,
    });
  }
}

/**
 * Keyboard navigation helpers
 */

/**
 * Checks if a keyboard event is an activation key (Enter or Space)
 *
 * @param event - The keyboard event
 * @returns Whether the key is an activation key
 */
export function isActivationKey(event: KeyboardEvent): boolean {
  return event.key === 'Enter' || event.key === ' ' || event.key === 'Spacebar';
}

/**
 * Checks if a keyboard event is an arrow key
 *
 * @param event - The keyboard event
 * @returns The arrow direction or null
 */
export function getArrowDirection(
  event: KeyboardEvent
): 'up' | 'down' | 'left' | 'right' | null {
  switch (event.key) {
    case 'ArrowUp':
      return 'up';
    case 'ArrowDown':
      return 'down';
    case 'ArrowLeft':
      return 'left';
    case 'ArrowRight':
      return 'right';
    default:
      return null;
  }
}

/**
 * Checks if a keyboard event is an escape key
 *
 * @param event - The keyboard event
 * @returns Whether the key is escape
 */
export function isEscapeKey(event: KeyboardEvent): boolean {
  return event.key === 'Escape' || event.key === 'Esc';
}

/**
 * Gets the next/previous element in a list based on arrow key
 *
 * @param elements - Array of elements
 * @param currentIndex - Current index
 * @param direction - Navigation direction
 * @returns Next element index or null
 */
export function getNextElementIndex(
  elements: HTMLElement[],
  currentIndex: number,
  direction: 'up' | 'down' | 'left' | 'right'
): number | null {
  const isForward = direction === 'down' || direction === 'right';
  const isBackward = direction === 'up' || direction === 'left';

  if (isForward && currentIndex < elements.length - 1) {
    return currentIndex + 1;
  }

  if (isBackward && currentIndex > 0) {
    return currentIndex - 1;
  }

  return null;
}

/**
 * Color contrast utilities
 */

/**
 * Calculates relative luminance of an RGB color
 * Based on WCAG 2.1 formula
 *
 * @param r - Red (0-255)
 * @param g - Green (0-255)
 * @param b - Blue (0-255)
 * @returns Relative luminance (0-1)
 */
function getRelativeLuminance(r: number, g: number, b: number): number {
  const rsRGB = r / 255;
  const gsRGB = g / 255;
  const bsRGB = b / 255;

  const rLin =
    rsRGB <= 0.03928 ? rsRGB / 12.92 : Math.pow((rsRGB + 0.055) / 1.055, 2.4);
  const gLin =
    gsRGB <= 0.03928 ? gsRGB / 12.92 : Math.pow((gsRGB + 0.055) / 1.055, 2.4);
  const bLin =
    bsRGB <= 0.03928 ? bsRGB / 12.92 : Math.pow((bsRGB + 0.055) / 1.055, 2.4);

  return 0.2126 * rLin + 0.7152 * gLin + 0.0722 * bLin;
}

/**
 * Calculates contrast ratio between two colors
 * Based on WCAG 2.1 formula
 *
 * @param rgb1 - First color [r, g, b]
 * @param rgb2 - Second color [r, g, b]
 * @returns Contrast ratio (1-21)
 */
export function getContrastRatio(
  rgb1: [number, number, number],
  rgb2: [number, number, number]
): number {
  const l1 = getRelativeLuminance(...rgb1);
  const l2 = getRelativeLuminance(...rgb2);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

/**
 * Checks if contrast ratio meets WCAG AA standard
 *
 * @param contrastRatio - The contrast ratio to check
 * @param isLargeText - Whether the text is large (18pt+ or 14pt+ bold)
 * @returns Whether the contrast meets AA standard
 */
export function meetsWCAGAA(
  contrastRatio: number,
  isLargeText: boolean = false
): boolean {
  const threshold = isLargeText ? 3 : 4.5;
  return contrastRatio >= threshold;
}

/**
 * Checks if contrast ratio meets WCAG AAA standard
 *
 * @param contrastRatio - The contrast ratio to check
 * @param isLargeText - Whether the text is large (18pt+ or 14pt+ bold)
 * @returns Whether the contrast meets AAA standard
 */
export function meetsWCAGAAA(
  contrastRatio: number,
  isLargeText: boolean = false
): boolean {
  const threshold = isLargeText ? 4.5 : 7;
  return contrastRatio >= threshold;
}

/**
 * Generates an accessible label for a bounding box
 *
 * @param elementType - Type of the element (e.g., 'heading', 'table')
 * @param index - Index of the element on the page
 * @param pageNumber - Current page number
 * @returns Accessible label
 */
export function generateBBoxLabel(
  elementType: string,
  index: number,
  pageNumber?: number
): string {
  const pagePrefix = pageNumber ? `Page ${pageNumber}, ` : '';
  const elementName = elementType
    .replace(/-/g, ' ')
    .replace(/\b\w/g, (l) => l.toUpperCase());
  return `${pagePrefix}${elementName} ${index + 1}`;
}

/**
 * Generates an accessible description for a chunk
 *
 * @param chunkId - ID of the chunk
 * @param isActive - Whether the chunk is currently active
 * @param isHovered - Whether the chunk is currently hovered
 * @returns Accessible description
 */
export function generateChunkDescription(
  chunkId: string,
  isActive: boolean,
  isHovered: boolean
): string {
  let description = `Chunk ${chunkId}`;

  if (isActive && isHovered) {
    description += ', selected and highlighted';
  } else if (isActive) {
    description += ', selected';
  } else if (isHovered) {
    description += ', highlighted';
  }

  return description;
}

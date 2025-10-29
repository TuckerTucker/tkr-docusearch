/**
 * Scroll to Chunk Utility
 *
 * Agent 7: Chunk Highlighter Component
 * Wave 1 - BBox Overlay React Implementation
 *
 * Provides smooth scrolling functionality to highlight chunks in markdown content.
 * Uses IntersectionObserver to ensure chunks are properly visible after scrolling.
 */

export interface ScrollToChunkOptions {
  /**
   * Scroll behavior: 'smooth' for animated, 'instant' for immediate, 'auto' for browser default
   * @default 'smooth'
   */
  behavior?: ScrollBehavior;
  /**
   * Vertical alignment: 'start', 'center', 'end', or 'nearest'
   * @default 'center'
   */
  block?: ScrollLogicalPosition;
  /**
   * Horizontal alignment: 'start', 'center', 'end', or 'nearest'
   * @default 'nearest'
   */
  inline?: ScrollLogicalPosition;
  /**
   * Additional offset from the top in pixels (useful for fixed headers)
   * @default 0
   */
  offset?: number;
}

export interface ScrollResult {
  /**
   * Whether the scroll operation was successful
   */
  success: boolean;
  /**
   * The element that was scrolled to, if found
   */
  element: HTMLElement | null;
  /**
   * Error message if the operation failed
   */
  error?: string;
}

/**
 * Scrolls to a chunk element identified by its data-chunk-id attribute.
 *
 * @param chunkId - The ID of the chunk to scroll to
 * @param container - The scrollable container element (optional, defaults to window)
 * @param options - Scroll behavior options
 * @returns Promise that resolves with the scroll result
 *
 * @example
 * ```typescript
 * const result = await scrollToChunk('chunk-123', containerRef.current, {
 *   behavior: 'smooth',
 *   block: 'center',
 *   offset: 80 // Account for fixed header
 * });
 *
 * if (result.success) {
 *   console.log('Scrolled to chunk:', result.element);
 * } else {
 *   console.error('Scroll failed:', result.error);
 * }
 * ```
 */
export async function scrollToChunk(
  chunkId: string,
  container?: HTMLElement | null,
  options: ScrollToChunkOptions = {}
): Promise<ScrollResult> {
  const {
    behavior = 'smooth',
    block = 'center',
    inline = 'nearest',
    offset = 0,
  } = options;

  // Validate chunk ID
  if (!chunkId || typeof chunkId !== 'string') {
    return {
      success: false,
      element: null,
      error: 'Invalid chunk ID provided',
    };
  }

  // Find the chunk element
  const searchRoot = container || document;
  const chunkElement = searchRoot.querySelector(
    `[data-chunk-id="${CSS.escape(chunkId)}"]`
  ) as HTMLElement;

  if (!chunkElement) {
    return {
      success: false,
      element: null,
      error: `Chunk with ID "${chunkId}" not found`,
    };
  }

  // Handle offset if provided
  if (offset !== 0) {
    // Calculate the target position with offset
    const elementRect = chunkElement.getBoundingClientRect();
    const containerRect = container?.getBoundingClientRect();
    const scrollTop = container?.scrollTop || window.scrollY;

    const targetTop = elementRect.top + scrollTop - (containerRect?.top || 0) - offset;

    if (container) {
      container.scrollTo({
        top: targetTop,
        behavior,
      });
    } else {
      window.scrollTo({
        top: targetTop,
        behavior,
      });
    }
  } else {
    // Use standard scrollIntoView
    chunkElement.scrollIntoView({
      behavior,
      block,
      inline,
    });
  }

  // Wait for scroll to complete and verify element is in view
  return new Promise((resolve) => {
    // If instant scroll, resolve immediately
    if (behavior === 'instant' || behavior === 'auto') {
      resolve({
        success: true,
        element: chunkElement,
      });
      return;
    }

    // For smooth scrolling, use IntersectionObserver to detect when in view
    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        if (entry.isIntersecting) {
          observer.disconnect();
          resolve({
            success: true,
            element: chunkElement,
          });
        }
      },
      {
        root: container || null,
        threshold: 0.5, // At least 50% visible
        rootMargin: offset ? `-${offset}px 0px 0px 0px` : '0px',
      }
    );

    observer.observe(chunkElement);

    // Timeout fallback in case IntersectionObserver doesn't fire
    setTimeout(() => {
      observer.disconnect();
      resolve({
        success: true,
        element: chunkElement,
      });
    }, 1000); // Generous timeout for smooth scroll
  });
}

/**
 * Gets the bounding rectangle of a chunk element relative to its container.
 *
 * @param chunkId - The ID of the chunk
 * @param container - The container element (optional)
 * @returns The DOMRect of the chunk, or null if not found
 */
export function getChunkRect(
  chunkId: string,
  container?: HTMLElement | null
): DOMRect | null {
  const searchRoot = container || document;
  const chunkElement = searchRoot.querySelector(
    `[data-chunk-id="${CSS.escape(chunkId)}"]`
  ) as HTMLElement;

  return chunkElement?.getBoundingClientRect() || null;
}

/**
 * Checks if a chunk is currently visible in the viewport or container.
 *
 * @param chunkId - The ID of the chunk
 * @param container - The container element (optional)
 * @param threshold - Percentage of element that must be visible (0-1, default: 0.5)
 * @returns Promise that resolves to true if chunk is visible
 */
export function isChunkVisible(
  chunkId: string,
  container?: HTMLElement | null,
  threshold: number = 0.5
): Promise<boolean> {
  return new Promise((resolve) => {
    const searchRoot = container || document;
    const chunkElement = searchRoot.querySelector(
      `[data-chunk-id="${CSS.escape(chunkId)}"]`
    ) as HTMLElement;

    if (!chunkElement) {
      resolve(false);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        observer.disconnect();
        resolve(entry.isIntersecting && entry.intersectionRatio >= threshold);
      },
      {
        root: container || null,
        threshold,
      }
    );

    observer.observe(chunkElement);

    // Quick timeout fallback
    setTimeout(() => {
      observer.disconnect();
      resolve(false);
    }, 100);
  });
}

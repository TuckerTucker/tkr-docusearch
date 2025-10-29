/**
 * useChunkHighlight Hook
 *
 * Agent 7: Chunk Highlighter Component
 * Wave 1 - BBox Overlay React Implementation
 * Agent 12: Performance Optimizer - Wave 3
 *
 * React hook for managing chunk highlighting, hover states, and smooth scrolling.
 * Integrates with markdown content to provide visual feedback for chunk selection.
 *
 * Performance optimizations:
 * - Debounced hover handlers (50ms)
 * - Memoized callbacks
 * - Event delegation for better performance
 */

import { useEffect, useCallback, useRef, RefObject } from 'react';
import { useDebounce } from '../../hooks/useDebounce';
import { scrollToChunk, ScrollToChunkOptions } from './scrollToChunk';

export interface UseChunkHighlightOptions {
  /**
   * Reference to the container element that holds the chunks
   */
  containerRef: RefObject<HTMLElement>;
  /**
   * The ID of the currently active chunk (e.g., from citation click)
   */
  activeChunkId?: string | null;
  /**
   * The ID of the currently hovered chunk
   */
  hoveredChunkId?: string | null;
  /**
   * Callback fired when a chunk is hovered
   */
  onChunkHover?: (chunkId: string | null) => void;
  /**
   * Scroll behavior for navigation to chunks
   * @default 'smooth'
   */
  scrollBehavior?: ScrollBehavior;
  /**
   * Offset from top for scrolling (useful for fixed headers)
   * @default 0
   */
  scrollOffset?: number;
  /**
   * CSS class name to apply to active chunks
   * @default 'chunk-active'
   */
  activeClassName?: string;
  /**
   * CSS class name to apply to hovered chunks
   * @default 'chunk-hovered'
   */
  hoveredClassName?: string;
  /**
   * Whether to automatically scroll to active chunk when it changes
   * @default true
   */
  autoScrollToActive?: boolean;
}

export interface UseChunkHighlightResult {
  /**
   * Programmatically highlight a specific chunk
   */
  highlightChunk: (chunkId: string) => void;
  /**
   * Clear all highlighting
   */
  clearHighlight: () => void;
  /**
   * Scroll to a specific chunk
   */
  scrollToChunk: (chunkId: string, options?: ScrollToChunkOptions) => Promise<void>;
  /**
   * Check if a chunk is currently active
   */
  isActive: (chunkId: string) => boolean;
  /**
   * Check if a chunk is currently hovered
   */
  isHovered: (chunkId: string) => boolean;
}

const ACTIVE_CLASS = 'chunk-active';
const HOVERED_CLASS = 'chunk-hovered';

/**
 * Hook for managing chunk highlighting and interactions.
 *
 * This hook handles:
 * - Adding/removing CSS classes for active and hovered states
 * - Detecting hover events on chunk elements
 * - Smooth scrolling to chunks
 * - Managing focus for accessibility
 *
 * @example
 * ```typescript
 * function ResearchView() {
 *   const containerRef = useRef<HTMLDivElement>(null);
 *   const [activeChunkId, setActiveChunkId] = useState<string | null>(null);
 *
 *   const { highlightChunk, scrollToChunk } = useChunkHighlight({
 *     containerRef,
 *     activeChunkId,
 *     onChunkHover: (chunkId) => console.log('Hovered:', chunkId),
 *     scrollOffset: 80, // Account for fixed header
 *   });
 *
 *   return (
 *     <div ref={containerRef}>
 *       <div data-chunk-id="chunk-1">Content here...</div>
 *     </div>
 *   );
 * }
 * ```
 */
export function useChunkHighlight(
  options: UseChunkHighlightOptions
): UseChunkHighlightResult {
  const {
    containerRef,
    activeChunkId,
    hoveredChunkId,
    onChunkHover,
    scrollBehavior = 'smooth',
    scrollOffset = 0,
    activeClassName = ACTIVE_CLASS,
    hoveredClassName = HOVERED_CLASS,
    autoScrollToActive = true,
  } = options;

  // Track previous active chunk for cleanup
  const previousActiveRef = useRef<string | null>(null);
  const previousHoveredRef = useRef<string | null>(null);

  /**
   * Gets all chunk elements in the container
   */
  const getAllChunks = useCallback((): HTMLElement[] => {
    if (!containerRef.current) return [];
    return Array.from(
      containerRef.current.querySelectorAll('[data-chunk-id]')
    ) as HTMLElement[];
  }, [containerRef]);

  /**
   * Gets a specific chunk element by ID
   */
  const getChunkElement = useCallback(
    (chunkId: string): HTMLElement | null => {
      if (!containerRef.current) return null;
      return containerRef.current.querySelector(
        `[data-chunk-id="${CSS.escape(chunkId)}"]`
      ) as HTMLElement;
    },
    [containerRef]
  );

  /**
   * Applies CSS class to a chunk element
   */
  const applyChunkClass = useCallback(
    (chunkId: string | null, className: string, add: boolean) => {
      if (!chunkId) return;
      const element = getChunkElement(chunkId);
      if (element) {
        if (add) {
          element.classList.add(className);
        } else {
          element.classList.remove(className);
        }
      }
    },
    [getChunkElement]
  );

  /**
   * Handle active chunk changes
   */
  useEffect(() => {
    // Remove class from previous active chunk
    if (previousActiveRef.current && previousActiveRef.current !== activeChunkId) {
      applyChunkClass(previousActiveRef.current, activeClassName, false);
    }

    // Add class to new active chunk
    if (activeChunkId) {
      applyChunkClass(activeChunkId, activeClassName, true);

      // Auto-scroll to active chunk if enabled
      if (autoScrollToActive) {
        scrollToChunk(activeChunkId, containerRef.current, {
          behavior: scrollBehavior,
          block: 'center',
          offset: scrollOffset,
        });
      }
    }

    previousActiveRef.current = activeChunkId || null;
  }, [
    activeChunkId,
    applyChunkClass,
    activeClassName,
    autoScrollToActive,
    scrollBehavior,
    scrollOffset,
    containerRef,
  ]);

  /**
   * Handle hovered chunk changes
   */
  useEffect(() => {
    // Remove class from previous hovered chunk
    if (previousHoveredRef.current && previousHoveredRef.current !== hoveredChunkId) {
      applyChunkClass(previousHoveredRef.current, hoveredClassName, false);
    }

    // Add class to new hovered chunk
    if (hoveredChunkId) {
      applyChunkClass(hoveredChunkId, hoveredClassName, true);
    }

    previousHoveredRef.current = hoveredChunkId || null;
  }, [hoveredChunkId, applyChunkClass, hoveredClassName]);

  // Debounce hover callback for smoother performance (50ms)
  const debouncedOnChunkHover = useDebounce(
    useCallback((chunkId: string | null) => {
      if (onChunkHover) {
        onChunkHover(chunkId);
      }
    }, [onChunkHover]),
    50
  );

  /**
   * Setup hover event listeners
   */
  useEffect(() => {
    const container = containerRef.current;
    if (!container || !onChunkHover) return;

    const handleMouseEnter = (event: Event) => {
      const target = event.target as HTMLElement;
      const chunkElement = target.closest('[data-chunk-id]') as HTMLElement;
      if (chunkElement) {
        const chunkId = chunkElement.getAttribute('data-chunk-id');
        if (chunkId) {
          debouncedOnChunkHover(chunkId);
        }
      }
    };

    const handleMouseLeave = (event: Event) => {
      const target = event.target as HTMLElement;
      const chunkElement = target.closest('[data-chunk-id]') as HTMLElement;
      if (chunkElement) {
        // Check if we're actually leaving the chunk (not just moving to a child)
        const relatedTarget = (event as MouseEvent).relatedTarget as HTMLElement;
        if (!chunkElement.contains(relatedTarget)) {
          debouncedOnChunkHover(null);
        }
      }
    };

    // Use event delegation for better performance
    container.addEventListener('mouseenter', handleMouseEnter, true);
    container.addEventListener('mouseleave', handleMouseLeave, true);

    return () => {
      container.removeEventListener('mouseenter', handleMouseEnter, true);
      container.removeEventListener('mouseleave', handleMouseLeave, true);
    };
  }, [containerRef, onChunkHover, debouncedOnChunkHover]);

  /**
   * Programmatically highlight a chunk
   */
  const highlightChunk = useCallback(
    (chunkId: string) => {
      const element = getChunkElement(chunkId);
      if (element) {
        element.classList.add(activeClassName);
        // Also set focus for accessibility
        element.setAttribute('tabindex', '-1');
        element.focus({ preventScroll: true });
      }
    },
    [getChunkElement, activeClassName]
  );

  /**
   * Clear all highlighting
   */
  const clearHighlight = useCallback(() => {
    getAllChunks().forEach((chunk) => {
      chunk.classList.remove(activeClassName, hoveredClassName);
      chunk.removeAttribute('tabindex');
    });
  }, [getAllChunks, activeClassName, hoveredClassName]);

  /**
   * Scroll to a specific chunk
   */
  const scrollToChunkHandler = useCallback(
    async (chunkId: string, customOptions?: ScrollToChunkOptions) => {
      const options = {
        behavior: scrollBehavior,
        block: 'center' as ScrollLogicalPosition,
        offset: scrollOffset,
        ...customOptions,
      };

      await scrollToChunk(chunkId, containerRef.current, options);
    },
    [scrollBehavior, scrollOffset, containerRef]
  );

  /**
   * Check if a chunk is active
   */
  const isActive = useCallback(
    (chunkId: string): boolean => {
      return activeChunkId === chunkId;
    },
    [activeChunkId]
  );

  /**
   * Check if a chunk is hovered
   */
  const isHovered = useCallback(
    (chunkId: string): boolean => {
      return hoveredChunkId === chunkId;
    },
    [hoveredChunkId]
  );

  return {
    highlightChunk,
    clearHighlight,
    scrollToChunk: scrollToChunkHandler,
    isActive,
    isHovered,
  };
}

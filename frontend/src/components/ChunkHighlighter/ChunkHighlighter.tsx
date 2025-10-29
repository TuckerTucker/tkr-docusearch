/**
 * ChunkHighlighter Component
 *
 * Agent 7: Chunk Highlighter Component
 * Wave 1 - BBox Overlay React Implementation
 * Agent 12: Performance Optimizer - Wave 3
 *
 * Wrapper component that adds chunk highlighting capabilities to markdown content.
 * Automatically adds data-chunk-id attributes to elements and manages highlighting state.
 *
 * Performance optimizations:
 * - Memoized component to prevent unnecessary re-renders
 * - Memoized callbacks for event handlers
 * - Debounced hover interactions
 */

import React, { useRef, useEffect, ReactNode, useCallback } from 'react';
import { useChunkHighlight } from './useChunkHighlight';
import { announceToScreenReader, generateChunkDescription } from '../../utils/accessibility';
import styles from './ChunkHighlighter.module.css';

export interface ChunkHighlighterProps {
  /**
   * The content to render with chunk highlighting support
   */
  children: ReactNode;
  /**
   * The ID of the currently active chunk
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
   * Callback fired when a chunk is clicked
   */
  onChunkClick?: (chunkId: string) => void;
  /**
   * Whether to automatically scroll to active chunk
   * @default true
   */
  autoScroll?: boolean;
  /**
   * Offset from top for scrolling (useful for fixed headers)
   * @default 0
   */
  scrollOffset?: number;
  /**
   * Scroll behavior
   * @default 'smooth'
   */
  scrollBehavior?: ScrollBehavior;
  /**
   * Additional CSS class name for the container
   */
  className?: string;
  /**
   * Whether to add chunk IDs to block-level elements automatically
   * @default true
   */
  autoAddChunkIds?: boolean;
  /**
   * Custom chunk ID prefix
   * @default 'chunk'
   */
  chunkIdPrefix?: string;
}

/**
 * Component that wraps content to enable chunk highlighting.
 *
 * This component:
 * - Wraps content in a container with chunk highlighting support
 * - Automatically adds data-chunk-id attributes to elements
 * - Manages active and hovered states
 * - Provides smooth scrolling to chunks
 * - Handles accessibility (focus management, keyboard navigation)
 *
 * @example
 * ```tsx
 * <ChunkHighlighter
 *   activeChunkId={activeChunk}
 *   onChunkHover={handleChunkHover}
 *   onChunkClick={handleChunkClick}
 *   scrollOffset={80}
 * >
 *   <div data-chunk-id="chunk-1">First paragraph</div>
 *   <div data-chunk-id="chunk-2">Second paragraph</div>
 * </ChunkHighlighter>
 * ```
 */
export const ChunkHighlighter: React.FC<ChunkHighlighterProps> = React.memo(({
  children,
  activeChunkId,
  hoveredChunkId,
  onChunkHover,
  onChunkClick,
  autoScroll = true,
  scrollOffset = 0,
  scrollBehavior = 'smooth',
  className,
  autoAddChunkIds = true,
  chunkIdPrefix = 'chunk',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  // Use the chunk highlight hook
  const { isActive, isHovered } = useChunkHighlight({
    containerRef,
    activeChunkId,
    hoveredChunkId,
    onChunkHover,
    scrollBehavior,
    scrollOffset,
    autoScrollToActive: autoScroll,
  });

  /**
   * Automatically add chunk IDs and ARIA attributes to block elements
   */
  useEffect(() => {
    if (!autoAddChunkIds || !containerRef.current) return;

    const blockElements = containerRef.current.querySelectorAll(
      'p, h1, h2, h3, h4, h5, h6, li, blockquote, pre, div.chunk-item'
    );

    let chunkCounter = 0;

    blockElements.forEach((element) => {
      const htmlElement = element as HTMLElement;
      // Only add ID if element doesn't already have one
      if (!htmlElement.hasAttribute('data-chunk-id')) {
        const chunkId = `${chunkIdPrefix}-${chunkCounter++}`;
        htmlElement.setAttribute('data-chunk-id', chunkId);
        // Make element focusable for accessibility
        htmlElement.setAttribute('tabindex', '-1');
        // Add ARIA role for screen readers
        htmlElement.setAttribute('role', 'article');
        // Add descriptive ARIA label
        const elementName = htmlElement.tagName.toLowerCase();
        htmlElement.setAttribute('aria-label', `Content chunk ${chunkCounter}: ${elementName}`);
      }
    });
  }, [children, autoAddChunkIds, chunkIdPrefix]);

  /**
   * Handle click events on chunks with screen reader announcements - memoized
   */
  const handleClick = useCallback((event: MouseEvent) => {
    if (!onChunkClick) return;

    const target = event.target as HTMLElement;
    const chunkElement = target.closest('[data-chunk-id]') as HTMLElement;
    if (chunkElement) {
      const chunkId = chunkElement.getAttribute('data-chunk-id');
      if (chunkId) {
        onChunkClick(chunkId);
        // Announce to screen readers
        const description = generateChunkDescription(chunkId, true, false);
        announceToScreenReader(`Selected: ${description}`, 'polite');
      }
    }
  }, [onChunkClick]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !onChunkClick) return;

    container.addEventListener('click', handleClick);

    return () => {
      container.removeEventListener('click', handleClick);
    };
  }, [onChunkClick, handleClick]);

  /**
   * Handle keyboard navigation with screen reader announcements - memoized
   */
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    const container = containerRef.current;
    if (!container) return;

    // Only handle if focus is on a chunk element
    const target = event.target as HTMLElement;
    if (!target.hasAttribute('data-chunk-id')) return;

    const allChunks = Array.from(
      container.querySelectorAll('[data-chunk-id]')
    ) as HTMLElement[];
    const currentIndex = allChunks.indexOf(target);

    let nextElement: HTMLElement | null = null;
    let navigationDirection = '';

    switch (event.key) {
      case 'ArrowDown':
      case 'ArrowRight':
        // Move to next chunk
        if (currentIndex < allChunks.length - 1) {
          nextElement = allChunks[currentIndex + 1];
          navigationDirection = 'next';
        }
        break;
      case 'ArrowUp':
      case 'ArrowLeft':
        // Move to previous chunk
        if (currentIndex > 0) {
          nextElement = allChunks[currentIndex - 1];
          navigationDirection = 'previous';
        }
        break;
      case 'Home':
        // Move to first chunk
        nextElement = allChunks[0];
        navigationDirection = 'first';
        break;
      case 'End':
        // Move to last chunk
        nextElement = allChunks[allChunks.length - 1];
        navigationDirection = 'last';
        break;
      case 'Enter':
      case ' ':
        // Activate current chunk
        event.preventDefault();
        const chunkId = target.getAttribute('data-chunk-id');
        if (chunkId && onChunkClick) {
          onChunkClick(chunkId);
          const description = generateChunkDescription(chunkId, true, false);
          announceToScreenReader(`Activated: ${description}`, 'polite');
        }
        return;
    }

    if (nextElement) {
      event.preventDefault();
      nextElement.focus();
      nextElement.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      });

      // Announce navigation to screen readers
      const nextChunkId = nextElement.getAttribute('data-chunk-id');
      if (nextChunkId) {
        const announcement = `Navigated to ${navigationDirection} chunk: ${nextChunkId}`;
        announceToScreenReader(announcement, 'polite');
      }
    }
  }, [onChunkClick]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    container.addEventListener('keydown', handleKeyDown);

    return () => {
      container.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);

  /**
   * Announce active chunk changes to screen readers
   */
  useEffect(() => {
    if (activeChunkId && containerRef.current) {
      const activeElement = containerRef.current.querySelector(
        `[data-chunk-id="${CSS.escape(activeChunkId)}"]`
      ) as HTMLElement;

      if (activeElement) {
        // Mark element as current for screen readers
        activeElement.setAttribute('aria-current', 'true');
        const description = generateChunkDescription(activeChunkId, true, false);
        announceToScreenReader(`Active chunk: ${description}`, 'polite');
      }

      // Clean up previous active elements
      return () => {
        if (activeElement) {
          activeElement.removeAttribute('aria-current');
        }
      };
    }
  }, [activeChunkId]);

  return (
    <div
      ref={containerRef}
      className={`${styles.chunkHighlighter} ${className || ''}`}
      role="region"
      aria-label="Highlighted content with navigable chunks"
      aria-live="polite"
      aria-atomic="false"
    >
      {children}
    </div>
  );
});

ChunkHighlighter.displayName = 'ChunkHighlighter';

export default ChunkHighlighter;

/**
 * useAccessibleNavigation Hook
 *
 * Agent 11: Accessibility Specialist
 * Wave 3 - BBox Overlay React Implementation
 *
 * React hook for managing keyboard navigation, focus management, and
 * screen reader announcements for accessible bounding box and chunk interaction.
 *
 * Features:
 * - Arrow key navigation between bboxes (←/→/↑/↓)
 * - Tab key to cycle through chunks
 * - Enter/Space to activate bbox/chunk
 * - Escape to clear active selection
 * - Focus management with restoration
 * - Screen reader announcements
 *
 * @example
 * ```typescript
 * const {
 *   handleKeyDown,
 *   currentFocusIndex,
 *   announceNavigation,
 * } = useAccessibleNavigation({
 *   elements: bboxElements,
 *   onActivate: (index) => handleBboxClick(index),
 *   onEscape: () => clearSelection(),
 * });
 * ```
 */

import { useState, useCallback, useEffect, useRef, RefObject } from 'react';
import {
  announceToScreenReader,
  getArrowDirection,
  isActivationKey,
  isEscapeKey,
  getNextElementIndex,
  moveFocusToElement,
  restoreFocus,
  generateBBoxLabel,
  generateChunkDescription,
} from '../utils/accessibility';

/**
 * Options for useAccessibleNavigation hook
 */
export interface UseAccessibleNavigationOptions {
  /**
   * Container element reference
   */
  containerRef: RefObject<HTMLElement>;

  /**
   * Whether navigation is enabled
   * @default true
   */
  enabled?: boolean;

  /**
   * Callback fired when an element is activated (Enter/Space)
   */
  onActivate?: (index: number, element: HTMLElement) => void;

  /**
   * Callback fired when navigation occurs
   */
  onNavigate?: (index: number, element: HTMLElement) => void;

  /**
   * Callback fired when escape is pressed
   */
  onEscape?: () => void;

  /**
   * Callback fired when tab is pressed
   */
  onTab?: (shiftKey: boolean) => void;

  /**
   * Selector for navigable elements
   * @default '[data-chunk-id], [role="button"]'
   */
  elementSelector?: string;

  /**
   * Whether to announce navigation to screen readers
   * @default true
   */
  announceNavigation?: boolean;

  /**
   * Whether to wrap around at start/end
   * @default false
   */
  wrapNavigation?: boolean;

  /**
   * Whether to prevent default behavior for handled keys
   * @default true
   */
  preventDefault?: boolean;

  /**
   * Custom announcement generator
   */
  generateAnnouncement?: (
    element: HTMLElement,
    index: number,
    action: 'navigate' | 'activate'
  ) => string;
}

/**
 * Return value of useAccessibleNavigation hook
 */
export interface UseAccessibleNavigationResult {
  /**
   * Current focused element index
   */
  currentFocusIndex: number | null;

  /**
   * Total number of navigable elements
   */
  totalElements: number;

  /**
   * Manually set focus to an element by index
   */
  focusElement: (index: number) => void;

  /**
   * Navigate to next element
   */
  navigateNext: () => void;

  /**
   * Navigate to previous element
   */
  navigatePrevious: () => void;

  /**
   * Navigate to first element
   */
  navigateFirst: () => void;

  /**
   * Navigate to last element
   */
  navigateLast: () => void;

  /**
   * Clear focus and reset state
   */
  clearFocus: () => void;

  /**
   * Get all navigable elements
   */
  getElements: () => HTMLElement[];

  /**
   * Announce a message to screen readers
   */
  announce: (message: string, priority?: 'polite' | 'assertive') => void;
}

/**
 * Hook for managing accessible keyboard navigation
 */
export function useAccessibleNavigation(
  options: UseAccessibleNavigationOptions
): UseAccessibleNavigationResult {
  const {
    containerRef,
    enabled = true,
    onActivate,
    onNavigate,
    onEscape,
    onTab,
    elementSelector = '[data-chunk-id], [role="button"]',
    announceNavigation = true,
    wrapNavigation = false,
    preventDefault = true,
    generateAnnouncement,
  } = options;

  const [currentFocusIndex, setCurrentFocusIndex] = useState<number | null>(
    null
  );
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const elementsRef = useRef<HTMLElement[]>([]);

  /**
   * Gets all navigable elements in the container
   */
  const getElements = useCallback((): HTMLElement[] => {
    if (!containerRef.current) return [];
    return Array.from(
      containerRef.current.querySelectorAll<HTMLElement>(elementSelector)
    ).filter((el) => {
      // Filter out elements that are not visible or disabled
      return (
        el.offsetWidth > 0 &&
        el.offsetHeight > 0 &&
        !el.hasAttribute('disabled') &&
        !el.hasAttribute('aria-disabled')
      );
    });
  }, [containerRef, elementSelector]);

  /**
   * Updates the cached elements list
   */
  const updateElements = useCallback(() => {
    elementsRef.current = getElements();
  }, [getElements]);

  /**
   * Gets the current index of the focused element
   */
  const getCurrentIndex = useCallback((): number => {
    const activeElement = document.activeElement as HTMLElement;
    return elementsRef.current.indexOf(activeElement);
  }, []);

  /**
   * Generates an announcement for an element
   */
  const generateDefaultAnnouncement = useCallback(
    (
      element: HTMLElement,
      index: number,
      action: 'navigate' | 'activate'
    ): string => {
      if (generateAnnouncement) {
        return generateAnnouncement(element, index, action);
      }

      const elementType =
        element.getAttribute('data-element-type') || 'element';
      const chunkId = element.getAttribute('data-chunk-id');
      const isActive = element.getAttribute('aria-pressed') === 'true';
      const isHovered = element.classList.contains('hovered');

      if (chunkId) {
        return generateChunkDescription(chunkId, isActive, isHovered);
      }

      const actionText = action === 'activate' ? 'Activated' : 'Navigated to';
      return `${actionText} ${generateBBoxLabel(elementType, index)}`;
    },
    [generateAnnouncement]
  );

  /**
   * Announces a message to screen readers
   */
  const announce = useCallback(
    (message: string, priority: 'polite' | 'assertive' = 'polite') => {
      if (announceNavigation) {
        announceToScreenReader(message, priority);
      }
    },
    [announceNavigation]
  );

  /**
   * Focuses an element by index
   */
  const focusElement = useCallback(
    (index: number) => {
      updateElements();
      const elements = elementsRef.current;

      if (index < 0 || index >= elements.length) {
        return;
      }

      const element = elements[index];
      if (element) {
        // Store previous focus
        if (document.activeElement instanceof HTMLElement) {
          previousFocusRef.current = document.activeElement;
        }

        // Move focus
        const success = moveFocusToElement(element, { preventScroll: false });

        if (success) {
          setCurrentFocusIndex(index);

          // Announce navigation
          const announcement = generateDefaultAnnouncement(
            element,
            index,
            'navigate'
          );
          announce(announcement);

          // Fire callback
          if (onNavigate) {
            onNavigate(index, element);
          }
        }
      }
    },
    [updateElements, announce, generateDefaultAnnouncement, onNavigate]
  );

  /**
   * Navigates to the next element
   */
  const navigateNext = useCallback(() => {
    updateElements();
    const elements = elementsRef.current;
    const currentIndex = getCurrentIndex();

    let nextIndex: number | null = null;

    if (currentIndex === -1) {
      // No element focused, focus first
      nextIndex = 0;
    } else if (currentIndex < elements.length - 1) {
      // Move to next element
      nextIndex = currentIndex + 1;
    } else if (wrapNavigation) {
      // Wrap to first element
      nextIndex = 0;
    }

    if (nextIndex !== null) {
      focusElement(nextIndex);
    }
  }, [updateElements, getCurrentIndex, wrapNavigation, focusElement]);

  /**
   * Navigates to the previous element
   */
  const navigatePrevious = useCallback(() => {
    updateElements();
    const elements = elementsRef.current;
    const currentIndex = getCurrentIndex();

    let prevIndex: number | null = null;

    if (currentIndex === -1) {
      // No element focused, focus last
      prevIndex = elements.length - 1;
    } else if (currentIndex > 0) {
      // Move to previous element
      prevIndex = currentIndex - 1;
    } else if (wrapNavigation) {
      // Wrap to last element
      prevIndex = elements.length - 1;
    }

    if (prevIndex !== null) {
      focusElement(prevIndex);
    }
  }, [updateElements, getCurrentIndex, wrapNavigation, focusElement]);

  /**
   * Navigates to the first element
   */
  const navigateFirst = useCallback(() => {
    updateElements();
    if (elementsRef.current.length > 0) {
      focusElement(0);
    }
  }, [updateElements, focusElement]);

  /**
   * Navigates to the last element
   */
  const navigateLast = useCallback(() => {
    updateElements();
    const elements = elementsRef.current;
    if (elements.length > 0) {
      focusElement(elements.length - 1);
    }
  }, [updateElements, focusElement]);

  /**
   * Clears focus and restores previous focus
   */
  const clearFocus = useCallback(() => {
    setCurrentFocusIndex(null);

    // Restore previous focus if available
    if (previousFocusRef.current) {
      restoreFocus(previousFocusRef.current);
      previousFocusRef.current = null;
    }

    // Announce
    announce('Selection cleared');

    // Fire callback
    if (onEscape) {
      onEscape();
    }
  }, [announce, onEscape]);

  /**
   * Handles keyboard events for navigation
   */
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return;

      const target = event.target as HTMLElement;
      if (!containerRef.current?.contains(target)) return;

      // Check if target is a navigable element
      const elements = getElements();
      const currentIndex = elements.indexOf(target);
      if (currentIndex === -1) return;

      let handled = false;

      // Arrow key navigation
      const direction = getArrowDirection(event);
      if (direction) {
        handled = true;
        if (direction === 'down' || direction === 'right') {
          navigateNext();
        } else if (direction === 'up' || direction === 'left') {
          navigatePrevious();
        }
      }

      // Home/End navigation
      if (event.key === 'Home') {
        handled = true;
        navigateFirst();
      } else if (event.key === 'End') {
        handled = true;
        navigateLast();
      }

      // Tab navigation
      if (event.key === 'Tab') {
        if (onTab) {
          onTab(event.shiftKey);
        }
      }

      // Activation keys (Enter/Space)
      if (isActivationKey(event)) {
        handled = true;
        if (onActivate) {
          onActivate(currentIndex, target);
        }

        // Announce activation
        const announcement = generateDefaultAnnouncement(
          target,
          currentIndex,
          'activate'
        );
        announce(announcement, 'polite');
      }

      // Escape key
      if (isEscapeKey(event)) {
        handled = true;
        clearFocus();
      }

      // Prevent default if we handled the event
      if (handled && preventDefault) {
        event.preventDefault();
      }
    },
    [
      enabled,
      containerRef,
      getElements,
      navigateNext,
      navigatePrevious,
      navigateFirst,
      navigateLast,
      onTab,
      onActivate,
      clearFocus,
      preventDefault,
      generateDefaultAnnouncement,
      announce,
    ]
  );

  /**
   * Setup keyboard event listener
   */
  useEffect(() => {
    if (!enabled || !containerRef.current) return;

    const container = containerRef.current;
    container.addEventListener('keydown', handleKeyDown);

    return () => {
      container.removeEventListener('keydown', handleKeyDown);
    };
  }, [enabled, containerRef, handleKeyDown]);

  /**
   * Update elements when container changes
   */
  useEffect(() => {
    updateElements();
  }, [updateElements]);

  return {
    currentFocusIndex,
    totalElements: elementsRef.current.length,
    focusElement,
    navigateNext,
    navigatePrevious,
    navigateFirst,
    navigateLast,
    clearFocus,
    getElements,
    announce,
  };
}

/**
 * useKeyboardNav Hook - Keyboard navigation handler
 *
 * Handles keyboard events for navigation (arrow keys, Escape, Enter).
 *
 * Provider: infrastructure-agent (Wave 1)
 * Contract: integration-contracts/hooks.contract.md
 */

import { useEffect } from 'react';

/**
 * Hook for keyboard navigation
 *
 * Handles keyboard events for navigation (arrow keys, Escape, Enter).
 * Automatically ignores events when focus is in input/textarea/select elements.
 *
 * @param {Object} [config={}] - Navigation configuration
 * @param {Function} [config.onArrowLeft] - Left arrow handler
 * @param {Function} [config.onArrowRight] - Right arrow handler
 * @param {Function} [config.onArrowUp] - Up arrow handler
 * @param {Function} [config.onArrowDown] - Down arrow handler
 * @param {Function} [config.onEscape] - Escape key handler
 * @param {Function} [config.onEnter] - Enter key handler
 * @param {boolean} [config.enabled=true] - Enable/disable keyboard navigation
 *
 * @example
 * // Image gallery navigation
 * const [currentImage, setCurrentImage] = useState(0);
 * const images = ['img1.jpg', 'img2.jpg', 'img3.jpg'];
 *
 * useKeyboardNav({
 *   onArrowLeft: () => setCurrentImage(prev => Math.max(0, prev - 1)),
 *   onArrowRight: () => setCurrentImage(prev => Math.min(images.length - 1, prev + 1)),
 *   onEscape: () => setCurrentImage(0),
 * });
 *
 * @example
 * // Modal with Enter/Escape handling
 * const [isModalOpen, setIsModalOpen] = useState(false);
 *
 * useKeyboardNav({
 *   onEscape: () => setIsModalOpen(false),
 *   onEnter: () => handleSubmit(),
 *   enabled: isModalOpen,
 * });
 *
 * @example
 * // Document viewer with arrow navigation
 * useKeyboardNav({
 *   onArrowUp: () => scrollUp(),
 *   onArrowDown: () => scrollDown(),
 *   onArrowLeft: () => previousPage(),
 *   onArrowRight: () => nextPage(),
 * });
 */
export function useKeyboardNav(config = {}) {
  const {
    onArrowLeft,
    onArrowRight,
    onArrowUp,
    onArrowDown,
    onEscape,
    onEnter,
    enabled = true,
  } = config;

  useEffect(() => {
    if (!enabled) return;

    /**
     * Handle keyboard event
     *
     * @param {KeyboardEvent} event - Keyboard event
     */
    const handleKeyDown = (event) => {
      // Don't trigger if focus is in input/textarea/select
      const tagName = event.target.tagName.toLowerCase();
      if (tagName === 'input' || tagName === 'textarea' || tagName === 'select') {
        return;
      }

      let handled = false;

      switch (event.key) {
        case 'ArrowLeft':
          if (onArrowLeft) {
            onArrowLeft();
            handled = true;
          }
          break;

        case 'ArrowRight':
          if (onArrowRight) {
            onArrowRight();
            handled = true;
          }
          break;

        case 'ArrowUp':
          if (onArrowUp) {
            onArrowUp();
            handled = true;
          }
          break;

        case 'ArrowDown':
          if (onArrowDown) {
            onArrowDown();
            handled = true;
          }
          break;

        case 'Escape':
          if (onEscape) {
            onEscape();
            handled = true;
          }
          break;

        case 'Enter':
          if (onEnter) {
            onEnter();
            handled = true;
          }
          break;

        default:
          break;
      }

      // Prevent default browser behavior for handled keys
      if (handled) {
        event.preventDefault();
      }
    };

    document.addEventListener('keydown', handleKeyDown);

    // Cleanup
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [onArrowLeft, onArrowRight, onArrowUp, onArrowDown, onEscape, onEnter, enabled]);
}

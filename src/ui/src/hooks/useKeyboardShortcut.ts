/**
 * Keyboard Shortcut Hook - DocuSearch UI
 * Provider: Wave 3 (Polish & Refinement)
 *
 * Custom hook for managing keyboard shortcuts
 */

import { useEffect, useCallback } from 'react';

export type KeyCombo = {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  meta?: boolean;
};

/**
 * Keyboard shortcut hook
 *
 * Registers a keyboard shortcut and calls the callback when triggered
 *
 * @param combo - Key combination to listen for
 * @param callback - Function to call when shortcut is triggered
 * @param enabled - Whether the shortcut is enabled (default: true)
 *
 * @example
 * useKeyboardShortcut({ key: 'k', ctrl: true }, () => {
 *   console.log('Ctrl+K pressed');
 * });
 */
export function useKeyboardShortcut(
  combo: KeyCombo,
  callback: () => void,
  enabled = true
): void {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      // Check if the key combo matches
      const keyMatches = event.key.toLowerCase() === combo.key.toLowerCase();
      const ctrlMatches = combo.ctrl === undefined || event.ctrlKey === combo.ctrl;
      const shiftMatches = combo.shift === undefined || event.shiftKey === combo.shift;
      const altMatches = combo.alt === undefined || event.altKey === combo.alt;
      const metaMatches = combo.meta === undefined || event.metaKey === combo.meta;

      if (keyMatches && ctrlMatches && shiftMatches && altMatches && metaMatches) {
        // Don't trigger if user is typing in an input/textarea
        const target = event.target as HTMLElement;
        if (
          target.tagName === 'INPUT' ||
          target.tagName === 'TEXTAREA' ||
          target.isContentEditable
        ) {
          return;
        }

        event.preventDefault();
        callback();
      }
    },
    [combo, callback]
  );

  useEffect(() => {
    if (!enabled) return;

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown, enabled]);
}

/**
 * Multiple keyboard shortcuts hook
 *
 * Registers multiple keyboard shortcuts at once
 *
 * @param shortcuts - Array of shortcut configurations
 * @param enabled - Whether shortcuts are enabled (default: true)
 *
 * @example
 * useKeyboardShortcuts([
 *   { combo: { key: 'k', ctrl: true }, callback: openSearch },
 *   { combo: { key: 'u', ctrl: true }, callback: openUpload },
 * ]);
 */
export function useKeyboardShortcuts(
  shortcuts: Array<{ combo: KeyCombo; callback: () => void }>,
  enabled = true
): void {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      for (const { combo, callback } of shortcuts) {
        const keyMatches = event.key.toLowerCase() === combo.key.toLowerCase();
        const ctrlMatches = combo.ctrl === undefined || event.ctrlKey === combo.ctrl;
        const shiftMatches = combo.shift === undefined || event.shiftKey === combo.shift;
        const altMatches = combo.alt === undefined || event.altKey === combo.alt;
        const metaMatches = combo.meta === undefined || event.metaKey === combo.meta;

        if (keyMatches && ctrlMatches && shiftMatches && altMatches && metaMatches) {
          // Don't trigger if user is typing in an input/textarea
          const target = event.target as HTMLElement;
          if (
            target.tagName === 'INPUT' ||
            target.tagName === 'TEXTAREA' ||
            target.isContentEditable
          ) {
            continue;
          }

          event.preventDefault();
          callback();
          break; // Only trigger first matching shortcut
        }
      }
    },
    [shortcuts]
  );

  useEffect(() => {
    if (!enabled) return;

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown, enabled]);
}

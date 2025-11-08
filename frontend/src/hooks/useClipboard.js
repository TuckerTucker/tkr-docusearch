/**
 * useClipboard Hook - Copy text to clipboard with feedback
 *
 * Provides clipboard functionality with automatic reset after 2 seconds.
 *
 * Provider: infrastructure-agent (Wave 1)
 * Contract: integration-contracts/hooks.contract.md
 */

import { useState } from 'react';

/**
 * Hook for clipboard operations
 *
 * Provides clipboard functionality with automatic feedback reset after 2 seconds.
 * Includes fallback for older browsers without Clipboard API support.
 *
 * @returns {Object} Clipboard interface
 * @returns {Function} returns.copy - Async function to copy text to clipboard
 * @returns {boolean} returns.isCopied - Success state (true for 2 seconds after copy)
 * @returns {Error|null} returns.error - Error object if copy failed
 *
 * @example
 * // Basic copy with feedback
 * const { copy, isCopied } = useClipboard();
 *
 * const handleCopy = async () => {
 *   await copy('Text to copy to clipboard');
 * };
 *
 * return (
 *   <button onClick={handleCopy}>
 *     {isCopied ? 'Copied!' : 'Copy'}
 *   </button>
 * );
 *
 * @example
 * // Copy with error handling
 * const { copy, isCopied, error } = useClipboard();
 *
 * const handleCopy = async (text) => {
 *   await copy(text);
 *   if (error) {
 *     console.error('Failed to copy:', error);
 *   }
 * };
 */
export function useClipboard() {
  const [isCopied, setIsCopied] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Copy text to clipboard
   *
   * @param {string} text - Text to copy
   * @returns {Promise<void>}
   */
  const copy = async (text) => {
    try {
      // Try modern Clipboard API first
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        setIsCopied(true);
        setError(null);
      } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        const successful = document.execCommand('copy');
        textArea.remove();

        if (successful) {
          setIsCopied(true);
          setError(null);
        } else {
          throw new Error('Copy command failed');
        }
      }

      // Reset after 2 seconds
      setTimeout(() => {
        setIsCopied(false);
      }, 2000);
    } catch (err) {
      console.error('Failed to copy text:', err);
      setError(err);
      setIsCopied(false);
    }
  };

  return {
    copy,
    isCopied,
    error,
  };
}

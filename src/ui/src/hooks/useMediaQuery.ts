/**
 * useMediaQuery Hook - DocuSearch UI
 * Provider: Hook utilities
 * Consumers: All responsive components
 *
 * Task 6: Mobile responsive layouts
 */

import { useState, useEffect } from 'react';

/**
 * Custom hook for responsive media queries
 *
 * Listens to window.matchMedia changes and returns boolean match status
 *
 * @param query - Media query string (e.g., "(max-width: 640px)")
 * @returns Boolean indicating if media query matches
 *
 * @example
 * const isMobile = useMediaQuery('(max-width: 640px)');
 * const isTablet = useMediaQuery('(min-width: 640px) and (max-width: 1024px)');
 * const isDesktop = useMediaQuery('(min-width: 1024px)');
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const media = window.matchMedia(query);

    // Set initial value
    setMatches(media.matches);

    // Listen for changes
    const listener = (e: MediaQueryListEvent) => setMatches(e.matches);
    media.addEventListener('change', listener);

    return () => media.removeEventListener('change', listener);
  }, [query]);

  return matches;
}

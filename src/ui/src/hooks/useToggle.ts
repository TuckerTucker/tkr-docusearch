/**
 * Toggle State Hook - DocuSearch UI
 * Provider: Agent 2 (Design System Engineer)
 * Consumers: Agent 3, Agent 4, Agent 5
 */

import { useState, useCallback } from 'react';

/**
 * Hook for managing boolean toggle state
 *
 * @param initialValue - Initial state (default: false)
 * @returns Tuple of [state, toggle, setTrue, setFalse]
 *
 * @example
 * const [isExpanded, toggleExpanded, expand, collapse] = useToggle(false);
 *
 * <button onClick={toggleExpanded}>Toggle</button>
 * <button onClick={expand}>Open</button>
 * <button onClick={collapse}>Close</button>
 */
export function useToggle(
  initialValue = false
): [boolean, () => void, () => void, () => void] {
  const [state, setState] = useState(initialValue);

  const toggle = useCallback(() => {
    setState(prev => !prev);
  }, []);

  const setTrue = useCallback(() => {
    setState(true);
  }, []);

  const setFalse = useCallback(() => {
    setState(false);
  }, []);

  return [state, toggle, setTrue, setFalse];
}

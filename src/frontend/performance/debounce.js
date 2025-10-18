/**
 * Debounce and Throttle Utilities
 *
 * Performance optimization utilities for rate-limiting function calls.
 * Prevents excessive event handler firing during frequent events like
 * resize, scroll, and hover.
 *
 * Wave 3 - Agent 13: Performance Optimizer
 *
 * @module debounce
 */

/**
 * Debounce a function call - delays execution until after a quiet period.
 * Useful for events that fire many times in succession but you only care
 * about the final state (e.g., window resize, search input).
 *
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds (default: 150ms)
 * @param {Object} options - Configuration options
 * @param {boolean} options.leading - Execute on leading edge (default: false)
 * @param {boolean} options.trailing - Execute on trailing edge (default: true)
 * @param {number} options.maxWait - Maximum time to wait before forcing execution
 * @returns {Function} Debounced function with cancel() method
 *
 * @example
 * const handleResize = debounce(() => {
 *   console.log('Window resized!');
 * }, 150);
 *
 * window.addEventListener('resize', handleResize);
 *
 * // Later, cancel pending execution:
 * handleResize.cancel();
 */
export function debounce(func, wait = 150, options = {}) {
  if (typeof func !== 'function') {
    throw new TypeError('Expected a function');
  }

  let timerId = null;
  let lastCallTime = 0;
  let lastInvokeTime = 0;
  let lastArgs = null;
  let lastThis = null;
  let result = undefined;

  const leading = options.leading !== undefined ? options.leading : false;
  const trailing = options.trailing !== undefined ? options.trailing : true;
  const maxWait = options.maxWait;

  /**
   * Invoke the debounced function
   */
  function invokeFunc(time) {
    const args = lastArgs;
    const thisArg = lastThis;

    lastArgs = lastThis = null;
    lastInvokeTime = time;
    result = func.apply(thisArg, args);
    return result;
  }

  /**
   * Handle leading edge execution
   */
  function leadingEdge(time) {
    lastInvokeTime = time;
    timerId = setTimeout(timerExpired, wait);
    return leading ? invokeFunc(time) : result;
  }

  /**
   * Calculate remaining wait time
   */
  function remainingWait(time) {
    const timeSinceLastCall = time - lastCallTime;
    const timeSinceLastInvoke = time - lastInvokeTime;
    const timeWaiting = wait - timeSinceLastCall;

    return maxWait !== undefined
      ? Math.min(timeWaiting, maxWait - timeSinceLastInvoke)
      : timeWaiting;
  }

  /**
   * Check if function should be invoked
   */
  function shouldInvoke(time) {
    const timeSinceLastCall = time - lastCallTime;
    const timeSinceLastInvoke = time - lastInvokeTime;

    return (
      lastCallTime === 0 ||
      timeSinceLastCall >= wait ||
      timeSinceLastCall < 0 ||
      (maxWait !== undefined && timeSinceLastInvoke >= maxWait)
    );
  }

  /**
   * Handle timer expiration
   */
  function timerExpired() {
    const time = Date.now();
    if (shouldInvoke(time)) {
      return trailingEdge(time);
    }
    // Restart timer with remaining time
    timerId = setTimeout(timerExpired, remainingWait(time));
  }

  /**
   * Handle trailing edge execution
   */
  function trailingEdge(time) {
    timerId = null;

    if (trailing && lastArgs) {
      return invokeFunc(time);
    }
    lastArgs = lastThis = null;
    return result;
  }

  /**
   * Cancel pending execution
   */
  function cancel() {
    if (timerId !== null) {
      clearTimeout(timerId);
    }
    lastInvokeTime = 0;
    lastArgs = lastCallTime = lastThis = timerId = null;
  }

  /**
   * Immediately invoke the function and cancel pending execution
   */
  function flush() {
    return timerId === null ? result : trailingEdge(Date.now());
  }

  /**
   * Check if function is pending
   */
  function pending() {
    return timerId !== null;
  }

  /**
   * The debounced function
   */
  function debounced(...args) {
    const time = Date.now();
    const isInvoking = shouldInvoke(time);

    lastArgs = args;
    lastThis = this;
    lastCallTime = time;

    if (isInvoking) {
      if (timerId === null) {
        return leadingEdge(lastCallTime);
      }
      if (maxWait !== undefined) {
        // Handle invocations in a tight loop
        timerId = setTimeout(timerExpired, wait);
        return invokeFunc(lastCallTime);
      }
    }
    if (timerId === null) {
      timerId = setTimeout(timerExpired, wait);
    }
    return result;
  }

  // Attach utility methods
  debounced.cancel = cancel;
  debounced.flush = flush;
  debounced.pending = pending;

  return debounced;
}

/**
 * Throttle a function call - limits execution rate to at most once per interval.
 * Useful for events that fire continuously but you want regular updates
 * (e.g., scroll position tracking).
 *
 * @param {Function} func - Function to throttle
 * @param {number} limit - Minimum time between calls in milliseconds (default: 100ms)
 * @param {Object} options - Configuration options
 * @param {boolean} options.leading - Execute on leading edge (default: true)
 * @param {boolean} options.trailing - Execute on trailing edge (default: true)
 * @returns {Function} Throttled function with cancel() method
 *
 * @example
 * const handleScroll = throttle(() => {
 *   console.log('Scroll position:', window.scrollY);
 * }, 100);
 *
 * window.addEventListener('scroll', handleScroll);
 */
export function throttle(func, limit = 100, options = {}) {
  const leading = options.leading !== undefined ? options.leading : true;
  const trailing = options.trailing !== undefined ? options.trailing : true;

  return debounce(func, limit, {
    leading,
    trailing,
    maxWait: limit,
  });
}

/**
 * Request Animation Frame debounce - syncs function execution with browser repaint.
 * Ensures smooth 60fps animations by executing once per frame.
 * Perfect for hover effects and visual updates.
 *
 * @param {Function} func - Function to execute
 * @returns {Function} RAF-debounced function with cancel() method
 *
 * @example
 * const handleHover = rafDebounce((event) => {
 *   updateHighlight(event.target);
 * });
 *
 * element.addEventListener('mousemove', handleHover);
 */
export function rafDebounce(func) {
  if (typeof func !== 'function') {
    throw new TypeError('Expected a function');
  }

  let rafId = null;
  let lastArgs = null;
  let lastThis = null;

  /**
   * Execute function on next animation frame
   */
  function scheduleRAF() {
    rafId = requestAnimationFrame(() => {
      const args = lastArgs;
      const thisArg = lastThis;
      rafId = null;
      lastArgs = lastThis = null;

      try {
        func.apply(thisArg, args);
      } catch (error) {
        console.error('[rafDebounce] Error executing function:', error);
      }
    });
  }

  /**
   * The RAF-debounced function
   */
  function rafDebounced(...args) {
    lastArgs = args;
    lastThis = this;

    // Cancel pending frame if exists
    if (rafId !== null) {
      cancelAnimationFrame(rafId);
    }

    scheduleRAF();
  }

  /**
   * Cancel pending execution
   */
  function cancel() {
    if (rafId !== null) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }
    lastArgs = lastThis = null;
  }

  /**
   * Check if execution is pending
   */
  function pending() {
    return rafId !== null;
  }

  // Attach utility methods
  rafDebounced.cancel = cancel;
  rafDebounced.pending = pending;

  return rafDebounced;
}

/**
 * Idle callback debounce - executes during browser idle time.
 * Useful for low-priority background tasks that shouldn't block user interaction.
 *
 * @param {Function} func - Function to execute during idle time
 * @param {Object} options - Configuration options
 * @param {number} options.timeout - Maximum time to wait before forcing execution (default: 2000ms)
 * @returns {Function} Idle-debounced function with cancel() method
 *
 * @example
 * const saveState = idleDebounce(() => {
 *   localStorage.setItem('state', JSON.stringify(appState));
 * });
 *
 * // Will execute during next idle period
 * saveState();
 */
export function idleDebounce(func, options = {}) {
  if (typeof func !== 'function') {
    throw new TypeError('Expected a function');
  }

  const timeout = options.timeout !== undefined ? options.timeout : 2000;

  let idleId = null;
  let lastArgs = null;
  let lastThis = null;

  /**
   * Execute function during idle callback
   */
  function scheduleIdle() {
    const callback = (deadline) => {
      const args = lastArgs;
      const thisArg = lastThis;
      idleId = null;
      lastArgs = lastThis = null;

      try {
        func.apply(thisArg, args);
      } catch (error) {
        console.error('[idleDebounce] Error executing function:', error);
      }
    };

    // Use requestIdleCallback if available, fallback to setTimeout
    if ('requestIdleCallback' in window) {
      idleId = requestIdleCallback(callback, { timeout });
    } else {
      idleId = setTimeout(() => callback({ didTimeout: true }), timeout);
    }
  }

  /**
   * The idle-debounced function
   */
  function idleDebounced(...args) {
    lastArgs = args;
    lastThis = this;

    // Cancel pending idle callback if exists
    if (idleId !== null) {
      if ('cancelIdleCallback' in window) {
        cancelIdleCallback(idleId);
      } else {
        clearTimeout(idleId);
      }
    }

    scheduleIdle();
  }

  /**
   * Cancel pending execution
   */
  function cancel() {
    if (idleId !== null) {
      if ('cancelIdleCallback' in window) {
        cancelIdleCallback(idleId);
      } else {
        clearTimeout(idleId);
      }
      idleId = null;
    }
    lastArgs = lastThis = null;
  }

  /**
   * Check if execution is pending
   */
  function pending() {
    return idleId !== null;
  }

  // Attach utility methods
  idleDebounced.cancel = cancel;
  idleDebounced.pending = pending;

  return idleDebounced;
}

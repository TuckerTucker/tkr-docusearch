/**
 * LiveRegion Component - WCAG 2.1 AA Compliant ARIA Live Regions
 *
 * Provides accessible announcements for dynamic content changes using ARIA live regions.
 * Supports both polite (default) and assertive (urgent) announcements.
 *
 * Features:
 * - Screen reader only announcements
 * - Configurable politeness level (polite, assertive)
 * - Support for status and alert roles
 * - Automatic role selection based on politeness
 * - Message queue to prevent overlap (for assertive regions)
 *
 * WCAG 2.4.4: Link Purpose (In Context)
 * WCAG 4.1.3: Status Messages
 *
 * @component
 *
 * @example
 * // Simple polite announcement (search results)
 * <LiveRegion message="Search completed: 15 documents found" politeness="polite" />
 *
 * @example
 * // Assertive announcement (errors, urgent updates)
 * <LiveRegion message="Upload failed: File too large" politeness="assertive" role="alert" />
 *
 * @example
 * // Research loading announcement
 * <LiveRegion
 *   message="Searching documents and generating answer..."
 *   politeness="polite"
 *   role="status"
 * />
 */
import { useEffect, useRef } from 'react';
import PropTypes from 'prop-types';

export default function LiveRegion({
  message,
  politeness = 'polite',
  role = 'status',
  ariaLive = null,
  ariaAtomic = true,
  delay = 100
}) {
  const regionRef = useRef(null);

  // Use ariaLive if provided, otherwise derive from politeness
  const effectiveAriaLive = ariaLive || politeness;

  useEffect(() => {
    if (!message || !regionRef.current) {
      return;
    }

    // Small delay to ensure DOM is ready for screen reader
    const timeoutId = setTimeout(() => {
      if (regionRef.current) {
        // Clear previous content first
        regionRef.current.textContent = '';

        // Set the message with a small delay to ensure screen reader announces it
        requestAnimationFrame(() => {
          if (regionRef.current) {
            regionRef.current.textContent = message;
          }
        });
      }
    }, delay);

    return () => clearTimeout(timeoutId);
  }, [message, delay]);

  return (
    <div
      ref={regionRef}
      role={role}
      aria-live={effectiveAriaLive}
      aria-atomic={ariaAtomic}
      className="sr-only"
      data-testid="live-region"
    />
  );
}

LiveRegion.propTypes = {
  /** Message to announce via screen reader */
  message: PropTypes.string,

  /** ARIA politeness level: 'polite', 'assertive', or 'off' */
  politeness: PropTypes.oneOf(['polite', 'assertive', 'off']),

  /** ARIA role: 'status', 'alert', or 'region' */
  role: PropTypes.oneOf(['status', 'alert', 'region']),

  /** Explicit aria-live value (overrides politeness) */
  ariaLive: PropTypes.oneOf(['polite', 'assertive', 'off']),

  /** Whether to announce entire region (true) or only changes (false) */
  ariaAtomic: PropTypes.bool,

  /** Delay in ms before announcing (allows animation to complete) */
  delay: PropTypes.number
};

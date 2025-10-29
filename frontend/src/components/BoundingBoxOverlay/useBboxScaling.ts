/**
 * BBox Scaling Hook
 *
 * Agent 5: BoundingBoxOverlay Component
 * Wave 1 - BBox Overlay React Implementation
 * Agent 12: Performance Optimizer - Wave 3
 *
 * Custom React hook that tracks image dimensions using ResizeObserver
 * and provides responsive scaling for bounding box overlays.
 *
 * Features:
 * - Automatic dimension tracking with ResizeObserver
 * - Throttled updates for optimal 60fps performance
 * - Proper cleanup on unmount
 * - TypeScript type safety
 * - RAF-based updates for smooth rendering
 */

import { useState, useEffect, useRef } from 'react';
import { useThrottleRAF } from '../../hooks/useThrottle';
import type { DisplayedDimensions } from './types';

/**
 * Hook to track displayed image dimensions using ResizeObserver.
 *
 * This hook observes the image element and updates dimensions whenever
 * the image is resized (window resize, container changes, etc.).
 *
 * Uses ResizeObserver for optimal performance and native browser support.
 * Falls back gracefully if ResizeObserver is not available.
 *
 * @param imageElement - The image element to observe
 * @returns Current displayed dimensions (width and height in pixels)
 *
 * @example
 * const imageRef = useRef<HTMLImageElement>(null);
 * const dimensions = useBboxScaling(imageRef.current);
 *
 * console.log(`Image displayed at ${dimensions.width}x${dimensions.height}`);
 */
export function useBboxScaling(
  imageElement: HTMLImageElement | null
): DisplayedDimensions {
  const [dimensions, setDimensions] = useState<DisplayedDimensions>({
    width: 0,
    height: 0,
  });

  // Store ResizeObserver in ref to persist across renders
  const observerRef = useRef<ResizeObserver | null>(null);

  // Throttle dimension updates using RAF for smooth 60fps performance
  const throttledSetDimensions = useThrottleRAF(setDimensions);

  useEffect(() => {
    // No image to observe
    if (!imageElement) {
      setDimensions({ width: 0, height: 0 });
      return;
    }

    // Set initial dimensions immediately using offsetWidth/offsetHeight
    // This ensures dimensions are available even before ResizeObserver fires
    const updateDimensions = () => {
      setDimensions({
        width: imageElement.offsetWidth,
        height: imageElement.offsetHeight,
      });
    };

    // Set initial dimensions
    updateDimensions();

    // Check if ResizeObserver is supported
    if (typeof ResizeObserver === 'undefined') {
      // Fallback: use window resize listener
      window.addEventListener('resize', updateDimensions);
      return () => {
        window.removeEventListener('resize', updateDimensions);
      };
    }

    // Create ResizeObserver to track image size changes
    // Uses RAF-throttled updates for optimal performance
    observerRef.current = new ResizeObserver((entries) => {
      for (const entry of entries) {
        // Use contentBoxSize if available (more precise)
        if (entry.contentBoxSize) {
          const contentBoxSize = Array.isArray(entry.contentBoxSize)
            ? entry.contentBoxSize[0]
            : entry.contentBoxSize;

          throttledSetDimensions({
            width: contentBoxSize.inlineSize,
            height: contentBoxSize.blockSize,
          });
        } else {
          // Fallback to contentRect
          throttledSetDimensions({
            width: entry.contentRect.width,
            height: entry.contentRect.height,
          });
        }
      }
    });

    // Start observing the image element
    observerRef.current.observe(imageElement);

    // Cleanup: disconnect observer on unmount or image change
    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
        observerRef.current = null;
      }
    };
  }, [imageElement, throttledSetDimensions]);

  return dimensions;
}

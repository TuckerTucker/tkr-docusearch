/**
 * SkeletonLoader Component
 *
 * Agent 13: Visual Polish & Animation Designer
 * Wave 3 - BBox Overlay React Implementation
 *
 * Loading skeleton for BoundingBoxOverlay component.
 * Shows animated placeholder while bbox structure is loading.
 *
 * Features:
 * - Shimmer animation
 * - Smooth fade-in when content loads
 * - Respects prefers-reduced-motion
 * - Matches bbox visual style
 */

import React from 'react';
import styles from './SkeletonLoader.module.css';

export interface SkeletonLoaderProps {
  /**
   * Width of the image container
   */
  width: number;
  /**
   * Height of the image container
   */
  height: number;
  /**
   * Number of skeleton boxes to show
   * @default 5
   */
  count?: number;
  /**
   * Additional CSS class name
   */
  className?: string;
}

/**
 * SkeletonLoader component for BoundingBoxOverlay.
 *
 * Displays animated skeleton boxes while bbox structure is loading.
 * Automatically generates random bbox positions for visual variety.
 *
 * @example
 * ```tsx
 * <SkeletonLoader width={600} height={800} count={8} />
 * ```
 */
export const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({
  width,
  height,
  count = 5,
  className = '',
}) => {
  // Generate random skeleton boxes
  const skeletonBoxes = React.useMemo(() => {
    const boxes = [];
    const padding = 72; // Standard page padding
    const usableWidth = width - padding * 2;
    const usableHeight = height - padding * 2;

    for (let i = 0; i < count; i++) {
      // Distribute boxes vertically with some randomness
      const baseY = padding + (usableHeight / count) * i;
      const y = baseY + (Math.random() - 0.5) * 30;

      // Random width (40-80% of page width)
      const boxWidth = usableWidth * (0.4 + Math.random() * 0.4);
      const x = padding + Math.random() * (usableWidth - boxWidth);

      // Random height (text, heading, table variations)
      const heightVariant = Math.random();
      let boxHeight;
      if (heightVariant < 0.3) {
        // Short text
        boxHeight = 20 + Math.random() * 30;
      } else if (heightVariant < 0.6) {
        // Medium (paragraph)
        boxHeight = 60 + Math.random() * 40;
      } else {
        // Tall (table, figure)
        boxHeight = 120 + Math.random() * 80;
      }

      boxes.push({
        id: `skeleton-${i}`,
        x,
        y,
        width: boxWidth,
        height: boxHeight,
      });
    }

    return boxes;
  }, [width, height, count]);

  return (
    <svg
      className={`${styles.skeletonOverlay} ${className}`}
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="Loading bounding boxes"
      aria-busy="true"
    >
      {/* Background shimmer gradient */}
      <defs>
        <linearGradient id="shimmer-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="var(--muted)" stopOpacity="0.3">
            <animate
              attributeName="offset"
              values="-1; -1; 1"
              dur="2s"
              repeatCount="indefinite"
            />
          </stop>
          <stop offset="50%" stopColor="var(--muted)" stopOpacity="0.6">
            <animate
              attributeName="offset"
              values="-0.5; -0.5; 1.5"
              dur="2s"
              repeatCount="indefinite"
            />
          </stop>
          <stop offset="100%" stopColor="var(--muted)" stopOpacity="0.3">
            <animate
              attributeName="offset"
              values="0; 0; 2"
              dur="2s"
              repeatCount="indefinite"
            />
          </stop>
        </linearGradient>
      </defs>

      {/* Skeleton boxes */}
      {skeletonBoxes.map((box) => (
        <rect
          key={box.id}
          className={styles.skeletonBox}
          x={box.x}
          y={box.y}
          width={box.width}
          height={box.height}
          fill="url(#shimmer-gradient)"
          stroke="var(--border)"
          strokeWidth="2"
          strokeOpacity="0.4"
          rx="4"
        />
      ))}
    </svg>
  );
};

export default SkeletonLoader;

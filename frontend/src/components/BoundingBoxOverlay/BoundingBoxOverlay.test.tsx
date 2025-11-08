/**
 * BoundingBoxOverlay Component Tests
 *
 * Agent 5: BoundingBoxOverlay Component
 * Wave 1 - BBox Overlay React Implementation
 *
 * Comprehensive test suite for BoundingBoxOverlay component.
 * Tests rendering, scaling, interactions, and edge cases.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BoundingBoxOverlay } from './BoundingBoxOverlay';
import type { BBoxWithMetadata } from './types';

describe('BoundingBoxOverlay', () => {
  // Mock image element
  let mockImage: HTMLImageElement;

  // Sample bboxes for testing
  const sampleBboxes: BBoxWithMetadata[] = [
    {
      x1: 72,
      y1: 100,
      x2: 540,
      y2: 150,
      chunk_id: 'chunk1',
      element_type: 'heading',
      confidence: 0.95,
    },
    {
      x1: 72,
      y1: 200,
      x2: 540,
      y2: 400,
      chunk_id: 'chunk2',
      element_type: 'table',
      confidence: 0.88,
    },
    {
      x1: 100,
      y1: 450,
      x2: 300,
      y2: 600,
      chunk_id: 'chunk3',
      element_type: 'picture',
      confidence: 0.92,
    },
  ];

  beforeEach(() => {
    // Create a mock image element with dimensions
    mockImage = document.createElement('img');
    Object.defineProperty(mockImage, 'offsetWidth', {
      writable: true,
      value: 1020,
    });
    Object.defineProperty(mockImage, 'offsetHeight', {
      writable: true,
      value: 1320,
    });
  });

  describe('Rendering', () => {
    it('renders SVG overlay with correct dimensions', () => {
      const { container } = render(
        <BoundingBoxOverlay
          imageElement={mockImage}
          bboxes={sampleBboxes}
          originalWidth={612}
          originalHeight={792}
        />
      );

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
      expect(svg).toHaveAttribute('width', '1020');
      expect(svg).toHaveAttribute('height', '1320');
    });

    it('renders correct number of bounding boxes', () => {
      const { container } = render(
        <BoundingBoxOverlay
          imageElement={mockImage}
          bboxes={sampleBboxes}
          originalWidth={612}
          originalHeight={792}
        />
      );

      const rects = container.querySelectorAll('rect');
      expect(rects).toHaveLength(3);
    });

    it('does not render when imageElement is null', () => {
      const { container } = render(
        <BoundingBoxOverlay
          imageElement={null}
          bboxes={sampleBboxes}
          originalWidth={612}
          originalHeight={792}
        />
      );

      const svg = container.querySelector('svg');
      expect(svg).not.toBeInTheDocument();
    });

    it('does not render when image has zero dimensions', () => {
      const zeroImage = document.createElement('img');
      Object.defineProperty(zeroImage, 'offsetWidth', { value: 0 });
      Object.defineProperty(zeroImage, 'offsetHeight', { value: 0 });

      const { container } = render(
        <BoundingBoxOverlay
          imageElement={zeroImage}
          bboxes={sampleBboxes}
          originalWidth={612}
          originalHeight={792}
        />
      );

      const svg = container.querySelector('svg');
      expect(svg).not.toBeInTheDocument();
    });

    it('handles empty bboxes array', () => {
      const { container } = render(
        <BoundingBoxOverlay
          imageElement={mockImage}
          bboxes={[]}
          originalWidth={612}
          originalHeight={792}
        />
      );

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();

      const rects = container.querySelectorAll('rect');
      expect(rects).toHaveLength(0);
    });
  });

  describe('Coordinate Scaling', () => {
    it('scales bboxes correctly for display', () => {
      const { container } = render(
        <BoundingBoxOverlay
          imageElement={mockImage}
          bboxes={[sampleBboxes[0]]}
          originalWidth={612}
          originalHeight={792}
        />
      );

      const rect = container.querySelector('rect');
      expect(rect).toBeInTheDocument();

      // Original: x1=72, y1=100, x2=540, y2=150
      // Scale factors: 1020/612 ≈ 1.6667, 1320/792 ≈ 1.6667
      // Expected: x1=120, y1≈167, width=780, height≈83

      const x = parseFloat(rect!.getAttribute('x') || '0');
      const y = parseFloat(rect!.getAttribute('y') || '0');
      const width = parseFloat(rect!.getAttribute('width') || '0');
      const height = parseFloat(rect!.getAttribute('height') || '0');

      expect(x).toBeCloseTo(120, 0);
      expect(y).toBeCloseTo(166.67, 0);
      expect(width).toBeCloseTo(780, 0);
      expect(height).toBeCloseTo(83.33, 0);
    });

    it('maintains bbox proportions across different display sizes', () => {
      const smallImage = document.createElement('img');
      Object.defineProperty(smallImage, 'offsetWidth', { value: 306 });
      Object.defineProperty(smallImage, 'offsetHeight', { value: 396 });

      const { container } = render(
        <BoundingBoxOverlay
          imageElement={smallImage}
          bboxes={[sampleBboxes[0]]}
          originalWidth={612}
          originalHeight={792}
        />
      );

      const rect = container.querySelector('rect');
      const width = parseFloat(rect!.getAttribute('width') || '0');
      const height = parseFloat(rect!.getAttribute('height') || '0');

      // At half scale, dimensions should also be halved
      expect(width).toBeCloseTo(234, 0); // (540-72) * 0.5
      expect(height).toBeCloseTo(25, 0); // (150-100) * 0.5
    });
  });

  describe('Interactions', () => {
    it('calls onBboxClick when bbox is clicked', () => {
      const handleClick = vi.fn();

      const { container } = render(
        <BoundingBoxOverlay
          imageElement={mockImage}
          bboxes={[sampleBboxes[0]]}
          originalWidth={612}
          originalHeight={792}
          onBboxClick={handleClick}
        />
      );

      const rect = container.querySelector('rect');
      fireEvent.click(rect!);

      expect(handleClick).toHaveBeenCalledTimes(1);
      expect(handleClick).toHaveBeenCalledWith(
        'chunk1',
        expect.objectContaining({
          x1: expect.any(Number),
          y1: expect.any(Number),
          x2: expect.any(Number),
          y2: expect.any(Number),
        })
      );
    });

    it('calls onBboxHover when mouse enters bbox', async () => {
      const handleHover = vi.fn();
      const user = userEvent.setup();

      const { container } = render(
        <BoundingBoxOverlay
          imageElement={mockImage}
          bboxes={[sampleBboxes[0]]}
          originalWidth={612}
          originalHeight={792}
          onBboxHover={handleHover}
        />
      );

      const rect = container.querySelector('rect') as HTMLElement;
      await user.hover(rect);

      // Wait for debounce to complete (50ms)
      await waitFor(() => {
        expect(handleHover).toHaveBeenCalledWith('chunk1');
      }, { timeout: 200 });
    });

    it('calls onBboxHover with null when mouse leaves bbox', async () => {
      const handleHover = vi.fn();
      const user = userEvent.setup();

      const { container } = render(
        <BoundingBoxOverlay
          imageElement={mockImage}
          bboxes={[sampleBboxes[0]]}
          originalWidth={612}
          originalHeight={792}
          onBboxHover={handleHover}
        />
      );

      const rect = container.querySelector('rect') as HTMLElement;
      await user.hover(rect);
      await user.unhover(rect);

      // Wait for debounce to complete (50ms)
      await waitFor(() => {
        expect(handleHover).toHaveBeenLastCalledWith(null);
      }, { timeout: 200 });
    });

    it('handles keyboard interaction (Enter key)', () => {
      const handleClick = vi.fn();

      const { container } = render(
        <BoundingBoxOverlay
          imageElement={mockImage}
          bboxes={[sampleBboxes[0]]}
          originalWidth={612}
          originalHeight={792}
          onBboxClick={handleClick}
        />
      );

      const rect = container.querySelector('rect');
      fireEvent.keyDown(rect!, { key: 'Enter' });

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('handles keyboard interaction (Space key)', () => {
      const handleClick = vi.fn();

      const { container } = render(
        <BoundingBoxOverlay
          imageElement={mockImage}
          bboxes={[sampleBboxes[0]]}
          originalWidth={612}
          originalHeight={792}
          onBboxClick={handleClick}
        />
      );

      const rect = container.querySelector('rect');
      fireEvent.keyDown(rect!, { key: ' ' });

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('does not trigger click on other keys', () => {
      const handleClick = vi.fn();

      const { container } = render(
        <BoundingBoxOverlay
          imageElement={mockImage}
          bboxes={[sampleBboxes[0]]}
          originalWidth={612}
          originalHeight={792}
          onBboxClick={handleClick}
        />
      );

      const rect = container.querySelector('rect');
      fireEvent.keyDown(rect!, { key: 'a' });

      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  describe('Visual States', () => {
    it('applies active class to active chunk', () => {
      const { container } = render(
        <BoundingBoxOverlay
          imageElement={mockImage}
          bboxes={sampleBboxes}
          originalWidth={612}
          originalHeight={792}
          activeChunkId="chunk2"
        />
      );

      const rects = container.querySelectorAll('rect');
      // CSS modules add hash to class names, so we check class attribute contains the style
      const class1 = rects[1].getAttribute('class') || '';
      const class0 = rects[0].getAttribute('class') || '';
      const class2 = rects[2].getAttribute('class') || '';
      expect(class1).toContain('active');
      expect(class0).not.toContain('active');
      expect(class2).not.toContain('active');
    });

    it('applies hovered class to hovered chunk', () => {
      const { container } = render(
        <BoundingBoxOverlay
          imageElement={mockImage}
          bboxes={sampleBboxes}
          originalWidth={612}
          originalHeight={792}
          hoveredChunkId="chunk1"
        />
      );

      const rects = container.querySelectorAll('rect');
      // CSS modules add hash to class names, so we check class attribute contains the style
      const class0 = rects[0].getAttribute('class') || '';
      const class1 = rects[1].getAttribute('class') || '';
      const class2 = rects[2].getAttribute('class') || '';
      expect(class0).toContain('hovered');
      expect(class1).not.toContain('hovered');
      expect(class2).not.toContain('hovered');
    });

    it('applies element type classes correctly', () => {
      const { container } = render(
        <BoundingBoxOverlay
          imageElement={mockImage}
          bboxes={sampleBboxes}
          originalWidth={612}
          originalHeight={792}
        />
      );

      const rects = container.querySelectorAll('rect');
      // CSS modules add hash to class names, so we check class attribute contains the style
      const class0 = rects[0].getAttribute('class') || '';
      const class1 = rects[1].getAttribute('class') || '';
      const class2 = rects[2].getAttribute('class') || '';
      expect(class0).toContain('type-heading');
      expect(class1).toContain('type-table');
      expect(class2).toContain('type-picture');
    });
  });

  describe('Data Attributes', () => {
    it('sets correct data attributes on bbox elements', () => {
      const { container } = render(
        <BoundingBoxOverlay
          imageElement={mockImage}
          bboxes={[sampleBboxes[0]]}
          originalWidth={612}
          originalHeight={792}
        />
      );

      const rect = container.querySelector('rect');
      expect(rect).toHaveAttribute('data-chunk-id', 'chunk1');
      expect(rect).toHaveAttribute('data-element-type', 'heading');
    });

    it('sets unknown element type when not provided', () => {
      const bboxWithoutType: BBoxWithMetadata = {
        x1: 0,
        y1: 0,
        x2: 100,
        y2: 100,
        chunk_id: 'test',
      };

      const { container } = render(
        <BoundingBoxOverlay
          imageElement={mockImage}
          bboxes={[bboxWithoutType]}
          originalWidth={612}
          originalHeight={792}
        />
      );

      const rect = container.querySelector('rect');
      expect(rect).toHaveAttribute('data-element-type', 'unknown');
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA attributes', () => {
      const { container } = render(
        <BoundingBoxOverlay
          imageElement={mockImage}
          bboxes={[sampleBboxes[0]]}
          originalWidth={612}
          originalHeight={792}
        />
      );

      const svg = container.querySelector('svg');
      expect(svg).toHaveAttribute('role', 'region');
      expect(svg).toHaveAttribute('aria-label', 'Document structure overlay with navigable elements');

      const rect = container.querySelector('rect');
      expect(rect).toHaveAttribute('role', 'button');
      // aria-label format: "{ElementType} {index+1}" e.g. "Heading 1"
      const label = rect!.getAttribute('aria-label');
      expect(label).toBe('Heading 1');
      expect(rect).toHaveAttribute('tabindex', '0');
    });
  });

  describe('Edge Cases', () => {
    it('handles zero original dimensions gracefully', () => {
      const { container } = render(
        <BoundingBoxOverlay
          imageElement={mockImage}
          bboxes={sampleBboxes}
          originalWidth={0}
          originalHeight={0}
        />
      );

      const rects = container.querySelectorAll('rect');
      expect(rects).toHaveLength(0);
    });

    it('applies custom className', () => {
      const { container } = render(
        <BoundingBoxOverlay
          imageElement={mockImage}
          bboxes={sampleBboxes}
          originalWidth={612}
          originalHeight={792}
          className="custom-overlay"
        />
      );

      const svg = container.querySelector('svg');
      expect(svg).toHaveClass('custom-overlay');
    });

    it('handles very small bboxes with minimum size enforcement', () => {
      const tinyBbox: BBoxWithMetadata = {
        x1: 100,
        y1: 100,
        x2: 101,
        y2: 101,
        chunk_id: 'tiny',
      };

      const { container } = render(
        <BoundingBoxOverlay
          imageElement={mockImage}
          bboxes={[tinyBbox]}
          originalWidth={612}
          originalHeight={792}
        />
      );

      const rect = container.querySelector('rect');
      const width = parseFloat(rect!.getAttribute('width') || '0');
      const height = parseFloat(rect!.getAttribute('height') || '0');

      // Should be at least minimum size (10px)
      expect(width).toBeGreaterThanOrEqual(10);
      expect(height).toBeGreaterThanOrEqual(10);
    });
  });
});

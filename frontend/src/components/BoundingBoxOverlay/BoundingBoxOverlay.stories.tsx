/**
 * BoundingBoxOverlay Storybook Stories
 *
 * Agent 5: BoundingBoxOverlay Component (Enhanced by Agent 13)
 * Wave 1-3 - BBox Overlay React Implementation
 *
 * Interactive demonstrations of BoundingBoxOverlay component states.
 * Showcases rendering, scaling, interactions, element types, and Wave 3 animations.
 *
 * Wave 3 Additions:
 * - Animation showcase stories
 * - Loading skeleton demonstrations
 * - Theme variation examples
 * - Dark mode comparisons
 * - Reduced motion examples
 *
 * NOTE: This file is ready for Storybook integration. To use:
 * 1. Install Storybook: npx storybook@latest init
 * 2. Run Storybook: npm run storybook
 *
 * @storybook/react v7+ (CSF 3.0 format)
 */

import type { Meta, StoryObj } from '@storybook/react';
import { useState, useRef, useEffect } from 'react';
import { BoundingBoxOverlay } from './BoundingBoxOverlay';
import { SkeletonLoader } from './SkeletonLoader';
import type { BBoxWithMetadata } from './types';

// Story metadata
const meta: Meta<typeof BoundingBoxOverlay> = {
  title: 'Components/BoundingBoxOverlay',
  component: BoundingBoxOverlay,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: `
BoundingBoxOverlay renders SVG overlays on document page images showing
bounding boxes for document elements (headings, tables, pictures, etc.).

Features:
- Responsive scaling using ResizeObserver
- Interactive hover and click states
- Active chunk highlighting
- Element type styling
- Keyboard accessible
        `,
      },
    },
  },
  argTypes: {
    imageElement: {
      description: 'Reference to the image element to overlay',
      control: false,
    },
    bboxes: {
      description: 'Array of bounding boxes to render',
      control: 'object',
    },
    originalWidth: {
      description: 'Original image width in pixels',
      control: { type: 'number', min: 100, max: 2000, step: 10 },
    },
    originalHeight: {
      description: 'Original image height in pixels',
      control: { type: 'number', min: 100, max: 2000, step: 10 },
    },
    activeChunkId: {
      description: 'ID of the currently active chunk',
      control: 'text',
    },
    hoveredChunkId: {
      description: 'ID of the currently hovered chunk',
      control: 'text',
    },
    className: {
      description: 'Additional CSS class name',
      control: 'text',
    },
  },
};

export default meta;
type Story = StoryObj<typeof BoundingBoxOverlay>;

// Sample document page image URL (placeholder)
const SAMPLE_IMAGE_URL =
  'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjEyIiBoZWlnaHQ9Ijc5MiIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNjEyIiBoZWlnaHQ9Ijc5MiIgZmlsbD0iI2Y1ZjVmNSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIyNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZG9taW5hbnQtYmFzZWxpbmU9Im1pZGRsZSI+RG9jdW1lbnQgUGFnZTwvdGV4dD48L3N2Zz4=';

// Sample bboxes for different element types
const sampleBboxes: BBoxWithMetadata[] = [
  {
    x1: 72,
    y1: 60,
    x2: 540,
    y2: 100,
    chunk_id: 'chunk_title',
    element_type: 'heading',
    confidence: 0.98,
  },
  {
    x1: 72,
    y1: 120,
    x2: 540,
    y2: 160,
    chunk_id: 'chunk_section1',
    element_type: 'heading',
    confidence: 0.95,
  },
  {
    x1: 72,
    y1: 180,
    x2: 540,
    y2: 250,
    chunk_id: 'chunk_para1',
    element_type: 'text',
    confidence: 0.92,
  },
  {
    x1: 72,
    y1: 270,
    x2: 540,
    y2: 450,
    chunk_id: 'chunk_table1',
    element_type: 'table',
    confidence: 0.89,
  },
  {
    x1: 150,
    y1: 470,
    x2: 462,
    y2: 650,
    chunk_id: 'chunk_figure1',
    element_type: 'picture',
    confidence: 0.94,
  },
  {
    x1: 72,
    y1: 670,
    x2: 540,
    y2: 740,
    chunk_id: 'chunk_para2',
    element_type: 'text',
    confidence: 0.91,
  },
];

// Story wrapper component that creates an image element
const StoryWrapper = ({
  bboxes,
  originalWidth,
  originalHeight,
  activeChunkId,
  hoveredChunkId,
  interactive = false,
}: {
  bboxes: BBoxWithMetadata[];
  originalWidth: number;
  originalHeight: number;
  activeChunkId?: string | null;
  hoveredChunkId?: string | null;
  interactive?: boolean;
}) => {
  const imageRef = useRef<HTMLImageElement>(null);
  const [imageElement, setImageElement] = useState<HTMLImageElement | null>(null);
  const [activeId, setActiveId] = useState<string | null>(activeChunkId || null);
  const [hoveredId, setHoveredId] = useState<string | null>(hoveredChunkId || null);

  useEffect(() => {
    if (imageRef.current) {
      setImageElement(imageRef.current);
    }
  }, []);

  const handleBboxClick = (chunkId: string) => {
    if (interactive) {
      setActiveId(activeId === chunkId ? null : chunkId);
      console.log('Clicked bbox:', chunkId);
    }
  };

  const handleBboxHover = (chunkId: string | null) => {
    if (interactive) {
      setHoveredId(chunkId);
      console.log('Hovered bbox:', chunkId);
    }
  };

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <img
        ref={imageRef}
        src={SAMPLE_IMAGE_URL}
        alt="Sample document page"
        style={{ maxWidth: '600px', display: 'block' }}
      />
      <BoundingBoxOverlay
        imageElement={imageElement}
        bboxes={bboxes}
        originalWidth={originalWidth}
        originalHeight={originalHeight}
        activeChunkId={interactive ? activeId : activeChunkId}
        hoveredChunkId={interactive ? hoveredId : hoveredChunkId}
        onBboxClick={interactive ? handleBboxClick : undefined}
        onBboxHover={interactive ? handleBboxHover : undefined}
      />
    </div>
  );
};

/**
 * Basic overlay with multiple bboxes of different element types.
 * Demonstrates default rendering with headings, tables, pictures, and text.
 */
export const Basic: Story = {
  render: () => (
    <StoryWrapper
      bboxes={sampleBboxes}
      originalWidth={612}
      originalHeight={792}
    />
  ),
};

/**
 * Interactive overlay with click and hover handlers.
 * Click a bbox to activate it, hover to see hover state.
 */
export const Interactive: Story = {
  render: () => (
    <StoryWrapper
      bboxes={sampleBboxes}
      originalWidth={612}
      originalHeight={792}
      interactive={true}
    />
  ),
  parameters: {
    docs: {
      description: {
        story: 'Click any bounding box to activate it. Hover to see the hover state. Check the Actions panel to see event callbacks.',
      },
    },
  },
};

/**
 * Active state: Shows a specific chunk highlighted.
 */
export const ActiveState: Story = {
  render: () => (
    <StoryWrapper
      bboxes={sampleBboxes}
      originalWidth={612}
      originalHeight={792}
      activeChunkId="chunk_table1"
    />
  ),
};

/**
 * Hovered state: Shows a specific chunk in hover state.
 */
export const HoveredState: Story = {
  render: () => (
    <StoryWrapper
      bboxes={sampleBboxes}
      originalWidth={612}
      originalHeight={792}
      hoveredChunkId="chunk_figure1"
    />
  ),
};

/**
 * Active + Hovered: Shows combined state styling.
 */
export const ActiveAndHovered: Story = {
  render: () => (
    <StoryWrapper
      bboxes={sampleBboxes}
      originalWidth={612}
      originalHeight={792}
      activeChunkId="chunk_table1"
      hoveredChunkId="chunk_table1"
    />
  ),
};

/**
 * Only headings: Demonstrates heading element type styling.
 */
export const HeadingsOnly: Story = {
  render: () => {
    const headingBboxes = sampleBboxes.filter(
      (bbox) => bbox.element_type === 'heading'
    );
    return (
      <StoryWrapper
        bboxes={headingBboxes}
        originalWidth={612}
        originalHeight={792}
      />
    );
  },
};

/**
 * Only tables: Demonstrates table element type styling.
 */
export const TablesOnly: Story = {
  render: () => {
    const tableBboxes = sampleBboxes.filter(
      (bbox) => bbox.element_type === 'table'
    );
    return (
      <StoryWrapper
        bboxes={tableBboxes}
        originalWidth={612}
        originalHeight={792}
      />
    );
  },
};

/**
 * Only pictures: Demonstrates picture element type styling.
 */
export const PicturesOnly: Story = {
  render: () => {
    const pictureBboxes = sampleBboxes.filter(
      (bbox) => bbox.element_type === 'picture'
    );
    return (
      <StoryWrapper
        bboxes={pictureBboxes}
        originalWidth={612}
        originalHeight={792}
      />
    );
  },
};

/**
 * Empty state: No bboxes to display.
 */
export const EmptyState: Story = {
  render: () => (
    <StoryWrapper
      bboxes={[]}
      originalWidth={612}
      originalHeight={792}
    />
  ),
};

/**
 * Dense layout: Many overlapping bboxes.
 */
export const DenseLayout: Story = {
  render: () => {
    const denseBboxes: BBoxWithMetadata[] = Array.from({ length: 20 }, (_, i) => ({
      x1: 72 + (i % 4) * 120,
      y1: 60 + Math.floor(i / 4) * 150,
      x2: 152 + (i % 4) * 120,
      y2: 140 + Math.floor(i / 4) * 150,
      chunk_id: `chunk_${i}`,
      element_type: ['heading', 'table', 'picture', 'text'][i % 4],
    }));

    return (
      <StoryWrapper
        bboxes={denseBboxes}
        originalWidth={612}
        originalHeight={792}
        interactive={true}
      />
    );
  },
};

/**
 * Responsive scaling: Demonstrates bbox scaling at different sizes.
 */
export const ResponsiveScaling: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
      <div>
        <h3>Small (300px)</h3>
        <div style={{ width: '300px' }}>
          <StoryWrapper
            bboxes={sampleBboxes}
            originalWidth={612}
            originalHeight={792}
          />
        </div>
      </div>
      <div>
        <h3>Medium (450px)</h3>
        <div style={{ width: '450px' }}>
          <StoryWrapper
            bboxes={sampleBboxes}
            originalWidth={612}
            originalHeight={792}
          />
        </div>
      </div>
      <div>
        <h3>Large (600px)</h3>
        <div style={{ width: '600px' }}>
          <StoryWrapper
            bboxes={sampleBboxes}
            originalWidth={612}
            originalHeight={792}
          />
        </div>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Bounding boxes scale proportionally with image size while maintaining correct positioning.',
      },
    },
  },
};

/* ============================================
   Wave 3: Animation and Loading Stories
   ============================================ */

/**
 * Loading skeleton: Shows animated skeleton while bboxes load.
 * Wave 3: SkeletonLoader component with shimmer animation.
 */
export const LoadingSkeleton: Story = {
  render: () => (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <img
        src={SAMPLE_IMAGE_URL}
        alt="Sample document page"
        style={{ maxWidth: '600px', display: 'block' }}
      />
      <SkeletonLoader width={600} height={792} count={8} />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Wave 3: Animated skeleton loader shows shimmer effect while bbox structure is loading. Respects prefers-reduced-motion.',
      },
    },
  },
};

/**
 * Loading to loaded transition: Demonstrates transition from skeleton to actual bboxes.
 * Wave 3: Smooth fade transition between states.
 */
export const LoadingTransition: Story = {
  render: () => {
    const imageRef = useRef<HTMLImageElement>(null);
    const [imageElement, setImageElement] = useState<HTMLImageElement | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
      if (imageRef.current) {
        setImageElement(imageRef.current);
      }
    }, []);

    useEffect(() => {
      // Simulate loading delay
      const timer = setTimeout(() => setIsLoading(false), 3000);
      return () => clearTimeout(timer);
    }, []);

    return (
      <div style={{ position: 'relative', display: 'inline-block' }}>
        <img
          ref={imageRef}
          src={SAMPLE_IMAGE_URL}
          alt="Sample document page"
          style={{ maxWidth: '600px', display: 'block' }}
        />
        {isLoading ? (
          <SkeletonLoader width={600} height={792} count={8} />
        ) : (
          <BoundingBoxOverlay
            imageElement={imageElement}
            bboxes={sampleBboxes}
            originalWidth={612}
            originalHeight={792}
          />
        )}
        <button
          onClick={() => setIsLoading(!isLoading)}
          style={{
            position: 'absolute',
            top: '10px',
            right: '10px',
            padding: '8px 16px',
            borderRadius: '4px',
            border: '1px solid #ccc',
            background: 'white',
            cursor: 'pointer',
          }}
        >
          {isLoading ? 'Show Bboxes' : 'Show Loading'}
        </button>
      </div>
    );
  },
  parameters: {
    docs: {
      description: {
        story: 'Wave 3: Click the button to toggle between loading skeleton and actual bboxes. Notice the smooth transition.',
      },
    },
  },
};

/**
 * Animation showcase: Demonstrates all animation states in sequence.
 * Wave 3: Hover, active, and combined animations.
 */
export const AnimationShowcase: Story = {
  render: () => {
    const imageRef = useRef<HTMLImageElement>(null);
    const [imageElement, setImageElement] = useState<HTMLImageElement | null>(null);
    const [state, setState] = useState<'default' | 'hover' | 'active' | 'both'>('default');

    useEffect(() => {
      if (imageRef.current) {
        setImageElement(imageRef.current);
      }
    }, []);

    // Cycle through states
    useEffect(() => {
      const states: ('default' | 'hover' | 'active' | 'both')[] = ['default', 'hover', 'active', 'both'];
      let index = 0;
      const interval = setInterval(() => {
        index = (index + 1) % states.length;
        setState(states[index]);
      }, 2000);
      return () => clearInterval(interval);
    }, []);

    const activeChunkId = state === 'active' || state === 'both' ? 'chunk_table1' : null;
    const hoveredChunkId = state === 'hover' || state === 'both' ? 'chunk_table1' : null;

    return (
      <div>
        <div style={{ marginBottom: '16px', textAlign: 'center' }}>
          <strong>Current State: {state}</strong>
        </div>
        <div style={{ position: 'relative', display: 'inline-block' }}>
          <img
            ref={imageRef}
            src={SAMPLE_IMAGE_URL}
            alt="Sample document page"
            style={{ maxWidth: '600px', display: 'block' }}
          />
          <BoundingBoxOverlay
            imageElement={imageElement}
            bboxes={sampleBboxes}
            originalWidth={612}
            originalHeight={792}
            activeChunkId={activeChunkId}
            hoveredChunkId={hoveredChunkId}
          />
        </div>
      </div>
    );
  },
  parameters: {
    docs: {
      description: {
        story: 'Wave 3: Automatically cycles through animation states (default → hover → active → both). Watch the table bbox for smooth transitions, scale effects, and glow animations.',
      },
    },
  },
};

/**
 * Dark mode comparison: Shows bbox styling in light vs dark mode.
 * Wave 3: Enhanced dark mode colors and glows.
 */
export const DarkModeComparison: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
      <div>
        <h3>Light Mode</h3>
        <div style={{ background: 'oklch(0.9582 0.0152 90.2357)', padding: '1rem' }}>
          <StoryWrapper
            bboxes={sampleBboxes}
            originalWidth={612}
            originalHeight={792}
            activeChunkId="chunk_table1"
            hoveredChunkId="chunk_figure1"
          />
        </div>
      </div>
      <div>
        <h3>Dark Mode</h3>
        <div className="dark" style={{ background: 'oklch(0.2747 0.0139 57.6523)', padding: '1rem' }}>
          <StoryWrapper
            bboxes={sampleBboxes}
            originalWidth={612}
            originalHeight={792}
            activeChunkId="chunk_table1"
            hoveredChunkId="chunk_figure1"
          />
        </div>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Wave 3: Side-by-side comparison of light and dark modes. Note the adjusted opacity, brighter colors, and enhanced glows in dark mode.',
      },
    },
  },
};

/**
 * Theme variations: Shows bbox styling across all supported themes.
 * Wave 3: Theme-specific colors and effects.
 */
export const ThemeVariations: Story = {
  render: () => {
    const themes = [
      { name: 'Kraft Paper', theme: 'kraft-paper' },
      { name: 'Graphite', theme: 'graphite' },
      { name: 'Blue on Black', theme: 'blue-on-black' },
      { name: 'Gold on Blue', theme: 'gold-on-blue' },
      { name: 'Notebook', theme: 'notebook' },
    ];

    return (
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>
        {themes.map(({ name, theme }) => (
          <div key={theme} data-theme={theme}>
            <h4 style={{ textAlign: 'center', marginBottom: '0.5rem' }}>{name}</h4>
            <div style={{ transform: 'scale(0.5)', transformOrigin: 'top center' }}>
              <StoryWrapper
                bboxes={sampleBboxes}
                originalWidth={612}
                originalHeight={792}
                activeChunkId="chunk_table1"
              />
            </div>
          </div>
        ))}
      </div>
    );
  },
  parameters: {
    docs: {
      description: {
        story: 'Wave 3: All supported themes with their unique color palettes and visual effects. Each theme has custom bbox colors, glows, and shadows.',
      },
    },
  },
};

/**
 * Reduced motion: Shows how animations respect accessibility preferences.
 * Wave 3: Instant transitions with prefers-reduced-motion.
 */
export const ReducedMotion: Story = {
  render: () => (
    <div>
      <div style={{ marginBottom: '16px', padding: '12px', background: '#f0f0f0', borderRadius: '4px' }}>
        <strong>Accessibility Note:</strong> This story demonstrates reduced motion support.
        In your browser's accessibility settings, enable "Reduce motion" to see instant
        transitions instead of animations.
      </div>
      <StoryWrapper
        bboxes={sampleBboxes}
        originalWidth={612}
        originalHeight={792}
        interactive={true}
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Wave 3: When prefers-reduced-motion is enabled, all animations become instant while maintaining final visual states. Click bboxes to test.',
      },
    },
  },
};

# BoundingBox Overlay API Reference

**Agent 14: Testing & Documentation**
**Wave 3 - BBox Overlay React Implementation**

Complete API documentation for all bbox overlay components, hooks, and utilities.

## Table of Contents

- [Components](#components)
  - [BoundingBoxOverlay](#boundingboxoverlay)
  - [BBoxController](#bboxcontroller)
- [Hooks](#hooks)
  - [useChunkNavigation](#usechunknavigation)
  - [useChunkHighlight](#usechunkhighlight)
  - [useBboxScaling](#usebboxscaling)
  - [useDocumentStructure](#usedocumentstructure)
- [Type Definitions](#type-definitions)
- [Utilities](#utilities)

---

## Components

### BoundingBoxOverlay

Visual overlay component that renders bounding boxes on document images.

**Import**:
```tsx
import { BoundingBoxOverlay } from '@/components/BoundingBoxOverlay';
```

**Props**:

```typescript
interface BoundingBoxOverlayProps {
  /** Reference to the image element to overlay */
  imageElement: HTMLImageElement | null;

  /** Array of bounding boxes to render */
  bboxes: BBoxWithMetadata[];

  /** Original image width in pixels */
  originalWidth: number;

  /** Original image height in pixels */
  originalHeight: number;

  /** Callback fired when a bbox is clicked */
  onBboxClick?: (chunkId: string, bbox: BBox) => void;

  /** Callback fired when a bbox is hovered or unhovered */
  onBboxHover?: (chunkId: string | null) => void;

  /** ID of the currently active chunk (highlighted) */
  activeChunkId?: string | null;

  /** ID of the currently hovered chunk */
  hoveredChunkId?: string | null;

  /** Additional CSS class name for the overlay container */
  className?: string;
}
```

**Usage Example**:

```tsx
function DocumentPage() {
  const imageRef = useRef<HTMLImageElement>(null);
  const [activeChunk, setActiveChunk] = useState<string | null>(null);

  return (
    <div style={{ position: 'relative' }}>
      <img
        ref={imageRef}
        src="/document-page-1.png"
        alt="Document page"
      />
      <BoundingBoxOverlay
        imageElement={imageRef.current}
        bboxes={documentBboxes}
        originalWidth={612}
        originalHeight={792}
        onBboxClick={(chunkId) => setActiveChunk(chunkId)}
        onBboxHover={(chunkId) => console.log('Hover:', chunkId)}
        activeChunkId={activeChunk}
      />
    </div>
  );
}
```

**Features**:
- ✅ Automatic scaling with ResizeObserver
- ✅ Keyboard accessible (Tab, Enter, Space)
- ✅ ARIA attributes for screen readers
- ✅ Visual states (default, hovered, active)
- ✅ Element type-based styling

**CSS Modules**:
- `.overlay` - SVG container
- `.bbox` - Individual bounding box
- `.active` - Active state modifier
- `.hovered` - Hover state modifier
- `.type-heading`, `.type-table`, etc. - Element type modifiers

---

### BBoxController

Orchestration layer that coordinates bidirectional highlighting between bbox overlay and text chunks.

**Import**:
```tsx
import { BBoxController } from '@/features/details/components/BBoxController';
```

**Props**:

```typescript
interface BBoxControllerProps {
  /** Document ID */
  docId: string;

  /** Current page number (1-indexed) */
  currentPage: number;

  /** Reference to the image element to overlay bboxes on */
  imageElement: HTMLImageElement | null;

  /** Reference to the markdown container for chunk highlighting */
  markdownContainerRef: RefObject<HTMLElement>;

  /** Whether to automatically scroll to active chunk */
  autoScroll?: boolean; // default: true

  /** Offset from top for scrolling (useful for fixed headers) */
  scrollOffset?: number; // default: 0

  /** Scroll behavior */
  scrollBehavior?: ScrollBehavior; // default: 'smooth'

  /** Callback fired when bbox is clicked (optional) */
  onBboxClick?: (chunkId: string, bbox: BBox) => void;

  /** Callback fired when chunk hover state changes (optional) */
  onChunkHover?: (chunkId: string | null) => void;

  /** Whether to enable URL parameter navigation */
  enableUrlNavigation?: boolean; // default: true
}
```

**Usage Example**:

```tsx
function DocumentDetails() {
  const imageRef = useRef<HTMLImageElement>(null);
  const markdownRef = useRef<HTMLDivElement>(null);
  const [currentPage, setCurrentPage] = useState(1);

  return (
    <div>
      <img ref={imageRef} src={`/doc/${docId}/page/${currentPage}`} />
      <div ref={markdownRef}>
        <Markdown>{documentContent}</Markdown>
      </div>

      <BBoxController
        docId={docId}
        currentPage={currentPage}
        imageElement={imageRef.current}
        markdownContainerRef={markdownRef}
        scrollOffset={60} // Account for fixed header
        onBboxClick={(chunkId) => console.log('Clicked:', chunkId)}
      />
    </div>
  );
}
```

**Features**:
- ✅ Fetches document structure automatically
- ✅ Manages shared highlighting state
- ✅ Coordinates bbox ↔ chunk events
- ✅ Handles URL-based navigation
- ✅ Loading and error state handling

---

## Hooks

### useChunkNavigation

Hook for URL parameter-based chunk navigation with optional URL updating.

**Import**:
```tsx
import { useChunkNavigation } from '@/features/details/hooks/useChunkNavigation';
```

**Signature**:

```typescript
function useChunkNavigation(options?: {
  /** Callback fired when navigation to chunk occurs */
  onChunkNavigate?: (chunkId: string) => void;

  /** Whether to update URL when navigateToChunk is called */
  updateUrl?: boolean; // default: false
}): {
  /** Chunk ID from URL parameter (null if not present) */
  initialChunkId: string | null;

  /** Function to navigate to a chunk programmatically */
  navigateToChunk: (chunkId: string, updateUrl?: boolean) => void;
}
```

**Usage Example**:

```tsx
function DocumentView() {
  const { initialChunkId, navigateToChunk } = useChunkNavigation({
    onChunkNavigate: (chunkId) => {
      console.log('Navigating to:', chunkId);
      scrollToChunk(chunkId);
      setActiveChunk(chunkId);
    },
    updateUrl: true
  });

  useEffect(() => {
    if (initialChunkId) {
      console.log('Deep linked to:', initialChunkId);
    }
  }, [initialChunkId]);

  return (
    <button onClick={() => navigateToChunk('chunk-5')}>
      Jump to Section 5
    </button>
  );
}
```

**Features**:
- ✅ Parses chunk ID from URL on mount
- ✅ Fires callback for initial navigation
- ✅ Programmatic navigation with `navigateToChunk`
- ✅ Optional URL updating
- ✅ React Router integration

---

### useChunkHighlight

Hook for managing chunk highlighting in markdown content with bidirectional events.

**Import**:
```tsx
import { useChunkHighlight } from '@/components/ChunkHighlighter/useChunkHighlight';
```

**Signature**:

```typescript
function useChunkHighlight(options: {
  /** Container ref for markdown content */
  containerRef: RefObject<HTMLElement>;

  /** Active chunk ID */
  activeChunkId: string | null;

  /** Hovered chunk ID */
  hoveredChunkId: string | null;

  /** Callback when chunk is hovered */
  onChunkHover?: (chunkId: string | null) => void;

  /** Scroll behavior */
  scrollBehavior?: ScrollBehavior; // default: 'smooth'

  /** Scroll offset for fixed headers */
  scrollOffset?: number; // default: 0

  /** Whether to auto-scroll when activeChunkId changes */
  autoScrollToActive?: boolean; // default: true
}): {
  /** Function to scroll to a specific chunk */
  scrollToChunk: (chunkId: string) => void;
}
```

**Usage Example**:

```tsx
function MarkdownContent({ activeChunkId, hoveredChunkId, onHover }) {
  const containerRef = useRef<HTMLDivElement>(null);

  const { scrollToChunk } = useChunkHighlight({
    containerRef,
    activeChunkId,
    hoveredChunkId,
    onChunkHover: onHover,
    scrollOffset: 60,
    autoScrollToActive: true
  });

  return (
    <div ref={containerRef}>
      <Markdown>{content}</Markdown>
    </div>
  );
}
```

**Features**:
- ✅ Applies CSS classes for active/hovered states
- ✅ Smooth scrolling to chunks
- ✅ Hover event handling
- ✅ Auto-scroll on active change
- ✅ Header offset support

---

### useBboxScaling

Hook for tracking displayed image dimensions with ResizeObserver.

**Import**:
```tsx
import { useBboxScaling } from '@/components/BoundingBoxOverlay/useBboxScaling';
```

**Signature**:

```typescript
function useBboxScaling(
  imageElement: HTMLImageElement | null
): DisplayedDimensions;

interface DisplayedDimensions {
  width: number;
  height: number;
}
```

**Usage Example**:

```tsx
function ImageOverlay({ imageRef }) {
  const dimensions = useBboxScaling(imageRef.current);

  return (
    <svg
      width={dimensions.width}
      height={dimensions.height}
    >
      {/* Scaled bboxes */}
    </svg>
  );
}
```

**Features**:
- ✅ Tracks image resize events
- ✅ Cleans up ResizeObserver on unmount
- ✅ Returns { width: 0, height: 0 } when image not loaded

---

### useDocumentStructure

Hook for fetching document structure data with React Query.

**Import**:
```tsx
import { useDocumentStructure } from '@/hooks/useDocumentStructure';
```

**Signature**:

```typescript
function useDocumentStructure(options: {
  docId: string;
  page: number;
  enabled?: boolean; // default: true
}): {
  structure: DocumentStructure | null;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
}
```

**Usage Example**:

```tsx
function DocumentPage({ docId, page }) {
  const { structure, isLoading, isError } = useDocumentStructure({
    docId,
    page,
    enabled: true
  });

  if (isLoading) return <Spinner />;
  if (isError) return <Error />;
  if (!structure) return null;

  return <BBoxDisplay structure={structure} />;
}
```

**Features**:
- ✅ React Query integration (caching, deduplication)
- ✅ Automatic refetch on docId/page change
- ✅ Error handling
- ✅ Loading states

---

## Type Definitions

### BBox

Base bounding box coordinates.

```typescript
interface BBox {
  /** Left edge x-coordinate */
  x1: number;

  /** Top edge y-coordinate */
  y1: number;

  /** Right edge x-coordinate */
  x2: number;

  /** Bottom edge y-coordinate */
  y2: number;
}
```

---

### BBoxWithMetadata

Bounding box with chunk and element information.

```typescript
interface BBoxWithMetadata extends BBox {
  /** Unique identifier for the chunk */
  chunk_id: string;

  /** Type of document element */
  element_type?: 'heading' | 'table' | 'picture' | 'text' | string;

  /** Confidence score (0-1) */
  confidence?: number;

  /** Additional metadata */
  metadata?: Record<string, unknown>;
}
```

---

### ScaledBBox

Bounding box with calculated dimensions.

```typescript
interface ScaledBBox extends BBox {
  /** Width (x2 - x1) */
  width: number;

  /** Height (y2 - y1) */
  height: number;
}
```

---

### ScalingOptions

Options for bbox scaling operations.

```typescript
interface ScalingOptions {
  /** Minimum size in pixels */
  minSize?: number; // default: 10

  /** Whether to enforce minimum */
  enforceMinimum?: boolean; // default: true

  /** Whether to clamp to bounds */
  clampToBounds?: boolean; // default: true
}
```

---

## Utilities

### scaleBboxForDisplay

Scales a bounding box from original to display dimensions.

**Import**:
```tsx
import { scaleBboxForDisplay } from '@/utils/coordinateScaler';
```

**Signature**:

```typescript
function scaleBboxForDisplay(
  bbox: BBox,
  originalWidth: number,
  originalHeight: number,
  displayedWidth: number,
  displayedHeight: number,
  options?: ScalingOptions
): ScaledBBox;
```

**Usage Example**:

```tsx
const scaled = scaleBboxForDisplay(
  { x1: 72, y1: 100, x2: 540, y2: 150 },
  612,  // original width
  792,  // original height
  400,  // displayed width
  520,  // displayed height
  {
    minSize: 10,
    enforceMinimum: true,
    clampToBounds: true
  }
);

console.log(scaled);
// { x1: 47, y1: 66, x2: 353, y2: 98, width: 306, height: 32 }
```

---

### parseChunkFromUrl

Parses chunk ID from URL search parameters.

**Import**:
```tsx
import { parseChunkFromUrl } from '@/features/details/utils/urlParams';
```

**Signature**:

```typescript
function parseChunkFromUrl(searchParams?: string): string | null;
```

**Usage Example**:

```tsx
const chunkId = parseChunkFromUrl('?chunk=chunk-5&page=2');
console.log(chunkId); // "chunk-5"
```

---

### updateChunkInUrl

Updates chunk parameter in URL without page reload.

**Import**:
```tsx
import { updateChunkInUrl } from '@/features/details/utils/urlParams';
```

**Signature**:

```typescript
function updateChunkInUrl(chunkId: string): void;
```

**Usage Example**:

```tsx
updateChunkInUrl('chunk-10');
// URL becomes: /details/doc-123?chunk=chunk-10
```

---

## Accessibility

### ARIA Attributes

All components include proper ARIA attributes:

```tsx
<svg role="img" aria-label="Document bounding boxes">
  <rect
    role="button"
    aria-label="Heading bounding box"
    tabIndex={0}
    data-chunk-id="chunk-0"
  />
</svg>
```

### Keyboard Support

Standard keyboard interactions:
- `Tab` - Focus next bbox
- `Enter` / `Space` - Activate focused bbox
- `Esc` - Clear active selection

### Screen Reader Support

Elements announce:
- Element type (heading, table, etc.)
- Current state (active, hovered)
- Action hints ("Press Enter to navigate")

---

## Performance

### Optimization Strategies

1. **useMemo** for scaled bboxes (prevents recomputation)
2. **useCallback** for event handlers (prevents re-renders)
3. **ResizeObserver** for efficient dimension tracking
4. **React Query** for API caching and deduplication

### Performance Metrics

- Initial render: < 500ms
- Click response: < 100ms
- Hover response: < 50ms
- Scroll animation: 600ms
- Frame rate: 60fps

---

## Error Handling

All components gracefully handle:
- Missing structure data (renders nothing)
- Invalid chunk IDs (logs warning, continues)
- Image load failures (no crash)
- API errors (displays error state)

---

## Testing

See comprehensive E2E tests:
- `/frontend/e2e/bbox-overlay.spec.js`
- `/frontend/e2e/bidirectional-highlighting.spec.js`
- `/frontend/e2e/url-navigation.spec.js`
- `/frontend/e2e/accessibility.spec.js`
- `/frontend/e2e/performance.spec.js`

---

## Related Documentation

- [User Guide](../features/bbox-overlay-user-guide.md)
- [Integration Guide](../integration/bbox-overlay-integration.md)
- [Performance Benchmarks](../performance/bbox-overlay-benchmarks.md)

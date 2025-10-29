# BoundingBox Overlay Integration Guide

**Agent 14: Testing & Documentation**
**Wave 3 - BBox Overlay React Implementation**

Complete guide for integrating bbox overlay functionality into your document viewing pages.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Step-by-Step Integration](#step-by-step-integration)
3. [Complete Examples](#complete-examples)
4. [Common Patterns](#common-patterns)
5. [Migration Guide](#migration-guide)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

---

## Quick Start

**Minimal integration (3 steps)**:

```tsx
import { BBoxController } from '@/features/details/components/BBoxController';

function DocumentPage() {
  const imageRef = useRef<HTMLImageElement>(null);
  const markdownRef = useRef<HTMLDivElement>(null);

  return (
    <>
      <img ref={imageRef} src="/doc/page.png" />
      <div ref={markdownRef}><Markdown>{content}</Markdown></div>
      <BBoxController
        docId="doc-123"
        currentPage={1}
        imageElement={imageRef.current}
        markdownContainerRef={markdownRef}
      />
    </>
  );
}
```

That's it! BBoxController handles everything else.

---

## Step-by-Step Integration

### Step 1: Add Required Refs

Create refs for your image and markdown container:

```tsx
function DocumentDetails() {
  // 1. Create refs
  const imageRef = useRef<HTMLImageElement>(null);
  const markdownRef = useRef<HTMLDivElement>(null);

  return (
    <div>
      {/* 2. Attach refs to elements */}
      <img ref={imageRef} src={documentImage} alt="Document page" />
      <div ref={markdownRef}>
        <Markdown>{documentContent}</Markdown>
      </div>
    </div>
  );
}
```

**Why refs?**
- BBoxController needs direct DOM access for overlay positioning
- Markdown container needed for chunk highlighting and scrolling

---

### Step 2: Add BBoxController

Import and render the controller:

```tsx
import { BBoxController } from '@/features/details/components/BBoxController';

function DocumentDetails() {
  const imageRef = useRef<HTMLImageElement>(null);
  const markdownRef = useRef<HTMLDivElement>(null);
  const [currentPage, setCurrentPage] = useState(1);

  return (
    <div>
      <img ref={imageRef} src={documentImage} />
      <div ref={markdownRef}>
        <Markdown>{documentContent}</Markdown>
      </div>

      {/* 3. Add BBoxController */}
      <BBoxController
        docId={documentId}
        currentPage={currentPage}
        imageElement={imageRef.current}
        markdownContainerRef={markdownRef}
      />
    </div>
  );
}
```

**Required props**:
- `docId` - Document identifier for fetching structure
- `currentPage` - Current page number (1-indexed)
- `imageElement` - Ref to image element
- `markdownContainerRef` - Ref to markdown container

---

### Step 3: Add Styling (Optional)

The overlay uses CSS modules, but you may want to position the image container:

```tsx
function DocumentDetails() {
  return (
    <div style={{ position: 'relative' }}>
      {/* Image and overlay will share this positioned container */}
      <img ref={imageRef} src={documentImage} />

      {/* BBoxController renders overlay absolutely positioned over image */}
      <BBoxController {...props} />
    </div>
  );
}
```

**CSS tips**:
- Image container should be `position: relative`
- Overlay will be `position: absolute` over the image
- No z-index conflicts (overlay is already configured)

---

### Step 4: Configure Options (Optional)

Customize behavior with optional props:

```tsx
<BBoxController
  docId={documentId}
  currentPage={currentPage}
  imageElement={imageRef.current}
  markdownContainerRef={markdownRef}

  // Optional: Scroll configuration
  autoScroll={true}
  scrollOffset={60}  // Account for fixed header
  scrollBehavior="smooth"

  // Optional: Callbacks
  onBboxClick={(chunkId, bbox) => {
    console.log('Clicked:', chunkId);
    analytics.track('bbox_click', { chunkId });
  }}
  onChunkHover={(chunkId) => {
    console.log('Hovering:', chunkId);
  }}

  // Optional: URL navigation
  enableUrlNavigation={true}
/>
```

---

## Complete Examples

### Example 1: Basic Document Viewer

```tsx
import React, { useRef, useState } from 'react';
import { BBoxController } from '@/features/details/components/BBoxController';
import Markdown from 'react-markdown';

function BasicDocumentViewer({ documentId }) {
  const imageRef = useRef<HTMLImageElement>(null);
  const markdownRef = useRef<HTMLDivElement>(null);
  const [currentPage, setCurrentPage] = useState(1);

  // Fetch document data
  const { data: document } = useDocument(documentId);

  if (!document) return <Loading />;

  return (
    <div className="document-viewer">
      {/* Page controls */}
      <div className="page-controls">
        <button onClick={() => setCurrentPage(p => Math.max(1, p - 1))}>
          Previous
        </button>
        <span>Page {currentPage} of {document.total_pages}</span>
        <button onClick={() => setCurrentPage(p => Math.min(document.total_pages, p + 1))}>
          Next
        </button>
      </div>

      {/* Image + Overlay */}
      <div className="image-container" style={{ position: 'relative' }}>
        <img
          ref={imageRef}
          src={`/api/documents/${documentId}/pages/${currentPage}/image`}
          alt={`Page ${currentPage}`}
        />
      </div>

      {/* Content */}
      <div ref={markdownRef} className="content">
        <Markdown>{document.content}</Markdown>
      </div>

      {/* BBox Overlay Controller */}
      <BBoxController
        docId={documentId}
        currentPage={currentPage}
        imageElement={imageRef.current}
        markdownContainerRef={markdownRef}
      />
    </div>
  );
}
```

---

### Example 2: With Fixed Header

```tsx
function DocumentViewerWithHeader({ documentId }) {
  const HEADER_HEIGHT = 60;
  const imageRef = useRef<HTMLImageElement>(null);
  const markdownRef = useRef<HTMLDivElement>(null);
  const [currentPage, setCurrentPage] = useState(1);

  return (
    <div>
      {/* Fixed header */}
      <header style={{ position: 'fixed', top: 0, height: HEADER_HEIGHT }}>
        <h1>Document Viewer</h1>
      </header>

      {/* Content with top padding */}
      <main style={{ paddingTop: HEADER_HEIGHT }}>
        <div style={{ position: 'relative' }}>
          <img ref={imageRef} src={pageImage} />
        </div>

        <div ref={markdownRef}>
          <Markdown>{content}</Markdown>
        </div>

        {/* Pass scrollOffset to account for fixed header */}
        <BBoxController
          docId={documentId}
          currentPage={currentPage}
          imageElement={imageRef.current}
          markdownContainerRef={markdownRef}
          scrollOffset={HEADER_HEIGHT}  // Important!
        />
      </main>
    </div>
  );
}
```

---

### Example 3: With Analytics

```tsx
function DocumentViewerWithAnalytics({ documentId }) {
  const imageRef = useRef<HTMLImageElement>(null);
  const markdownRef = useRef<HTMLDivElement>(null);

  const handleBboxClick = useCallback((chunkId: string, bbox: BBox) => {
    // Track bbox interactions
    analytics.track('bbox_interaction', {
      documentId,
      chunkId,
      elementType: bbox.element_type,
      timestamp: new Date().toISOString()
    });
  }, [documentId]);

  const handleChunkHover = useCallback((chunkId: string | null) => {
    if (chunkId) {
      analytics.track('chunk_hover', { documentId, chunkId });
    }
  }, [documentId]);

  return (
    <>
      <img ref={imageRef} src={pageImage} />
      <div ref={markdownRef}><Markdown>{content}</Markdown></div>

      <BBoxController
        docId={documentId}
        currentPage={1}
        imageElement={imageRef.current}
        markdownContainerRef={markdownRef}
        onBboxClick={handleBboxClick}
        onChunkHover={handleChunkHover}
      />
    </>
  );
}
```

---

### Example 4: Multi-Page with URL Sync

```tsx
function MultiPageDocumentViewer({ documentId }) {
  const imageRef = useRef<HTMLImageElement>(null);
  const markdownRef = useRef<HTMLDivElement>(null);

  // Get page from URL
  const [searchParams, setSearchParams] = useSearchParams();
  const currentPage = parseInt(searchParams.get('page') || '1', 10);

  const setPage = (page: number) => {
    setSearchParams({ page: page.toString() });
  };

  return (
    <>
      <div className="page-controls">
        <button onClick={() => setPage(currentPage - 1)}>Prev</button>
        <span>Page {currentPage}</span>
        <button onClick={() => setPage(currentPage + 1)}>Next</button>
      </div>

      <img ref={imageRef} src={`/pages/${currentPage}`} />
      <div ref={markdownRef}><Markdown>{content}</Markdown></div>

      {/* URL navigation enabled */}
      <BBoxController
        docId={documentId}
        currentPage={currentPage}
        imageElement={imageRef.current}
        markdownContainerRef={markdownRef}
        enableUrlNavigation={true}  // Enables ?chunk=... navigation
      />
    </>
  );
}
```

---

## Common Patterns

### Pattern 1: Lazy Loading

Only render BBoxController when image is loaded:

```tsx
function LazyBBoxViewer() {
  const imageRef = useRef<HTMLImageElement>(null);
  const [imageLoaded, setImageLoaded] = useState(false);

  return (
    <>
      <img
        ref={imageRef}
        src={imageSrc}
        onLoad={() => setImageLoaded(true)}
      />

      {imageLoaded && (
        <BBoxController
          imageElement={imageRef.current}
          {...otherProps}
        />
      )}
    </>
  );
}
```

---

### Pattern 2: Conditional Rendering

Only show overlay when structure is available:

```tsx
function ConditionalBBoxViewer({ documentId }) {
  const { structure } = useDocumentStructure({ docId: documentId, page: 1 });

  return (
    <>
      <img ref={imageRef} src={imageSrc} />
      <div ref={markdownRef}><Markdown>{content}</Markdown></div>

      {/* Only render if structure exists */}
      {structure && (
        <BBoxController
          docId={documentId}
          currentPage={1}
          imageElement={imageRef.current}
          markdownContainerRef={markdownRef}
        />
      )}
    </>
  );
}
```

---

### Pattern 3: Custom Scroll Behavior

Disable auto-scroll and handle manually:

```tsx
function CustomScrollViewer() {
  const imageRef = useRef<HTMLImageElement>(null);
  const markdownRef = useRef<HTMLDivElement>(null);
  const [activeChunk, setActiveChunk] = useState<string | null>(null);

  const handleBboxClick = (chunkId: string) => {
    setActiveChunk(chunkId);

    // Custom scroll logic
    const element = document.querySelector(`[data-chunk-id="${chunkId}"]`);
    if (element) {
      element.scrollIntoView({ behavior: 'instant', block: 'center' });
    }
  };

  return (
    <>
      <img ref={imageRef} src={imageSrc} />
      <div ref={markdownRef}><Markdown>{content}</Markdown></div>

      <BBoxController
        docId={documentId}
        currentPage={1}
        imageElement={imageRef.current}
        markdownContainerRef={markdownRef}
        autoScroll={false}  // Disable auto-scroll
        onBboxClick={handleBboxClick}
      />
    </>
  );
}
```

---

## Migration Guide

### Migrating from Legacy UI

**Before (Legacy)**:
```html
<div class="document-page">
  <img src="/page.png" />
  <div class="content">...</div>
</div>
```

**After (React with BBox)**:
```tsx
function DocumentPage() {
  const imageRef = useRef<HTMLImageElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  return (
    <div className="document-page">
      <img ref={imageRef} src="/page.png" />
      <div ref={contentRef} className="content">...</div>

      {/* Add BBoxController */}
      <BBoxController
        docId={docId}
        currentPage={page}
        imageElement={imageRef.current}
        markdownContainerRef={contentRef}
      />
    </div>
  );
}
```

**Changes**:
1. ✅ Add refs to image and content container
2. ✅ Import and render BBoxController
3. ✅ Pass required props
4. ✅ No CSS changes needed (overlay handles positioning)

---

### Migrating Existing React Pages

**Before**:
```tsx
function ExistingPage({ doc }) {
  return (
    <div>
      <DocumentImage src={doc.image} />
      <DocumentContent markdown={doc.content} />
    </div>
  );
}
```

**After**:
```tsx
function ExistingPage({ doc }) {
  const imageRef = useRef<HTMLImageElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  return (
    <div>
      <DocumentImage ref={imageRef} src={doc.image} />
      <DocumentContent ref={contentRef} markdown={doc.content} />

      {/* Add BBoxController */}
      <BBoxController
        docId={doc.id}
        currentPage={doc.page}
        imageElement={imageRef.current}
        markdownContainerRef={contentRef}
      />
    </div>
  );
}
```

**Steps**:
1. Add refs to child components (may need to forward refs)
2. Import BBoxController
3. Render with proper props
4. Test scrolling and highlighting

---

## Troubleshooting

### Problem: Overlay Not Appearing

**Symptom**: No bboxes visible on image

**Debug checklist**:
```tsx
// 1. Check refs are set
console.log('Image ref:', imageRef.current);
console.log('Markdown ref:', markdownRef.current);

// 2. Check image is loaded
<img
  ref={imageRef}
  src={src}
  onLoad={() => console.log('Image loaded')}
  onError={(e) => console.error('Image error:', e)}
/>

// 3. Check structure data
const { structure, isLoading, isError } = useDocumentStructure({
  docId,
  page: currentPage
});
console.log('Structure:', structure, 'Loading:', isLoading, 'Error:', isError);

// 4. Check for errors in console
// Look for fetch errors, CORS issues, or JavaScript errors
```

**Common fixes**:
- Ensure image has loaded before rendering controller
- Verify structure API is returning data
- Check CORS if API on different domain
- Verify refs are not null

---

### Problem: Scrolling Not Working

**Symptom**: Clicking bbox doesn't scroll to content

**Debug**:
```tsx
<BBoxController
  {...props}
  onBboxClick={(chunkId) => {
    console.log('Clicked chunk:', chunkId);

    // Check if chunk exists
    const element = document.querySelector(`[data-chunk-id="${chunkId}"]`);
    console.log('Chunk element:', element);

    if (!element) {
      console.error('Chunk not found in DOM!');
    }
  }}
/>
```

**Common fixes**:
- Verify markdown container has `data-chunk-id` attributes
- Check markdown renderer is adding proper attributes
- Ensure chunk IDs match between structure and markdown
- Verify autoScroll is not disabled

---

### Problem: Bboxes Misaligned

**Symptom**: Bboxes don't match document elements

**Debug**:
```tsx
// Check original vs displayed dimensions
const { structure } = useDocumentStructure({ docId, page });
console.log('Original dimensions:', structure.page_width, structure.page_height);

const displayedDims = useBboxScaling(imageRef.current);
console.log('Displayed dimensions:', displayedDims.width, displayedDims.height);

// Check scaling calculation
const bbox = structure.elements[0].bbox;
const scaled = scaleBboxForDisplay(
  bbox,
  structure.page_width,
  structure.page_height,
  displayedDims.width,
  displayedDims.height
);
console.log('Original bbox:', bbox);
console.log('Scaled bbox:', scaled);
```

**Common fixes**:
- Verify structure contains correct page dimensions
- Check image CSS (no `object-fit: cover` or similar)
- Ensure image displays at natural aspect ratio
- Verify no CSS transforms on image

---

## Best Practices

### 1. Performance

✅ **Use memo for expensive computations**:
```tsx
const transformedData = useMemo(
  () => expensiveTransform(rawData),
  [rawData]
);
```

✅ **Debounce resize events** (handled by useBboxScaling):
```tsx
// Built-in, no action needed
```

✅ **Lazy load images**:
```tsx
<img
  ref={imageRef}
  loading="lazy"
  src={imageSrc}
/>
```

---

### 2. Accessibility

✅ **Provide alt text**:
```tsx
<img
  ref={imageRef}
  src={imageSrc}
  alt={`Document page ${currentPage}`}
/>
```

✅ **Support keyboard navigation** (built-in):
```tsx
// No action needed, BBoxController handles it
```

✅ **Test with screen readers**:
- NVDA (Windows)
- JAWS (Windows)
- VoiceOver (macOS/iOS)

---

### 3. Error Handling

✅ **Handle missing structure gracefully**:
```tsx
const { structure, isError } = useDocumentStructure({ docId, page });

if (isError) {
  return <div>Unable to load document structure</div>;
}

if (!structure) {
  return null; // Or fallback UI
}
```

✅ **Handle image load failures**:
```tsx
<img
  ref={imageRef}
  src={imageSrc}
  onError={() => {
    console.error('Image failed to load');
    setImageError(true);
  }}
/>
```

---

### 4. Testing

✅ **Test with E2E tests**:
```tsx
// Use Playwright tests provided
npx playwright test e2e/bbox-overlay.spec.js
```

✅ **Test across browsers**:
- Chrome/Edge (Chromium)
- Firefox
- Safari

✅ **Test responsive behavior**:
```tsx
// Resize window and verify bboxes scale
```

---

## Related Documentation

- [User Guide](../features/bbox-overlay-user-guide.md)
- [API Reference](../api/bbox-overlay-api.md)
- [Performance Benchmarks](../performance/bbox-overlay-benchmarks.md)

---

## Support

For integration questions:
1. Check this guide
2. Review API documentation
3. Check E2E test examples
4. File GitHub issue with:
   - Your integration code
   - Error messages
   - Browser/version
   - Expected vs actual behavior

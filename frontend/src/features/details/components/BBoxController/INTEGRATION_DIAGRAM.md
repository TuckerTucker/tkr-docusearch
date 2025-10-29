# BBoxController Integration Diagram

## Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Document Details View                          │
│                      (ContentViewer Component)                          │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         Slideshow Component                             │
│                    (Document Page Viewer)                               │
│                                                                          │
│  ┌────────────────────────────────────────────────────────┐             │
│  │  Image Container (position: relative)                  │             │
│  │                                                         │             │
│  │  ┌──────────────────────────────────────────────┐     │             │
│  │  │  <img ref={imageRef} src={pageImage} />      │     │             │
│  │  │  (Document page image)                       │     │             │
│  │  └──────────────────────────────────────────────┘     │             │
│  │                       ↑                                │             │
│  │                       │ imageElement                   │             │
│  │                       │                                │             │
│  │  ┌────────────────────┴──────────────────────────┐    │             │
│  │  │                                                │    │             │
│  │  │         BBoxController                         │    │             │
│  │  │     (Agent 8 - Orchestration Layer)           │    │             │
│  │  │                                                │    │             │
│  │  │  Props:                                        │    │             │
│  │  │  • docId: string                               │    │             │
│  │  │  • currentPage: number                         │    │             │
│  │  │  • imageElement: HTMLImageElement              │    │             │
│  │  │  • markdownContainerRef: RefObject            │    │             │
│  │  │                                                │    │             │
│  │  │  State:                                        │    │             │
│  │  │  • activeChunkId: string | null                │    │             │
│  │  │  • hoveredChunkId: string | null               │    │             │
│  │  │                                                │    │             │
│  │  └───────┬────────────────────────┬───────────────┘    │             │
│  │          │                        │                    │             │
│  └──────────┼────────────────────────┼────────────────────┘             │
│             │                        │                                  │
│             ↓                        ↓                                  │
│   ┌─────────────────────┐  ┌────────────────────┐                      │
│   │ BoundingBoxOverlay  │  │ useChunkHighlight  │                      │
│   │   (Agent 5)         │  │   (Agent 7)        │                      │
│   │                     │  │                    │                      │
│   │ • Visual overlays   │  │ • Text highlights  │                      │
│   │ • Interactive rects │  │ • Smooth scrolling │                      │
│   │ • Hover/click       │  │ • Focus management │                      │
│   └─────────────────────┘  └────────────────────┘                      │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         1. Structure Fetching                            │
└──────────────────────────────────────────────────────────────────────────┘

Backend API                    React Query                 BBoxController
     │                              │                            │
     │  GET /api/.../structure      │                            │
     │◄─────────────────────────────┤                            │
     │                              │                            │
     │  PageStructure JSON          │                            │
     ├─────────────────────────────►│                            │
     │                              │                            │
     │                              │  useDocumentStructure()    │
     │                              │◄───────────────────────────┤
     │                              │                            │
     │                              │  structure: PageStructure  │
     │                              ├───────────────────────────►│
     │                              │                            │

┌──────────────────────────────────────────────────────────────────────────┐
│                      2. Structure Transformation                         │
└──────────────────────────────────────────────────────────────────────────┘

PageStructure (from API)          BBoxController          BBoxWithMetadata[]
     │                                  │                         │
     │  {                               │                         │
     │    headings: [...],              │                         │
     │    tables: [...],                │                         │
     │    pictures: [...]               │                         │
     │  }                               │                         │
     ├─────────────────────────────────►│                         │
     │                                  │                         │
     │              transformStructureToBboxes()                  │
     │                                  ├────────────────────────►│
     │                                  │                         │
     │                                  │  [                      │
     │                                  │    {chunk_id, x1, y1,   │
     │                                  │     x2, y2, type},      │
     │                                  │    ...                  │
     │                                  │  ]                      │

┌──────────────────────────────────────────────────────────────────────────┐
│                    3. Bidirectional Event Flow                           │
└──────────────────────────────────────────────────────────────────────────┘

┌─────────────────────┐                           ┌────────────────────────┐
│ BoundingBoxOverlay  │                           │  Markdown Content      │
│  (Visual Layer)     │                           │  (Text Layer)          │
└──────────┬──────────┘                           └──────────┬─────────────┘
           │                                                 │
           │  User hovers bbox                               │
           │  onBboxHover(chunkId)                          │
           ├────────────────────────────────────┐            │
           │                                    │            │
           │                                    ↓            │
           │                         ┌─────────────────────┐ │
           │                         │  BBoxController     │ │
           │                         │                     │ │
           │                         │  State:             │ │
           │                         │  hoveredChunkId =   │ │
           │                         │    chunkId          │ │
           │                         └─────────────────────┘ │
           │                                    │            │
           │                                    │            │
           │                                    ├────────────┼───────┐
           │                                    │            │       │
           │  activeChunkId={chunkId}           │            │       │
           │◄───────────────────────────────────┘            │       │
           │                                                 │       │
           │  Bbox highlights                                │       │
           │                                                 │       │
           │                                hoveredChunkId = │       │
           │                                     chunkId     │       │
           │                                ◄────────────────┼───────┘
           │                                                 │
           │                                                 │  Chunk highlights
           │                                                 │

           │  User hovers chunk                              │
           │                                                 │
           │                                onChunkHover()   │
           │                                ◄────────────────┤
           │                                    │            │
           │                         ┌─────────▼───────────┐ │
           │                         │  BBoxController     │ │
           │                         │                     │ │
           │                         │  State:             │ │
           │                         │  hoveredChunkId =   │ │
           │                         │    chunkId          │ │
           │                         └─────────────────────┘ │
           │                                    │            │
           │  hoveredChunkId={chunkId}          │            │
           │◄───────────────────────────────────┘            │
           │                                                 │
           │  Bbox highlights                                │
           │                                                 │

┌──────────────────────────────────────────────────────────────────────────┐
│                       4. URL Navigation Flow                             │
└──────────────────────────────────────────────────────────────────────────┘

URL: /details/doc123?chunk=heading-0
           │
           │  useSearchParams()
           │
           ↓
┌────────────────────────┐
│  useChunkNavigation    │
│  (Agent 10)            │
│                        │
│  initialChunkId =      │
│    'heading-0'         │
└───────────┬────────────┘
            │
            │  onChunkNavigate('heading-0')
            │
            ↓
┌────────────────────────┐
│  BBoxController        │
│                        │
│  setActiveChunkId(     │
│    'heading-0'         │
│  )                     │
│  scrollToChunk(        │
│    'heading-0'         │
│  )                     │
└───────────┬────────────┘
            │
            ├────────────────────────────────┬─────────────────────────────┐
            │                                │                             │
            ↓                                ↓                             ↓
┌──────────────────────┐       ┌──────────────────────┐      ┌──────────────────────┐
│ BoundingBoxOverlay   │       │ useChunkHighlight    │      │ Markdown Container   │
│                      │       │                      │      │                      │
│ Highlights bbox      │       │ Adds 'chunk-active'  │      │ Scrolls into view    │
│ for 'heading-0'      │       │ class                │      │                      │
└──────────────────────┘       └──────────────────────┘      └──────────────────────┘
```

## State Synchronization

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        BBoxController State                              │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  const [activeChunkId, setActiveChunkId] = useState(null);      │    │
│  │  const [hoveredChunkId, setHoveredChunkId] = useState(null);    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                           │
│         ┌───────────────────────────┬──────────────────────────┐         │
│         │                           │                          │         │
│         ↓                           ↓                          ↓         │
│  ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐ │
│  │ BoundingBoxOverlay│    │ useChunkHighlight│    │ useChunkNavigation│ │
│  │                   │    │                  │    │                   │ │
│  │ Receives:         │    │ Receives:        │    │ Updates:          │ │
│  │ • activeChunkId   │    │ • activeChunkId  │    │ • activeChunkId   │ │
│  │ • hoveredChunkId  │    │ • hoveredChunkId │    │   (via callback)  │ │
│  │                   │    │                  │    │                   │ │
│  │ Fires:            │    │ Fires:           │    │                   │ │
│  │ • onBboxClick     │    │ • onChunkHover   │    │                   │ │
│  │ • onBboxHover     │    │                  │    │                   │ │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘ │
│         │                           │                                    │
│         └───────────────────────────┴─────────────────────────────────┐ │
│                                                                        │ │
│                          Updates shared state                          │ │
│                     (activeChunkId, hoveredChunkId)                    │ │
│                                                                        │ │
└────────────────────────────────────────────────────────────────────────┘
```

## Component Lifecycle

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     BBoxController Lifecycle                             │
└──────────────────────────────────────────────────────────────────────────┘

1. Mount
   │
   ├─ useDocumentStructure({ docId, page }) ──► Fetch structure
   │
   ├─ useChunkNavigation({ onChunkNavigate }) ─► Parse URL param
   │
   └─ useChunkHighlight({ containerRef, ... }) ─► Setup event listeners

2. Structure Loaded
   │
   ├─ transformStructureToBboxes(structure) ───► Convert to flat array
   │
   ├─ getOriginalDimensions(structure) ────────► Get image dimensions
   │
   └─ hasAnyBboxes(structure) ─────────────────► Check if renderable

3. Render
   │
   └─ <BoundingBoxOverlay
        imageElement={imageRef.current}
        bboxes={transformedBboxes}
        activeChunkId={activeChunkId}
        hoveredChunkId={hoveredChunkId}
        onBboxClick={handleBboxClick}
        onBboxHover={handleBboxHover}
      />

4. User Interaction
   │
   ├─ Bbox hover ──► setHoveredChunkId ──► Re-render ──► Chunk highlights
   │
   ├─ Bbox click ──► setActiveChunkId + scroll ──► Chunk active
   │
   ├─ Chunk hover ─► setHoveredChunkId ──► Re-render ──► Bbox highlights
   │
   └─ Chunk click ─► setActiveChunkId ──► Re-render ──► Bbox active

5. Page Change
   │
   ├─ currentPage prop changes
   │
   ├─ useDocumentStructure refetches ──────────► New structure
   │
   └─ State resets (activeChunkId, hoveredChunkId)

6. Unmount
   │
   └─ Cleanup event listeners (handled by hooks)
```

## Error Handling Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         Error Handling                                   │
└──────────────────────────────────────────────────────────────────────────┘

useDocumentStructure({ docId, page })
           │
           ├─ isLoading = true ─────────► return null (no render)
           │
           ├─ isError = true ───────────► console.error() + return null
           │
           ├─ structure = undefined ────► return null
           │
           ├─ !hasAnyBboxes(structure) ─► return null
           │
           └─ Success ──────────────────► Render BoundingBoxOverlay

Graceful Degradation:
• No visual disruption on error
• Console logging for debugging
• Overlay simply doesn't appear
• Rest of UI continues working
```

## Integration Points Summary

```
BBoxController
├── Dependencies (Input)
│   ├── useDocumentStructure (Agent 6) ─────► Structure data
│   ├── useChunkNavigation (Agent 10) ──────► URL navigation
│   ├── useChunkHighlight (Agent 7) ────────► Text highlighting
│   └── BoundingBoxOverlay (Agent 5) ───────► Visual overlays
│
├── Props (Input)
│   ├── docId ──────────────────────────────► Document identifier
│   ├── currentPage ────────────────────────► Page number
│   ├── imageElement ───────────────────────► Image ref for overlay
│   └── markdownContainerRef ───────────────► Container ref for chunks
│
├── State (Internal)
│   ├── activeChunkId ──────────────────────► Click selection
│   └── hoveredChunkId ─────────────────────► Hover state
│
└── Outputs (Callbacks - Optional)
    ├── onBboxClick(chunkId, bbox) ─────────► External tracking
    └── onChunkHover(chunkId) ──────────────► External tracking
```

## File Structure Visualization

```
frontend/src/
├── features/details/
│   └── components/
│       └── BBoxController/                    ← AGENT 8 TERRITORY
│           ├── BBoxController.tsx             ← Main orchestration
│           ├── structureTransform.ts          ← Transformation utils
│           ├── BBoxController.test.tsx        ← Test suite
│           ├── index.ts                       ← Barrel exports
│           ├── README.md                      ← Documentation
│           ├── AGENT_8_SUMMARY.md            ← Implementation summary
│           └── INTEGRATION_DIAGRAM.md        ← This file
│
├── components/
│   ├── BoundingBoxOverlay/                    ← Agent 5 (dependency)
│   │   ├── BoundingBoxOverlay.tsx
│   │   ├── types.ts
│   │   └── useBboxScaling.ts
│   │
│   └── ChunkHighlighter/                      ← Agent 7 (dependency)
│       ├── ChunkHighlighter.tsx
│       ├── useChunkHighlight.ts
│       └── scrollToChunk.ts
│
├── hooks/
│   └── useDocumentStructure.ts                ← Agent 6 (dependency)
│
└── media/
    └── Slideshow.jsx                          ← Integration point (modified)
```

---

## Summary

The BBoxController serves as the **central orchestration hub** that:

1. **Fetches** document structure data via useDocumentStructure
2. **Transforms** structure to flat bbox array via structureTransform
3. **Manages** shared highlight state (active + hovered)
4. **Coordinates** bidirectional events between visual and text layers
5. **Handles** URL navigation via useChunkNavigation
6. **Integrates** seamlessly into existing Slideshow component

All without breaking existing functionality or requiring major refactoring.

**Result**: A powerful bidirectional highlighting system that enhances document exploration UX.

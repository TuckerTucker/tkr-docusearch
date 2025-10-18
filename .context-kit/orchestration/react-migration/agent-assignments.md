# Agent Territorial Assignments

**Migration Goal:** Vanilla JS → React + Vite SPA
**Total Agents:** 6
**Execution Model:** Wave-based with synchronization gates

---

## Agent 1: foundation-agent

**Primary Responsibility:** Project scaffolding, build configuration, routing, shared utilities

### File Ownership

```
frontend/
├── package.json                     [CREATE]
├── vite.config.js                   [CREATE]
├── .eslintrc.js                     [CREATE]
├── .gitignore                       [CREATE]
├── public/
│   ├── index.html                   [CREATE]
│   └── favicon.svg                  [COPY]
├── src/
│   ├── main.jsx                     [CREATE]
│   ├── App.jsx                      [CREATE]
│   ├── styles/
│   │   ├── global.css               [COPY from src/frontend/styles.css]
│   │   ├── themes/                  [COPY ALL from src/frontend/styles/themes/]
│   │   └── accessibility.css        [COPY]
│   ├── constants/
│   │   ├── config.js                [CREATE]
│   │   └── routes.js                [CREATE]
│   ├── utils/
│   │   ├── clipboard.js             [COPY from src/frontend/clipboard-utils.js]
│   │   ├── download.js              [COPY from src/frontend/download-utils.js]
│   │   ├── formatting.js            [CREATE]
│   │   ├── url.js                   [CREATE]
│   │   └── assets.js                [COPY from src/frontend/assets.js]
│   └── components/
│       └── ErrorBoundary.jsx        [CREATE]
```

### Wave 0 Tasks (Solo)
1. Initialize Vite + React project
2. Install dependencies (React Router, React Query, Zustand)
3. Configure Vite proxy
4. Copy CSS assets
5. Set up routing with placeholder views
6. Verify dev server works

### Wave 1 Tasks (Parallel with others)
1. Copy utility modules
2. Create constants
3. Create ErrorBoundary
4. Add React Query provider to App.jsx
5. Configure ESLint

### Wave 4 Tasks (Final Integration)
1. Create production build configuration
2. Optimize bundle chunks
3. Create deployment scripts
4. Integration with `scripts/start-all.sh`

---

## Agent 2: infrastructure-agent

**Primary Responsibility:** API clients, state management, WebSocket, custom hooks

### File Ownership

```
frontend/src/
├── services/
│   ├── api.js                       [PORT from src/frontend/api-client.js]
│   ├── websocket.js                 [PORT from src/frontend/websocket-client.js]
│   └── research.js                  [CREATE]
├── stores/
│   ├── useConnectionStore.js        [CREATE]
│   ├── useThemeStore.js             [CREATE]
│   └── useDocumentStore.js          [CREATE]
└── hooks/
    ├── useWebSocket.js              [CREATE - wraps services/websocket.js]
    ├── useDocuments.js              [CREATE - React Query wrapper]
    ├── useDocumentDetails.js        [CREATE - React Query wrapper]
    ├── useResearch.js               [CREATE - React Query wrapper]
    ├── useClipboard.js              [CREATE]
    └── useKeyboardNav.js            [CREATE]
```

### Wave 1 Tasks
1. Port API client (api.js)
2. Port WebSocket client (websocket.js + useWebSocket.js hook)
3. Create connection store (Zustand)
4. Create theme store (Zustand with persist)
5. Create documents store (Zustand with persist)
6. Create useDocuments hook (React Query)
7. Create useDocumentDetails hook (React Query)
8. Create useResearch hook (React Query)
9. Create useClipboard hook
10. Create useKeyboardNav hook

### Integration Contracts Provided
- `api-service.contract.md`
- `stores.contract.md`
- `hooks.contract.md`

### Testing Requirements
- Unit tests for all stores
- Unit tests for all hooks
- Mock API responses (MSW handlers)

---

## Agent 3: layout-agent

**Primary Responsibility:** Layout shell, header, footer, theme/style components

### File Ownership

```
frontend/src/components/
├── layout/
│   ├── Layout.jsx                   [CREATE]
│   ├── Header.jsx                   [CREATE]
│   └── Footer.jsx                   [CREATE]
└── common/
    ├── ThemeToggle.jsx              [PORT from src/frontend/theme-toggle.js]
    ├── StyleSelector.jsx            [PORT from src/frontend/style-selector.js]
    ├── ConnectionStatus.jsx         [CREATE]
    └── LoadingSpinner.jsx           [CREATE]
```

### Wave 1 Tasks
1. Port ThemeToggle component
2. Port StyleSelector component
3. Create ConnectionStatus component
4. Create LoadingSpinner component
5. Create Header component
6. Create Footer component
7. Create Layout component
8. Wire Layout into App.jsx routes

### Integration Contracts Consumed
- `stores.contract.md` (uses useThemeStore, useConnectionStore)

### Integration Contracts Provided
- `layout-components.contract.md`

### Testing Requirements
- Component tests for ThemeToggle, StyleSelector
- Integration test for Layout (renders header + footer)

---

## Agent 4: library-agent

**Primary Responsibility:** Document library view, filters, cards, upload modal

### File Ownership

```
frontend/src/
├── views/
│   └── LibraryView.jsx              [CREATE]
├── features/library/
│   ├── FilterBar.jsx                [PORT from src/frontend/filter-bar.js]
│   └── UploadModal.jsx              [PORT from src/frontend/upload-modal.js]
└── components/document/
    ├── DocumentCard.jsx             [PORT from src/frontend/document-card.js]
    ├── DocumentGrid.jsx             [CREATE]
    ├── DocumentBadge.jsx            [CREATE]
    ├── DocumentCardSkeleton.jsx     [CREATE - Wave 3]
    ├── BoundingBoxOverlay.jsx       [PORT Wave 3 from src/frontend/bounding-box-overlay.js]
    └── ChunkHighlighter.jsx         [PORT Wave 3 from src/frontend/chunk-highlighter.js]
```

### Wave 2 Tasks
1. Port DocumentCard component
2. Create DocumentGrid component
3. Create DocumentBadge component
4. Port FilterBar component
5. Port UploadModal component
6. Build LibraryView (compose all components)
7. Integrate WebSocket real-time updates
8. Add upload functionality
9. Add document deletion with optimistic updates

### Wave 3 Tasks (Advanced Features)
1. Port BoundingBoxOverlay
2. Integrate bounding boxes into search results
3. Add DocumentCardSkeleton
4. Write component tests
5. Write integration tests for LibraryView

### Integration Contracts Consumed
- `api-service.contract.md` (uses api.documents.*)
- `stores.contract.md` (uses useDocumentStore)
- `hooks.contract.md` (uses useDocuments, useWebSocket)

### Integration Contracts Provided
- `document-components.contract.md`
- `library-view.contract.md`

### Testing Requirements
- Component tests for DocumentCard, FilterBar, UploadModal
- Integration tests for LibraryView (full flow)

---

## Agent 5: details-agent

**Primary Responsibility:** Document details view, slideshow, audio player, accordion

### File Ownership

```
frontend/src/
├── views/
│   └── DetailsView.jsx              [CREATE]
├── features/details/
│   ├── ContentViewer.jsx            [CREATE]
│   └── TextAccordion.jsx            [CREATE]
├── components/media/
│   ├── Slideshow.jsx                [PORT from src/frontend/slideshow.js]
│   ├── AudioPlayer.jsx              [PORT from src/frontend/audio-player.js]
│   ├── AlbumArt.jsx                 [CREATE]
│   ├── SlideshowSkeleton.jsx        [CREATE - Wave 3]
│   └── AudioPlayerSkeleton.jsx      [CREATE - Wave 3]
└── components/ui/
    └── Accordion.jsx                [PORT from src/frontend/accordion.js]
```

### Wave 2 Tasks
1. Port Slideshow component
2. Port AudioPlayer component
3. Create AlbumArt component
4. Port Accordion component
5. Create ContentViewer (conditional rendering based on file type)
6. Create TextAccordion
7. Build DetailsView (two-column layout)
8. Add clipboard copy functionality
9. Add download functionality
10. Test with PDF, DOCX, PPTX, MP3, WAV files

### Wave 3 Tasks (Advanced Features)
1. Port ChunkHighlighter
2. Integrate chunk highlighting into Accordion
3. Add skeletons (SlideshowSkeleton, AudioPlayerSkeleton)
4. Add keyboard navigation enhancements
5. Write component tests
6. Write integration tests for DetailsView

### Integration Contracts Consumed
- `api-service.contract.md` (uses api.documents.get, api.documents.getMarkdown)
- `hooks.contract.md` (uses useDocumentDetails, useClipboard, useKeyboardNav)

### Integration Contracts Provided
- `media-components.contract.md`
- `details-view.contract.md`

### Testing Requirements
- Component tests for Slideshow, AudioPlayer, Accordion
- Integration tests for DetailsView (navigation, media playback)

---

## Agent 6: research-agent

**Primary Responsibility:** Research view, answer display, reference cards, citations

### File Ownership

```
frontend/src/
├── views/
│   └── ResearchView.jsx             [CREATE]
├── features/research/
│   ├── ResearchPanel.jsx            [CREATE]
│   └── ReferencesPanel.jsx          [CREATE]
└── components/research/
    ├── AnswerDisplay.jsx            [PORT from src/frontend/answer-display.js]
    ├── ReferenceCard.jsx            [PORT from src/frontend/reference-card.js]
    ├── CitationLink.jsx             [CREATE]
    ├── QueryInput.jsx               [CREATE]
    ├── AnswerDisplaySkeleton.jsx    [CREATE - Wave 3]
    └── ReferenceCardSkeleton.jsx    [CREATE - Wave 3]
```

### Wave 2 Tasks
1. Port AnswerDisplay component
2. Port ReferenceCard component
3. Create CitationLink component
4. Create QueryInput component
5. Create ResearchPanel
6. Create ReferencesPanel
7. Build ResearchView (two-panel layout)
8. Implement bidirectional citation highlighting
9. Add view toggle (detailed/simple)
10. Add empty/loading/error states

### Wave 3 Tasks (Advanced Features)
1. Add skeletons (AnswerDisplaySkeleton, ReferenceCardSkeleton)
2. Add copy answer button
3. Write component tests
4. Write integration tests for ResearchView

### Integration Contracts Consumed
- `api-service.contract.md` (uses api.research.ask)
- `hooks.contract.md` (uses useResearch, useClipboard)

### Integration Contracts Provided
- `research-components.contract.md`
- `research-view.contract.md`

### Testing Requirements
- Component tests for AnswerDisplay, ReferenceCard, CitationLink
- Integration tests for ResearchView (query → answer → citations)

---

## Conflict Prevention Strategy

### 1. Territorial Boundaries (No Overlaps)
- Each agent has exclusive write access to their directories
- No shared file modifications
- New files only (no editing others' files)

### 2. Interface-First Development
- All agents read integration contracts before starting
- Mock dependencies during development
- Real integration happens in Wave 4

### 3. Communication via Contracts
- Contracts define all interfaces (props, function signatures, data shapes)
- Changes to contracts require all affected agents' approval
- Contracts are versioned (append changelog to contract file)

### 4. Status Broadcasting
- Each agent publishes status.json every 15 minutes
- Status includes: completed tasks, current task, blockers, deliverables

### 5. Progressive Validation
- Each wave ends with synchronization gate
- All tests must pass before proceeding
- Integration tests verify contracts are honored

---

## Cross-Agent Dependencies

| Consumer Agent | Depends On | Contract |
|---------------|-----------|----------|
| layout-agent | infrastructure-agent | stores.contract.md |
| library-agent | infrastructure-agent | api-service.contract.md, stores.contract.md, hooks.contract.md |
| library-agent | layout-agent | layout-components.contract.md |
| details-agent | infrastructure-agent | api-service.contract.md, hooks.contract.md |
| details-agent | layout-agent | layout-components.contract.md |
| research-agent | infrastructure-agent | api-service.contract.md, hooks.contract.md |
| research-agent | layout-agent | layout-components.contract.md |

**Key Insight:** infrastructure-agent and layout-agent must complete Wave 1 before others can proceed with Wave 2.

---

## Execution Order

```
Wave 0: foundation-agent (SOLO)
├── Deliverable: Project scaffold, routing, dev server
└── Gate: Dev server runs, routes work

Wave 1: foundation-agent + infrastructure-agent + layout-agent (PARALLEL)
├── foundation-agent: Utilities, constants, error boundary
├── infrastructure-agent: API, stores, hooks
├── layout-agent: Layout shell, theme/style components
└── Gate: Layout renders, stores accessible, API callable

Wave 2: library-agent + details-agent + research-agent (PARALLEL)
├── library-agent: LibraryView complete
├── details-agent: DetailsView complete
├── research-agent: ResearchView complete
└── Gate: All 3 views functional, navigation works

Wave 3: library-agent + details-agent + research-agent (PARALLEL)
├── library-agent: Advanced features, tests
├── details-agent: Advanced features, tests
├── research-agent: Advanced features, tests
└── Gate: All tests pass, coverage >80%

Wave 4: ALL agents (PARALLEL)
├── Cross-agent integration testing
├── E2E test suite
├── Production build
└── Gate: Production-ready
```

---

## Success Criteria

Each agent is successful when:
- ✅ All assigned files created/ported
- ✅ All integration contracts honored
- ✅ All unit tests passing
- ✅ All integration tests passing
- ✅ No console errors in their territory
- ✅ Lighthouse accessibility score 100 for their components
- ✅ Documentation complete (JSDoc annotations)

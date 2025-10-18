# React Migration Orchestration Plan

**Feature Goal:** Migrate 3-page vanilla JS frontend to React + Vite SPA
**Max Agents:** 6 parallel agents
**Strategy:** Territorial ownership + Interface-first development
**Timeline:** 4 waves with synchronization gates

---

## Executive Summary

**Current State:**
- 3 standalone HTML pages (index.html, details.html, research.html)
- Vanilla JS ES6 modules (~6,700 LOC)
- No build tooling, no routing
- Well-architected components with event-driven patterns

**Target State:**
- Single-page React 18 application
- Vite 5 build tooling with HMR
- React Router 6 for navigation
- Zustand for global state, React Query for server state
- Zero changes to Python backend

**Success Criteria:**
- ✅ All 3 views functional (library, details, research)
- ✅ Feature parity with current vanilla JS app
- ✅ WebSocket real-time updates working
- ✅ Upload, search, filter, details, research all functional
- ✅ Lighthouse accessibility score 100
- ✅ No regression in WCAG 2.1 AA compliance

---

## Territorial Ownership Map

| Agent | Territory (Files) | Responsibility |
|-------|------------------|----------------|
| **foundation-agent** | `frontend/vite.config.js`, `frontend/package.json`, `frontend/src/main.jsx`, `frontend/src/App.jsx` | Project scaffolding, build config, routing setup |
| **infrastructure-agent** | `frontend/src/services/`, `frontend/src/stores/`, `frontend/src/hooks/useWebSocket.js` | API clients, state management, WebSocket integration |
| **layout-agent** | `frontend/src/components/layout/`, `frontend/src/components/common/Theme*.jsx`, `frontend/src/components/common/StyleSelector.jsx`, `frontend/src/components/common/ConnectionStatus.jsx` | Header, Footer, Layout, theme/style components |
| **library-agent** | `frontend/src/views/LibraryView.jsx`, `frontend/src/features/library/`, `frontend/src/components/document/` | Document library view, filters, cards, upload |
| **details-agent** | `frontend/src/views/DetailsView.jsx`, `frontend/src/features/details/`, `frontend/src/components/media/`, `frontend/src/components/ui/Accordion.jsx` | Document details view, slideshow, audio player, accordion |
| **research-agent** | `frontend/src/views/ResearchView.jsx`, `frontend/src/features/research/`, `frontend/src/components/research/` | Research view, answer display, reference cards, citations |

**Conflict Prevention:**
- No shared file modifications (each agent creates new files)
- Integration via contract specifications (no direct imports until integration wave)
- Mock/stub interfaces during development
- Final integration in Wave 4

---

## Wave Execution Plan

### Wave 0: Prerequisites & Foundation (Solo: foundation-agent)

**Duration:** 2-3 hours
**Parallelism:** 1 agent
**Goal:** Create project structure, verify build system works

#### Agent: foundation-agent

**Tasks:**
1. Initialize Vite + React project in `frontend/` directory
2. Install core dependencies (react-router-dom, react-query, zustand)
3. Configure Vite proxy to Python backend (:8002, :8000)
4. Copy existing CSS assets (`styles.css`, themes) to `frontend/src/styles/`
5. Set up React Router with 3 routes (/, /details/:id, /research)
6. Create placeholder view components (LibraryView, DetailsView, ResearchView)
7. Verify dev server runs and API proxy works

**Deliverables:**
- ✅ `frontend/package.json` with all dependencies
- ✅ `frontend/vite.config.js` with proxy configuration
- ✅ `frontend/src/main.jsx` with React + Router setup
- ✅ `frontend/src/App.jsx` with route definitions
- ✅ `frontend/src/views/LibraryView.jsx` (placeholder)
- ✅ `frontend/src/views/DetailsView.jsx` (placeholder)
- ✅ `frontend/src/views/ResearchView.jsx` (placeholder)
- ✅ `frontend/src/styles/` directory with all CSS

**Validation Gate:**
- [ ] `npm run dev` starts server on :3000
- [ ] Navigate to all 3 routes successfully
- [ ] API call to `/api/documents` returns data
- [ ] CSS themes load correctly

---

### Wave 1: Infrastructure & Layout (Parallel: 3 agents)

**Duration:** 1 day
**Parallelism:** 3 agents (infrastructure-agent, layout-agent, foundation-agent)
**Goal:** Cross-cutting concerns needed by all views

#### Agent: infrastructure-agent

**Territory:** `frontend/src/services/`, `frontend/src/stores/`, `frontend/src/hooks/`

**Tasks:**
1. Port API client → `services/api.js` (copy from `src/frontend/api-client.js`)
2. Port WebSocket client → `services/websocket.js` + `hooks/useWebSocket.js`
3. Create connection store → `stores/useConnectionStore.js` (Zustand)
4. Create theme store → `stores/useThemeStore.js` (Zustand with persist)
5. Create documents store → `stores/useDocumentStore.js` (filters state)
6. Create `hooks/useDocuments.js` (React Query wrapper)
7. Create `hooks/useDocumentDetails.js` (React Query wrapper)
8. Create `hooks/useResearch.js` (React Query wrapper)

**Deliverables:**
- ✅ `services/api.js` - REST API client
- ✅ `services/websocket.js` - WebSocket connection manager
- ✅ `services/research.js` - Research API client
- ✅ `hooks/useWebSocket.js` - React hook for WebSocket
- ✅ `hooks/useDocuments.js` - Documents query hook
- ✅ `hooks/useDocumentDetails.js` - Document details query hook
- ✅ `hooks/useResearch.js` - Research mutation hook
- ✅ `stores/useConnectionStore.js` - Connection status
- ✅ `stores/useThemeStore.js` - Theme/style preferences
- ✅ `stores/useDocumentStore.js` - Filter state

**Integration Contracts:**
- See `integration-contracts/api-service.contract.md`
- See `integration-contracts/stores.contract.md`
- See `integration-contracts/hooks.contract.md`

**Validation:**
- [ ] All stores expose documented API
- [ ] All hooks accept documented props
- [ ] API service functions match contract signatures
- [ ] Unit tests for stores pass

---

#### Agent: layout-agent

**Territory:** `frontend/src/components/layout/`, `frontend/src/components/common/`

**Tasks:**
1. Port ThemeToggle → `components/common/ThemeToggle.jsx`
2. Port StyleSelector → `components/common/StyleSelector.jsx`
3. Create ConnectionStatus → `components/common/ConnectionStatus.jsx`
4. Create LoadingSpinner → `components/common/LoadingSpinner.jsx`
5. Create Header → `components/layout/Header.jsx`
6. Create Footer → `components/layout/Footer.jsx`
7. Create Layout → `components/layout/Layout.jsx`
8. Wire Layout into App.jsx routes

**Deliverables:**
- ✅ `components/common/ThemeToggle.jsx`
- ✅ `components/common/StyleSelector.jsx`
- ✅ `components/common/ConnectionStatus.jsx`
- ✅ `components/common/LoadingSpinner.jsx`
- ✅ `components/layout/Header.jsx`
- ✅ `components/layout/Footer.jsx`
- ✅ `components/layout/Layout.jsx`

**Integration Contracts:**
- See `integration-contracts/layout-components.contract.md`

**Validation:**
- [ ] Theme toggle switches between light/dark
- [ ] Style selector loads different themes
- [ ] Connection status reflects WebSocket state
- [ ] Header shows correct title per route
- [ ] Footer renders on all pages

---

#### Agent: foundation-agent (continues)

**Territory:** `frontend/src/utils/`, `frontend/src/constants/`

**Tasks:**
1. Copy utility modules → `utils/clipboard.js`, `utils/download.js`, `utils/formatting.js`, `utils/url.js`
2. Copy assets → `utils/assets.js` (default album art SVG)
3. Create constants → `constants/config.js`, `constants/routes.js`
4. Create error boundary → `components/ErrorBoundary.jsx`
5. Add React Query provider to App.jsx
6. Add error boundaries to route components

**Deliverables:**
- ✅ `utils/clipboard.js`
- ✅ `utils/download.js`
- ✅ `utils/formatting.js`
- ✅ `utils/url.js`
- ✅ `utils/assets.js`
- ✅ `constants/config.js`
- ✅ `constants/routes.js`
- ✅ `components/ErrorBoundary.jsx`

**Validation:**
- [ ] Utility functions work in isolation
- [ ] Error boundary catches component errors
- [ ] React Query provider wraps app

---

**Wave 1 Synchronization Gate:**
- [ ] All 3 agents complete their deliverables
- [ ] Layout component renders with Header + Footer
- [ ] Theme toggle and style selector work
- [ ] Connection status shows "disconnected" (no WebSocket yet)
- [ ] All stores accessible via hooks
- [ ] API service can be imported
- [ ] No TypeScript/ESLint errors
- [ ] Dev server runs without errors

---

### Wave 2: Feature Views (Parallel: 3 agents)

**Duration:** 2 days
**Parallelism:** 3 agents (library-agent, details-agent, research-agent)
**Goal:** Implement all 3 main views with feature parity

#### Agent: library-agent

**Territory:** `frontend/src/views/LibraryView.jsx`, `frontend/src/features/library/`, `frontend/src/components/document/`

**Tasks:**
1. Port DocumentCard → `components/document/DocumentCard.jsx`
2. Create DocumentGrid → `components/document/DocumentGrid.jsx`
3. Create DocumentBadge → `components/document/DocumentBadge.jsx`
4. Port FilterBar → `features/library/FilterBar.jsx`
5. Port UploadModal → `features/library/UploadModal.jsx`
6. Build LibraryView (compose all components)
7. Integrate WebSocket real-time updates
8. Add upload functionality
9. Add document deletion (with optimistic updates)

**Deliverables:**
- ✅ `components/document/DocumentCard.jsx` (document + audio variants)
- ✅ `components/document/DocumentGrid.jsx`
- ✅ `components/document/DocumentBadge.jsx`
- ✅ `features/library/FilterBar.jsx`
- ✅ `features/library/UploadModal.jsx`
- ✅ `views/LibraryView.jsx` (complete)

**Integration Contracts:**
- See `integration-contracts/document-components.contract.md`
- See `integration-contracts/library-view.contract.md`

**Validation:**
- [ ] Document cards render with correct data
- [ ] Filter bar filters documents
- [ ] Upload modal accepts files and uploads
- [ ] Real-time updates show new documents
- [ ] Deletion removes cards optimistically
- [ ] Pagination works
- [ ] Search debounces correctly

---

#### Agent: details-agent

**Territory:** `frontend/src/views/DetailsView.jsx`, `frontend/src/features/details/`, `frontend/src/components/media/`, `frontend/src/components/ui/Accordion.jsx`

**Tasks:**
1. Port Slideshow → `components/media/Slideshow.jsx`
2. Port AudioPlayer → `components/media/AudioPlayer.jsx`
3. Create AlbumArt → `components/media/AlbumArt.jsx`
4. Port Accordion → `components/ui/Accordion.jsx`
5. Create ContentViewer → `features/details/ContentViewer.jsx` (conditional rendering)
6. Create TextAccordion → `features/details/TextAccordion.jsx`
7. Build DetailsView (two-column layout)
8. Add clipboard copy functionality
9. Add download functionality
10. Test with PDF, DOCX, PPTX, MP3, WAV files

**Deliverables:**
- ✅ `components/media/Slideshow.jsx`
- ✅ `components/media/AudioPlayer.jsx`
- ✅ `components/media/AlbumArt.jsx`
- ✅ `components/ui/Accordion.jsx`
- ✅ `features/details/ContentViewer.jsx`
- ✅ `features/details/TextAccordion.jsx`
- ✅ `views/DetailsView.jsx` (complete)

**Integration Contracts:**
- See `integration-contracts/media-components.contract.md`
- See `integration-contracts/details-view.contract.md`

**Validation:**
- [ ] Slideshow navigates pages with keyboard
- [ ] Audio player plays with VTT captions
- [ ] Album art displays with fallback
- [ ] Accordion expands/collapses sections
- [ ] Markdown renders correctly
- [ ] Copy to clipboard works
- [ ] Download document works
- [ ] Navigation from library → details works

---

#### Agent: research-agent

**Territory:** `frontend/src/views/ResearchView.jsx`, `frontend/src/features/research/`, `frontend/src/components/research/`

**Tasks:**
1. Port AnswerDisplay → `components/research/AnswerDisplay.jsx`
2. Port ReferenceCard → `components/research/ReferenceCard.jsx`
3. Create CitationLink → `components/research/CitationLink.jsx`
4. Create QueryInput → `components/research/QueryInput.jsx`
5. Create ResearchPanel → `features/research/ResearchPanel.jsx`
6. Create ReferencesPanel → `features/research/ReferencesPanel.jsx`
7. Build ResearchView (two-panel layout)
8. Implement bidirectional citation highlighting
9. Add view toggle (detailed/simple)
10. Add empty/loading/error states

**Deliverables:**
- ✅ `components/research/AnswerDisplay.jsx`
- ✅ `components/research/ReferenceCard.jsx`
- ✅ `components/research/CitationLink.jsx`
- ✅ `components/research/QueryInput.jsx`
- ✅ `features/research/ResearchPanel.jsx`
- ✅ `features/research/ReferencesPanel.jsx`
- ✅ `views/ResearchView.jsx` (complete)

**Integration Contracts:**
- See `integration-contracts/research-components.contract.md`
- See `integration-contracts/research-view.contract.md`

**Validation:**
- [ ] Query submission triggers research API
- [ ] Answer displays with markdown rendering
- [ ] Citations are clickable and highlight references
- [ ] Reference cards show document metadata
- [ ] Bidirectional highlighting works (answer ↔ references)
- [ ] View toggle switches between detailed/simple
- [ ] Loading state shows during query
- [ ] Error state shows on API failure

---

**Wave 2 Synchronization Gate:**
- [ ] All 3 agents complete their deliverables
- [ ] LibraryView fully functional (browse, search, filter, upload)
- [ ] DetailsView fully functional (view document, navigate pages, play audio)
- [ ] ResearchView fully functional (ask questions, see answers, click citations)
- [ ] Navigation between all 3 views works
- [ ] Real-time updates working in library
- [ ] No console errors
- [ ] Accessibility audit passes (Lighthouse)

---

### Wave 3: Advanced Features & Quality (Parallel: 3 agents)

**Duration:** 1-2 days
**Parallelism:** 3 agents (library-agent, details-agent, research-agent)
**Goal:** Add advanced features, optimize performance, expand test coverage

#### Agent: library-agent (continues)

**Territory:** `frontend/src/features/library/`, `frontend/src/components/document/`

**Tasks:**
1. Port BoundingBoxOverlay → `components/document/BoundingBoxOverlay.jsx`
2. Integrate bounding boxes into Slideshow for search highlighting
3. Add loading skeletons for DocumentCard
4. Add infinite scroll pagination (optional)
5. Add bulk document operations (optional)
6. Write component tests for DocumentCard, FilterBar, UploadModal
7. Write integration tests for LibraryView

**Deliverables:**
- ✅ `components/document/BoundingBoxOverlay.jsx`
- ✅ `components/document/DocumentCardSkeleton.jsx`
- ✅ Component tests (FilterBar, DocumentCard, UploadModal)
- ✅ Integration tests (LibraryView)

**Validation:**
- [ ] Bounding boxes render on search results
- [ ] Skeletons show during loading
- [ ] Component tests pass (coverage >80%)
- [ ] Integration tests pass

---

#### Agent: details-agent (continues)

**Territory:** `frontend/src/features/details/`, `frontend/src/components/media/`, `frontend/src/components/ui/`

**Tasks:**
1. Port ChunkHighlighter → `components/document/ChunkHighlighter.jsx`
2. Integrate chunk highlighting into Accordion
3. Add loading skeletons for Slideshow, AudioPlayer
4. Add keyboard navigation enhancements (useKeyboardNav hook)
5. Add ARIA enhancements (useAriaAnnounce hook)
6. Write component tests for Slideshow, AudioPlayer, Accordion
7. Write integration tests for DetailsView

**Deliverables:**
- ✅ `components/document/ChunkHighlighter.jsx`
- ✅ `components/media/SlideshowSkeleton.jsx`
- ✅ `hooks/useKeyboardNav.js`
- ✅ `hooks/useAriaAnnounce.js`
- ✅ Component tests (Slideshow, AudioPlayer, Accordion)
- ✅ Integration tests (DetailsView)

**Validation:**
- [ ] Chunk highlighting works in accordion
- [ ] Keyboard navigation fully functional
- [ ] Screen reader announcements work
- [ ] Component tests pass (coverage >80%)
- [ ] Integration tests pass

---

#### Agent: research-agent (continues)

**Territory:** `frontend/src/features/research/`, `frontend/src/components/research/`

**Tasks:**
1. Add loading skeletons for AnswerDisplay, ReferenceCard
2. Add copy answer button
3. Add export citations button (optional)
4. Add query history (optional)
5. Add model selector (if multiple LLM providers)
6. Write component tests for AnswerDisplay, ReferenceCard, CitationLink
7. Write integration tests for ResearchView

**Deliverables:**
- ✅ `components/research/AnswerDisplaySkeleton.jsx`
- ✅ `components/research/ReferenceCardSkeleton.jsx`
- ✅ Component tests (AnswerDisplay, ReferenceCard, CitationLink)
- ✅ Integration tests (ResearchView)

**Validation:**
- [ ] Skeletons show during loading
- [ ] Copy answer works
- [ ] Component tests pass (coverage >80%)
- [ ] Integration tests pass

---

**Wave 3 Synchronization Gate:**
- [ ] All advanced features implemented
- [ ] All component tests passing
- [ ] All integration tests passing
- [ ] Test coverage >80%
- [ ] Lighthouse accessibility score 100
- [ ] No console warnings or errors
- [ ] Performance optimized (lazy loading, code splitting)

---

### Wave 4: Integration, Testing & Deployment (All agents)

**Duration:** 1 day
**Parallelism:** All 6 agents
**Goal:** Final integration, E2E testing, production readiness

#### All Agents: Cross-Integration Testing

**Tasks:**
1. **foundation-agent**: Build production bundle, optimize chunks, create deployment scripts
2. **infrastructure-agent**: E2E test API integration, WebSocket reconnection, error handling
3. **layout-agent**: E2E test navigation, theme persistence, connection status
4. **library-agent**: E2E test upload → process → view flow
5. **details-agent**: E2E test library → details navigation, media playback
6. **research-agent**: E2E test research query → answer → citation → details navigation

**Deliverables:**
- ✅ Production build configuration
- ✅ E2E test suite (Playwright or Cypress)
- ✅ Deployment scripts (integrate with `scripts/start-all.sh`)
- ✅ Updated documentation (README, architecture docs)
- ✅ Migration guide for contributors
- ✅ Lighthouse audit report (all scores >90)

**Final Validation Gate:**
- [ ] Production build succeeds
- [ ] All E2E tests pass
- [ ] Lighthouse: Performance >90, Accessibility 100, Best Practices >90
- [ ] Manual QA: All features work in production build
- [ ] Documentation complete
- [ ] Legacy frontend archived

---

## Success Metrics

### Functional Metrics
- ✅ All 3 views fully functional
- ✅ Feature parity with vanilla JS app
- ✅ Real-time updates working
- ✅ Upload, search, filter, details, research operational

### Quality Metrics
- ✅ Test coverage >80%
- ✅ Lighthouse accessibility score 100
- ✅ Lighthouse performance >90
- ✅ Zero console errors in production
- ✅ WCAG 2.1 AA compliance maintained

### Performance Metrics
- ✅ First Contentful Paint <1s
- ✅ Time to Interactive <2s
- ✅ Bundle size <500KB (gzipped)
- ✅ Lighthouse performance >90

---

## Risk Management

| Risk | Mitigation | Owner |
|------|-----------|-------|
| **WebSocket reconnection issues** | Implement exponential backoff, test edge cases | infrastructure-agent |
| **Bundle size bloat** | Code splitting, lazy loading, tree-shaking | foundation-agent |
| **Accessibility regression** | eslint-plugin-jsx-a11y, automated testing | All agents |
| **Integration conflicts** | Interface-first development, progressive testing | All agents |
| **Theme flicker on load** | SSR theme detection, inline critical CSS | layout-agent |
| **API proxy issues in production** | Absolute URLs in production build | foundation-agent |

---

## Communication Protocol

### Status Broadcasting
Each agent publishes status to `.context-kit/orchestration/react-migration/status/{agent-name}.json`:

```json
{
  "agent": "library-agent",
  "wave": 2,
  "status": "in_progress",
  "completed_tasks": 7,
  "total_tasks": 9,
  "deliverables": [
    {"file": "components/document/DocumentCard.jsx", "status": "complete"},
    {"file": "components/document/DocumentGrid.jsx", "status": "complete"},
    {"file": "features/library/FilterBar.jsx", "status": "in_progress"}
  ],
  "blockers": [],
  "updated_at": "2025-10-18T10:30:00Z"
}
```

### Contract Compliance
All agents validate against contracts before marking deliverables complete:
1. Check function signatures match contract
2. Verify prop types match specifications
3. Run contract validation tests
4. Update integration contract with actual implementation notes

### Integration Testing
Each agent runs integration tests after completing deliverables:
1. Unit tests for their components
2. Integration tests for their view
3. Contract compliance tests
4. Cross-agent smoke tests (if dependencies exist)

---

## Execution Command

```bash
# Wave 0: Foundation (solo)
claude-code --agent=foundation-agent --task="Wave 0 Foundation" --spec=".context-kit/orchestration/react-migration/integration-contracts/foundation.contract.md"

# Wave 1: Infrastructure & Layout (parallel)
claude-code --parallel \
  --agent=infrastructure-agent --task="Wave 1 Infrastructure" \
  --agent=layout-agent --task="Wave 1 Layout" \
  --agent=foundation-agent --task="Wave 1 Utilities"

# Wave 2: Feature Views (parallel)
claude-code --parallel \
  --agent=library-agent --task="Wave 2 Library View" \
  --agent=details-agent --task="Wave 2 Details View" \
  --agent=research-agent --task="Wave 2 Research View"

# Wave 3: Advanced Features (parallel)
claude-code --parallel \
  --agent=library-agent --task="Wave 3 Library Advanced" \
  --agent=details-agent --task="Wave 3 Details Advanced" \
  --agent=research-agent --task="Wave 3 Research Advanced"

# Wave 4: Integration & Deployment (all agents)
claude-code --parallel \
  --all-agents --task="Wave 4 Final Integration"
```

---

## Next Steps

1. ✅ Generate all integration contracts (see `integration-contracts/` directory)
2. ✅ Create agent assignment specifications
3. ✅ Set up validation strategy
4. ✅ Document coordination protocol
5. 🚀 Begin Wave 0 execution

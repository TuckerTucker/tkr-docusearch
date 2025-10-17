# Research Page Implementation Plan

**Created:** 2025-10-17
**Status:** Planning
**Priority:** New Feature
**Complexity:** Medium-High

---

## Goal

Build a research page that displays AI-generated answers with inline citations linked to source documents via interactive reference cards.

---

## Design Requirements

### Layout
- **Two-panel split view:**
  - Left: Answer panel with AI-generated text and inline citations
  - Right: References panel showing source documents
- **View modes:**
  - Detailed: Shows document thumbnails (64px max-height), file type, filename, Details button
  - Simple: Compact list with numbered references and filenames

### Interactions
- **Bidirectional highlighting:**
  - Hover on citation marker `[1]` → Highlights corresponding reference card
  - Hover on reference card → Highlights sentence(s) containing that citation
- **Navigation:**
  - Details button → Links to existing `/details.html?filename={filename}`

### Styling
- Kraft Paper theme consistency
- Responsive layout (stack panels on mobile)
- Accessibility: WCAG 2.1 AA compliance

---

## Reference Materials

### Mockups
- `/Volumes/tkr-riffic/@tkr-projects/tkr-docusearch/.context-kit/_ref/research page/detailed_references_and_answer.svg`
- `/Volumes/tkr-riffic/@tkr-projects/tkr-docusearch/.context-kit/_ref/research page/simple_references.svg`
- `/Volumes/tkr-riffic/@tkr-projects/tkr-docusearch/.context-kit/_ref/research page/references_highlighting.md`

### Existing Components to Leverage
- `src/frontend/document-card.js` - Thumbnail system and file type handling
- `src/frontend/details.html` - Target for Details button navigation
- `src/frontend/assets.js` - SVG assets and theme tokens

---

## Technical Decisions

### Thumbnail Strategy
**Decision:** Reuse existing thumbnail infrastructure with `max-height: 64px`

**Rationale:**
- Cover art (audio): Square images become 64×64px
- Documents: Portrait images use full 64px height with proportional width (~45-50px)
- No new thumbnail generation needed
- Consistent with existing lazy loading and error handling

**Implementation:**
```css
.reference-card__thumbnail {
  max-height: 64px;
  width: auto;
  object-fit: contain;
}
```

### Component Architecture
- **New:** `reference-card.js` - Lightweight component for reference display
- **Reuse:** Thumbnail loading logic from `document-card.js`
- **Reuse:** File type detection and icons from `document-card.js`

---

## Ordered Task List

### 1. Explore existing frontend structure
**Purpose:** Identify integration points and avoid rework

- Map current HTML pages and routing patterns
- Review JavaScript module organization (`src/frontend/*.js`)
- Identify CSS theme tokens and reusable styles
- Document available API endpoints (or plan new ones)

**Outputs:**
- Architecture notes
- List of reusable components/utilities
- API contract definition (if new endpoint needed)

---

### 2. Create reference card component (`reference-card.js`)
**Purpose:** Core building block for references panel

**Features:**
- Number badge (1, 2, 3...)
- Thumbnail display (max-height: 64px)
- File type indicator (MP3, PDF, etc.)
- Filename with ellipsis handling
- Details button linking to `/details.html?filename=X`

**Variants:**
- `detailed` - Shows thumbnail, file type, full metadata
- `simple` - Minimal list item with number and filename

**Dependencies:**
- Reuse thumbnail loading from `document-card.js`
- Reuse file type icons/detection

---

### 3. Style reference card component
**Purpose:** Match Kraft Paper theme and mockup design

- Apply theme tokens (colors, typography, spacing)
- Implement hover states
- Add highlight state styling (`.reference-card--highlighted`)
- Ensure 64px thumbnail constraint works for both variants
- Test with real thumbnails (documents and cover art)

---

### 4. Build answer display component
**Purpose:** Render AI answer with clickable citations

**Features:**
- Container for answer text
- Markdown/rich text rendering
- Inline citation markers: `[1]`, `[2]`, etc.
- Citation-to-reference mapping data structure

**Data Model:**
```javascript
{
  answerText: "Lorem ipsum [1] dolor sit [2][3] amet...",
  citations: [
    { id: 1, filename: "doc1.pdf", spans: [[12, 45]] }, // char ranges
    { id: 2, filename: "doc2.pdf", spans: [[50, 80], [120, 150]] }
  ]
}
```

**Styling:**
- Citation markers styled as inline badges
- Kraft Paper theme applied
- Readable typography

---

### 5. Implement bidirectional highlighting logic
**Purpose:** Core interaction feature

**Interactions:**
1. **Hover on citation → Highlight reference(s)**
   - Add `.reference-card--highlighted` class to matching cards
   - Support multiple references for one citation

2. **Hover on reference → Highlight sentence(s)**
   - Add `.citation--highlighted` class to matching citation markers
   - Optionally highlight containing sentence/paragraph

**Implementation:**
- Event delegation on answer container and references container
- Use data attributes: `data-citation-id="1"` for mapping
- CSS transitions for smooth highlighting

**Performance:**
- Throttle/debounce if needed
- Use event delegation to minimize listeners

---

### 6. Create research page layout (`research.html`)
**Purpose:** Page shell and responsive structure

**Structure:**
```html
<body>
  <header class="research-header">
    <!-- User icon, search input, Ask button -->
  </header>

  <main class="research-main">
    <section class="answer-panel">
      <!-- Answer text with citations -->
    </section>

    <aside class="references-panel">
      <div class="references-header">
        <button class="view-toggle" data-view="detailed">Detailed</button>
        <button class="view-toggle" data-view="simple">Simple</button>
      </div>
      <div class="references-list">
        <!-- Reference cards -->
      </div>
    </aside>
  </main>
</body>
```

**Responsive:**
- Desktop: Side-by-side panels (600px each)
- Mobile: Stacked vertically

---

### 7. Build query input interface
**Purpose:** User entry point for asking questions

**Features:**
- Text input with placeholder: "Ask a question about your documents..."
- "Ask" button (styled per theme)
- Loading state (disable input, show spinner)
- Clear button to reset

**Form handling:**
- Prevent default form submission
- Validate non-empty query
- Trigger API call on submit

---

### 8. Integrate API for answer generation
**Purpose:** Connect frontend to AI backend

**API Contract (to define/verify):**
```
POST /api/research/ask
Body: { query: "What is X?" }

Response: {
  answer: "Lorem ipsum [1] dolor [2]...",
  references: [
    {
      id: 1,
      filename: "doc1.pdf",
      thumbnailUrl: "/data/images/doc1_page_001_thumb.jpg",
      dateAdded: "2025-10-15",
      extension: "pdf"
    }
  ]
}
```

**Implementation:**
- `fetch()` to API endpoint
- Parse response and render answer + references
- Error handling (network, 500, timeout)
- Loading state management

---

### 9. Add empty and error states
**Purpose:** Handle all UI states gracefully

**States:**
1. **Initial/Empty:** No query submitted yet
   - Show welcome message
   - Prompt to ask a question

2. **Loading:** Query submitted, waiting for response
   - Show spinner/skeleton
   - Disable input

3. **Success:** Answer received
   - Display answer + references

4. **Error:** API failure
   - Show error message
   - Allow retry

5. **No Results:** Query succeeded but no documents found
   - Friendly message
   - Suggest broader query

---

### 10. Implement accessibility features
**Purpose:** WCAG 2.1 AA compliance

**Requirements:**
- ARIA labels on citation markers: `aria-label="Citation 1: Reference to doc1.pdf"`
- ARIA labels on reference cards: `aria-label="Reference 1: doc1.pdf, Added October 15, 2025"`
- Keyboard navigation:
  - Tab through citations and reference cards
  - Enter/Space to activate Details button
  - Escape to clear highlighting
- Focus indicators (visible outline)
- Screen reader announcements for state changes

**Testing:**
- Test with keyboard only
- Test with screen reader (VoiceOver, NVDA)
- Verify highlight interactions are accessible

---

### 11. Add mobile responsive behavior
**Purpose:** Ensure usability on all screen sizes

**Breakpoints:**
- Desktop (>768px): Side-by-side panels
- Tablet (480-768px): Stacked with reduced spacing
- Mobile (<480px): Fully stacked, adjusted typography

**Mobile considerations:**
- 64px thumbnails still work well
- Touch targets ≥44px for buttons
- Test highlighting on touch (may need tap instead of hover)
- Adjust font sizes for readability

---

### 12. Polish interactions and animations
**Purpose:** Enhance user experience

**Enhancements:**
- Smooth transitions for highlight states (150-200ms)
- Detailed/Simple toggle animation (fade/slide)
- Button hover/active states with micro-animations
- Loading skeleton for better perceived performance
- Subtle animations for answer reveal

**Consistency:**
- Match existing app animations (check document-card.js)
- Use CSS transitions, not JavaScript-based animations
- Respect `prefers-reduced-motion`

---

### 13. Cross-browser testing and bug fixes
**Purpose:** Ensure consistent experience

**Browsers to test:**
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

**Test cases:**
- Citation highlighting works in all browsers
- Thumbnails render correctly (aspect ratios preserved)
- Responsive breakpoints trigger properly
- Keyboard navigation works
- No layout shifts or flashing

**Known edge cases to test:**
- Very long filenames
- Documents without thumbnails
- Queries with no results
- Multiple citations in same sentence
- Mobile touch vs desktop hover

---

## Dependencies & Blockers

### Hard Dependencies
- Task 2 (reference card) must complete before Task 5 (highlighting)
- Task 4 (answer display) must complete before Task 5 (highlighting)
- Task 6 (page layout) needs Tasks 2 and 4
- Task 8 (API integration) needs Task 6

### Potential Blockers
- **API endpoint:** If it doesn't exist, need to create or mock it (identify in Task 1)
- **Citation parsing:** Need clear format from AI backend (define in Task 1)
- **Thumbnail availability:** Confirm all documents have thumbnails generated

---

## Success Criteria

### Functional
- [ ] User can submit a research query
- [ ] Answer displays with inline citation markers
- [ ] References panel shows source documents
- [ ] Hovering citation highlights reference(s)
- [ ] Hovering reference highlights citation(s)
- [ ] Details button navigates to existing details page
- [ ] Detailed/Simple view toggle works
- [ ] Mobile responsive layout functions

### Non-Functional
- [ ] Page loads in <2s on standard connection
- [ ] Highlighting responds in <100ms
- [ ] WCAG 2.1 AA accessibility validated
- [ ] Works in Chrome, Firefox, Safari, Edge
- [ ] No console errors or warnings

---

## Risk Mitigation

### Early Tasks (1, 8)
- Task 1 identifies unknowns before deep implementation
- Task 8 validates API contract mid-stream (can adjust earlier work if needed)

### Incremental Polish (10-13)
- Core functionality (Tasks 2-7) prioritized
- Polish tasks can be done incrementally or deferred

### Fallbacks
- If API not ready: Mock data for frontend development
- If highlighting too complex: Start with one-way (citation → reference)
- If mobile breaks: Desktop-only MVP, iterate on responsive

---

## Notes

### Known Issues from References
- Typo in `references_highlighting.md:1` - "attribution bug" should be "reference badge" or "citation marker"

### Future Enhancements (Out of Scope)
- Multi-page citations (e.g., "See pages 3-5 of doc1.pdf")
- Inline preview popover on citation hover
- Export answer as PDF with citations
- Share research results via URL
- History of past queries

---

## Appendix: Data Structures

### Reference Card Props
```javascript
{
  id: 1,                          // Citation number
  filename: "document.pdf",       // Full filename
  thumbnailUrl: "/path/to/thumb", // Existing thumbnail
  extension: "pdf",               // File type
  dateAdded: "2025-10-15",       // Upload date
  variant: "detailed" | "simple"  // Display mode
}
```

### Answer Data
```javascript
{
  text: "Lorem [1] ipsum [2][3]...",
  citations: [
    {
      id: 1,
      filename: "doc1.pdf",
      positions: [
        { start: 6, end: 9 }  // Character indices for "[1]"
      ]
    }
  ]
}
```

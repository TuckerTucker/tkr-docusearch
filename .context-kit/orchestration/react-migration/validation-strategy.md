# Validation Strategy & Quality Gates

**Goal:** Ensure each wave delivers working, tested, production-quality code
**Approach:** Progressive validation with automated gates

---

## Validation Layers

### Layer 1: Contract Compliance (Automated)
**When:** After each agent completes a deliverable
**What:** Validate that implementations match integration contracts
**How:** Contract validation tests + TypeScript type checking (if enabled)

### Layer 2: Unit Testing (Automated)
**When:** During development (continuous)
**What:** Test individual components and functions in isolation
**How:** Vitest + React Testing Library

### Layer 3: Integration Testing (Automated)
**When:** After Wave 2, Wave 3
**What:** Test component interactions and data flow
**How:** React Testing Library + Mock Service Worker (MSW)

### Layer 4: E2E Testing (Automated)
**When:** Wave 4 only
**What:** Test full user workflows across views
**How:** Playwright or Cypress

### Layer 5: Manual QA (Manual)
**When:** After each wave
**What:** Visual inspection, exploratory testing
**How:** Human tester with test matrix

---

## Wave 0 Validation Gate

**Goal:** Verify project scaffolding is correct

### Automated Checks
- [ ] `npm install` succeeds (all dependencies resolve)
- [ ] `npm run dev` starts dev server on port 3000
- [ ] Navigate to http://localhost:3000 - app renders
- [ ] Navigate to all 3 routes (/, /details/test, /research) - placeholder views render
- [ ] API proxy works: `fetch('/api/documents')` returns data from :8002
- [ ] No console errors on page load
- [ ] ESLint passes: `npm run lint`

### Manual Checks
- [ ] CSS themes load correctly (kraft-paper by default)
- [ ] Dev server HMR (Hot Module Replacement) works - edit file, see instant update
- [ ] Browser DevTools show React component tree

### Deliverables Verified
- ✅ `package.json` with all required dependencies
- ✅ `vite.config.js` with proxy configuration
- ✅ `src/main.jsx` renders React app
- ✅ `src/App.jsx` defines routes
- ✅ Placeholder views (LibraryView, DetailsView, ResearchView) render

### Exit Criteria
**ALL automated checks must pass before Wave 1 begins.**

---

## Wave 1 Validation Gate

**Goal:** Verify infrastructure and layout are functional

### Contract Compliance Tests

#### API Service Contract
```javascript
// tests/contracts/api-service.test.js
import { api } from '@services/api';

describe('API Service Contract', () => {
  test('api.documents.list() returns correct shape', async () => {
    const data = await api.documents.list({ limit: 10 });
    expect(data).toHaveProperty('documents');
    expect(data).toHaveProperty('total');
    expect(data.documents).toBeInstanceOf(Array);
  });

  test('api.documents.get(id) returns correct shape', async () => {
    const doc = await api.documents.get('test-id');
    expect(doc).toHaveProperty('doc_id');
    expect(doc).toHaveProperty('filename');
    expect(doc).toHaveProperty('status');
  });

  // ... more contract tests
});
```

#### Stores Contract
```javascript
// tests/contracts/stores.test.js
import { useConnectionStore, useThemeStore, useDocumentStore } from '@stores';

describe('Stores Contract', () => {
  test('useConnectionStore has required API', () => {
    const store = useConnectionStore.getState();
    expect(store).toHaveProperty('status');
    expect(store).toHaveProperty('setConnected');
    expect(store).toHaveProperty('setDisconnected');
  });

  test('useThemeStore persists to localStorage', () => {
    const { setTheme } = useThemeStore.getState();
    setTheme('dark');
    expect(localStorage.getItem('docusearch-theme')).toContain('dark');
  });

  // ... more contract tests
});
```

#### Hooks Contract
```javascript
// tests/contracts/hooks.test.js
import { renderHook } from '@testing-library/react';
import { useDocuments, useWebSocket } from '@hooks';

describe('Hooks Contract', () => {
  test('useDocuments returns correct shape', () => {
    const { result } = renderHook(() => useDocuments({}));
    expect(result.current).toHaveProperty('documents');
    expect(result.current).toHaveProperty('isLoading');
    expect(result.current).toHaveProperty('deleteDocument');
  });

  // ... more contract tests
});
```

### Unit Tests

#### infrastructure-agent
```bash
npm run test -- stores/
npm run test -- services/
npm run test -- hooks/
```
**Coverage Target:** >80% for stores, services, hooks

#### layout-agent
```bash
npm run test -- components/layout/
npm run test -- components/common/ThemeToggle
npm run test -- components/common/StyleSelector
```
**Coverage Target:** >80% for layout components

#### foundation-agent
```bash
npm run test -- utils/
npm run test -- components/ErrorBoundary
```
**Coverage Target:** 100% for utilities

### Integration Tests

```javascript
// tests/integration/layout.test.js
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Layout } from '@components/layout/Layout';

describe('Layout Integration', () => {
  test('renders header, footer, and outlet', () => {
    render(
      <BrowserRouter>
        <Layout />
      </BrowserRouter>
    );

    expect(screen.getByRole('banner')).toBeInTheDocument();  // Header
    expect(screen.getByRole('contentinfo')).toBeInTheDocument();  // Footer
  });

  test('theme toggle switches theme', () => {
    const { container } = render(<Layout />);
    const toggle = screen.getByLabelText('Toggle theme');

    toggle.click();
    expect(document.documentElement).toHaveClass('dark');

    toggle.click();
    expect(document.documentElement).not.toHaveClass('dark');
  });
});
```

### Manual Checks
- [ ] Layout renders with Header + Footer on all routes
- [ ] Theme toggle switches between light/dark (visual check)
- [ ] Style selector dropdown opens and changes theme (visual check)
- [ ] Connection status shows "disconnected" (no WebSocket yet)
- [ ] No console errors
- [ ] No React warnings (key props, etc.)

### Exit Criteria
- ✅ All contract compliance tests pass
- ✅ All unit tests pass (>80% coverage)
- ✅ All integration tests pass
- ✅ All manual checks pass
- ✅ ESLint passes
- ✅ No TypeScript errors (if enabled)

**ONLY proceed to Wave 2 if ALL criteria met.**

---

## Wave 2 Validation Gate

**Goal:** Verify all 3 views are functional with feature parity

### Integration Tests (Per View)

#### LibraryView Integration Test
```javascript
// tests/integration/library-view.test.js
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LibraryView } from '@views/LibraryView';

describe('LibraryView Integration', () => {
  test('loads and displays documents', async () => {
    render(<LibraryView />);

    expect(screen.getByText('Loading documents...')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Sample Document.pdf')).toBeInTheDocument();
    });
  });

  test('filter bar filters documents', async () => {
    render(<LibraryView />);
    const user = userEvent.setup();

    await waitFor(() => screen.getByText('Sample Document.pdf'));

    const searchInput = screen.getByPlaceholderText('Search documents...');
    await user.type(searchInput, 'energy');

    await waitFor(() => {
      expect(screen.queryByText('Sample Document.pdf')).not.toBeInTheDocument();
      expect(screen.getByText('Energy Report.docx')).toBeInTheDocument();
    });
  });

  test('upload modal opens on drag', async () => {
    render(<LibraryView />);

    // Simulate drag over
    fireEvent.dragOver(document.body, {
      dataTransfer: { files: [] }
    });

    expect(screen.getByText('Drop files to upload')).toBeInTheDocument();
  });

  test('delete document removes from list', async () => {
    render(<LibraryView />);
    const user = userEvent.setup();

    await waitFor(() => screen.getByText('Sample Document.pdf'));

    const deleteBtn = screen.getByLabelText('Delete Sample Document.pdf');
    await user.click(deleteBtn);

    await waitFor(() => {
      expect(screen.queryByText('Sample Document.pdf')).not.toBeInTheDocument();
    });
  });
});
```

#### DetailsView Integration Test
```javascript
// tests/integration/details-view.test.js
import { render, screen, waitFor } from '@testing-library/react';
import { DetailsView } from '@views/DetailsView';

describe('DetailsView Integration', () => {
  test('loads and displays document details', async () => {
    render(<DetailsView />);

    expect(screen.getByText('Loading document...')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Sample Document.pdf')).toBeInTheDocument();
    });
  });

  test('slideshow navigates pages', async () => {
    render(<DetailsView />);
    const user = userEvent.setup();

    await waitFor(() => screen.getByText('Page 1 / 5'));

    const nextBtn = screen.getByLabelText('Next page');
    await user.click(nextBtn);

    expect(screen.getByText('Page 2 / 5')).toBeInTheDocument();
  });

  test('audio player plays audio', async () => {
    render(<DetailsView />);

    await waitFor(() => screen.getByText('Audio Playback'));

    const audio = screen.getByTestId('audio-player');
    expect(audio).toHaveAttribute('src', expect.stringContaining('.mp3'));
  });

  test('accordion expands sections', async () => {
    render(<DetailsView />);
    const user = userEvent.setup();

    await waitFor(() => screen.getByText('Introduction'));

    const sectionBtn = screen.getByText('Introduction');
    await user.click(sectionBtn);

    expect(screen.getByText(/This document discusses.../)).toBeInTheDocument();
  });
});
```

#### ResearchView Integration Test
```javascript
// tests/integration/research-view.test.js
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ResearchView } from '@views/ResearchView';

describe('ResearchView Integration', () => {
  test('submits query and displays answer', async () => {
    render(<ResearchView />);
    const user = userEvent.setup();

    const input = screen.getByPlaceholderText('Ask a question...');
    await user.type(input, 'What is renewable energy?');

    const submitBtn = screen.getByText('Ask');
    await user.click(submitBtn);

    expect(screen.getByText('Researching your question...')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/Renewable energy refers to.../)).toBeInTheDocument();
    }, { timeout: 5000 });
  });

  test('citations link to references', async () => {
    render(<ResearchView />);
    const user = userEvent.setup();

    // Submit query (shortened for brevity)
    await submitQuery('What is renewable energy?');

    await waitFor(() => screen.getByText(/Renewable energy refers to.../));

    const citation = screen.getByText('[1]');
    await user.click(citation);

    // Reference card should highlight
    const refCard = screen.getByTestId('reference-card-1');
    expect(refCard).toHaveClass('highlighted');
  });

  test('view toggle switches between detailed and simple', async () => {
    render(<ResearchView />);
    const user = userEvent.setup();

    await submitQuery('What is renewable energy?');
    await waitFor(() => screen.getAllByText(/Reference/));

    const simpleBtn = screen.getByText('Simple');
    await user.click(simpleBtn);

    // Check that thumbnail is hidden (simple view)
    expect(screen.queryByAltText('Document thumbnail')).not.toBeInTheDocument();
  });
});
```

### Cross-View Navigation Tests
```javascript
// tests/integration/navigation.test.js
describe('Cross-View Navigation', () => {
  test('navigate from library to details', async () => {
    render(<App />);

    await waitFor(() => screen.getByText('Sample Document.pdf'));

    const card = screen.getByText('Sample Document.pdf');
    await user.click(card);

    await waitFor(() => {
      expect(screen.getByText('Document Details')).toBeInTheDocument();
    });
  });

  test('navigate from details back to library', async () => {
    render(<App />);

    // ... navigate to details first

    const backBtn = screen.getByText('← Back to Library');
    await user.click(backBtn);

    await waitFor(() => {
      expect(screen.getByText('Document Library')).toBeInTheDocument();
    });
  });

  test('navigate to research and back', async () => {
    render(<App />);

    const researchLink = screen.getByText('Research →');
    await user.click(researchLink);

    expect(screen.getByText('Start your research')).toBeInTheDocument();

    const backBtn = screen.getByText('← Back to Library');
    await user.click(backBtn);

    expect(screen.getByText('Document Library')).toBeInTheDocument();
  });
});
```

### Manual QA Test Matrix

| Feature | Test Case | Expected Result | Status |
|---------|-----------|----------------|--------|
| **LibraryView** |
| Document Cards | Load library page | All documents display with thumbnails | |
| Search | Type "energy" in search | Filter documents containing "energy" | |
| Sort | Change sort to "Name A-Z" | Documents sort alphabetically | |
| File Type Filter | Select "PDF" filter | Only PDF documents show | |
| Pagination | Click page 2 | Next 50 documents load | |
| Upload | Drag PDF file | Upload modal opens, file uploads | |
| Real-time Update | Upload completes | New document appears in grid | |
| Delete | Click delete button | Document removed immediately | |
| **DetailsView** |
| PDF Slideshow | Open PDF document | Slideshow with page navigation shows | |
| Keyboard Nav | Press → arrow key | Next page displays | |
| Page Input | Type "5" in page input | Jump to page 5 | |
| Audio Player | Open MP3 file | Audio player with album art shows | |
| VTT Captions | Play audio | Captions display in overlay | |
| Accordion | Click section | Section expands, markdown renders | |
| Copy Text | Click copy button | Text copied to clipboard | |
| Download | Click download button | File downloads | |
| **ResearchView** |
| Query Submission | Type and submit query | Loading state, then answer displays | |
| Inline Citations | See answer with [1], [2] | Citations are superscript links | |
| Citation Click | Click [1] | Reference card #1 highlights | |
| Bidirectional Highlight | Hover over citation | Reference card highlights | |
| Reference Card | View references panel | All references show metadata | |
| View Toggle | Click "Simple" | References switch to simple view | |
| **Cross-View** |
| Library → Details | Click document card | Navigate to details view | |
| Details → Library | Click back button | Navigate back to library | |
| Library → Research | Click research link | Navigate to research view | |
| Theme Persistence | Change theme, refresh page | Theme persists | |

### Accessibility Tests (Automated)

```javascript
// tests/accessibility/a11y.test.js
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
expect.extend(toHaveNoViolations);

describe('Accessibility', () => {
  test('LibraryView has no a11y violations', async () => {
    const { container } = render(<LibraryView />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  test('DetailsView has no a11y violations', async () => {
    const { container } = render(<DetailsView />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  test('ResearchView has no a11y violations', async () => {
    const { container } = render(<ResearchView />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```

### Exit Criteria
- ✅ All integration tests pass (LibraryView, DetailsView, ResearchView)
- ✅ All navigation tests pass
- ✅ All accessibility tests pass (jest-axe)
- ✅ Manual QA test matrix 100% complete
- ✅ No console errors in any view
- ✅ No React warnings
- ✅ Lighthouse accessibility score 100 (all views)

**ONLY proceed to Wave 3 if ALL criteria met.**

---

## Wave 3 Validation Gate

**Goal:** Verify advanced features and optimize performance

### Performance Tests

```javascript
// tests/performance/bundle-size.test.js
import { execSync } from 'child_process';

describe('Bundle Size', () => {
  test('production bundle < 500KB gzipped', () => {
    execSync('npm run build');
    const sizeOutput = execSync('du -sh dist/*.js').toString();
    const sizeKB = parseInt(sizeOutput);
    expect(sizeKB).toBeLessThan(500);
  });

  test('initial chunk < 200KB gzipped', () => {
    // Check main chunk size
  });
});
```

### Lighthouse Audits (Automated)

```javascript
// tests/lighthouse/lighthouse.test.js
import lighthouse from 'lighthouse';
import chromeLauncher from 'chrome-launcher';

describe('Lighthouse Audits', () => {
  test('LibraryView performance > 90', async () => {
    const chrome = await chromeLauncher.launch();
    const results = await lighthouse('http://localhost:3000', {
      port: chrome.port,
      onlyCategories: ['performance']
    });

    expect(results.lhr.categories.performance.score).toBeGreaterThan(0.9);
    await chrome.kill();
  });

  test('All views accessibility = 100', async () => {
    const views = ['/', '/details/test', '/research'];

    for (const view of views) {
      const results = await lighthouse(`http://localhost:3000${view}`, {
        onlyCategories: ['accessibility']
      });
      expect(results.lhr.categories.accessibility.score).toBe(1.0);
    }
  });
});
```

### Advanced Feature Tests

```javascript
// tests/features/bounding-boxes.test.js
test('bounding boxes render on search results', () => {
  // Test BoundingBoxOverlay integration
});

// tests/features/chunk-highlighting.test.js
test('chunk highlighting works in accordion', () => {
  // Test ChunkHighlighter integration
});

// tests/features/loading-skeletons.test.js
test('skeletons show during loading', () => {
  // Test skeleton components
});
```

### Exit Criteria
- ✅ All advanced feature tests pass
- ✅ Test coverage >80% (overall)
- ✅ Lighthouse performance >90 (all views)
- ✅ Lighthouse accessibility 100 (all views)
- ✅ Bundle size <500KB gzipped
- ✅ No performance regressions from Wave 2

**ONLY proceed to Wave 4 if ALL criteria met.**

---

## Wave 4 Validation Gate

**Goal:** Verify production readiness and full E2E functionality

### E2E Tests (Playwright)

```javascript
// tests/e2e/full-workflow.spec.js
import { test, expect } from '@playwright/test';

test('full workflow: upload → process → view → research', async ({ page }) => {
  // 1. Upload document
  await page.goto('http://localhost:3000');
  const fileInput = await page.locator('input[type="file"]');
  await fileInput.setInputFiles('./test-fixtures/sample.pdf');

  await expect(page.locator('.document-card')).toContainText('sample.pdf');

  // 2. Wait for processing
  await expect(page.locator('.status--processing')).toBeVisible();
  await expect(page.locator('.status--completed')).toBeVisible({ timeout: 60000 });

  // 3. Navigate to details
  await page.click('text=sample.pdf');
  await expect(page.locator('h1')).toContainText('Document Details');
  await expect(page.locator('.slideshow-image')).toBeVisible();

  // 4. Navigate to research
  await page.click('text=Research →');
  await page.fill('input[placeholder*="Ask a question"]', 'What is this document about?');
  await page.click('button:has-text("Ask")');

  await expect(page.locator('.answer-display')).toBeVisible({ timeout: 10000 });
  await expect(page.locator('[data-citation="1"]')).toBeVisible();
});

test('accessibility with keyboard only', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Navigate using Tab
  await page.keyboard.press('Tab');
  await page.keyboard.press('Tab');
  await page.keyboard.press('Enter');

  // Check focus indicators are visible
  const focused = await page.locator(':focus');
  await expect(focused).toBeVisible();
});

test('theme persists across navigation', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Toggle to dark theme
  await page.click('[aria-label="Toggle theme"]');
  await expect(page.locator('html')).toHaveClass(/dark/);

  // Navigate to details
  await page.click('text=sample.pdf');
  await expect(page.locator('html')).toHaveClass(/dark/);

  // Refresh page
  await page.reload();
  await expect(page.locator('html')).toHaveClass(/dark/);
});
```

### Production Build Tests

```bash
# Build production bundle
npm run build

# Serve production bundle
npm run preview

# Run tests against production build
PLAYWRIGHT_BASE_URL=http://localhost:4173 npm run test:e2e
```

### Final Manual QA Checklist

- [ ] Production build completes without errors
- [ ] Production build runs correctly (npm run preview)
- [ ] All features work in production mode
- [ ] API calls work with production URLs
- [ ] WebSocket reconnects after network interruption
- [ ] Upload works end-to-end (upload → process → view)
- [ ] Search highlights render correctly
- [ ] Citations work bidirectionally
- [ ] Theme persists across page refreshes
- [ ] All accessibility features work (keyboard nav, screen reader)
- [ ] Mobile responsive (test on 480px, 768px, 1024px)
- [ ] Works in Chrome, Firefox, Safari, Edge

### Exit Criteria
- ✅ All E2E tests pass (production build)
- ✅ Production build smoke test passes
- ✅ Final manual QA checklist 100% complete
- ✅ Documentation complete
- ✅ Deployment scripts working
- ✅ Legacy frontend archived

**READY FOR PRODUCTION DEPLOYMENT.**

---

## Testing Tools & Setup

### Required Dependencies

```json
{
  "devDependencies": {
    "vitest": "^1.6.0",
    "@testing-library/react": "^15.0.6",
    "@testing-library/jest-dom": "^6.4.5",
    "@testing-library/user-event": "^14.5.2",
    "jest-axe": "^8.0.0",
    "msw": "^2.3.0",
    "@playwright/test": "^1.44.0",
    "lighthouse": "^11.7.1",
    "chrome-launcher": "^1.1.0"
  }
}
```

### Test Scripts

```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "lighthouse": "node scripts/lighthouse-audit.js"
  }
}
```

### MSW Setup (Mock Service Worker)

```javascript
// tests/mocks/handlers.js
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/documents', () => {
    return HttpResponse.json({
      documents: [
        { doc_id: '1', filename: 'Sample Document.pdf', status: 'completed' }
      ],
      total: 1
    });
  }),

  http.post('/api/research/ask', async ({ request }) => {
    const { query } = await request.json();
    return HttpResponse.json({
      answer: `This is a test answer for: ${query} [1]`,
      references: [
        { id: 1, doc_id: '1', filename: 'Sample Document.pdf', page: 1 }
      ]
    });
  })
];
```

---

## Continuous Validation

### Pre-Commit Hooks (Husky)

```bash
# .husky/pre-commit
#!/bin/sh
npm run lint
npm run test -- --run
```

### CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npm run lint
      - run: npm run test -- --run
      - run: npm run build
      - run: npm run test:e2e
```

---

## Validation Ownership

| Validation Layer | Responsible Agent | Deliverable |
|-----------------|------------------|-------------|
| Contract Compliance | infrastructure-agent | Contract validation tests |
| Unit Tests | All agents | Component/function tests |
| Integration Tests | library-agent, details-agent, research-agent | View integration tests |
| E2E Tests | foundation-agent | Playwright test suite |
| Performance | foundation-agent | Lighthouse audit script |
| Accessibility | layout-agent | jest-axe setup + tests |
| Manual QA | All agents | Test matrix completion |

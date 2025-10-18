# Layout Components Integration Contract

**Provider:** layout-agent
**Consumers:** All view agents (library-agent, details-agent, research-agent)
**Technology:** React components with React Router

---

## Contract Overview

Layout components provide the structural shell for the application, including header, footer, and page wrapper. All routes inherit these components through the Layout wrapper.

---

## Component 1: Layout

**File:** `frontend/src/components/layout/Layout.jsx`
**Purpose:** Main layout wrapper that provides Header and Footer to all routes

### Props

None - uses React Router's `<Outlet />` for child routes

### Route Detection

```javascript
// Determines header props based on current route
const getHeaderProps = () => {
  const path = location.pathname;

  if (path.startsWith('/details/')) {
    return {
      title: 'Document Details',
      showBackButton: true,
      backTo: '/',
      showResearchLink: false
    };
  }

  if (path === '/research') {
    return {
      title: 'Research',
      showBackButton: true,
      backTo: '/',
      showResearchLink: false
    };
  }

  // Default (library/home)
  return {
    title: 'Document Library',
    showBackButton: false,
    showResearchLink: true
  };
};
```

### Usage in App.jsx

```javascript
import Layout from './components/layout/Layout';

<Routes>
  <Route element={<Layout />}>
    <Route path="/" element={<LibraryView />} />
    <Route path="/details/:id" element={<DetailsView />} />
    <Route path="/research" element={<ResearchView />} />
  </Route>
</Routes>
```

### Rendered Structure

```html
<div className="layout">
  <Header {...headerProps} />
  <main className="layout__main">
    <Outlet /> <!-- Child route renders here -->
  </main>
  <Footer />
</div>
```

---

## Component 2: Header

**File:** `frontend/src/components/layout/Header.jsx`
**Purpose:** Application header with dynamic content based on route

### Props

```typescript
{
  title?: string;              // Page title (default: 'Document Search')
  showBackButton?: boolean;    // Show back button (default: false)
  backTo?: string;             // Route to navigate back to (default: '/')
  showResearchLink?: boolean;  // Show research link button (default: false)
}
```

### Features

- Sticky positioning (`position: sticky; top: 0`)
- Back button with arrow icon (conditionally rendered)
- H1 title (responsive font size)
- Research link button (conditionally rendered)
- Role: `banner`

### Example Renders

**Library Page:**
```html
<header className="header" role="banner">
  <div className="header__container">
    <div className="header__left">
      <h1 className="header__title">Document Library</h1>
    </div>
    <nav className="header__nav">
      <Link to="/research" className="header__nav-link">
        <svg>...</svg>
        <span>Research</span>
      </Link>
    </nav>
  </div>
</header>
```

**Details Page:**
```html
<header className="header" role="banner">
  <div className="header__container">
    <div className="header__left">
      <Link to="/" className="header__back-button">
        <svg>...</svg>
        <span>Back</span>
      </Link>
      <h1 className="header__title">Document Details</h1>
    </div>
  </div>
</header>
```

---

## Component 3: Footer

**File:** `frontend/src/components/layout/Footer.jsx`
**Purpose:** Application footer with theme controls and connection status

### Props

```typescript
{
  showConnectionStatus?: boolean;  // Show connection status (default: true)
}
```

### Embedded Components

- `ThemeToggle` - Light/dark theme switch
- `StyleSelector` - Visual style dropdown
- `ConnectionStatus` - WebSocket status indicator

### Structure

```html
<footer className="footer" role="contentinfo">
  <div className="footer__container">
    <div className="footer__actions">
      <ThemeToggle />
      <StyleSelector />
    </div>
    <div className="footer__status">
      <ConnectionStatus />
    </div>
  </div>
</footer>
```

### Responsive Behavior

- Desktop: Two-column layout (actions left, status right)
- Mobile: Stacked column layout

---

## Component 4: ThemeToggle

**File:** `frontend/src/components/common/ThemeToggle.jsx`
**Purpose:** Toggle between light and dark themes

### Dependencies

- `useThemeStore` from `stores/useThemeStore`

### Features

- Icon indication: ☀ (light), ☾ (dark)
- Reads `getEffectiveTheme()` to determine current theme
- Calls `setTheme('light' | 'dark')` on toggle
- Keyboard accessible (Enter/Space)
- Rotate animation on click

### Usage

```javascript
import ThemeToggle from '@components/common/ThemeToggle';

<ThemeToggle />
```

---

## Component 5: StyleSelector

**File:** `frontend/src/components/common/StyleSelector.jsx`
**Purpose:** Dropdown selector for visual style themes

### Dependencies

- `useThemeStore` from `stores/useThemeStore`

### Available Styles

1. kraft-paper (default)
2. graphite
3. notebook
4. gold-on-blue
5. blue-on-black

### Features

- Dropdown with theme list
- Current theme displayed in button
- Checkmark on active theme
- Keyboard navigation (Escape to close)
- Click outside to close
- Loads CSS dynamically via `setStyle(styleId)`

### Usage

```javascript
import StyleSelector from '@components/common/StyleSelector';

<StyleSelector />
```

---

## Component 6: ConnectionStatus

**File:** `frontend/src/components/common/ConnectionStatus.jsx`
**Purpose:** Display WebSocket connection status

### Dependencies

- `useConnectionStore` from `stores/useConnectionStore`

### States

```javascript
connected    → '● Connected'     (green)
disconnected → '○ Disconnected'  (gray)
reconnecting → '◐ Reconnecting...' (orange, pulse animation)
```

### Features

- ARIA live region (`role="status" aria-live="polite"`)
- Pulse animation on reconnecting state
- Color-coded indicators

### Usage

```javascript
import ConnectionStatus from '@components/common/ConnectionStatus';

<ConnectionStatus />
```

---

## Component 7: LoadingSpinner

**File:** `frontend/src/components/common/LoadingSpinner.jsx`
**Purpose:** Simple loading spinner for loading states

### Props

```typescript
{
  size?: 'small' | 'medium';  // default: 'medium'
  className?: string;
  label?: string;             // default: 'Loading'
}
```

### Sizes

- small: 20px × 20px
- medium: 40px × 40px

### Features

- Spin animation (0.8s linear infinite)
- Screen reader accessible (`role="status" aria-label`)
- Dark theme support

### Usage

```javascript
import LoadingSpinner from '@components/common/LoadingSpinner';

<LoadingSpinner size="small" />
<LoadingSpinner size="medium" label="Loading documents..." />
```

---

## CSS Architecture

### Files

```
frontend/src/components/
├── layout/
│   ├── Layout.css
│   ├── Header.css
│   └── Footer.css
└── common/
    ├── ThemeToggle.css
    ├── StyleSelector.css
    ├── ConnectionStatus.css
    └── LoadingSpinner.css
```

### CSS Custom Properties Used

```css
/* Colors */
--color-bg-primary
--color-bg-secondary
--color-text-primary
--color-text-secondary
--color-text-tertiary
--color-border
--color-border-hover
--color-primary-base
--color-primary-hover
--color-primary-light
--color-status-ok
--color-status-warn
--color-status-err

/* Layout */
--layout-max-width
--z-sticky
--z-dropdown

/* Borders */
--border-radius-sm
--border-radius-md

/* Transitions */
--transition-base
--transition-ease

/* Shadows */
--shadow-sm
--shadow-md
--shadow-lg
```

### Dark Theme Support

All components support dark theme via `.dark` class on `<html>`:

```css
.dark .component {
  /* Dark theme overrides */
}
```

---

## Integration with Zustand Stores

### Theme Store Integration

**Provider:** infrastructure-agent (Wave 1)
**File:** `frontend/src/stores/useThemeStore.js`

```javascript
// ThemeToggle usage
const theme = useThemeStore((state) => state.theme);
const setTheme = useThemeStore((state) => state.setTheme);
const getEffectiveTheme = useThemeStore((state) => state.getEffectiveTheme);

// StyleSelector usage
const style = useThemeStore((state) => state.style);
const setStyle = useThemeStore((state) => state.setStyle);
```

**Side Effects:**
- `setTheme()` → Toggles `.dark` class on `<html>`
- `setStyle()` → Loads CSS file dynamically
- Persists to localStorage: `docusearch-theme`

### Connection Store Integration

**Provider:** infrastructure-agent (Wave 1)
**File:** `frontend/src/stores/useConnectionStore.js`

```javascript
// ConnectionStatus usage
const status = useConnectionStore((state) => state.status);
// Possible values: 'connected' | 'disconnected' | 'reconnecting'
```

**Note:** WebSocket hook (infrastructure-agent) will update this store

---

## Accessibility Features

### ARIA Roles

- Header: `role="banner"`
- Footer: `role="contentinfo"`
- ConnectionStatus: `role="status" aria-live="polite"`
- LoadingSpinner: `role="status"`

### Keyboard Navigation

- ThemeToggle: Enter/Space to toggle
- StyleSelector: Escape to close dropdown, Arrow keys to navigate (future)
- Header back button: Tab navigation, Enter to activate
- All interactive elements: Focus visible outline (2px)

### Focus Management

```css
:focus {
  outline: 2px solid var(--color-primary-base);
  outline-offset: 2px;
}
```

### Reduced Motion Support

```css
@media (prefers-reduced-motion: reduce) {
  * {
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
  }
}
```

---

## Responsive Breakpoints

```css
/* Mobile */
@media (max-width: 640px) {
  .header__back-text { display: none; }
  .header__title { font-size: 1.5rem; }
  .footer__container { flex-direction: column; }
  .layout__main { padding: 1rem; }
}

/* Desktop */
@media (min-width: 640px) {
  .header__back-text { display: inline; }
  .header__title { font-size: 1.875rem; }
}
```

---

## Validation Checklist

- [x] Layout component renders Header + Outlet + Footer
- [x] Header props dynamically set based on route
- [x] ThemeToggle switches between light/dark
- [x] StyleSelector loads theme CSS on change
- [x] ConnectionStatus shows correct state
- [x] LoadingSpinner renders in small/medium sizes
- [x] All components use Zustand stores
- [x] Dark theme support via `.dark` class
- [x] ARIA roles and labels present
- [x] Keyboard navigation functional
- [x] Responsive design mobile/desktop
- [x] CSS custom properties used consistently

---

## Usage Example (Full Integration)

```javascript
// App.jsx
import { Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import LibraryView from './views/LibraryView';
import DetailsView from './views/DetailsView';
import ResearchView from './views/ResearchView';

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<LibraryView />} />
        <Route path="/details/:id" element={<DetailsView />} />
        <Route path="/research" element={<ResearchView />} />
      </Route>
    </Routes>
  );
}
```

**Rendered on `/`:**
```html
<div class="layout">
  <header class="header" role="banner">
    <h1>Document Library</h1>
    <nav><Link to="/research">Research</Link></nav>
  </header>
  <main class="layout__main">
    <LibraryView />
  </main>
  <footer class="footer" role="contentinfo">
    <ThemeToggle />
    <StyleSelector />
    <ConnectionStatus />
  </footer>
</div>
```

**Rendered on `/details/abc123`:**
```html
<div class="layout">
  <header class="header" role="banner">
    <Link to="/">← Back</Link>
    <h1>Document Details</h1>
  </header>
  <main class="layout__main">
    <DetailsView />
  </main>
  <footer class="footer" role="contentinfo">
    <ThemeToggle />
    <StyleSelector />
    <ConnectionStatus />
  </footer>
</div>
```

---

## Notes for Downstream Agents

### For Library Agent (Wave 2)
- Use `LoadingSpinner` for document loading states
- Don't create your own header/footer (inherited from Layout)
- Focus on filter bar and document grid content

### For Details Agent (Wave 3)
- Use `LoadingSpinner` for document loading
- Header will automatically show "Document Details" + back button
- Don't create navigation elements

### For Research Agent (Wave 4)
- Header will automatically show "Research" + back button
- Use `LoadingSpinner` for AI query states
- Focus on two-panel research UI content

### For Infrastructure Agent (if not yet run)
- Stores already created by layout-agent as placeholders
- Replace `useConnectionStore.js` and `useThemeStore.js` if needed
- Ensure `useDocumentStore.js` is created for library-agent

---

## Files Created

```
frontend/src/
├── components/
│   ├── layout/
│   │   ├── Layout.jsx             ✅ Created
│   │   ├── Layout.css             ✅ Created
│   │   ├── Header.jsx             ✅ Created
│   │   ├── Header.css             ✅ Created
│   │   ├── Footer.jsx             ✅ Created
│   │   └── Footer.css             ✅ Created
│   └── common/
│       ├── ThemeToggle.jsx        ✅ Created
│       ├── ThemeToggle.css        ✅ Created
│       ├── StyleSelector.jsx      ✅ Created
│       ├── StyleSelector.css      ✅ Created
│       ├── ConnectionStatus.jsx   ✅ Created
│       ├── ConnectionStatus.css   ✅ Created
│       ├── LoadingSpinner.jsx     ✅ Created
│       └── LoadingSpinner.css     ✅ Created
├── stores/
│   ├── useConnectionStore.js      ✅ Created (placeholder)
│   └── useThemeStore.js           ✅ Created (placeholder)
└── App.jsx                        ✅ Updated

Total: 16 files created/updated
```

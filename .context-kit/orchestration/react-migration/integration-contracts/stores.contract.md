# State Stores Integration Contract

**Provider:** infrastructure-agent
**Consumers:** All agents (layout-agent, library-agent, details-agent, research-agent)
**Technology:** Zustand with persist middleware

---

## Contract Overview

Three Zustand stores manage global client state with localStorage persistence. These stores provide reactive state updates across the application without prop drilling.

---

## Store 1: Connection Store

**File:** `frontend/src/stores/useConnectionStore.js`
**Purpose:** Track WebSocket connection status

### State Shape

```typescript
{
  status: 'connected' | 'disconnected' | 'reconnecting';
  lastConnected: Date | null;
  reconnectAttempts: number;
}
```

### Actions

```typescript
setConnected: () => void
setDisconnected: () => void
setReconnecting: (attempts: number) => void
reset: () => void
```

### Usage Example

```javascript
import { useConnectionStore } from '@stores/useConnectionStore';

function ConnectionStatus() {
  const status = useConnectionStore((state) => state.status);
  const setConnected = useConnectionStore((state) => state.setConnected);

  return (
    <div className={`status status--${status}`}>
      {status === 'connected' && '● Connected'}
      {status === 'disconnected' && '○ Disconnected'}
      {status === 'reconnecting' && '◐ Reconnecting...'}
    </div>
  );
}
```

### Implementation Requirements

- ✅ No persistence (connection state should not persist across sessions)
- ✅ Initial state: `{ status: 'disconnected', lastConnected: null, reconnectAttempts: 0 }`
- ✅ `setConnected()` resets `reconnectAttempts` to 0
- ✅ `setReconnecting(attempts)` increments reconnect counter

---

## Store 2: Theme Store

**File:** `frontend/src/stores/useThemeStore.js`
**Purpose:** Manage theme (light/dark) and visual style (kraft-paper, graphite, etc.)

### State Shape

```typescript
{
  theme: 'light' | 'dark' | 'system';
  style: 'kraft-paper' | 'graphite' | 'notebook' | 'gold-on-blue' | 'blue-on-black';
  systemTheme: 'light' | 'dark';  // Detected from prefers-color-scheme
}
```

### Actions

```typescript
setTheme: (theme: 'light' | 'dark' | 'system') => void
setStyle: (style: string) => void
detectSystemTheme: () => void
getEffectiveTheme: () => 'light' | 'dark'  // Resolves 'system' to actual theme
```

### Usage Example

```javascript
import { useThemeStore } from '@stores/useThemeStore';

function ThemeToggle() {
  const theme = useThemeStore((state) => state.theme);
  const setTheme = useThemeStore((state) => state.setTheme);
  const effectiveTheme = useThemeStore((state) => state.getEffectiveTheme());

  const toggleTheme = () => {
    setTheme(effectiveTheme === 'light' ? 'dark' : 'light');
  };

  return <button onClick={toggleTheme}>Toggle Theme</button>;
}
```

### Implementation Requirements

- ✅ Persist to localStorage key: `docusearch-theme`
- ✅ Initial state: `{ theme: 'system', style: 'kraft-paper', systemTheme: 'light' }`
- ✅ `detectSystemTheme()` listens to `window.matchMedia('(prefers-color-scheme: dark)')`
- ✅ `getEffectiveTheme()` returns `systemTheme` if `theme === 'system'`, otherwise returns `theme`
- ✅ Apply theme by toggling `.dark` class on `<html>` element
- ✅ Load style CSS file dynamically when `setStyle()` is called

### Theme Application Side Effects

When theme changes, the store should:
1. Update localStorage
2. Toggle `.dark` class on `<html>`
3. Dispatch custom event: `window.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }))`

---

## Store 3: Document Store

**File:** `frontend/src/stores/useDocumentStore.js`
**Purpose:** Manage filter/sort/pagination state for document library

### State Shape

```typescript
{
  filters: {
    search: string;
    sortBy: 'newest_first' | 'oldest_first' | 'name_asc' | 'name_desc';
    fileTypeGroup: string;  // 'all' | 'pdf' | 'audio' | 'office' | ...
    limit: number;
    offset: number;
  };
  tempDocuments: Map<string, {
    filename: string;
    status: 'uploading' | 'processing';
    progress: number;
  }>;
}
```

### Actions

```typescript
setFilters: (partial: Partial<filters>) => void
resetFilters: () => void
setSearch: (search: string) => void
setSortBy: (sortBy: string) => void
setFileTypeGroup: (group: string) => void
setPage: (page: number) => void  // Calculates offset from page
addTempDocument: (tempId: string, filename: string) => void
updateTempDocumentProgress: (tempId: string, progress: number) => void
removeTempDocument: (tempId: string) => void
```

### Usage Example

```javascript
import { useDocumentStore } from '@stores/useDocumentStore';

function FilterBar() {
  const filters = useDocumentStore((state) => state.filters);
  const setSearch = useDocumentStore((state) => state.setSearch);

  return (
    <input
      type="text"
      value={filters.search}
      onChange={(e) => setSearch(e.target.value)}
      placeholder="Search documents..."
    />
  );
}
```

### Implementation Requirements

- ✅ Persist `filters` to localStorage key: `docusearch-filters`
- ✅ Do NOT persist `tempDocuments` (in-memory only)
- ✅ Initial state:
  ```javascript
  {
    filters: {
      search: '',
      sortBy: 'newest_first',
      fileTypeGroup: 'all',
      limit: 50,
      offset: 0
    },
    tempDocuments: new Map()
  }
  ```
- ✅ `setFilters()` merges partial updates (spread syntax)
- ✅ `setPage(page)` calculates `offset = (page - 1) * limit`
- ✅ `resetFilters()` restores initial filter state

### Temp Documents Lifecycle

1. Upload starts → `addTempDocument(tempId, filename)` → status: 'uploading'
2. Upload progresses → `updateTempDocumentProgress(tempId, progress)` → progress: 0-100
3. Upload completes → WebSocket message → status changes to 'processing'
4. Processing completes → WebSocket message → `removeTempDocument(tempId)` + real document appears

---

## Store Configuration (Zustand + Persist)

### Persist Middleware Configuration

```javascript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useThemeStore = create(
  persist(
    (set, get) => ({
      // state and actions
    }),
    {
      name: 'docusearch-theme',  // localStorage key
      partialize: (state) => ({ theme: state.theme, style: state.style })  // Only persist these
    }
  )
);
```

### Store Testing

Each store must provide:
- ✅ Initial state factory for tests
- ✅ Reset action for cleanup
- ✅ Mock localStorage for tests

Example test helper:

```javascript
// stores/__tests__/helpers.js
export function createMockStore(initialState) {
  return create((set) => ({
    ...initialState,
    reset: () => set(initialState)
  }));
}
```

---

## Integration Points

### With useWebSocket Hook (infrastructure-agent)
- WebSocket hook calls `setConnected()`, `setDisconnected()`, `setReconnecting()`
- On document status message → `updateTempDocumentProgress()` or `removeTempDocument()`

### With Layout Components (layout-agent)
- `Header.jsx` reads `useDocumentStore.filters.search` to show active filter count
- `Footer.jsx` contains `ThemeToggle` and `StyleSelector` which use `useThemeStore`
- `ConnectionStatus.jsx` uses `useConnectionStore`

### With Library View (library-agent)
- `LibraryView.jsx` reads `useDocumentStore.filters` to query documents
- `FilterBar.jsx` updates `useDocumentStore.filters`
- `UploadModal.jsx` calls `addTempDocument()` and `updateTempDocumentProgress()`

### With Details/Research Views
- `DetailsView.jsx` and `ResearchView.jsx` don't directly use stores (local state only)
- But they render `Header` and `Footer` which use stores

---

## Validation Checklist

- [ ] All 3 stores implemented with documented API
- [ ] Persist middleware configured correctly
- [ ] Initial states match specifications
- [ ] All actions update state immutably
- [ ] localStorage keys match documentation
- [ ] Theme application side effects work (class toggle, CSS loading)
- [ ] Temp documents lifecycle functional
- [ ] Test helpers provided
- [ ] JSDoc annotations complete

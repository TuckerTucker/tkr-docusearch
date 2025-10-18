# Frontend Infrastructure - Wave 1 Complete

Infrastructure layer for the React migration providing API services, state management, and custom hooks.

## Overview

Wave 1 establishes the foundation for the React migration with:
- **API Services**: Centralized HTTP client with timeout handling and error standardization
- **Zustand Stores**: Global state management with localStorage persistence
- **Custom Hooks**: React Query wrappers and utility hooks for common patterns

## Directory Structure

```
frontend/src/
├── services/          # API and WebSocket services
│   ├── api.js         # REST API client (327 lines)
│   ├── websocket.js   # WebSocket manager (157 lines)
│   └── research.js    # Research service wrapper (80 lines)
├── stores/            # Zustand state stores
│   ├── useConnectionStore.js   # WebSocket status (47 lines)
│   ├── useThemeStore.js        # Theme/style with persist (139 lines)
│   └── useDocumentStore.js     # Filters with persist (116 lines)
└── hooks/             # Custom React hooks
    ├── useWebSocket.js          # WebSocket connection (101 lines)
    ├── useDocuments.js          # Document list + delete (75 lines)
    ├── useDocumentDetails.js   # Document + markdown (49 lines)
    ├── useResearch.js           # Research queries (39 lines)
    ├── useClipboard.js          # Clipboard operations (72 lines)
    └── useKeyboardNav.js        # Keyboard navigation (112 lines)
```

**Total Lines of Code**: 1,314 lines

## API Service (`services/api.js`)

Centralized REST API client with namespaced endpoints:

### Usage

```javascript
import { api, APIError } from '@services/api';

// Fetch documents
const { documents, total } = await api.documents.list({
  search: 'energy',
  sort_by: 'newest_first',
  file_type_group: 'pdf',
  limit: 50,
  offset: 0
});

// Get document details
const doc = await api.documents.get(docId);

// Get markdown content
const { sections } = await api.documents.getMarkdown(docId);

// Delete document
await api.documents.delete(docId);

// Upload file
await api.upload.uploadFile(file, (progress) => {
  console.log(`Upload: ${progress}%`);
});

// Research query
const { answer, references } = await api.research.ask('What are the main themes?');

// Check health
const { status } = await api.status.get();
```

### Features

- 30-second timeout on all requests
- Standardized `APIError` with status codes
- Automatic JSON parsing
- Progress tracking for uploads (XMLHttpRequest)
- Query parameter building

## WebSocket Service (`services/websocket.js`)

WebSocket connection manager with automatic reconnection:

### Usage

```javascript
import { WebSocketManager } from '@services/websocket';

const ws = new WebSocketManager('ws://localhost:8002/ws', {
  onMessage: (event) => {
    const data = JSON.parse(event.data);
    console.log('Message:', data);
  },
  onOpen: () => console.log('Connected'),
  onClose: () => console.log('Disconnected'),
  reconnectInterval: 3000,
  maxReconnectAttempts: 10
});

ws.connect();
ws.send({ type: 'ping' });
ws.disconnect();
```

### Features

- Exponential backoff: 1s, 2s, 4s, 8s, ..., max 30s
- Automatic JSON stringification
- Connection state tracking
- Clean disconnect handling

## Zustand Stores

### Connection Store (`stores/useConnectionStore.js`)

Tracks WebSocket connection status (no persistence):

```javascript
import { useConnectionStore } from '@stores/useConnectionStore';

function ConnectionStatus() {
  const status = useConnectionStore((state) => state.status);
  const setConnected = useConnectionStore((state) => state.setConnected);

  return <div>{status}</div>; // 'connected' | 'disconnected' | 'reconnecting'
}
```

**State**: `{ status, lastConnected, reconnectAttempts }`
**Actions**: `setConnected()`, `setDisconnected()`, `setReconnecting(attempts)`, `reset()`

### Theme Store (`stores/useThemeStore.js`)

Manages theme and visual style with localStorage persistence:

```javascript
import { useThemeStore } from '@stores/useThemeStore';

function ThemeToggle() {
  const theme = useThemeStore((state) => state.theme);
  const setTheme = useThemeStore((state) => state.setTheme);
  const effectiveTheme = useThemeStore((state) => state.getEffectiveTheme());

  return (
    <button onClick={() => setTheme(effectiveTheme === 'light' ? 'dark' : 'light')}>
      Toggle Theme
    </button>
  );
}
```

**State**: `{ theme, style, systemTheme }`
**Actions**: `setTheme(theme)`, `setStyle(style)`, `detectSystemTheme()`, `getEffectiveTheme()`
**Persistence**: `localStorage['docusearch-theme']`

**Features**:
- Toggles `.dark` class on `<html>`
- Loads style CSS dynamically
- Listens to system theme changes
- Dispatches `themechange` custom event

### Document Store (`stores/useDocumentStore.js`)

Manages document filters and temporary upload state:

```javascript
import { useDocumentStore } from '@stores/useDocumentStore';

function FilterBar() {
  const filters = useDocumentStore((state) => state.filters);
  const setSearch = useDocumentStore((state) => state.setSearch);

  return (
    <input
      value={filters.search}
      onChange={(e) => setSearch(e.target.value)}
    />
  );
}
```

**State**: `{ filters, tempDocuments }`
**Actions**: `setFilters(partial)`, `resetFilters()`, `setSearch()`, `setSortBy()`, `setFileTypeGroup()`, `setPage(page)`, `addTempDocument()`, `updateTempDocumentProgress()`, `removeTempDocument()`
**Persistence**: `localStorage['docusearch-filters']` (filters only, not tempDocuments)

## Custom Hooks

### useWebSocket (`hooks/useWebSocket.js`)

React hook wrapper for WebSocket with automatic cleanup:

```javascript
import { useWebSocket } from '@hooks/useWebSocket';

function RealtimeComponent() {
  const { send, isConnected, reconnectAttempts } = useWebSocket(
    'ws://localhost:8002/ws',
    {
      onMessage: (event) => {
        const data = JSON.parse(event.data);
        // Handle message
      },
      onOpen: () => console.log('Connected'),
      onClose: () => console.log('Disconnected')
    }
  );

  return <div>{isConnected ? 'Connected' : 'Disconnected'}</div>;
}
```

### useDocuments (`hooks/useDocuments.js`)

React Query wrapper for document list with optimistic delete:

```javascript
import { useDocuments } from '@hooks/useDocuments';

function LibraryView() {
  const { documents, totalCount, isLoading, deleteDocument } = useDocuments({
    search: 'energy',
    sortBy: 'newest_first'
  });

  return (
    <div>
      {documents.map((doc) => (
        <button key={doc.doc_id} onClick={() => deleteDocument(doc.doc_id)}>
          Delete
        </button>
      ))}
    </div>
  );
}
```

**Features**:
- Automatic caching per filter combination
- Optimistic delete with rollback on error
- 30-second stale time

### useDocumentDetails (`hooks/useDocumentDetails.js`)

Fetches document metadata and markdown in parallel:

```javascript
import { useDocumentDetails } from '@hooks/useDocumentDetails';

function DetailsView({ docId }) {
  const { document, markdown, isLoading } = useDocumentDetails(docId);

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <h1>{document.filename}</h1>
      <Accordion sections={markdown.sections} />
    </div>
  );
}
```

### useResearch (`hooks/useResearch.js`)

React Query mutation for research queries:

```javascript
import { useResearch } from '@hooks/useResearch';

function ResearchView() {
  const { ask, answer, references, isLoading, reset } = useResearch();

  const handleSubmit = async (query) => {
    await ask(query);
  };

  return (
    <div>
      {answer && <AnswerDisplay answer={answer} references={references} />}
    </div>
  );
}
```

### useClipboard (`hooks/useClipboard.js`)

Clipboard operations with automatic feedback reset:

```javascript
import { useClipboard } from '@hooks/useClipboard';

function CopyButton({ text }) {
  const { copy, isCopied } = useClipboard();

  return (
    <button onClick={() => copy(text)}>
      {isCopied ? 'Copied!' : 'Copy'}
    </button>
  );
}
```

**Features**:
- Modern Clipboard API with fallback to `execCommand`
- Auto-resets `isCopied` after 2 seconds

### useKeyboardNav (`hooks/useKeyboardNav.js`)

Keyboard navigation handler:

```javascript
import { useKeyboardNav } from '@hooks/useKeyboardNav';

function Slideshow({ currentPage, onPageChange }) {
  useKeyboardNav({
    onArrowLeft: () => onPageChange(currentPage - 1),
    onArrowRight: () => onPageChange(currentPage + 1),
    onEscape: () => onPageChange(1)
  });

  return <div>Page {currentPage}</div>;
}
```

**Features**:
- Ignores events when focus is in input/textarea
- Prevents default browser behavior for handled keys
- Can be enabled/disabled

## Integration Points

### With Layout Components (Wave 2)
- `Header.jsx` uses `useDocumentStore` for active filter count
- `ThemeToggle` uses `useThemeStore`
- `ConnectionStatus` uses `useConnectionStore`

### With Library View (Wave 3)
- `LibraryView.jsx` uses `useDocuments` hook
- `FilterBar.jsx` updates `useDocumentStore` filters
- `UploadModal.jsx` uses `api.upload.uploadFile` and `useDocumentStore.addTempDocument`

### With Details View (Wave 4)
- `DetailsView.jsx` uses `useDocumentDetails` hook
- `Slideshow.jsx` uses `useKeyboardNav` hook

### With Research View (Wave 5)
- `ResearchView.jsx` uses `useResearch` hook
- `AnswerDisplay.jsx` uses `useClipboard` hook

## React Query Configuration

All hooks use a shared `QueryClient` configuration:

```javascript
// App.jsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,          // 30 seconds
      cacheTime: 5 * 60 * 1000,  // 5 minutes
      refetchOnWindowFocus: true,
      retry: 1
    },
    mutations: {
      retry: 0
    }
  }
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      {/* routes */}
    </QueryClientProvider>
  );
}
```

## Validation

All deliverables have been validated:

```
✅ Services (3/3): api.js, websocket.js, research.js
✅ Stores (3/3): useConnectionStore, useThemeStore, useDocumentStore
✅ Hooks (6/6): useWebSocket, useDocuments, useDocumentDetails, useResearch, useClipboard, useKeyboardNav
✅ Contract compliance: All exports match specifications
✅ Error handling: Standardized APIError class
✅ Persistence: Theme and filters persisted to localStorage
✅ Cleanup: All hooks clean up on unmount
```

## Next Steps

Wave 1 is complete. The infrastructure is ready for Wave 2 (layout-agent) to begin building React components that consume these services, stores, and hooks.

## Contract References

- `integration-contracts/api-service.contract.md`
- `integration-contracts/stores.contract.md`
- `integration-contracts/hooks.contract.md`

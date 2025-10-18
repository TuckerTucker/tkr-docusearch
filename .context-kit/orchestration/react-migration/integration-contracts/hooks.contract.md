# Custom Hooks Integration Contract

**Provider:** infrastructure-agent
**Consumers:** All view agents (library-agent, details-agent, research-agent)
**Technology:** React Query + Custom Hooks

---

## Contract Overview

Custom hooks abstract data fetching, WebSocket communication, and complex stateful logic. They provide a consistent interface for React components to access server data and real-time updates.

---

## Hook 1: useWebSocket

**File:** `frontend/src/hooks/useWebSocket.js`
**Purpose:** Manage WebSocket connection with automatic reconnection

### Hook Signature

```typescript
useWebSocket(url: string, options?: {
  onMessage?: (event: MessageEvent) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  reconnectInterval?: number;  // Default: 3000ms
  maxReconnectAttempts?: number;  // Default: 10
}): {
  send: (data: string | object) => void;
  isConnected: boolean;
  reconnectAttempts: number;
}
```

### Usage Example

```javascript
import { useWebSocket } from '@hooks/useWebSocket';
import { useConnectionStore } from '@stores/useConnectionStore';

function useRealtimeUpdates() {
  const setConnected = useConnectionStore((state) => state.setConnected);
  const setDisconnected = useConnectionStore((state) => state.setDisconnected);

  const { send, isConnected } = useWebSocket('ws://localhost:8002/ws', {
    onMessage: (event) => {
      const data = JSON.parse(event.data);
      console.log('WebSocket message:', data);
      // Handle document status updates
    },
    onOpen: () => {
      console.log('WebSocket connected');
      setConnected();
    },
    onClose: () => {
      console.log('WebSocket disconnected');
      setDisconnected();
    }
  });

  return { send, isConnected };
}
```

### Implementation Requirements

- ✅ Automatically reconnect with exponential backoff
- ✅ Clean up on unmount (close connection)
- ✅ Update connection store on state changes
- ✅ JSON.stringify objects before sending
- ✅ Prevent reconnect on intentional close

### Reconnection Logic

```javascript
// Exponential backoff: 1s, 2s, 4s, 8s, ..., max 30s
const delay = Math.min(1000 * Math.pow(2, attempts), 30000);
```

---

## Hook 2: useDocuments

**File:** `frontend/src/hooks/useDocuments.js`
**Purpose:** Fetch and cache document list with React Query

### Hook Signature

```typescript
useDocuments(filters: {
  search?: string;
  sortBy?: string;
  fileTypeGroup?: string;
  limit?: number;
  offset?: number;
}): {
  documents: Document[];
  totalCount: number;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
  deleteDocument: (docId: string) => Promise<void>;
}
```

### Usage Example

```javascript
import { useDocuments } from '@hooks/useDocuments';
import { useDocumentStore } from '@stores/useDocumentStore';

function LibraryView() {
  const filters = useDocumentStore((state) => state.filters);
  const { documents, totalCount, isLoading, deleteDocument } = useDocuments(filters);

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      {documents.map((doc) => (
        <DocumentCard
          key={doc.doc_id}
          document={doc}
          onDelete={() => deleteDocument(doc.doc_id)}
        />
      ))}
    </div>
  );
}
```

### Implementation Requirements

- ✅ Use `useQuery` from React Query
- ✅ Query key: `['documents', filters]` (enables automatic caching per filter combination)
- ✅ Stale time: 30 seconds (reduces unnecessary refetches)
- ✅ `deleteDocument` uses `useMutation` with optimistic updates
- ✅ On delete: immediately remove from cache, rollback on error
- ✅ Refetch on window focus (default React Query behavior)

### Optimistic Delete Implementation

```javascript
const deleteMutation = useMutation({
  mutationFn: (docId) => api.documents.delete(docId),
  onMutate: async (docId) => {
    // Cancel outgoing refetches
    await queryClient.cancelQueries(['documents']);

    // Snapshot current data
    const previous = queryClient.getQueryData(['documents', filters]);

    // Optimistically update
    queryClient.setQueryData(['documents', filters], (old) => ({
      ...old,
      documents: old.documents.filter((doc) => doc.doc_id !== docId),
      total: old.total - 1
    }));

    return { previous };
  },
  onError: (err, docId, context) => {
    // Rollback on error
    queryClient.setQueryData(['documents', filters], context.previous);
  },
  onSettled: () => {
    // Refetch to sync with server
    queryClient.invalidateQueries(['documents']);
  }
});
```

---

## Hook 3: useDocumentDetails

**File:** `frontend/src/hooks/useDocumentDetails.js`
**Purpose:** Fetch document metadata and markdown content

### Hook Signature

```typescript
useDocumentDetails(docId: string): {
  document: Document | null;
  markdown: { sections: Section[] } | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}
```

### Usage Example

```javascript
import { useDocumentDetails } from '@hooks/useDocumentDetails';
import { useParams } from 'react-router-dom';

function DetailsView() {
  const { id } = useParams();
  const { document, markdown, isLoading } = useDocumentDetails(id);

  if (isLoading) return <div>Loading document...</div>;
  if (!document) return <div>Document not found</div>;

  return (
    <div>
      <Slideshow document={document} />
      <Accordion sections={markdown.sections} />
    </div>
  );
}
```

### Implementation Requirements

- ✅ Use `useQueries` to fetch document + markdown in parallel
- ✅ Query keys: `['document', docId]` and `['markdown', docId]`
- ✅ Stale time: 5 minutes (document metadata changes rarely)
- ✅ Enable query only if `docId` is truthy
- ✅ Return combined loading state (loading if either query is loading)

---

## Hook 4: useResearch

**File:** `frontend/src/hooks/useResearch.js`
**Purpose:** Submit research queries with caching

### Hook Signature

```typescript
useResearch(): {
  ask: (query: string) => Promise<void>;
  answer: string | null;
  references: Reference[];
  isLoading: boolean;
  error: Error | null;
  reset: () => void;
}
```

### Usage Example

```javascript
import { useResearch } from '@hooks/useResearch';

function ResearchView() {
  const { ask, answer, references, isLoading, error } = useResearch();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const query = e.target.query.value;
    await ask(query);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input name="query" placeholder="Ask a question..." />
      <button type="submit">Ask</button>

      {isLoading && <div>Researching...</div>}
      {answer && <AnswerDisplay answer={answer} references={references} />}
      {error && <div>Error: {error.message}</div>}
    </form>
  );
}
```

### Implementation Requirements

- ✅ Use `useMutation` from React Query
- ✅ Cache recent queries (query key: `['research', query]`)
- ✅ Timeout: 30 seconds (LLM can be slow)
- ✅ `reset()` clears answer and references (for new query)
- ✅ Store last query/answer in mutation state

---

## Hook 5: useClipboard

**File:** `frontend/src/hooks/useClipboard.js`
**Purpose:** Copy text to clipboard with feedback

### Hook Signature

```typescript
useClipboard(): {
  copy: (text: string) => Promise<void>;
  isCopied: boolean;
  error: Error | null;
}
```

### Usage Example

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

### Implementation Requirements

- ✅ Use Clipboard API (`navigator.clipboard.writeText`)
- ✅ Fallback to `document.execCommand('copy')` for older browsers
- ✅ `isCopied` auto-resets to `false` after 2 seconds
- ✅ Handle permission errors gracefully

---

## Hook 6: useKeyboardNav

**File:** `frontend/src/hooks/useKeyboardNav.js`
**Purpose:** Handle keyboard navigation (arrow keys, Escape, Enter, etc.)

### Hook Signature

```typescript
useKeyboardNav(config: {
  onArrowLeft?: () => void;
  onArrowRight?: () => void;
  onArrowUp?: () => void;
  onArrowDown?: () => void;
  onEscape?: () => void;
  onEnter?: () => void;
  enabled?: boolean;  // Default: true
}): void
```

### Usage Example

```javascript
import { useKeyboardNav } from '@hooks/useKeyboardNav';

function Slideshow({ currentPage, totalPages, onPageChange }) {
  useKeyboardNav({
    onArrowLeft: () => onPageChange(Math.max(1, currentPage - 1)),
    onArrowRight: () => onPageChange(Math.min(totalPages, currentPage + 1))
  });

  return <div>Page {currentPage} of {totalPages}</div>;
}
```

### Implementation Requirements

- ✅ Use `useEffect` with event listener on `document`
- ✅ Clean up on unmount
- ✅ Disable when `enabled: false`
- ✅ Prevent default browser behavior (scrolling) for handled keys
- ✅ Don't trigger if focus is in input/textarea

---

## React Query Configuration

All hooks use a shared QueryClient configuration:

```javascript
// App.jsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,  // 30 seconds
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

---

## Testing Requirements

Each hook must provide:
- ✅ Mock implementation for testing
- ✅ Unit tests with React Testing Library's `renderHook`
- ✅ Test loading, success, and error states
- ✅ Test cleanup on unmount

Example test:

```javascript
import { renderHook, waitFor } from '@testing-library/react';
import { useDocuments } from './useDocuments';

test('useDocuments fetches documents', async () => {
  const { result } = renderHook(() => useDocuments({ search: 'test' }));

  expect(result.current.isLoading).toBe(true);

  await waitFor(() => {
    expect(result.current.documents).toHaveLength(3);
  });

  expect(result.current.isLoading).toBe(false);
});
```

---

## Validation Checklist

- [ ] All 6 hooks implemented with documented API
- [ ] React Query configuration matches specification
- [ ] Optimistic updates working for mutations
- [ ] Error handling consistent across hooks
- [ ] Loading states accurate
- [ ] Cleanup on unmount prevents memory leaks
- [ ] Test utilities provided
- [ ] JSDoc annotations complete

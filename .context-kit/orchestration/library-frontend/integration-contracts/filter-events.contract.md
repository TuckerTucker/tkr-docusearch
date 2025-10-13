# Filter Bar Events Contract

**Provider**: `filter-bar.js` (Agent 4)
**Consumer**: `library-manager.js` (Agent 2)
**Communication**: DOM Custom Events

---

## Event System

FilterBar emits custom events when filters change. LibraryManager listens and re-queries the Documents API.

---

## Event 1: filterChange

### **Event Name**
```javascript
'filterChange'
```

### **Dispatched When**
- User changes search input (after 300ms debounce)
- User selects different sort option
- User checks/unchecks file type filter
- User clicks "Clear Filters" button

---

### **Event Detail Schema**

```javascript
event.detail = {
  search: string,      // Search query or empty string
  sort_by: string,     // Sort field: 'date_added', 'filename', 'page_count'
  file_types: array,   // Selected file types: ['pdf', 'docx', 'pptx', 'audio']
  limit: number,       // Results per page (default: 50)
  offset: number       // Pagination offset (default: 0)
}
```

---

### **Example Event Detail**

```javascript
// User searches for "report" and sorts by date
{
  search: 'report',
  sort_by: 'date_added',
  file_types: ['pdf', 'docx', 'pptx', 'audio'],
  limit: 50,
  offset: 0
}
```

```javascript
// User filters for PDFs only, sorted by filename
{
  search: '',
  sort_by: 'filename',
  file_types: ['pdf'],
  limit: 50,
  offset: 0
}
```

```javascript
// User clears all filters
{
  search: '',
  sort_by: 'date_added',
  file_types: ['pdf', 'docx', 'pptx', 'audio'],
  limit: 50,
  offset: 0
}
```

---

## Event 2: pageChange

### **Event Name**
```javascript
'pageChange'
```

### **Dispatched When**
- User clicks "Next" or "Previous" pagination button
- User clicks specific page number

---

### **Event Detail Schema**

```javascript
event.detail = {
  offset: number,      // New pagination offset
  limit: number        // Results per page (unchanged)
}
```

---

### **Example Event Detail**

```javascript
// User clicks "Next" (page 2)
{
  offset: 50,
  limit: 50
}
```

```javascript
// User clicks "Previous" (back to page 1)
{
  offset: 0,
  limit: 50
}
```

---

## FilterBar Implementation (Provider)

### **Class Interface**

```javascript
class FilterBar {
  constructor(containerSelector) {
    this.container = document.querySelector(containerSelector);
    this.state = {
      search: '',
      sort_by: 'date_added',
      file_types: ['pdf', 'docx', 'pptx', 'audio'],
      limit: 50,
      offset: 0
    };
    this.init();
  }

  init() {
    // Render filter UI
    // Attach event listeners
    // Initialize URL state from query params
  }

  handleSearchInput(value) {
    // Debounce 300ms
    // Update state.search
    // Emit filterChange
  }

  handleSortChange(value) {
    // Update state.sort_by
    // Emit filterChange
  }

  handleFileTypeToggle(fileType, checked) {
    // Update state.file_types
    // Emit filterChange
  }

  clearFilters() {
    // Reset state to defaults
    // Update UI
    // Emit filterChange
  }

  emitFilterChange() {
    const event = new CustomEvent('filterChange', {
      detail: { ...this.state },
      bubbles: true
    });
    this.container.dispatchEvent(event);
  }

  emitPageChange(offset) {
    const event = new CustomEvent('pageChange', {
      detail: { offset, limit: this.state.limit },
      bubbles: true
    });
    this.container.dispatchEvent(event);
  }

  updateUrlParams() {
    // Update URL query params for bookmarking
    const params = new URLSearchParams();
    if (this.state.search) params.set('search', this.state.search);
    if (this.state.sort_by !== 'date_added') params.set('sort_by', this.state.sort_by);
    if (this.state.offset > 0) params.set('offset', this.state.offset);
    // ... update URL without reload
    history.pushState(null, '', `?${params.toString()}`);
  }
}
```

---

## LibraryManager Implementation (Consumer)

### **Event Listener Setup**

```javascript
class LibraryManager {
  constructor() {
    this.filterBar = new FilterBar('#filter-bar');
    this.currentQuery = {
      search: '',
      sort_by: 'date_added',
      file_types: ['pdf', 'docx', 'pptx', 'audio'],
      limit: 50,
      offset: 0
    };
    this.attachEventListeners();
  }

  attachEventListeners() {
    // Listen for filter changes
    document.addEventListener('filterChange', (event) => {
      this.handleFilterChange(event.detail);
    });

    // Listen for pagination changes
    document.addEventListener('pageChange', (event) => {
      this.handlePageChange(event.detail);
    });
  }

  async handleFilterChange(detail) {
    // Update current query
    this.currentQuery = { ...detail };

    // Show loading state
    this.showLoadingState();

    try {
      // Re-query API with new filters
      const response = await this.apiClient.listDocuments({
        limit: detail.limit,
        offset: detail.offset,
        search: detail.search || null,
        sort_by: detail.sort_by
      });

      // Filter by file type (client-side, since API doesn't support it)
      let documents = response.documents;
      if (detail.file_types.length < 4) {
        documents = documents.filter(doc => {
          const ext = doc.filename.split('.').pop().toLowerCase();
          return detail.file_types.includes(ext) ||
                 (detail.file_types.includes('audio') && ['mp3', 'wav', 'm4a'].includes(ext));
        });
      }

      // Re-render grid
      this.renderDocuments(documents);

      // Update pagination
      this.updatePagination(response.total, detail.limit, detail.offset);

    } catch (error) {
      this.showErrorState(error);
    }
  }

  async handlePageChange(detail) {
    // Update offset
    this.currentQuery.offset = detail.offset;

    // Re-query with same filters, new offset
    await this.handleFilterChange(this.currentQuery);

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}
```

---

## URL State Management

### **URL Query Parameters**

FilterBar should sync state to URL for bookmarking:

```
/frontend/?search=report&sort_by=filename&offset=50
```

**Parameters**:
- `search` - Search query (if not empty)
- `sort_by` - Sort field (if not default 'date_added')
- `offset` - Pagination offset (if not 0)
- `file_types` - Selected types (future enhancement)

**On Page Load**:
FilterBar should read URL params and initialize state accordingly.

---

## Testing Requirements

### **Provider Validation** (Agent 4)
- [ ] Search input emits `filterChange` after 300ms debounce
- [ ] Sort dropdown emits `filterChange` immediately
- [ ] File type checkboxes emit `filterChange` immediately
- [ ] Clear button resets state and emits `filterChange`
- [ ] Event detail contains all required fields
- [ ] URL params update on state change
- [ ] URL params initialize state on page load
- [ ] Pagination buttons emit `pageChange`

### **Consumer Validation** (Agent 2)
- [ ] LibraryManager receives `filterChange` events
- [ ] API re-queried with correct parameters
- [ ] Grid re-renders with filtered documents
- [ ] Loading state shown during query
- [ ] Error state shown on failure
- [ ] Page change scrolls to top

---

## Debounce Configuration

**Search Input Debounce**: 300ms

**Rationale**:
- Prevents excessive API calls while typing
- Good balance between responsiveness and efficiency
- Users typically pause typing for ~250-350ms

**Implementation**:
```javascript
let searchTimeout;
searchInput.addEventListener('input', (e) => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    this.handleSearchInput(e.target.value);
  }, 300);
});
```

---

## File Type Filtering

**Note**: Documents API does not support file type filtering.

**Strategy**:
1. FilterBar emits all selected file types in event detail
2. LibraryManager queries API normally
3. LibraryManager filters results client-side based on file extension

**File Type Mapping**:
```javascript
const FILE_TYPE_EXTENSIONS = {
  pdf: ['pdf'],
  docx: ['docx', 'doc'],
  pptx: ['pptx', 'ppt'],
  audio: ['mp3', 'wav', 'flac', 'm4a', 'aac']
};
```

**Future Enhancement**: Add file type filter to Documents API for server-side filtering.

---

## Example Full Flow

```javascript
// 1. User types "report" in search box
//    (FilterBar debounces 300ms)

// 2. FilterBar emits event
const event = new CustomEvent('filterChange', {
  detail: {
    search: 'report',
    sort_by: 'date_added',
    file_types: ['pdf', 'docx', 'pptx', 'audio'],
    limit: 50,
    offset: 0
  }
});

// 3. LibraryManager receives event
handleFilterChange(detail) {
  // Show loading spinner
  this.showLoadingState();

  // Query API
  const response = await this.apiClient.listDocuments({
    search: 'report',
    sort_by: 'date_added',
    limit: 50,
    offset: 0
  });

  // Render results
  this.renderDocuments(response.documents);
}

// 4. User clicks "Next" for page 2
const pageEvent = new CustomEvent('pageChange', {
  detail: { offset: 50, limit: 50 }
});

// 5. LibraryManager queries page 2 with same filters
handlePageChange(detail) {
  this.currentQuery.offset = 50;
  await this.handleFilterChange(this.currentQuery);
  window.scrollTo({ top: 0, behavior: 'smooth' });
}
```

---

## Change Log

- 2025-10-13: Initial contract specification
- Status: **DRAFT** (to be implemented in Wave 1)

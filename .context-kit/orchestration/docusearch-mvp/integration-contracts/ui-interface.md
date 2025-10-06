# UI Interface Contract

**Owner**: ui-agent
**Consumers**: End users (browser)
**Providers**: search-agent, processing-agent (via status files)
**Purpose**: Define web UI components, API endpoints, and user interactions

---

## UI Components

### 1. Search Page

**File**: `src/ui/search.html`

**Purpose**: Primary interface for document search

**Sections**:
- Header with branding and navigation
- Search query input form
- Search mode selector (hybrid, visual, text)
- Filters panel (date range, filename, page range)
- Results display area
- Result preview modal

---

## Search Form

### Query Input

```html
<form id="search-form">
  <!-- Query input -->
  <div class="query-input">
    <label for="query">Search Query</label>
    <input
      type="text"
      id="query"
      name="query"
      placeholder="Enter search query (e.g., 'quarterly revenue growth')"
      required
      minlength="2"
      maxlength="500"
    />
    <button type="submit">Search</button>
  </div>

  <!-- Search mode selector -->
  <div class="search-mode">
    <label>Search Mode</label>
    <select id="search-mode" name="search_mode">
      <option value="hybrid" selected>Hybrid (Visual + Text)</option>
      <option value="visual">Visual Only</option>
      <option value="text">Text Only</option>
    </select>
  </div>

  <!-- Number of results -->
  <div class="result-count">
    <label for="n-results">Results</label>
    <select id="n-results" name="n_results">
      <option value="5">5</option>
      <option value="10" selected>10</option>
      <option value="20">20</option>
      <option value="50">50</option>
    </select>
  </div>
</form>
```

---

## Filters Panel

### Filter Options

```html
<div id="filters-panel" class="filters">
  <h3>Filters</h3>

  <!-- Date range filter -->
  <div class="filter-group">
    <label>Date Range</label>
    <input type="date" id="date-start" name="date_start" />
    <span>to</span>
    <input type="date" id="date-end" name="date_end" />
  </div>

  <!-- Filename filter -->
  <div class="filter-group">
    <label for="filename">Filename Contains</label>
    <input
      type="text"
      id="filename"
      name="filename"
      placeholder="e.g., 'Q3-2023'"
    />
  </div>

  <!-- Page range filter -->
  <div class="filter-group">
    <label>Page Range</label>
    <input type="number" id="page-min" name="page_min" min="1" placeholder="From" />
    <span>to</span>
    <input type="number" id="page-max" name="page_max" min="1" placeholder="To" />
  </div>

  <!-- Document type filter -->
  <div class="filter-group">
    <label>Document Type</label>
    <div class="checkbox-group">
      <label><input type="checkbox" name="type" value="pdf" checked /> PDF</label>
      <label><input type="checkbox" name="type" value="docx" checked /> DOCX</label>
      <label><input type="checkbox" name="type" value="pptx" checked /> PPTX</label>
    </div>
  </div>

  <!-- Clear filters button -->
  <button type="button" id="clear-filters">Clear Filters</button>
</div>
```

---

## Search API Integration

### API Endpoint

**URL**: `http://localhost:8000/api/search/query`
**Method**: POST
**Content-Type**: application/json

### Request Format

```typescript
interface SearchRequest {
  query: string;                      // Search query text (required)
  n_results: number;                  // Number of results to return (default: 10)
  search_mode?: 'hybrid' | 'visual' | 'text';  // Search type (default: 'hybrid')
  filters?: {
    date_range?: {
      start: string;                  // ISO 8601 date (YYYY-MM-DD)
      end: string;                    // ISO 8601 date (YYYY-MM-DD)
    };
    filename?: string;                // Substring match on filename
    page_range?: {
      min: number;                    // Minimum page number (1-indexed)
      max: number;                    // Maximum page number (1-indexed)
    };
    document_types?: string[];        // ['pdf', 'docx', 'pptx']
  };
}
```

### Response Format

```typescript
interface SearchResponse {
  query: string;                      // Original query
  total_results: number;              // Total matching documents
  results: SearchResult[];            // Top N results
  search_mode: string;                // Mode used for search
  timing: {
    stage1_ms: number;                // Stage 1 retrieval time
    stage2_ms: number;                // Stage 2 re-ranking time
    total_ms: number;                 // Total search time
  };
}

interface SearchResult {
  doc_id: string;                     // Unique document identifier
  filename: string;                   // Original filename
  page_num?: number;                  // Page number (visual results)
  chunk_id?: string;                  // Chunk ID (text results)
  score: number;                      // Relevance score (0-1)
  type: 'visual' | 'text';            // Result type
  snippet?: string;                   // Text snippet (text results)
  thumbnail?: string;                 // Base64 image (visual results)
  metadata: {
    upload_date: string;              // ISO 8601 timestamp
    file_size_mb: number;             // File size
    total_pages: number;              // Total pages in document
  };
}
```

---

## Results Display

### Result Card Template

```html
<div class="result-card" data-doc-id="${result.doc_id}" data-page="${result.page_num}">
  <!-- Result header -->
  <div class="result-header">
    <span class="result-type ${result.type}">${result.type}</span>
    <span class="result-score">Score: ${(result.score * 100).toFixed(1)}%</span>
  </div>

  <!-- Result content -->
  <div class="result-content">
    <!-- Visual result: show thumbnail -->
    ${result.type === 'visual' ?
      `<img src="data:image/png;base64,${result.thumbnail}"
            alt="Page ${result.page_num}"
            class="result-thumbnail" />`
      : ''}

    <!-- Text result: show snippet -->
    ${result.type === 'text' ?
      `<p class="result-snippet">${highlightQuery(result.snippet, query)}</p>`
      : ''}
  </div>

  <!-- Result footer -->
  <div class="result-footer">
    <div class="result-meta">
      <strong>${result.filename}</strong>
      ${result.page_num ? `Page ${result.page_num}` : ''}
      <span class="upload-date">${formatDate(result.metadata.upload_date)}</span>
    </div>
    <button class="preview-btn" onclick="openPreview('${result.doc_id}', ${result.page_num})">
      Preview
    </button>
  </div>
</div>
```

---

## Result Preview Modal

### Modal Structure

```html
<div id="preview-modal" class="modal" style="display: none;">
  <div class="modal-overlay" onclick="closePreview()"></div>

  <div class="modal-content">
    <!-- Modal header -->
    <div class="modal-header">
      <h2 id="preview-title">Document Preview</h2>
      <button class="close-btn" onclick="closePreview()">×</button>
    </div>

    <!-- Modal body -->
    <div class="modal-body">
      <!-- Document info -->
      <div class="preview-info">
        <strong id="preview-filename">filename.pdf</strong>
        <span id="preview-page">Page 1 of 10</span>
      </div>

      <!-- Page image -->
      <div class="preview-image-container">
        <img id="preview-image" src="" alt="Document page" />
      </div>

      <!-- Page navigation -->
      <div class="preview-navigation">
        <button id="prev-page" onclick="navigatePage(-1)">← Previous</button>
        <span id="page-indicator">1 / 10</span>
        <button id="next-page" onclick="navigatePage(1)">Next →</button>
      </div>

      <!-- Text content -->
      <div class="preview-text">
        <h3>Page Text</h3>
        <pre id="preview-text-content"></pre>
      </div>
    </div>

    <!-- Modal footer -->
    <div class="modal-footer">
      <button onclick="downloadDocument()">Download Document</button>
      <button onclick="closePreview()">Close</button>
    </div>
  </div>
</div>
```

### Preview API

**Endpoint**: `/api/preview/{doc_id}/{page_num}`
**Method**: GET

**Response**:
```json
{
  "doc_id": "uuid",
  "filename": "Q3-2023-Earnings.pdf",
  "page_num": 5,
  "total_pages": 25,
  "image": "base64-encoded-png",
  "text": "Full page text content...",
  "metadata": {
    "upload_date": "2023-10-06T14:30:00Z",
    "file_size_mb": 2.5
  }
}
```

---

## Status Dashboard

**File**: `src/ui/status_dashboard.html`

**Purpose**: Monitor document processing queue and status

### Dashboard Components

```html
<div id="status-dashboard">
  <!-- Queue statistics -->
  <div class="queue-stats">
    <div class="stat-card">
      <h3>Queue Size</h3>
      <span id="queue-size" class="stat-value">0</span>
    </div>
    <div class="stat-card">
      <h3>Processing</h3>
      <span id="processing-count" class="stat-value">0</span>
    </div>
    <div class="stat-card">
      <h3>Completed Today</h3>
      <span id="completed-today" class="stat-value">0</span>
    </div>
    <div class="stat-card">
      <h3>Failed Today</h3>
      <span id="failed-today" class="stat-value error">0</span>
    </div>
  </div>

  <!-- Current processing -->
  <div class="current-processing">
    <h3>Currently Processing</h3>
    <div id="current-doc" class="processing-item" style="display: none;">
      <div class="doc-info">
        <strong id="current-filename">filename.pdf</strong>
        <span id="current-stage">Parsing document...</span>
      </div>
      <div class="progress-bar">
        <div id="progress-fill" class="progress-fill" style="width: 0%"></div>
      </div>
      <div class="progress-text">
        <span id="progress-percent">0%</span>
        <span id="eta">ETA: 1m 30s</span>
      </div>
    </div>
  </div>

  <!-- Recent documents -->
  <div class="recent-documents">
    <h3>Recent Documents</h3>
    <table id="recent-docs-table">
      <thead>
        <tr>
          <th>Filename</th>
          <th>Status</th>
          <th>Pages</th>
          <th>Processing Time</th>
          <th>Uploaded</th>
        </tr>
      </thead>
      <tbody id="recent-docs-body">
        <!-- Populated dynamically -->
      </tbody>
    </table>
  </div>
</div>
```

### Status API

**Endpoint**: `/api/status`
**Method**: GET

**Response**:
```json
{
  "queue": {
    "size": 3,
    "processing": 1,
    "completed_today": 15,
    "failed_today": 1,
    "avg_processing_time_seconds": 87,
    "estimated_wait_time_seconds": 261
  },
  "current": {
    "doc_id": "uuid",
    "filename": "Q3-2023-Earnings.pdf",
    "status": "embedding_visual",
    "progress": 0.65,
    "stage": "Processing page 13 of 20",
    "elapsed_seconds": 45,
    "estimated_remaining_seconds": 24
  },
  "recent": [
    {
      "doc_id": "uuid",
      "filename": "Contract-2023.pdf",
      "status": "completed",
      "total_pages": 50,
      "processing_time_seconds": 320,
      "upload_timestamp": "2023-10-06T14:15:00Z"
    }
  ]
}
```

---

## JavaScript API Client

### Search API Client

```javascript
// src/ui/search.js

class SearchAPIClient {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }

  async search(query, options = {}) {
    const request = {
      query,
      n_results: options.n_results || 10,
      search_mode: options.search_mode || 'hybrid',
      filters: options.filters || {}
    };

    const response = await fetch(`${this.baseURL}/api/search/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      throw new Error(`Search failed: ${response.statusText}`);
    }

    return await response.json();
  }

  async preview(docId, pageNum) {
    const response = await fetch(
      `${this.baseURL}/api/preview/${docId}/${pageNum}`
    );

    if (!response.ok) {
      throw new Error(`Preview failed: ${response.statusText}`);
    }

    return await response.json();
  }

  async getStatus() {
    const response = await fetch(`${this.baseURL}/api/status`);

    if (!response.ok) {
      throw new Error(`Status check failed: ${response.statusText}`);
    }

    return await response.json();
  }
}

// Initialize API client
const searchAPI = new SearchAPIClient();
```

---

## Event Handlers

### Search Form Submission

```javascript
document.getElementById('search-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const query = document.getElementById('query').value.trim();
  if (!query) return;

  // Show loading state
  showLoading();

  try {
    // Gather form data
    const searchMode = document.getElementById('search-mode').value;
    const nResults = parseInt(document.getElementById('n-results').value);
    const filters = collectFilters();

    // Execute search
    const results = await searchAPI.search(query, {
      search_mode: searchMode,
      n_results: nResults,
      filters
    });

    // Display results
    displayResults(results);

    // Update search stats
    updateSearchStats(results.timing);

  } catch (error) {
    showError(`Search failed: ${error.message}`);
  } finally {
    hideLoading();
  }
});
```

### Real-time Status Updates

```javascript
// Poll status every 5 seconds
let statusInterval;

function startStatusPolling() {
  statusInterval = setInterval(async () => {
    try {
      const status = await searchAPI.getStatus();
      updateDashboard(status);
    } catch (error) {
      console.error('Status update failed:', error);
    }
  }, 5000);
}

function stopStatusPolling() {
  if (statusInterval) {
    clearInterval(statusInterval);
    statusInterval = null;
  }
}

// Start polling when dashboard is visible
if (document.getElementById('status-dashboard')) {
  startStatusPolling();
}
```

---

## UI Styling

### CSS Framework

**Approach**: Custom CSS with CSS variables for theming

```css
/* src/ui/styles.css */

:root {
  /* Colors */
  --primary-color: #2563eb;
  --success-color: #10b981;
  --error-color: #ef4444;
  --text-color: #1f2937;
  --bg-color: #ffffff;
  --border-color: #e5e7eb;

  /* Spacing */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;

  /* Typography */
  --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
}

/* Layout */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--spacing-lg);
}

/* Result cards */
.result-card {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-md);
  transition: box-shadow 0.2s;
}

.result-card:hover {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
```

---

## Accessibility

### WCAG 2.1 AA Compliance

**Requirements**:
- Keyboard navigation support
- Screen reader compatibility
- Sufficient color contrast (4.5:1 minimum)
- Focus indicators visible
- ARIA labels for interactive elements
- Alt text for images

**Example**:
```html
<button
  class="preview-btn"
  onclick="openPreview('${result.doc_id}', ${result.page_num})"
  aria-label="Preview ${result.filename} page ${result.page_num}"
>
  Preview
</button>
```

---

## Error Handling

### User-Facing Error Messages

```javascript
function showError(message, type = 'error') {
  const errorDiv = document.createElement('div');
  errorDiv.className = `alert alert-${type}`;
  errorDiv.textContent = message;
  errorDiv.setAttribute('role', 'alert');

  document.querySelector('.container').prepend(errorDiv);

  // Auto-dismiss after 5 seconds
  setTimeout(() => errorDiv.remove(), 5000);
}

// Error scenarios
const ERROR_MESSAGES = {
  SEARCH_FAILED: 'Search request failed. Please try again.',
  NO_RESULTS: 'No results found for your query. Try different search terms.',
  PREVIEW_FAILED: 'Unable to load preview. The document may have been deleted.',
  STATUS_UNAVAILABLE: 'Processing status unavailable. Check back later.',
  NETWORK_ERROR: 'Network error. Please check your connection.'
};
```

---

## Testing Requirements

### UI Tests

- Form validation (empty query, invalid filters)
- Search API integration (success, error cases)
- Results display (visual, text, hybrid)
- Preview modal (open, navigate, close)
- Status dashboard updates
- Filter application and clearing
- Keyboard navigation
- Screen reader compatibility

### Mock API Responses (Wave 2)

```javascript
// Mock search response for development
const MOCK_SEARCH_RESPONSE = {
  query: "revenue growth",
  total_results: 42,
  results: [
    {
      doc_id: "mock-uuid-1",
      filename: "Q3-2023-Earnings.pdf",
      page_num: 5,
      score: 0.92,
      type: "visual",
      thumbnail: "base64-encoded-image",
      metadata: {
        upload_date: "2023-10-06T10:00:00Z",
        file_size_mb: 2.5,
        total_pages: 25
      }
    }
  ],
  search_mode: "hybrid",
  timing: {
    stage1_ms: 180,
    stage2_ms: 95,
    total_ms: 275
  }
};
```

---

## Contract Version

**Version**: 1.0
**Last Updated**: 2025-10-06
**Status**: Draft (pending Wave 1 review)

---

## Notes

- UI served via copyparty's web server (`/www` directory)
- Search API proxied through copyparty or direct to processing-worker
- Real-time updates via polling (WebSocket upgrade in future)
- Responsive design for mobile/tablet/desktop
- Progressive enhancement (works without JavaScript for basic upload)
- Status dashboard optional (can be hidden for simple deployments)

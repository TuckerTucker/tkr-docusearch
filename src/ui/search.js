/**
 * DocuSearch - Search Interface JavaScript
 * Wave 2: Mock API Implementation
 */

// ============================================================================
// Mock Data Generator
// ============================================================================

/**
 * Generate mock base64 thumbnail (simple colored rectangle)
 */
function generateMockThumbnail(color = '#3b82f6') {
  // Create a simple SVG as base64
  const svg = `<svg width="200" height="250" xmlns="http://www.w3.org/2000/svg">
    <rect width="200" height="250" fill="${color}"/>
    <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="white" font-size="16">
      Document Page Preview
    </text>
  </svg>`;
  return btoa(svg);
}

/**
 * Generate mock search results
 */
function generateMockResults(query, searchMode, nResults) {
  const mockDocuments = [
    { filename: 'Q3-2023-Earnings.pdf', pages: 25, uploadDate: '2023-10-06T10:00:00Z' },
    { filename: 'Annual-Report-2023.pdf', pages: 120, uploadDate: '2023-09-15T14:30:00Z' },
    { filename: 'Marketing-Strategy-Q4.docx', pages: 45, uploadDate: '2023-10-01T09:15:00Z' },
    { filename: 'Product-Roadmap-2024.pptx', pages: 30, uploadDate: '2023-09-28T16:20:00Z' },
    { filename: 'Financial-Summary-Sept.pdf', pages: 15, uploadDate: '2023-09-30T11:45:00Z' },
    { filename: 'Contract-Agreement-ABC.pdf', pages: 50, uploadDate: '2023-08-20T13:00:00Z' },
    { filename: 'Technical-Specifications.pdf', pages: 78, uploadDate: '2023-09-10T10:30:00Z' },
    { filename: 'Meeting-Notes-Sept-2023.docx', pages: 8, uploadDate: '2023-09-25T15:00:00Z' },
    { filename: 'Budget-Proposal-2024.xlsx', pages: 12, uploadDate: '2023-09-18T12:00:00Z' },
    { filename: 'Employee-Handbook-v3.pdf', pages: 95, uploadDate: '2023-08-15T09:00:00Z' }
  ];

  const results = [];
  const actualResults = Math.min(nResults, mockDocuments.length);

  for (let i = 0; i < actualResults; i++) {
    const doc = mockDocuments[i];
    const isVisual = searchMode === 'visual' || (searchMode === 'hybrid' && i % 2 === 0);
    const score = 0.95 - (i * 0.05);
    const pageNum = Math.floor(Math.random() * doc.pages) + 1;

    const result = {
      doc_id: `mock-uuid-${i + 1}`,
      filename: doc.filename,
      score: score,
      type: isVisual ? 'visual' : 'text',
      metadata: {
        upload_date: doc.uploadDate,
        file_size_mb: parseFloat((Math.random() * 5 + 0.5).toFixed(2)),
        total_pages: doc.pages
      }
    };

    if (isVisual) {
      result.page_num = pageNum;
      result.thumbnail = generateMockThumbnail(i % 2 === 0 ? '#3b82f6' : '#8b5cf6');
    } else {
      result.chunk_id = `chunk-${i + 1}`;
      result.snippet = `This is a sample text snippet from ${doc.filename} that matches your query "${query}". The content discusses relevant topics and information that would be useful for your search. This is mock data for Wave 2 development.`;
    }

    results.push(result);
  }

  return results;
}

/**
 * Generate mock preview data
 */
function generateMockPreview(docId, pageNum) {
  return {
    doc_id: docId,
    filename: 'Sample-Document.pdf',
    page_num: pageNum,
    total_pages: 25,
    image: generateMockThumbnail('#10b981'),
    text: `This is the full text content of page ${pageNum}.\n\nThis is mock data for Wave 2 development. In Wave 3, this will be replaced with actual document content extracted from the uploaded PDFs.\n\nThe text would normally contain the complete OCR or extracted text from the document page, allowing users to search within the content and verify that the result matches their query.\n\nAdditional paragraphs would appear here with relevant document content.`,
    metadata: {
      upload_date: '2023-10-06T14:30:00Z',
      file_size_mb: 2.5
    }
  };
}

/**
 * Generate mock status data
 */
function generateMockStatus() {
  return {
    queue: {
      size: Math.floor(Math.random() * 5),
      processing: Math.random() > 0.5 ? 1 : 0,
      completed_today: Math.floor(Math.random() * 20) + 5,
      failed_today: Math.floor(Math.random() * 2),
      avg_processing_time_seconds: 87,
      estimated_wait_time_seconds: 261
    },
    current: Math.random() > 0.5 ? {
      doc_id: 'mock-processing-uuid',
      filename: 'Q3-2023-Earnings.pdf',
      status: 'embedding_visual',
      progress: Math.random(),
      stage: `Processing page ${Math.floor(Math.random() * 20) + 1} of 20`,
      elapsed_seconds: Math.floor(Math.random() * 60) + 10,
      estimated_remaining_seconds: Math.floor(Math.random() * 40) + 10
    } : null,
    recent: [
      {
        doc_id: 'mock-recent-1',
        filename: 'Contract-2023.pdf',
        status: 'completed',
        total_pages: 50,
        processing_time_seconds: 320,
        upload_timestamp: new Date(Date.now() - 3600000).toISOString()
      },
      {
        doc_id: 'mock-recent-2',
        filename: 'Annual-Report.pdf',
        status: 'completed',
        total_pages: 120,
        processing_time_seconds: 840,
        upload_timestamp: new Date(Date.now() - 7200000).toISOString()
      }
    ]
  };
}

// ============================================================================
// Search API Client
// ============================================================================

class SearchAPIClient {
  constructor(baseURL = 'http://localhost:8000', useMockData = true) {
    this.baseURL = baseURL;
    this.useMockData = useMockData;  // Wave 2: Always use mock data
  }

  async search(query, options = {}) {
    // Wave 2: Return mock data
    if (this.useMockData) {
      // Simulate network delay
      await new Promise(resolve => setTimeout(resolve, 300 + Math.random() * 200));

      const results = generateMockResults(
        query,
        options.search_mode || 'hybrid',
        options.n_results || 10
      );

      return {
        query,
        total_results: results.length + Math.floor(Math.random() * 20),
        results,
        search_mode: options.search_mode || 'hybrid',
        search_time_ms: Math.floor(Math.random() * 150) + 150
      };
    }

    // Wave 3: Real API call
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
    // Wave 2: Return mock data
    if (this.useMockData) {
      await new Promise(resolve => setTimeout(resolve, 200));
      return generateMockPreview(docId, pageNum);
    }

    // Wave 3: Real API call
    const response = await fetch(
      `${this.baseURL}/api/preview/${docId}/${pageNum}`
    );

    if (!response.ok) {
      throw new Error(`Preview failed: ${response.statusText}`);
    }

    return await response.json();
  }

  async getStatus() {
    // Wave 2: Return mock data
    if (this.useMockData) {
      await new Promise(resolve => setTimeout(resolve, 100));
      return generateMockStatus();
    }

    // Wave 3: Real API call
    const response = await fetch(`${this.baseURL}/api/status`);

    if (!response.ok) {
      throw new Error(`Status check failed: ${response.statusText}`);
    }

    return await response.json();
  }
}

// Initialize API client (Wave 3: real API connected)
const searchAPI = new SearchAPIClient('http://localhost:8002', false);

// ============================================================================
// UI State Management
// ============================================================================

const state = {
  currentResults: null,
  currentPreview: {
    docId: null,
    pageNum: null,
    totalPages: null
  }
};

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Format date to human-readable string
 */
function formatDate(isoString) {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 60) return `${diffMins} minutes ago`;
  if (diffHours < 24) return `${diffHours} hours ago`;
  if (diffDays < 7) return `${diffDays} days ago`;

  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

/**
 * Highlight query terms in text
 */
function highlightQuery(text, query) {
  if (!query || !text) return text;

  const terms = query.toLowerCase().split(/\s+/);
  let highlighted = text;

  terms.forEach(term => {
    const regex = new RegExp(`(${term})`, 'gi');
    highlighted = highlighted.replace(regex, '<mark>$1</mark>');
  });

  return highlighted;
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
  const container = document.getElementById('alert-container');
  const alert = document.createElement('div');
  alert.className = `alert alert-${type}`;
  alert.setAttribute('role', 'alert');
  alert.textContent = message;

  container.appendChild(alert);

  setTimeout(() => alert.remove(), 5000);
}

/**
 * Show/hide loading indicator
 */
function setLoading(isLoading) {
  const loading = document.getElementById('loading');
  loading.hidden = !isLoading;
}

// ============================================================================
// Filter Management
// ============================================================================

/**
 * Collect filter values from form
 */
function collectFilters() {
  const filters = {};

  // Date range
  const dateStart = document.getElementById('date-start').value;
  const dateEnd = document.getElementById('date-end').value;
  if (dateStart || dateEnd) {
    filters.date_range = {};
    if (dateStart) filters.date_range.start = dateStart;
    if (dateEnd) filters.date_range.end = dateEnd;
  }

  // Filename
  const filename = document.getElementById('filename').value.trim();
  if (filename) {
    filters.filename = filename;
  }

  // Page range
  const pageMin = document.getElementById('page-min').value;
  const pageMax = document.getElementById('page-max').value;
  if (pageMin || pageMax) {
    filters.page_range = {};
    if (pageMin) filters.page_range.min = parseInt(pageMin);
    if (pageMax) filters.page_range.max = parseInt(pageMax);
  }

  // Document types
  const checkedTypes = Array.from(
    document.querySelectorAll('input[name="type"]:checked')
  ).map(cb => cb.value);
  if (checkedTypes.length > 0 && checkedTypes.length < 3) {
    filters.document_types = checkedTypes;
  }

  return filters;
}

/**
 * Clear all filters
 */
function clearFilters() {
  document.getElementById('date-start').value = '';
  document.getElementById('date-end').value = '';
  document.getElementById('filename').value = '';
  document.getElementById('page-min').value = '';
  document.getElementById('page-max').value = '';

  document.querySelectorAll('input[name="type"]').forEach(cb => {
    cb.checked = true;
  });
}

// ============================================================================
// Results Display
// ============================================================================

/**
 * Display search results
 */
function displayResults(response) {
  state.currentResults = response;

  const resultsSection = document.getElementById('results-section');
  const resultsContainer = document.getElementById('results-container');
  const noResults = document.getElementById('no-results');
  const searchStats = document.getElementById('search-stats');

  // Update stats
  document.getElementById('stat-query').textContent = response.query;
  document.getElementById('stat-count').textContent = response.total_results;
  document.getElementById('stat-time').textContent = `${Math.round(response.search_time_ms)}ms`;
  document.getElementById('stat-mode').textContent = response.search_mode;
  searchStats.hidden = false;

  if (response.results.length === 0) {
    resultsSection.hidden = true;
    noResults.hidden = false;
    return;
  }

  noResults.hidden = true;
  resultsSection.hidden = false;

  // Clear previous results
  resultsContainer.innerHTML = '';

  // Render results
  response.results.forEach(result => {
    const card = createResultCard(result, response.query);
    resultsContainer.appendChild(card);
  });
}

/**
 * Create result card element
 */
function createResultCard(result, query) {
  const card = document.createElement('div');
  card.className = 'result-card';
  card.setAttribute('data-doc-id', result.doc_id);
  if (result.page_num) card.setAttribute('data-page', result.page_num);

  // Result header
  const header = document.createElement('div');
  header.className = 'result-header';
  header.innerHTML = `
    <span class="result-type ${result.type}">${result.type}</span>
    <span class="result-score">Score: ${(result.score * 100).toFixed(1)}%</span>
  `;
  card.appendChild(header);

  // Result content
  const content = document.createElement('div');
  content.className = 'result-content';

  if (result.type === 'visual') {
    const img = document.createElement('img');
    const placeholderSrc = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2VlZSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPk5vIFByZXZpZXc8L3RleHQ+PC9zdmc+';

    // Handle both URL paths and base64 data
    if (result.thumbnail && result.thumbnail.startsWith('/')) {
      // URL path - use directly
      img.src = result.thumbnail;
    } else if (result.thumbnail && result.thumbnail.startsWith('data:')) {
      // Already a data URI - use directly
      img.src = result.thumbnail;
    } else if (result.thumbnail) {
      // Base64 data - wrap in data URI
      img.src = `data:image/svg+xml;base64,${result.thumbnail}`;
    } else {
      // No thumbnail - use placeholder
      img.src = placeholderSrc;
    }

    // Fallback to placeholder on load error (e.g., 404)
    img.onerror = () => {
      img.src = placeholderSrc;
    };

    img.alt = `${result.filename} - Page ${result.page_num}`;
    img.className = 'result-thumbnail';
    content.appendChild(img);
  } else {
    const snippet = document.createElement('p');
    snippet.className = 'result-snippet';
    snippet.innerHTML = highlightQuery(result.snippet, query);
    content.appendChild(snippet);
  }

  card.appendChild(content);

  // Result footer
  const footer = document.createElement('div');
  footer.className = 'result-footer';

  const meta = document.createElement('div');
  meta.className = 'result-meta';

  // Handle missing or different date field names
  const dateStr = result.metadata.upload_date || result.metadata.timestamp;
  const dateDisplay = dateStr ? formatDate(dateStr) : '';

  meta.innerHTML = `
    <strong>${result.filename}</strong>
    ${result.page_num ? `<span class="page-num">Page ${result.page_num}</span>` : ''}
    ${dateDisplay ? `<span class="upload-date">${dateDisplay}</span>` : ''}
  `;
  footer.appendChild(meta);

  const previewBtn = document.createElement('button');
  previewBtn.className = 'btn btn-sm btn-primary preview-btn';
  previewBtn.textContent = 'Preview';
  previewBtn.setAttribute('aria-label', `Preview ${result.filename}${result.page_num ? ` page ${result.page_num}` : ''}`);
  previewBtn.addEventListener('click', () => openPreview(result.doc_id, result.page_num || 1));
  footer.appendChild(previewBtn);

  card.appendChild(footer);

  return card;
}

// ============================================================================
// Preview Modal
// ============================================================================

/**
 * Open preview modal
 */
async function openPreview(docId, pageNum) {
  const modal = document.getElementById('preview-modal');
  modal.hidden = false;
  document.body.style.overflow = 'hidden';

  try {
    const preview = await searchAPI.preview(docId, pageNum);

    state.currentPreview = {
      docId: preview.doc_id,
      pageNum: preview.page_num,
      totalPages: preview.total_pages
    };

    // Update modal content
    document.getElementById('preview-filename').textContent = preview.filename;
    document.getElementById('preview-page').textContent =
      `Page ${preview.page_num} of ${preview.total_pages}`;
    document.getElementById('preview-image').src =
      `data:image/svg+xml;base64,${preview.image}`;
    document.getElementById('page-indicator').textContent =
      `${preview.page_num} / ${preview.total_pages}`;
    document.getElementById('preview-text-content').textContent = preview.text;

    // Update navigation buttons
    document.getElementById('prev-page').disabled = preview.page_num === 1;
    document.getElementById('next-page').disabled = preview.page_num === preview.total_pages;

  } catch (error) {
    showAlert(`Preview failed: ${error.message}`, 'error');
    closePreview();
  }
}

/**
 * Close preview modal
 */
function closePreview() {
  const modal = document.getElementById('preview-modal');
  modal.hidden = true;
  document.body.style.overflow = '';
}

/**
 * Navigate preview pages
 */
async function navigatePage(delta) {
  const newPage = state.currentPreview.pageNum + delta;
  if (newPage < 1 || newPage > state.currentPreview.totalPages) return;

  await openPreview(state.currentPreview.docId, newPage);
}

// ============================================================================
// Event Handlers
// ============================================================================

/**
 * Handle search form submission
 */
document.getElementById('search-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const query = document.getElementById('query').value.trim();
  if (!query || query.length < 2) {
    showAlert('Please enter at least 2 characters', 'warning');
    return;
  }

  setLoading(true);

  try {
    const searchMode = document.getElementById('search-mode').value;
    const nResults = parseInt(document.getElementById('n-results').value);
    const filters = collectFilters();

    const results = await searchAPI.search(query, {
      search_mode: searchMode,
      n_results: nResults,
      filters
    });

    displayResults(results);

  } catch (error) {
    showAlert(`Search failed: ${error.message}`, 'error');
    console.error('Search error:', error);
  } finally {
    setLoading(false);
  }
});

/**
 * Toggle filters panel
 */
document.getElementById('toggle-filters').addEventListener('click', () => {
  const panel = document.getElementById('filters-panel');
  const button = document.getElementById('toggle-filters');
  const isHidden = panel.hidden;

  panel.hidden = !isHidden;
  button.setAttribute('aria-expanded', isHidden ? 'true' : 'false');

  const icon = button.querySelector('.btn-icon');
  icon.textContent = isHidden ? '▲' : '▼';
});

/**
 * Clear filters button
 */
document.getElementById('clear-filters').addEventListener('click', () => {
  clearFilters();
  showAlert('Filters cleared', 'info');
});

/**
 * Modal close handlers
 */
document.querySelector('.modal-overlay').addEventListener('click', closePreview);
document.querySelector('.close-btn').addEventListener('click', closePreview);
document.getElementById('close-modal').addEventListener('click', closePreview);

/**
 * Page navigation
 */
document.getElementById('prev-page').addEventListener('click', () => navigatePage(-1));
document.getElementById('next-page').addEventListener('click', () => navigatePage(1));

/**
 * Download document (placeholder)
 */
document.getElementById('download-document').addEventListener('click', () => {
  showAlert('Download functionality will be available in Wave 3', 'info');
});

/**
 * Keyboard shortcuts
 */
document.addEventListener('keydown', (e) => {
  // Escape key closes modal
  if (e.key === 'Escape' && !document.getElementById('preview-modal').hidden) {
    closePreview();
  }

  // Arrow keys for preview navigation
  if (!document.getElementById('preview-modal').hidden) {
    if (e.key === 'ArrowLeft') {
      navigatePage(-1);
    } else if (e.key === 'ArrowRight') {
      navigatePage(1);
    }
  }
});

// ============================================================================
// Initialize
// ============================================================================

console.log('DocuSearch Search Interface initialized (Wave 2 - Mock Data)');

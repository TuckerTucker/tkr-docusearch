/**
 * DocuSearch - Status Dashboard JavaScript
 * Wave 2: Mock Status Data Implementation
 */

// Import mock data generator from search.js context
// In production, this would be a shared module

// ============================================================================
// Mock Status Data Generator
// ============================================================================

/**
 * Generate mock status data
 */
function generateMockStatus() {
  const hasActiveProcessing = Math.random() > 0.4;
  const queueSize = Math.floor(Math.random() * 8);
  const completedToday = Math.floor(Math.random() * 30) + 5;
  const failedToday = Math.floor(Math.random() * 3);

  const status = {
    queue: {
      size: queueSize,
      processing: hasActiveProcessing ? 1 : 0,
      completed_today: completedToday,
      failed_today: failedToday,
      avg_processing_time_seconds: Math.floor(Math.random() * 60) + 40,
      estimated_wait_time_seconds: queueSize * (Math.floor(Math.random() * 60) + 40)
    },
    current: null,
    recent: []
  };

  // Current processing document
  if (hasActiveProcessing) {
    const processingStages = [
      'Parsing document structure',
      'Extracting text content',
      'Processing page 5 of 25',
      'Generating visual embeddings',
      'Creating text embeddings',
      'Indexing content'
    ];

    status.current = {
      doc_id: 'mock-processing-uuid',
      filename: ['Q3-2023-Earnings.pdf', 'Annual-Report.pdf', 'Marketing-Strategy.docx'][Math.floor(Math.random() * 3)],
      status: ['parsing', 'extracting_text', 'embedding_visual', 'embedding_text', 'indexing'][Math.floor(Math.random() * 5)],
      progress: Math.random() * 0.8 + 0.1,
      stage: processingStages[Math.floor(Math.random() * processingStages.length)],
      elapsed_seconds: Math.floor(Math.random() * 120) + 10,
      estimated_remaining_seconds: Math.floor(Math.random() * 60) + 5
    };
  }

  // Recent documents
  const recentFilenames = [
    'Contract-2023.pdf',
    'Annual-Report.pdf',
    'Product-Roadmap-Q4.pptx',
    'Financial-Summary.pdf',
    'Technical-Specs.pdf',
    'Meeting-Notes-Sept.docx',
    'Budget-Proposal-2024.xlsx',
    'Employee-Handbook.pdf'
  ];

  const recentCount = Math.min(5, completedToday + failedToday);
  const now = Date.now();

  for (let i = 0; i < recentCount; i++) {
    const isCompleted = i < completedToday || Math.random() > 0.2;
    const uploadTime = now - (i + 1) * 3600000 - Math.random() * 3600000;

    status.recent.push({
      doc_id: `mock-recent-${i + 1}`,
      filename: recentFilenames[i % recentFilenames.length],
      status: isCompleted ? 'completed' : 'failed',
      total_pages: Math.floor(Math.random() * 100) + 10,
      processing_time_seconds: Math.floor(Math.random() * 300) + 60,
      upload_timestamp: new Date(uploadTime).toISOString(),
      error: !isCompleted ? 'Processing timeout' : undefined
    });
  }

  return status;
}

// ============================================================================
// Status API Client
// ============================================================================

class StatusAPIClient {
  constructor(baseURL = 'http://localhost:8002', useMockData = false) {
    this.baseURL = baseURL;
    this.useMockData = useMockData;
  }

  async getStatus() {
    // Fallback to mock data if requested
    if (this.useMockData) {
      await new Promise(resolve => setTimeout(resolve, 100 + Math.random() * 100));
      return generateMockStatus();
    }

    // Wave 4: Real API call with fallback
    try {
      const response = await fetch(`${this.baseURL}/status`);

      if (!response.ok) {
        throw new Error(`Status check failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API status check failed, falling back to mock data:', error);
      this.useMockData = true;
      return await this.getStatus();
    }
  }
}

// Initialize API client (Wave 4: real API with fallback)
const statusAPI = new StatusAPIClient('http://localhost:8002', false);

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Format seconds to human-readable time
 */
function formatDuration(seconds) {
  if (seconds < 60) {
    return `${seconds}s`;
  } else if (seconds < 3600) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${mins}m`;
  }
}

/**
 * Format date to human-readable string
 */
function formatDate(isoString) {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} min ago`;
  if (diffHours < 24) return `${diffHours}h ago`;

  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

/**
 * Format status for display
 */
function formatStatus(status) {
  const statusMap = {
    'completed': 'Completed',
    'failed': 'Failed',
    'parsing': 'Parsing',
    'extracting_text': 'Extracting Text',
    'embedding_visual': 'Visual Embedding',
    'embedding_text': 'Text Embedding',
    'indexing': 'Indexing'
  };
  return statusMap[status] || status;
}

// ============================================================================
// Dashboard Update Functions
// ============================================================================

/**
 * Update queue statistics
 */
function updateQueueStats(queueData) {
  document.getElementById('queue-size').textContent = queueData.size;
  document.getElementById('processing-count').textContent = queueData.processing;
  document.getElementById('completed-today').textContent = queueData.completed_today;
  document.getElementById('failed-today').textContent = queueData.failed_today;
  document.getElementById('avg-time').textContent = formatDuration(queueData.avg_processing_time_seconds);
  document.getElementById('est-wait').textContent = formatDuration(queueData.estimated_wait_time_seconds);
}

/**
 * Update current processing section
 */
function updateCurrentProcessing(currentData) {
  const noProcessing = document.getElementById('no-processing');
  const currentDoc = document.getElementById('current-doc');

  if (!currentData) {
    noProcessing.hidden = false;
    currentDoc.hidden = true;
    return;
  }

  noProcessing.hidden = true;
  currentDoc.hidden = false;

  document.getElementById('current-filename').textContent = currentData.filename;
  document.getElementById('current-status').textContent = formatStatus(currentData.status);
  document.getElementById('current-elapsed').textContent = `Elapsed: ${formatDuration(currentData.elapsed_seconds)}`;
  document.getElementById('current-eta').textContent = `ETA: ${formatDuration(currentData.estimated_remaining_seconds)}`;

  const progressPercent = Math.round(currentData.progress * 100);
  document.getElementById('progress-fill').style.width = `${progressPercent}%`;
  document.getElementById('progress-percent').textContent = `${progressPercent}%`;
  document.getElementById('progress-stage').textContent = currentData.stage;
}

/**
 * Update recent documents table
 */
function updateRecentDocuments(recentData) {
  const tbody = document.getElementById('recent-docs-body');

  if (!recentData || recentData.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="empty-cell">No recent documents</td></tr>';
    return;
  }

  tbody.innerHTML = '';

  recentData.forEach(doc => {
    const row = document.createElement('tr');
    row.className = doc.status === 'failed' ? 'table-row-error' : '';

    const statusClass = doc.status === 'completed' ? 'status-success' :
                       doc.status === 'failed' ? 'status-error' : 'status-info';

    row.innerHTML = `
      <td class="cell-filename" title="${doc.filename}">${doc.filename}</td>
      <td class="cell-status">
        <span class="status-badge ${statusClass}">${formatStatus(doc.status)}</span>
        ${doc.error ? `<span class="error-text" title="${doc.error}">⚠️</span>` : ''}
      </td>
      <td class="cell-pages">${doc.total_pages}</td>
      <td class="cell-time">${formatDuration(doc.processing_time_seconds)}</td>
      <td class="cell-date">${formatDate(doc.upload_timestamp)}</td>
    `;

    tbody.appendChild(row);
  });
}

/**
 * Update entire dashboard
 */
async function updateDashboard() {
  try {
    const status = await statusAPI.getStatus();

    updateQueueStats(status.queue);
    updateCurrentProcessing(status.current);
    updateRecentDocuments(status.recent);

    // Update refresh indicator
    updateRefreshIndicator(true);

  } catch (error) {
    console.error('Failed to update status:', error);
    updateRefreshIndicator(false);
  }
}

/**
 * Update refresh indicator
 */
function updateRefreshIndicator(success) {
  const indicator = document.querySelector('.refresh-indicator');
  indicator.className = 'refresh-indicator' + (success ? ' refresh-success' : ' refresh-error');
}

// ============================================================================
// Auto-refresh Management
// ============================================================================

let refreshInterval = null;
let isRefreshActive = false;

/**
 * Start auto-refresh
 */
function startAutoRefresh() {
  if (refreshInterval) return;

  isRefreshActive = true;
  updateRefreshStatus();

  // Initial update
  updateDashboard();

  // Set up interval (5 seconds)
  refreshInterval = setInterval(updateDashboard, 5000);
}

/**
 * Stop auto-refresh
 */
function stopAutoRefresh() {
  if (refreshInterval) {
    clearInterval(refreshInterval);
    refreshInterval = null;
  }

  isRefreshActive = false;
  updateRefreshStatus();
}

/**
 * Toggle auto-refresh
 */
function toggleAutoRefresh() {
  if (isRefreshActive) {
    stopAutoRefresh();
  } else {
    startAutoRefresh();
  }
}

/**
 * Update refresh status text
 */
function updateRefreshStatus() {
  const statusText = document.getElementById('refresh-status');
  const toggleBtn = document.getElementById('toggle-refresh');

  if (isRefreshActive) {
    statusText.textContent = 'Auto-refresh: Active (every 5s)';
    toggleBtn.textContent = 'Pause';
    toggleBtn.classList.remove('btn-primary');
    toggleBtn.classList.add('btn-outline');
  } else {
    statusText.textContent = 'Auto-refresh: Paused';
    toggleBtn.textContent = 'Resume';
    toggleBtn.classList.remove('btn-outline');
    toggleBtn.classList.add('btn-primary');
  }
}

// ============================================================================
// Event Handlers
// ============================================================================

/**
 * Toggle refresh button
 */
document.getElementById('toggle-refresh').addEventListener('click', toggleAutoRefresh);

/**
 * Page visibility change (pause when hidden)
 */
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    if (isRefreshActive) {
      stopAutoRefresh();
      // Store that we were active
      sessionStorage.setItem('wasRefreshActive', 'true');
    }
  } else {
    // Resume if we were active before
    if (sessionStorage.getItem('wasRefreshActive') === 'true') {
      startAutoRefresh();
      sessionStorage.removeItem('wasRefreshActive');
    }
  }
});

/**
 * Cleanup on page unload
 */
window.addEventListener('beforeunload', () => {
  stopAutoRefresh();
});

// ============================================================================
// Initialize
// ============================================================================

console.log('DocuSearch Status Dashboard initialized (Wave 2 - Mock Data)');

// Start auto-refresh on load
startAutoRefresh();

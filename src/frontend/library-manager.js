/**
 * LibraryManager - Core library logic
 *
 * Coordinates all components: WebSocket, API, filters, upload, and document cards.
 * Manages document state and real-time updates.
 *
 * Provider: library-agent (Wave 1)
 * Integrates: All Wave 1 components
 */

import { WebSocketClient } from './websocket-client.js';
import { DocumentsAPIClient } from './api-client.js';
import { createDocumentCard, updateCardState } from './document-card.js';
import { FilterBar } from './filter-bar.js';
import { UploadModal } from './upload-modal.js';

/**
 * Library Manager - Main application controller
 */
export class LibraryManager {
  constructor() {
    // Components
    this.wsClient = null;
    this.apiClient = null;
    this.filterBar = null;
    this.uploadModal = null;

    // DOM elements
    this.grid = null;
    this.connectionStatus = null;

    // State
    this.documentCards = new Map(); // doc_id → HTMLElement
    this.currentQuery = {
      search: '',
      sort_by: 'date_added',
      file_types: ['pdf', 'docx', 'pptx', 'audio'],
      limit: 50,
      offset: 0
    };

    // Temp document tracking (for uploads)
    this.tempDocs = new Map(); // temp_id → {filename, card}
  }

  /**
   * Initialize library
   */
  async init() {
    console.log('Initializing LibraryManager...');

    // Get DOM elements
    this.grid = document.getElementById('document-grid');
    this.connectionStatus = document.getElementById('connection-status');

    if (!this.grid || !this.connectionStatus) {
      console.error('Required DOM elements not found');
      return;
    }

    // Initialize components
    this.apiClient = new DocumentsAPIClient('http://localhost:8002');

    this.filterBar = new FilterBar('#filter-bar');

    this.uploadModal = new UploadModal({
      copypartyUrl: 'http://localhost:8000',
      uploadPath: '/uploads'
    });
    this.uploadModal.init();

    // Attach event listeners
    this.attachEventListeners();

    // Initialize WebSocket
    this.wsClient = new WebSocketClient('ws://localhost:8002/ws');
    this.setupWebSocket();
    this.wsClient.connect();

    // Load initial documents
    await this.loadDocuments();

    console.log('LibraryManager initialized');
  }

  /**
   * Setup WebSocket event handlers
   */
  setupWebSocket() {
    this.wsClient.on('connected', () => {
      console.log('WebSocket connected');
      this.updateConnectionStatus('connected');
    });

    this.wsClient.on('disconnected', () => {
      console.log('WebSocket disconnected');
      this.updateConnectionStatus('disconnected');
    });

    this.wsClient.on('reconnecting', (data) => {
      console.log(`WebSocket reconnecting (attempt ${data.attempt})...`);
      this.updateConnectionStatus('reconnecting');
    });

    this.wsClient.on('status_update', (message) => {
      this.handleStatusUpdate(message);
    });

    this.wsClient.on('log', (message) => {
      console.log(`[Worker Log] ${message.level}: ${message.message}`);
    });
  }

  /**
   * Attach event listeners
   */
  attachEventListeners() {
    // Filter change events
    document.addEventListener('filterChange', (e) => {
      this.handleFilterChange(e.detail);
    });

    // Page change events
    document.addEventListener('pageChange', (e) => {
      this.handlePageChange(e.detail);
    });

    // Upload complete events
    document.addEventListener('uploadComplete', (e) => {
      this.handleUploadComplete(e.detail);
    });

    // Upload error events
    document.addEventListener('uploadError', (e) => {
      console.error('Upload error:', e.detail);
    });
  }

  /**
   * Load documents from API
   */
  async loadDocuments() {
    try {
      this.showLoadingState();

      const response = await this.apiClient.listDocuments(this.currentQuery);

      // Clear grid
      this.grid.innerHTML = '';
      this.documentCards.clear();

      // Filter by file type (client-side)
      let documents = response.documents;
      if (this.currentQuery.file_types.length < 4) {
        documents = documents.filter(doc => {
          const ext = doc.filename.split('.').pop().toLowerCase();
          return this.currentQuery.file_types.includes(ext) ||
                 (this.currentQuery.file_types.includes('audio') && ['mp3', 'wav', 'm4a', 'flac'].includes(ext));
        });
      }

      // Render documents
      if (documents.length === 0) {
        this.showEmptyState();
      } else {
        this.renderDocuments(documents);
      }

      // Update pagination
      this.filterBar.updatePaginationDisplay(response.total);

    } catch (error) {
      console.error('Failed to load documents:', error);
      this.showErrorState(error.message);
    }
  }

  /**
   * Render documents to grid
   * @param {Array} documents - Document list from API
   */
  renderDocuments(documents) {
    const fragment = document.createDocumentFragment();

    documents.forEach(doc => {
      const card = createDocumentCard({
        filename: doc.filename,
        thumbnailUrl: doc.first_page_thumb ? `http://localhost:8002${doc.first_page_thumb}` : '',
        dateAdded: new Date(doc.date_added),
        detailsUrl: `#/document/${doc.doc_id}`,
        state: 'completed'
      });

      this.documentCards.set(doc.doc_id, card);
      fragment.appendChild(card);
    });

    this.grid.appendChild(fragment);
  }

  /**
   * Handle filter change
   * @param {Object} detail - Filter event detail
   */
  async handleFilterChange(detail) {
    this.currentQuery = { ...detail };
    await this.loadDocuments();
  }

  /**
   * Handle page change
   * @param {Object} detail - Page event detail
   */
  async handlePageChange(detail) {
    this.currentQuery.offset = detail.offset;
    await this.loadDocuments();

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  /**
   * Handle upload complete
   * @param {Object} detail - Upload event detail
   */
  handleUploadComplete(detail) {
    const { filename } = detail;

    // Create loading card
    const card = createDocumentCard({
      filename,
      thumbnailUrl: '',
      dateAdded: new Date(),
      detailsUrl: '#',
      state: 'loading'
    });

    // Generate temporary ID
    const tempId = `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    // Add to grid (at top)
    this.grid.prepend(card);

    // Track temp card
    this.tempDocs.set(tempId, { filename, card });

    console.log(`Upload complete: ${filename} (temp ID: ${tempId})`);
  }

  /**
   * Handle WebSocket status update
   * @param {Object} message - Status update message
   */
  handleStatusUpdate(message) {
    const { doc_id, status, progress, stage, filename } = message;

    console.log(`Status update: ${doc_id} - ${status} (${Math.round((progress || 0) * 100)}%)`);

    let card = this.documentCards.get(doc_id);

    if (!card && status === 'processing') {
      // Check if this matches a temp doc
      let tempId = null;
      for (const [tid, tdata] of this.tempDocs.entries()) {
        if (tdata.filename === filename) {
          tempId = tid;
          card = tdata.card;
          break;
        }
      }

      if (card) {
        // Replace temp card with real doc_id
        this.tempDocs.delete(tempId);
        this.documentCards.set(doc_id, card);
      } else {
        // Create new processing card
        card = createDocumentCard({
          filename,
          thumbnailUrl: '',
          dateAdded: new Date(),
          detailsUrl: '#',
          state: 'processing',
          processingStatus: { stage, progress }
        });

        this.grid.prepend(card);
        this.documentCards.set(doc_id, card);
      }
    }

    // Update existing card
    if (card) {
      if (status === 'processing') {
        updateCardState(card, { state: 'processing', stage, progress });
      } else if (status === 'completed') {
        // Reload library to get full document data
        this.loadDocuments();
      } else if (status === 'failed') {
        // Mark as failed (could implement error state)
        console.error(`Document processing failed: ${doc_id}`);
      }
    }
  }

  /**
   * Update connection status indicator
   * @param {string} status - Connection status (connected, disconnected, reconnecting)
   */
  updateConnectionStatus(status) {
    if (!this.connectionStatus) return;

    const statusMap = {
      connected: { text: 'Connected', class: 'connected' },
      disconnected: { text: 'Disconnected', class: 'disconnected' },
      reconnecting: { text: 'Reconnecting...', class: 'reconnecting' }
    };

    const config = statusMap[status] || statusMap.disconnected;

    this.connectionStatus.textContent = config.text;
    this.connectionStatus.className = `connection-status connection-status--${config.class}`;
  }

  /**
   * Show loading state
   */
  showLoadingState() {
    this.grid.innerHTML = '<div class="loading">Loading documents...</div>';
  }

  /**
   * Show empty state
   */
  showEmptyState() {
    this.grid.innerHTML = '<div class="empty-state">No documents found. Try uploading some files!</div>';
  }

  /**
   * Show error state
   * @param {string} message - Error message
   */
  showErrorState(message) {
    this.grid.innerHTML = `<div class="error-state">Error loading documents: ${message}</div>`;
  }
}

// Auto-initialize on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    const manager = new LibraryManager();
    manager.init();
  });
} else {
  const manager = new LibraryManager();
  manager.init();
}

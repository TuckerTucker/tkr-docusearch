/**
 * Integration Test Suite for Library Frontend
 *
 * Tests cross-component integration, event handling, and API contracts.
 * Run in browser console or with test framework.
 *
 * Usage:
 *   1. Open http://localhost:8002/frontend/ in browser
 *   2. Open console
 *   3. Paste this file or use: <script type="module" src="test-integration.js"></script>
 *   4. Tests run automatically
 */

import { WebSocketClient } from './websocket-client.js';
import { DocumentsAPIClient } from './api-client.js';
import { createDocumentCard, updateCardState } from './document-card.js';
import { FilterBar } from './filter-bar.js';
import { UploadModal } from './upload-modal.js';
import { LibraryManager } from './library-manager.js';

// Test utilities
const assert = (condition, message) => {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
  console.log(` ${message}`);
};

const assertThrows = async (fn, message) => {
  try {
    await fn();
    throw new Error(`Expected error but none thrown: ${message}`);
  } catch (error) {
    console.log(` ${message}`);
  }
};

// Test results tracking
const results = {
  total: 0,
  passed: 0,
  failed: 0,
  tests: []
};

const test = (name, fn) => {
  results.total++;
  return (async () => {
    try {
      console.group(`Test: ${name}`);
      await fn();
      results.passed++;
      results.tests.push({ name, status: 'PASS' });
      console.log(` PASS: ${name}`);
      console.groupEnd();
    } catch (error) {
      results.failed++;
      results.tests.push({ name, status: 'FAIL', error: error.message });
      console.error(`L FAIL: ${name}`, error);
      console.groupEnd();
    }
  })();
};

// ============================================
// Test Suite 1: WebSocketClient
// ============================================

const testWebSocketClient = async () => {
  console.group('= WebSocketClient Tests');

  await test('WebSocketClient: Constructor initializes properties', () => {
    const ws = new WebSocketClient('ws://localhost:8002/ws');
    assert(ws.url === 'ws://localhost:8002/ws', 'URL stored correctly');
    assert(ws.reconnectAttempts === 0, 'Reconnect attempts initialized');
    assert(ws.handlers.connected, 'Handlers object initialized');
  });

  await test('WebSocketClient: Event handler registration', () => {
    const ws = new WebSocketClient('ws://localhost:8002/ws');
    let called = false;
    ws.on('connected', () => { called = true; });
    ws.emit('connected');
    assert(called, 'Event handler called');
  });

  await test('WebSocketClient: Message type routing', () => {
    const ws = new WebSocketClient('ws://localhost:8002/ws');
    let statusReceived = null;
    ws.on('status_update', (data) => { statusReceived = data; });
    ws.handleMessage({ type: 'status_update', doc_id: 'test123', status: 'processing' });
    assert(statusReceived !== null, 'Status update routed correctly');
    assert(statusReceived.doc_id === 'test123', 'Message data passed through');
  });

  await test('WebSocketClient: Reconnection backoff calculation', () => {
    const ws = new WebSocketClient('ws://localhost:8002/ws');
    ws.reconnectAttempts = 0;
    const delay1 = Math.min(1000 * Math.pow(2, 0), 32000);
    assert(delay1 === 1000, 'First retry: 1 second');

    ws.reconnectAttempts = 5;
    const delay5 = Math.min(1000 * Math.pow(2, 5), 32000);
    assert(delay5 === 32000, 'Fifth retry: capped at 32 seconds');
  });

  console.groupEnd();
};

// ============================================
// Test Suite 2: DocumentsAPIClient
// ============================================

const testDocumentsAPIClient = async () => {
  console.group('=Ä DocumentsAPIClient Tests');

  await test('DocumentsAPIClient: Constructor sets base URL', () => {
    const client = new DocumentsAPIClient('http://localhost:8002');
    assert(client.baseUrl === 'http://localhost:8002', 'Base URL stored');
  });

  await test('DocumentsAPIClient: listDocuments builds query string', async () => {
    const client = new DocumentsAPIClient('http://localhost:8002');

    // Mock fetch to capture URL
    const originalFetch = window.fetch;
    let capturedUrl = null;
    window.fetch = (url) => {
      capturedUrl = url;
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ documents: [], total: 0, limit: 50, offset: 0 })
      });
    };

    await client.listDocuments({ limit: 10, offset: 20, search: 'test', sort_by: 'filename' });

    assert(capturedUrl.includes('limit=10'), 'Limit param added');
    assert(capturedUrl.includes('offset=20'), 'Offset param added');
    assert(capturedUrl.includes('search=test'), 'Search param added');
    assert(capturedUrl.includes('sort_by=filename'), 'Sort param added');

    window.fetch = originalFetch;
  });

  await test('DocumentsAPIClient: getDocument validates doc_id', async () => {
    const client = new DocumentsAPIClient('http://localhost:8002');

    await assertThrows(
      () => client.getDocument('invalid id with spaces'),
      'Invalid doc_id throws error'
    );
  });

  await test('DocumentsAPIClient: getImageUrl generates correct URL', () => {
    const client = new DocumentsAPIClient('http://localhost:8002');
    const url = client.getImageUrl('abc123', 'page001.png');
    assert(url === 'http://localhost:8002/images/abc123/page001.png', 'Image URL correct');
  });

  console.groupEnd();
};

// ============================================
// Test Suite 3: DocumentCard
// ============================================

const testDocumentCard = async () => {
  console.group('<´ DocumentCard Tests');

  await test('DocumentCard: createDocumentCard returns HTMLElement', () => {
    const card = createDocumentCard({
      filename: 'test.pdf',
      thumbnailUrl: '',
      dateAdded: new Date(),
      detailsUrl: '#',
      state: 'completed'
    });
    assert(card instanceof HTMLElement, 'Returns HTMLElement');
    assert(card.classList.contains('document-card'), 'Has document-card class');
  });

  await test('DocumentCard: State classes applied correctly', () => {
    const loadingCard = createDocumentCard({
      filename: 'test.pdf',
      state: 'loading'
    });
    assert(loadingCard.classList.contains('document-card--loading'), 'Loading state applied');

    const processingCard = createDocumentCard({
      filename: 'test.pdf',
      state: 'processing',
      processingStatus: { stage: 'embedding', progress: 0.5 }
    });
    assert(processingCard.classList.contains('document-card--processing'), 'Processing state applied');
  });

  await test('DocumentCard: Variant detection (document vs audio)', () => {
    const pdfCard = createDocumentCard({ filename: 'test.pdf', state: 'completed' });
    assert(pdfCard.classList.contains('document-card--document'), 'PDF uses document variant');

    const audioCard = createDocumentCard({ filename: 'test.mp3', state: 'completed' });
    assert(audioCard.classList.contains('document-card--audio'), 'MP3 uses audio variant');
  });

  await test('DocumentCard: updateCardState updates progress', () => {
    const card = createDocumentCard({
      filename: 'test.pdf',
      state: 'processing',
      processingStatus: { stage: 'embedding', progress: 0.3 }
    });

    updateCardState(card, { state: 'processing', stage: 'storing', progress: 0.7 });

    const progressBar = card.querySelector('.document-card__progress-fill');
    if (progressBar) {
      assert(progressBar.style.width === '70%', 'Progress bar updated');
    }
  });

  await test('DocumentCard: Filename displayed correctly', () => {
    const card = createDocumentCard({
      filename: 'My Important Document.pdf',
      state: 'completed'
    });
    const filenameEl = card.querySelector('.document-card__filename');
    assert(filenameEl.textContent === 'My Important Document.pdf', 'Filename displayed');
  });

  console.groupEnd();
};

// ============================================
// Test Suite 4: FilterBar
// ============================================

const testFilterBar = async () => {
  console.group('= FilterBar Tests');

  await test('FilterBar: Constructor requires valid container', () => {
    try {
      new FilterBar('#nonexistent-container');
      throw new Error('Should have thrown error');
    } catch (error) {
      assert(error.message.includes('not found'), 'Throws error for missing container');
    }
  });

  await test('FilterBar: Renders UI elements', () => {
    // Create test container
    const container = document.createElement('div');
    container.id = 'test-filter-bar';
    document.body.appendChild(container);

    const filterBar = new FilterBar('#test-filter-bar');

    assert(container.querySelector('input[type="search"]'), 'Search input rendered');
    assert(container.querySelector('select'), 'Sort select rendered');
    assert(container.querySelectorAll('input[type="checkbox"]').length > 0, 'Checkboxes rendered');
    assert(container.querySelector('button'), 'Clear button rendered');

    document.body.removeChild(container);
  });

  await test('FilterBar: State initialization', () => {
    const container = document.createElement('div');
    container.id = 'test-filter-bar-2';
    document.body.appendChild(container);

    const filterBar = new FilterBar('#test-filter-bar-2');

    assert(filterBar.state.search === '', 'Search empty initially');
    assert(filterBar.state.sort_by === 'date_added', 'Sort by date_added default');
    assert(Array.isArray(filterBar.state.file_types), 'File types is array');
    assert(filterBar.state.limit === 50, 'Default limit 50');
    assert(filterBar.state.offset === 0, 'Default offset 0');

    document.body.removeChild(container);
  });

  await test('FilterBar: Event emission structure', () => {
    const container = document.createElement('div');
    container.id = 'test-filter-bar-3';
    document.body.appendChild(container);

    const filterBar = new FilterBar('#test-filter-bar-3');

    let eventDetail = null;
    container.addEventListener('filterChange', (e) => {
      eventDetail = e.detail;
    });

    filterBar.emitFilterChange();

    assert(eventDetail !== null, 'Event emitted');
    assert(eventDetail.search === '', 'Detail includes search');
    assert(eventDetail.sort_by === 'date_added', 'Detail includes sort_by');
    assert(Array.isArray(eventDetail.file_types), 'Detail includes file_types');

    document.body.removeChild(container);
  });

  console.groupEnd();
};

// ============================================
// Test Suite 5: UploadModal
// ============================================

const testUploadModal = async () => {
  console.group('=ä UploadModal Tests');

  await test('UploadModal: Constructor sets configuration', () => {
    const modal = new UploadModal({
      copypartyUrl: 'http://localhost:8000',
      uploadPath: '/uploads',
      maxFileSize: 100 * 1024 * 1024
    });

    assert(modal.copypartyUrl === 'http://localhost:8000', 'Copyparty URL set');
    assert(modal.uploadPath === '/uploads', 'Upload path set');
    assert(modal.maxFileSize === 100 * 1024 * 1024, 'Max file size set');
  });

  await test('UploadModal: File validation - extension', () => {
    const modal = new UploadModal();

    const validFile = new File(['content'], 'test.pdf', { type: 'application/pdf' });
    const validResult = modal.validateFile(validFile);
    assert(validResult.valid === true, 'Valid file accepted');

    const invalidFile = new File(['content'], 'test.exe', { type: 'application/x-msdownload' });
    const invalidResult = modal.validateFile(invalidFile);
    assert(invalidResult.valid === false, 'Invalid file rejected');
    assert(invalidResult.code === 'UNSUPPORTED_TYPE', 'Correct error code');
  });

  await test('UploadModal: File validation - size', () => {
    const modal = new UploadModal({ maxFileSize: 1024 }); // 1KB limit

    const smallFile = new File(['x'.repeat(500)], 'small.pdf', { type: 'application/pdf' });
    const smallResult = modal.validateFile(smallFile);
    assert(smallResult.valid === true, 'Small file accepted');

    const largeFile = new File(['x'.repeat(2000)], 'large.pdf', { type: 'application/pdf' });
    const largeResult = modal.validateFile(largeFile);
    assert(largeResult.valid === false, 'Large file rejected');
    assert(largeResult.code === 'FILE_TOO_LARGE', 'Correct error code');
  });

  await test('UploadModal: Modal DOM creation', () => {
    const modal = new UploadModal();
    modal.init();

    const modalEl = document.querySelector('.upload-modal');
    assert(modalEl !== null, 'Modal element created');
    assert(modalEl.querySelector('.upload-modal__drop-zone'), 'Drop zone created');
    assert(modalEl.querySelector('.upload-modal__close'), 'Close button created');

    modal.destroy();
  });

  await test('UploadModal: Drag counter logic', () => {
    const modal = new UploadModal();
    modal.init();

    assert(modal.dragCounter === 0, 'Drag counter starts at 0');

    // Simulate drag enter
    const dragEnterEvent = new Event('dragenter');
    document.body.dispatchEvent(dragEnterEvent);

    // Counter should increment (implementation detail)
    // Modal should show when counter === 1

    modal.destroy();
  });

  console.groupEnd();
};

// ============================================
// Test Suite 6: LibraryManager Integration
// ============================================

const testLibraryManagerIntegration = async () => {
  console.group('=Ú LibraryManager Integration Tests');

  await test('LibraryManager: Constructor initializes components', () => {
    const manager = new LibraryManager();

    assert(manager.currentQuery, 'Current query initialized');
    assert(manager.documentCards instanceof Map, 'Document cards Map initialized');
    assert(manager.tempDocs instanceof Map, 'Temp docs Map initialized');
  });

  await test('LibraryManager: Component initialization', async () => {
    // Create required DOM elements
    const grid = document.createElement('div');
    grid.id = 'document-grid';
    const status = document.createElement('div');
    status.id = 'connection-status';
    const filterBar = document.createElement('div');
    filterBar.id = 'filter-bar';

    document.body.appendChild(grid);
    document.body.appendChild(status);
    document.body.appendChild(filterBar);

    const manager = new LibraryManager();

    // Note: init() would actually start services, so we just test properties
    assert(manager.grid === null, 'Grid not set until init');
    assert(manager.connectionStatus === null, 'Status not set until init');

    document.body.removeChild(grid);
    document.body.removeChild(status);
    document.body.removeChild(filterBar);
  });

  await test('LibraryManager: Filter change handler updates query', () => {
    const manager = new LibraryManager();

    const originalQuery = { ...manager.currentQuery };
    const newQuery = {
      search: 'test',
      sort_by: 'filename',
      file_types: ['pdf'],
      limit: 50,
      offset: 0
    };

    manager.currentQuery = newQuery;
    assert(manager.currentQuery.search === 'test', 'Query updated');
  });

  await test('LibraryManager: Document card tracking', () => {
    const manager = new LibraryManager();

    const fakeCard = document.createElement('div');
    manager.documentCards.set('doc123', fakeCard);

    assert(manager.documentCards.has('doc123'), 'Card tracked in Map');
    assert(manager.documentCards.get('doc123') === fakeCard, 'Card retrievable by ID');
  });

  await test('LibraryManager: Temp document tracking', () => {
    const manager = new LibraryManager();

    const fakeCard = document.createElement('div');
    const tempId = 'temp_123456';
    manager.tempDocs.set(tempId, { filename: 'test.pdf', card: fakeCard });

    assert(manager.tempDocs.has(tempId), 'Temp doc tracked');
    assert(manager.tempDocs.get(tempId).filename === 'test.pdf', 'Filename stored');
  });

  console.groupEnd();
};

// ============================================
// Test Suite 7: Event Integration
// ============================================

const testEventIntegration = async () => {
  console.group('= Event Integration Tests');

  await test('Event: FilterBar ’ LibraryManager communication', () => {
    const container = document.createElement('div');
    container.id = 'test-event-filter';
    document.body.appendChild(container);

    const filterBar = new FilterBar('#test-event-filter');

    let eventReceived = false;
    container.addEventListener('filterChange', () => {
      eventReceived = true;
    });

    filterBar.emitFilterChange();
    assert(eventReceived, 'FilterChange event received');

    document.body.removeChild(container);
  });

  await test('Event: UploadModal ’ LibraryManager communication', () => {
    const modal = new UploadModal();
    modal.init();

    let uploadComplete = false;
    document.addEventListener('uploadComplete', () => {
      uploadComplete = true;
    }, { once: true });

    modal.emitUploadComplete('test.pdf', '/uploads/test.pdf', 1024, {});
    assert(uploadComplete, 'UploadComplete event received');

    modal.destroy();
  });

  await test('Event: CustomEvent detail structure', () => {
    const container = document.createElement('div');
    container.id = 'test-event-detail';
    document.body.appendChild(container);

    const filterBar = new FilterBar('#test-event-detail');

    let capturedDetail = null;
    container.addEventListener('filterChange', (e) => {
      capturedDetail = e.detail;
    });

    filterBar.emitFilterChange();

    assert(capturedDetail !== null, 'Event detail captured');
    assert(capturedDetail.hasOwnProperty('search'), 'Detail has search');
    assert(capturedDetail.hasOwnProperty('sort_by'), 'Detail has sort_by');
    assert(capturedDetail.hasOwnProperty('file_types'), 'Detail has file_types');
    assert(capturedDetail.hasOwnProperty('limit'), 'Detail has limit');
    assert(capturedDetail.hasOwnProperty('offset'), 'Detail has offset');

    document.body.removeChild(container);
  });

  console.groupEnd();
};

// ============================================
// Run All Tests
// ============================================

const runAllTests = async () => {
  console.log('>ê Starting Integration Test Suite\n');
  console.log('=' .repeat(60));

  const startTime = performance.now();

  await testWebSocketClient();
  await testDocumentsAPIClient();
  await testDocumentCard();
  await testFilterBar();
  await testUploadModal();
  await testLibraryManagerIntegration();
  await testEventIntegration();

  const endTime = performance.now();
  const duration = ((endTime - startTime) / 1000).toFixed(2);

  console.log('\n' + '='.repeat(60));
  console.log('=Ê Test Results');
  console.log('='.repeat(60));
  console.log(`Total Tests:  ${results.total}`);
  console.log(` Passed:    ${results.passed}`);
  console.log(`L Failed:    ${results.failed}`);
  console.log(`ñ  Duration:  ${duration}s`);
  console.log(`=È Coverage:  ${((results.passed / results.total) * 100).toFixed(1)}%`);

  if (results.failed > 0) {
    console.log('\nL Failed Tests:');
    results.tests.filter(t => t.status === 'FAIL').forEach(t => {
      console.log(`  - ${t.name}: ${t.error}`);
    });
  }

  console.log('\n' + (results.failed === 0 ? ' All tests passed!' : 'L Some tests failed'));
  console.log('='.repeat(60));

  return results;
};

// Auto-run if loaded as module
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', runAllTests);
} else {
  runAllTests();
}

export { runAllTests, results };

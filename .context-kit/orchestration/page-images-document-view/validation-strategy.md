# Validation Strategy: Page Images & Document View

**Orchestration Plan:** page-images-document-view
**Created:** 2025-10-11

---

## Overview

This validation strategy defines the testing and quality assurance approach for the page images and document view implementation. It includes wave gates, integration tests, performance benchmarks, and final acceptance criteria.

---

## Wave Synchronization Gates

### Wave 1 Gate: Foundation Complete

**Objective:** Verify infrastructure and core utilities are functional

**Prerequisites:**
- infra-agent: Configuration module complete
- image-agent: Image utilities complete
- storage-agent: Schema updates complete

**Validation Tests:**

```bash
# 1. Configuration validation
python -c "from src.config.image_config import PAGE_IMAGE_DIR; assert PAGE_IMAGE_DIR.exists()"
python -c "from src.config.image_config import THUMBNAIL_SIZE; assert THUMBNAIL_SIZE == (300, 400)"

# 2. Directory structure
test -d data/page_images && echo "✅ Directory exists" || echo "❌ Directory missing"

# 3. Docker Compose validation
docker-compose -f docker/docker-compose.yml config > /dev/null && echo "✅ Valid" || echo "❌ Invalid"

# 4. Image utils unit tests
pytest tests/test_image_utils.py -v --cov=src.processing.image_utils --cov-report=term-missing
# Expected: 95%+ coverage, all tests pass

# 5. Storage tests
pytest src/storage/test_storage.py::test_add_visual_embedding_with_image_paths -v
# Expected: New tests pass, existing tests still pass

# 6. Import validation (no errors)
python -c "
from src.config.image_config import PAGE_IMAGE_DIR, THUMBNAIL_SIZE
from src.processing.image_utils import save_page_image, generate_thumbnail
from src.storage.chroma_client import ChromaClient
print('✅ All imports successful')
"
```

**Success Criteria:**
- [ ] All configuration constants defined and validated
- [ ] `data/page_images/` directory exists and is writable
- [ ] Docker Compose validates with new volume mount
- [ ] Image utils tests pass with 95%+ coverage
- [ ] Storage tests pass (new + existing)
- [ ] No import errors

**Gate Pass Condition:** ALL criteria met

---

### Wave 2 Gate: Processing Integration Complete

**Objective:** Verify images are saved during document processing

**Prerequisites:**
- Wave 1 gate passed
- parser-agent: Parser integration complete
- visual-processor-agent: Processor updates complete

**Validation Tests:**

```python
# integration_test_wave2.py

def test_end_to_end_image_persistence():
    """Test that uploading a document saves page images."""
    import requests
    from pathlib import Path

    # 1. Upload test PDF
    with open('tests/data/test_document.pdf', 'rb') as f:
        response = requests.post(
            'http://localhost:8000/upload',
            files={'file': f}
        )
    assert response.status_code == 200

    # 2. Wait for processing
    time.sleep(5)

    # 3. Check that images were created
    page_image_dir = Path('data/page_images')
    doc_dirs = list(page_image_dir.glob('*'))
    assert len(doc_dirs) > 0, "No document directories created"

    # 4. Verify images exist
    latest_dir = sorted(doc_dirs, key=lambda p: p.stat().st_mtime)[-1]
    png_files = list(latest_dir.glob('page*.png'))
    jpg_files = list(latest_dir.glob('page*_thumb.jpg'))

    assert len(png_files) > 0, "No PNG images found"
    assert len(jpg_files) > 0, "No thumbnail images found"
    assert len(png_files) == len(jpg_files), "Mismatch between PNGs and thumbnails"

    # 5. Query ChromaDB for metadata
    from src.storage.chroma_client import ChromaClient
    client = ChromaClient()

    # Get latest document from visual collection
    results = client.collection_manager.get_collection('visual').get(limit=10)

    # Find entries for our document
    doc_entries = [
        m for m in results['metadatas']
        if latest_dir.name in m.get('image_path', '')
    ]

    assert len(doc_entries) > 0, "No ChromaDB entries with image_path"
    assert all('image_path' in m for m in doc_entries), "Missing image_path in metadata"
    assert all('thumb_path' in m for m in doc_entries), "Missing thumb_path in metadata"

    print(f"✅ Wave 2 validation passed: {len(doc_entries)} pages with images")

def test_processing_performance_impact():
    """Verify image saving doesn't slow processing by >10%."""
    import time

    # Measure baseline (if we have it from before)
    # Or just verify current processing is reasonable

    start = time.time()
    # Process document
    elapsed = time.time() - start

    # Should process typical 10-page PDF in < 60 seconds
    assert elapsed < 60, f"Processing too slow: {elapsed}s"
    print(f"✅ Processing time acceptable: {elapsed:.1f}s")
```

**Manual Testing:**

```bash
# 1. Upload test document
curl -X POST -F "file=@tests/data/test_document.pdf" http://localhost:8000/upload

# 2. Check images created
ls -lh data/page_images/$(ls -t data/page_images/ | head -1)/
# Expected: page001.png, page001_thumb.jpg, page002.png, page002_thumb.jpg, ...

# 3. Check file sizes
du -sh data/page_images/$(ls -t data/page_images/ | head -1)/
# Expected: PNGs ~100-500KB each, thumbnails ~20-50KB each

# 4. Verify image quality (manual check)
open data/page_images/$(ls -t data/page_images/ | head -1)/page001.png
open data/page_images/$(ls -t data/page_images/ | head -1)/page001_thumb.jpg
# Expected: Images render correctly, thumbnails readable
```

**Success Criteria:**
- [ ] Uploading PDF creates image files
- [ ] Both full PNG and thumbnail JPG created per page
- [ ] ChromaDB metadata includes `image_path` and `thumb_path`
- [ ] Processing time increase <10% vs baseline
- [ ] Existing tests still pass (backward compatibility)
- [ ] No disk space leaks (images in correct location)

**Gate Pass Condition:** ALL criteria met

---

### Wave 3 Gate: Backend API Complete

**Objective:** Verify API endpoints return correct data

**Prerequisites:**
- Wave 2 gate passed
- api-agent: API endpoints complete

**Validation Tests:**

```bash
# API endpoint tests

# 1. Test GET /documents (list)
curl -s http://localhost:8002/documents | jq .
# Expected: JSON with documents array, total, limit, offset

# 2. Test pagination
curl -s "http://localhost:8002/documents?limit=5&offset=0" | jq '.documents | length'
# Expected: 5 (or fewer if less than 5 documents)

# 3. Test search
curl -s "http://localhost:8002/documents?search=test" | jq '.documents[].filename'
# Expected: Only filenames containing "test"

# 4. Test GET /documents/{doc_id}
DOC_ID=$(curl -s http://localhost:8002/documents | jq -r '.documents[0].doc_id')
curl -s "http://localhost:8002/documents/$DOC_ID" | jq .
# Expected: Detailed document with pages, chunks, metadata

# 5. Test image serving
DOC_ID=$(curl -s http://localhost:8002/documents | jq -r '.documents[0].doc_id')
curl -I "http://localhost:8002/images/$DOC_ID/page001_thumb.jpg"
# Expected: 200 OK, Content-Type: image/jpeg, Cache-Control header

# 6. Test 404 handling
curl -I "http://localhost:8002/documents/nonexistent"
# Expected: 404 Not Found

curl -I "http://localhost:8002/images/nonexistent/page001.png"
# Expected: 404 Not Found

# 7. Test path traversal prevention
curl -I "http://localhost:8002/images/../../../etc/passwd"
# Expected: 403 Forbidden (or 404)
```

**Automated API Tests:**

```python
# test_documents_api.py (excerpt)

def test_get_documents_returns_valid_schema(client):
    """Test response schema matches contract."""
    response = client.get("/documents")
    assert response.status_code == 200
    data = response.json()

    # Validate schema
    assert "documents" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data

    if data["documents"]:
        doc = data["documents"][0]
        assert "doc_id" in doc
        assert "filename" in doc
        assert "page_count" in doc
        assert "chunk_count" in doc
        assert "date_added" in doc

def test_api_performance_targets(client):
    """Verify API meets performance targets."""
    import time

    # Test GET /documents latency
    start = time.time()
    response = client.get("/documents")
    latency = time.time() - start
    assert latency < 0.5, f"GET /documents too slow: {latency}s"

    # Test GET /documents/{id} latency
    if response.json()["documents"]:
        doc_id = response.json()["documents"][0]["doc_id"]
        start = time.time()
        response = client.get(f"/documents/{doc_id}")
        latency = time.time() - start
        assert latency < 0.2, f"GET /documents/{{id}} too slow: {latency}s"
```

**Success Criteria:**
- [ ] GET /documents returns valid JSON
- [ ] Pagination works correctly
- [ ] Search filtering works
- [ ] GET /documents/{id} returns details
- [ ] GET /images/{id}/{file} serves images
- [ ] 404 responses for missing resources
- [ ] Path traversal attempts blocked
- [ ] CORS headers present
- [ ] Performance targets met
- [ ] API tests pass with 95%+ coverage

**Gate Pass Condition:** ALL criteria met

---

### Wave 4 Gate: Frontend UI Complete

**Objective:** Verify UI displays documents with thumbnails

**Prerequisites:**
- Wave 3 gate passed
- ui-agent: UI implementation complete

**Manual UI Testing Checklist:**

```
Browser: Chrome
[ ] Navigate to http://localhost:8002/monitor
[ ] See "Processing" and "Documents" tabs
[ ] Click "Documents" tab
[ ] See loading state briefly
[ ] See document list table
[ ] Thumbnails load and display correctly
[ ] Filename column shows full names
[ ] Doc ID column shows truncated IDs (with tooltip on hover)
[ ] Page count and chunk count display
[ ] Date column shows relative time ("2 hours ago")
[ ] Search input field present
[ ] Type in search - list filters
[ ] Sort dropdown present
[ ] Change sort order - list re-orders
[ ] No console errors (open DevTools)
[ ] Mobile responsive (resize window)

Browser: Firefox
[ ] Repeat above tests
[ ] Verify images load

Browser: Safari
[ ] Repeat above tests
[ ] Verify images load
```

**Automated UI Tests:**

```javascript
// UI integration test (can be run with Puppeteer or Playwright)

test('Documents tab displays and functions correctly', async () => {
  const page = await browser.newPage();
  await page.goto('http://localhost:8002/monitor');

  // Click Documents tab
  await page.click('button[data-tab="documents"]');

  // Wait for list to load
  await page.waitForSelector('#documents-view table', { timeout: 5000 });

  // Check that rows exist
  const rows = await page.$$('#documents-view table tbody tr');
  expect(rows.length).toBeGreaterThan(0);

  // Check that thumbnails are present
  const thumbnails = await page.$$('#documents-view table img');
  expect(thumbnails.length).toBeGreaterThan(0);

  // Check that first thumbnail loads
  const firstThumb = thumbnails[0];
  const naturalWidth = await firstThumb.evaluate(img => img.naturalWidth);
  expect(naturalWidth).toBeGreaterThan(0);

  // Test search
  await page.type('#document-search', 'test');
  await page.waitForTimeout(500); // Debounce
  const filteredRows = await page.$$('#documents-view table tbody tr');
  expect(filteredRows.length).toBeLessThanOrEqual(rows.length);

  // No console errors
  const errors = await page.evaluate(() => {
    return window.testErrors || [];
  });
  expect(errors.length).toBe(0);
});
```

**Success Criteria:**
- [ ] Documents tab visible and clickable
- [ ] List loads and displays documents
- [ ] Thumbnails render correctly
- [ ] Search functionality works
- [ ] Sort functionality works
- [ ] No JavaScript console errors
- [ ] Works in Chrome, Firefox, Safari
- [ ] Mobile responsive (basic)
- [ ] Empty state handles gracefully
- [ ] Error states handle gracefully

**Gate Pass Condition:** ALL criteria met

---

## Final Integration Validation

### End-to-End Workflow Test

```python
def test_complete_workflow():
    """Test complete workflow from upload to UI display."""

    # 1. Upload document
    response = requests.post(
        'http://localhost:8000/upload',
        files={'file': open('tests/data/sample.pdf', 'rb')}
    )
    assert response.status_code == 200

    # 2. Wait for processing
    time.sleep(5)

    # 3. Verify images on disk
    page_images = Path('data/page_images')
    doc_dirs = list(page_images.glob('*'))
    assert len(doc_dirs) > 0

    # 4. Query API
    response = requests.get('http://localhost:8002/documents')
    assert response.status_code == 200
    docs = response.json()['documents']
    assert len(docs) > 0
    assert docs[0]['has_images'] == True

    # 5. Get document details
    doc_id = docs[0]['doc_id']
    response = requests.get(f'http://localhost:8002/documents/{doc_id}')
    assert response.status_code == 200
    detail = response.json()
    assert len(detail['pages']) > 0
    assert detail['pages'][0]['thumb_path'] is not None

    # 6. Fetch thumbnail
    thumb_url = detail['pages'][0]['thumb_path']
    response = requests.get(f'http://localhost:8002{thumb_url}')
    assert response.status_code == 200
    assert response.headers['content-type'] == 'image/jpeg'
    assert len(response.content) > 0

    print("✅ End-to-end workflow validated")
```

### Performance Benchmark Suite

```python
def test_performance_benchmarks():
    """Validate all performance targets."""

    metrics = {}

    # 1. Image save performance
    from PIL import Image
    from src.processing.image_utils import save_page_image

    img = Image.new('RGB', (1200, 1600))
    start = time.time()
    save_page_image(img, 'perf-test', 1)
    metrics['image_save'] = time.time() - start
    assert metrics['image_save'] < 0.5, "Image save too slow"

    # 2. API list performance
    start = time.time()
    response = requests.get('http://localhost:8002/documents')
    metrics['api_list'] = time.time() - start
    assert metrics['api_list'] < 0.5, "API list too slow"

    # 3. API detail performance
    doc_id = response.json()['documents'][0]['doc_id']
    start = time.time()
    response = requests.get(f'http://localhost:8002/documents/{doc_id}')
    metrics['api_detail'] = time.time() - start
    assert metrics['api_detail'] < 0.2, "API detail too slow"

    # 4. Image serve performance
    start = time.time()
    response = requests.get(f'http://localhost:8002/images/{doc_id}/page001_thumb.jpg')
    metrics['image_serve'] = time.time() - start
    assert metrics['image_serve'] < 0.1, "Image serve too slow"

    # 5. Processing overhead
    # (Requires baseline measurement from before feature)
    # Target: <10% increase

    print("Performance metrics:")
    for key, value in metrics.items():
        print(f"  {key}: {value*1000:.1f}ms")

    return metrics
```

### Backward Compatibility Test

```python
def test_backward_compatibility():
    """Verify system works with documents that don't have images."""

    # 1. Query documents
    response = requests.get('http://localhost:8002/documents')
    docs = response.json()['documents']

    # 2. Find document without images (if any exist from before)
    old_docs = [d for d in docs if not d.get('has_images', True)]

    if old_docs:
        # 3. Get details
        doc_id = old_docs[0]['doc_id']
        response = requests.get(f'http://localhost:8002/documents/{doc_id}')
        assert response.status_code == 200

        # 4. Verify nulls handled gracefully
        detail = response.json()
        for page in detail['pages']:
            # image_path and thumb_path should be null, not missing
            assert 'image_path' in page
            assert 'thumb_path' in page

    # 5. Check UI handles missing thumbnails
    # (Manual test: Should show placeholder icon)

    print("✅ Backward compatibility validated")
```

---

## Security Audit

### Security Test Checklist

```bash
# 1. Path traversal prevention
curl -I "http://localhost:8002/images/../../../etc/passwd"
# Expected: 403 or 404

curl -I "http://localhost:8002/images/..%2F..%2F..%2Fetc%2Fpasswd"
# Expected: 403 or 404

# 2. File extension validation
curl -I "http://localhost:8002/images/test-doc/malicious.sh"
# Expected: 403 or 404

# 3. doc_id validation
curl -I "http://localhost:8002/images/../../etc/page001.png"
# Expected: 403 or 400

# 4. SQL injection (n/a - using ChromaDB, but test anyway)
curl "http://localhost:8002/documents?search='; DROP TABLE--"
# Expected: 200 (search finds nothing, doesn't crash)

# 5. XSS prevention
curl "http://localhost:8002/documents?search=<script>alert('xss')</script>"
# Expected: 200 (no script execution in response)
```

---

## Acceptance Criteria

### Feature Complete Checklist

- [ ] **Infrastructure**
  - [ ] `data/page_images/` directory exists
  - [ ] Docker volume mounted
  - [ ] Configuration validated

- [ ] **Image Persistence**
  - [ ] Images saved during processing
  - [ ] Thumbnails generated
  - [ ] Paths stored in ChromaDB

- [ ] **API Endpoints**
  - [ ] GET /documents working
  - [ ] GET /documents/{id} working
  - [ ] GET /images/{id}/{file} working
  - [ ] Error handling correct
  - [ ] Security validated

- [ ] **UI**
  - [ ] Documents tab visible
  - [ ] List displays correctly
  - [ ] Thumbnails load
  - [ ] Search works
  - [ ] Sort works
  - [ ] Cross-browser compatible

- [ ] **Performance**
  - [ ] Processing overhead <10%
  - [ ] API latency targets met
  - [ ] Image serving fast (<100ms)

- [ ] **Quality**
  - [ ] All tests passing
  - [ ] 95%+ test coverage
  - [ ] No security vulnerabilities
  - [ ] Backward compatible
  - [ ] Documentation updated

**Final Gate:** ALL items checked

---

**Document Version:** 1.0
**Last Updated:** 2025-10-11

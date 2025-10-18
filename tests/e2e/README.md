# E2E Integration Test Suite

Comprehensive end-to-end tests for the enhanced mode bidirectional highlighting feature.

## Overview

This test suite validates the complete pipeline from document processing through structure extraction, storage, search, and research API integration, with focus on bidirectional highlighting between page bounding boxes and markdown text chunks.

### Test Coverage

- **34 total tests** across 3 test files
- **12 test classes** covering different aspects
- **Full pipeline validation** from upload to interactive highlighting

## Test Files

### 1. test_enhanced_mode_e2e.py (5 tests)

Tests document processing with enhanced metadata storage.

**Test Classes:**
- `TestEnhancedModeE2E` (5 tests)

**Coverage:**
- Upload and processing pipeline
- Structure retrieval with decompression
- Page-to-chunk mapping
- Enhanced visual metadata fields
- Enhanced text metadata fields

**Key Scenarios:**
```python
# Test structure compression/decompression
test_structure_retrieval_with_decompression()

# Test querying chunks by page
test_page_chunk_mapping()

# Test all enhanced metadata fields stored correctly
test_enhanced_visual_metadata_fields()
test_enhanced_text_metadata_fields()
```

### 2. test_research_to_details_flow.py (17 tests)

Tests the user journey from research query to document details navigation.

**Test Classes:**
- `TestResearchQueryWithChunkContext` (4 tests)
- `TestResearchAPIResponseFormat` (3 tests)
- `TestDeepLinkNavigation` (3 tests)
- `TestMarkdownChunkMarkers` (3 tests)
- `TestEdgeCases` (4 tests)

**Coverage:**
- Research API chunk_id inclusion
- Chunk_id format consistency
- URL-based navigation with chunk parameter
- Markdown chunk markers
- Edge cases (hyphens, boundaries, mixed results)

**Key Scenarios:**
```python
# Test chunk_id in research results
test_source_document_includes_chunk_id()
test_chunk_id_extraction_from_metadata()

# Test deep link navigation
test_details_url_with_chunk_parameter()
test_navigation_from_research_to_details()

# Test markdown markers
test_markdown_chunk_marker_format()
test_chunk_markers_match_chromadb()
```

### 3. test_bidirectional_highlighting.py (12 tests)

Tests data flow for bidirectional highlighting between bboxes and chunks.

**Test Classes:**
- `TestBboxToChunkDataFlow` (2 tests)
- `TestChunkToBboxDataFlow` (2 tests)
- `TestCoordinateSystemConsistency` (4 tests)
- `TestEdgeCases` (4 tests)

**Coverage:**
- Bbox → chunk data flow
- Chunk → bbox data flow
- Coordinate system consistency
- Multi-element highlighting
- Edge cases (empty structure, missing bboxes, special characters)

**Key Scenarios:**
```python
# Test bbox to chunk mapping
test_structure_bboxes_have_chunk_context()
test_fetch_chunk_metadata_for_bbox()

# Test chunk to bbox mapping
test_chunk_markers_map_to_bboxes()
test_chunk_with_multiple_related_elements()

# Test coordinate system
test_bbox_format_documentation()
test_bbox_to_frontend_conversion()
```

## Running Tests

### Prerequisites

Start required services before running tests:

```bash
./scripts/start-all.sh
```

Verify services are running:
```bash
./scripts/status.sh
```

Required services:
- ChromaDB (port 8001)
- Worker API (port 8002)

### Run All E2E Tests

```bash
# Using test runner script (recommended)
./scripts/run_e2e_tests.sh

# With service management
./scripts/run_e2e_tests.sh --start-services --stop-services

# With coverage
./scripts/run_e2e_tests.sh --coverage

# Skip slow tests
./scripts/run_e2e_tests.sh --skip-slow
```

### Run Specific Test Files

```bash
# Enhanced mode tests
pytest tests/e2e/test_enhanced_mode_e2e.py -v

# Research flow tests
pytest tests/e2e/test_research_to_details_flow.py -v

# Bidirectional highlighting tests
pytest tests/e2e/test_bidirectional_highlighting.py -v
```

### Run Specific Test Classes

```bash
# Bbox to chunk data flow
pytest tests/e2e/test_bidirectional_highlighting.py::TestBboxToChunkDataFlow -v

# Research API response format
pytest tests/e2e/test_research_to_details_flow.py::TestResearchAPIResponseFormat -v
```

### Run with Markers

```bash
# Only integration tests
pytest tests/e2e/ -v -m integration

# Skip slow tests
pytest tests/e2e/ -v -m "not slow"

# Both markers
pytest tests/e2e/ -v -m "integration and not slow"
```

## Test Requirements

### Service Dependencies

All tests require running services:
- **ChromaDB** - Document storage and retrieval
- **Worker API** - Document processing and status

Tests will automatically skip if services are unavailable:
```
SKIPPED - Required services not running. Run ./scripts/start-all.sh first.
```

### Environment Configuration

Configure via environment variables:

```bash
# ChromaDB configuration
export CHROMA_HOST=localhost
export CHROMA_PORT=8001

# Worker API configuration
export WORKER_API_URL=http://localhost:8002

# Copyparty configuration
export COPYPARTY_URL=http://localhost:8000
```

## Test Fixtures

### Provided Fixtures

See `fixtures/conftest.py` for all available fixtures:

- **Service clients:** `chromadb_client`, `worker_api_client`, `research_api_client`
- **Service checks:** `services_available`, `skip_if_services_unavailable`
- **Test data:** `test_doc_ids`, `cleanup_test_documents`
- **Helpers:** `wait_for_processing_helper`

### Auto-Cleanup

Tests automatically clean up data after execution:

```python
def test_something(chromadb_client, test_doc_ids):
    doc_id = "test-doc-123"
    test_doc_ids.append(doc_id)  # Add to cleanup list

    # Test code...

    # Cleanup happens automatically
```

## Coverage Reports

### Generate Coverage

```bash
# With test runner
./scripts/run_e2e_tests.sh --coverage

# With pytest directly
pytest tests/e2e/ -v --cov=src --cov-report=html:htmlcov/e2e --cov-report=term
```

### View Coverage

```bash
# Open HTML report
open htmlcov/e2e/index.html

# Terminal report
pytest tests/e2e/ --cov=src --cov-report=term
```

### Coverage Targets

- **Overall:** ≥80% for new code
- **Enhanced metadata:** 100% (critical path)
- **Structure API:** 100% (critical path)
- **Research integration:** ≥90%
- **Bidirectional flow:** ≥85%

## Test Output

### Successful Run

```
============================= test session starts ==============================
collected 34 items

tests/e2e/test_enhanced_mode_e2e.py .....                                [ 14%]
tests/e2e/test_research_to_details_flow.py .................             [ 64%]
tests/e2e/test_bidirectional_highlighting.py ............                [100%]

============================== 34 passed in 45.23s ==============================
```

### With Coverage

```
============================= test session starts ==============================
collected 34 items

tests/e2e/test_enhanced_mode_e2e.py .....                                [ 14%]
tests/e2e/test_research_to_details_flow.py .................             [ 64%]
tests/e2e/test_bidirectional_highlighting.py ............                [100%]

---------- coverage: platform darwin, python 3.13.3 -----------
Name                                           Stmts   Miss  Cover
------------------------------------------------------------------
src/processing/handlers/enhanced_metadata.py      89      2    98%
src/storage/compression.py                        45      0   100%
src/storage/metadata_schema.py                   156      8    95%
src/research/chunk_extractor.py                   42      0   100%
src/api/research.py                              120     12    90%
------------------------------------------------------------------
TOTAL                                            452     22    95%

Coverage HTML written to htmlcov/e2e/index.html
```

## Debugging Failed Tests

### View Detailed Output

```bash
# Verbose output with stdout
pytest tests/e2e/ -v -s

# Stop on first failure
pytest tests/e2e/ -v -x

# Show local variables on failure
pytest tests/e2e/ -v -l

# Full traceback
pytest tests/e2e/ -v --tb=long
```

### Check Service Status

```bash
# Check all services
./scripts/status.sh

# Check ChromaDB
curl http://localhost:8001/api/v1/heartbeat

# Check Worker API
curl http://localhost:8002/health
```

### View Logs

```bash
# Worker logs
tail -f logs/worker-native.log

# Docker logs
docker-compose -f docker/docker-compose.yml logs -f
```

## Known Limitations

### Tests Requiring Manual Validation

Some aspects require manual testing in browser:

1. **Frontend Interactions:**
   - Click handlers
   - Hover effects
   - DOM manipulation
   - CSS highlighting

2. **Visual Validation:**
   - Bbox overlay rendering
   - Highlight colors and styles
   - Responsive behavior

3. **User Experience:**
   - Smooth scrolling
   - Transition animations
   - Keyboard navigation

These are documented but not automated.

### Service-Dependent Tests

All E2E tests require running services. Cannot run in pure unit test mode.

### Sample Documents

Full upload-to-processing tests require sample documents. Currently skipped if unavailable.

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest

    services:
      chromadb:
        image: chromadb/chroma:latest
        ports:
          - 8001:8001

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Start services
        run: ./scripts/start-all.sh

      - name: Run E2E tests
        run: ./scripts/run_e2e_tests.sh --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./htmlcov/e2e/coverage.xml
```

## Contributing

### Adding New Tests

1. Add test to appropriate file (enhanced_mode, research_flow, highlighting)
2. Use `@pytest.mark.integration` decorator
3. Use `@pytest.mark.slow` for tests >5s
4. Add to `test_doc_ids` for auto-cleanup
5. Document test scenario in docstring
6. Update this README with test count

### Test Guidelines

- **Isolation:** Each test should be independent
- **Cleanup:** Use `test_doc_ids` fixture for auto-cleanup
- **Markers:** Use appropriate markers (`integration`, `slow`)
- **Documentation:** Clear docstrings explaining data flow
- **Real Data:** Use real ChromaDB, no mocks
- **Reproducibility:** Tests should be deterministic

## Support

### Issues

Report test failures with:
1. Full pytest output (`-v -s`)
2. Service status (`./scripts/status.sh --json`)
3. Environment details (OS, Python version)
4. Steps to reproduce

### Questions

See also:
- `fixtures/README.md` - Fixture documentation
- `fixtures/helpers.py` - Helper function reference
- Project docs: `docs/TESTING.md`

## Summary

- **34 tests** validating bidirectional highlighting
- **3 test files** covering different aspects
- **Comprehensive coverage** of enhanced mode pipeline
- **Auto-cleanup** for test data
- **Service-based** integration testing
- **CI/CD ready** with coverage reporting

Run tests with:
```bash
./scripts/run_e2e_tests.sh
```

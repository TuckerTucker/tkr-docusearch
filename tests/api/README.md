# API Tests

Unit and integration tests for the DocuSearch API endpoints.

## Test Files

### `test_markdown_endpoint.py`
Comprehensive tests for the markdown download API endpoint (`/api/document/{doc_id}/markdown`).

**Test Coverage:**
- ✅ Successful downloads (200 OK)
- ✅ Document not found (404)
- ✅ Markdown not available (404)
- ✅ Markdown file missing (404)
- ✅ Invalid doc_id format (400)
- ✅ Filename sanitization
- ✅ Header validation
- ✅ Performance (<100ms)
- ✅ Wave 2 integration test (CRITICAL gate)

**Total Tests:** 24 tests, all passing

## Running Tests

### Run all API tests
```bash
pytest tests/api/ -v
```

### Run markdown endpoint tests only
```bash
pytest tests/api/test_markdown_endpoint.py -v
```

### Run Wave 2 integration test (gate for Wave 3)
```bash
pytest tests/api/test_markdown_endpoint.py::TestWave2Integration::test_wave2_integration -v
```

### Run with coverage (requires pytest-cov)
```bash
pytest tests/api/test_markdown_endpoint.py --cov=src/api/routes/markdown --cov-report=term-missing
```

## Test Structure

### Fixtures
- `mock_storage_client`: Mock ChromaDB client with test data
- `markdown_dir`: Temporary directory with test markdown files
- `mock_app`: FastAPI test app with mocked dependencies
- `client`: FastAPI TestClient for making requests

### Test Classes

1. **TestDownloadMarkdownSuccess** - Successful download scenarios
2. **TestDownloadMarkdownNotFound** - 404 when document doesn't exist
3. **TestDownloadMarkdownNotAvailable** - 404 when no markdown available
4. **TestDownloadMarkdownFileMissing** - 404 when file deleted
5. **TestDownloadMarkdownInvalidDocId** - 400 for invalid formats
6. **TestFilenameSanitization** - Filename cleaning validation
7. **TestDownloadPerformance** - Performance validation (<100ms)
8. **TestWave2Integration** - Critical integration test (Wave 3 gate)
9. **TestErrorHandling** - Comprehensive error scenarios
10. **TestHeaderValidation** - HTTP header validation
11. **TestEdgeCases** - Edge cases and boundary conditions
12. **TestFilenameSanitizationUnit** - Unit tests for sanitize_filename()

## Wave 2 Integration Test

The `test_wave2_integration` test is **CRITICAL** - it must pass before Wave 3 (UI integration) can begin.

**Validates:**
- API downloads markdown correctly
- Headers match specification exactly
- Content matches stored file
- Filename is properly sanitized

**Status:** ✅ PASSED - Wave 3 can proceed

## Test Results

```
======================== 24 passed, 14 warnings in 3.70s ========================
```

**Success Criteria:**
- ✅ All 24 tests passing (100% pass rate)
- ✅ Test successful downloads (200 OK)
- ✅ Test all 404 scenarios (3 types)
- ✅ Test 400 invalid doc_id
- ✅ Test header correctness
- ✅ Test filename sanitization
- ✅ Performance validated (<100ms)
- ✅ Wave 2 integration test passes

## Contract Compliance

All tests follow the API specification in:
- `.context-kit/orchestration/markdown-storage-export/integration-contracts/markdown-api-contract.md`

## Next Steps

With Wave 2 complete and all tests passing:
1. ✅ Wave 2 gate: PASSED
2. ➡️ Wave 3: UI integration can begin
3. ➡️ Agent 6 can implement download button in UI

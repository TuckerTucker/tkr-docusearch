# Integration Tests for .doc Conversion

This directory contains comprehensive integration tests for the legacy .doc to .docx conversion feature introduced in Wave 8.

## Overview

The .doc conversion feature enables the system to process legacy Microsoft Word `.doc` files by:
1. Detecting `.doc` files in the processing pipeline
2. Converting them to `.docx` format using the `legacy-office-converter` Docker service
3. Processing the converted file with Docling
4. Preserving conversion metadata throughout the pipeline
5. Making the content searchable

## Test Structure

### Test Files

1. **`fixtures_doc_conversion.py`** - Shared test fixtures
   - Service configuration fixtures
   - Test document fixtures
   - Mock response fixtures
   - Storage and cleanup utilities

2. **`test_legacy_office_service.py`** - Service-level integration tests
   - Health endpoint validation
   - Endpoint functionality tests
   - Concurrent request handling
   - Error handling scenarios
   - Client integration tests

3. **`test_doc_conversion_e2e.py`** - End-to-end pipeline tests
   - Complete processing pipeline validation
   - Metadata propagation tests
   - Search integration tests
   - Error handling tests
   - Path translation tests

### Test Categories

#### Service Tests (test_legacy_office_service.py)
- ✅ Service health checks
- ✅ Capability advertisement (PPTX + .doc)
- ✅ Endpoint existence and validation
- ✅ Concurrent request handling
- ✅ Client wrapper integration
- ✅ Error handling and edge cases

#### E2E Pipeline Tests (test_doc_conversion_e2e.py)
- ✅ .doc file detection and conversion
- ✅ Original filename preservation
- ✅ Metadata schema compliance
- ✅ Complete processing pipeline
- ✅ Metadata storage in ChromaDB
- ✅ Search integration
- ✅ Path translation (native ↔ Docker)
- ✅ Error scenarios

## Prerequisites

### Required Services

1. **ChromaDB** (port 8001)
   ```bash
   docker compose up -d chromadb
   ```

2. **legacy-office-converter** (port 8003)
   ```bash
   docker compose up -d legacy-office-converter
   ```

3. **Worker Service** (port 8002) - for E2E tests
   ```bash
   ./scripts/run-worker-native.sh
   ```

### Environment Variables

```bash
# Legacy office service (optional, defaults shown)
export LEGACY_OFFICE_HOST=localhost
export LEGACY_OFFICE_PORT=8003

# ChromaDB (optional, defaults shown)
export CHROMA_HOST=localhost
export CHROMA_PORT=8001
```

## Running Tests

### Quick Start

```bash
# Start required services
./scripts/start-all.sh

# Run all .doc conversion tests
pytest tests/integration/test_legacy_office_service.py \
       tests/integration/test_doc_conversion_e2e.py \
       -v

# Or run specific test files
pytest tests/integration/test_legacy_office_service.py -v
pytest tests/integration/test_doc_conversion_e2e.py -v
```

### Running Individual Test Classes

```bash
# Service health tests
pytest tests/integration/test_legacy_office_service.py::TestLegacyOfficeServiceHealth -v

# Doc conversion endpoint tests
pytest tests/integration/test_legacy_office_service.py::TestDocConversionEndpoint -v

# E2E pipeline tests
pytest tests/integration/test_doc_conversion_e2e.py::TestDocConversionE2E -v

# Metadata propagation tests
pytest tests/integration/test_doc_conversion_e2e.py::TestMetadataPropagation -v
```

### Running Specific Tests

```bash
# Test health endpoint shows capabilities
pytest tests/integration/test_legacy_office_service.py::TestLegacyOfficeServiceHealth::test_health_endpoint_shows_capabilities -v

# Test original filename preserved
pytest tests/integration/test_doc_conversion_e2e.py::TestDocConversionE2E::test_original_filename_preserved_in_metadata -v

# Test concurrent requests
pytest tests/integration/test_legacy_office_service.py::TestConcurrentCapabilities::test_concurrent_pptx_and_doc_conversions -v
```

### Test Markers

```bash
# Run only integration tests
pytest tests/integration/ -v -m integration

# Skip slow tests
pytest tests/integration/ -v -m "not slow"

# Run only slow tests
pytest tests/integration/ -v -m slow
```

### Output Options

```bash
# Verbose output with logging
pytest tests/integration/ -v -s

# Show test coverage
pytest tests/integration/ -v --cov=tkr_docusearch.processing

# Generate HTML coverage report
pytest tests/integration/ -v --cov=tkr_docusearch.processing --cov-report=html

# JSON output for CI
pytest tests/integration/ -v --json-report --json-report-file=test-report.json
```

## Test Coverage

### Service Integration Tests (16 test cases)

**TestLegacyOfficeServiceHealth (3 tests)**
- ✅ Health endpoint accessible
- ✅ Health shows both capabilities (PPTX + .doc)
- ✅ Root endpoint provides service info

**TestDocConversionEndpoint (4 tests)**
- ✅ /convert-doc endpoint exists
- ✅ Requires file_path parameter
- ✅ Handles missing files (404)
- ✅ Returns expected response format

**TestPptxRenderingEndpoint (2 tests)**
- ✅ /render endpoint exists
- ✅ Validates required parameters

**TestConcurrentCapabilities (2 tests)**
- ✅ Handles concurrent PPTX + .doc requests
- ✅ Handles multiple concurrent .doc requests (slow)

**TestLegacyOfficeClient (4 tests)**
- ✅ Client health check
- ✅ Client get_info()
- ✅ Client error handling
- ✅ Singleton pattern

**TestServiceErrorHandling (3 tests)**
- ✅ Invalid JSON payload
- ✅ Missing Content-Type header
- ✅ Timeout handling

### E2E Pipeline Tests (12 test cases)

**TestDocConversionE2E (4 tests)**
- ✅ .doc detection triggers conversion
- ✅ Original filename preserved
- ✅ Metadata follows schema
- ✅ Complete pipeline (mock)

**TestMetadataPropagation (1 test)**
- ✅ Conversion metadata stored in ChromaDB

**TestConvertedDocSearch (1 test)**
- ✅ Converted content is searchable

**TestDocConversionErrorHandling (3 tests)**
- ✅ Service unavailable error
- ✅ Corrupt file error
- ✅ Missing file error

**TestPathTranslation (2 tests)**
- ✅ Native to Docker path translation
- ✅ Docker path passthrough

**Total: 28 test cases**

## Test Fixtures

### Service Fixtures
- `legacy_office_host` - Service host from environment
- `legacy_office_port` - Service port from environment
- `legacy_office_url` - Full service URL
- `legacy_office_client` - Client instance
- `legacy_office_available` - Service availability check
- `skip_if_legacy_office_unavailable` - Auto-skip fixture

### Document Fixtures
- `sample_doc_file` - Sample .doc file (if available)
- `docker_doc_path` - Docker-formatted .doc path
- `docker_pptx_path` - Docker-formatted .pptx path

### Mock Fixtures
- `mock_doc_conversion_result` - Successful conversion response
- `mock_health_response` - Health endpoint response

### Storage Fixtures
- `embedding_engine_instance` - Mock embedding engine
- `storage_client_instance` - Mock ChromaDB client
- `cleanup_converted_files` - Automatic file cleanup

## CI/CD Integration

### GitHub Actions Example

```yaml
name: .doc Conversion Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      chromadb:
        image: chromadb/chroma:latest
        ports:
          - 8001:8000

      legacy-office-converter:
        image: your-registry/legacy-office-converter:latest
        ports:
          - 8003:8003

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run integration tests
        run: |
          pytest tests/integration/test_legacy_office_service.py \
                 tests/integration/test_doc_conversion_e2e.py \
                 -v --cov --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Troubleshooting

### Common Issues

#### 1. Service not available
```
SKIPPED [1] tests/integration/fixtures_doc_conversion.py:91:
Legacy office service not running.
```

**Solution:**
```bash
# Start the service
docker compose up -d legacy-office-converter

# Check service health
curl http://localhost:8003/health
```

#### 2. Test file not found
```
WARNING: No sample .doc file found in fixtures
```

**Solution:**
Tests use mocks and don't require actual `.doc` files. This warning is informational only.

#### 3. Port conflicts
```
ERROR: Cannot start service legacy-office-converter:
Bind for 0.0.0.0:8003 failed: port is already allocated.
```

**Solution:**
```bash
# Find process using port
lsof -i :8003

# Or use different port
export LEGACY_OFFICE_PORT=8004
```

#### 4. ChromaDB connection error
```
ConnectionError: Failed to connect to ChromaDB
```

**Solution:**
```bash
# Start ChromaDB
docker compose up -d chromadb

# Verify it's running
curl http://localhost:8001/api/v1/heartbeat
```

### Debug Mode

Run tests with verbose logging:

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with pytest output
pytest tests/integration/ -v -s --log-cli-level=DEBUG
```

## Best Practices

### Writing New Tests

1. **Use appropriate fixtures** - Leverage existing fixtures from `fixtures_doc_conversion.py`
2. **Mark integration tests** - Use `@pytest.mark.integration`
3. **Mark slow tests** - Use `@pytest.mark.slow` for tests >5s
4. **Skip when services unavailable** - Use `skip_if_legacy_office_unavailable` fixture
5. **Clean up resources** - Use `cleanup_converted_files` fixture
6. **Mock when possible** - Mock file I/O and expensive operations
7. **Test error paths** - Include negative test cases
8. **Document test purpose** - Clear docstrings for each test

### Example Test Template

```python
@pytest.mark.integration
def test_something_important(
    legacy_office_client,
    skip_if_legacy_office_unavailable,
    cleanup_converted_files
):
    """Test that something important works correctly.

    This test validates...
    """
    # Arrange
    doc_path = "/uploads/test.doc"

    # Act
    docx_path = legacy_office_client.convert_doc_to_docx(doc_path)
    cleanup_converted_files.append(docx_path)

    # Assert
    assert docx_path.endswith(".docx")

    logger.info("✓ Test passed")
```

## Related Documentation

- **Architecture**: `docs/LEGACY_OFFICE_SERVICE.md` - Service architecture
- **API Contract**: `docs/PROCESSING_INTERFACE.md` - Processing interface
- **Metadata Schema**: `docs/metadata-schema.json` - Metadata contract
- **Docker Compose**: `docker-compose.yml` - Service configuration
- **Unit Tests**: `tests/processing/test_docling_parser_doc_conversion.py` - Parser unit tests

## Contributing

When adding new tests:

1. Follow existing test structure and naming conventions
2. Add tests to appropriate test class
3. Update test coverage counts in this README
4. Document any new fixtures
5. Ensure tests pass both locally and in CI

## License

Copyright 2025 Tucker. All rights reserved.

---

**Last Updated**: 2025-11-19
**Wave**: 8 (Legacy Office Doc Conversion)
**Author**: Agent-Integration-Testing

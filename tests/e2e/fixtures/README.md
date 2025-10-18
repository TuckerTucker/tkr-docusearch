# E2E Test Fixtures

This directory contains fixtures and sample documents for end-to-end integration testing.

## Directory Structure

```
fixtures/
├── __init__.py                 # Package init
├── conftest.py                 # Pytest fixtures
├── helpers.py                  # Helper utilities
├── README.md                   # This file
└── sample_documents/           # Sample test documents
    ├── complex_pdf.pdf         # PDF with structure (optional)
    ├── simple_text.pdf         # Plain text PDF (optional)
    └── README.md               # Sample docs instructions
```

## Pytest Fixtures

### Service Health Fixtures

- **`chromadb_host`** - ChromaDB host from environment
- **`chromadb_port`** - ChromaDB port from environment
- **`worker_api_url`** - Worker API base URL
- **`copyparty_url`** - Copyparty UI base URL
- **`chromadb_url`** - ChromaDB full URL
- **`services_available`** - Check if required services are running
- **`skip_if_services_unavailable`** - Skip test if services not running

### API Client Fixtures

- **`chromadb_client`** - Real ChromaDB client for E2E tests
- **`worker_api_client`** - HTTP client for Worker API
- **`research_api_client`** - FastAPI test client for Research API

### Test Document Fixtures

- **`fixtures_dir`** - Path to fixtures directory
- **`sample_documents_dir`** - Path to sample documents directory
- **`sample_pdf_with_structure`** - Sample PDF with complex structure (optional)
- **`sample_simple_pdf`** - Sample PDF without structure (optional)

### Test Data Management

- **`test_doc_ids`** - List to track document IDs for cleanup
- **`cleanup_test_documents`** - Auto-cleanup after each test
- **`wait_for_processing_helper`** - Helper function for polling document status

## Helper Functions

### Document Generation

```python
from tests.e2e.fixtures.helpers import create_test_pdf, create_test_pdf_with_structure

# Create simple PDF
pdf_path = create_test_pdf(Path("test.pdf"), content="Test content")

# Create PDF with structure
structured_pdf = create_test_pdf_with_structure(
    Path("structured.pdf"),
    num_pages=3,
    num_headings=5,
    num_tables=2
)
```

### Service Verification

```python
from tests.e2e.fixtures.helpers import verify_chromadb_connection, verify_worker_api_connection

if verify_chromadb_connection():
    print("ChromaDB is accessible")

if verify_worker_api_connection():
    print("Worker API is accessible")
```

### Processing Monitoring

```python
from tests.e2e.fixtures.helpers import wait_for_document_processing

result = wait_for_document_processing(
    client=worker_api_client,
    doc_id="test-doc-123",
    timeout=60
)

if result["status"] == "completed":
    print(f"Processing completed in {result['duration']:.2f}s")
```

### Cleanup

```python
from tests.e2e.fixtures.helpers import cleanup_test_documents, get_document_stats

# Get document stats
stats = get_document_stats(chromadb_client, "test-doc-123")
print(f"Visual embeddings: {stats['visual_embeddings']}")
print(f"Text embeddings: {stats['text_embeddings']}")

# Cleanup
cleanup_stats = cleanup_test_documents(
    chromadb_client,
    doc_ids=["test-doc-123", "test-doc-456"],
    verbose=True
)
print(f"Deleted {cleanup_stats['visual_deleted']} visual, {cleanup_stats['text_deleted']} text")
```

## Usage in Tests

### Basic Test with Auto-Cleanup

```python
@pytest.mark.integration
def test_something(chromadb_client, test_doc_ids):
    """Test with automatic cleanup."""
    doc_id = "test-doc-auto-cleanup"

    # Add to cleanup list
    test_doc_ids.append(doc_id)

    # Test code here
    # ...

    # Cleanup happens automatically via cleanup_test_documents fixture
```

### Test with Service Check

```python
@pytest.mark.integration
def test_requires_services(
    chromadb_client,
    worker_api_client,
    skip_if_services_unavailable
):
    """Test that requires services to be running."""
    # Test will be skipped if services not available
    # ...
```

### Test with Document Processing

```python
@pytest.mark.integration
@pytest.mark.slow
def test_document_processing(
    worker_api_client,
    chromadb_client,
    wait_for_processing_helper,
    test_doc_ids
):
    """Test document processing pipeline."""
    doc_id = "test-processing"
    test_doc_ids.append(doc_id)

    # Trigger processing (implementation depends on webhook setup)
    # ...

    # Wait for completion
    result = wait_for_processing_helper(doc_id, timeout=60)
    assert result["status"] == "completed"

    # Verify results
    stats = get_document_stats(chromadb_client, doc_id)
    assert stats["visual_embeddings"] > 0
```

## Sample Documents

Sample documents are optional. Tests will skip if not available.

To create sample documents:

1. Navigate to `sample_documents/` directory
2. Create PDFs manually or use helper functions:

```python
from pathlib import Path
from tests.e2e.fixtures.helpers import create_test_pdf_with_structure

# Create complex PDF
create_test_pdf_with_structure(
    Path("tests/e2e/fixtures/sample_documents/complex_pdf.pdf"),
    num_pages=5,
    num_headings=10,
    num_tables=3
)
```

3. Add real documents with known structure for more comprehensive testing

## Environment Variables

Configure services via environment:

- `CHROMA_HOST` - ChromaDB host (default: localhost)
- `CHROMA_PORT` - ChromaDB port (default: 8001)
- `WORKER_API_URL` - Worker API URL (default: http://localhost:8002)
- `COPYPARTY_URL` - Copyparty URL (default: http://localhost:8000)

## Running E2E Tests

```bash
# Start services first
./scripts/start-all.sh

# Run all E2E tests
pytest tests/e2e/ -v

# Run specific test file
pytest tests/e2e/test_enhanced_mode_e2e.py -v

# Run with coverage
pytest tests/e2e/ -v --cov=src --cov-report=html

# Run only integration tests
pytest tests/e2e/ -v -m integration

# Skip slow tests
pytest tests/e2e/ -v -m "not slow"
```

## Notes

- E2E tests require running services (ChromaDB, Worker API)
- Tests will skip automatically if services unavailable
- Auto-cleanup removes test data after each test
- Use `test_doc_ids` list to track documents for cleanup
- Mark slow tests with `@pytest.mark.slow`
- Mark tests requiring services with `@pytest.mark.integration`

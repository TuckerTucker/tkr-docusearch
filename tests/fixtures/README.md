# Test Fixtures

This directory contains test fixtures for backend API testing. All files are minimal but valid, designed specifically for testing document processing, upload, and search functionality.

## Available Fixtures

### 1. sample.pdf
**Size:** ~2.5 KB
**Pages:** 2
**Content:** Structured text with headers, bullet points, and body paragraphs

**Purpose:**
- Test PDF parsing and visual processing
- Validate page image generation
- Test multi-page document handling
- Verify visual embedding generation (ColPali)
- Test text chunk extraction from PDF

**Expected Behavior:**
- Generates 2 page images (one per page)
- Creates 2 visual embeddings (one per page)
- Extracts multiple text chunks (depending on chunk size)
- Processing mode: VISUAL (full visual + text processing)

**Test Keywords:** "document processing pipeline", "vector embeddings", "similarity search", "ChromaDB integration"

---

### 2. sample.docx
**Size:** ~37 KB
**Pages:** 1 (logical)
**Content:** Structured document with heading, sections, bullet lists

**Purpose:**
- Test DOCX parsing (Microsoft Word format)
- Validate text-only processing mode
- Test structure extraction from Office documents
- Verify text chunking without visual embeddings

**Expected Behavior:**
- NO page images generated (text-only format)
- NO visual embeddings created
- Extracts text content with structure (headings, lists)
- Generates text chunks with embeddings
- Processing mode: TEXT_ONLY

**Test Keywords:** "document features", "testing notes", "Docling parser", "text embedding handler"

---

### 3. sample.txt
**Size:** ~765 bytes
**Content:** Plain text with ASCII art header, sections, and testing notes

**Purpose:**
- Test plain text file processing
- Validate simple text chunking
- Test text-only embedding generation
- Verify minimal format handling

**Expected Behavior:**
- NO page images generated
- NO visual embeddings created
- Simple text chunking (no structure extraction)
- Generates 1-2 text chunks (depending on settings)
- Processing mode: TEXT_ONLY

**Test Keywords:** "text processing", "plain text", "semantic search", "chunking", "embeddings"

---

### 4. sample.mp3
**Size:** ~15.8 KB
**Duration:** ~1 second
**Format:** MP3 (MPEG-1 Layer III, 44.1kHz, 128kbps, mono)
**Content:** Silent audio

**Purpose:**
- Test audio file handling
- Validate MP3 format recognition
- Test audio metadata extraction
- Verify audio processing pipeline

**Expected Behavior:**
- Recognized as audio format
- Can extract ID3 metadata (if present)
- Supports transcription processing (Whisper ASR)
- Processing mode: AUDIO

**Note:** This is a minimal silent MP3. For transcription testing, replace with an MP3 containing speech.

---

### 5. sample.wav
**Size:** ~32 KB
**Duration:** 1 second
**Format:** WAV (16kHz, 16-bit, mono)
**Content:** Silent audio

**Purpose:**
- Test WAV file handling
- Validate uncompressed audio processing
- Test Whisper ASR default format
- Verify audio chunking

**Expected Behavior:**
- Recognized as audio format
- 16kHz matches Whisper default sample rate
- Supports direct transcription without conversion
- Processing mode: AUDIO

**Note:** This is a minimal silent WAV. For transcription testing, replace with an audio file containing speech.

---

## Usage in Tests

### Basic Upload Test

```python
import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"

def test_upload_pdf(api_client):
    """Test PDF upload and processing."""
    pdf_path = FIXTURES_DIR / "sample.pdf"

    with open(pdf_path, "rb") as f:
        response = api_client.post(
            "/api/upload",
            files={"file": ("sample.pdf", f, "application/pdf")}
        )

    assert response.status_code == 200
    data = response.json()
    assert "doc_id" in data
    assert data["filename"] == "sample.pdf"
    assert data["total_pages"] == 2
```

### Processing Validation Test

```python
def test_processing_complete(api_client, chromadb_client):
    """Test document processing completion."""
    pdf_path = FIXTURES_DIR / "sample.pdf"

    # Upload
    with open(pdf_path, "rb") as f:
        response = api_client.post("/api/upload", files={"file": ("sample.pdf", f)})
    doc_id = response.json()["doc_id"]

    # Wait for processing
    from tests.e2e.fixtures.helpers import wait_for_document_processing
    result = wait_for_document_processing(api_client, doc_id, timeout=60)

    assert result["status"] == "completed"

    # Verify embeddings in ChromaDB
    visual_results = chromadb_client._visual_collection.get(
        where={"doc_id": doc_id}
    )
    text_results = chromadb_client._text_collection.get(
        where={"doc_id": doc_id}
    )

    assert len(visual_results["ids"]) == 2  # 2 pages
    assert len(text_results["ids"]) > 0  # At least 1 text chunk
```

### Search Test

```python
def test_search_fixture_content(search_api_client):
    """Test search against fixture content."""
    # Upload and process sample.pdf first (in setup)

    response = search_api_client.post(
        "/api/search",
        json={
            "query": "document processing pipeline",
            "top_k": 5
        }
    )

    assert response.status_code == 200
    results = response.json()["results"]

    # Should find relevant content from sample.pdf
    assert len(results) > 0
    assert any("sample.pdf" in r["metadata"]["filename"] for r in results)
```

### Format-Specific Test

```python
@pytest.mark.parametrize("fixture,expected_format,expected_embeddings", [
    ("sample.pdf", "VISUAL", {"visual": 2, "text": ">0"}),
    ("sample.docx", "TEXT_ONLY", {"visual": 0, "text": ">0"}),
    ("sample.txt", "TEXT_ONLY", {"visual": 0, "text": ">0"}),
])
def test_format_processing(api_client, fixture, expected_format, expected_embeddings):
    """Test processing for different document formats."""
    file_path = FIXTURES_DIR / fixture

    # Upload and process
    with open(file_path, "rb") as f:
        response = api_client.post("/api/upload", files={"file": (fixture, f)})

    # Verify format detection and processing
    # ... test implementation
```

### Cleanup Test

```python
def test_fixture_cleanup(api_client, test_doc_ids):
    """Test document deletion with fixtures."""
    pdf_path = FIXTURES_DIR / "sample.pdf"

    # Upload
    with open(pdf_path, "rb") as f:
        response = api_client.post("/api/upload", files={"file": ("sample.pdf", f)})
    doc_id = response.json()["doc_id"]
    test_doc_ids.append(doc_id)  # Auto-cleanup

    # Verify upload
    status_response = api_client.get(f"/api/status/{doc_id}")
    assert status_response.status_code == 200

    # Delete
    delete_response = api_client.delete(f"/api/documents/{doc_id}")
    assert delete_response.status_code == 200

    # Verify deletion
    status_response = api_client.get(f"/api/status/{doc_id}")
    assert status_response.status_code == 404
```

---

## Regenerating Fixtures

If you need to regenerate the fixtures (e.g., after modifying requirements):

```bash
cd tests/fixtures
python generate_fixtures.py
```

This will recreate all fixture files with the latest specifications.

---

## File Size Limits

All fixtures are designed to be small (<100KB) for fast testing:

| File | Size | Status |
|------|------|--------|
| sample.pdf | ~2.5 KB | ✓ Well under limit |
| sample.docx | ~37 KB | ✓ Under limit |
| sample.txt | ~765 bytes | ✓ Well under limit |
| sample.mp3 | ~15.8 KB | ✓ Well under limit |
| sample.wav | ~32 KB | ✓ Under limit |

**Total:** ~88 KB for all fixtures

---

## Supported Format Reference

Based on `src/processing/docling_parser.py`:

### Visual Formats (Full Processing)
- `.pdf` - Portable Document Format
- `.pptx` - Microsoft PowerPoint (requires slide-renderer service)

### Image Formats (Single-Page Visual)
- `.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp`, `.webp`

### Office Formats (Text-Only)
- `.docx` - Microsoft Word ✓ (fixture provided)
- `.xlsx` - Microsoft Excel

### Text-Only Formats
- `.txt` - Plain text ✓ (fixture provided)
- `.md` - Markdown
- `.html`, `.htm`, `.xhtml` - HTML/XHTML
- `.asciidoc` - AsciiDoc
- `.csv` - CSV

### Audio Formats
- `.mp3` - MPEG Audio ✓ (fixture provided)
- `.wav` - Waveform Audio ✓ (fixture provided)
- `.vtt` - Web Video Text Tracks

### Specialized Formats
- `.xml` - XML (USPTO/JATS)
- `.json` - JSON (Docling native)

---

## Adding New Fixtures

To add a new fixture:

1. Create the file (manually or programmatically)
2. Ensure it's small (<100KB) but valid
3. Add entry to this README with:
   - File size
   - Content description
   - Expected behavior
   - Test keywords
4. Update `generate_fixtures.py` if it should be auto-generated

---

## Integration with E2E Tests

These fixtures complement the E2E test fixtures in `tests/e2e/fixtures/`:

- **API fixtures** (this directory): Basic valid files for API endpoint testing
- **E2E fixtures**: More complex documents with structure for end-to-end testing

Use API fixtures for:
- Unit tests of upload/processing endpoints
- Quick validation tests
- Format-specific behavior testing
- Cleanup and deletion testing

Use E2E fixtures for:
- Full pipeline testing
- Structure extraction validation
- Complex document scenarios
- Performance benchmarking

---

## Notes

- All fixtures are **minimal but valid** - they contain the minimum data required for each format
- Files are **deterministic** - regeneration produces identical files (except timestamps in DOCX)
- Audio files are **silent** - replace with real audio for transcription testing
- All fixtures are **safe to commit** - no sensitive data, small sizes
- Files are **tested** - each fixture has been validated with the actual processing pipeline

---

## Troubleshooting

### Fixture not found
```python
# Always use absolute path from fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
file_path = FIXTURES_DIR / "sample.pdf"
```

### Processing timeout
- Check if services are running (`./scripts/status.sh`)
- Increase timeout in `wait_for_document_processing()`
- Check Worker API logs

### Wrong number of embeddings
- Verify format type (VISUAL vs TEXT_ONLY)
- Check chunk size settings
- Review processing mode in logs

### Missing dependencies
```bash
pip install reportlab python-docx
```

---

## Related Documentation

- [E2E Test Fixtures](../e2e/fixtures/README.md) - E2E testing fixtures and helpers
- [Processing Interface](../../src/processing/PROCESSING_INTERFACE.md) - Processing pipeline contracts
- [Format Support](../../src/processing/docling_parser.py) - Full format support details
- [API Documentation](../../docs/api/) - API endpoint specifications

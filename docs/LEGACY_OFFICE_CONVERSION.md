# Legacy Office Format Conversion

**Last Updated:** 2025-11-19

DocuSearch now supports legacy Microsoft Office formats (`.doc`, `.dot`) through automatic conversion to modern formats (`.docx`). This feature enables seamless processing of older documents without requiring manual conversion.

## Table of Contents

- [Overview](#overview)
- [Supported Formats](#supported-formats)
- [How It Works](#how-it-works)
- [User Experience](#user-experience)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Performance](#performance)
- [Limitations](#limitations)
- [Troubleshooting](#troubleshooting)
- [Security](#security)

---

## Overview

The legacy Office conversion feature automatically detects and converts `.doc` files to `.docx` format during the document processing pipeline. This conversion happens transparently to the user, preserving the original filename in metadata while processing the modern format internally.

**Key Features:**
- ✅ Automatic detection of legacy formats
- ✅ Transparent conversion using LibreOffice
- ✅ Original filename preservation
- ✅ No user intervention required
- ✅ Seamless integration with existing pipeline

---

## Supported Formats

### Legacy Formats (Auto-Converted)

| Format | Extension | Support Level | Notes |
|--------|-----------|---------------|-------|
| Word 97-2003 | `.doc` | ✅ Full | Primary target format |
| Word 95 | `.doc` | ✅ Full | Older binary format |
| Word 6.0 | `.doc` | ✅ Full | Very old format |
| Word Template | `.dot` | ✅ Full | Template files |

### Output Format

| Format | Extension | Notes |
|--------|-----------|-------|
| Word 2007+ | `.docx` | OOXML format (internal processing) |

**Note:** While the conversion produces `.docx` files, the original filename (e.g., `report.doc`) is preserved in the document metadata and UI.

---

## How It Works

### Automatic Conversion Process

```
┌────────────────────────────────────────────────────────────┐
│ 1. Upload .doc File                                        │
│    User uploads "quarterly_report.doc" via Copyparty       │
└─────────────────┬──────────────────────────────────────────┘
                  │
                  ▼
┌────────────────────────────────────────────────────────────┐
│ 2. Detection                                               │
│    Worker detects .doc extension → triggers conversion    │
└─────────────────┬──────────────────────────────────────────┘
                  │
                  ▼
┌────────────────────────────────────────────────────────────┐
│ 3. Conversion (legacy-office-converter service)           │
│    LibreOffice: quarterly_report.doc → quarterly_report.docx │
│    Time: ~1-5 seconds (typical)                            │
└─────────────────┬──────────────────────────────────────────┘
                  │
                  ▼
┌────────────────────────────────────────────────────────────┐
│ 4. Processing                                              │
│    .docx file processed through standard pipeline:        │
│    - Parse with Docling                                    │
│    - Extract pages/chunks                                  │
│    - Generate embeddings                                   │
│    - Store in ChromaDB                                     │
└─────────────────┬──────────────────────────────────────────┘
                  │
                  ▼
┌────────────────────────────────────────────────────────────┐
│ 5. Metadata Storage                                        │
│    Original filename preserved:                            │
│    - Display name: "quarterly_report.doc"                  │
│    - Internal path: /uploads/quarterly_report.docx         │
└────────────────────────────────────────────────────────────┘
```

### Technical Flow

1. **File Upload**: User uploads `.doc` file to Copyparty (port 8000)
2. **Webhook Trigger**: Copyparty calls `/hooks/on_upload.py`
3. **Format Detection**: Worker detects `.doc` extension in `DocConverter.convert_if_needed()`
4. **API Call**: Worker calls `POST /convert-doc` on legacy-office-converter service
5. **LibreOffice Conversion**: Service runs `libreoffice --headless --convert-to docx`
6. **Path Return**: Service returns path to `.docx` file
7. **Standard Processing**: Worker processes `.docx` through normal pipeline
8. **Metadata Preservation**: Original `.doc` filename stored in metadata

---

## User Experience

### What Users See

**Upload:**
- User uploads `report.doc` via web UI or Copyparty
- No special steps required

**Processing:**
- Document appears in UI as "report.doc" (original name)
- Processing status shows standard progress
- Conversion happens transparently (typically adds 1-5 seconds)

**Search & View:**
- Document searchable immediately after processing
- Document name displays as "report.doc" in all views
- Content viewer shows document contents normally
- Research bot can cite from the document

**What Users DON'T See:**
- Internal `.docx` conversion
- Conversion API calls
- Temporary file paths

---

## Architecture

### Service: legacy-office-converter

**Container Name:** `docusearch-legacy-office-converter`
**Port:** 8003
**Image Base:** `python:3.14-slim`
**Key Components:**
- LibreOffice (headless mode)
- FastAPI HTTP server
- PDF/image rendering tools

### Docker Configuration

```yaml
# docker/docker-compose.yml
services:
  legacy-office-converter:
    build:
      context: .
      dockerfile: Dockerfile.legacy-office-converter
    container_name: docusearch-legacy-office-converter
    ports:
      - "8003:8003"
    volumes:
      - ../data/uploads:/uploads
      - ../data/page_images:/page_images
    environment:
      - ALLOWED_UPLOAD_DIRS=/uploads,/data/uploads
```

### LibreOffice Installation

The container includes:
```dockerfile
RUN apt-get install -y \
    libreoffice \              # Core LibreOffice
    libreoffice-writer \       # Word processing (for .doc)
    libreoffice-impress \      # Presentations
    libreoffice-calc \         # Spreadsheets
    fonts-liberation \         # Font support
    poppler-utils \            # PDF utilities
    imagemagick                # Image processing
```

### Python Client

**Module:** `src/processing/legacy_office_client.py`

```python
from src.processing.legacy_office_client import get_legacy_office_client

client = get_legacy_office_client()
docx_path = client.convert_doc_to_docx(
    doc_path="/uploads/report.doc",
    output_dir="/uploads"
)
# Returns: "/uploads/report.docx"
```

### Integration Points

1. **DocConverter** (`src/processing/parsers/doc_converter.py`)
   - Detects `.doc` files
   - Calls conversion client
   - Returns converted path

2. **DoclingParser** (`src/processing/docling_parser.py`)
   - Calls DocConverter before parsing
   - Processes converted `.docx` file
   - Preserves original filename

3. **Processor** (`src/processing/processor.py`)
   - Receives document with metadata
   - Stores original filename
   - Uses converted file for embedding

---

## Configuration

### Environment Variables

**New Variables (Recommended):**
```bash
# .env
LEGACY_OFFICE_HOST=localhost
LEGACY_OFFICE_PORT=8003
LEGACY_OFFICE_ENABLED=true
DOC_CONVERSION_TIMEOUT=30
```

**Legacy Variables (Still Supported):**
```bash
# Backward compatibility
SLIDE_RENDERER_HOST=localhost
SLIDE_RENDERER_PORT=8003
```

**Configuration Priority:**
1. `LEGACY_OFFICE_HOST` (if set)
2. Falls back to `SLIDE_RENDERER_HOST`
3. Defaults to `localhost`

### Timeout Settings

| Setting | Default | Range | Notes |
|---------|---------|-------|-------|
| `DOC_CONVERSION_TIMEOUT` | 30s | 10-120s | Per-file conversion timeout |
| HTTP request timeout | 60s | 30-300s | Client-side timeout |

**Recommendation:** Set timeout based on expected file sizes:
- Small files (< 1 MB): 30s
- Medium files (1-5 MB): 60s
- Large files (5-20 MB): 120s

### File Size Limits

**Recommended Maximum:** 50 MB

**Enforcement:**
```bash
# In .env
MAX_UPLOAD_SIZE_MB=50
```

Files larger than this may:
- Take excessive time to convert
- Consume too much memory
- Risk timeout failures

---

## Performance

### Conversion Times

Based on typical LibreOffice performance:

| File Size | Complexity | Typical Time | Notes |
|-----------|------------|--------------|-------|
| < 100 KB | Simple text | 1-2s | Most documents |
| 100 KB - 1 MB | Text + images | 2-5s | Common case |
| 1 MB - 5 MB | Complex formatting | 5-15s | Heavy formatting |
| 5 MB - 20 MB | Heavy images/objects | 15-60s | Large files |
| > 20 MB | Very large | 60s+ | Rare |

**Factors Affecting Speed:**
- Number of embedded images
- Complex formatting (tables, objects)
- Embedded OLE objects
- Container CPU allocation
- Concurrent conversions

### File Size Changes

**Typical Compression:**
- `.docx` files are **10-50% smaller** than `.doc` files
- Text-heavy documents compress more
- Image-heavy documents compress less

**Example:**
```
report.doc     → 850 KB
report.docx    → 420 KB (50% reduction)
```

### Resource Usage

**Per Conversion:**
- **CPU:** ~50-100% of 1 core (duration: 1-5s)
- **Memory:** ~100-200 MB
- **Disk I/O:** Minimal (read .doc, write .docx)

**Container Limits (Recommended):**
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 512M
    reservations:
      cpus: '0.5'
      memory: 256M
```

---

## Limitations

### 1. Password-Protected Files ❌

**Status:** Not Supported

**Behavior:**
- Conversion fails with error
- Error message: "LibreOffice conversion failed"
- File status shows as "failed" in UI

**Workaround:**
1. Decrypt file manually
2. Upload decrypted version
3. Or use `.docx` version if available

---

### 2. VBA Macros ⚠️

**Status:** Macros Removed

**Behavior:**
- Document content is preserved
- VBA macros are stripped during conversion
- No warning/error generated

**Impact:**
- For document search: ✅ No impact (text is preserved)
- For macro-dependent workflows: ❌ Macros lost

**Note:** This is acceptable for DocuSearch's use case (search and embedding).

---

### 3. Embedded Objects ⚠️

**Status:** Partial Support

**Behavior:**
- Embedded Excel spreadsheets → May lose live linking
- Embedded videos/audio → Converted to static links
- Custom drawing objects → May have layout changes
- ActiveX controls → Removed

**Impact:**
- Visual fidelity may be reduced
- Text content is fully preserved
- Search functionality unaffected

---

### 4. Custom Fonts ⚠️

**Status:** Font Substitution

**Behavior:**
- Fonts not in container → Substituted with Liberation fonts
- Layout may shift slightly
- Content fully preserved

**Mitigation:**
- Container includes `fonts-liberation` (common substitutes)

**Impact:**
- Text search: ✅ No impact
- Visual similarity search: ⚠️ Minor layout differences possible

---

### 5. Track Changes and Comments ✅

**Status:** Generally Preserved

**Behavior:**
- Track changes metadata maintained
- Comments preserved
- Revision history kept (if stored in document)

**Impact:** ✅ No significant issues

---

### 6. Digital Signatures ❌

**Status:** Removed

**Behavior:**
- Digital signatures stripped during conversion
- Document loses signed status
- No warning generated

**Impact:**
- For document search: ✅ No impact
- For document verification: ❌ Signature lost

---

### 7. Mail Merge Data Sources ❌

**Status:** Not Preserved

**Behavior:**
- External data source connections lost
- Document template preserved
- Placeholder fields remain

**Impact:**
- Template text searchable
- Data source link removed

---

## Troubleshooting

### Common Issues

#### Issue: "Conversion failed: Service unavailable"

**Cause:** `legacy-office-converter` service not running

**Solution:**
```bash
# Check service status
./scripts/status.sh

# Start all services
./scripts/start-all.sh

# Check logs
docker logs docusearch-legacy-office-converter
```

---

#### Issue: "Conversion timeout"

**Cause:** Large or complex file exceeds timeout

**Solution:**
```bash
# Increase timeout in .env
DOC_CONVERSION_TIMEOUT=120

# Restart services
./scripts/stop-all.sh
./scripts/start-all.sh
```

**Alternative:** Split large document into smaller sections

---

#### Issue: "File not found"

**Cause:** File path not accessible to container

**Solution:**
1. Verify file uploaded to correct directory:
   ```bash
   ls -la data/uploads/
   ```
2. Check volume mount in `docker-compose.yml`:
   ```yaml
   volumes:
     - ../data/uploads:/uploads
   ```
3. Restart container if volume changed

---

#### Issue: "Invalid file type"

**Cause:** File extension not `.doc` or `.dot`

**Solution:**
- Verify file is actually a `.doc` file:
  ```bash
  file data/uploads/document.doc
  ```
- If file is corrupted, try opening in Word and re-saving

---

#### Issue: "Password-protected file"

**Cause:** LibreOffice cannot convert encrypted files

**Solution:**
1. Open file in Microsoft Word
2. Remove password protection (File → Info → Protect Document)
3. Save and re-upload

**Alternative:** Use `.docx` version if available

---

#### Issue: "Conversion produces empty file"

**Cause:** Corrupted .doc file or LibreOffice error

**Solution:**
1. Verify file is valid:
   ```bash
   file data/uploads/document.doc
   ```
2. Try opening in LibreOffice manually:
   ```bash
   docker exec docusearch-legacy-office-converter \
     libreoffice --headless --convert-to docx /uploads/document.doc
   ```
3. Check logs for LibreOffice errors:
   ```bash
   docker logs docusearch-legacy-office-converter | grep -i error
   ```

---

### Debug Mode

**Enable verbose logging:**
```bash
# In docker-compose.yml
environment:
  - LOG_LEVEL=DEBUG

# Restart service
docker-compose restart legacy-office-converter

# Watch logs
docker logs -f docusearch-legacy-office-converter
```

**Look for:**
- LibreOffice command execution
- File paths being processed
- Exit codes
- Error messages

---

### Manual Conversion Test

**Test conversion manually:**
```bash
# Enter container
docker exec -it docusearch-legacy-office-converter bash

# Run conversion
libreoffice --headless --convert-to docx \
  --outdir /uploads \
  /uploads/test.doc

# Check output
ls -lh /uploads/test.docx
```

---

## Security

### Path Validation

**Allowed Directories:**
- `/uploads`
- `/data/uploads`

**Enforcement:**
```python
# All paths validated against allowed directories
# Path traversal attempts blocked (e.g., "../../../etc/passwd")
# Symlink resolution prevents escaping allowed paths
```

**Example Blocked Paths:**
```
/etc/passwd           → ❌ Blocked
../../../etc/passwd   → ❌ Blocked
/uploads/../etc       → ❌ Blocked (after resolution)
/tmp/malicious.doc    → ❌ Blocked
```

---

### Allowed File Extensions

**Permitted:**
- `.doc`
- `.dot`
- `.pptx` (for slide rendering)

**Blocked:**
- `.exe`, `.sh`, `.py`, etc.
- Arbitrary file types

**Validation:**
```python
ALLOWED_EXTENSIONS = {".pptx", ".ppt", ".doc"}
if requested_path.suffix.lower() not in ALLOWED_EXTENSIONS:
    raise HTTPException(status_code=400)
```

---

### Container Isolation

**Security Measures:**
- ✅ Runs in isolated Docker container
- ✅ No host network access
- ✅ Volume mounts limited to `/uploads` and `/page_images`
- ✅ No privileged mode
- ✅ Resource limits (CPU, memory)

**Recommended Limits:**
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 512M
```

---

### Denial of Service Protection

**File Size Limits:**
- Recommended max: 50 MB
- Enforced at upload level

**Conversion Timeout:**
- Default: 30 seconds
- Maximum: 120 seconds
- Prevents resource exhaustion

**Concurrent Conversion Limits:**
- Sequential processing (one at a time)
- Prevents memory exhaustion
- Queue depth monitoring

---

### XXE Attack Mitigation

**Protection:**
- LibreOffice 7.x+ has built-in XXE protection
- XML external entity attacks blocked
- No additional configuration needed

---

## Additional Resources

**Related Documentation:**
- [Quick Start Guide](QUICK_START.md) - Getting started with DocuSearch
- [Multi-Format Support](MULTI_FORMAT_SUPPORT.md) - All supported formats
- [API Reference](API_LEGACY_OFFICE.md) - API endpoint documentation
- [Troubleshooting Guide](TROUBLESHOOTING_DOC_CONVERSION.md) - Detailed troubleshooting
- [Migration Guide](LEGACY_OFFICE_MIGRATION.md) - Migration from slide-renderer

**Contracts & Specifications:**
- [Doc Conversion API Contract](../.context-kit/orchestration/legacy-office-doc-conversion/integration-contracts/doc-conversion-api.yaml)
- [LibreOffice Capabilities](../.context-kit/orchestration/legacy-office-doc-conversion/validation/libreoffice-capabilities.md)
- [Validation Report](../.context-kit/orchestration/legacy-office-doc-conversion/integration-contracts/VALIDATION-REPORT.md)

**External References:**
- [LibreOffice Documentation](https://documentation.libreoffice.org/)
- [LibreOffice CLI Parameters](https://help.libreoffice.org/latest/en-US/text/shared/guide/start_parameters.html)
- [OOXML Specification](https://www.ecma-international.org/publications-and-standards/standards/ecma-376/)

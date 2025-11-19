# Legacy Office Converter API

**Last Updated:** 2025-11-19
**Service:** legacy-office-converter
**Version:** 2.0.0
**Port:** 8003

## Overview

The Legacy Office Converter API provides HTTP endpoints for converting legacy Microsoft Office documents and rendering presentations to images using LibreOffice in headless mode.

**Base URL:** `http://localhost:8003`

**Capabilities:**
- Convert `.doc` files to `.docx` format
- Render PPTX slides to PNG images
- Health monitoring

---

## Table of Contents

- [Endpoints](#endpoints)
  - [POST /convert-doc](#post-convert-doc)
  - [POST /render](#post-render)
  - [GET /health](#get-health)
  - [GET /](#get-)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Integration](#integration)

---

## Endpoints

### POST /convert-doc

Convert a legacy `.doc` file to modern `.docx` format.

**URL:** `/convert-doc`
**Method:** `POST`
**Content-Type:** `application/json`

#### Request Body

```json
{
  "file_path": "/uploads/document.doc",
  "output_dir": "/uploads"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file_path` | string | Yes | Absolute path to .doc file (must be in `/uploads`) |
| `output_dir` | string | Yes | Directory for output .docx file |

**Constraints:**
- `file_path` must be within allowed directories (`/uploads`, `/data/uploads`)
- `file_path` must have `.doc` or `.dot` extension
- File must exist and be readable
- File must not be password-protected

#### Success Response (200)

```json
{
  "success": true,
  "docx_path": "/uploads/document.docx",
  "file_size_bytes": 189440,
  "conversion_time_ms": 2340
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Always `true` for successful conversion |
| `docx_path` | string | Absolute path to converted .docx file |
| `file_size_bytes` | integer | Size of converted file in bytes |
| `conversion_time_ms` | integer | Time taken for conversion in milliseconds |

#### Error Responses

**400 Bad Request** - Invalid file type or request

```json
{
  "success": false,
  "error": "Invalid file type: .txt. Only .doc and .dot supported",
  "docx_path": null,
  "file_size_bytes": null,
  "conversion_time_ms": null
}
```

**403 Forbidden** - Path outside allowed directories

```json
{
  "success": false,
  "error": "Access denied: Path outside allowed directories",
  "docx_path": null,
  "file_size_bytes": null,
  "conversion_time_ms": null
}
```

**404 Not Found** - File doesn't exist

```json
{
  "success": false,
  "error": "File not found: document.doc",
  "docx_path": null,
  "file_size_bytes": null,
  "conversion_time_ms": null
}
```

**500 Internal Server Error** - LibreOffice failure

```json
{
  "success": false,
  "error": "LibreOffice conversion failed: corrupted file structure",
  "docx_path": null,
  "file_size_bytes": null,
  "conversion_time_ms": 2150
}
```

#### Timeout

**Default:** 30 seconds
**Configurable via:** `DOC_CONVERSION_TIMEOUT` environment variable

If conversion exceeds timeout:
```json
{
  "success": false,
  "error": "Conversion timeout exceeded (30s)",
  "docx_path": null,
  "file_size_bytes": null,
  "conversion_time_ms": 30000
}
```

---

### POST /render

Render PowerPoint slides to PNG images.

**URL:** `/render`
**Method:** `POST`
**Content-Type:** `application/json`

#### Request Body

```json
{
  "file_path": "/uploads/presentation.pptx",
  "output_dir": "/page_images/temp-slides-abc123",
  "dpi": 150
}
```

**Parameters:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `file_path` | string | Yes | - | Path to PPTX file |
| `output_dir` | string | Yes | - | Directory for PNG images |
| `dpi` | integer | No | 150 | Resolution (DPI) for rendering |

#### Success Response (200)

```json
{
  "success": true,
  "slide_count": 12,
  "slide_paths": [
    "/page_images/temp-slides-abc123/page001.png",
    "/page_images/temp-slides-abc123/page002.png",
    "/page_images/temp-slides-abc123/page003.png"
  ],
  "error": null
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Conversion success status |
| `slide_count` | integer | Number of slides rendered |
| `slide_paths` | array[string] | Paths to rendered PNG files |
| `error` | string\|null | Error message if failed |

#### Error Responses

**404 Not Found** - PPTX file not found

```json
{
  "success": false,
  "slide_count": 0,
  "slide_paths": [],
  "error": "File not found: presentation.pptx"
}
```

**500 Internal Server Error** - Rendering failure

```json
{
  "success": false,
  "slide_count": 0,
  "slide_paths": [],
  "error": "Rendering failed: LibreOffice conversion error"
}
```

---

### GET /health

Health check endpoint.

**URL:** `/health`
**Method:** `GET`

#### Success Response (200)

```json
{
  "status": "healthy",
  "service": "legacy-office-converter",
  "capabilities": ["pptx-rendering", "doc-conversion"]
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Service health status |
| `service` | string | Service name |
| `capabilities` | array[string] | List of supported features |

---

### GET /

Service information endpoint.

**URL:** `/`
**Method:** `GET`

#### Success Response (200)

```json
{
  "service": "Legacy Office Converter API",
  "version": "2.0.0",
  "capabilities": ["pptx-rendering", "doc-conversion"],
  "endpoints": {
    "health": "GET /health",
    "render_pptx": "POST /render",
    "convert_doc": "POST /convert-doc"
  }
}
```

---

## Data Models

### ConversionRequest

```typescript
{
  file_path: string;     // Path to .doc file (must match ^/uploads/.*\.doc$)
  output_dir: string;    // Output directory (must match ^/uploads(/.*)?$)
}
```

### ConversionSuccessResponse

```typescript
{
  success: true;
  docx_path: string;           // Path to converted .docx
  file_size_bytes: number;     // Size in bytes (>= 0)
  conversion_time_ms: number;  // Time in milliseconds (>= 0)
}
```

### ConversionErrorResponse

```typescript
{
  success: false;
  error: string;                    // Human-readable error message
  docx_path: null;
  file_size_bytes: null;
  conversion_time_ms: number | null;  // Time before failure (if applicable)
}
```

### RenderRequest

```typescript
{
  file_path: string;   // Path to PPTX file
  output_dir: string;  // Output directory for PNGs
  dpi?: number;        // Optional, default: 150
}
```

### RenderResponse

```typescript
{
  success: boolean;
  slide_count: number;
  slide_paths: string[];
  error: string | null;
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 200 | Success | Conversion completed successfully |
| 400 | Bad Request | Invalid file extension, malformed request |
| 403 | Forbidden | Path outside allowed directories |
| 404 | Not Found | File doesn't exist |
| 500 | Internal Server Error | LibreOffice failure, conversion error, timeout |

### Error Response Format

All error responses follow this structure:

```json
{
  "success": false,
  "error": "Human-readable error message",
  "docx_path": null,
  "file_size_bytes": null,
  "conversion_time_ms": <number or null>
}
```

### Common Error Messages

| Error Message | Cause | Solution |
|--------------|-------|----------|
| `Invalid file type: .xxx` | Wrong file extension | Use `.doc` or `.dot` files only |
| `Access denied: Path outside allowed directories` | Path traversal attempt | Use paths within `/uploads` |
| `File not found: xxx.doc` | File doesn't exist | Verify file path and existence |
| `LibreOffice conversion failed: ...` | Corrupted file or LibreOffice error | Check file integrity |
| `Conversion timeout exceeded (30s)` | File too large or complex | Increase timeout or split file |
| `Password-protected file` | File is encrypted | Decrypt file before conversion |

---

## Examples

### Example 1: Basic .doc Conversion

**Request:**
```bash
curl -X POST http://localhost:8003/convert-doc \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/uploads/quarterly_report.doc",
    "output_dir": "/uploads"
  }'
```

**Response:**
```json
{
  "success": true,
  "docx_path": "/uploads/quarterly_report.docx",
  "file_size_bytes": 245760,
  "conversion_time_ms": 1850
}
```

---

### Example 2: Conversion Error (File Not Found)

**Request:**
```bash
curl -X POST http://localhost:8003/convert-doc \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/uploads/missing.doc",
    "output_dir": "/uploads"
  }'
```

**Response (404):**
```json
{
  "success": false,
  "error": "File not found: missing.doc",
  "docx_path": null,
  "file_size_bytes": null,
  "conversion_time_ms": null
}
```

---

### Example 3: Invalid File Type

**Request:**
```bash
curl -X POST http://localhost:8003/convert-doc \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/uploads/document.txt",
    "output_dir": "/uploads"
  }'
```

**Response (400):**
```json
{
  "success": false,
  "error": "Invalid file type: .txt",
  "docx_path": null,
  "file_size_bytes": null,
  "conversion_time_ms": null
}
```

---

### Example 4: Health Check

**Request:**
```bash
curl http://localhost:8003/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "legacy-office-converter",
  "capabilities": ["pptx-rendering", "doc-conversion"]
}
```

---

### Example 5: Service Info

**Request:**
```bash
curl http://localhost:8003/
```

**Response:**
```json
{
  "service": "Legacy Office Converter API",
  "version": "2.0.0",
  "capabilities": ["pptx-rendering", "doc-conversion"],
  "endpoints": {
    "health": "GET /health",
    "render_pptx": "POST /render",
    "convert_doc": "POST /convert-doc"
  }
}
```

---

### Example 6: Python Client Usage

```python
from src.processing.legacy_office_client import get_legacy_office_client

# Get singleton client
client = get_legacy_office_client()

# Check service health
is_healthy = client.check_health()
print(f"Service healthy: {is_healthy}")

# Convert .doc to .docx
try:
    docx_path = client.convert_doc_to_docx(
        doc_path="/uploads/report.doc",
        output_dir="/uploads"
    )
    print(f"Conversion successful: {docx_path}")

except FileNotFoundError as e:
    print(f"File not found: {e}")

except LegacyOfficeError as e:
    print(f"Conversion failed: {e}")
```

---

### Example 7: Integration with DocConverter

```python
from src.processing.parsers.doc_converter import DocConverter

converter = DocConverter()

# Automatically convert .doc if needed
path_to_use, was_converted = converter.convert_if_needed(
    "/uploads/quarterly_report.doc"
)

print(f"Processing: {path_to_use}")
print(f"Converted: {was_converted}")
# Output:
# Processing: /uploads/quarterly_report.docx
# Converted: True
```

---

## Integration

### Service Configuration

**Environment Variables:**

```bash
# Primary configuration
LEGACY_OFFICE_HOST=localhost
LEGACY_OFFICE_PORT=8003
LEGACY_OFFICE_ENABLED=true
DOC_CONVERSION_TIMEOUT=30

# Backward compatibility (deprecated)
SLIDE_RENDERER_HOST=localhost
SLIDE_RENDERER_PORT=8003
```

### Docker Compose

```yaml
services:
  legacy-office-converter:
    build:
      context: ./docker
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

### Client Initialization

**Python:**
```python
from src.processing.legacy_office_client import LegacyOfficeClient

# Manual initialization
client = LegacyOfficeClient(
    host="localhost",
    port=8003,
    timeout=60
)

# Or use singleton
from src.processing.legacy_office_client import get_legacy_office_client
client = get_legacy_office_client()
```

**JavaScript/TypeScript:**
```typescript
const LEGACY_OFFICE_BASE_URL = 'http://localhost:8003';

async function convertDocToDocx(docPath: string): Promise<string> {
  const response = await fetch(`${LEGACY_OFFICE_BASE_URL}/convert-doc`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      file_path: docPath,
      output_dir: '/uploads'
    })
  });

  const result = await response.json();

  if (!result.success) {
    throw new Error(result.error);
  }

  return result.docx_path;
}
```

---

## Performance

### Typical Conversion Times

| File Size | Complexity | Time Range |
|-----------|------------|------------|
| < 100 KB | Simple text | 1-2s |
| 100 KB - 1 MB | Text + images | 2-5s |
| 1 MB - 5 MB | Complex formatting | 5-15s |
| 5 MB - 20 MB | Heavy images | 15-60s |

### Optimization Tips

1. **Batch Processing:** Process files sequentially to avoid resource exhaustion
2. **Timeout Configuration:** Set timeout based on expected file sizes
3. **Resource Limits:** Configure Docker resource limits appropriately
4. **Health Checks:** Monitor service health before sending requests
5. **Retry Logic:** Implement exponential backoff for transient errors

---

## Security

### Path Validation

**Allowed directories:**
- `/uploads`
- `/data/uploads`

**Blocked attempts:**
- Path traversal: `../../../etc/passwd`
- Absolute paths outside allowed dirs: `/tmp/file.doc`
- Symlink escapes

**Enforcement:**
All paths are validated and resolved before processing.

### File Type Validation

**Allowed extensions:**
- `.doc` (Word 97-2003)
- `.dot` (Word Template)
- `.pptx` (PowerPoint)

**Validation:**
Extension checked before processing. Invalid types return 400 error.

### Resource Limits

**Recommended Docker limits:**
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 512M
```

**Timeout protection:**
- Default: 30s per conversion
- Prevents resource exhaustion from large files

---

## Troubleshooting

### Service Not Responding

**Check service status:**
```bash
curl http://localhost:8003/health
```

**View logs:**
```bash
docker logs docusearch-legacy-office-converter
```

**Restart service:**
```bash
docker restart docusearch-legacy-office-converter
```

### Conversion Failures

**Check LibreOffice availability:**
```bash
docker exec docusearch-legacy-office-converter \
  libreoffice --version
```

**Test manual conversion:**
```bash
docker exec docusearch-legacy-office-converter \
  libreoffice --headless --convert-to docx \
  --outdir /uploads /uploads/test.doc
```

### Port Conflicts

**Check port usage:**
```bash
lsof -i :8003
```

**Change port:**
Edit `docker-compose.yml`:
```yaml
ports:
  - "8004:8003"  # Map to different host port
```

---

## Additional Resources

**Related Documentation:**
- [Legacy Office Conversion Guide](LEGACY_OFFICE_CONVERSION.md) - Complete feature guide
- [Multi-Format Support](MULTI_FORMAT_SUPPORT.md) - All supported formats
- [Troubleshooting Guide](TROUBLESHOOTING_DOC_CONVERSION.md) - Detailed troubleshooting
- [Quick Start](QUICK_START.md) - Getting started

**Specifications:**
- [OpenAPI Contract](../.context-kit/orchestration/legacy-office-doc-conversion/integration-contracts/doc-conversion-api.yaml)
- [Client Interface](../.context-kit/orchestration/legacy-office-doc-conversion/integration-contracts/client-interface.json)
- [LibreOffice Capabilities](../.context-kit/orchestration/legacy-office-doc-conversion/validation/libreoffice-capabilities.md)

**External:**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LibreOffice CLI](https://help.libreoffice.org/latest/en-US/text/shared/guide/start_parameters.html)

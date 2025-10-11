# Image Storage Architecture

**Feature:** Page Image Persistence and Thumbnail Generation
**Status:** Wave 1 - Foundation
**Last Updated:** 2025-10-11

---

## Overview

This document describes the image storage architecture for persisting page images during document processing. The system generates and stores full-resolution page images and thumbnails for all processed documents, enabling visual document browsing in the monitoring UI.

---

## Directory Structure

```
data/
  page_images/              # Base directory for all page images
    {doc_id}/               # Subdirectory per document (SHA-256 hash)
      page001.png           # Full-resolution page 1 (PNG format)
      page001_thumb.jpg     # Thumbnail for page 1 (JPEG format)
      page002.png           # Full-resolution page 2
      page002_thumb.jpg     # Thumbnail for page 2
      ...
```

### Storage Locations

| Environment | Base Path | Mount Point |
|-------------|-----------|-------------|
| **Docker** | `data/page_images/` (host) | `/page_images` (container) |
| **Native** | `data/page_images/` | N/A |

---

## Image Formats

### Full-Resolution Images

- **Format:** PNG
- **Purpose:** Archival, high-quality viewing
- **Naming:** `page{num:03d}.png` (e.g., `page001.png`, `page010.png`)
- **Resolution:** Controlled by Docling's `images_scale` parameter (default: 2.0 = 144 DPI)
- **Size:** Typically 100-500 KB per page (depends on content)

### Thumbnails

- **Format:** JPEG
- **Purpose:** Fast loading in UI, list views
- **Naming:** `page{num:03d}_thumb.jpg` (e.g., `page001_thumb.jpg`)
- **Dimensions:** 300x400 pixels (portrait) or 400x300 pixels (landscape)
- **Quality:** 85% JPEG quality
- **Size:** Typically 20-50 KB per thumbnail

---

## Configuration

All configuration is centralized in `src/config/image_config.py`:

```python
# Base directory
PAGE_IMAGE_DIR = Path("/page_images")  # Docker
# or: Path("data/page_images")         # Native

# Thumbnail settings
THUMBNAIL_SIZE = (300, 400)  # (width, height) pixels
THUMBNAIL_QUALITY = 85       # JPEG quality (1-100)

# Formats
IMAGE_FORMAT = "PNG"
THUMBNAIL_FORMAT = "JPEG"

# Validation
MAX_IMAGE_SIZE_MB = 50
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PAGE_IMAGE_DIR` | `/page_images` | Base directory for image storage |

---

## Processing Pipeline Integration

### 1. Document Upload

User uploads document via Copyparty (port 8000) → Stored in `data/uploads/`

### 2. Docling Parsing

`docling_parser.py` extracts pages with images:
```python
result = document_converter.convert(file_path)

for page in result.pages:
    # Get PIL Image from Docling
    image = page.get_image()  # PIL.Image object
```

### 3. Image Persistence

`image_utils.save_page_image()` saves both versions:
```python
from src.processing.image_utils import save_page_image

image_path, thumb_path = save_page_image(
    image=image,
    doc_id="a3b2c1d4...",
    page_num=1
)
# Returns:
#   image_path = "/page_images/a3b2c1d4.../page001.png"
#   thumb_path = "/page_images/a3b2c1d4.../page001_thumb.jpg"
```

### 4. Metadata Storage

Paths stored in ChromaDB alongside embeddings:
```python
metadata = {
    "doc_id": "a3b2c1d4...",
    "page": 1,
    "filename": "report.pdf",
    "image_path": "/page_images/a3b2c1d4.../page001.png",
    "thumb_path": "/page_images/a3b2c1d4.../page001_thumb.jpg",
    # ... other metadata
}
```

---

## API Access

### Serving Images

Images are served via HTTP by the processing worker (port 8002):

```http
GET /images/{doc_id}/{filename} HTTP/1.1
Host: localhost:8002

Example:
GET /images/a3b2c1d4e5f6/page001_thumb.jpg
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: image/jpeg
Cache-Control: max-age=86400
Content-Length: 34567

<binary image data>
```

### Security

- **Path validation:** Doc ID format validated (alphanumeric + dashes, 8-64 chars)
- **Filename validation:** Only `page\d{3}(_thumb)?\.(png|jpg)` allowed
- **Path traversal prevention:** Attempts to access `../` blocked (403 Forbidden)

---

## Performance Considerations

### Storage Space

**Typical document (10 pages):**
- Full images: 10 × 300 KB = 3 MB
- Thumbnails: 10 × 30 KB = 300 KB
- **Total:** ~3.3 MB per document

**For 100 documents (1000 pages):**
- Full images: 1000 × 300 KB = 300 MB
- Thumbnails: 1000 × 30 KB = 30 MB
- **Total:** ~330 MB

### Processing Impact

**Image saving overhead:**
- Full PNG save: ~100-200ms per page
- Thumbnail generation: ~30-50ms per page
- **Total:** ~150-250ms per page

**Target:** <10% increase in total processing time
- Baseline: ~5-10 seconds per page (embedding generation)
- With images: ~5.2-10.3 seconds per page
- **Overhead:** ~200ms (2-4%)

### Caching

Images are served with caching headers:
```http
Cache-Control: max-age=86400  # 24 hours
```

Browsers cache images → Subsequent loads are instant.

---

## Error Handling

### Disk Full

```python
try:
    save_page_image(image, doc_id, page_num)
except DiskFullError:
    logger.error("Disk full - cannot save images")
    # Processing continues without images
```

### Permission Errors

Configuration validation on startup:
```python
# In image_config.py
validate_config()  # Raises ConfigurationError if no write permission
```

### Missing Images

If image saving fails:
- Processing continues (images optional)
- Metadata has `image_path: null`
- UI shows placeholder icon

---

## Cleanup and Maintenance

### Deleting Documents

```python
from src.processing.image_utils import delete_document_images

# Delete all images for a document
count = delete_document_images(doc_id="a3b2c1d4...")
# Returns: number of files deleted (e.g., 20 for 10 pages)
```

### Orphaned Images

Images without corresponding ChromaDB entries can be cleaned up:

```bash
# Find all doc_ids in page_images/
ls data/page_images/

# Query ChromaDB for existing doc_ids
# Compare and delete orphans
```

(Future enhancement: Automated cleanup script)

---

## Backward Compatibility

### Existing Documents

Documents processed before this feature:
- Have no `image_path` or `thumb_path` in metadata
- API returns `null` for these fields
- UI shows placeholder icons

### Migration

No migration required - old documents continue to work.

New documents automatically get images upon re-processing.

---

## Troubleshooting

### Images not being saved

**Check:**
1. Directory exists: `ls data/page_images/`
2. Permissions: `touch data/page_images/.test && rm data/page_images/.test`
3. Docker mount: `docker exec docusearch-worker ls /page_images`
4. Logs: `tail -f logs/worker-native.log | grep image`

### Images not displaying in UI

**Check:**
1. API endpoint: `curl http://localhost:8002/images/{doc_id}/page001_thumb.jpg`
2. CORS headers: Check browser console for errors
3. File exists: `ls data/page_images/{doc_id}/page001_thumb.jpg`
4. Permissions: File readable by worker process

### Disk space issues

**Monitor usage:**
```bash
du -sh data/page_images/
df -h data/
```

**Set up alerts:**
```bash
# Warn if >80% full
if [ $(df data/ | tail -1 | awk '{print $5}' | sed 's/%//') -gt 80 ]; then
    echo "Warning: Disk >80% full"
fi
```

---

## Future Enhancements

### Compression

- Use WebP format for thumbnails (better compression)
- Implement progressive JPEG for faster initial load

### Lazy Loading

- Generate thumbnails on-demand (first request)
- Cache in memory for hot images

### CDN Integration

- Serve images from CDN for production
- Upload to S3/CloudFront automatically

### Image Processing

- Add OCR layer visualization
- Highlight search terms in images
- Support image rotation/zoom

---

## References

- Orchestration Plan: `.context-kit/orchestration/page-images-document-view/`
- Integration Contract: `integration-contracts/01-image-config.contract.md`
- Code: `src/processing/image_utils.py`
- Tests: `tests/test_image_utils.py`

---

**Document Version:** 1.0
**Author:** infra-agent (Wave 1)

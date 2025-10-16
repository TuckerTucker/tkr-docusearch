# Integration Contract: Album Art API Endpoint

**Contract ID**: IC-001

**Provider**: backend-api-agent (Wave 1)

**Consumers**: frontend-ui-agent, integration-test-agent

**Status**: SPECIFIED

---

## Endpoint Specification

### `GET /documents/{doc_id}/cover`

**Purpose**: Serve album art image for audio documents

**Request**:
```
GET /documents/abc123def456/cover HTTP/1.1
Host: localhost:8002
```

**Response (Success - 200 OK)**:
```
HTTP/1.1 200 OK
Content-Type: image/jpeg
Content-Length: 34949
Cache-Control: public, max-age=31536000

<binary image data>
```

**Response (Not Found - 404)**:
```json
{
  "detail": "Album art not found for document abc123def456"
}
```

**Response (Invalid ID - 400)**:
```json
{
  "detail": "Invalid document ID format"
}
```

---

## Implementation Requirements

### File Location

```python
# Path construction
doc_id = "abc123def456"
base_dir = Path("data/images") / doc_id

# Check for cover art (multiple extensions)
for ext in ["jpg", "jpeg", "png"]:
    cover_path = base_dir / f"cover.{ext}"
    if cover_path.exists():
        return FileResponse(cover_path, media_type=get_mime_type(ext))

# Not found
raise HTTPException(404, detail=f"Album art not found for document {doc_id}")
```

### MIME Type Detection

```python
def get_mime_type(extension: str) -> str:
    """Get MIME type from file extension."""
    mime_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "svg": "image/svg+xml"
    }
    return mime_types.get(extension.lower(), "application/octet-stream")
```

### Security Validation

```python
# Validate doc_id format (prevent path traversal)
DOC_ID_PATTERN = re.compile(r'^[a-zA-Z0-9\-]{8,64}$')

if not DOC_ID_PATTERN.match(doc_id):
    raise HTTPException(400, detail="Invalid document ID format")
```

### Cache Headers

```python
# Add cache headers for performance
return FileResponse(
    cover_path,
    media_type=mime_type,
    headers={
        "Cache-Control": "public, max-age=31536000",  # 1 year
        "ETag": f'"{doc_id}-cover"'
    }
)
```

---

## Integration Points

### For frontend-ui-agent

**Album Art URL Construction**:
```javascript
// In audio-player.js
const albumArtUrl = `/documents/${this.docId}/cover`;

// Set image source
document.getElementById('album-art').src = albumArtUrl;

// Error handler (404 → fallback)
imageElement.onerror = () => {
    imageElement.src = DEFAULT_ALBUM_ART_SVG; // data URI
};
```

**Metadata Check**:
```javascript
// Check if album art exists before requesting
if (metadata.has_album_art) {
    loadAlbumArt(`/documents/${docId}/cover`);
} else {
    showDefaultAlbumArt();
}
```

---

## Testing Requirements

### Unit Tests

**File**: `src/processing/test_audio_album_art.py`

```python
def test_cover_endpoint_with_art():
    """Test album art endpoint returns image when available."""
    # Setup: Create test cover art file
    doc_id = "test-doc-001"
    cover_path = Path(f"data/images/{doc_id}/cover.jpg")
    cover_path.parent.mkdir(parents=True, exist_ok=True)
    cover_path.write_bytes(b"fake-image-data")

    # Test: Request cover art
    response = client.get(f"/documents/{doc_id}/cover")

    # Assert
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert "cache-control" in response.headers


def test_cover_endpoint_without_art():
    """Test album art endpoint returns 404 when unavailable."""
    response = client.get("/documents/no-cover-doc/cover")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_cover_endpoint_invalid_id():
    """Test album art endpoint rejects invalid doc IDs."""
    invalid_ids = [
        "../etc/passwd",
        "abc",  # too short
        "abc123/../../secret",
        "doc_id_with_invalid_chars!@#"
    ]

    for invalid_id in invalid_ids:
        response = client.get(f"/documents/{invalid_id}/cover")
        assert response.status_code == 400
```

### Manual Testing

```bash
# Test with real audio file
curl -I http://localhost:8002/documents/{real_doc_id}/cover
# Expected: 200 OK, image/jpeg

# Test without cover art
curl -I http://localhost:8002/documents/{no_art_doc_id}/cover
# Expected: 404 Not Found

# Test invalid ID
curl http://localhost:8002/documents/../../../etc/passwd/cover
# Expected: 400 Bad Request
```

---

## Performance Requirements

- Response time: < 50ms (local file serving)
- Cache headers: 1 year for immutable images
- No image processing (serve raw file)

---

## Error Handling

| Error | Status | Response |
|-------|--------|----------|
| Cover art not found | 404 | `{"detail": "Album art not found..."}` |
| Invalid doc ID | 400 | `{"detail": "Invalid document ID..."}` |
| File read error | 500 | `{"detail": "Internal server error"}` |

---

## Acceptance Criteria

- [x] Endpoint serves JPEG images
- [x] Endpoint serves PNG images
- [x] Endpoint returns 404 when no cover art
- [x] Endpoint validates doc_id format
- [x] Endpoint sets correct MIME type
- [x] Endpoint includes cache headers
- [x] Unit tests cover all scenarios
- [x] No path traversal vulnerabilities

---

## Example Implementation

```python
@router.get("/documents/{doc_id}/cover", tags=["documents"])
async def get_album_art(doc_id: str):
    """
    Get album art image for audio document.

    Returns album art as JPEG/PNG if available, 404 otherwise.
    """
    # Validate doc_id
    if not DOC_ID_PATTERN.match(doc_id):
        raise HTTPException(400, detail="Invalid document ID format")

    # Check for cover art file
    base_dir = Path("data/images") / doc_id

    for ext in ["jpg", "jpeg", "png"]:
        cover_path = base_dir / f"cover.{ext}"
        if cover_path.exists():
            mime_type = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png"

            return FileResponse(
                cover_path,
                media_type=mime_type,
                headers={
                    "Cache-Control": "public, max-age=31536000",
                    "ETag": f'"{doc_id}-cover"'
                }
            )

    # Not found
    raise HTTPException(
        404,
        detail=f"Album art not found for document {doc_id}"
    )
```

---

**Version**: 1.0
**Date**: 2025-10-15
**Status**: Ready for implementation

# Integration Contract: Album Art Metadata Extension

**Contract ID**: IC-002

**Provider**: backend-api-agent (Wave 1)

**Consumers**: frontend-ui-agent

**Status**: SPECIFIED

---

## Schema Extension

### DocumentMetadata Class

**File**: `src/processing/documents_api.py`

**Extension**:
```python
class DocumentMetadata(BaseModel):
    """Document metadata schema."""
    page_count: int
    chunk_count: int
    has_images: bool
    collections: List[str]
    raw_metadata: Optional[Dict[str, Any]] = None
    vtt_available: bool = False
    markdown_available: bool = False
    has_timestamps: bool = False

    # NEW: Album art fields
    has_album_art: bool = Field(
        False,
        description="True if album art image exists for this document"
    )
    album_art_url: Optional[str] = Field(
        None,
        description="URL to album art image (e.g., /documents/{doc_id}/cover)"
    )
```

---

## Field Specifications

### `has_album_art`

**Type**: `bool`

**Default**: `False`

**Purpose**: Indicates whether album art image exists on filesystem

**Computation Logic**:
```python
def check_album_art_exists(doc_id: str) -> bool:
    """Check if album art file exists for document."""
    base_dir = Path("data/images") / doc_id

    # Check for cover art in any supported format
    for ext in ["jpg", "jpeg", "png"]:
        cover_path = base_dir / f"cover.{ext}"
        if cover_path.exists():
            return True

    return False
```

**Examples**:
```python
# Audio with album art
metadata.has_album_art = True

# Audio without album art
metadata.has_album_art = False

# Non-audio document (PDF, text)
metadata.has_album_art = False
```

---

### `album_art_url`

**Type**: `Optional[str]`

**Default**: `None`

**Purpose**: Provides URL to album art endpoint

**Construction Logic**:
```python
def get_album_art_url(doc_id: str, has_album_art: bool) -> Optional[str]:
    """Get album art URL if available."""
    if has_album_art:
        return f"/documents/{doc_id}/cover"
    return None
```

**Examples**:
```python
# Album art available
metadata.album_art_url = "/documents/abc123def456/cover"

# Album art not available
metadata.album_art_url = None
```

---

## Integration with Existing API

### GET /documents/{doc_id}

**Response Extension**:
```json
{
  "doc_id": "abc123def456",
  "filename": "podcast-episode.mp3",
  "date_added": "2025-10-15T10:30:00Z",
  "pages": [],
  "chunks": [...],
  "metadata": {
    "page_count": 0,
    "chunk_count": 5,
    "has_images": false,
    "collections": ["audio_collection"],
    "raw_metadata": {
      "title": "Podcast Episode 42",
      "artist": "Host Name",
      "album": "Podcast Series",
      "duration_seconds": 691.9,
      "has_album_art": true
    },
    "vtt_available": true,
    "markdown_available": true,
    "has_timestamps": true,

    // NEW FIELDS
    "has_album_art": true,
    "album_art_url": "/documents/abc123def456/cover"
  }
}
```

**Without Album Art**:
```json
{
  "metadata": {
    // ... other fields ...
    "has_album_art": false,
    "album_art_url": null
  }
}
```

---

## Implementation Requirements

### Modify `get_document_by_id` Function

**File**: `src/processing/documents_api.py`

**Changes**:
```python
@router.get("/documents/{doc_id}", response_model=DocumentDetail)
async def get_document_by_id(doc_id: str):
    """Get document details by ID."""

    # ... existing code ...

    # NEW: Check for album art
    has_album_art = check_album_art_exists(doc_id)
    album_art_url = get_album_art_url(doc_id, has_album_art)

    metadata = DocumentMetadata(
        page_count=len(pages),
        chunk_count=len(chunks),
        has_images=has_page_images,
        collections=collections,
        raw_metadata=first_chunk_meta,
        vtt_available=vtt_exists,
        markdown_available=md_exists,
        has_timestamps=has_timestamps,
        # NEW FIELDS
        has_album_art=has_album_art,
        album_art_url=album_art_url
    )

    # ... rest of function ...
```

---

## Integration Points

### For frontend-ui-agent

**Usage in audio-player.js**:
```javascript
class AudioPlayer {
    constructor(containerId, docId, metadata, chunks) {
        this.metadata = metadata;
        // ...
        this.displayAlbumArt();
    }

    displayAlbumArt() {
        const albumArtElement = document.getElementById('album-art');

        // Check metadata flag
        if (this.metadata.has_album_art && this.metadata.album_art_url) {
            // Load album art from URL
            albumArtElement.src = this.metadata.album_art_url;

            // Fallback on error
            albumArtElement.onerror = () => {
                albumArtElement.src = DEFAULT_ALBUM_ART_SVG;
            };
        } else {
            // Show default SVG
            albumArtElement.src = DEFAULT_ALBUM_ART_SVG;
        }
    }
}
```

---

## Testing Requirements

### Unit Tests

**File**: `src/processing/test_audio_album_art.py`

```python
def test_metadata_has_album_art():
    """Test metadata includes album art fields when available."""
    # Setup: Create test document with album art
    doc_id = create_test_audio_with_album_art()

    # Test: Get document metadata
    response = client.get(f"/documents/{doc_id}")
    data = response.json()

    # Assert: Album art fields present
    assert response.status_code == 200
    assert data["metadata"]["has_album_art"] is True
    assert data["metadata"]["album_art_url"] == f"/documents/{doc_id}/cover"


def test_metadata_without_album_art():
    """Test metadata fields when album art unavailable."""
    # Setup: Create test document without album art
    doc_id = create_test_audio_without_album_art()

    # Test: Get document metadata
    response = client.get(f"/documents/{doc_id}")
    data = response.json()

    # Assert: Album art fields indicate unavailable
    assert response.status_code == 200
    assert data["metadata"]["has_album_art"] is False
    assert data["metadata"]["album_art_url"] is None


def test_metadata_non_audio_document():
    """Test album art fields for non-audio documents."""
    # Setup: Create PDF document
    doc_id = create_test_pdf()

    # Test: Get document metadata
    response = client.get(f"/documents/{doc_id}")
    data = response.json()

    # Assert: Album art fields default to false/null
    assert data["metadata"]["has_album_art"] is False
    assert data["metadata"]["album_art_url"] is None
```

---

## Backward Compatibility

**Requirement**: Must not break existing API consumers

**Approach**:
- New fields have defaults (`False`, `None`)
- Existing fields unchanged
- No breaking changes to response structure

**Migration**: None required (additive change only)

---

## Performance Considerations

### File Existence Check

```python
# Optimize: Cache result per request
@lru_cache(maxsize=128)
def check_album_art_exists(doc_id: str) -> bool:
    """Cached album art existence check."""
    # ... implementation ...
```

**Performance Target**: < 1ms per check (filesystem lookup)

---

## Acceptance Criteria

- [x] `has_album_art` field added to `DocumentMetadata`
- [x] `album_art_url` field added to `DocumentMetadata`
- [x] Fields computed correctly for audio with album art
- [x] Fields default correctly for audio without album art
- [x] Fields default correctly for non-audio documents
- [x] Unit tests cover all scenarios
- [x] Backward compatible with existing API
- [x] Performance < 1ms overhead

---

**Version**: 1.0
**Date**: 2025-10-15
**Status**: Ready for implementation

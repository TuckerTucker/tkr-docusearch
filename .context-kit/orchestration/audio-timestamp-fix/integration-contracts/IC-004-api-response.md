# IC-004: API Response Contract

**Version**: 1.0
**Status**: ✅ Approved
**Author**: Backend Specification Agent
**Reviewers**: Frontend Specification Agent, Frontend Implementation Agent
**Date**: 2025-10-16

---

## Overview

Defines the structure of API responses for documents with timestamps. Specifies how chunks with populated timestamp fields are returned to the frontend and ensures backward compatibility for documents without timestamps.

---

## API Endpoints Affected

### 1. GET /documents/{doc_id}
**Purpose**: Retrieve full document with metadata and chunks
**Changes**: Chunks now include `start_time` and `end_time` fields

### 2. GET /documents/{doc_id}/vtt
**Purpose**: Retrieve VTT file for audio playback
**Changes**: None (already exists and works)

### 3. GET /documents/{doc_id}/markdown
**Purpose**: Retrieve full markdown content
**Changes**: None (still includes timestamp markers for backward compat)

---

## Response Schema: GET /documents/{doc_id}

### Current Response (Before Fix)
```json
{
  "doc_id": "5e57bdeb-f37b-43e3-80ca-63bacaebeaab",
  "filename": "Myth 1.mp3",
  "metadata": {
    "raw_metadata": {
      "format_type": "audio"
    },
    "has_timestamps": false,
    "vtt_available": false,
    "markdown_available": true
  },
  "chunks": [
    {
      "chunk_id": "chunk_5e57bdeb-f37b-43e3-80ca-63bacaebeaab-chunk0000",
      "text_content": "[time: 0.62-3.96]  Myth 1. Ideas come in a flash.",
      "start_time": null,
      "end_time": null,
      "has_timestamps": false
    }
  ],
  "pages": []
}
```

### Updated Response (After Fix)
```json
{
  "doc_id": "5e57bdeb-f37b-43e3-80ca-63bacaebeaab",
  "filename": "Myth 1.mp3",
  "metadata": {
    "raw_metadata": {
      "format_type": "audio"
    },
    "has_timestamps": true,
    "vtt_available": true,
    "markdown_available": true
  },
  "chunks": [
    {
      "chunk_id": "chunk_5e57bdeb-f37b-43e3-80ca-63bacaebeaab-chunk0000",
      "text_content": "Myth 1. Ideas come in a flash.",
      "start_time": 0.62,
      "end_time": 3.96,
      "has_timestamps": true
    },
    {
      "chunk_id": "chunk_5e57bdeb-f37b-43e3-80ca-63bacaebeaab-chunk0001",
      "text_content": "Ideas may feel like they come in a flash, but it's actually after your brain has done a lot of work.",
      "start_time": 5.92,
      "end_time": 12.04,
      "has_timestamps": true
    }
  ],
  "pages": []
}
```

---

## Key Changes

### Change 1: Cleaned Text Content
```json
// Before
"text_content": "[time: 0.62-3.96]  Myth 1. Ideas come in a flash."

// After
"text_content": "Myth 1. Ideas come in a flash."
```
**Impact**: Text no longer contains `[time: X-Y]` markers

### Change 2: Populated Timestamp Fields
```json
// Before
"start_time": null,
"end_time": null

// After
"start_time": 0.62,
"end_time": 3.96
```
**Impact**: Frontend can use these fields directly instead of parsing markdown

### Change 3: Accurate Metadata Flags
```json
// Before
"has_timestamps": false,
"vtt_available": false

// After
"has_timestamps": true,
"vtt_available": true
```
**Impact**: Frontend knows VTT is available for native track element

---

## Chunk Response Schema

### TypeScript Interface (Frontend Reference)
```typescript
interface Chunk {
  chunk_id: string;
  text_content: string;        // Cleaned text (no [time: X-Y])
  start_time: number | null;   // Float seconds or null
  end_time: number | null;     // Float seconds or null
  has_timestamps: boolean;     // Convenience flag
  embedding_id?: string;       // Optional
  // ... other fields
}
```

### Python Model (Backend Reference)
```python
from typing import Optional
from pydantic import BaseModel

class ChunkResponse(BaseModel):
    chunk_id: str
    text_content: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    has_timestamps: bool = False
    embedding_id: Optional[str] = None
```

---

## Metadata Response Schema

### TypeScript Interface (Frontend Reference)
```typescript
interface DocumentMetadata {
  raw_metadata: {
    format_type?: string;  // "audio", "pdf", etc.
    // ... other raw metadata
  };
  has_timestamps: boolean;       // True if any chunk has timestamps
  vtt_available: boolean;        // True if VTT file exists
  markdown_available: boolean;   // True if markdown exists
  // ... other metadata fields
}
```

### Metadata Flags Meaning

| Flag | Meaning | Frontend Usage |
|------|---------|----------------|
| `has_timestamps` | At least one chunk has timestamps | Show timestamp UI, enable seeking |
| `vtt_available` | VTT file successfully generated | Load VTT track for captions |
| `format_type: "audio"` | Document is audio file | Show audio player |

---

## Backward Compatibility

### Documents Without Timestamps

**Example**: Audio file processed before this fix, or audio without transcript

```json
{
  "doc_id": "...",
  "filename": "old-audio.mp3",
  "metadata": {
    "has_timestamps": false,
    "vtt_available": false
  },
  "chunks": [
    {
      "chunk_id": "...",
      "text_content": "Some text without timestamps",
      "start_time": null,
      "end_time": null,
      "has_timestamps": false
    }
  ]
}
```

**Frontend Behavior**:
- Audio player loads and plays normally
- No VTT track loaded (graceful degradation)
- No captions displayed
- Accordion shows text without timestamps

**Key**: Frontend must handle `null` timestamps gracefully.

---

## API Implementation Notes

### No Changes Required to API Code

The API endpoint `GET /documents/{doc_id}` in `documents_api.py` **already returns chunk fields correctly**. The API simply serializes whatever is in ChromaDB.

**Current API Code** (Lines ~450-550):
```python
@router.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get document with all chunks and metadata"""

    # Fetch from ChromaDB
    text_results = chroma_client._text_collection.get(
        where={"doc_id": doc_id},
        limit=1000
    )

    # Serialize chunks
    chunks = []
    for i, chunk_id in enumerate(text_results["ids"]):
        metadata = text_results["metadatas"][i]

        chunk = {
            "chunk_id": chunk_id,
            "text_content": metadata.get("text", ""),
            "start_time": metadata.get("start_time"),  # Already returns this
            "end_time": metadata.get("end_time"),      # Already returns this
            "has_timestamps": metadata.get("has_timestamps", False),
            # ... other fields
        }
        chunks.append(chunk)

    return {
        "doc_id": doc_id,
        "filename": metadata.get("filename"),
        "metadata": {...},
        "chunks": chunks,
        "pages": pages
    }
```

**Why No Changes Needed**:
- API already returns `start_time` and `end_time` from metadata
- Currently these are `null` because chunks don't have them
- After backend fix, chunks will have them, API automatically returns them
- API is a **pass-through** - no code changes required

---

## VTT Endpoint Response

### GET /documents/{doc_id}/vtt

**Current Implementation** (Already working):
```python
@router.get("/documents/{doc_id}/vtt")
async def get_vtt(doc_id: str):
    """Get VTT file for audio playback"""

    # Fetch metadata to get vtt_path
    text_results = chroma_client._text_collection.get(
        where={"doc_id": doc_id},
        limit=1
    )

    metadata = text_results["metadatas"][0]

    if not metadata.get("vtt_available"):
        raise HTTPException(
            status_code=404,
            detail={"error": "VTT file not found", ...}
        )

    vtt_path = Path(metadata["vtt_path"])

    if not vtt_path.exists():
        raise HTTPException(status_code=404, ...)

    # Return VTT content
    with open(vtt_path, "r", encoding="utf-8") as f:
        vtt_content = f.read()

    return Response(
        content=vtt_content,
        media_type="text/vtt",
        headers={"Content-Type": "text/vtt; charset=utf-8"}
    )
```

**Changes Required**: None (already works correctly)

**After Fix**:
- `vtt_available` will be `True` instead of `False`
- `vtt_path` will be set to actual file path
- VTT file will exist at that path
- Endpoint returns VTT content successfully

---

## Example: Complete Audio Document Response

```json
{
  "doc_id": "5e57bdeb-f37b-43e3-80ca-63bacaebeaab",
  "filename": "Myth 1.mp3",
  "date_added": "2025-10-16T06:44:27.769582Z",

  "metadata": {
    "raw_metadata": {
      "format_type": "audio",
      "duration": 82.46,
      "audio_codec": "mp3"
    },
    "format_type": "audio",
    "has_timestamps": true,
    "vtt_available": true,
    "markdown_available": true,
    "album_art_available": true,
    "chunk_count": 13
  },

  "chunks": [
    {
      "chunk_id": "chunk_5e57bdeb-f37b-43e3-80ca-63bacaebeaab-chunk0000",
      "text_content": "Myth 1. Ideas come in a flash.",
      "start_time": 0.62,
      "end_time": 3.96,
      "has_timestamps": true,
      "embedding_id": "emb_0"
    },
    {
      "chunk_id": "chunk_5e57bdeb-f37b-43e3-80ca-63bacaebeaab-chunk0001",
      "text_content": "Ideas may feel like they come in a flash, but it's actually after your brain has done a lot of work.",
      "start_time": 5.92,
      "end_time": 12.04,
      "has_timestamps": true,
      "embedding_id": "emb_1"
    }
    // ... more chunks
  ],

  "pages": []
}
```

---

## Frontend Consumption Pattern

### Before Fix (Markdown Parsing)
```javascript
// Frontend had to fetch markdown and parse timestamps
const markdown = await fetch(`/documents/${docId}/markdown`);
const segments = parseMarkdownSegments(markdown);  // Regex parsing
segments.forEach(seg => {
    displaySegment(seg.text, seg.startTime, seg.endTime);
});
```

### After Fix (Direct Field Access)
```javascript
// Frontend uses chunk fields directly
const response = await fetch(`/documents/${docId}`);
const data = await response.json();

data.chunks.forEach(chunk => {
    if (chunk.start_time !== null) {
        displaySegment(chunk.text_content, chunk.start_time, chunk.end_time);
    }
});
```

**Benefits**:
- No markdown parsing needed
- Clean text without markers
- Type-safe access to timestamps
- Backward compatible (check for null)

---

## Testing

### Test 1: Audio with Timestamps
```python
def test_api_response_with_timestamps():
    response = client.get("/documents/5e57bdeb-f37b-43e3-80ca-63bacaebeaab")
    data = response.json()

    assert data["metadata"]["has_timestamps"] == True
    assert data["metadata"]["vtt_available"] == True

    chunk = data["chunks"][0]
    assert chunk["start_time"] is not None
    assert chunk["end_time"] is not None
    assert chunk["start_time"] >= 0.0
    assert chunk["end_time"] > chunk["start_time"]
    assert "[time:" not in chunk["text_content"]
```

### Test 2: Audio without Timestamps
```python
def test_api_response_without_timestamps():
    response = client.get("/documents/{doc_id}")
    data = response.json()

    assert data["metadata"]["has_timestamps"] == False
    assert data["metadata"]["vtt_available"] == False

    chunk = data["chunks"][0]
    assert chunk["start_time"] is None
    assert chunk["end_time"] is None
```

### Test 3: VTT Endpoint Success
```python
def test_vtt_endpoint_returns_content():
    response = client.get("/documents/{doc_id}/vtt")

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/vtt; charset=utf-8"
    assert response.text.startswith("WEBVTT")
    assert "-->" in response.text
```

### Test 4: VTT Endpoint 404
```python
def test_vtt_endpoint_not_available():
    # Document without VTT
    response = client.get("/documents/{doc_id_no_vtt}/vtt")

    assert response.status_code == 404
    assert "VTT file not found" in response.json()["detail"]["error"]
```

---

## Success Criteria

### API Correctness
- [ ] Chunks include `start_time` and `end_time` fields
- [ ] Text content cleaned (no `[time: X-Y]` markers)
- [ ] Metadata flags accurate
- [ ] VTT endpoint returns valid content
- [ ] Backward compatible (null timestamps handled)

### Frontend Compatibility
- [ ] Frontend can access `chunk.start_time` directly
- [ ] Frontend can load VTT from `/documents/{doc_id}/vtt`
- [ ] Frontend handles null timestamps gracefully
- [ ] No breaking changes to existing API structure

### Performance
- [ ] API response time unchanged
- [ ] Response size similar (cleaned text slightly smaller)

---

## Dependencies

**Depends On**:
- IC-001 (TextChunk Timestamp Contract) - chunk fields
- IC-002 (VTT Pipeline Contract) - VTT file creation
- IC-003 (Metadata Flags Contract) - flags in response

**Consumed By**:
- IC-005 (VTT Track Element Contract) - frontend loads VTT
- IC-006 (Caption Display Contract) - frontend uses fields
- IC-007 (Accordion Timestamp Contract) - frontend displays chunks
- Frontend Implementation Agent (Wave 2)

---

## Review Checklist

- [x] Response schema clearly defined
- [x] TypeScript interfaces provided for frontend
- [x] Backward compatibility addressed
- [x] Example responses comprehensive
- [x] No API code changes required (pass-through)
- [x] Test scenarios cover success and failure
- [x] Frontend consumption patterns documented

---

**Contract Status**: ✅ Ready for Implementation

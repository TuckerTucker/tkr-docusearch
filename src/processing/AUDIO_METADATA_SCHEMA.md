# Audio Metadata Schema Design

## Overview
Extension to the document metadata schema to support ID3 tags and audio properties from MP3/WAV files.

## ChromaDB Metadata Fields

### Core Document Fields (Existing)
```python
{
    "doc_id": str,           # SHA-256 hash of file content
    "filename": str,          # Original filename
    "file_size": int,         # File size in bytes
    "format": str,            # "mp3" or "wav"
    "format_type": str,       # "audio"
}
```

### Transcription Fields (Existing - from Docling/Whisper)
```python
{
    "transcript_method": str,           # "whisper"
    "asr_model_used": str,              # "turbo", "base", etc.
    "asr_language": str,                # "en", "es", etc.
    "has_word_timestamps": bool,        # Whether word-level timing exists
}
```

### ID3 Metadata Fields (NEW)
```python
{
    # Basic ID3 tags
    "audio_title": Optional[str],       # TIT2 - Track title
    "audio_artist": Optional[str],      # TPE1 - Primary artist
    "audio_album": Optional[str],       # TALB - Album name
    "audio_album_artist": Optional[str],# TPE2 - Album artist (compilations)
    "audio_year": Optional[str],        # TDRC - Recording year
    "audio_genre": Optional[str],       # TCON - Genre
    "audio_track_number": Optional[str],# TRCK - Track number (e.g., "3/12")

    # Extended metadata (useful for podcasts)
    "audio_composer": Optional[str],    # TCOM - Composer
    "audio_comment": Optional[str],     # COMM - Comment/description
    "audio_publisher": Optional[str],   # TPUB - Publisher/label

    # Technical metadata (not ID3, from mutagen.info)
    "audio_duration_seconds": Optional[float],  # Duration in seconds
    "audio_bitrate_kbps": Optional[int],        # Bitrate in kbps
    "audio_sample_rate_hz": Optional[int],      # Sample rate in Hz
    "audio_channels": Optional[int],            # 1=mono, 2=stereo
    "audio_encoder": Optional[str],             # TSSE - Encoding software
}
```

### Album Art Fields (NEW)
```python
{
    # Album art metadata (reference only, image stored separately)
    "has_album_art": bool,              # Whether album art exists
    "album_art_path": Optional[str],    # Relative path to saved image
    "album_art_mime": Optional[str],    # MIME type (e.g., "image/jpeg")
    "album_art_size_bytes": Optional[int], # Original image size
    "album_art_description": Optional[str], # APIC description (e.g., "Cover (front)")
}
```

## Album Art Storage Strategy

### Filesystem Location
```
data/images/{doc_id}/
├── cover.jpg          # Front cover (primary)
├── cover_thumb.jpg    # Thumbnail (optional, future enhancement)
└── metadata.json      # Image metadata (optional)
```

### Storage Rules
1. **Primary location**: `data/images/{doc_id}/cover.{ext}`
   - Extension matches source: `.jpg`, `.png`, `.gif`
   - Prefer front cover if multiple images exist

2. **Size limits**:
   - No resizing initially (store original)
   - Future: Consider thumbnail generation for UI

3. **Metadata reference**:
   - Store path relative to project root: `data/images/{doc_id}/cover.jpg`
   - Store in ChromaDB `album_art_path` field

4. **Cleanup**:
   - Delete image when document is deleted
   - Handle orphaned images (future enhancement)

## Field Naming Convention

### Rationale for `audio_` prefix
- **Clarity**: Distinguishes audio metadata from document metadata
- **Consistency**: Matches existing pattern (`visual_embeddings`, `text_embeddings`)
- **Namespace**: Prevents collisions with future features
- **Searchability**: Easy to filter in ChromaDB queries

### Alternative considered: `id3_` prefix
- ❌ Too specific (excludes WAV properties)
- ❌ Technical jargon (ID3 is MP3-specific)
- ✅ `audio_` is format-agnostic

## ChromaDB Size Constraints

### Metadata Size Limits
- ChromaDB has no hard limit, but recommend < 100KB per document
- Our schema: ~20 fields × ~100 bytes avg = ~2KB ✅
- Album art stored separately (not in metadata) ✅

### Handling Large Text Fields
- `audio_comment` can be long (podcast descriptions)
- Truncate if > 1000 characters
- Store full text in separate file if needed (future)

## Handling Missing Data

### Default Values
```python
# When tag is missing
"audio_title": None          # Not filename fallback
"audio_artist": None         # Not "Unknown Artist"
"audio_album": None          # Explicit None for clarity

# When property unavailable
"audio_duration_seconds": None  # Let Docling provide if possible
```

### Rationale
- **Explicit None**: Distinguishes "missing" from "empty string"
- **No fallbacks**: Prevents pollution with guessed/generated data
- **Search flexibility**: Can query for `WHERE audio_artist IS NULL`

## Search Enhancement Examples

### After Implementation
```python
# Find all podcasts by specific artist
results = search_engine.search(
    query="AI ethics",
    filter={"audio_artist": "Lex Fridman"}
)

# Find music from specific year
results = search_engine.search(
    query="rock music",
    filter={"audio_year": "1990", "audio_genre": "Rock"}
)

# Find files with album art
results = search_engine.search(
    query="presentation",
    filter={"has_album_art": True}
)
```

## Backward Compatibility

### Existing Documents
- Old documents have `None` for new fields ✅
- No migration needed ✅
- Search works on both old and new documents ✅

### New Fields Optional
- All new fields are `Optional[...]` in type hints
- Code checks existence before accessing
- Graceful degradation if missing

## Future Enhancements

### Potential Additions
1. **Podcast-specific fields**:
   - Episode number
   - Show notes URL
   - Chapter markers

2. **Audio analysis**:
   - Waveform generation
   - Spectogram thumbnails
   - Audio fingerprinting

3. **Multi-language support**:
   - Detected language (separate from ASR language)
   - Multiple transcriptions

## Implementation Checklist
- [ ] Create `audio_metadata.py` extractor
- [ ] Update `docling_parser.py` to use extractor
- [ ] Implement album art filesystem storage
- [ ] Add fields to metadata merging logic
- [ ] Test with files that have: full tags, partial tags, no tags
- [ ] Verify ChromaDB indexing of new fields
- [ ] Update documents API to return new fields

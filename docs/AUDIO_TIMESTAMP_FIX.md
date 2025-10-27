# Audio Timestamp Fix - October 2025

## Problem

**Regression Detected**: Audio files uploaded after October 27, 2025 had no timestamps, breaking bidirectional navigation between the audio player and text accordion.

**Symptoms**:
- Accordion sections showed "Page 1" instead of "Chunk 1/2"
- VTT transcript section missing from accordion
- Console logs showed `start_time: null, end_time: null`
- Bidirectional navigation broken (clicking accordion didn't seek audio)

## Root Cause

**Line 178 in `src/processing/docling_parser.py`** used the wrong export method:

```python
# BROKEN - strips timestamp markers
text = doc.export_to_text()
```

Docling's `export_to_text()` method strips `[time: X-Y]` timestamp markers from the transcript, while `export_to_markdown()` preserves them.

**Why this matters**: The ingestion pipeline relies on these markers being present in the text. The `text_processor.py:extract_timestamps_from_text()` function parses these markers to extract start/end times for each chunk.

## Investigation Path

1. **Initial Hypothesis**: Docling provenance data extraction
   - Enhanced `_extract_chunk_timestamps()` to extract from provenance
   - Created debug tools to inspect docling structure
   - **Finding**: MLX Whisper does NOT populate provenance data (`prov: False`)

2. **Research**: Docling documentation and examples
   - Found ASR pipeline example: `docs/examples/minimal_asr_pipeline.py`
   - Example showed `export_to_markdown()` preserves timestamps:
     ```python
     # [time: 0.0-4.0] Shakespeare on Scenery by Oscar Wilde
     # [time: 5.28-9.96] This is a LibriVox recording...
     ```
   - **Root cause identified**: We were using the wrong export method

## Solution

### 1. Fix Audio Export Method

**File**: `src/processing/docling_parser.py` (lines 174-200)

```python
# Handle audio formats (transcript only, no images)
if ext and ext in AUDIO_FORMATS:
    logger.info(f"Processing audio file as text-only transcript")
    try:
        # IMPORTANT: Use export_to_markdown() for audio to preserve [time: X-Y] markers
        # export_to_text() strips these markers, breaking timestamp extraction
        text = doc.export_to_markdown() if hasattr(doc, "export_to_markdown") else ""

        logger.info(f"[AUDIO] Using export_to_markdown() to preserve timestamps")

        # Check if timestamps are present in output
        import re
        timestamp_pattern = r"\[time:\s*([\d.]+)-([\d.]+)\]"
        timestamp_matches = re.findall(timestamp_pattern, text)
        if timestamp_matches:
            logger.info(f"[AUDIO] ✓ Found {len(timestamp_matches)} timestamp markers in transcript")
        else:
            logger.warning(f"[AUDIO] ⚠ NO timestamp markers found in transcript - timestamps may not work")

        pages.append(
            Page(page_num=1, image=None, width=0, height=0, text=text)
        )
```

**Key Changes**:
- Changed from `export_to_text()` to `export_to_markdown()`
- Added logging to verify timestamp markers are present
- Added warning if no markers found (for debugging)

### 2. Fix Audio Accordion Titles

**File**: `frontend/src/features/details/TextAccordion.jsx` (lines 231-244)

```javascript
let title;

// Determine if this is an audio document
const isAudio = document?.metadata?.format_type === 'audio';

if (hasTimestamp) {
  title = `Segment ${index + 1}`;
} else if (pageNumber && !isAudio) {
  // Only use page numbers for visual documents (PDF, PPTX, etc.)
  // Audio transcripts shouldn't show "Page 1" - they should show "Chunk 1"
  title = `Page ${pageNumber}`;
} else {
  title = `Chunk ${index + 1}`;
}
```

**Why**: Audio chunks were incorrectly showing "Page 1" because page_number was being set. This ensures audio shows "Chunk 1/2" instead.

### 3. Integration Test to Prevent Regression

**File**: `tests/test_audio_timestamp_integration.py` (NEW)

```python
def test_audio_timestamp_extraction(audio_file, processor, tmp_path):
    """Test that audio timestamps are extracted correctly."""

    # Process audio file
    result = processor.process_document(file_path=audio_file)

    # Retrieve from ChromaDB
    storage = processor.storage_client
    text_data = storage.client.get_collection("text").get(
        where={"filename": Path(audio_file).name}
    )

    # Check timestamp extraction
    chunks_with_timestamps = [
        m for m in text_data["metadatas"]
        if m.get("start_time") is not None and m.get("end_time") is not None
    ]

    # CRITICAL ASSERTION: Audio files MUST have timestamps
    assert chunks_with_timestamps, (
        "REGRESSION: Audio file has NO timestamps! "
        "This breaks bidirectional navigation. "
        "Check docling provenance extraction."
    )
```

**Purpose**: This test will fail immediately if timestamps are missing, preventing future regressions.

## How the Fix Works

### Timestamp Flow (End-to-End)

1. **Audio Ingestion** (`docling_parser.py`):
   - Docling converts audio to transcript with MLX Whisper
   - `export_to_markdown()` preserves `[time: X-Y]` markers in text
   - Example: `"[time: 0.0-4.0] Shakespeare on Scenery by Oscar Wilde"`

2. **Text Processing** (`text_processor.py`):
   - `extract_timestamps_from_text()` parses markers using regex
   - Extracts start_time from FIRST marker, end_time from LAST marker
   - Returns cleaned text with markers removed

3. **Chunk Creation** (`processor.py`):
   - Chunks inherit timestamps from parent text
   - Metadata includes `start_time`, `end_time`, `has_timestamps: true`

4. **VTT Generation** (`vtt_generator.py`):
   - Creates WebVTT subtitle file from timestamped chunks
   - Uses `caption_splitter.py` for intelligent caption splitting

5. **Frontend Display** (`TextAccordion.jsx`):
   - Renders accordion sections with timestamps
   - Shows "VTT Transcript" section if available
   - Enables bidirectional navigation

## Verification Steps

### 1. Check Logs

```bash
tail -f logs/worker-native.log | grep AUDIO
```

**Expected Output**:
```
[AUDIO] Using export_to_markdown() to preserve timestamps
[AUDIO] ✓ Found 47 timestamp markers in transcript
```

**Bad Output**:
```
[AUDIO] ⚠ NO timestamp markers found in transcript - timestamps may not work
```

### 2. Upload Audio File

1. Go to http://localhost:3000
2. Upload an MP3/WAV file
3. Check ingestion success

### 3. Verify UI

**Expected Behavior**:
- Accordion shows "Chunk 1", "Chunk 2", etc. (NOT "Page 1")
- "VTT Transcript" section appears in accordion
- Clicking accordion seeks audio player
- Audio playback highlights current chunk

**Check Console**:
```javascript
// Should show timestamps
start_time: 0.0
end_time: 4.0
```

### 4. Run Integration Test

```bash
pytest tests/test_audio_timestamp_integration.py -v
```

**Expected**: All assertions pass, including the critical timestamp check.

## Debug Tools

### Inspect Audio Provenance

```bash
python scripts/inspect_audio_provenance.py tests/fixtures/sample.mp3
```

**Purpose**: Dumps docling document structure and provenance data.

**Key Findings**:
- MLX Whisper does NOT populate `doc.texts[].prov`
- Must use markdown export to preserve timestamps
- `export_to_text()` output has no `[time: X-Y]` markers

### Inspect Whisper Output

```bash
python scripts/inspect_whisper_output.py tests/fixtures/sample.mp3
```

**Purpose**: Inspects raw docling result attributes and backend data.

## Technical Details

### Timestamp Format

**In Transcript**:
```markdown
[time: 0.0-4.0] Shakespeare on Scenery by Oscar Wilde
[time: 5.28-9.96] This is a LibriVox recording...
```

**Regex Pattern**:
```python
r"\[time:\s*([\d.]+)-([\d.]+)\]"
```

**In ChromaDB**:
```json
{
  "start_time": 0.0,
  "end_time": 4.0,
  "has_timestamps": true
}
```

**In VTT**:
```vtt
WEBVTT

1
00:00:00.000 --> 00:00:04.000
Shakespeare on Scenery by Oscar Wilde

2
00:00:05.280 --> 00:00:09.960
This is a LibriVox recording...
```

### Why MLX Whisper Doesn't Use Provenance

Docling's provenance system was designed for document layout analysis (pages, paragraphs, tables). Audio transcription is a different domain - there's no "page" or "layout" to track. Instead, MLX Whisper embeds timestamps directly in the markdown output using `[time: X-Y]` markers.

This is actually MORE reliable than provenance because:
1. It survives text processing/chunking
2. It's explicitly designed for temporal data
3. It's format-agnostic (works with any parser)

## Dependencies

- **Docling**: >= 2.58.0 (for MLX Whisper support)
- **MLX**: Apple Silicon optimization (5x faster than CPU Whisper)
- **text_processor.py**: `extract_timestamps_from_text()` function
- **vtt_generator.py**: VTT file generation
- **caption_splitter.py**: Intelligent caption chunking

## Related Files

### Backend
- `src/processing/docling_parser.py` - Audio parsing (THE FIX)
- `src/processing/text_processor.py` - Timestamp extraction
- `src/processing/processor.py` - Document processing orchestration
- `src/storage/vtt_generator.py` - VTT file generation
- `src/utils/caption_splitter.py` - Caption splitting logic

### Frontend
- `frontend/src/features/details/TextAccordion.jsx` - Accordion titles (FIXED)
- `frontend/src/features/details/DocumentDetailsPage.jsx` - Audio player integration
- `frontend/src/components/ui/Accordion.jsx` - Base accordion component

### Tests
- `tests/test_audio_timestamp_integration.py` - Integration test (NEW)
- `tests/fixtures/sample.mp3` - Test audio file

### Debug Tools
- `scripts/inspect_audio_provenance.py` - Provenance inspector (NEW)
- `scripts/inspect_whisper_output.py` - Whisper output inspector (NEW)

## Future Considerations

1. **Timestamp Precision**: Currently uses seconds (float). Consider milliseconds for precise seeking.

2. **Alternative ASR Providers**: If switching from MLX Whisper, verify timestamp format compatibility.

3. **Chunking Strategy**: Current strategy uses word count. Consider time-based chunking for audio (e.g., 30-second segments).

4. **VTT Customization**: Add styling, positioning, or speaker identification in future.

5. **Monitoring**: Add metrics for timestamp extraction success rate.

## Lessons Learned

1. **Export Method Matters**: Always check which docling export method preserves required metadata.

2. **Provenance Isn't Universal**: Not all docling backends populate provenance data.

3. **Test at Integration Level**: Unit tests on provenance extraction passed, but integration test would have caught the real issue.

4. **Debug Tools Are Essential**: Custom inspection scripts were critical for understanding docling's internal structure.

5. **Documentation Examples**: Docling's own examples provided the key insight - always check official examples.

## Summary

**Problem**: Audio timestamps broken due to using `export_to_text()` which strips `[time: X-Y]` markers.

**Solution**: Use `export_to_markdown()` for audio files to preserve timestamp markers.

**Impact**: Fixes bidirectional navigation, VTT generation, and audio player sync.

**Prevention**: Integration test ensures timestamps are present for all audio uploads.

**Status**: ✅ FIXED and deployed (October 27, 2025)

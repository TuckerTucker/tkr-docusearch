# Parser ASR Implementation Interface Contract

**Provider**: parser-agent (docling_parser module)
**Consumers**: processor-agent (existing pipeline)
**File**: `src/processing/docling_parser.py`

## Interface Specification

### Modified: _parse_with_docling()

**Purpose**: Add Whisper ASR support for MP3/WAV audio files.

**Current Signature** (unchanged):
```python
def _parse_with_docling(
    self,
    file_path: str,
    config: Optional[EnhancedModeConfig] = None
) -> tuple:
    """Parse document using Docling.

    Returns:
        Tuple of (pages, metadata, docling_document)
    """
```

**Modified Implementation Contract**:

Add ASR pipeline configuration for `.mp3` and `.wav` files (after line 455):

```python
# New imports at top of file
from docling.datamodel import asr_model_specs
from docling.datamodel.pipeline_options import AsrPipelineOptions
from docling.pipeline.asr_pipeline import AsrPipeline
from docling.document_converter import AudioFormatOption
from docling.datamodel.base_models import InputFormat
from src.config.processing_config import AsrConfig

# Inside _parse_with_docling(), after format_options dict created
ext = Path(file_path).suffix.lower()

# Configure ASR for audio files
if ext in ['.mp3', '.wav']:
    try:
        # Load ASR configuration
        asr_config = AsrConfig.from_env()

        if asr_config.enabled:
            logger.info(f"Configuring ASR pipeline for {ext} with model={asr_config.model}")

            # Create Docling ASR options
            pipeline_options = AsrPipelineOptions()
            pipeline_options.asr_options = asr_config.to_docling_model_spec()

            # Add to format options
            format_options[InputFormat.AUDIO] = AudioFormatOption(
                pipeline_cls=AsrPipeline,
                pipeline_options=pipeline_options
            )

            logger.debug(
                f"ASR config: model={asr_config.model}, "
                f"language={asr_config.language}, device={asr_config.device}"
            )
        else:
            logger.warning(f"ASR disabled, audio file {file_path} will have minimal processing")

    except Exception as e:
        logger.error(f"Failed to configure ASR: {e}")
        # Continue without ASR (fallback to basic processing)
```

### Modified Metadata for Audio Files

**Additional metadata fields for audio** (added around line 492):

```python
# After existing metadata fields
if ext in ['.mp3', '.wav'] and format_type_enum == FormatType.AUDIO:
    # ASR-specific metadata
    metadata["transcript_method"] = "whisper"
    metadata["asr_model_used"] = asr_config.model if 'asr_config' in locals() else "unknown"
    metadata["asr_language"] = asr_config.language if 'asr_config' in locals() else "unknown"
    metadata["audio_format"] = ext[1:]  # "mp3" or "wav"

    # Try to extract duration from Docling document
    if hasattr(doc, 'audio_duration'):
        metadata["audio_duration_seconds"] = doc.audio_duration
    elif hasattr(doc.origin, 'duration'):
        metadata["audio_duration_seconds"] = doc.origin.duration

    # Extract timestamp information if available
    if hasattr(doc, 'texts') and doc.texts:
        # Check if timestamps are in provenance
        has_timestamps = False
        for text_item in doc.texts:
            if hasattr(text_item, 'prov') and text_item.prov:
                for prov in text_item.prov:
                    if hasattr(prov, 'start_time') and hasattr(prov, 'end_time'):
                        has_timestamps = True
                        break
                if has_timestamps:
                    break

        metadata["has_word_timestamps"] = has_timestamps
```

## Contract Requirements

### ASR Configuration:
1. **Must attempt ASR config** for `.mp3` and `.wav` files
2. **Must not break parsing** if ASR config fails (log error, continue)
3. **Must respect ASR_ENABLED** environment variable
4. **Must log ASR configuration** details (model, language, device)

### Audio Metadata:
Required fields for audio files:
- `transcript_method`: "whisper" (literal string)
- `asr_model_used`: Model name (turbo, base, etc.)
- `asr_language`: Language code or "auto"
- `audio_format`: "mp3" or "wav"

Optional fields (if available):
- `audio_duration_seconds`: float
- `has_word_timestamps`: bool

### Error Handling:
- ASR config fails → log error, continue with basic processing
- Whisper transcription fails → Docling should raise, propagate error
- Missing dependencies → log error, continue with basic processing

### Backward Compatibility:
- VTT files (.vtt) continue to work unchanged
- Non-audio files unaffected
- No breaking changes to existing API

## Data Flow

```
MP3/WAV file →
Detect format →
Load AsrConfig →
Create AsrPipelineOptions →
Add to format_options →
DocumentConverter.convert() →
Whisper transcription →
DoclingDocument with transcript →
Extract metadata →
Return (pages, metadata, doc)
```

## Performance Contract

- ASR configuration overhead: <50ms
- Whisper transcription: depends on audio length and device
  - CPU: ~30-60s per minute of audio
  - MPS: ~3-6s per minute of audio (10x faster)
  - CUDA: ~2-3s per minute of audio (20x faster)
- No impact on non-audio file processing

### Performance Monitoring:
Log transcription time:
```python
start = time.time()
result = converter.convert(file_path)
duration = time.time() - start
logger.info(f"Audio transcription took {duration:.1f}s")
```

## Format-Specific Behavior

### MP3 Files:
- Requires ffmpeg for decoding
- Supported bitrates: 32-320 kbps
- Supported sample rates: 8-48 kHz
- Maximum duration: unlimited (but processing time scales linearly)

### WAV Files:
- Native support (no ffmpeg needed)
- Supported sample rates: 8-48 kHz
- Supported bit depths: 8, 16, 24, 32
- Maximum duration: unlimited

### VTT Files (unchanged):
- Transcript already present
- No ASR needed
- Existing processing continues unchanged

## Testing Contract

Parser agent MUST implement:
- Unit test: MP3 file with ASR enabled
- Unit test: WAV file with ASR enabled
- Unit test: Audio file with ASR disabled (fallback)
- Unit test: ASR config failure (graceful degradation)
- Unit test: Metadata includes ASR fields
- Integration test: MP3 → transcript → pages → chunks
- Integration test: WAV → transcript → pages → chunks
- Performance test: 10s audio <5s processing time (MPS)

## Validation Checklist

- [ ] ASR imports added
- [ ] AsrConfig loading added
- [ ] ASR pipeline configuration added
- [ ] Audio-specific metadata added
- [ ] Error handling for ASR failures
- [ ] Logging for ASR configuration and timing
- [ ] VTT files still work unchanged
- [ ] Non-audio files unaffected
- [ ] Tests cover MP3 and WAV
- [ ] Tests cover ASR enabled/disabled
- [ ] Performance benchmarks documented

## Integration Notes

**Config Agent**: Provides AsrConfig class
**Processor Agent**: Receives unchanged pages/metadata (no changes needed)
**Storage Agent**: Receives audio metadata (no special handling)
**Existing Pipeline**: Works unchanged (audio files are text-only documents)

## Dependencies

### System Requirements:
- **ffmpeg**: Required for MP3 decoding
  - Installation: `brew install ffmpeg` (macOS)
  - Verify: `ffmpeg -version`
  - Docling will raise error if missing for MP3 files

### Python Requirements:
- `docling[asr]`: Includes openai-whisper and dependencies
- `torch`: For Whisper inference
- Already installed in current environment

### Model Downloads:
- Whisper models downloaded on first use
- Cached in HuggingFace cache directory
- Turbo model: ~809MB download
- Happens automatically, may add 1-2min on first run

## Error Messages

### Missing ffmpeg:
```
ERROR: ffmpeg not found. Install with: brew install ffmpeg
Audio file processing requires ffmpeg for MP3 decoding.
```

### Missing ASR dependencies:
```
ERROR: Docling ASR not installed. Install with: pip install docling[asr]
```

### Transcription failure:
```
ERROR: Whisper transcription failed: [error details]
Check audio file format and ensure ffmpeg is working correctly.
```

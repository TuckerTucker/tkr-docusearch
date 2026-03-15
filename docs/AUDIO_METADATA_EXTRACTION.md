# Audio Metadata Extraction

## Overview

DocuSearch automatically extracts ID3 metadata tags and audio properties from MP3 and WAV files during processing. This metadata is stored in Koji (Lance-based file database) alongside transcriptions and embeddings, making audio files fully searchable by both content and metadata.

## Features

### ID3 Tag Extraction
Extracts standard ID3v2 tags from audio files:
- **Title** (`audio_title`) - Track title
- **Artist** (`audio_artist`) - Performing artist
- **Album** (`audio_album`) - Album name
- **Album Artist** (`audio_album_artist`) - Album artist (may differ from track artist)
- **Year** (`audio_year`) - Release year
- **Genre** (`audio_genre`) - Music genre
- **Track Number** (`audio_track_number`) - Track number in album
- **Composer** (`audio_composer`) - Song composer
- **Comment** (`audio_comment`) - ID3 comment field
- **Publisher** (`audio_publisher`) - Record label/publisher

### Audio Properties
Extracts technical audio information:
- **Duration** (`audio_duration_seconds`) - Track length in seconds
- **Bitrate** (`audio_bitrate_kbps`) - Audio bitrate in kbps
- **Sample Rate** (`audio_sample_rate_hz`) - Sample rate in Hz (e.g., 44100)
- **Channels** (`audio_channels`) - Number of audio channels (1=mono, 2=stereo)
- **Encoder** (`audio_encoder`) - Software used to encode the file
- **Format** (`audio_format`) - File format (mp3, wav, etc.)

### Album Art Extraction
Extracts and stores embedded album artwork:
- Automatically saves album art to `data/images/{doc_id}/cover.{ext}`
- Stores metadata: `album_art_path`, `album_art_mime`, `album_art_size_bytes`, `album_art_description`
- Supports JPEG and PNG formats
- Flag: `has_album_art` (boolean)

## Architecture

### Components

1. **`src/processing/audio_metadata.py`** - Core extraction module
   - `AudioMetadata` dataclass - Metadata container
   - `extract_audio_metadata()` - Main extraction function
   - `save_album_art()` - Album art file writer
   - Uses `mutagen` library for universal audio format support

2. **`src/processing/docling_parser.py`** - Integration point
   - Calls ID3 extraction before Docling conversion
   - Merges ID3 metadata with transcription metadata
   - Handles album art extraction and temporary storage

3. **`src/processing/processor.py`** - Storage coordination
   - Saves album art to filesystem
   - Stores metadata in Koji with embeddings
   - Filters binary data from Koji metadata

### Processing Flow

```
1. Audio file uploaded via POST /uploads/ (worker, port 8002)
   ↓
2. Webhook triggers processing
   ↓
3. ID3 extraction (audio_metadata.py)
   - Read ID3 tags
   - Extract audio properties
   - Extract album art (APIC frames)
   ↓
4. Whisper transcription (docling_parser.py)
   - Convert audio to text
   - Generate embeddings via Shikomi (gRPC, port 50051)
   ↓
5. Metadata merging
   - Combine ID3 tags + audio properties + transcription metadata
   ↓
6. Storage (processor.py)
   - Save album art to filesystem
   - Store embeddings + metadata in Koji
```

## Usage

### Automatic Processing

Audio metadata extraction is automatic. Simply upload MP3 or WAV files through the worker upload endpoint at `http://localhost:8002/uploads/`:

1. Upload audio file
2. Wait for processing to complete
3. Metadata and album art are automatically extracted and stored

### Manual Testing

Test ID3 extraction on a specific file:

```bash
python3 << 'EOF'
from src.processing.audio_metadata import extract_audio_metadata

# Extract metadata
metadata = extract_audio_metadata("data/uploads/your_file.mp3")

# Display results
print(f"Title: {metadata.title}")
print(f"Artist: {metadata.artist}")
print(f"Album: {metadata.album}")
print(f"Duration: {metadata.duration_seconds}s")
print(f"Bitrate: {metadata.bitrate_kbps} kbps")
print(f"Album art: {'Yes' if metadata.has_album_art else 'No'}")

# Display all metadata as dict
print("\nMetadata dict:")
print(metadata.to_dict())
EOF
```

### Querying Metadata

Search Koji for audio files with specific metadata:

```python
import koji

db = koji.open("data/koji.db")

# Find all audio files
results = db.query(
    "text_embeddings",
    filter="format_type = 'audio'",
    limit=100,
)

# Filter by specific artist (example)
for row in results:
    if row.get('audio_artist') == 'Artist Name':
        print(f"Found: {row['filename']}")
        print(f"  Album: {row.get('audio_album')}")
        print(f"  Duration: {row.get('audio_duration_seconds')}s")
```

## Album Art Storage

### File Structure
```
data/images/
└── {doc_id}/
    └── cover.{ext}   # JPEG or PNG
```

### Accessing Album Art

Album art path is stored in metadata:
```python
# Get album art path from metadata
album_art_path = metadata.get('album_art_path')

# Example: data/images/dd2e80cd-0e04-40f3-9559-d63d44b4da1b/cover.jpg

# Verify file exists
import os
if album_art_path and os.path.exists(album_art_path):
    print(f"Album art: {album_art_path}")
    print(f"Size: {os.path.getsize(album_art_path)} bytes")
```

## Metadata Schema

All audio metadata fields use the `audio_` prefix in Koji. See [AUDIO_METADATA_SCHEMA.md](../src/processing/AUDIO_METADATA_SCHEMA.md) for complete schema documentation.

### Example Metadata in Koji

```json
{
  "filename": "track.mp3",
  "format_type": "audio",
  "audio_duration_seconds": 691.9,
  "audio_bitrate_kbps": 128,
  "audio_sample_rate_hz": 44100,
  "audio_channels": 2,
  "audio_encoder": "GarageBand 10.1.2",
  "audio_format": "mp3",
  "audio_title": "Track Title",
  "audio_artist": "Artist Name",
  "audio_album": "Album Name",
  "audio_year": "2023",
  "audio_genre": "Rock",
  "has_album_art": true,
  "album_art_path": "data/images/{doc_id}/cover.jpg",
  "album_art_mime": "image/jpeg",
  "album_art_size_bytes": 34949,
  "asr_model_used": "turbo",
  "asr_language": "en"
}
```

## Supported Audio Formats

- **MP3** (.mp3) - Full ID3v2 tag support
- **WAV** (.wav) - Basic metadata support

## Dependencies

The feature requires the `mutagen` library for audio metadata extraction:

```bash
# Included in requirements.txt
mutagen>=1.47.0
```

When setting up the native worker, mutagen is automatically installed:

```bash
./scripts/run-worker-native.sh setup
```

## Troubleshooting

### No ID3 Tags Extracted

**Problem**: Metadata shows only audio properties, no ID3 tags.

**Causes**:
1. File doesn't contain ID3 tags (some audio files lack metadata)
2. File has ID3v1 tags (not supported - only ID3v2)
3. File is corrupted

**Solution**:
- Use audio tagging software (e.g., MP3Tag, MusicBrainz Picard) to add ID3v2 tags
- Verify tags with: `python3 -m mutagen.id3 your_file.mp3`

### Album Art Not Saved

**Problem**: `has_album_art: true` but no file in `data/images/`

**Causes**:
1. Insufficient disk space
2. Permission issues on `data/images/` directory
3. Processing error (check worker logs)

**Solution**:
```bash
# Check permissions
ls -ld data/images/

# Check disk space
df -h data/

# Check worker logs for errors
grep -i "album art" logs/worker-native.log
```

### Processing Fails for Audio Files

**Problem**: Audio files upload but processing fails

**Causes**:
1. Whisper not installed or configured
2. FFmpeg not available (required for Whisper)
3. Path handling issues

**Solution**:
```bash
# Verify Whisper is available
python3 -c "import whisper; print('OK')"

# Verify FFmpeg is available
ffmpeg -version

# Check worker logs
tail -100 logs/worker-native.log | grep -i error
```

### Metadata Missing in Koji

**Problem**: Audio processed but metadata not in Koji

**Causes**:
1. Koji DB file not found or path misconfigured (`KOJI_DB_PATH`)
2. Metadata filtering removed fields
3. Field name mismatch

**Solution**:
```bash
# Verify KOJI_DB_PATH is set
echo $KOJI_DB_PATH

# Check what metadata was stored
python3 << 'EOF'
import koji
db = koji.open("data/koji.db")
results = db.query("text_embeddings", limit=1)
if results:
    print(list(results[0].keys()))
EOF
```

## Performance

- **ID3 extraction**: ~10-50ms per file
- **Album art extraction**: ~5-20ms for typical 30-100KB images
- **No impact on transcription**: Extraction runs in parallel with Whisper

## Future Enhancements

Potential improvements:
- Support for additional audio formats (FLAC, M4A, OGG)
- Lyrics extraction (USLT frames)
- BPM and key detection
- ReplayGain information
- Multi-image support (back cover, booklet)
- Batch metadata editing interface

## See Also

- [AUDIO_METADATA_SCHEMA.md](../src/processing/AUDIO_METADATA_SCHEMA.md) - Complete metadata schema
- [NATIVE_WORKER_SETUP.md](NATIVE_WORKER_SETUP.md) - Worker configuration
- [QUICK_START.md](QUICK_START.md) - Getting started guide

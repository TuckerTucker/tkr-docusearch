# TinyTag Migration: Linear Implementation Plan

**Related ADR**: `audio-metadata-library-decision.md` (ADR-001)
**Goal**: Replace mutagen (GPLv2+) with TinyTag (MIT) for license compliance
**Priority**: Quality with thorough testing
**Estimated Duration**: 2-3 hours focused work
**Status**: READY TO IMPLEMENT

---

## Overview

This plan provides a linear, dependency-ordered sequence of tasks to migrate from mutagen to TinyTag while maintaining all critical functionality and ensuring zero breakage.

**Key Principles**:
- Each task builds on previous completed work
- Multiple validation points throughout
- Clear rollback procedures at each stage
- No artificial parallelization (dependencies are sequential)

---

## Prerequisites Check

Before starting, verify:
- [ ] Git working directory is clean
- [ ] All tests currently passing
- [ ] Worker is running and healthy
- [ ] You have ~2-3 hours of focused time available

```bash
# Verify prerequisites
git status
pytest src/processing/test_audio_metadata.py -v
./scripts/status.sh
```

---

## Task Checklist

### Phase: Setup & Preparation (30 min)

#### ☐ Task 1: Create feature branch and backup
**Duration**: 5 min
**Risk**: LOW
**Rollback**: `git checkout main && git branch -D feat/migrate-tinytag-license-compliance`

```bash
# Create feature branch
git checkout -b feat/migrate-tinytag-license-compliance

# Backup current implementation
cp src/processing/audio_metadata.py src/processing/audio_metadata_mutagen.backup

# Verify backup
ls -lh src/processing/audio_metadata_mutagen.backup
```

**Success Criteria**:
- [ ] New branch created
- [ ] Backup file exists
- [ ] Working directory clean

---

#### ☐ Task 2: Install TinyTag and verify basic functionality
**Duration**: 10 min
**Risk**: MEDIUM (validates library compatibility early)
**Rollback**: `pip uninstall tinytag`

```bash
# Install TinyTag
pip install tinytag==1.10.1

# Verify installation
python -c "from tinytag import TinyTag; print(TinyTag.__version__)"

# Test with sample MP3 (if available)
python -c "
from tinytag import TinyTag
import os

# Find a test MP3 file
test_files = [
    'data/uploads/test.mp3',
    'src/processing/test_data/sample.mp3'
]

for f in test_files:
    if os.path.exists(f):
        tag = TinyTag.get(f, image=True)
        print(f'✅ TinyTag works with {f}')
        print(f'   Title: {tag.title}')
        print(f'   Duration: {tag.duration}s')
        print(f'   Has image: {tag.get_image() is not None}')
        break
else:
    print('⚠️ No test MP3 files found - will validate during testing phase')
"
```

**Success Criteria**:
- [ ] TinyTag installed successfully
- [ ] Can import TinyTag module
- [ ] Basic extraction works (if test file available)

**Validation**:
```bash
pip show tinytag | grep "Version\|License"
# Expected: Version: 1.10.1, License: MIT
```

---

#### ☐ Task 3: Prepare test fixtures
**Duration**: 15 min
**Risk**: LOW
**Rollback**: Delete test files

Create comprehensive test files to validate the migration:

```bash
# Create test data directory if needed
mkdir -p src/processing/test_data

# You'll need these test cases:
# 1. MP3 with ID3v2 tags + JPEG album art
# 2. MP3 with PNG album art (tests MIME detection)
# 3. WAV without tags (tests audio properties only)
# 4. MP3 without album art (tests fallback)

# Document where test files are located
cat > src/processing/test_data/README.md << 'EOF'
# Test Audio Files

Required for TinyTag migration validation:

1. **test_with_jpeg_art.mp3**: MP3 with ID3v2.4 tags and JPEG album art
2. **test_with_png_art.mp3**: MP3 with PNG album art (tests MIME detection)
3. **test_no_tags.wav**: WAV file without metadata tags
4. **test_no_art.mp3**: MP3 with tags but no album art

These files are used to validate:
- Audio property extraction (duration, bitrate, sample rate, channels)
- ID3 tag extraction (title, artist, album, year, genre, etc.)
- Album art extraction with correct MIME type detection
- Graceful handling of missing metadata
EOF
```

**Success Criteria**:
- [ ] Test data directory exists
- [ ] At least 2-3 test audio files available
- [ ] Test files represent different edge cases

---

### Phase: Core Implementation (60 min)

#### ☐ Task 4: Update AudioMetadata dataclass
**Duration**: 5 min
**Risk**: MEDIUM (interface change affects downstream code)
**Rollback**: `git checkout src/processing/audio_metadata.py`

**File**: `src/processing/audio_metadata.py:26-54`

```python
# REMOVE these fields from AudioMetadata dataclass:
composer: Optional[str] = None          # Line 38
publisher: Optional[str] = None         # Line 40
encoder: Optional[str] = None           # Line 47

# KEEP all other fields unchanged
```

**Success Criteria**:
- [ ] Three fields removed from dataclass
- [ ] All other fields remain intact
- [ ] No syntax errors (`python -m py_compile src/processing/audio_metadata.py`)

---

#### ☐ Task 5: Replace import statements
**Duration**: 2 min
**Risk**: LOW
**Rollback**: Undo changes

**File**: `src/processing/audio_metadata.py:15-21`

```python
# REMOVE:
try:
    from mutagen import File as MutagenFile
    from mutagen.id3 import ID3
    from mutagen.mp3 import MP3
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

# REPLACE WITH:
try:
    from tinytag import TinyTag
    import imghdr
    TINYTAG_AVAILABLE = True
except ImportError:
    TINYTAG_AVAILABLE = False
```

**Success Criteria**:
- [ ] Old imports removed
- [ ] New imports added
- [ ] TINYTAG_AVAILABLE flag replaces MUTAGEN_AVAILABLE

---

#### ☐ Task 6: Rewrite extract_audio_metadata() function
**Duration**: 30 min
**Risk**: HIGH (core functionality rewrite)
**Rollback**: `cp src/processing/audio_metadata_mutagen.backup src/processing/audio_metadata.py`

**File**: `src/processing/audio_metadata.py:112-167`

**Complete replacement implementation**:

```python
def extract_audio_metadata(file_path: str) -> AudioMetadata:
    """
    Extract ID3 tags and audio properties from an audio file using TinyTag.

    Args:
        file_path: Path to MP3 or WAV file

    Returns:
        AudioMetadata instance with extracted data

    Raises:
        ImportError: If TinyTag is not installed
        FileNotFoundError: If file doesn't exist
        Exception: For other errors (logged, not raised - returns empty metadata)
    """
    if not TINYTAG_AVAILABLE:
        logger.error("TinyTag library not installed - cannot extract audio metadata")
        raise ImportError("TinyTag is required for audio metadata extraction")

    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    metadata = AudioMetadata()

    try:
        # Load audio file with TinyTag (include image data)
        tag = TinyTag.get(file_path, image=True)

        logger.debug(f"Processing audio file: {file_path_obj.name}")

        # Extract audio properties
        if tag.duration is not None:
            metadata.duration_seconds = float(tag.duration)
        if tag.bitrate is not None:
            metadata.bitrate_kbps = int(tag.bitrate)
        if tag.samplerate is not None:
            metadata.sample_rate_hz = int(tag.samplerate)
        if tag.channels is not None:
            metadata.channels = int(tag.channels)

        # Extract ID3 tags (TinyTag handles None gracefully)
        metadata.title = tag.title
        metadata.artist = tag.artist
        metadata.album = tag.album
        metadata.album_artist = tag.albumartist
        metadata.year = tag.year
        metadata.genre = tag.genre
        metadata.track_number = tag.track
        metadata.comment = tag.comment

        # Extract album art with MIME type detection
        album_art_data = tag.get_image()
        if album_art_data:
            metadata.has_album_art = True
            metadata.album_art_data = album_art_data
            metadata.album_art_size_bytes = len(album_art_data)

            # Detect MIME type from image bytes using imghdr
            image_type = imghdr.what(None, h=album_art_data)
            mime_map = {
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'webp': 'image/webp',
                'bmp': 'image/bmp'
            }
            metadata.album_art_mime = mime_map.get(image_type, 'image/jpeg')

            logger.debug(
                f"Extracted album art: {metadata.album_art_mime}, "
                f"{metadata.album_art_size_bytes / 1024:.1f} KB"
            )

        logger.info(
            f"Extracted metadata from {file_path_obj.name}: "
            f"title={metadata.title}, artist={metadata.artist}, "
            f"duration={metadata.duration_seconds:.1f}s, "
            f"album_art={metadata.has_album_art}"
        )

    except Exception as e:
        logger.error(f"Failed to extract metadata from {file_path}: {e}", exc_info=True)
        # Return partially populated metadata rather than failing

    return metadata
```

**Success Criteria**:
- [ ] Function signature unchanged
- [ ] Returns AudioMetadata instance
- [ ] Handles exceptions gracefully
- [ ] Logging preserved
- [ ] MIME type detection implemented

**Validation**:
```bash
# Syntax check
python -m py_compile src/processing/audio_metadata.py
echo $?  # Should be 0
```

---

#### ☐ Task 7: Remove obsolete helper functions
**Duration**: 3 min
**Risk**: LOW
**Rollback**: Git revert

**File**: `src/processing/audio_metadata.py:170-272`

```python
# DELETE these functions entirely:
def _extract_audio_properties(audio, metadata: AudioMetadata) -> None:
    # Lines 170-188

def _extract_id3_tags(audio, metadata: AudioMetadata) -> None:
    # Lines 190-230

def _extract_album_art(audio, metadata: AudioMetadata) -> None:
    # Lines 232-272
```

**Success Criteria**:
- [ ] Three helper functions removed
- [ ] No references to these functions remain
- [ ] File still compiles

---

#### ☐ Task 8: Update to_chromadb_metadata() method
**Duration**: 5 min
**Risk**: MEDIUM (affects ChromaDB storage)
**Rollback**: Git revert

**File**: `src/processing/audio_metadata.py:56-109`

```python
# REMOVE these sections from to_chromadb_metadata():

# Lines 78-79: Composer
if self.composer:
    metadata["audio_composer"] = self.composer

# Lines 85-86: Publisher
if self.publisher:
    metadata["audio_publisher"] = self.publisher

# Lines 97-99: Encoder
if self.encoder:
    metadata["audio_encoder"] = self.encoder
```

**Success Criteria**:
- [ ] Three field mappings removed
- [ ] All other mappings intact
- [ ] Method still returns dict

**Note**: Existing ChromaDB records will continue to work - these fields simply won't be populated for new records.

---

### Phase: Testing & Validation (30 min)

#### ☐ Task 9: Update unit test fixtures
**Duration**: 10 min
**Risk**: LOW
**Rollback**: Git revert

**File**: `src/processing/test_audio_metadata.py`

```python
# Update any test fixtures that expect composer/publisher/encoder
# Example:
expected_metadata = {
    'title': 'Test Track',
    'artist': 'Test Artist',
    # REMOVE: 'composer': 'Test Composer',
    # REMOVE: 'publisher': 'Test Publisher',
    # REMOVE: 'encoder': 'LAME',
}

# Add MIME type detection tests:
def test_album_art_mime_detection_jpeg():
    """Test MIME type detection for JPEG album art"""
    metadata = extract_audio_metadata('test_with_jpeg_art.mp3')
    assert metadata.has_album_art
    assert metadata.album_art_mime == 'image/jpeg'

def test_album_art_mime_detection_png():
    """Test MIME type detection for PNG album art"""
    metadata = extract_audio_metadata('test_with_png_art.mp3')
    assert metadata.has_album_art
    assert metadata.album_art_mime == 'image/png'
```

**Success Criteria**:
- [ ] No tests expect removed fields
- [ ] MIME detection tests added
- [ ] Test fixtures updated

---

#### ☐ Task 10: Run unit test suite
**Duration**: 5 min
**Risk**: HIGH (validation gate)
**Rollback**: Fix failures or revert to backup

```bash
# Run audio metadata tests specifically
pytest src/processing/test_audio_metadata.py -v --tb=short

# Check test coverage
pytest src/processing/test_audio_metadata.py --cov=src.processing.audio_metadata --cov-report=term-missing
```

**Success Criteria**:
- [ ] All tests pass
- [ ] No warnings about missing imports
- [ ] Coverage ≥ 80%

**If tests fail**:
1. Review error messages
2. Fix implementation issues
3. Rerun tests
4. If unfixable within 30 min, rollback: `cp src/processing/audio_metadata_mutagen.backup src/processing/audio_metadata.py`

---

#### ☐ Task 11: Manual testing with real audio files
**Duration**: 15 min
**Risk**: MEDIUM (catches edge cases)
**Rollback**: N/A (validation only)

```python
# Create a test script: test_tinytag_migration.py
from src.processing.audio_metadata import extract_audio_metadata
from pathlib import Path

test_cases = [
    ('data/uploads/test.mp3', 'MP3 with tags'),
    ('data/uploads/test.wav', 'WAV without tags'),
    ('data/uploads/podcast.mp3', 'Podcast with long comment'),
]

for file_path, description in test_cases:
    if not Path(file_path).exists():
        print(f"⚠️  Skip {description}: file not found")
        continue

    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"File: {file_path}")
    print('='*60)

    try:
        meta = extract_audio_metadata(file_path)

        print(f"✅ Extraction successful")
        print(f"   Title: {meta.title}")
        print(f"   Artist: {meta.artist}")
        print(f"   Duration: {meta.duration_seconds:.1f}s")
        print(f"   Bitrate: {meta.bitrate_kbps} kbps")
        print(f"   Sample Rate: {meta.sample_rate_hz} Hz")
        print(f"   Channels: {meta.channels}")
        print(f"   Album Art: {meta.has_album_art}")
        if meta.has_album_art:
            print(f"   MIME Type: {meta.album_art_mime}")
            print(f"   Size: {meta.album_art_size_bytes / 1024:.1f} KB")

    except Exception as e:
        print(f"❌ Extraction failed: {e}")

# Run it
python test_tinytag_migration.py
```

**Test cases to validate**:
- [ ] MP3 with ID3v2.4 tags
- [ ] MP3 with ID3v2.3 tags
- [ ] MP3 with JPEG album art
- [ ] MP3 with PNG album art
- [ ] WAV without tags (audio properties only)
- [ ] MP3 without album art
- [ ] Files with missing tags (title=None handled gracefully)

**Success Criteria**:
- [ ] All test cases extract without errors
- [ ] MIME types detected correctly (JPEG=image/jpeg, PNG=image/png)
- [ ] Missing tags handled gracefully (None values)

---

### Phase: Integration & Documentation (30 min)

#### ☐ Task 12: Run full processing test suite
**Duration**: 10 min
**Risk**: HIGH (validates integration)
**Rollback**: Full rollback if failures

```bash
# Run all processing tests
pytest src/processing/ -v

# Specifically check integration with:
# - docling_parser.py
# - processor.py
# - worker_webhook.py
```

**Success Criteria**:
- [ ] All processing tests pass
- [ ] No import errors
- [ ] No AudioMetadata attribute errors

---

#### ☐ Task 13: Update requirements.txt
**Duration**: 2 min
**Risk**: LOW
**Rollback**: Git revert

```bash
# Edit requirements.txt
# REMOVE:
mutagen>=1.47.0

# ADD:
tinytag>=1.10.1

# Verify syntax
pip check
```

**Success Criteria**:
- [ ] mutagen removed
- [ ] tinytag added
- [ ] No dependency conflicts

---

#### ☐ Task 14: Reinstall dependencies in clean environment
**Duration**: 5 min
**Risk**: MEDIUM (validates dependency changes)
**Rollback**: Restore old requirements.txt

```bash
# Remove old dependencies
pip uninstall mutagen -y

# Reinstall from requirements
./scripts/run-worker-native.sh setup

# Verify
pip show tinytag
pip show mutagen  # Should fail
```

**Success Criteria**:
- [ ] TinyTag installed
- [ ] mutagen NOT installed
- [ ] Worker setup completes successfully

---

#### ☐ Task 15: Update AUDIO_METADATA_SCHEMA.md
**Duration**: 5 min
**Risk**: LOW
**Rollback**: Git revert

**File**: `src/processing/AUDIO_METADATA_SCHEMA.md`

```markdown
# REMOVE sections documenting:
- composer field
- publisher field
- encoder field

# UPDATE library reference:
## Audio Metadata Extraction Library

**Library**: TinyTag (MIT License)
**Version**: 1.10.1
**Migration**: Replaced mutagen (GPLv2+) in October 2025 for license compliance

### MIME Type Detection

Album art MIME types are detected using Python's built-in `imghdr` module
by inspecting image byte headers, rather than relying on ID3 tag metadata.
This provides more reliable format detection.

### Removed Fields (v2.0)

The following fields were removed during the TinyTag migration:
- `composer` (TCOM ID3 tag) - Low usage (<5% of files)
- `publisher` (TPUB ID3 tag) - Low usage
- `encoder` (TSSE ID3 tag) - Rarely needed

Existing ChromaDB records may still contain these fields but they will not
be populated for new audio files processed after October 2025.
```

**Success Criteria**:
- [ ] Removed fields documented
- [ ] Library reference updated
- [ ] MIME detection method explained

---

#### ☐ Task 16: Update audio_metadata.py module docstring
**Duration**: 3 min
**Risk**: LOW
**Rollback**: Git revert

**File**: `src/processing/audio_metadata.py:1-8`

```python
"""
Audio metadata extraction using TinyTag.

Extracts ID3 tags, audio properties, and album art from MP3/WAV files.
Designed to work alongside Docling's ASR transcription pipeline.

MIME type detection uses Python's imghdr module for reliable format identification.

See AUDIO_METADATA_SCHEMA.md for complete metadata field documentation.

Migration: Replaced mutagen (GPLv2+) with TinyTag (MIT) in October 2025
for license compliance. See ADR-001 for details.
"""
```

**Success Criteria**:
- [ ] Docstring updated
- [ ] References TinyTag
- [ ] Migration noted
- [ ] ADR referenced

---

### Phase: Final Validation (15 min)

#### ☐ Task 17: End-to-end integration test
**Duration**: 10 min
**Risk**: CRITICAL (final validation)
**Rollback**: Full rollback if failures

```bash
# 1. Start the system
./scripts/start-all.sh

# 2. Verify worker health
./scripts/status.sh
# Expected: Worker status: running, healthy

# 3. Upload test MP3 via Copyparty
# Visit: http://localhost:8000
# Upload: test_with_jpeg_art.mp3

# 4. Monitor worker logs
tail -f logs/worker-native.log
# Expected: "Extracted metadata from test_with_jpeg_art.mp3"
# Expected: "Saved album art to: data/images/{doc_id}/cover.jpg"

# 5. Verify ChromaDB metadata
python -c "
from src.storage.chroma_client import ChromaClient
client = ChromaClient()
results = client.collection('text').query(query_texts=['test'], n_results=1)
print(results['metadatas'][0])  # Should contain audio_* fields
"

# 6. Test search for audio content
python -c "
from src.search.search_engine import SearchEngine
engine = SearchEngine()
results = engine.search('test music', mode='hybrid')
print(f'Found {len(results)} results')
for r in results[:3]:
    print(f'  - {r.doc_id}: {r.metadata.get(\"audio_title\")}')
"
```

**Success Criteria**:
- [ ] Worker starts successfully
- [ ] Audio file uploads without errors
- [ ] Metadata extracted and logged
- [ ] Album art saved with correct extension (.jpg or .png)
- [ ] ChromaDB contains audio_* metadata fields
- [ ] Search returns audio documents

**Critical Checks**:
- [ ] MIME type: `album_art_mime` correctly detected
- [ ] File extension: Album art saved as `.jpg` or `.png` (not always `.jpg`)
- [ ] No AttributeError for removed fields (composer, publisher, encoder)

---

#### ☐ Task 18: Review diff before commit
**Duration**: 5 min
**Risk**: LOW
**Rollback**: N/A (review only)

```bash
# Check changed files
git status

# Review changes
git diff --stat
git diff src/processing/audio_metadata.py
git diff requirements.txt

# Verify no unintended changes
git diff src/processing/docling_parser.py  # Should be empty
git diff src/processing/processor.py       # Should be empty
```

**Success Criteria**:
- [ ] Only expected files modified
- [ ] No debugging code left in
- [ ] No commented-out code blocks
- [ ] Import statements clean

---

### Phase: Commit & Deploy (15 min)

#### ☐ Task 19: Commit with comprehensive message
**Duration**: 5 min
**Risk**: LOW
**Rollback**: `git reset HEAD~1`

```bash
git add src/processing/audio_metadata.py \
        src/processing/test_audio_metadata.py \
        requirements.txt \
        src/processing/AUDIO_METADATA_SCHEMA.md

git commit -m "feat(audio): migrate from mutagen (GPL) to TinyTag (MIT) for license compliance

Replace mutagen with TinyTag to resolve HIGH-risk GPL license issue identified
in dependency audit (2025-10-16). Maintains all critical functionality while
enabling proprietary/commercial distribution.

Changes:
- Replace mutagen.File with TinyTag.get() for metadata extraction
- Implement MIME detection via imghdr for album art (more reliable than ID3 tags)
- Remove composer/publisher/encoder fields (low usage <5%)
- Update tests to validate MIME type detection
- Update documentation to reflect library change

Migration details:
- All audio properties preserved: duration, bitrate, sample rate, channels
- All core ID3 tags preserved: title, artist, album, year, genre, track, comment
- Album art extraction preserved with improved MIME detection
- Backward compatible: ChromaDB metadata format unchanged
- No breaking changes for downstream consumers (docling_parser, processor)

Breaking changes:
- AudioMetadata.composer removed (TCOM tag, classical music only)
- AudioMetadata.publisher removed (TPUB tag, audiobooks/podcasts)
- AudioMetadata.encoder removed (TSSE tag, rarely used)

Testing:
- All unit tests pass (src/processing/test_audio_metadata.py)
- All integration tests pass (src/processing/)
- End-to-end validation: upload → extract → search works
- MIME detection tested: JPEG (.jpg) and PNG (.png) formats

Resolves: HIGH-risk license compliance issue (mutagen GPLv2+)
Related: ADR-001 audio-metadata-library-decision.md
Related: dependency-audit-report.html (2025-10-16)

Timeline: Estimated 2-3 hours, actual: [FILL IN]
Risk: LOW (thoroughly tested, clear rollback path)
"
```

**Success Criteria**:
- [ ] Commit created
- [ ] Message is comprehensive
- [ ] All changed files included
- [ ] Commit hash noted for reference

---

#### ☐ Task 20: Update ADR status
**Duration**: 3 min
**Risk**: LOW
**Rollback**: Git revert

**File**: `.context-kit/_specs/audio-metadata-library-decision.md`

```markdown
# Near top of file, update:
**Status**: ACCEPTED (Implemented 2025-10-16)

# At bottom, add:
---

## Implementation Notes

**Implementation Date**: 2025-10-16
**Commit**: [INSERT COMMIT HASH]
**Implementation Time**: [INSERT ACTUAL TIME]
**Deviations from Plan**: [None / or list any]

### Post-Implementation Validation

- [x] All unit tests pass
- [x] All integration tests pass
- [x] End-to-end processing works
- [x] MIME detection ≥95% accurate (validated with JPEG/PNG)
- [x] Album art file extensions correct
- [x] No GPL dependencies remain

### Issues Encountered

[None / or list any issues and how they were resolved]

### Performance Notes

[Any observations about TinyTag performance vs mutagen]
```

**Success Criteria**:
- [ ] Status changed to ACCEPTED
- [ ] Implementation date recorded
- [ ] Commit hash linked

---

#### ☐ Task 21: Update dependency audit report
**Duration**: 5 min
**Risk**: LOW
**Rollback**: Git revert

**File**: `.context-kit/analysis/reports/2025-10-16/dependency-audit-report.html`

```html
<!-- Update the mutagen row in the license table -->
<tr style="background-color: #d4edda;">
    <td><strong>mutagen</strong></td>
    <td><del>1.47.0</del> REMOVED</td>
    <td><del>GPLv2+</del> Replaced with TinyTag (MIT)</td>
    <td><span class="badge badge-success">RESOLVED</span></td>
    <td><a href="https://github.com/quodlibet/mutagen" target="_blank">Link</a></td>
</tr>

<!-- Add TinyTag row -->
<tr>
    <td><strong>tinytag</strong></td>
    <td>1.10.1</td>
    <td>MIT ✅</td>
    <td><span class="badge badge-success">LOW</span></td>
    <td><a href="https://github.com/devsnd/tinytag" target="_blank">Link</a></td>
</tr>

<!-- Update summary card -->
<div class="card severity-low">
    <h3>Actual License Issues</h3>
    <div class="stat-value">4</div>
    <div class="stat-label">1 AGPL, 0 GPL, 3 LGPL/dev-only (mutagen resolved)</div>
</div>
```

**Success Criteria**:
- [ ] mutagen marked as RESOLVED
- [ ] TinyTag added as LOW risk
- [ ] License issue count updated: 5 → 4

---

#### ☐ Task 22: Monitor production logs (24 hours)
**Duration**: Passive monitoring
**Risk**: LOW
**Rollback**: Available if issues detected

```bash
# Check logs periodically
tail -f logs/worker-native.log | grep -i "audio\|metadata\|album"

# Monitor for errors
grep -i "error.*audio\|failed.*metadata" logs/worker-native.log

# Check MIME detection accuracy
grep "album_art_mime" logs/worker-native.log | sort | uniq -c
# Expected: Variety of MIME types (image/jpeg, image/png, etc.)
```

**Monitor for**:
- [ ] Extraction failures
- [ ] MIME type detection issues
- [ ] File extension problems
- [ ] Missing metadata fields

**If issues detected**:
1. Assess severity
2. If critical: rollback immediately
3. If minor: document and create follow-up task

---

## Completion Checklist

### Code Changes
- [ ] AudioMetadata dataclass updated (removed 3 fields)
- [ ] Imports replaced (mutagen → TinyTag + imghdr)
- [ ] extract_audio_metadata() rewritten
- [ ] Helper functions removed
- [ ] to_chromadb_metadata() updated
- [ ] requirements.txt updated

### Testing
- [ ] Unit tests updated and passing
- [ ] Integration tests passing
- [ ] End-to-end validation complete
- [ ] Manual testing with multiple formats

### Documentation
- [ ] AUDIO_METADATA_SCHEMA.md updated
- [ ] audio_metadata.py docstring updated
- [ ] ADR-001 status updated to ACCEPTED
- [ ] Dependency audit report updated

### Deployment
- [ ] Changes committed with comprehensive message
- [ ] Dependencies reinstalled cleanly
- [ ] Worker running and healthy
- [ ] Production monitoring active

---

## Rollback Procedures

### Emergency Rollback (during implementation)

```bash
# Restore backup
cp src/processing/audio_metadata_mutagen.backup src/processing/audio_metadata.py

# Restore requirements
git checkout requirements.txt

# Reinstall mutagen
pip install mutagen>=1.47.0
pip uninstall tinytag -y

# Restart worker
./scripts/stop-all.sh
./scripts/start-all.sh

# Verify
pytest src/processing/test_audio_metadata.py
./scripts/status.sh
```

### Post-Commit Rollback

```bash
# Revert commit
git revert HEAD

# Or hard reset (if not pushed)
git reset --hard HEAD~1

# Follow emergency rollback procedure above
```

---

## Success Metrics

**Implementation Success**:
- [ ] All 22 tasks completed
- [ ] Zero test failures
- [ ] Zero production errors in first 24 hours
- [ ] MIME detection accuracy ≥95%

**License Compliance Success**:
- [ ] mutagen removed from all environments
- [ ] No GPL dependencies in `pip freeze`
- [ ] Dependency audit shows 4 issues (down from 5)

**Functional Success**:
- [ ] Audio files process without errors
- [ ] Album art saved with correct extensions
- [ ] Search returns audio documents
- [ ] Metadata displayed correctly in UI (if applicable)

---

## Post-Implementation Tasks

After successful deployment:

1. **Remove backup file**:
   ```bash
   rm src/processing/audio_metadata_mutagen.backup
   ```

2. **Update CHANGELOG.md** (if exists):
   ```markdown
   ## [2.1.0] - 2025-10-16

   ### Changed
   - Migrated from mutagen (GPLv2+) to TinyTag (MIT) for license compliance
   - MIME type detection now uses imghdr (more reliable)

   ### Removed
   - AudioMetadata.composer field (low usage)
   - AudioMetadata.publisher field (low usage)
   - AudioMetadata.encoder field (low usage)
   ```

3. **Add CI/CD license check** (future):
   ```bash
   # Prevent GPL dependencies from being added
   pip-licenses | grep -E "GPL|AGPL" && exit 1 || exit 0
   ```

4. **Document in team communication**:
   - Announce completion in team chat
   - Note any breaking changes (composer/publisher/encoder removed)
   - Share performance observations

---

## Reference Links

- **ADR**: `.context-kit/_specs/audio-metadata-library-decision.md`
- **Dependency Audit**: `.context-kit/analysis/reports/2025-10-16/dependency-audit-report.html`
- **TinyTag Docs**: https://github.com/devsnd/tinytag
- **imghdr Docs**: https://docs.python.org/3/library/imghdr.html

---

**Plan Status**: READY TO EXECUTE
**Last Updated**: 2025-10-16
**Estimated Duration**: 2-3 hours
**Actual Duration**: [TO BE FILLED]

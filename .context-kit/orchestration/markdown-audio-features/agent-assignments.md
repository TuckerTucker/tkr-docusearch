# Agent Assignments & Territorial Boundaries

**Orchestration**: markdown-audio-features
**Created**: 2025-10-11
**Total Agents**: 6
**Execution Model**: Wave-based parallel execution with zero-conflict territorial ownership

## Overview

This document defines the territorial boundaries and responsibilities for each agent. **Territorial ownership** is the key to conflict-free parallel development:

- Each agent owns **specific files or sections** of files
- **No overlapping territories** between agents
- **Clear handoff specifications** at integration points
- **New files preferred** over modifying shared files

## Agent Registry

| Agent | Territory | Wave | Dependencies | Status |
|-------|-----------|------|--------------|--------|
| compression-agent | `src/storage/compression.py` | 1 | None | Pending |
| config-asr-agent | `src/config/processing_config.py` | 1 | None | Pending |
| parser-markdown-agent | `src/processing/docling_parser.py` (lines 488-510) | 2 | compression-agent | Pending |
| parser-asr-agent | `src/processing/docling_parser.py` (lines 1-30, 455-480, 492-510) | 2 | config-asr-agent | Pending |
| storage-markdown-agent | `src/storage/chroma_client.py` | 3 | compression-agent, parser-markdown-agent | Pending |
| testing-integration-agent | `src/processing/test_*.py` | 3-4 | All agents | Pending |

---

## Agent 1: compression-agent

### Territory
**Owned Files**:
- `src/storage/compression.py` (full file ownership)

**Allowed to modify**:
- This file only (no other files)

**Not allowed to modify**:
- Any other files in the codebase

### Responsibilities

#### Primary Deliverables:
1. **compress_markdown() function**
   - Input: markdown text (string)
   - Output: base64-encoded gzip-compressed string
   - Max input size: 10MB
   - Performance: <100ms for 1MB

2. **decompress_markdown() function**
   - Input: compressed base64 string
   - Output: original markdown text
   - Round-trip guarantee: `original == decompress(compress(original))`
   - Error detection: CRC validation

3. **Exception classes**
   - `CompressionError` (base)
   - `MarkdownTooLargeError`
   - `CorruptedDataError`

4. **Unit tests**
   - Round-trip tests (1KB, 100KB, 1MB)
   - Error handling tests
   - Unicode/emoji tests
   - Performance benchmarks

#### Integration Interface:
```python
# Other agents will import like this:
from src.storage.compression import compress_markdown, decompress_markdown

# Usage:
compressed = compress_markdown(markdown_text)
original = decompress_markdown(compressed)
```

### Dependencies
- **None** (uses only Python standard library)

### Handoff Specifications
**Consumers**:
- `parser-markdown-agent`: Will use compress_markdown() indirectly (via storage)
- `storage-markdown-agent`: Will call compress_markdown() and decompress_markdown()

**Interface Contract**: See `integration-contracts/01-compression-interface.md`

### Validation Checklist
- [ ] compress_markdown() implemented and tested
- [ ] decompress_markdown() implemented and tested
- [ ] Exception classes defined
- [ ] Round-trip tests pass (100% success)
- [ ] Performance benchmarks meet targets (<100ms for 1MB)
- [ ] Code reviewed by storage-markdown-agent

### Effort Estimate
**Time**: 2-3 hours
**Complexity**: Low (standard compression, well-defined interface)

---

## Agent 2: config-asr-agent

### Territory
**Owned Files**:
- `src/config/processing_config.py` (AsrConfig class only)

**Allowed to modify**:
- Add new AsrConfig dataclass to existing file
- Do not modify existing classes (EnhancedModeConfig, etc.)

**Not allowed to modify**:
- Existing configuration classes
- Any other files

### Responsibilities

#### Primary Deliverables:
1. **AsrConfig dataclass**
   - Fields: enabled, model, language, device, word_timestamps, temperature, max_time_chunk
   - Validation in __post_init__()
   - Type hints on all fields
   - Documentation for each field

2. **from_env() class method**
   - Load configuration from environment variables
   - Graceful handling of missing variables (use defaults)
   - Boolean parsing (true/false, case-insensitive)
   - Numeric parsing with error handling

3. **to_docling_model_spec() method**
   - Convert AsrConfig → InlineAsrNativeWhisperOptions
   - Correct model name mapping
   - Language code handling

4. **Unit tests**
   - Default values test
   - Environment variable loading test
   - Validation rejection tests
   - Conversion to Docling spec test

#### Integration Interface:
```python
# Other agents will import like this:
from src.config.processing_config import AsrConfig

# Usage:
asr_config = AsrConfig.from_env()
docling_spec = asr_config.to_docling_model_spec()
```

### Dependencies
- **None** (Docling import only in to_docling_model_spec(), lazy loaded)

### Handoff Specifications
**Consumers**:
- `parser-asr-agent`: Will instantiate AsrConfig and use to_docling_model_spec()

**Interface Contract**: See `integration-contracts/04-asr-config-interface.md`

### Validation Checklist
- [ ] AsrConfig dataclass defined
- [ ] All fields have correct types and defaults
- [ ] Validation rejects invalid values
- [ ] from_env() loads from environment
- [ ] to_docling_model_spec() returns correct type
- [ ] All unit tests pass
- [ ] Code reviewed by parser-asr-agent

### Effort Estimate
**Time**: 2-3 hours
**Complexity**: Low (configuration dataclass, well-defined interface)

---

## Agent 3: parser-markdown-agent

### Territory
**Owned Lines**:
- `src/processing/docling_parser.py`
  - Lines 488-510 (metadata extraction section)
  - Add new try/except block for markdown extraction

**Coordination Required**:
- Must coordinate with parser-asr-agent (different sections of same file)
- Edit lines 488-510 first (before parser-asr-agent edits 455-480)

**Not allowed to modify**:
- Lines 1-487 (import section, class definition, other methods)
- Lines 511+ (rest of file)
- Any ASR-related code

### Responsibilities

#### Primary Deliverables:
1. **Markdown extraction**
   - Call `doc.export_to_markdown()` after line 488
   - Try/except with non-blocking error handling
   - Add 4 metadata fields: full_markdown, markdown_length, markdown_extracted, markdown_error
   - Logging for successful extraction and failures

2. **Error handling**
   - Extraction failures must not block document processing
   - Log warnings (not errors) for extraction failures
   - Set markdown_extracted = False on failure
   - Store error message in markdown_error field

3. **Unit tests**
   - PDF markdown extraction test
   - DOCX markdown extraction test
   - Image-only document test (empty markdown)
   - Extraction failure handling test

#### Integration Interface:
```python
# Metadata output format:
metadata = {
    # ... existing fields ...
    "full_markdown": str,  # Actual markdown text
    "markdown_length": int,  # Character count
    "markdown_extracted": bool,  # Success/failure flag
    "markdown_error": Optional[str]  # Error message if failed
}
```

### Dependencies
- **None** for implementation
- **compression-agent** for integration tests (optional)

### Handoff Specifications
**Consumers**:
- `storage-markdown-agent`: Will receive metadata dict with markdown fields
- `processor.py`: Will pass metadata through unchanged (no modifications needed)

**Interface Contract**: See `integration-contracts/02-parser-markdown-interface.md`

### Coordination Protocol
**With parser-asr-agent**:
1. parser-markdown-agent edits lines 488-510 first
2. Commit changes to version control
3. parser-asr-agent pulls changes
4. parser-asr-agent edits lines 455-480 and 492-510 (audio metadata)
5. No direct conflicts (different line ranges)

### Validation Checklist
- [ ] Markdown extraction added after Docling parse
- [ ] All 4 metadata fields present
- [ ] Error handling is non-blocking
- [ ] Empty documents handled correctly
- [ ] Logging added
- [ ] Unit tests pass
- [ ] No breaking changes to existing functionality
- [ ] Code reviewed by storage-markdown-agent

### Effort Estimate
**Time**: 2-3 hours
**Complexity**: Low (simple extraction with error handling)

---

## Agent 4: parser-asr-agent

### Territory
**Owned Lines**:
- `src/processing/docling_parser.py`
  - Lines 1-30 (imports section - add ASR imports)
  - Lines 455-480 (format_options section - add ASR config)
  - Lines 492-510 (metadata section - add audio metadata)

**Coordination Required**:
- Must coordinate with parser-markdown-agent (different sections of same file)
- Wait for parser-markdown-agent to commit before editing lines 492-510

**Not allowed to modify**:
- Lines 488-491 (markdown extraction - owned by parser-markdown-agent)
- Any markdown-related code

### Responsibilities

#### Primary Deliverables:
1. **ASR imports**
   - Add imports at top of file (lines 14-20)
   - Import ASR components from Docling
   - Import AsrConfig from config module
   - Graceful import error handling

2. **ASR pipeline configuration**
   - Detect .mp3 and .wav extensions
   - Load AsrConfig from environment
   - Create AsrPipelineOptions
   - Add AudioFormatOption to format_options dict
   - Error handling for ASR config failures

3. **Audio metadata extraction**
   - Add ASR-specific fields: transcript_method, asr_model_used, asr_language, audio_format
   - Extract audio duration if available
   - Extract timestamp information if available
   - Add has_word_timestamps flag

4. **Unit tests**
   - MP3 processing test
   - WAV processing test
   - ASR disabled test (fallback)
   - ASR config failure test (graceful degradation)
   - Metadata validation test

#### Integration Interface:
```python
# Additional metadata fields for audio:
audio_metadata = {
    "transcript_method": "whisper",
    "asr_model_used": str,  # "turbo", "base", etc.
    "asr_language": str,  # "en", "auto", etc.
    "audio_format": str,  # "mp3" or "wav"
    "audio_duration_seconds": Optional[float],
    "has_word_timestamps": bool
}
```

### Dependencies
- **config-asr-agent** (AsrConfig class must be implemented first)
- **System**: ffmpeg must be installed for MP3 processing
- **Python**: docling[asr] dependencies must be installed

### Handoff Specifications
**Consumers**:
- `processor.py`: Will receive pages and metadata (no changes needed)
- `storage-markdown-agent`: Will store audio metadata unchanged

**Interface Contract**: See `integration-contracts/05-parser-asr-interface.md`

### Coordination Protocol
**With parser-markdown-agent**:
1. Wait for parser-markdown-agent to commit markdown extraction
2. Pull latest changes
3. Edit lines 1-30 (imports) - no conflicts
4. Edit lines 455-480 (ASR config) - no conflicts
5. Edit lines 492-510 (audio metadata) - may have merge with markdown fields
6. Resolve merge: both sets of metadata should coexist

### Validation Checklist
- [ ] ASR imports added
- [ ] AsrConfig loading added
- [ ] ASR pipeline configuration works for MP3
- [ ] ASR pipeline configuration works for WAV
- [ ] Audio metadata fields added
- [ ] Error handling for ASR failures
- [ ] VTT files unchanged
- [ ] Non-audio files unaffected
- [ ] Unit tests pass
- [ ] Performance logged
- [ ] Code reviewed by config-asr-agent

### Effort Estimate
**Time**: 3-4 hours
**Complexity**: Medium (integration with Docling ASR, coordination required)

---

## Agent 5: storage-markdown-agent

### Territory
**Owned Files**:
- `src/storage/chroma_client.py`
  - Modify: add_visual_embedding() method (add compression logic)
  - Modify: add_text_embedding() method (add compression logic)
  - Add: get_document_markdown() method (new)

**Allowed to modify**:
- Only the methods specified above
- Add imports for compression functions

**Not allowed to modify**:
- Other ChromaClient methods (search, delete, etc.)
- Collection initialization
- Other storage modules

### Responsibilities

#### Primary Deliverables:
1. **Compression logic in add_visual_embedding()**
   - Check if metadata contains "full_markdown"
   - If markdown >1KB: compress and replace
   - Add compression flag to metadata
   - Store compressed version

2. **Compression logic in add_text_embedding()**
   - Same logic as add_visual_embedding()

3. **get_document_markdown() method**
   - Query any embedding by doc_id
   - Handle missing markdown gracefully (return None)
   - Decompress if compressed
   - Return original markdown text

4. **Unit tests**
   - Store small markdown (no compression) test
   - Store large markdown (with compression) test
   - Retrieve compressed markdown test
   - Retrieve uncompressed markdown test
   - Missing markdown returns None test
   - Corrupted data raises error test

#### Integration Interface:
```python
# Metadata changes:
# Input (from parser):
metadata = {"full_markdown": str, ...}

# Output (stored in ChromaDB):
metadata = {
    "full_markdown_compressed": str,  # If >1KB
    "markdown_compression": "gzip+base64",  # Or "none"
    ...
}

# Retrieval:
markdown = client.get_document_markdown(doc_id)
```

### Dependencies
- **compression-agent** (compress/decompress functions)
- **parser-markdown-agent** (metadata format with full_markdown field)

### Handoff Specifications
**Providers**:
- `compression-agent`: Provides compress_markdown() and decompress_markdown()
- `parser-markdown-agent`: Provides metadata with full_markdown field

**Consumers**:
- `search-agent` (future): Will call get_document_markdown() for search results

**Interface Contract**: See `integration-contracts/03-storage-markdown-interface.md`

### Validation Checklist
- [ ] Compression logic added to add_visual_embedding()
- [ ] Compression logic added to add_text_embedding()
- [ ] get_document_markdown() method implemented
- [ ] Compression threshold (1KB) works correctly
- [ ] All metadata fields correctly set
- [ ] Error handling for missing/corrupted markdown
- [ ] Backward compatibility maintained
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Code reviewed by compression-agent and parser-markdown-agent

### Effort Estimate
**Time**: 3-4 hours
**Complexity**: Medium (integration with compression, multiple method modifications)

---

## Agent 6: testing-integration-agent

### Territory
**Owned Files**:
- `src/processing/test_markdown_storage.py` (new file, full ownership)
- `src/processing/test_audio_processing.py` (new file, full ownership)
- Test data files in `data/test-documents/` (if needed)

**Allowed to modify**:
- Only the test files above
- Can add test data files

**Not allowed to modify**:
- Any production code
- Existing test files (unless adding to them)

### Responsibilities

#### Primary Deliverables:
1. **test_markdown_storage.py**
   - Test compress_markdown() and decompress_markdown()
   - Test round-trip compression with various sizes
   - Test markdown extraction in parser
   - Test markdown storage in ChromaDB
   - Test markdown retrieval via get_document_markdown()
   - Test with real PDF documents
   - Test error handling

2. **test_audio_processing.py**
   - Test MP3 file processing
   - Test WAV file processing
   - Test transcript quality (basic checks)
   - Test metadata includes ASR fields
   - Test no visual embeddings created for audio
   - Test text embeddings created for audio
   - Test search works with audio content
   - Test performance benchmarks

3. **Integration test scenarios**
   - End-to-end: PDF → markdown → storage → retrieval
   - End-to-end: MP3 → transcript → embeddings → search
   - End-to-end: WAV → transcript → embeddings → search
   - Cross-feature: Audio file with markdown extraction (should work)

4. **Test documentation**
   - Document test scenarios and expected results
   - Document test data requirements
   - Document how to run tests
   - Document known limitations

#### Integration Interface:
```python
# Test files can import from any agent's territory:
from src.storage.compression import compress_markdown
from src.config.processing_config import AsrConfig
from src.processing.docling_parser import DoclingParser
from src.storage.chroma_client import ChromaClient
```

### Dependencies
- **All agents** (tests everything)

### Handoff Specifications
**Validates**:
- compression-agent (compression functions)
- config-asr-agent (ASR configuration)
- parser-markdown-agent (markdown extraction)
- parser-asr-agent (audio processing)
- storage-markdown-agent (markdown storage/retrieval)

**No consumers** (tests are endpoints)

### Validation Checklist
- [ ] test_markdown_storage.py created with comprehensive tests
- [ ] test_audio_processing.py created with comprehensive tests
- [ ] All tests pass
- [ ] Integration tests cover end-to-end scenarios
- [ ] Performance benchmarks included
- [ ] Test documentation complete
- [ ] Test data prepared (if needed)
- [ ] Cross-agent integration validated

### Effort Estimate
**Time**: 3-4 hours (Wave 3) + 2-3 hours (Wave 4 integration)
**Complexity**: Medium (requires understanding of all components)

---

## Territorial Conflict Resolution

### Prevention
- **Clear boundaries**: Each agent knows exactly what they can modify
- **Coordination protocol**: Agents working on same file have explicit ordering
- **Handoff specifications**: Clear interface contracts between agents
- **Version control**: All agents use feature branches, merge to main after validation

### Resolution Process

If territorial conflict occurs:
1. **Identify conflict**: Which agents, which files, which lines?
2. **Review boundaries**: Did someone violate territory?
3. **Coordinate resolution**:
   - Agent with earlier wave number has priority
   - Agent with critical path has priority (if same wave)
   - Last resort: Orchestrator decides
4. **Update plan**: Clarify boundaries to prevent recurrence

### Example Conflict

**Scenario**: parser-markdown-agent and parser-asr-agent both edit line 495

**Resolution**:
1. Check coordination protocol (see agent assignments above)
2. parser-markdown-agent commits first (per protocol)
3. parser-asr-agent pulls and merges
4. If merge conflict: parser-asr-agent resolves (later in sequence)
5. Result: Both sets of metadata coexist in metadata dict

---

## Status Tracking

Each agent must update their status file after completing tasks:

**Location**: `.context-kit/orchestration/markdown-audio-features/status/{agent-name}-status.json`

**Format**:
```json
{
  "agent": "agent-name",
  "wave": 1,
  "status": "completed",
  "timestamp": "2025-10-11T10:30:00Z",
  "deliverables": [
    {"file": "path/to/file.py", "status": "completed", "tests_passing": true}
  ],
  "blockers": [],
  "notes": "All tests passing, ready for integration"
}
```

---

## Handoff Summary

### Wave 1 Handoffs
- **compression-agent → storage-markdown-agent**: compress/decompress functions
- **config-asr-agent → parser-asr-agent**: AsrConfig class

### Wave 2 Handoffs
- **parser-markdown-agent → storage-markdown-agent**: Metadata format with markdown
- **parser-asr-agent → processor.py**: Pages and metadata (no changes needed in processor)

### Wave 3 Handoffs
- **storage-markdown-agent → testing-integration-agent**: Storage methods for testing
- **All agents → testing-integration-agent**: Components for integration tests

### Wave 4 Handoffs
- **testing-integration-agent → All agents**: Test results and code review feedback
- **All agents → Deployment**: Validated, tested, ready-to-deploy code

---

*Generated as part of markdown-audio-features orchestration plan on 2025-10-11*

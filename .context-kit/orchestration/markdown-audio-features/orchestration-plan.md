# Orchestration Plan: Markdown Storage + Audio Processing

**Created**: 2025-10-11
**Features**: Full markdown storage in ChromaDB + MP3/WAV audio processing with Whisper ASR
**Max Agents**: 6 (configured for maximum parallelism)
**Execution Model**: Wave-based with synchronization gates

## Executive Summary

This orchestration implements two independent features that extend the document processing pipeline:

1. **Markdown Storage**: Extract full Docling markdown and store in ChromaDB metadata with compression
2. **Audio Processing**: Transcribe MP3/WAV files using Whisper ASR for searchable audio content

**Key Architectural Principles**:
- **Territorial Ownership**: Each agent owns specific files (zero overlap)
- **Interface-First**: Contracts defined before implementation
- **Progressive Validation**: Quality gates after each wave
- **Maximum Parallelism**: Independent work happens simultaneously

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Feature 1: Markdown Storage             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Compression Agent  →  Parser Agent  →  Storage Client     │
│   (compression.py)     (docling_parser)   (chroma_client)  │
│          ↓                    ↓                  ↓          │
│    compress/decompress    extract markdown    store/retrieve│
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  Feature 2: Audio Processing                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Config Agent  →  Parser Agent  →  Existing Pipeline      │
│  (AsrConfig)      (ASR integration)   (processor.py)        │
│       ↓                  ↓                   ↓              │
│  ASR settings    Whisper transcription  text embeddings    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Agent Assignments & Territorial Boundaries

### Agent 1: compression-agent
**Territory**: `src/storage/compression.py`
**Responsibilities**:
- Implement `compress_markdown()` function
- Implement `decompress_markdown()` function
- Add exception classes for compression errors
- Implement round-trip validation
**Deliverables**:
- Working compression functions
- Unit tests for compression/decompression
- Performance benchmarks
**Dependencies**: None (pure Python, standard library)
**Estimated Effort**: 2-3 hours

### Agent 2: parser-markdown-agent
**Territory**: `src/processing/docling_parser.py` (markdown extraction only)
**Responsibilities**:
- Extract markdown in `_parse_with_docling()` method
- Add markdown metadata fields (full_markdown, markdown_length, etc.)
- Error handling for extraction failures
- Logging for markdown extraction
**Deliverables**:
- Modified `_parse_with_docling()` with markdown extraction
- Unit tests for markdown extraction
- Tests for error handling
**Dependencies**:
- None for implementation
- compression-agent for integration tests
**Estimated Effort**: 2-3 hours

### Agent 3: storage-markdown-agent
**Territory**: `src/storage/chroma_client.py` (markdown handling only)
**Responsibilities**:
- Add markdown compression logic to `add_visual_embedding()`
- Add markdown compression logic to `add_text_embedding()`
- Implement `get_document_markdown()` retrieval method
- Handle compression thresholds and flags
**Deliverables**:
- Modified storage methods with compression
- New retrieval method
- Unit tests for storage/retrieval
- Integration tests with compression
**Dependencies**:
- compression-agent (compress/decompress functions)
- parser-markdown-agent (markdown metadata format)
**Estimated Effort**: 3-4 hours

### Agent 4: config-asr-agent
**Territory**: `src/config/processing_config.py` (AsrConfig only)
**Responsibilities**:
- Implement `AsrConfig` dataclass
- Add field validation
- Implement `from_env()` for environment variables
- Implement `to_docling_model_spec()` conversion
**Deliverables**:
- Working AsrConfig class
- Unit tests for validation
- Unit tests for environment loading
- Documentation for configuration options
**Dependencies**: None (Docling import is lazy)
**Estimated Effort**: 2-3 hours

### Agent 5: parser-asr-agent
**Territory**: `src/processing/docling_parser.py` (ASR integration only)
**Responsibilities**:
- Add ASR imports
- Add ASR pipeline configuration for MP3/WAV
- Add audio-specific metadata extraction
- Error handling for ASR failures
- Performance logging
**Deliverables**:
- Modified `_parse_with_docling()` with ASR support
- Unit tests for MP3/WAV processing
- Integration tests for audio pipeline
- Performance benchmarks
**Dependencies**:
- config-asr-agent (AsrConfig class)
- System: ffmpeg installed
**Estimated Effort**: 3-4 hours

### Agent 6: testing-integration-agent
**Territory**: `src/processing/test_markdown_storage.py`, `src/processing/test_audio_processing.py`
**Responsibilities**:
- Create comprehensive markdown storage tests
- Create comprehensive audio processing tests
- Create end-to-end integration tests
- Document test scenarios and expected results
**Deliverables**:
- `test_markdown_storage.py` test suite
- `test_audio_processing.py` test suite
- Test documentation
- Test data samples (if needed)
**Dependencies**:
- All agents (tests everything)
**Estimated Effort**: 3-4 hours

## Wave-Based Execution Plan

### Wave 0: Prerequisites & Environment Check

**Duration**: 15-30 minutes
**Agents**: Manual (developer) or automation script
**Parallel**: N/A

**Tasks**:
1. Verify ffmpeg installed: `ffmpeg -version`
2. Verify docling[asr] installed: `python -c "import docling; from docling.pipeline import asr_pipeline"`
3. Create orchestration directory structure
4. Review integration contracts

**Validation Gate**:
- [ ] ffmpeg available
- [ ] docling[asr] dependencies present
- [ ] All integration contracts reviewed
- [ ] Development environment ready

**Proceed if**: All checks pass
**Block if**: Missing dependencies (install before proceeding)

---

### Wave 1: Foundation Layer (Compression + Config)

**Duration**: 2-3 hours
**Agents**: compression-agent, config-asr-agent
**Parallel**: YES (fully independent)

#### compression-agent
**Tasks**:
1. Implement `compress_markdown()` with gzip + base64
2. Implement `decompress_markdown()` with validation
3. Add exception classes (`CompressionError`, `MarkdownTooLargeError`, `CorruptedDataError`)
4. Write unit tests for round-trip compression
5. Write unit tests for error cases
6. Benchmark compression performance

**Deliverables**:
- `src/storage/compression.py` updated
- All tests passing
- Performance: <100ms for 1MB markdown

#### config-asr-agent (parallel)
**Tasks**:
1. Define `AsrConfig` dataclass in `processing_config.py`
2. Implement field validation in `__post_init__()`
3. Implement `from_env()` with environment variable loading
4. Implement `to_docling_model_spec()` conversion
5. Write unit tests for validation
6. Write unit tests for environment loading
7. Document configuration options

**Deliverables**:
- `src/config/processing_config.py` updated with AsrConfig
- All tests passing
- Configuration documented

**Validation Gate**:
- [ ] compress_markdown() works correctly
- [ ] decompress_markdown() works correctly
- [ ] Round-trip tests pass (original == decompressed)
- [ ] AsrConfig validates all fields
- [ ] AsrConfig loads from environment
- [ ] AsrConfig converts to Docling spec
- [ ] All Wave 1 tests pass

**Proceed if**: Both agents complete successfully
**Block if**: Compression or config validation fails

---

### Wave 2: Parser Layer (Markdown + ASR Integration)

**Duration**: 3-4 hours
**Agents**: parser-markdown-agent, parser-asr-agent
**Parallel**: YES (different parts of same file, careful coordination)

#### parser-markdown-agent
**Territory**: Lines 488-510 in `docling_parser.py` (markdown extraction)
**Tasks**:
1. Add markdown extraction after Docling parse
2. Add try/except with non-blocking error handling
3. Add 4 metadata fields (full_markdown, markdown_length, markdown_extracted, markdown_error)
4. Add logging for extraction
5. Write unit tests for PDF markdown extraction
6. Write unit tests for error handling

**Deliverables**:
- Markdown extraction in `_parse_with_docling()`
- Metadata includes markdown fields
- Tests passing

#### parser-asr-agent (parallel)
**Territory**: Lines 455-480 in `docling_parser.py` (ASR config) + lines 492-510 (audio metadata)
**Tasks**:
1. Add ASR imports at top of file
2. Add ASR pipeline configuration for MP3/WAV (before converter creation)
3. Add audio-specific metadata extraction (after metadata dict creation)
4. Add error handling for ASR failures
5. Add performance logging
6. Write unit tests for MP3 processing
7. Write unit tests for WAV processing

**Deliverables**:
- ASR configuration in `_parse_with_docling()`
- Audio metadata fields
- Tests passing

**Coordination Protocol**:
- parser-markdown-agent: Edit lines 488-510 first
- parser-asr-agent: Edit lines 455-480 and 492-510 (different line ranges)
- No direct conflicts (different sections of file)
- Final merge: parser-asr-agent waits for parser-markdown-agent commit

**Validation Gate**:
- [ ] Markdown extraction works for PDFs
- [ ] Markdown metadata present in parser output
- [ ] Markdown extraction failures are non-blocking
- [ ] ASR configuration works for MP3 files
- [ ] ASR configuration works for WAV files
- [ ] Audio metadata includes ASR fields
- [ ] Non-audio files unaffected
- [ ] All Wave 2 tests pass

**Proceed if**: Both parser agents complete and no conflicts
**Block if**: Parser tests fail or merge conflicts occur

---

### Wave 3: Storage Layer + Validation

**Duration**: 3-4 hours
**Agents**: storage-markdown-agent, testing-integration-agent
**Parallel**: YES (storage implementation + test preparation)

#### storage-markdown-agent
**Tasks**:
1. Add compression logic to `add_visual_embedding()`
2. Add compression logic to `add_text_embedding()`
3. Implement `get_document_markdown()` retrieval method
4. Add compression threshold handling (1KB)
5. Add metadata flags (markdown_compression)
6. Write unit tests for compression in storage
7. Write unit tests for retrieval

**Deliverables**:
- Modified storage methods
- New retrieval method
- All tests passing

#### testing-integration-agent (parallel)
**Tasks**:
1. Create `test_markdown_storage.py`:
   - Test compression/decompression
   - Test storage/retrieval
   - Test with various document sizes
2. Create `test_audio_processing.py`:
   - Test MP3 processing
   - Test WAV processing
   - Test metadata validation
   - Test no visual embeddings for audio
3. Prepare test data samples
4. Document test scenarios

**Deliverables**:
- Two new test files
- Test documentation
- Test data (if needed)

**Validation Gate**:
- [ ] Markdown compressed before storage (>1KB)
- [ ] Markdown stored uncompressed (<1KB)
- [ ] get_document_markdown() retrieves correctly
- [ ] Compressed markdown decompresses correctly
- [ ] test_markdown_storage.py all tests pass
- [ ] test_audio_processing.py all tests pass
- [ ] All Wave 3 tests pass

**Proceed if**: Storage works and tests are comprehensive
**Block if**: Storage tests fail or retrieval doesn't work

---

### Wave 4: End-to-End Integration & Validation

**Duration**: 2-3 hours
**Agents**: testing-integration-agent (lead), all agents (support)
**Parallel**: NO (coordinated validation)

**Tasks**:
1. Run full integration test: PDF with markdown
2. Run full integration test: MP3 with transcription
3. Run full integration test: WAV with transcription
4. Verify markdown searchable via existing search
5. Verify audio transcript searchable
6. Performance validation:
   - Markdown extraction: <100ms
   - Markdown compression: <100ms
   - MP3 transcription: <5s for 10s audio (MPS)
7. Cross-agent code review:
   - compression-agent reviews storage-markdown-agent usage
   - config-asr-agent reviews parser-asr-agent usage
   - parser-markdown-agent reviews storage-markdown-agent usage

**Deliverables**:
- All integration tests passing
- Performance benchmarks documented
- Code review feedback addressed

**Validation Gate**:
- [ ] PDF → markdown stored → markdown retrieved → matches original
- [ ] MP3 → transcript → text embeddings → searchable
- [ ] WAV → transcript → text embeddings → searchable
- [ ] No visual embeddings for audio files
- [ ] Performance targets met
- [ ] No regressions in existing features
- [ ] All agents approve integration

**Proceed if**: All integration tests pass and performance is acceptable
**Block if**: Integration fails or performance below targets

---

### Wave 5: Documentation & Deployment

**Duration**: 1-2 hours
**Agents**: documentation-agent (or manual)
**Parallel**: N/A

**Tasks**:
1. Update `README.md`:
   - Add MP3/WAV to supported formats
   - Document ffmpeg requirement
   - Add ASR configuration options
2. Update `docs/QUICK_START.md`:
   - Add audio upload example
   - Document expected processing times
3. Create `docs/AUDIO_PROCESSING.md`:
   - Whisper model comparison
   - Performance benchmarks
   - Language support
   - Troubleshooting guide
4. Update `.env.example` with ASR variables
5. Update `CHANGELOG.md` with new features

**Deliverables**:
- All documentation updated
- Examples working
- Deployment guide ready

**Validation Gate**:
- [ ] README includes audio formats
- [ ] QUICK_START has audio examples
- [ ] AUDIO_PROCESSING.md complete
- [ ] .env.example includes ASR variables
- [ ] CHANGELOG updated
- [ ] Documentation reviewed

**Proceed if**: Documentation complete and reviewed
**Deploy if**: All validation gates passed

---

## Synchronization Protocol

### Status Broadcasting

Each agent must update status in shared location:
`.context-kit/orchestration/markdown-audio-features/status/`

**Status file format** (`{agent-name}-status.json`):
```json
{
  "agent": "compression-agent",
  "wave": 1,
  "status": "completed",  // pending, in_progress, completed, failed
  "timestamp": "2025-10-11T10:30:00Z",
  "deliverables": [
    {
      "file": "src/storage/compression.py",
      "status": "completed",
      "tests_passing": true
    }
  ],
  "blockers": [],
  "notes": "All compression tests passing, performance exceeds targets"
}
```

### Wave Transition Protocol

**Before starting next wave**:
1. All agents in current wave must report "completed"
2. All validation gate items must be checked
3. Integration tests must pass
4. Any blockers must be resolved

**If agent fails**:
1. Agent reports "failed" status with details
2. Wave coordinator reviews failure
3. Options:
   - Fix and retry (if time permits)
   - Simplify requirements
   - Defer to future iteration
4. Update validation gate accordingly

### Communication Channels

- **Status updates**: JSON files in status/ directory
- **Blockers**: Create `.context-kit/orchestration/markdown-audio-features/blockers/{agent-name}-{issue}.md`
- **Questions**: Create `.context-kit/orchestration/markdown-audio-features/questions/{agent-name}-{question}.md`
- **Code reviews**: PR comments or inline in code

## Circuit Breaker Strategy

### Failure Isolation

If an agent fails:
1. **Isolate failure**: Other agents continue if not dependent
2. **Document failure**: Record in status file with details
3. **Assess impact**: Which features are blocked?
4. **Recovery options**:
   - Retry with fixes
   - Implement minimal version
   - Defer feature
   - Proceed without (if non-critical)

### Rollback Procedures

If Wave N fails:
1. **Revert changes**: Git rollback to pre-wave state
2. **Review contracts**: Are contracts unclear?
3. **Adjust plan**: Simplify or re-sequence
4. **Retry or defer**: Based on priority and time

### Critical Path

**Feature 1 (Markdown)**:
- Critical: compression-agent → parser-markdown-agent → storage-markdown-agent
- If any fails: Feature incomplete

**Feature 2 (Audio)**:
- Critical: config-asr-agent → parser-asr-agent
- If any fails: Feature incomplete
- storage-markdown-agent not critical for audio (uses existing storage)

**Independence**:
- Markdown feature can succeed without audio feature
- Audio feature can succeed without markdown feature

## Quality Metrics

### Code Quality
- All new code has unit tests (>80% coverage)
- All integration points have integration tests
- No new linter warnings
- Type hints on all new functions
- Docstrings on all new public methods

### Performance
- Markdown extraction: <100ms per document
- Markdown compression: <100ms for 1MB
- Audio transcription: <5s for 10s audio (MPS device)
- No regression in existing processing times

### Integration
- All validation gates pass
- Cross-agent code reviews complete
- Integration tests pass
- No merge conflicts
- Backward compatibility maintained

## Risk Management

### High Risks

**Risk 1: ffmpeg not installed**
- Probability: Medium
- Impact: High (blocks MP3 processing)
- Mitigation: Check in Wave 0, document clearly
- Fallback: Process only WAV files

**Risk 2: Whisper model download fails**
- Probability: Low
- Impact: High (blocks audio processing)
- Mitigation: Pre-download models, document
- Fallback: Retry with smaller model

**Risk 3: Parser merge conflicts**
- Probability: Medium
- Impact: Medium (delays Wave 2)
- Mitigation: Clear line ownership, careful coordination
- Fallback: Sequential editing instead of parallel

### Medium Risks

**Risk 4: Markdown compression insufficient**
- Probability: Low
- Impact: Medium (metadata size issues)
- Mitigation: Test with large documents, adjust threshold
- Fallback: Increase metadata size limit

**Risk 5: Performance below targets**
- Probability: Low
- Impact: Low (degrades UX)
- Mitigation: Benchmark early, optimize if needed
- Fallback: Adjust targets or defer optimization

## Success Criteria

### Mandatory (Must Have)
- [ ] Markdown extracted and stored for all documents
- [ ] Markdown retrievable via get_document_markdown()
- [ ] MP3 files transcribed with Whisper
- [ ] WAV files transcribed with Whisper
- [ ] Audio transcript searchable
- [ ] All tests passing
- [ ] No regressions
- [ ] Performance targets met

### Nice to Have
- [ ] Word-level timestamps stored
- [ ] Language auto-detection working
- [ ] Compression ratio >3x for large documents
- [ ] Documentation with examples
- [ ] Performance exceeds targets by 20%

### Post-MVP Enhancements
- Timestamp-based audio search
- Multi-language audio support
- Enhanced audio metadata (speakers, confidence scores)
- Markdown export API endpoint
- Audio snippet playback from search results

## Estimated Timeline

- **Wave 0**: 30 minutes (prerequisites)
- **Wave 1**: 2-3 hours (compression + config)
- **Wave 2**: 3-4 hours (parser integration)
- **Wave 3**: 3-4 hours (storage + tests)
- **Wave 4**: 2-3 hours (integration validation)
- **Wave 5**: 1-2 hours (documentation)

**Total**: 12-17 hours development time
**With 6 parallel agents**: ~8-10 hours elapsed time
**Efficiency gain**: ~40-50% time savings from parallelism

## Conclusion

This orchestration plan maximizes parallelism while ensuring zero conflicts through:
- Clear territorial boundaries (no file overlaps)
- Interface-first development (contracts before code)
- Progressive validation (gates after each wave)
- Circuit breaker strategies (failure isolation and recovery)

**Ready to execute**: All contracts defined, agents assigned, waves planned.

**Next steps**:
1. Review and approve this plan
2. Execute Wave 0 (prerequisites)
3. Launch Wave 1 agents in parallel
4. Monitor progress and validate at each gate

---

*Generated by orchestration-plan command on 2025-10-11*

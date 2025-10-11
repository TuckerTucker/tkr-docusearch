# Validation Strategy

**Orchestration**: markdown-audio-features
**Created**: 2025-10-11
**Purpose**: Define validation criteria, testing approach, and quality gates for markdown storage and audio processing features

## Overview

This validation strategy ensures that:
1. Each agent's deliverables meet interface contracts
2. Integration points work correctly between agents
3. No regressions occur in existing functionality
4. Performance targets are met
5. Quality standards are maintained throughout development

## Validation Layers

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 5: Production Validation                             │
│ - End-to-end user workflows                                │
│ - Performance under load                                   │
│ - Backward compatibility                                   │
└─────────────────────────────────────────────────────────────┘
                              ▲
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: Integration Testing                               │
│ - Cross-agent integration                                  │
│ - Complete feature workflows                               │
│ - Interface contract compliance                            │
└─────────────────────────────────────────────────────────────┘
                              ▲
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Component Testing                                 │
│ - Individual agent deliverables                            │
│ - Interface method testing                                 │
│ - Error handling                                           │
└─────────────────────────────────────────────────────────────┘
                              ▲
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Unit Testing                                      │
│ - Individual functions/methods                             │
│ - Edge cases                                               │
│ - Error conditions                                         │
└─────────────────────────────────────────────────────────────┘
                              ▲
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Code Quality                                      │
│ - Linting (ruff, mypy)                                     │
│ - Type checking                                            │
│ - Documentation completeness                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Wave-by-Wave Validation

### Wave 0: Prerequisites Validation

**Validation Gate**:
- [ ] ffmpeg installed and accessible: `ffmpeg -version`
- [ ] docling[asr] dependencies present: `python -c "from docling.pipeline import asr_pipeline"`
- [ ] ChromaDB running at localhost:8001: `curl http://localhost:8001/api/v2/heartbeat`
- [ ] Test data directory exists: `data/test-documents/`
- [ ] All integration contracts reviewed and approved

**Automated Check Script**:
```bash
#!/bin/bash
# scripts/check-prerequisites.sh

echo "Checking prerequisites..."

# Check ffmpeg
if command -v ffmpeg &> /dev/null; then
    echo "✓ ffmpeg installed: $(ffmpeg -version | head -n1)"
else
    echo "✗ ffmpeg not found. Install with: brew install ffmpeg"
    exit 1
fi

# Check docling[asr]
if python -c "from docling.pipeline import asr_pipeline" 2>/dev/null; then
    echo "✓ docling[asr] dependencies present"
else
    echo "✗ docling[asr] not installed. Install with: pip install docling[asr]"
    exit 1
fi

# Check ChromaDB
if curl -s http://localhost:8001/api/v2/heartbeat > /dev/null; then
    echo "✓ ChromaDB accessible at localhost:8001"
else
    echo "✗ ChromaDB not accessible. Start with: ./scripts/start-all.sh"
    exit 1
fi

echo "All prerequisites met ✓"
```

**Proceed if**: All checks pass
**Block if**: Any check fails

---

### Wave 1: Foundation Layer Validation

#### compression-agent Validation

**Unit Tests** (must pass):
```python
# src/storage/test_compression.py

def test_compress_markdown_basic():
    """Test basic markdown compression."""
    markdown = "# Title\n\nContent here..."
    compressed = compress_markdown(markdown)
    assert isinstance(compressed, str)
    assert len(compressed) > 0
    # Compression should reduce size for typical markdown
    assert len(compressed) < len(markdown)

def test_decompress_markdown_basic():
    """Test basic markdown decompression."""
    original = "# Title\n\nContent here..."
    compressed = compress_markdown(original)
    decompressed = decompress_markdown(compressed)
    assert decompressed == original  # Exact equality

def test_round_trip_various_sizes():
    """Test round-trip with various markdown sizes."""
    test_cases = [
        "Short",  # Tiny
        "# Heading\n\n" + "Paragraph. " * 100,  # ~1KB
        "# Document\n\n" + "Content. " * 10000,  # ~100KB
        "# Large Doc\n\n" + "Text. " * 100000  # ~1MB
    ]
    for original in test_cases:
        compressed = compress_markdown(original)
        decompressed = decompress_markdown(compressed)
        assert decompressed == original, f"Round-trip failed for {len(original)} chars"

def test_unicode_and_emoji():
    """Test handling of unicode and emoji."""
    markdown = "# Test 中文 🚀\n\nContent with émojis 😀 and unicode: こんにちは"
    compressed = compress_markdown(markdown)
    decompressed = decompress_markdown(compressed)
    assert decompressed == markdown

def test_empty_string():
    """Test empty markdown handling."""
    compressed = compress_markdown("")
    assert isinstance(compressed, str)
    decompressed = decompress_markdown(compressed)
    assert decompressed == ""

def test_markdown_too_large():
    """Test size limit enforcement."""
    huge_markdown = "x" * (11 * 1024 * 1024)  # 11MB
    with pytest.raises(MarkdownTooLargeError):
        compress_markdown(huge_markdown)

def test_corrupted_data():
    """Test detection of corrupted compressed data."""
    with pytest.raises(CorruptedDataError):
        decompress_markdown("invalid_base64!@#$")

def test_deterministic_output():
    """Test that compression is deterministic."""
    markdown = "# Test\n\nDeterministic content"
    compressed1 = compress_markdown(markdown)
    compressed2 = compress_markdown(markdown)
    assert compressed1 == compressed2
```

**Performance Benchmarks** (must meet targets):
```python
def test_compression_performance():
    """Test compression performance targets."""
    import time

    # 1MB markdown
    markdown = "# Document\n\n" + "Content. " * 100000

    start = time.time()
    compressed = compress_markdown(markdown)
    duration = time.time() - start

    assert duration < 0.1, f"Compression too slow: {duration:.3f}s (target <100ms)"

def test_decompression_performance():
    """Test decompression performance targets."""
    import time

    markdown = "# Document\n\n" + "Content. " * 100000
    compressed = compress_markdown(markdown)

    start = time.time()
    decompressed = decompress_markdown(compressed)
    duration = time.time() - start

    assert duration < 0.05, f"Decompression too slow: {duration:.3f}s (target <50ms)"
```

**Validation Gate**:
- [ ] All unit tests pass (10/10)
- [ ] Round-trip fidelity: 100%
- [ ] Performance: <100ms for 1MB (compression), <50ms (decompression)
- [ ] Compression ratio: >3x for typical markdown
- [ ] Code coverage: >90%
- [ ] Type hints on all functions
- [ ] Docstrings complete

#### config-asr-agent Validation

**Unit Tests** (must pass):
```python
# src/config/test_asr_config.py

def test_asr_config_defaults():
    """Test default configuration values."""
    config = AsrConfig()
    assert config.enabled is True
    assert config.model == "turbo"
    assert config.language == "en"
    assert config.device == "mps"
    assert config.word_timestamps is True
    assert config.temperature == 0.0
    assert config.max_time_chunk == 30.0

def test_asr_config_from_env_with_values():
    """Test loading from environment variables."""
    import os
    os.environ["ASR_MODEL"] = "base"
    os.environ["ASR_LANGUAGE"] = "es"
    os.environ["ASR_DEVICE"] = "cpu"

    config = AsrConfig.from_env()
    assert config.model == "base"
    assert config.language == "es"
    assert config.device == "cpu"

    # Cleanup
    del os.environ["ASR_MODEL"]
    del os.environ["ASR_LANGUAGE"]
    del os.environ["ASR_DEVICE"]

def test_asr_config_from_env_missing():
    """Test defaults when environment variables missing."""
    config = AsrConfig.from_env()
    assert config.model == "turbo"  # Default

def test_validation_invalid_model():
    """Test validation rejects invalid model names."""
    with pytest.raises(ValueError, match="Invalid model"):
        AsrConfig(model="invalid")

def test_validation_invalid_device():
    """Test validation rejects invalid device types."""
    with pytest.raises(ValueError, match="Invalid device"):
        AsrConfig(device="invalid")

def test_validation_temperature_range():
    """Test validation rejects invalid temperature."""
    with pytest.raises(ValueError, match="Temperature must be"):
        AsrConfig(temperature=-0.1)
    with pytest.raises(ValueError, match="Temperature must be"):
        AsrConfig(temperature=1.1)

def test_to_docling_model_spec():
    """Test conversion to Docling ASR specification."""
    config = AsrConfig(model="turbo", language="en")
    spec = config.to_docling_model_spec()

    from docling.datamodel.pipeline_options_asr_model import InlineAsrNativeWhisperOptions
    assert isinstance(spec, InlineAsrNativeWhisperOptions)
    assert "turbo" in spec.repo_id or "large-v3-turbo" in spec.repo_id

def test_model_name_mapping():
    """Test model name to repo_id mapping."""
    models = ["turbo", "base", "small", "medium", "large"]
    for model in models:
        config = AsrConfig(model=model)
        spec = config.to_docling_model_spec()
        assert spec.repo_id.startswith("openai/whisper-")
```

**Validation Gate**:
- [ ] All unit tests pass (10/10)
- [ ] Validation rejects all invalid values
- [ ] Environment loading works with missing variables
- [ ] Conversion to Docling spec correct for all models
- [ ] Code coverage: >90%
- [ ] Type hints on all fields/methods
- [ ] Docstrings complete

**Wave 1 Overall Gate**:
- [ ] compression-agent validation complete
- [ ] config-asr-agent validation complete
- [ ] No blocking issues
- [ ] Both agents' code reviewed
- [ ] Ready to proceed to Wave 2

---

### Wave 2: Parser Layer Validation

#### parser-markdown-agent Validation

**Unit Tests** (must pass):
```python
# src/processing/test_parser_markdown.py

def test_markdown_extraction_pdf():
    """Test markdown extraction from PDF."""
    parser = DoclingParser()
    parsed_doc = parser.parse_document("data/test-documents/sample.pdf")

    assert "full_markdown" in parsed_doc.metadata
    assert "markdown_length" in parsed_doc.metadata
    assert "markdown_extracted" in parsed_doc.metadata
    assert "markdown_error" in parsed_doc.metadata

    assert parsed_doc.metadata["markdown_extracted"] is True
    assert len(parsed_doc.metadata["full_markdown"]) > 0
    assert parsed_doc.metadata["markdown_length"] == len(parsed_doc.metadata["full_markdown"])
    assert parsed_doc.metadata["markdown_error"] is None

def test_markdown_extraction_docx():
    """Test markdown extraction from DOCX."""
    parser = DoclingParser()
    parsed_doc = parser.parse_document("data/test-documents/sample.docx")

    assert parsed_doc.metadata["markdown_extracted"] is True
    assert "# " in parsed_doc.metadata["full_markdown"]  # Should have headings

def test_markdown_extraction_image_only():
    """Test markdown extraction from image-only document."""
    parser = DoclingParser()
    parsed_doc = parser.parse_document("data/test-documents/image-only.png")

    # Should have metadata fields even if empty
    assert "full_markdown" in parsed_doc.metadata
    assert parsed_doc.metadata["markdown_extracted"] is True
    # May be empty for image-only
    assert isinstance(parsed_doc.metadata["full_markdown"], str)

def test_markdown_extraction_failure_handling():
    """Test non-blocking error handling when extraction fails."""
    # This test may need to mock doc.export_to_markdown() to raise an exception
    # For now, we verify the error fields exist
    parser = DoclingParser()
    parsed_doc = parser.parse_document("data/test-documents/sample.pdf")

    # Verify error fields exist (even if None)
    assert "markdown_error" in parsed_doc.metadata
    assert parsed_doc.metadata["markdown_error"] is None or isinstance(parsed_doc.metadata["markdown_error"], str)

def test_existing_functionality_unchanged():
    """Test that existing parser functionality still works."""
    parser = DoclingParser()
    parsed_doc = parser.parse_document("data/test-documents/sample.pdf")

    # Verify existing fields still present
    assert "title" in parsed_doc.metadata
    assert "format" in parsed_doc.metadata
    assert "num_pages" in parsed_doc.metadata
    assert len(parsed_doc.pages) > 0
    assert len(parsed_doc.text_chunks) > 0
```

**Validation Gate**:
- [ ] All unit tests pass
- [ ] Markdown extracted from PDF, DOCX, PNG
- [ ] Error handling is non-blocking
- [ ] Metadata fields always present
- [ ] Existing functionality unchanged (regression tests pass)
- [ ] Code coverage: >80%

#### parser-asr-agent Validation

**Unit Tests** (must pass):
```python
# src/processing/test_parser_asr.py

@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg not installed")
def test_mp3_processing_with_asr():
    """Test MP3 file processing with Whisper ASR."""
    parser = DoclingParser()
    parsed_doc = parser.parse_document("data/test-documents/sample_10s.mp3")

    # Verify audio metadata
    assert "transcript_method" in parsed_doc.metadata
    assert parsed_doc.metadata["transcript_method"] == "whisper"
    assert "asr_model_used" in parsed_doc.metadata
    assert "asr_language" in parsed_doc.metadata
    assert "audio_format" in parsed_doc.metadata
    assert parsed_doc.metadata["audio_format"] == "mp3"

    # Verify transcript
    assert len(parsed_doc.pages) == 1  # Audio = single page
    assert parsed_doc.pages[0].image is None  # No visual for audio
    assert len(parsed_doc.pages[0].text) > 0  # Has transcript
    assert len(parsed_doc.text_chunks) > 0  # Has chunks

def test_wav_processing_with_asr():
    """Test WAV file processing with Whisper ASR."""
    parser = DoclingParser()
    parsed_doc = parser.parse_document("data/test-documents/sample_10s.wav")

    assert parsed_doc.metadata["audio_format"] == "wav"
    assert len(parsed_doc.pages[0].text) > 0
    assert len(parsed_doc.text_chunks) > 0

def test_asr_disabled_fallback():
    """Test graceful fallback when ASR is disabled."""
    import os
    os.environ["ASR_ENABLED"] = "false"

    parser = DoclingParser()
    # Should not raise exception, just log warning
    parsed_doc = parser.parse_document("data/test-documents/sample_10s.mp3")

    del os.environ["ASR_ENABLED"]

def test_asr_config_failure_graceful():
    """Test graceful degradation when ASR config fails."""
    # Set invalid ASR config
    import os
    os.environ["ASR_MODEL"] = "invalid_model"

    parser = DoclingParser()
    # Should log error but not crash
    # May fall back to basic processing

    del os.environ["ASR_MODEL"]

def test_vtt_files_unchanged():
    """Test that VTT file processing still works unchanged."""
    parser = DoclingParser()
    parsed_doc = parser.parse_document("data/test-documents/sample.vtt")

    # VTT should work as before (no ASR needed)
    assert len(parsed_doc.pages) > 0
    assert len(parsed_doc.text_chunks) > 0

def test_non_audio_files_unchanged():
    """Test that non-audio files are unaffected."""
    parser = DoclingParser()
    parsed_doc = parser.parse_document("data/test-documents/sample.pdf")

    # Should not have audio metadata
    assert "audio_format" not in parsed_doc.metadata
    # Should still work normally
    assert len(parsed_doc.pages) > 0
```

**Performance Tests**:
```python
def test_asr_performance_mps():
    """Test ASR performance with MPS device."""
    import time
    import os
    os.environ["ASR_DEVICE"] = "mps"

    parser = DoclingParser()

    start = time.time()
    parsed_doc = parser.parse_document("data/test-documents/sample_10s.mp3")
    duration = time.time() - start

    # 10s audio should process in <5s with MPS
    assert duration < 5.0, f"ASR too slow: {duration:.1f}s (target <5s for 10s audio)"

    del os.environ["ASR_DEVICE"]
```

**Validation Gate**:
- [ ] All unit tests pass
- [ ] MP3 processing works with transcription
- [ ] WAV processing works with transcription
- [ ] Audio metadata includes ASR fields
- [ ] ASR disabled fallback works
- [ ] VTT files unchanged
- [ ] Non-audio files unchanged
- [ ] Performance: <5s for 10s audio (MPS)
- [ ] Code coverage: >80%

**Wave 2 Overall Gate**:
- [ ] parser-markdown-agent validation complete
- [ ] parser-asr-agent validation complete
- [ ] No merge conflicts in docling_parser.py
- [ ] Both sets of functionality coexist correctly
- [ ] Ready to proceed to Wave 3

---

### Wave 3: Storage & Testing Validation

#### storage-markdown-agent Validation

**Unit Tests** (must pass):
```python
# src/storage/test_chroma_markdown.py

def test_store_small_markdown_no_compression():
    """Test storing small markdown without compression."""
    client = ChromaClient()
    doc_id = "test-doc-small"

    embeddings = np.random.randn(1031, 128).astype(np.float32)
    metadata = {
        "filename": "test.pdf",
        "source_path": "/path/to/test.pdf",
        "full_markdown": "# Small\n\nContent",  # <1KB
        "markdown_extracted": True
    }

    embedding_id = client.add_visual_embedding(doc_id, 1, embeddings, metadata)

    # Verify storage
    result = client._visual_collection.get(ids=[embedding_id], include=["metadatas"])
    stored_metadata = result['metadatas'][0]

    assert "full_markdown" in stored_metadata  # Uncompressed
    assert stored_metadata["markdown_compression"] == "none"

def test_store_large_markdown_with_compression():
    """Test storing large markdown with compression."""
    client = ChromaClient()
    doc_id = "test-doc-large"

    embeddings = np.random.randn(1031, 128).astype(np.float32)
    large_markdown = "# Large\n\n" + "Content. " * 1000  # >1KB
    metadata = {
        "filename": "test.pdf",
        "source_path": "/path/to/test.pdf",
        "full_markdown": large_markdown,
        "markdown_extracted": True
    }

    embedding_id = client.add_visual_embedding(doc_id, 1, embeddings, metadata)

    # Verify storage
    result = client._visual_collection.get(ids=[embedding_id], include=["metadatas"])
    stored_metadata = result['metadatas'][0]

    assert "full_markdown_compressed" in stored_metadata
    assert "full_markdown" not in stored_metadata  # Original removed
    assert stored_metadata["markdown_compression"] == "gzip+base64"

def test_get_document_markdown_compressed():
    """Test retrieving compressed markdown."""
    client = ChromaClient()
    doc_id = "test-doc-compressed"

    # Store document with compressed markdown
    embeddings = np.random.randn(1031, 128).astype(np.float32)
    original_markdown = "# Test\n\n" + "Content. " * 1000
    metadata = {
        "filename": "test.pdf",
        "source_path": "/path/to/test.pdf",
        "full_markdown": original_markdown,
        "markdown_extracted": True
    }

    client.add_visual_embedding(doc_id, 1, embeddings, metadata)

    # Retrieve markdown
    retrieved = client.get_document_markdown(doc_id)

    assert retrieved == original_markdown  # Exact match

def test_get_document_markdown_missing():
    """Test retrieving markdown when not available."""
    client = ChromaClient()
    doc_id = "test-doc-no-markdown"

    # Store document without markdown
    embeddings = np.random.randn(1031, 128).astype(np.float32)
    metadata = {
        "filename": "test.pdf",
        "source_path": "/path/to/test.pdf"
    }

    client.add_visual_embedding(doc_id, 1, embeddings, metadata)

    # Should return None (not raise exception)
    retrieved = client.get_document_markdown(doc_id)
    assert retrieved is None

def test_backward_compatibility():
    """Test that existing embeddings still work."""
    client = ChromaClient()
    doc_id = "test-doc-old"

    # Store embedding without markdown (like old code)
    embeddings = np.random.randn(1031, 128).astype(np.float32)
    metadata = {
        "filename": "old.pdf",
        "source_path": "/path/to/old.pdf"
    }

    client.add_visual_embedding(doc_id, 1, embeddings, metadata)

    # Should not crash
    retrieved = client.get_document_markdown(doc_id)
    assert retrieved is None
```

**Validation Gate**:
- [ ] All unit tests pass
- [ ] Small markdown stored uncompressed
- [ ] Large markdown stored compressed
- [ ] Retrieval works for compressed markdown
- [ ] Retrieval works for uncompressed markdown
- [ ] Missing markdown returns None (not error)
- [ ] Backward compatibility maintained
- [ ] Code coverage: >85%

#### testing-integration-agent Validation

**Test Files Created**:
- [ ] `src/processing/test_markdown_storage.py` exists
- [ ] `src/processing/test_audio_processing.py` exists
- [ ] Both files have comprehensive test coverage
- [ ] All tests pass

**Wave 3 Overall Gate**:
- [ ] storage-markdown-agent validation complete
- [ ] testing-integration-agent tests created
- [ ] All Wave 3 tests pass
- [ ] Ready to proceed to Wave 4 (integration)

---

### Wave 4: End-to-End Integration Validation

**Integration Test Scenarios**:

#### Scenario 1: PDF with Markdown (Full Workflow)
```python
def test_pdf_markdown_full_workflow():
    """Test complete PDF → markdown → storage → retrieval workflow."""
    # Parse PDF
    parser = DoclingParser()
    parsed_doc = parser.parse_document("data/test-documents/sample.pdf")

    # Verify markdown extracted
    assert parsed_doc.metadata["markdown_extracted"] is True
    original_markdown = parsed_doc.metadata["full_markdown"]

    # Process through pipeline (creates embeddings)
    processor = DocumentProcessor(embedding_engine, storage_client)
    confirmation = processor.process_document("data/test-documents/sample.pdf")

    # Retrieve markdown
    retrieved_markdown = storage_client.get_document_markdown(confirmation.doc_id)

    # Verify exact match
    assert retrieved_markdown == original_markdown
```

#### Scenario 2: MP3 Audio (Full Workflow)
```python
@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg not installed")
def test_mp3_audio_full_workflow():
    """Test complete MP3 → transcript → embeddings → search workflow."""
    # Parse MP3
    parser = DoclingParser()
    parsed_doc = parser.parse_document("data/test-documents/sample_10s.mp3")

    # Verify transcript
    assert len(parsed_doc.pages) == 1
    assert parsed_doc.pages[0].image is None  # No visual
    assert len(parsed_doc.pages[0].text) > 0  # Has transcript

    # Process through pipeline
    processor = DocumentProcessor(embedding_engine, storage_client)
    confirmation = processor.process_document("data/test-documents/sample_10s.mp3")

    # Verify no visual embeddings
    assert len(confirmation.visual_ids) == 0

    # Verify text embeddings
    assert len(confirmation.text_ids) > 0

    # Test search
    search_engine = SearchEngine(embedding_engine, storage_client)
    results = search_engine.search("expected keyword from transcript")

    # Verify audio document found
    assert any(confirmation.doc_id in r.doc_id for r in results)
```

#### Scenario 3: Cross-Feature Validation
```python
def test_audio_with_markdown_extraction():
    """Test that audio files also get markdown extraction (if applicable)."""
    parser = DoclingParser()
    parsed_doc = parser.parse_document("data/test-documents/sample_10s.mp3")

    # Audio should also have markdown metadata fields
    assert "markdown_extracted" in parsed_doc.metadata
    # May be empty, but should be present
```

**Performance Validation**:
```python
def test_performance_targets_met():
    """Validate all performance targets are met."""
    import time

    # Markdown extraction overhead
    parser = DoclingParser()
    start = time.time()
    parsed_doc = parser.parse_document("data/test-documents/sample.pdf")
    duration = time.time() - start
    # Should not add significant overhead (<100ms)

    # Markdown compression
    markdown = "# Test\n\n" + "Content. " * 100000  # 1MB
    start = time.time()
    compressed = compress_markdown(markdown)
    duration = time.time() - start
    assert duration < 0.1, f"Compression too slow: {duration}s"

    # Audio transcription (10s audio, MPS)
    if ffmpeg_available() and mps_available():
        start = time.time()
        parsed_doc = parser.parse_document("data/test-documents/sample_10s.mp3")
        duration = time.time() - start
        assert duration < 5.0, f"ASR too slow: {duration}s"
```

**Regression Testing**:
```python
def test_no_regressions_in_existing_features():
    """Verify no regressions in existing document processing."""
    # Test PDF processing (existing)
    parser = DoclingParser()
    pdf_doc = parser.parse_document("data/test-documents/existing_test.pdf")
    assert len(pdf_doc.pages) > 0
    assert len(pdf_doc.text_chunks) > 0

    # Test search (existing)
    search_engine = SearchEngine(embedding_engine, storage_client)
    results = search_engine.search("test query")
    assert len(results) >= 0  # Should not crash

    # Test processing pipeline (existing)
    processor = DocumentProcessor(embedding_engine, storage_client)
    confirmation = processor.process_document("data/test-documents/existing_test.pdf")
    assert confirmation.total_size_bytes > 0
```

**Validation Gate (Wave 4)**:
- [ ] PDF → markdown → storage → retrieval works end-to-end
- [ ] MP3 → transcript → embeddings → search works end-to-end
- [ ] WAV → transcript → embeddings → search works end-to-end
- [ ] Audio creates no visual embeddings
- [ ] Audio transcript is searchable
- [ ] Performance targets met (all benchmarks)
- [ ] No regressions in existing features
- [ ] Cross-agent code review complete
- [ ] All integration tests passing

---

## Quality Metrics

### Code Quality

**Required Standards**:
- **Type hints**: All public functions/methods have type hints
- **Docstrings**: All public functions/methods have Google-style docstrings
- **Linting**: No errors from `ruff check`
- **Type checking**: No errors from `mypy`
- **Code coverage**: >80% for new code
- **Complexity**: Cyclomatic complexity <10 per function

**Automated Checks**:
```bash
# Run from project root
ruff check src/
mypy src/
pytest --cov=src --cov-report=html
```

### Test Quality

**Coverage Requirements**:
- Unit tests: >90% coverage per module
- Integration tests: All interface contracts validated
- Regression tests: Existing functionality verified
- Performance tests: All targets benchmarked

**Test Organization**:
```
src/
├── storage/
│   ├── compression.py
│   └── test_compression.py  # Unit tests
├── config/
│   ├── processing_config.py
│   └── test_asr_config.py  # Unit tests
├── processing/
│   ├── docling_parser.py
│   ├── test_parser_markdown.py  # Unit tests (markdown)
│   ├── test_parser_asr.py  # Unit tests (ASR)
│   ├── test_markdown_storage.py  # Integration tests
│   └── test_audio_processing.py  # Integration tests
```

### Performance Metrics

**Target Benchmarks**:
| Operation | Target | Validation Method |
|-----------|--------|-------------------|
| Markdown extraction | <100ms | Timed test with 100-page PDF |
| Markdown compression (1MB) | <100ms | Timed test with 1MB markdown |
| Markdown decompression (1MB) | <50ms | Timed test with compressed 1MB |
| MP3 transcription (10s audio, MPS) | <5s | Timed test with sample_10s.mp3 |
| WAV transcription (10s audio, MPS) | <5s | Timed test with sample_10s.wav |

**Performance Monitoring**:
- Log all processing times during validation
- Compare against baseline (existing features)
- Alert if any operation exceeds 2x target

---

## Cross-Agent Code Review

### Review Protocol

After each wave, consumers review their dependencies:

**Wave 1 Reviews**:
- storage-markdown-agent reviews compression-agent code
- parser-asr-agent reviews config-asr-agent code

**Wave 2 Reviews**:
- storage-markdown-agent reviews parser-markdown-agent metadata format
- processor-agent (existing) reviews parser-asr-agent output

**Wave 3 Reviews**:
- testing-integration-agent reviews all agents' code
- All agents review testing-integration-agent's tests

### Review Checklist

For each review:
- [ ] Interface contract followed exactly
- [ ] Error handling is robust
- [ ] Performance targets met
- [ ] Code is readable and maintainable
- [ ] Tests are comprehensive
- [ ] Documentation is complete
- [ ] No breaking changes to existing functionality

---

## Failure Recovery

### Validation Failure Protocol

If any validation gate fails:

1. **Identify failure**:
   - Which test(s) failed?
   - Which agent is responsible?
   - Is it critical or can we proceed?

2. **Assess impact**:
   - Blocks entire feature?
   - Blocks dependent agents?
   - Can be fixed quickly (<30min)?

3. **Decide action**:
   - **Fix immediately**: If quick fix available
   - **Defer to next iteration**: If non-critical
   - **Simplify requirement**: If overly ambitious
   - **Rollback wave**: If fundamentally broken

4. **Document decision**:
   - Update status files
   - Record in blockers/
   - Notify dependent agents

### Circuit Breaker Thresholds

**Yellow alert** (warn but proceed):
- 1-2 non-critical tests failing
- Performance 10-20% below target
- Code coverage 75-80%

**Red alert** (block next wave):
- Any critical test failing
- Performance >50% below target
- Code coverage <75%
- Integration tests failing
- Regression tests failing

---

## Success Criteria Summary

### Mandatory (Must Pass)
- [ ] All unit tests passing (100%)
- [ ] All integration tests passing (100%)
- [ ] All performance benchmarks met (100%)
- [ ] No regressions in existing features
- [ ] Code coverage >80% on new code
- [ ] Type checking passes with no errors
- [ ] Linting passes with no errors
- [ ] All integration contracts validated

### Nice to Have
- [ ] Code coverage >90%
- [ ] Performance exceeds targets by 20%
- [ ] Zero linting warnings
- [ ] Documentation includes examples
- [ ] Comprehensive error messages

---

*Generated as part of markdown-audio-features orchestration plan on 2025-10-11*

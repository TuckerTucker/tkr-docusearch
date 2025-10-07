# Validation Strategy: Docling Enhanced Mode

**Plan ID**: docling-enhanced-mode
**Version**: 1.0
**Status**: Specification

## Validation Philosophy

Progressive validation with clear gates between waves ensures quality at each stage:
1. **Unit validation**: Each component tested in isolation
2. **Integration validation**: Components tested together
3. **System validation**: Full pipeline tested end-to-end
4. **Performance validation**: Benchmarks verify targets met
5. **Regression validation**: Existing functionality preserved

---

## Wave Gates

### Wave 0 → Wave 1 Gate

**Prerequisites**:
- ☐ All integration contracts written and reviewed
- ☐ Baseline metrics captured from current system
- ☐ Test document set prepared (3-5 PDFs with rich structure)
- ☐ Orchestration directory initialized

**Validation**:
```bash
# Capture baseline metrics
pytest src/test_end_to_end.py --benchmark
# Record: processing time, storage size, search latency

# Verify test documents
ls -lh data/test_documents/
# Should have: technical_paper.pdf, report_with_tables.pdf, etc.
```

**Gate Criteria**:
- All contracts approved
- Baseline metrics recorded
- Test documents ready

---

### Wave 1 → Wave 2 Gate

**Agents completing**: config-agent, metadata-agent (schema only)

**Validation Tests**:

```python
# Test 1: Configuration Loading
def test_config_loads_from_env():
    config = EnhancedModeConfig.from_env()
    assert config.enable_table_structure == True
    assert config.chunking_strategy == ChunkingStrategy.HYBRID
    assert config.max_chunk_tokens == 512

# Test 2: Configuration Validation
def test_config_validation():
    config = EnhancedModeConfig(
        min_chunk_tokens=600,  # > max_chunk_tokens
        max_chunk_tokens=512
    )
    with pytest.raises(AssertionError):
        validate_config(config)

# Test 3: Pipeline Options Creation
def test_create_pipeline_options():
    config = EnhancedModeConfig()
    options = create_pipeline_options(config)
    assert options.do_table_structure == True
    assert options.do_picture_classification == True

# Test 4: Metadata Schema Instantiation
def test_metadata_schema_classes():
    structure = DocumentStructure(
        headings=[],
        tables=[],
        pictures=[],
        code_blocks=[],
        formulas=[]
    )
    assert structure.to_dict() is not None
```

**Run Command**:
```bash
pytest src/config/test_processing_config.py -v
pytest src/storage/test_metadata_schema.py -v
```

**Gate Criteria**:
- ✅ All configuration tests pass
- ✅ Environment variables parsed correctly
- ✅ Pipeline options created successfully
- ✅ Metadata schema classes defined and validated

---

### Wave 2 → Wave 3 Gate

**Agents completing**: structure-agent, chunking-agent

**Validation Tests**:

```python
# Test 5: Structure Extraction
def test_structure_extraction():
    # Load test document
    from docling.document_converter import DocumentConverter
    converter = DocumentConverter()
    result = converter.convert("data/test_documents/technical_paper.pdf")

    # Extract structure
    config = EnhancedModeConfig()
    structure = extract_document_structure(result.document, config)

    # Validate
    assert len(structure.headings) > 0, "Should extract headings"
    assert len(structure.tables) >= 0, "Should extract tables (may be 0)"
    assert structure.size_estimate_kb() < 100, "Structure within size limit"

# Test 6: Smart Chunking
def test_smart_chunking():
    # Create chunker
    config = EnhancedModeConfig(chunking_strategy=ChunkingStrategy.HYBRID)
    chunker = create_chunker(config)
    assert isinstance(chunker, SmartChunker)

    # Load document
    converter = DocumentConverter()
    result = converter.convert("data/test_documents/technical_paper.pdf")

    # Extract structure
    structure = extract_document_structure(result.document, config)

    # Chunk
    chunks = chunker.chunk_document(
        doc=result.document,
        doc_id="test-doc",
        structure=structure
    )

    # Validate
    assert len(chunks) > 0, "Should produce chunks"
    assert all(c.context is not None for c in chunks), "All chunks have context"
    assert all(c.context.section_path for c in chunks), "Section paths populated"

# Test 7: Chunking Strategy Router
def test_chunking_strategy_router():
    # Hybrid strategy
    config_hybrid = EnhancedModeConfig(chunking_strategy=ChunkingStrategy.HYBRID)
    chunker_hybrid = create_chunker(config_hybrid)
    assert isinstance(chunker_hybrid, SmartChunker)

    # Legacy strategy
    config_legacy = EnhancedModeConfig(chunking_strategy=ChunkingStrategy.LEGACY)
    chunker_legacy = create_chunker(config_legacy)
    assert isinstance(chunker_legacy, LegacyChunker)
```

**Run Commands**:
```bash
pytest src/processing/test_structure_extractor.py -v
pytest src/processing/test_smart_chunker.py -v
pytest src/processing/test_docling_parser.py -v
```

**Gate Criteria**:
- ✅ Structure extraction works on all test documents
- ✅ Structure size within limits
- ✅ Smart chunking produces quality chunks
- ✅ Context metadata populated correctly
- ✅ Legacy chunking still works
- ✅ No errors or warnings on test set

---

### Wave 3 → Wave 4 Gate

**Agents completing**: metadata-agent (storage), integration-agent

**Validation Tests**:

```python
# Test 8: Enhanced Metadata Storage
def test_enhanced_metadata_storage():
    client = ChromaClient()

    # Create test data
    structure = DocumentStructure(
        headings=[HeadingInfo(text="Introduction", level=HeadingLevel.SECTION_HEADER, page_num=1)],
        tables=[],
        pictures=[],
        code_blocks=[],
        formulas=[]
    )

    embedding = np.random.rand(128)

    # Store
    embedding_id = client.add_visual_embedding(
        embedding=embedding,
        doc_id="test-doc",
        filename="test.pdf",
        page_num=1,
        structure=structure,
        page_context={"headings_on_page": ["Introduction"]}
    )

    # Retrieve
    results = client.chroma_collection_visual.get(ids=[embedding_id])
    metadata = results['metadatas'][0]

    # Validate
    assert 'structure' in metadata
    assert 'page_context' in metadata
    assert metadata['page_context']['headings_on_page'] == ["Introduction"]

# Test 9: Metadata Compression
def test_metadata_compression():
    structure_dict = {
        "headings": [{"text": "Introduction", "level": "SECTION_HEADER", "page": 1}],
        "tables": [],
        "pictures": []
    }

    # Compress
    compressed = compress_structure(structure_dict)
    assert len(compressed) < len(json.dumps(structure_dict))

    # Decompress
    decompressed = decompress_structure(compressed)
    assert decompressed == structure_dict

# Test 10: End-to-End Processing
def test_end_to_end_enhanced_processing():
    # Initialize processor with enhanced mode
    processor = DocumentProcessor(
        embedding_engine=embedding_engine,
        storage_client=storage_client,
        config=EnhancedModeConfig()
    )

    # Process test document
    result = processor.process_document("data/test_documents/technical_paper.pdf")

    # Validate
    assert result.doc_id is not None
    assert len(result.visual_ids) > 0
    assert len(result.text_ids) > 0

    # Check metadata was stored
    visual_results = storage_client.chroma_collection_visual.get(ids=[result.visual_ids[0]])
    assert 'structure' in visual_results['metadatas'][0]

    text_results = storage_client.chroma_collection_text.get(ids=[result.text_ids[0]])
    assert 'context' in text_results['metadatas'][0]
```

**Run Commands**:
```bash
pytest src/storage/test_enhanced_metadata.py -v
pytest src/processing/test_enhanced_processing.py -v
pytest tests/test_end_to_end_enhanced.py -v
```

**Performance Validation**:
```python
# Test 11: Performance Benchmark
def test_performance_overhead():
    # Baseline (legacy mode)
    config_legacy = EnhancedModeConfig(
        enable_table_structure=False,
        enable_picture_classification=False,
        chunking_strategy=ChunkingStrategy.LEGACY
    )
    processor_legacy = DocumentProcessor(
        embedding_engine=embedding_engine,
        storage_client=storage_client,
        config=config_legacy
    )

    start = time.time()
    processor_legacy.process_document("data/test_documents/technical_paper.pdf")
    baseline_time = time.time() - start

    # Enhanced mode
    config_enhanced = EnhancedModeConfig()
    processor_enhanced = DocumentProcessor(
        embedding_engine=embedding_engine,
        storage_client=storage_client,
        config=config_enhanced
    )

    start = time.time()
    processor_enhanced.process_document("data/test_documents/technical_paper.pdf")
    enhanced_time = time.time() - start

    # Validate overhead
    overhead_pct = ((enhanced_time - baseline_time) / baseline_time) * 100
    assert overhead_pct < 20, f"Processing overhead {overhead_pct:.1f}% exceeds 20% target"

    print(f"Baseline: {baseline_time:.2f}s, Enhanced: {enhanced_time:.2f}s, Overhead: {overhead_pct:.1f}%")
```

**Gate Criteria**:
- ✅ Enhanced metadata stores successfully
- ✅ Compression achieves >3x ratio
- ✅ Metadata size <50KB per embedding
- ✅ End-to-end processing works with all features
- ✅ Processing time overhead <20%
- ✅ Storage size overhead <30%
- ✅ No errors on test document set

---

### Wave 4 Final Validation

**Agent completing**: validation-agent

**Comprehensive Test Suite**:

```bash
# Run all tests
pytest src/ tests/ -v --cov=src --cov-report=html

# Performance benchmark suite
pytest tests/test_end_to_end_enhanced.py::test_performance_comparison -v

# Search quality validation
pytest tests/test_search_quality_enhanced.py -v

# Backward compatibility check
pytest tests/test_backward_compatibility.py -v
```

**Manual Validation Checklist**:

**Functional Validation**:
- ☐ Upload PDF with tables → tables extracted correctly
- ☐ Upload PDF with images → images classified correctly
- ☐ Upload PDF with sections → hierarchy captured correctly
- ☐ Search results include structural context
- ☐ Feature flags enable/disable correctly
- ☐ Legacy documents still searchable

**Performance Validation**:
- ☐ Processing time increase <20% (measure on 5+ documents)
- ☐ Storage size increase <30% (measure on 5+ documents)
- ☐ Search latency unchanged (<300ms)
- ☐ Memory usage acceptable (<150% baseline)

**Quality Validation**:
- ☐ Chunk boundaries better than word-based (manual review)
- ☐ Structure metadata accurate (spot check)
- ☐ Picture classifications correct (>90% accuracy)
- ☐ Search results improved (A/B comparison)

**Regression Validation**:
- ☐ All existing tests still pass
- ☐ Legacy documents work unchanged
- ☐ API contracts unchanged
- ☐ No breaking changes to storage format

**Final Gate Criteria**:
- ✅ All automated tests pass (100%)
- ✅ Performance targets met (<20% overhead)
- ✅ Quality targets met (measurable improvement)
- ✅ No regressions in existing functionality
- ✅ Documentation updated
- ✅ Performance report generated

---

## Test Document Set

### Required Test Documents

1. **technical_paper.pdf**
   - Complex hierarchical structure
   - Multiple sections and subsections
   - Tables with data
   - Figures with captions
   - Mathematical formulas
   - Code snippets

2. **business_report.pdf**
   - Executive summary
   - Charts and diagrams
   - Tables with financial data
   - Bulleted/numbered lists

3. **simple_document.pdf**
   - Minimal structure (baseline)
   - Plain text paragraphs
   - No tables or figures

4. **multi_format_test.docx**
   - DOCX format test
   - Tables and images
   - Sections and headings

5. **presentation.pptx**
   - PPTX format test
   - Multiple slides
   - Images and text

### Preparing Test Documents

```bash
# Create test directory
mkdir -p data/test_documents

# Download/copy test documents
# (Add actual test documents here)

# Verify documents
ls -lh data/test_documents/
```

---

## Continuous Validation

### During Development

```bash
# Quick validation after each change
pytest src/processing/test_enhanced_processing.py::test_structure_extraction -v

# Full validation before wave gate
pytest src/ -v
```

### Pre-Commit Validation

```bash
# Run fast tests
pytest src/ -v -m "not slow"

# Check code style
flake8 src/
black --check src/

# Type checking
mypy src/
```

---

## Performance Monitoring

### Metrics to Track

```python
@dataclass
class ValidationMetrics:
    """Metrics for validation reporting."""

    # Timing (seconds)
    parsing_time: float
    structure_time: float
    chunking_time: float
    embedding_time: float
    storage_time: float
    total_time: float

    # Size (KB)
    structure_size_kb: float
    metadata_size_kb: float
    storage_size_kb: float

    # Quality
    structure_accuracy: float  # 0-1
    chunk_quality_score: float  # 0-1
    search_quality_improvement: float  # percentage

    # Features
    features_enabled: List[str]
    chunking_strategy: str

    def overhead_percentage(self, baseline_time: float) -> float:
        return ((self.total_time - baseline_time) / baseline_time) * 100

    def report(self) -> str:
        """Generate validation report."""
        return f"""
Validation Metrics Report
=========================

Timing:
  Total: {self.total_time:.2f}s
  Parsing: {self.parsing_time:.2f}s
  Structure: {self.structure_time:.2f}s
  Chunking: {self.chunking_time:.2f}s
  Embedding: {self.embedding_time:.2f}s
  Storage: {self.storage_time:.2f}s

Size:
  Structure: {self.structure_size_kb:.1f}KB
  Metadata: {self.metadata_size_kb:.1f}KB
  Total Storage: {self.storage_size_kb:.1f}KB

Quality:
  Structure Accuracy: {self.structure_accuracy*100:.1f}%
  Chunk Quality: {self.chunk_quality_score*100:.1f}%
  Search Improvement: {self.search_quality_improvement:.1f}%

Configuration:
  Features: {', '.join(self.features_enabled)}
  Chunking: {self.chunking_strategy}
"""
```

---

## Failure Recovery

### Validation Failure Protocol

1. **Identify failing test**: Note exact test name and wave
2. **Isolate issue**: Run test in isolation with verbose output
3. **Review logs**: Check for error messages and stack traces
4. **Consult contracts**: Verify implementation matches specification
5. **Fix and revalidate**: Make fix, re-run test, verify pass
6. **Document**: Note issue and resolution in wave notes

### Wave Gate Failure

If wave gate fails:
1. **Block next wave**: Do not proceed to Wave N+1
2. **Notify agents**: All agents in Wave N notified of failure
3. **Root cause analysis**: Identify which deliverable caused failure
4. **Fix and revalidate**: Responsible agent fixes issue
5. **Re-run gate tests**: Full wave validation repeated
6. **Approve transition**: Only proceed when all tests pass

---

## Success Criteria Summary

### Must-Pass Criteria (Blocking)
- ✅ All automated tests pass
- ✅ Processing overhead <20%
- ✅ Storage overhead <30%
- ✅ No regressions in existing tests

### Should-Pass Criteria (Non-Blocking)
- ✅ Search quality improvement measurable
- ✅ Structure extraction accuracy >95%
- ✅ Picture classification accuracy >90%
- ✅ Chunk quality better than baseline

---

**Validation Strategy Version**: 1.0
**Last Updated**: 2025-10-07

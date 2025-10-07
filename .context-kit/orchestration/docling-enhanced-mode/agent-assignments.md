# Agent Assignments: Docling Enhanced Mode

**Plan ID**: docling-enhanced-mode
**Version**: 1.0
**Status**: Ready for execution

## Agent Roster

| Agent ID | Role | Primary Files | Wave Assignment |
|----------|------|---------------|-----------------|
| config-agent | Configuration & Feature Flags | `src/config/processing_config.py`, `.env.template` | Wave 1 |
| structure-agent | Structure Extraction | `src/processing/structure_extractor.py` | Wave 2 |
| chunking-agent | Smart Chunking | `src/processing/smart_chunker.py` | Wave 2 |
| metadata-agent | Metadata Schema & Storage | `src/storage/metadata_schema.py`, `chroma_client.py` | Wave 1, 3 |
| integration-agent | Pipeline Integration | `src/processing/processor.py` | Wave 3 |
| validation-agent | Testing & Validation | `src/processing/test_*.py` | Wave 4 |

---

## Agent 1: config-agent

### Responsibilities
- Define configuration dataclasses and enums
- Implement environment variable parsing
- Create configuration validation
- Update environment templates
- Provide configuration loading utilities

### Territorial Ownership
**Full ownership** (create new files):
- `src/config/processing_config.py` (new file)

**Shared files** (append only):
- `.env.template` (add new variables at end)
- `docker/.env.template` (add new variables at end)

### Deliverables
1. `src/config/processing_config.py` (~150-200 lines)
   - `EnhancedModeConfig` dataclass
   - `ChunkingStrategy` enum
   - `from_env()` class method
   - Configuration validation function
   - `create_pipeline_options()` helper

2. Updated `.env.template` with:
   ```bash
   # Enhanced Docling Features (Wave 5)
   ENABLE_TABLE_STRUCTURE=true
   ENABLE_PICTURE_CLASSIFICATION=true
   ENABLE_CODE_ENRICHMENT=false
   ENABLE_FORMULA_ENRICHMENT=false
   CHUNKING_STRATEGY=hybrid
   MAX_CHUNK_TOKENS=512
   MIN_CHUNK_TOKENS=100
   MERGE_PEER_CHUNKS=true
   TABLE_STRUCTURE_MODE=accurate
   IMAGES_SCALE=2.0
   ```

### Dependencies
- **Reads**: Integration contract specifications
- **Consumed by**: All other agents

### Validation Checklist
- ☐ Configuration loads from environment without errors
- ☐ Default values match specification
- ☐ Validation catches invalid values
- ☐ `create_pipeline_options()` produces valid PdfPipelineOptions
- ☐ Documentation strings complete

### Wave Assignment
**Wave 1** - Can run in parallel with metadata-agent

---

## Agent 2: structure-agent

### Responsibilities
- Extract hierarchical headings from DoclingDocument
- Extract table metadata with structure information
- Extract picture metadata with classifications
- Extract code blocks and formulas (if enabled)
- Build DocumentStructure object
- Validate structure size limits

### Territorial Ownership
**Full ownership** (create new files):
- `src/processing/structure_extractor.py` (new file)

**Shared files** (modify specific sections):
- `src/processing/docling_parser.py`:
  - Modify `_parse_with_docling()` to enable pipeline options
  - Add structure extraction call
  - Return docling_document for structure extraction

### Deliverables
1. `src/processing/structure_extractor.py` (~300-400 lines)
   - `DocumentStructure` dataclass
   - `HeadingInfo`, `TableInfo`, `PictureInfo` dataclasses
   - `extract_document_structure()` function
   - Helper functions: `_extract_headings()`, `_extract_tables()`, etc.
   - Size validation

2. Modified `src/processing/docling_parser.py`:
   - Update pipeline options in `_parse_with_docling()`
   - Add structure extraction to metadata
   - Return docling_document

### Dependencies
- **Reads**: CONFIG-001 (configuration contract)
- **Provides**: STRUCT-001 (structure extraction contract)
- **Consumed by**: chunking-agent, metadata-agent, integration-agent

### Validation Checklist
- ☐ Headings extracted with correct hierarchy
- ☐ Tables extracted with dimensions and captions
- ☐ Pictures extracted with classifications
- ☐ Structure size within limits
- ☐ Works with documents lacking structure
- ☐ No errors on test document set

### Wave Assignment
**Wave 2** - Can run in parallel with chunking-agent

---

## Agent 3: chunking-agent

### Responsibilities
- Implement SmartChunker wrapper around HybridChunker
- Extract chunk context from HybridChunker metadata
- Build section paths and element types
- Detect related tables/figures in chunks
- Maintain LegacyChunker for backward compatibility
- Implement chunking strategy router

### Territorial Ownership
**Full ownership** (create new files):
- `src/processing/smart_chunker.py` (new file)

**Shared files** (modify specific sections):
- `src/processing/docling_parser.py`:
  - Add `_chunk_document()` method
  - Update chunking logic to support strategy selection

### Deliverables
1. `src/processing/smart_chunker.py` (~250-350 lines)
   - `ChunkContext` dataclass
   - `SmartChunker` class with HybridChunker integration
   - `LegacyChunker` wrapper
   - `create_chunker()` factory function
   - Context extraction logic

2. Modified `src/processing/docling_parser.py`:
   - Add `_chunk_document()` routing method
   - Support both chunking strategies

### Dependencies
- **Reads**: CONFIG-001 (configuration contract), STRUCT-001 (structure contract)
- **Provides**: CHUNK-001 (chunking contract)
- **Consumed by**: metadata-agent, integration-agent

### Validation Checklist
- ☐ HybridChunker initializes correctly
- ☐ Chunks extracted from sample documents
- ☐ Context metadata populated accurately
- ☐ Legacy chunking still functional
- ☐ Chunking strategy router works
- ☐ No tokenization errors

### Wave Assignment
**Wave 2** - Can run in parallel with structure-agent

---

## Agent 4: metadata-agent

### Responsibilities
- Define metadata schemas for visual and text collections
- Implement compression for structure and context
- Update ChromaDB storage methods
- Add size validation
- Ensure backward compatibility
- Optimize compression ratios

### Territorial Ownership
**Full ownership** (create new files):
- `src/storage/metadata_schema.py` (new file - Wave 1)

**Shared files** (modify specific methods):
- `src/storage/chroma_client.py`:
  - Update `add_visual_embedding()` signature and implementation
  - Update `add_text_embedding()` signature and implementation
- `src/storage/compression.py`:
  - Add `compress_structure()` and `decompress_structure()`
  - Add `compress_context()` and `decompress_context()`

### Deliverables - Wave 1
1. `src/storage/metadata_schema.py` (~200-250 lines)
   - Schema class definitions
   - Validation functions
   - Size estimation utilities

### Deliverables - Wave 3
2. Modified `src/storage/chroma_client.py` (+100-150 lines)
   - Enhanced `add_visual_embedding()` with structure parameter
   - Enhanced `add_text_embedding()` with chunk context
   - Metadata validation before storage

3. Modified `src/storage/compression.py` (+50-80 lines)
   - Structure compression/decompression
   - Context compression/decompression

### Dependencies
- **Reads**: CONFIG-001, STRUCT-001, CHUNK-001
- **Provides**: STORE-001 (metadata storage contract)
- **Consumed by**: integration-agent

### Validation Checklist - Wave 1
- ☐ Schema classes defined correctly
- ☐ Validation functions work

### Validation Checklist - Wave 3
- ☐ Enhanced metadata stores successfully
- ☐ Compression achieves >3x ratio
- ☐ Metadata size within 50KB limit
- ☐ Retrieval works correctly
- ☐ Backward compatible with old metadata

### Wave Assignment
**Wave 1** (schema definition) - Parallel with config-agent
**Wave 3** (storage implementation) - After Wave 2 complete

---

## Agent 5: integration-agent

### Responsibilities
- Update DocumentProcessor to use enhanced configuration
- Integrate structure extraction into pipeline
- Integrate smart chunking into pipeline
- Build page context for visual embeddings
- Pass enhanced metadata to storage
- Implement graceful degradation
- Add performance monitoring

### Territorial Ownership
**Shared files** (modify main processing flow):
- `src/processing/processor.py`:
  - Update `__init__()` to load config
  - Update `process_document()` for enhanced flow
  - Add `_build_page_context()` helper
  - Add error handling and fallbacks

### Deliverables
1. Modified `src/processing/processor.py` (+150-200 lines)
   - Config initialization in `__init__()`
   - Enhanced `process_document()` method
   - Page context building
   - Enhanced metadata passing
   - Graceful degradation on feature failures
   - Performance metric logging

### Dependencies
- **Reads**: CONFIG-001, STRUCT-001, CHUNK-001, STORE-001
- **Provides**: PIPELINE-001 (pipeline integration contract)
- **Consumed by**: validation-agent

### Validation Checklist
- ☐ End-to-end processing works with enhancements
- ☐ Configuration loaded and applied correctly
- ☐ Structure, chunks, metadata all stored
- ☐ Processing time within 20% overhead target
- ☐ Graceful degradation works on failures
- ☐ Legacy mode still functional

### Wave Assignment
**Wave 3** - After Wave 2 complete, parallel with metadata-agent storage work

---

## Agent 6: validation-agent

### Responsibilities
- Create comprehensive test suite for enhanced features
- Test structure extraction accuracy
- Test smart chunking quality
- Test metadata storage/retrieval
- Run end-to-end validation
- Generate performance comparison report
- Update documentation

### Territorial Ownership
**Full ownership** (create new test files):
- `src/processing/test_enhanced_processing.py` (new)
- `src/storage/test_enhanced_metadata.py` (new)
- `tests/test_end_to_end_enhanced.py` (new)
- `.context-kit/orchestration/docling-enhanced-mode/PERFORMANCE_REPORT.md` (new)

### Deliverables
1. `src/processing/test_enhanced_processing.py` (~300-400 lines)
   - Structure extraction tests
   - Smart chunking tests
   - Feature flag tests
   - Integration tests

2. `src/storage/test_enhanced_metadata.py` (~200-300 lines)
   - Metadata storage tests
   - Compression tests
   - Size validation tests
   - Query tests

3. `tests/test_end_to_end_enhanced.py` (~250-350 lines)
   - Full pipeline tests with real documents
   - Performance benchmarking
   - Search quality comparison
   - Backward compatibility tests

4. `PERFORMANCE_REPORT.md` (performance analysis)
   - Timing comparisons (baseline vs enhanced)
   - Storage size analysis
   - Search quality improvements
   - Feature overhead breakdown

### Dependencies
- **Reads**: All integration contracts
- **Tests**: All implemented features
- **Validates**: System-wide integration

### Validation Checklist
- ☐ All unit tests pass
- ☐ All integration tests pass
- ☐ Performance targets met (<20% overhead)
- ☐ Storage efficiency maintained (<30% growth)
- ☐ Search quality improved (measurable)
- ☐ No regressions in existing functionality

### Wave Assignment
**Wave 4** - After Wave 3 complete

---

## Conflict Resolution

### File Ownership Matrix

| File | Owner | Other Access | Conflict Risk |
|------|-------|--------------|---------------|
| `src/config/processing_config.py` | config-agent | Read-only (all) | None |
| `src/processing/structure_extractor.py` | structure-agent | Read-only (all) | None |
| `src/processing/smart_chunker.py` | chunking-agent | Read-only (all) | None |
| `src/storage/metadata_schema.py` | metadata-agent | Read-only (all) | None |
| `src/processing/docling_parser.py` | structure-agent, chunking-agent | Modified by both | **LOW** (different methods) |
| `src/storage/chroma_client.py` | metadata-agent | integration-agent reads | **VERY LOW** (wave separation) |
| `src/storage/compression.py` | metadata-agent | All read | None |
| `src/processing/processor.py` | integration-agent | All read | None |

### Shared File Coordination

**`docling_parser.py`** modified by structure-agent AND chunking-agent:
- **structure-agent**: Modifies `_parse_with_docling()` method
- **chunking-agent**: Adds new `_chunk_document()` method
- **Resolution**: Different methods, no overlap
- **Risk**: Very Low

**`.env.template`** modified by config-agent:
- **Action**: Append new variables at end of file
- **Risk**: None (append-only)

---

## Communication Protocol

### Status Updates

Each agent must report:
1. **Start**: "Agent [name] starting Wave [N] work"
2. **Progress**: "Agent [name]: [milestone] complete"
3. **Deliverable**: "Agent [name]: Created [file_path]"
4. **Tests**: "Agent [name]: Tests [pass/fail]"
5. **Complete**: "Agent [name] Wave [N] complete - ready for gate"

### Handoff Protocol

Before Wave N+1:
1. All Wave N agents report completion
2. Run wave gate tests
3. Review deliverables
4. Approve transition to Wave N+1

---

## Success Criteria

### Per-Agent Criteria

**config-agent**:
- Configuration loads without errors
- All feature flags functional
- Environment templates updated

**structure-agent**:
- Structure extraction works on test documents
- Metadata size within limits
- No errors on diverse document types

**chunking-agent**:
- Smart chunking produces quality chunks
- Context metadata populated correctly
- Legacy fallback works

**metadata-agent**:
- Enhanced metadata stores successfully
- Compression achieves target ratios
- Backward compatibility maintained

**integration-agent**:
- End-to-end processing works
- Performance within targets
- Graceful degradation functional

**validation-agent**:
- All tests pass
- Performance report shows <20% overhead
- Search quality improved

---

**Agent Assignments Version**: 1.0
**Last Updated**: 2025-10-07

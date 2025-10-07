# Orchestration Plan: Docling Enhanced Mode

**Plan ID**: docling-enhanced-mode
**Created**: 2025-10-07
**Status**: Ready for execution
**Estimated Duration**: 3-4 waves (parallel execution)

## Executive Summary

Implement comprehensive document structure awareness and smart chunking using Docling's advanced features to significantly improve search quality. This enhancement enables hierarchical document understanding, table structure recognition, image classification, and intelligent chunking while maintaining <20% processing overhead.

### Success Criteria
- ✅ Document hierarchy (headings, sections, tables) extracted and stored
- ✅ Table structure recognized with accurate cell mapping
- ✅ Pictures classified by type (chart, diagram, photo, logo)
- ✅ Hybrid chunking respects document boundaries and structure
- ✅ Chunk metadata includes contextual information (parent headings, section paths)
- ✅ Processing time increase <20% vs baseline
- ✅ All features controlled by feature flags (enabled by default)
- ✅ Backward compatible with existing documents

### Feature Scope (All Included)
1. **Structure Extraction**: Headings, sections, hierarchy
2. **Table Recognition**: Structure extraction with TableFormer ACCURATE mode
3. **Picture Classification**: Image type detection (chart, diagram, photo, logo, signature)
4. **Smart Chunking**: Hybrid chunker with document-aware boundaries
5. **Metadata Enhancement**: Rich contextual metadata for all elements
6. **Search Enrichment**: Result context with structure information

## Architecture Overview

### Current State
```
File Upload → Docling (basic) → Pages + Text → ColPali Embeddings → ChromaDB
                                                                      └─> Basic metadata
```

### Enhanced State
```
File Upload → Docling (enhanced) → Structured Document
                                    ├─> Pages + Images → ColPali Visual Embeddings
                                    ├─> Smart Chunks → ColPali Text Embeddings
                                    ├─> Structure (headings, sections)
                                    ├─> Tables (structured data)
                                    └─> Picture Metadata (types, captions)
                                                 ↓
                                            ChromaDB
                                    ├─> Visual Collection (with rich metadata)
                                    └─> Text Collection (with contextual metadata)
```

## Agent Assignment Strategy

### Territorial Ownership Model

**Agent 1: Configuration Agent** (`config-agent`)
- **Territory**: Configuration files and feature flags
- **Files**:
  - `src/config/processing_config.py` (new/modified)
  - `.env.template`
  - `docker/.env.template`
- **No conflicts**: Only agent touching config files

**Agent 2: Structure Extraction Agent** (`structure-agent`)
- **Territory**: Document structure extraction from DoclingDocument
- **Files**:
  - `src/processing/structure_extractor.py` (new)
  - `src/processing/docling_parser.py` (modify - add structure extraction)
- **Dependencies**: Reads from config-agent contracts

**Agent 3: Smart Chunking Agent** (`chunking-agent`)
- **Territory**: Hybrid chunker integration
- **Files**:
  - `src/processing/smart_chunker.py` (new)
  - `src/processing/docling_parser.py` (modify - add chunking strategy)
- **Dependencies**: Reads from config-agent contracts

**Agent 4: Metadata Enhancement Agent** (`metadata-agent`)
- **Territory**: ChromaDB metadata schema and storage
- **Files**:
  - `src/storage/metadata_schema.py` (new)
  - `src/storage/chroma_client.py` (modify - enhance metadata storage)
  - `src/storage/compression.py` (modify - handle new fields)
- **Dependencies**: Consumes outputs from structure-agent and chunking-agent

**Agent 5: Pipeline Integration Agent** (`integration-agent`)
- **Territory**: Main processing pipeline orchestration
- **Files**:
  - `src/processing/processor.py` (modify - integrate all enhancements)
- **Dependencies**: Integrates all other agents' work

**Agent 6: Testing & Validation Agent** (`validation-agent`)
- **Territory**: Testing infrastructure and validation
- **Files**:
  - `src/processing/test_enhanced_processing.py` (new)
  - `src/storage/test_enhanced_metadata.py` (new)
  - `tests/test_end_to_end_enhanced.py` (new)
- **Dependencies**: Tests all integrated components

## Wave Execution Plan

### Wave 0: Foundation & Specifications (Prerequisite)

**Duration**: Sequential setup before parallel work begins
**Agents**: Orchestrator (you)

**Deliverables**:
1. Integration contracts written
2. Baseline metrics captured
3. Test document set prepared
4. Orchestration directory initialized

**Validation Gate**:
- ✅ All integration contracts reviewed and approved
- ✅ Baseline processing time and storage metrics recorded
- ✅ Test documents uploaded and processed with current system

---

### Wave 1: Configuration & Schemas (Foundation)

**Agents**: `config-agent`, `metadata-agent`
**Can run in parallel**: Yes (no file conflicts)

#### config-agent Tasks
1. Create `src/config/processing_config.py` with EnhancedModeConfig dataclass
2. Add feature flags: `ENABLE_TABLE_STRUCTURE`, `ENABLE_PICTURE_CLASSIFICATION`, `CHUNKING_STRATEGY`
3. Update `.env.template` with new variables (defaults: enabled)
4. Add configuration validation and logging

**Deliverables**:
- `src/config/processing_config.py` (150-200 lines)
- `.env.template` updated with 5-7 new variables
- Configuration contract fulfilled

**Validation**:
- ✅ Configuration loads without errors
- ✅ Feature flags default to enabled
- ✅ Environment variable parsing works

#### metadata-agent Tasks (Schema Definition)
1. Create `src/storage/metadata_schema.py` with schema definitions
2. Define StructureMetadata, ChunkContextMetadata, ElementMetadata classes
3. Add validation functions for schema compliance
4. Document metadata size targets (<50KB compressed)

**Deliverables**:
- `src/storage/metadata_schema.py` (200-250 lines)
- Schema documentation with examples
- Metadata schema contract fulfilled

**Validation**:
- ✅ Schema classes import and instantiate correctly
- ✅ Validation functions work as expected
- ✅ Schema aligns with ChromaDB constraints

**Integration Points**:
- Config provides settings to structure/chunking agents
- Metadata schema consumed by storage and processing agents

**Synchronization Gate**: Both agents must complete before Wave 2

---

### Wave 2: Core Feature Implementation (Parallel)

**Agents**: `structure-agent`, `chunking-agent`
**Can run in parallel**: Yes (different files, no conflicts)

#### structure-agent Tasks
1. Create `src/processing/structure_extractor.py`
2. Implement `extract_document_structure()` function
3. Extract headings with hierarchy levels
4. Extract tables with structure and captions
5. Extract pictures with classification metadata
6. Update `docling_parser.py` PdfPipelineOptions (enable table structure, picture classification)
7. Integrate structure extraction into `_parse_with_docling()`

**Deliverables**:
- `src/processing/structure_extractor.py` (300-400 lines)
- Modified `docling_parser.py` (+50-100 lines)
- Structure extraction contract fulfilled

**Validation**:
- ✅ Structure extractor handles DoclingDocument correctly
- ✅ Headings extracted with proper hierarchy
- ✅ Tables extracted with structure
- ✅ Pictures classified by type
- ✅ No errors on test document set

#### chunking-agent Tasks
1. Create `src/processing/smart_chunker.py`
2. Implement `SmartChunker` class wrapping HybridChunker
3. Add tokenizer initialization (auto-detect from config)
4. Implement `chunk_document()` with context extraction
5. Add legacy chunker wrapper for backward compatibility
6. Update `docling_parser.py` to support chunking strategy selection
7. Implement chunk metadata enrichment (parent headings, section paths)

**Deliverables**:
- `src/processing/smart_chunker.py` (250-350 lines)
- Modified `docling_parser.py` (+80-120 lines)
- Smart chunking contract fulfilled

**Validation**:
- ✅ HybridChunker initializes correctly
- ✅ Chunks respect document boundaries
- ✅ Context metadata populated accurately
- ✅ Legacy chunking still works
- ✅ No tokenization errors

**Integration Points**:
- Both agents read configuration from config-agent
- Both agents produce data conforming to metadata-agent schemas
- No direct dependencies between structure and chunking agents

**Synchronization Gate**: Both agents must complete and pass validation before Wave 3

---

### Wave 3: Storage & Pipeline Integration

**Agents**: `metadata-agent`, `integration-agent`
**Dependencies**: Wave 2 must complete first

#### metadata-agent Tasks (Storage Implementation)
1. Update `src/storage/chroma_client.py` to accept enhanced metadata
2. Modify `add_visual_embedding()` to store structure metadata
3. Modify `add_text_embedding()` to store chunk context
4. Update `src/storage/compression.py` to handle new fields efficiently
5. Add metadata validation before storage
6. Test storage round-trip with enhanced metadata

**Deliverables**:
- Modified `chroma_client.py` (+100-150 lines)
- Modified `compression.py` (+50-80 lines)
- Storage contract fulfilled

**Validation**:
- ✅ Enhanced metadata stores successfully
- ✅ Metadata retrieval works correctly
- ✅ Compression maintains <50KB target
- ✅ No data loss in round-trip
- ✅ Backward compatible with old metadata format

#### integration-agent Tasks
1. Update `src/processing/processor.py` to use EnhancedModeConfig
2. Initialize SmartChunker based on configuration
3. Call structure extraction in processing pipeline
4. Pass enhanced metadata to storage layer
5. Add progress tracking for new processing steps
6. Maintain backward compatibility mode
7. Add logging for enhancement features

**Deliverables**:
- Modified `processor.py` (+150-200 lines)
- Processing pipeline contract fulfilled

**Validation**:
- ✅ End-to-end processing works with enhancements enabled
- ✅ Processing completes without errors
- ✅ All metadata stored correctly
- ✅ Processing time increase <20%
- ✅ Legacy mode still functional

**Integration Points**:
- integration-agent consumes structure and chunking outputs
- integration-agent uses metadata-agent storage APIs
- All integration contracts validated

**Synchronization Gate**: Both agents complete and end-to-end test passes

---

### Wave 4: Testing, Validation & Documentation

**Agents**: `validation-agent`
**Dependencies**: Wave 3 must complete

#### validation-agent Tasks
1. Create `src/processing/test_enhanced_processing.py`
   - Test structure extraction accuracy
   - Test smart chunking quality
   - Test feature flag combinations
2. Create `src/storage/test_enhanced_metadata.py`
   - Test metadata storage/retrieval
   - Test compression efficiency
   - Test schema validation
3. Create `tests/test_end_to_end_enhanced.py`
   - Full pipeline test with real documents
   - Performance benchmarking
   - Search quality comparison
4. Run comprehensive validation suite
5. Generate performance comparison report
6. Update documentation with new features

**Deliverables**:
- `test_enhanced_processing.py` (300-400 lines)
- `test_enhanced_metadata.py` (200-300 lines)
- `test_end_to_end_enhanced.py` (250-350 lines)
- Performance report (markdown)
- Updated documentation

**Validation**:
- ✅ All tests pass
- ✅ Performance targets met (<20% slowdown)
- ✅ Storage efficiency maintained
- ✅ Search quality improved (measurable)
- ✅ No regressions in existing functionality

**Final Gate**: All validation tests pass, performance acceptable

---

## Integration Contracts

See `integration-contracts/` directory for detailed specifications:
1. `configuration-contract.md` - Config schema and feature flags
2. `structure-extraction-contract.md` - Structure data format
3. `chunking-contract.md` - Chunking interface and metadata
4. `metadata-storage-contract.md` - ChromaDB metadata schema
5. `processing-pipeline-contract.md` - Pipeline integration points

## Risk Mitigation Strategies

### Conflict Prevention
- **Territorial ownership**: Each agent owns specific files
- **New files preferred**: Minimize shared file modifications
- **Interface-first**: Contracts written before implementation
- **Feature flags**: Enable/disable features independently

### Quality Assurance
- **Progressive validation**: Tests after each wave
- **Performance gates**: <20% slowdown enforced
- **Backward compatibility**: Legacy mode always functional
- **Rollback capability**: Feature flags allow instant disable

### Failure Recovery
- **Wave gates**: Failures block next wave, not previous work
- **Independent features**: Table structure failure doesn't break chunking
- **Graceful degradation**: Features fail independently
- **Comprehensive logging**: Debug information at all stages

## Communication Protocol

### Status Broadcasting
Each agent must report:
- Wave completion status
- Deliverable locations (file paths)
- Test results (pass/fail)
- Performance metrics
- Integration issues

### Contract Compliance
Each agent must validate:
- Input data matches contracts
- Output data matches contracts
- Integration tests pass
- Performance targets met

### Handoff Procedure
Wave N+1 agents must:
1. Verify Wave N completion
2. Review Wave N deliverables
3. Validate integration contracts
4. Report any issues before starting

## Success Metrics

### Performance Targets
- Processing time increase: <20% (baseline + enhancement)
- Storage overhead: <30% (metadata size increase)
- Search latency: No change (still <300ms)
- Memory usage: <150% (acceptable for enhancement)

### Quality Targets
- Structure extraction accuracy: >95% (headings, tables)
- Picture classification accuracy: >90% (when present)
- Chunk boundary quality: Measurably better than word-based
- Metadata completeness: 100% (all available fields populated)

### Functional Targets
- All feature flags functional
- Backward compatibility: 100% (old docs still work)
- Test coverage: >90% for new code
- Documentation: Complete for all new features

## Post-Implementation

### Deployment Strategy
1. Deploy with feature flags enabled (default)
2. Monitor processing performance
3. Monitor storage growth
4. Validate search quality improvements
5. Collect user feedback

### Monitoring Points
- Processing time per document
- Storage size per document
- Feature utilization (which features used most)
- Error rates by feature
- Search quality metrics

### Future Enhancements
- Code block enrichment (if processing technical docs)
- Formula extraction (if processing scientific papers)
- Picture descriptions (if captioning valuable)
- Chart data extraction (structured chart data)
- Citation extraction (academic papers)

---

## Execution Readiness

**Prerequisites Complete**: ☐
**Integration Contracts Written**: ☐
**Test Documents Prepared**: ☐
**Baseline Metrics Captured**: ☐
**Agent Assignments Confirmed**: ☐

**Ready to Execute**: ☐ (check when all prerequisites complete)

---

**Orchestration Plan Version**: 1.0
**Last Updated**: 2025-10-07
**Next Review**: After Wave 2 completion

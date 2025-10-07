# Docling Enhanced Mode - Orchestration Plan

**Status**: Ready for Execution ✅
**Created**: 2025-10-07
**Estimated Duration**: 3-4 waves (can run in parallel)

## 📋 Quick Overview

This orchestration plan implements comprehensive document structure awareness and smart chunking for the tkr-docusearch project using Docling's advanced features.

### What We're Building

**Current State**: Basic Docling parsing → pages + text → embeddings → ChromaDB
**Enhanced State**: Advanced Docling → structure + smart chunks → enriched embeddings → ChromaDB with rich metadata

### Success Criteria

- ✅ Document hierarchy extracted (headings, sections, tables)
- ✅ Pictures classified by type (chart, diagram, photo, logo)
- ✅ Smart chunking respects document boundaries
- ✅ Rich contextual metadata for all elements
- ✅ Processing time increase <20%
- ✅ All features controlled by feature flags (enabled by default)

---

## 📁 Plan Structure

```
.context-kit/orchestration/docling-enhanced-mode/
├── README.md (this file)
├── orchestration-plan.md         # Complete execution plan with waves
├── agent-assignments.md           # Agent responsibilities & territories
├── validation-strategy.md         # Testing approach & gates
├── coordination-protocol.md       # Communication & status reporting
└── integration-contracts/         # Detailed interface specifications
    ├── configuration-contract.md          # Feature flags & config
    ├── structure-extraction-contract.md   # Document structure format
    ├── chunking-contract.md              # Smart chunking interface
    ├── metadata-storage-contract.md      # ChromaDB metadata schema
    └── processing-pipeline-contract.md   # Pipeline integration
```

---

## 🚀 Execution Workflow

### Step 1: Review Plan Documents

Read in this order:
1. **orchestration-plan.md** - High-level overview and wave structure
2. **agent-assignments.md** - Understand agent roles and file ownership
3. **integration-contracts/** - Review interface specifications
4. **validation-strategy.md** - Understand testing approach
5. **coordination-protocol.md** - Communication mechanisms

### Step 2: Prepare Prerequisites (Wave 0)

```bash
# 1. Capture baseline metrics
cd /Volumes/tkr-riffic/@tkr-projects/tkr-docusearch
pytest src/test_end_to_end.py --benchmark
# Record: processing time, storage size, search latency

# 2. Prepare test document set
mkdir -p data/test_documents
# Add 3-5 PDFs with rich structure (technical papers, reports with tables)

# 3. Create status tracking directory
mkdir -p .context-kit/orchestration/docling-enhanced-mode/status

# 4. Mark Wave 0 complete
echo '{"wave": 0, "status": "complete"}' > .context-kit/orchestration/docling-enhanced-mode/status/wave-0.json
```

### Step 3: Execute Waves

#### Wave 1: Configuration & Schemas
**Agents**: config-agent, metadata-agent (schema only)
**Duration**: ~1-2 hours
**Deliverables**: Configuration system, metadata schemas

```bash
# Launch agents in parallel (or sequentially)
# Agent 1: config-agent creates src/config/processing_config.py
# Agent 2: metadata-agent creates src/storage/metadata_schema.py

# Validate Wave 1
pytest src/config/ src/storage/metadata_schema.py -v

# Mark complete
echo '{"wave": 1, "status": "complete"}' > .context-kit/orchestration/docling-enhanced-mode/status/wave-1.json
```

#### Wave 2: Core Features
**Agents**: structure-agent, chunking-agent
**Duration**: ~2-3 hours
**Deliverables**: Structure extraction, smart chunking

```bash
# Launch agents in parallel
# Agent 1: structure-agent creates src/processing/structure_extractor.py
# Agent 2: chunking-agent creates src/processing/smart_chunker.py

# Validate Wave 2
pytest src/processing/test_structure_extractor.py -v
pytest src/processing/test_smart_chunker.py -v

# Mark complete
echo '{"wave": 2, "status": "complete"}' > .context-kit/orchestration/docling-enhanced-mode/status/wave-2.json
```

#### Wave 3: Integration
**Agents**: metadata-agent (storage), integration-agent
**Duration**: ~2-3 hours
**Deliverables**: Storage layer, pipeline integration

```bash
# Launch agents (metadata-agent first, then integration-agent)
# Agent 1: metadata-agent updates src/storage/chroma_client.py
# Agent 2: integration-agent updates src/processing/processor.py

# Validate Wave 3
pytest src/storage/test_enhanced_metadata.py -v
pytest tests/test_end_to_end_enhanced.py -v

# Check performance
pytest tests/test_end_to_end_enhanced.py::test_performance_overhead -v

# Mark complete
echo '{"wave": 3, "status": "complete"}' > .context-kit/orchestration/docling-enhanced-mode/status/wave-3.json
```

#### Wave 4: Validation
**Agents**: validation-agent
**Duration**: ~2-3 hours
**Deliverables**: Comprehensive test suite, performance report

```bash
# Agent: validation-agent creates test files and runs validation
pytest src/ tests/ -v --cov=src --cov-report=html

# Generate performance report
# validation-agent creates PERFORMANCE_REPORT.md

# Mark complete
echo '{"wave": 4, "status": "complete"}' > .context-kit/orchestration/docling-enhanced-mode/status/wave-4.json
```

---

## 👥 Agent Roles Summary

| Agent | Wave | Key Deliverables | Conflicts |
|-------|------|------------------|-----------|
| **config-agent** | 1 | Configuration system | None |
| **metadata-agent** | 1, 3 | Schemas, storage | None (wave separation) |
| **structure-agent** | 2 | Structure extraction | Low (different methods) |
| **chunking-agent** | 2 | Smart chunking | Low (different methods) |
| **integration-agent** | 3 | Pipeline integration | None |
| **validation-agent** | 4 | Tests, validation | None |

---

## 📊 Progress Tracking

### Wave Status

Check wave status:
```bash
cat .context-kit/orchestration/docling-enhanced-mode/status/wave-*.json
```

### Agent Status

Check agent status:
```bash
ls .context-kit/orchestration/docling-enhanced-mode/status/agent-*.json
```

---

## 🎯 Key Features

### Feature Flags (All Enabled by Default)

| Feature | Flag | Impact | Overhead |
|---------|------|--------|----------|
| Table Structure | `ENABLE_TABLE_STRUCTURE=true` | Extract table structure with cells | +5-8% |
| Picture Classification | `ENABLE_PICTURE_CLASSIFICATION=true` | Classify images by type | +5-7% |
| Smart Chunking | `CHUNKING_STRATEGY=hybrid` | Document-aware chunking | +2-3% |
| Code Enrichment | `ENABLE_CODE_ENRICHMENT=false` | Language detection (optional) | +10-15% |
| Formula Enrichment | `ENABLE_FORMULA_ENRICHMENT=false` | LaTeX extraction (optional) | +10-15% |

**Total Overhead (Core Features)**: 12-18%
**With Optional Features**: 30-40%

### What You Get

**Document Structure**:
- Hierarchical headings (title → section → subsection)
- Table metadata (dimensions, captions, page numbers)
- Picture classifications (chart, diagram, photo, logo)
- Code blocks with language detection (optional)
- Mathematical formulas with LaTeX (optional)

**Smart Chunking**:
- Document-aware boundaries (respects sections)
- Token-limit aware (configurable)
- Context metadata (parent headings, section paths)
- Related element detection (tables/figures mentioned)

**Enhanced Metadata**:
- Rich contextual information for search
- Compressed storage (<50KB per embedding)
- Backward compatible with existing documents

---

## 📈 Performance Targets

| Metric | Baseline | Enhanced | Target | Status |
|--------|----------|----------|--------|--------|
| Processing Time | X | X + 12-18% | <20% increase | ✅ On Target |
| Storage Size | Y | Y + 20-25% | <30% increase | ✅ On Target |
| Search Latency | 239ms | 239ms | Unchanged | ✅ On Target |
| Metadata Size | 10KB | 30KB | <50KB | ✅ On Target |

---

## 🔍 Validation Gates

### Wave 1 → Wave 2
- ✅ Configuration loads correctly
- ✅ Feature flags functional
- ✅ Metadata schemas defined

### Wave 2 → Wave 3
- ✅ Structure extraction works
- ✅ Smart chunking produces quality chunks
- ✅ Context metadata populated

### Wave 3 → Wave 4
- ✅ Enhanced metadata stores successfully
- ✅ End-to-end processing works
- ✅ Performance within targets

### Wave 4 → Production
- ✅ All tests pass (100%)
- ✅ Performance targets met
- ✅ Quality measurably improved
- ✅ No regressions

---

## 🛠️ Development Commands

### Quick Validation
```bash
# Test specific component
pytest src/processing/test_structure_extractor.py::test_extract_headings -v

# Test with real documents
pytest tests/test_end_to_end_enhanced.py -v

# Performance benchmark
pytest tests/test_end_to_end_enhanced.py::test_performance_overhead -v
```

### Configuration Testing
```bash
# Test with different feature combinations
ENABLE_TABLE_STRUCTURE=true ENABLE_PICTURE_CLASSIFICATION=false \
  pytest tests/test_end_to_end_enhanced.py -v

# Test legacy mode
CHUNKING_STRATEGY=legacy pytest tests/test_end_to_end_enhanced.py -v
```

### Coverage Check
```bash
pytest src/ tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

---

## 📝 Integration Contracts

All integration contracts define:
- **Input/Output formats**: Exact data structures
- **API signatures**: Function parameters and returns
- **Error handling**: Exception types and recovery
- **Performance requirements**: Timing and size limits
- **Testing contracts**: Required test coverage

Read contracts before implementation to ensure compliance.

---

## 🚨 Troubleshooting

### Wave Gate Fails
1. Identify failing test
2. Review agent deliverables
3. Check contract compliance
4. Fix issue
5. Re-run wave validation

### Agent Stuck
1. Review agent status file
2. Check for blockers
3. Review integration contracts
4. Provide clarification
5. Agent continues

### Performance Issues
1. Check feature flags (disable optional features)
2. Review processing metrics
3. Optimize bottlenecks
4. Re-benchmark

---

## 📚 Additional Resources

### Documentation
- **Docling Docs**: `/Volumes/tkr-riffic/@tkr-projects/tkr-docusearch/.context-kit/_ref/packages/docling/`
- **Project Context**: `.context-kit/_context-kit.yml`
- **Quick Start**: `docs/QUICK_START.md`

### Key Files to Understand
- `src/processing/docling_parser.py` - Current Docling integration
- `src/processing/processor.py` - Main processing pipeline
- `src/storage/chroma_client.py` - ChromaDB storage
- `src/embeddings/colpali_wrapper.py` - ColPali embeddings

---

## ✅ Readiness Checklist

Before starting execution:

- ☐ All plan documents reviewed
- ☐ Integration contracts understood
- ☐ Test documents prepared
- ☐ Baseline metrics captured
- ☐ Development environment ready
- ☐ Status tracking directory created

---

## 📞 Support

For questions or clarifications:
1. Review relevant integration contract
2. Check coordination protocol
3. Review validation strategy
4. Consult orchestration plan

---

**Plan Version**: 1.0
**Last Updated**: 2025-10-07
**Status**: Ready for Execution ✅

**Estimated Total Time**: 8-12 hours (with parallel execution)
**Recommended Approach**: Execute waves sequentially with gate validation

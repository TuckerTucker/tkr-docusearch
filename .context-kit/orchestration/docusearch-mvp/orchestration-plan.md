# Orchestration Plan: DocuSearch MVP Implementation

**Feature Goal**: Local document processing and semantic search system with copyparty, docling, ColNomic 7B, and ChromaDB

**Max Agents**: 6 parallel agents
**Timeline**: 2-3 weeks across 4 waves
**Architecture**: 3 Docker containers (copyparty, chromadb, processing-worker) on M1 MacBook Pro

---

## Executive Summary

This orchestration plan deploys 6 specialized agents across 4 waves to implement the DocuSearch MVP. The plan maximizes parallelism through:
- **Territorial ownership**: Each agent owns specific directories with zero overlap
- **Interface-first development**: Contracts defined before implementation
- **Progressive validation**: Quality gates between waves ensure integration
- **Wave synchronization**: Clear dependencies prevent conflicts

**Key Innovation**: Multi-vector embedding storage with two-stage search (representative vectors + late interaction re-ranking) using ColNomic 7B exclusively.

---

## Component Analysis & Parallelization Strategy

### Identified Components (Independent Development Tracks)

1. **Docker Infrastructure** (`docker/`)
   - docker-compose.yml, Dockerfiles, .env configuration
   - Container orchestration and networking
   - **Agent**: `infrastructure-agent`

2. **ChromaDB Integration** (`src/storage/`)
   - Client wrapper, collection management
   - Multi-vector storage strategy (CLS token + metadata)
   - **Agent**: `storage-agent`

3. **ColPali Engine Wrapper** (`src/embeddings/`)
   - ColQwen2_5 model loading and inference
   - Multi-vector embedding generation
   - Late interaction scoring
   - **Agent**: `embedding-agent`

4. **Document Processing Pipeline** (`src/processing/`)
   - Docling parser integration
   - Visual + text processing workflows
   - Processing worker main loop
   - **Agent**: `processing-agent`

5. **Search System** (`src/search/`)
   - Two-stage search implementation
   - Result merging and ranking
   - Query embedding
   - **Agent**: `search-agent`

6. **Web UI & Event Hooks** (`src/ui/`, `data/copyparty/`)
   - Search page (HTML/JS)
   - Copyparty event hooks
   - Processing status dashboard
   - **Agent**: `ui-agent`

---

## Integration Points & Interface Contracts

### Critical Integration Points

1. **Storage Contract** (`integration-contracts/storage-interface.md`)
   - ChromaDB collection schema
   - Multi-vector storage format
   - Metadata structure

2. **Embedding Contract** (`integration-contracts/embedding-interface.md`)
   - ColPali model initialization
   - Embedding generation API
   - Multi-vector scoring API

3. **Processing Contract** (`integration-contracts/processing-interface.md`)
   - Document processing workflow
   - Event hook trigger format
   - Processing status messages

4. **Search Contract** (`integration-contracts/search-interface.md`)
   - Query request/response format
   - Two-stage search pipeline
   - Result ranking algorithm

5. **Configuration Contract** (`integration-contracts/config-interface.md`)
   - Environment variables
   - Model paths and cache directories
   - Service endpoints

---

## Wave-Based Execution Plan

### Wave 1: Foundation & Contracts (Days 1-2)
**Objective**: Establish infrastructure and define all integration contracts

**Agents**: All 6 agents (contract definition phase)

#### Tasks

**infrastructure-agent**
- [ ] Create project directory structure
- [ ] Define docker-compose.yml skeleton
- [ ] Create Dockerfiles (copyparty, processing-worker)
- [ ] Define .env configuration template
- **Deliverable**: `docker/` directory with buildable containers

**storage-agent**
- [ ] Define ChromaDB collection schema (visual_collection, text_collection)
- [ ] Document multi-vector storage format (CLS token + base64 metadata)
- [ ] Create storage interface contract
- **Deliverable**: `integration-contracts/storage-interface.md`

**embedding-agent**
- [ ] Define ColPali model loading interface
- [ ] Document multi-vector embedding format (shape, dtype)
- [ ] Specify late interaction scoring API
- **Deliverable**: `integration-contracts/embedding-interface.md`

**processing-agent**
- [ ] Define document processing workflow stages
- [ ] Document event hook payload format
- [ ] Specify processing status messages
- **Deliverable**: `integration-contracts/processing-interface.md`

**search-agent**
- [ ] Define query request/response schema
- [ ] Document two-stage search pipeline
- [ ] Specify result ranking algorithm
- **Deliverable**: `integration-contracts/search-interface.md`

**ui-agent**
- [ ] Define search page UI contract (query form, results display)
- [ ] Document event hook integration points
- [ ] Specify status dashboard data format
- **Deliverable**: `integration-contracts/ui-interface.md`

#### Synchronization Gate: Wave 1 → Wave 2
- [ ] All integration contracts reviewed and approved
- [ ] Docker containers build successfully on M1 (ARM64)
- [ ] Directory structure matches territorial assignments
- [ ] No overlapping file ownership conflicts

---

### Wave 2: Core Components (Days 3-7)
**Objective**: Implement independent components with contract compliance

**Agents**: All 6 agents (parallel implementation)

#### Tasks

**infrastructure-agent** → `docker/`
- [ ] Complete docker-compose.yml with all 3 services
- [ ] Add health checks and resource limits
- [ ] Configure volume mounts (uploads, models, chroma_db)
- [ ] Test container orchestration (start, stop, logs)
- [ ] **Risk**: Verify PyTorch MPS availability in container
- [ ] **Risk**: Pre-download ColNomic 7B model (14GB cache)
- **Deliverable**: Working Docker environment, all services healthy

**storage-agent** → `src/storage/`
- [ ] Implement ChromaDB client wrapper (`chroma_client.py`)
- [ ] Create collection initialization logic
- [ ] Implement multi-vector storage (CLS token + base64 metadata)
- [ ] Add metadata validation and error handling
- [ ] Write unit tests for storage operations
- **Deliverable**: `ChromaClient` class with `add_embeddings()`, `search()` methods

**embedding-agent** → `src/embeddings/`
- [ ] Implement ColPali engine wrapper (`colpali_wrapper.py`)
- [ ] Load ColQwen2_5 model with MPS device mapping
- [ ] Implement `embed_images()` for visual processing
- [ ] Implement `embed_text()` for text processing
- [ ] Implement `score_multi_vector()` for late interaction
- [ ] Add FP16/INT8 quantization support
- [ ] Write unit tests with mock data
- **Deliverable**: `ColPaliEngine` class with embedding + scoring APIs

**processing-agent** → `src/processing/`
- [ ] Implement Docling parser wrapper (`docling_parser.py`)
- [ ] Create visual processing pipeline (`visual_processor.py`)
- [ ] Build page rendering logic (PDF → images)
- [ ] Integrate with embedding-agent API (mock for now)
- [ ] Integrate with storage-agent API (mock for now)
- [ ] Add error handling for corrupted documents
- [ ] Write unit tests with sample PDFs
- **Deliverable**: `DocumentProcessor` class with `process_visual()` method

**search-agent** → `src/search/`
- [ ] Implement Stage 1 search (representative vector retrieval)
- [ ] Implement Stage 2 search (late interaction re-ranking)
- [ ] Create result merging logic (visual + text collections)
- [ ] Add result ranking algorithm (MaxSim scores)
- [ ] Integrate with storage-agent API (mock for now)
- [ ] Integrate with embedding-agent API (mock for now)
- [ ] Write unit tests with mock embeddings
- **Deliverable**: `SearchEngine` class with `query()` method

**ui-agent** → `src/ui/`, `data/copyparty/`
- [ ] Create search page HTML (`www/search.html`)
- [ ] Implement search page JS (`www/search.js`)
- [ ] Build query form with input validation
- [ ] Create results display component
- [ ] Add copyparty event hook skeleton (`hooks/on_upload.py`)
- [ ] Create status dashboard mockup
- **Deliverable**: Functional search UI (with mock data)

#### Synchronization Gate: Wave 2 → Wave 3
- [ ] All components pass unit tests in isolation
- [ ] Mock interfaces match integration contracts exactly
- [ ] Docker environment runs without errors
- [ ] ColNomic 7B model loaded successfully with MPS
- [ ] No import errors or missing dependencies
- [ ] Code review: Each agent validates their dependencies

---

### Wave 3: Integration & End-to-End (Days 8-12)
**Objective**: Replace mocks with real integrations, test full workflows

**Agents**: 4 agents (focused integration work)

#### Tasks

**processing-agent** → `src/processing/`
- [ ] Replace embedding mock with real ColPali engine
- [ ] Replace storage mock with real ChromaDB client
- [ ] Implement text processing pipeline (`text_processor.py`)
- [ ] Add text chunking strategy (250 words avg)
- [ ] Create unified processor (`processor.py`) for hybrid workflow
- [ ] Implement processing worker main loop (`worker.py`)
- [ ] Add file monitoring with event triggers
- [ ] **Integration Test**: Upload sample PDF → verify embeddings in ChromaDB
- **Deliverable**: End-to-end processing pipeline (visual + text)

**search-agent** → `src/search/`
- [ ] Replace embedding mock with real ColPali scoring
- [ ] Replace storage mock with real ChromaDB queries
- [ ] Implement hybrid search (merge visual + text results)
- [ ] Optimize two-stage pipeline performance
- [ ] Add query logging for analysis
- [ ] **Integration Test**: Query → verify results from real embeddings
- **Deliverable**: Fully functional two-stage search system

**ui-agent** → `src/ui/`, `data/copyparty/`
- [ ] Connect search page to real search-agent API
- [ ] Implement copyparty event hook with processing trigger
- [ ] Add processing status polling
- [ ] Create loading states and error messages
- [ ] Build result preview modal
- [ ] **Integration Test**: Upload via UI → process → search → view results
- **Deliverable**: Complete user workflow (upload → search)

**infrastructure-agent** → `docker/`, `scripts/`
- [ ] Add inter-container communication configuration
- [ ] Create setup script (`scripts/setup.sh`)
- [ ] Add monitoring and logging configuration
- [ ] Create troubleshooting documentation
- [ ] Test full stack startup/shutdown
- [ ] **Integration Test**: Full environment health check
- **Deliverable**: Production-ready Docker orchestration

#### Synchronization Gate: Wave 3 → Wave 4
- [ ] End-to-end visual search works (upload → embed → search → results)
- [ ] ChromaDB contains valid multi-vector embeddings
- [ ] Two-stage search returns relevant results (<500ms)
- [ ] UI shows results with thumbnails and snippets
- [ ] Processing worker handles errors gracefully
- [ ] All integration tests pass
- [ ] Performance metrics meet targets (see validation-strategy.md)

---

### Wave 4: Production Polish & Scale Testing (Days 13-15)
**Objective**: Add production features, optimize performance, validate scalability

**Agents**: 3 agents (enhancement work)

#### Tasks

**search-agent** → `src/search/`
- [ ] Add search filters (date range, document type, folder)
- [ ] Implement pagination for large result sets
- [ ] Add caching for frequent queries
- [ ] Optimize late interaction re-ranking
- [ ] Add fallback keyword search
- **Deliverable**: Production-ready search with filters

**ui-agent** → `src/ui/`
- [ ] Enhance preview modal with highlights
- [ ] Add batch upload queue visualization
- [ ] Create processing status dashboard
- [ ] Implement real-time updates (polling/websockets)
- [ ] Add error recovery UI flows
- **Deliverable**: Polished user interface

**processing-agent** → `src/processing/`
- [ ] Implement processing queue (Redis or file-based)
- [ ] Add batch processing logic
- [ ] Implement INT8 quantization toggle
- [ ] Add processing metrics logging
- [ ] Create error recovery procedures
- **Deliverable**: Scalable processing system

#### Synchronization Gate: Wave 4 → Production Release
- [ ] Batch upload test: 100 documents processed successfully
- [ ] Search latency <500ms for p95
- [ ] Processing speed meets targets (FP16: 6s/page, INT8: 3s/page)
- [ ] Storage efficiency verified (embeddings + metadata < 3x original)
- [ ] User acceptance test: Upload → Search → Find target document
- [ ] All documentation complete (setup, usage, troubleshooting)
- [ ] Health checks pass for all services
- [ ] Performance metrics logged and analyzed

---

## Territorial Ownership (Zero Conflict Guarantee)

### Directory Assignments

| Agent | Owned Directories | Created Files | Read-Only Access |
|-------|------------------|---------------|------------------|
| **infrastructure-agent** | `docker/`, `scripts/`, `.env` | Dockerfiles, docker-compose.yml, setup scripts | All integration contracts |
| **storage-agent** | `src/storage/` | chroma_client.py, collection_manager.py | integration-contracts/embedding-interface.md |
| **embedding-agent** | `src/embeddings/` | colpali_wrapper.py, model_loader.py | integration-contracts/storage-interface.md |
| **processing-agent** | `src/processing/` | processor.py, worker.py, docling_parser.py, visual_processor.py, text_processor.py | integration-contracts/embedding-interface.md, storage-interface.md |
| **search-agent** | `src/search/` | search_engine.py, result_ranker.py | integration-contracts/embedding-interface.md, storage-interface.md |
| **ui-agent** | `src/ui/`, `data/copyparty/` | search.html, search.js, on_upload.py, status_dashboard.html | integration-contracts/search-interface.md, processing-interface.md |

### Conflict Prevention Rules

1. **No shared file writes**: Each agent owns exclusive write access to their directories
2. **Integration via contracts**: Agents communicate through documented interfaces only
3. **Mock-first development**: Use mocks until integration wave to avoid dependencies
4. **Contract-driven testing**: Unit tests validate contract compliance
5. **Code review gate**: Consumer agents review provider APIs before integration

---

## Dependency Graph

```
Wave 1: All agents define contracts (no dependencies)
  ↓
Wave 2: All agents implement in isolation (mock dependencies)
  ├── infrastructure-agent: Docker environment
  ├── storage-agent: ChromaDB client (independent)
  ├── embedding-agent: ColPali wrapper (independent)
  ├── processing-agent: Document processor (mocks: embedding + storage)
  ├── search-agent: Search engine (mocks: embedding + storage)
  └── ui-agent: Web UI (mocks: search + processing)
  ↓
Wave 3: Integration (replace mocks with real implementations)
  ├── processing-agent depends on: embedding-agent + storage-agent
  ├── search-agent depends on: embedding-agent + storage-agent
  ├── ui-agent depends on: search-agent + processing-agent
  └── infrastructure-agent: orchestrates all services
  ↓
Wave 4: Enhancement (all dependencies resolved)
  ├── search-agent: add filters and optimizations
  ├── ui-agent: add advanced features
  └── processing-agent: add queue and scaling
```

---

## Risk Mitigation Strategy

### High-Risk Items (Addressed in Wave 2)

1. **M1 Compatibility** (infrastructure-agent)
   - **Risk**: PyTorch MPS not available in Docker
   - **Mitigation**: Test in Wave 2, fallback to CPU if needed
   - **Validation**: `torch.backends.mps.is_available()` must return True

2. **Model Download** (infrastructure-agent)
   - **Risk**: ColNomic 7B download timeout (14GB)
   - **Mitigation**: Pre-cache model in setup script
   - **Validation**: Model loads in <30s from cache

3. **Multi-Vector Storage** (storage-agent)
   - **Risk**: ChromaDB metadata size limits
   - **Mitigation**: Test with real embeddings in Wave 2
   - **Validation**: Store 100-token sequence in metadata successfully

4. **Memory Overflow** (embedding-agent)
   - **Risk**: ColNomic 7B crashes with 8GB RAM
   - **Mitigation**: Implement INT8 quantization option
   - **Validation**: Container stays under 8GB memory limit

### Medium-Risk Items (Monitored in Wave 3)

5. **Search Performance** (search-agent)
   - **Risk**: Late interaction re-ranking too slow
   - **Mitigation**: Profile and optimize MaxSim computation
   - **Validation**: Two-stage search completes in <500ms

6. **Processing Backlog** (processing-agent)
   - **Risk**: 100 document upload creates backlog
   - **Mitigation**: Implement queue in Wave 4
   - **Validation**: Queue drains within 2 hours (FP16) or 1 hour (INT8)

---

## Success Metrics

### Wave 2 Targets (Component Completion)
- All unit tests pass (>90% coverage per component)
- Docker environment starts without errors
- Model loads successfully with MPS acceleration
- No integration contract violations

### Wave 3 Targets (Integration Success)
- End-to-end visual search works
- Sample PDF processed in <2 minutes (10 pages)
- Search returns relevant results in top 5
- UI displays results with correct metadata

### Wave 4 Targets (Production Readiness)
- Batch processing: 100 PDFs in <2 hours (FP16) or <1 hour (INT8)
- Search latency: p95 <500ms
- Storage efficiency: embeddings <3x original file size
- Uptime: 99% (health checks pass continuously)

---

## Agent Communication Protocol

### Status Broadcasting

Each agent must publish status after completing each task:

```json
{
  "agent": "processing-agent",
  "wave": 2,
  "task": "Implement visual processing pipeline",
  "status": "completed",
  "timestamp": "2025-10-06T15:30:00Z",
  "deliverables": ["src/processing/visual_processor.py"],
  "contracts_validated": ["embedding-interface.md", "storage-interface.md"],
  "next_task": "Implement text processing pipeline"
}
```

### Integration Testing

Before Wave 3 integration, each consumer agent must:
1. Review provider agent's API documentation
2. Validate contract compliance with unit tests
3. Test with real provider implementation (not mocks)
4. Report any contract violations for resolution

### Failure Recovery

If an agent encounters blocking issues:
1. **Document the blocker** (what, why, impact)
2. **Notify dependent agents** (who needs to know)
3. **Propose workaround** (temporary solution to unblock)
4. **Update timeline** (how much delay expected)

Example:
```
BLOCKER: ChromaDB metadata size limit (2MB) insufficient for 100-token embeddings
IMPACT: Blocks Wave 3 integration for storage-agent + processing-agent
WORKAROUND: Compress embeddings with gzip before base64 encoding (reduces 4x)
TIMELINE: +1 day to implement compression layer
```

---

## Next Steps

1. **Review this plan** with all stakeholders
2. **Create integration contracts** (all agents participate)
3. **Assign agents** to team members or AI agents
4. **Kickoff Wave 1** (contract definition phase)
5. **Daily standups** (async status broadcasts)
6. **Gate reviews** after each wave (validation before proceeding)

---

## Appendix: File Structure Preview

```
tkr-docusearch/
├── docker/
│   ├── docker-compose.yml              # infrastructure-agent
│   ├── Dockerfile.copyparty            # infrastructure-agent
│   ├── Dockerfile.processing-worker    # infrastructure-agent
│   └── .env                            # infrastructure-agent
│
├── src/
│   ├── storage/
│   │   ├── chroma_client.py           # storage-agent
│   │   └── collection_manager.py      # storage-agent
│   │
│   ├── embeddings/
│   │   ├── colpali_wrapper.py         # embedding-agent
│   │   └── model_loader.py            # embedding-agent
│   │
│   ├── processing/
│   │   ├── processor.py               # processing-agent (main)
│   │   ├── worker.py                  # processing-agent
│   │   ├── docling_parser.py          # processing-agent
│   │   ├── visual_processor.py        # processing-agent
│   │   └── text_processor.py          # processing-agent
│   │
│   ├── search/
│   │   ├── search_engine.py           # search-agent
│   │   └── result_ranker.py           # search-agent
│   │
│   └── ui/
│       ├── search.html                # ui-agent
│       ├── search.js                  # ui-agent
│       └── status_dashboard.html      # ui-agent
│
├── data/
│   └── copyparty/
│       ├── hooks/
│       │   └── on_upload.py           # ui-agent
│       └── www/                       # ui-agent (served by copyparty)
│
├── scripts/
│   └── setup.sh                       # infrastructure-agent
│
└── .context-kit/
    └── orchestration/
        └── docusearch-mvp/
            ├── orchestration-plan.md           # This file
            ├── agent-assignments.md
            ├── validation-strategy.md
            ├── coordination-protocol.md
            └── integration-contracts/
                ├── storage-interface.md
                ├── embedding-interface.md
                ├── processing-interface.md
                ├── search-interface.md
                ├── config-interface.md
                └── ui-interface.md
```

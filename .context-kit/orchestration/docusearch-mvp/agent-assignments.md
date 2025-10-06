# Agent Assignments & Territorial Ownership

**Purpose**: Define clear ownership boundaries to prevent conflicts and enable parallel development

**Principle**: Each agent owns exclusive write access to their directories. Integration happens through documented contracts only.

---

## Agent Roster

| Agent ID | Specialization | Primary Output | Team Member |
|----------|---------------|----------------|-------------|
| **infrastructure-agent** | Docker orchestration, DevOps | Runnable containers | TBD |
| **storage-agent** | ChromaDB integration | Storage client library | TBD |
| **embedding-agent** | ColPali engine | Embedding generation | TBD |
| **processing-agent** | Document processing | Processing pipeline | TBD |
| **search-agent** | Semantic search | Search engine | TBD |
| **ui-agent** | Web UI, event hooks | User interface | TBD |

---

## Territorial Boundaries

### infrastructure-agent

**Owned Directories**:
```
docker/
├── docker-compose.yml              ✍️ Write
├── Dockerfile.copyparty            ✍️ Write
├── Dockerfile.processing-worker    ✍️ Write
└── .env                            ✍️ Write

scripts/
├── setup.sh                        ✍️ Write
├── start.sh                        ✍️ Write
└── stop.sh                         ✍️ Write
```

**Read-Only Access**:
- All `integration-contracts/` (for container configuration)
- `src/*/requirements.txt` (for Dockerfile dependencies)

**Responsibilities**:
1. Docker Compose orchestration
2. Container networking and volumes
3. Health checks and resource limits
4. Environment variable configuration
5. Setup and startup scripts
6. M1-specific optimizations (ARM64 builds, MPS support)

**Deliverables**:
- [ ] `docker-compose.yml` with 3 services
- [ ] `Dockerfile.copyparty` (Python 3.11, copyparty, event hooks)
- [ ] `Dockerfile.processing-worker` (Python 3.10, PyTorch, ColPali, Docling)
- [ ] `.env` with all required environment variables
- [ ] `scripts/setup.sh` (initialize directories, pre-download models)
- [ ] `scripts/start.sh` (docker compose up with health checks)
- [ ] `scripts/stop.sh` (graceful shutdown)

**Critical Dependencies**:
- ColNomic 7B model (14GB download)
- PyTorch with MPS support (M1 GPU)
- ChromaDB ARM64 image

**Contract Compliance**:
- Must support all environment variables in `config-interface.md`
- Must mount volumes as specified in contracts
- Must expose ports: 8000 (copyparty), 8001 (chromadb)

---

### storage-agent

**Owned Directories**:
```
src/storage/
├── __init__.py                     ✍️ Write
├── chroma_client.py                ✍️ Write
├── collection_manager.py           ✍️ Write
├── compression.py                  ✍️ Write
└── test_storage.py                 ✍️ Write
```

**Read-Only Access**:
- `integration-contracts/storage-interface.md` (own contract)
- `integration-contracts/embedding-interface.md` (embedding formats)

**Responsibilities**:
1. ChromaDB client wrapper (`ChromaClient` class)
2. Collection initialization (visual_collection, text_collection)
3. Multi-vector storage implementation
4. Compression/decompression logic
5. Metadata validation
6. Storage unit tests

**Deliverables**:
- [ ] `chroma_client.py` with `ChromaClient` class
- [ ] `collection_manager.py` for collection lifecycle
- [ ] `compression.py` with gzip + base64 encoding
- [ ] `test_storage.py` with unit tests (>90% coverage)
- [ ] Documentation: API usage examples

**Critical Dependencies**:
- ChromaDB Python client (`chromadb>=0.4.0`)
- NumPy for array handling

**Contract Compliance**:
- Implement all methods in `storage-interface.md`
- Validate embedding shapes: (seq_length, 768)
- Support metadata filters in search
- Handle compression for embeddings >2MB

**Integration Points**:
- **Consumers**: processing-agent, search-agent
- **Test Strategy**: Mock ChromaDB server for unit tests, real ChromaDB for integration tests

---

### embedding-agent

**Owned Directories**:
```
src/embeddings/
├── __init__.py                     ✍️ Write
├── colpali_wrapper.py              ✍️ Write
├── model_loader.py                 ✍️ Write
├── scoring.py                      ✍️ Write
└── test_embeddings.py              ✍️ Write
```

**Read-Only Access**:
- `integration-contracts/embedding-interface.md` (own contract)
- `integration-contracts/storage-interface.md` (storage formats)

**Responsibilities**:
1. ColPali engine wrapper (`ColPaliEngine` class)
2. Model loading with MPS/CUDA/CPU fallback
3. Image embedding generation
4. Text embedding generation
5. Query embedding
6. Late interaction scoring (MaxSim)
7. FP16/INT8 quantization support
8. Embedding unit tests

**Deliverables**:
- [ ] `colpali_wrapper.py` with `ColPaliEngine` class
- [ ] `model_loader.py` for model initialization
- [ ] `scoring.py` with MaxSim algorithm
- [ ] `test_embeddings.py` with unit tests (>90% coverage)
- [ ] Performance benchmarks: FP16 vs INT8

**Critical Dependencies**:
- ColPali engine (`git+https://github.com/illuin-tech/colpali.git`)
- PyTorch with MPS support
- Transformers, PIL

**Contract Compliance**:
- Implement all methods in `embedding-interface.md`
- Return embeddings with shape (seq_length, 768)
- Support batch processing
- Handle device fallback (MPS → CUDA → CPU)

**Integration Points**:
- **Consumers**: processing-agent, search-agent
- **Test Strategy**: Mock model for unit tests, real model for integration tests

---

### processing-agent

**Owned Directories**:
```
src/processing/
├── __init__.py                     ✍️ Write
├── processor.py                    ✍️ Write (main coordinator)
├── worker.py                       ✍️ Write (daemon)
├── docling_parser.py               ✍️ Write
├── visual_processor.py             ✍️ Write
├── text_processor.py               ✍️ Write
├── queue_manager.py                ✍️ Write (Wave 4)
└── test_processing.py              ✍️ Write
```

**Read-Only Access**:
- `integration-contracts/processing-interface.md` (own contract)
- `integration-contracts/embedding-interface.md` (call embedding APIs)
- `integration-contracts/storage-interface.md` (call storage APIs)
- `data/copyparty/uploads/` (read uploaded files)

**Responsibilities**:
1. Document processing coordinator
2. Docling parser integration
3. Visual processing pipeline (PDF → images → embeddings)
4. Text processing pipeline (text → chunks → embeddings)
5. Hybrid workflow orchestration
6. Processing worker daemon
7. Event hook integration
8. Queue management (Wave 4)
9. Error handling and logging

**Deliverables**:
- [ ] `processor.py` with `DocumentProcessor` class (coordinator)
- [ ] `worker.py` with daemon loop (file monitoring)
- [ ] `docling_parser.py` for document parsing
- [ ] `visual_processor.py` for visual pipeline
- [ ] `text_processor.py` for text pipeline
- [ ] `queue_manager.py` for batch processing (Wave 4)
- [ ] `test_processing.py` with unit and integration tests
- [ ] Processing metrics logging

**Critical Dependencies**:
- Docling (`docling>=2.0.0`)
- pdf2image, Pillow
- Embedding-agent API (mock in Wave 2, real in Wave 3)
- Storage-agent API (mock in Wave 2, real in Wave 3)

**Contract Compliance**:
- Implement workflow in `processing-interface.md`
- Call embedding-agent APIs as specified
- Call storage-agent APIs as specified
- Generate event status messages

**Integration Points**:
- **Providers**: embedding-agent, storage-agent
- **Consumers**: ui-agent (via event hooks)
- **Test Strategy**: Mock providers in Wave 2, integration tests in Wave 3

---

### search-agent

**Owned Directories**:
```
src/search/
├── __init__.py                     ✍️ Write
├── search_engine.py                ✍️ Write (main)
├── result_ranker.py                ✍️ Write
├── query_processor.py              ✍️ Write
└── test_search.py                  ✍️ Write
```

**Read-Only Access**:
- `integration-contracts/search-interface.md` (own contract)
- `integration-contracts/embedding-interface.md` (call embedding APIs)
- `integration-contracts/storage-interface.md` (call storage APIs)

**Responsibilities**:
1. Search engine coordinator (`SearchEngine` class)
2. Two-stage search implementation
3. Stage 1: Fast retrieval using representative vectors
4. Stage 2: Re-ranking with late interaction
5. Result merging (visual + text)
6. Result formatting
7. Filter application
8. Search metrics

**Deliverables**:
- [ ] `search_engine.py` with `SearchEngine` class
- [ ] `result_ranker.py` for merging and ranking logic
- [ ] `query_processor.py` for query embedding
- [ ] `test_search.py` with unit and integration tests
- [ ] Search performance benchmarks

**Critical Dependencies**:
- Embedding-agent API (mock in Wave 2, real in Wave 3)
- Storage-agent API (mock in Wave 2, real in Wave 3)
- NumPy for score normalization

**Contract Compliance**:
- Implement all methods in `search-interface.md`
- Support search modes: hybrid, visual_only, text_only
- Apply filters correctly
- Meet latency targets (<500ms)

**Integration Points**:
- **Providers**: embedding-agent, storage-agent
- **Consumers**: ui-agent
- **Test Strategy**: Mock providers in Wave 2, integration tests in Wave 3

---

### ui-agent

**Owned Directories**:
```
src/ui/
├── search.html                     ✍️ Write
├── search.js                       ✍️ Write
├── status_dashboard.html           ✍️ Write
├── status_dashboard.js             ✍️ Write
└── styles.css                      ✍️ Write

data/copyparty/
├── hooks/
│   └── on_upload.py                ✍️ Write
└── www/                            ✍️ Write (symlink to src/ui/)
```

**Read-Only Access**:
- `integration-contracts/search-interface.md` (call search APIs)
- `integration-contracts/processing-interface.md` (trigger processing)
- `data/copyparty/uploads/` (for thumbnail generation)

**Responsibilities**:
1. Search page UI (HTML/JS/CSS)
2. Query form with validation
3. Results display component
4. Result preview modal
5. Copyparty event hook (on_upload.py)
6. Processing status dashboard
7. Real-time status updates
8. Error handling and user feedback

**Deliverables**:
- [ ] `search.html` with search UI
- [ ] `search.js` with search logic and API calls
- [ ] `status_dashboard.html` with processing queue view
- [ ] `status_dashboard.js` with real-time updates
- [ ] `styles.css` with responsive design
- [ ] `on_upload.py` event hook for processing trigger
- [ ] User documentation (how to upload, search, interpret results)

**Critical Dependencies**:
- Search-agent API (mock in Wave 2, real in Wave 3)
- Processing-agent worker (via file system events)
- Copyparty web server

**Contract Compliance**:
- Call search-agent APIs as specified in `search-interface.md`
- Trigger processing as specified in `processing-interface.md`
- Display results with all required fields

**Integration Points**:
- **Providers**: search-agent, processing-agent
- **Consumers**: End users (browser)
- **Test Strategy**: Mock search API in Wave 2, end-to-end tests in Wave 3

---

## Conflict Prevention Matrix

| Agent | Writes To | Reads From | Depends On |
|-------|-----------|------------|------------|
| **infrastructure-agent** | `docker/`, `scripts/` | All contracts | None |
| **storage-agent** | `src/storage/` | storage-interface.md | None |
| **embedding-agent** | `src/embeddings/` | embedding-interface.md | None |
| **processing-agent** | `src/processing/` | embedding-interface.md, storage-interface.md | embedding-agent, storage-agent |
| **search-agent** | `src/search/` | search-interface.md, embedding-interface.md, storage-interface.md | embedding-agent, storage-agent |
| **ui-agent** | `src/ui/`, `data/copyparty/` | search-interface.md, processing-interface.md | search-agent, processing-agent |

**Key Insight**: No overlapping write access ensures zero merge conflicts.

---

## Development Workflow (Per Agent)

### Wave 1: Contract Definition (1-2 days)
1. Review integration contracts relevant to your agent
2. Propose API additions or clarifications
3. Create test fixtures based on contracts
4. Set up development environment

### Wave 2: Independent Implementation (3-5 days)
1. Implement core functionality with mocks for dependencies
2. Write unit tests (target >90% coverage)
3. Validate contract compliance
4. Document your API with examples
5. Publish status: "Wave 2 complete, ready for integration"

### Wave 3: Integration (3-4 days)
1. Replace mocks with real provider implementations
2. Run integration tests with real dependencies
3. Report any contract violations to provider agents
4. Optimize for performance targets
5. Publish status: "Wave 3 complete, integration successful"

### Wave 4: Enhancement (2-3 days)
1. Add production features (filters, queue, dashboard)
2. Optimize performance bottlenecks
3. Add monitoring and logging
4. Complete documentation
5. Publish status: "Wave 4 complete, production ready"

---

## Communication Channels

### Status Updates (Required)

Each agent must post status after completing tasks:

**Format**:
```json
{
  "agent": "storage-agent",
  "wave": 2,
  "status": "completed",
  "task": "Implement ChromaClient with multi-vector storage",
  "timestamp": "2023-10-06T15:30:00Z",
  "deliverables": [
    "src/storage/chroma_client.py",
    "src/storage/test_storage.py"
  ],
  "contract_compliance": "100% (all methods implemented)",
  "test_coverage": "92%",
  "blockers": []
}
```

**Channel**: Post to `.context-kit/orchestration/docusearch-mvp/status/` directory

### Code Review (Wave 2 → Wave 3 Gate)

Before integration, consumer agents must review provider APIs:

**Example**: processing-agent reviews embedding-agent

1. Read `src/embeddings/colpali_wrapper.py`
2. Validate against `embedding-interface.md`
3. Test with mock data
4. Approve or request changes

**Format**:
```markdown
## Code Review: embedding-agent by processing-agent

**Contract**: embedding-interface.md
**Implementation**: src/embeddings/colpali_wrapper.py

### Compliance Check
- [x] All methods implemented
- [x] Correct input/output types
- [x] Error handling present
- [x] Unit tests pass

### Issues Found
None

### Approval
✅ Approved for integration

**Reviewer**: processing-agent
**Date**: 2023-10-06
```

### Blocker Resolution

If an agent encounters blockers:

1. **Document**: What is blocked and why
2. **Notify**: Tag dependent agents
3. **Propose**: Temporary workaround
4. **Escalate**: If no resolution in 24 hours

**Example**:
```markdown
## BLOCKER: ChromaDB Metadata Size Limit

**Reported By**: storage-agent
**Wave**: 2
**Impact**: Blocks integration with processing-agent

### Problem
ChromaDB metadata field limited to 2MB. Our multi-vector embeddings
(100 tokens × 768 dims × 4 bytes) = 300KB per page, but 10 pages
exceed limit.

### Proposed Solution
Add gzip compression before base64 encoding. Reduces size by 4x.

### Changes Required
- Update `storage-interface.md` with compression API
- Implement in `src/storage/compression.py`
- Update processing-agent to use compressed format

### Timeline
+1 day to implement and test

### Status
🟡 In Progress
```

---

## Handoff Procedures

### Wave 2 → Wave 3: Mock to Real Integration

**Provider Agent** (e.g., storage-agent):
1. Mark Wave 2 as complete
2. Publish final API documentation
3. Provide integration test fixtures
4. Be available for questions

**Consumer Agent** (e.g., processing-agent):
1. Review provider API documentation
2. Replace mocks with real imports
3. Run integration tests
4. Report any issues immediately
5. Validate contract compliance

### Wave 3 → Wave 4: Enhancement Phase

All agents:
1. Mark Wave 3 integration complete
2. Identify performance bottlenecks
3. Implement enhancements independently
4. Retest after changes
5. Document production readiness

---

## Ownership Transfer (If Needed)

If an agent needs to be reassigned:

1. **Document Current State**:
   - What's complete
   - What's in progress
   - What's blocking

2. **Code Review**:
   - New owner reviews all code
   - Asks clarifying questions
   - Tests functionality

3. **Handoff Meeting**:
   - Original owner explains decisions
   - New owner confirms understanding
   - Agreement on next steps

4. **Status Update**:
   - Announce ownership transfer
   - Update contact info in assignments

---

## Success Criteria (Per Agent)

### infrastructure-agent
- [ ] Docker Compose starts all 3 containers without errors
- [ ] Health checks pass for all services
- [ ] ColNomic 7B model loaded successfully with MPS
- [ ] All environment variables configured correctly
- [ ] Setup script runs without manual intervention

### storage-agent
- [ ] Unit tests pass (>90% coverage)
- [ ] Store and retrieve embeddings successfully
- [ ] Compression reduces size by 4x
- [ ] Search returns correct candidates
- [ ] Integration tests pass with real ChromaDB

### embedding-agent
- [ ] Unit tests pass (>90% coverage)
- [ ] Model loads on MPS device
- [ ] Embedding generation meets timing targets (FP16: 6s, INT8: 3s)
- [ ] Late interaction scoring works correctly
- [ ] Integration tests pass with real model

### processing-agent
- [ ] Unit tests pass (>90% coverage)
- [ ] Process sample PDF end-to-end (<2 min for 10 pages)
- [ ] Embeddings stored correctly in ChromaDB
- [ ] Event hook triggers processing successfully
- [ ] Integration tests pass with real providers

### search-agent
- [ ] Unit tests pass (>90% coverage)
- [ ] Two-stage search completes in <500ms
- [ ] Top-10 results are relevant for test queries
- [ ] Filters work correctly
- [ ] Integration tests pass with real providers

### ui-agent
- [ ] Search page renders correctly in browser
- [ ] Query form validates input
- [ ] Results display with all required fields
- [ ] Event hook triggers processing
- [ ] End-to-end test: upload → process → search → view results

---

## Agent Directory Quick Reference

```
tkr-docusearch/
├── docker/                         # infrastructure-agent
├── scripts/                        # infrastructure-agent
├── src/
│   ├── storage/                   # storage-agent
│   ├── embeddings/                # embedding-agent
│   ├── processing/                # processing-agent
│   ├── search/                    # search-agent
│   └── ui/                        # ui-agent
├── data/
│   └── copyparty/                 # ui-agent (hooks)
└── .context-kit/
    └── orchestration/
        └── docusearch-mvp/
            ├── orchestration-plan.md
            ├── agent-assignments.md    # This file
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

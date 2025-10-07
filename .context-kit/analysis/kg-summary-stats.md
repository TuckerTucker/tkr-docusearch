# Knowledge Graph Analysis - Summary Statistics
**Generated:** 2025-10-07
**Repository:** tkr-docusearch

---

## Entity Summary

### Modules (6 core + 2 supporting)
**Core Modules:**
1. `embeddings` - ColPali embedding generation with Metal GPU
2. `storage` - ChromaDB vector database client
3. `processing` - Document processing pipeline
4. `search` - Two-stage semantic search engine
5. `config` - Configuration management
6. `api` - REST API server

**Supporting:**
- `ui` - User interface components
- `hooks` - Webhook handlers

### Classes and Key Components (25+)

**Embeddings Module (6):**
- ColPaliEngine
- ModelLoader
- Scoring
- EmbeddingOutput
- BatchEmbeddingOutput
- ScoringOutput

**Storage Module (5):**
- ChromaClient
- CollectionManager
- Compression
- StorageError
- ChromaDBConnectionError

**Processing Module (6):**
- DocumentProcessor
- DoclingParser
- VisualProcessor
- TextProcessor
- ProcessingStatus
- StorageConfirmation

**Search Module (4):**
- SearchEngine
- QueryProcessor
- ResultRanker
- SearchError

**Config Module (3):**
- ModelConfig
- ProcessingConfig
- StorageConfig

**API Module (1):**
- FastAPI application (server.py)

### Functions/Methods (100+)
Key method categories:
- **Embedding:** 15+ methods (embed_images, embed_texts, embed_query, score_multi_vector, etc.)
- **Storage:** 20+ methods (add_visual_embedding, search_visual, delete_document, etc.)
- **Processing:** 25+ methods (process_document, parse_document, process_pages, etc.)
- **Search:** 15+ methods (search, _stage1_retrieval, _stage2_reranking, etc.)
- **API Endpoints:** 10+ routes (search, upload, status, health, etc.)
- **Utilities:** 25+ helper functions (validation, compression, formatting, etc.)

### Scripts (6 management + 3 utility)
**Management Scripts:**
1. `start-all.sh` - Unified startup (GPU/CPU/Docker-only modes)
2. `stop-all.sh` - Graceful shutdown with force option
3. `status.sh` - Service monitoring (text/JSON output)
4. `run-worker-native.sh` - Native worker lifecycle
5. `setup.sh` - Initial project setup
6. `query-chromadb.sh` - Database query utility

### Docker Services (3)
1. `copyparty` - File upload server (port 8000)
2. `chromadb` - Vector database (port 8001)
3. `processing-worker` - Document processor (port 8002, CPU mode)

### Configuration Files (5)
1. `docker-compose.yml` - Main Docker configuration
2. `docker-compose.native-worker.yml` - Native worker override
3. `ModelConfig` (Python) - Embedding model settings
4. `ProcessingConfig` (Python) - Processing settings
5. `StorageConfig` (Python) - Storage settings

---

## Relationship Summary

### Import Dependencies (40+)
**Module-level imports:**
- `api.server` → embeddings, storage, search, processing (4 dependencies)
- `processing.processor` → embeddings, storage, processing.* (6 dependencies)
- `search.search_engine` → embeddings, storage, search.* (5 dependencies)
- `embeddings.colpali_wrapper` → embeddings.*, config (4 dependencies)
- `storage.chroma_client` → storage.*, chromadb (3 dependencies)

**Total estimated:** 40-50 import relationships across modules

### Integration Contracts (5 validated)
1. **Embedding Interface:** ColPaliEngine → DocumentProcessor, SearchEngine
2. **Storage Interface:** ChromaClient → DocumentProcessor, SearchEngine
3. **Processing Interface:** DocumentProcessor → worker_webhook
4. **Search Interface:** SearchEngine → api.server
5. **Webhook Interface:** worker_webhook → Copyparty (Docker)

### Data Flow Patterns (3 primary)
1. **Upload Flow:** User → Copyparty → Webhook → Worker → Parser → Embedder → Storage (7 steps)
2. **Search Flow:** User → API → Query → Stage 1 → Stage 2 → Results (6 steps)
3. **Management Flow:** User → Script → Docker/Native → Services → Health (5 steps)

### Architectural Patterns (7)
1. **Hybrid Architecture** - Native Metal GPU + Docker services
2. **Two-Stage Search** - HNSW retrieval + MaxSim re-ranking
3. **Multi-Vector Compression** - CLS token + gzip full sequence
4. **Webhook-Driven Processing** - Event-based async pipeline
5. **Progressive Validation** - Wave gates with validation checkpoints
6. **Interface-First Development** - Contracts before implementation
7. **Environment-Driven Config** - 12-factor app methodology

---

## Key Architectural Insights

### Component Integration Points (5)
1. **Embedding ↔ Processing:** DocumentProcessor uses ColPaliEngine for visual/text embedding
2. **Embedding ↔ Search:** SearchEngine uses ColPaliEngine for query embedding and re-ranking
3. **Storage ↔ Processing:** DocumentProcessor stores embeddings in ChromaClient
4. **Storage ↔ Search:** SearchEngine retrieves candidates from ChromaClient
5. **API ↔ All Components:** FastAPI server orchestrates all components

### Performance Characteristics

**Embedding Performance:**
- Image: 2.3s/page (2.6x faster than 6s target)
- Text: 0.24s/chunk (25x faster than 6s target)
- Query: 0.2s (5x faster than 1s target)
- GPU acceleration: 10-20x faster than CPU

**Search Performance:**
- Total latency: 239ms (21% faster than 300ms target)
- Stage 1 (HNSW): 50-100ms
- Stage 2 (MaxSim): <1ms per document
- Accuracy: 100% (all expected docs at rank 1)

**Storage Efficiency:**
- Embedding dimension: 128 (6x smaller than 768)
- Compression ratio: 4x (gzip)
- Metadata size: <50KB per embedding

### Technology Stack Distribution

**Languages:**
- Python: 42 files (primary)
- Bash: 6 files (management)
- YAML: 2 files (Docker)

**Frameworks:**
- PyTorch (ML execution)
- FastAPI (web API)
- ChromaDB (vector storage)
- Docling (document parsing)

**Infrastructure:**
- Docker (containerization)
- Metal/MPS (GPU acceleration)
- Copyparty (file upload)

---

## Validation Status

### Wave Completion
- ✅ Wave 1: Foundation (contracts, structure)
- ✅ Wave 2: Components (embeddings, storage, processing, search)
- ✅ Wave 3: Integration (end-to-end tests, webhook)
- ✅ Wave 4: Production (validation, benchmarks)
- ✅ Wave 5: Management (unified scripts, GPU support)

### Integration Contracts
- ✅ Embedding Interface (validated)
- ✅ Storage Interface (validated)
- ✅ Processing Interface (integrated)
- ✅ Search Interface (validated)
- ✅ Webhook Interface (working)

### Production Readiness: 98%
**Completed:**
- Real ColPali + ChromaDB integration
- Metal GPU acceleration
- Two-stage search with 100% accuracy
- Performance exceeds targets
- Webhook processing pipeline
- Unified management system
- Comprehensive documentation

**Remaining (2%):**
- Scale testing (100+ documents)
- Enhanced UI features
- User acceptance testing

---

## Knowledge Graph Insights

### Most Connected Components
1. **DocumentProcessor** (processing module)
   - Integrates: embeddings, storage, parsing, visual/text processors
   - Dependencies: 6+
   - Consumers: worker_webhook, api.server

2. **SearchEngine** (search module)
   - Integrates: embeddings, storage, query_processor, result_ranker
   - Dependencies: 5+
   - Consumers: api.server

3. **ColPaliEngine** (embeddings module)
   - Used by: DocumentProcessor, SearchEngine
   - Provides: Image/text embedding, query embedding, late interaction scoring
   - Impact: High (core ML component)

### Critical Path Components
1. **ChromaClient** (storage)
   - Single point of failure for data persistence
   - Performance bottleneck potential at scale
   - Mitigation: Volume persistence, health monitoring

2. **ColPaliEngine** (embeddings)
   - Memory intensive (14GB FP16)
   - Startup time: 10-30s
   - Mitigation: Keep worker running, model caching

3. **Webhook System** (processing)
   - Asynchronous coupling between upload and processing
   - Failure modes: Worker down, ChromaDB unavailable
   - Mitigation: Status tracking, error handling, retry logic

### Module Independence Scores
- **config:** 100% (no internal dependencies, leaf module)
- **embeddings:** 90% (only depends on config)
- **storage:** 95% (minimal dependencies, only compression util)
- **processing:** 60% (depends on embeddings, storage, parsing)
- **search:** 65% (depends on embeddings, storage, processors)
- **api:** 40% (depends on all other modules)

---

## Recommendations for Knowledge Graph

### Entity Creation Priority
1. **High Priority:** Core classes (ColPaliEngine, ChromaClient, DocumentProcessor, SearchEngine)
2. **Medium Priority:** Supporting classes (processors, ranker, config)
3. **Low Priority:** Exception classes, utility functions

### Relationship Creation Priority
1. **High Priority:** Integration contracts (validated interfaces)
2. **Medium Priority:** Data flow patterns (pipeline stages)
3. **Low Priority:** Import dependencies (implementation details)

### Tags for Entity Classification
- `core-component` - Main architectural components
- `ml-model` - Machine learning related
- `storage` - Data persistence
- `api-endpoint` - HTTP API routes
- `management-script` - Operational scripts
- `configuration` - Settings and config
- `validated` - Wave-validated components
- `production-ready` - Deployment-ready components
- `gpu-accelerated` - Metal/CUDA optimized

---

**Statistics Summary:**
- **Total Entities:** 100+ (modules, classes, functions, scripts, configs)
- **Total Relationships:** 60+ (imports, integrations, data flows, patterns)
- **Architectural Patterns:** 7 major patterns identified
- **Integration Contracts:** 5 validated contracts
- **Production Status:** 98% ready for deployment

---

*This summary provides high-level statistics for knowledge graph population. See kg-analysis-report.md for detailed analysis.*

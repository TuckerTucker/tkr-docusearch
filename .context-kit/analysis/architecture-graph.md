# Architecture Dependency Graph - tkr-docusearch

## Component Hierarchy

```
tkr-docusearch/
│
├── Infrastructure Layer (Docker + Native)
│   ├── Docker Services
│   │   ├── copyparty:8000 (File Upload + Webhook)
│   │   ├── chromadb:8001 (Vector Database)
│   │   └── processing-worker:8002 (CPU mode only)
│   │
│   └── Native Services (GPU mode)
│       └── processing-worker:8002 (Metal MPS acceleration)
│
├── Management Layer (Bash Scripts)
│   ├── start-all.sh (Unified startup: GPU/CPU/Docker-only)
│   ├── stop-all.sh (Graceful shutdown + force)
│   ├── status.sh (Service monitoring: text/JSON)
│   ├── run-worker-native.sh (Native worker: setup/run/check)
│   ├── setup.sh (Initial project setup)
│   └── query-chromadb.sh (Database utilities)
│
├── Application Layer (Python)
│   │
│   ├── API Module (src/api/)
│   │   ├── server.py ────────────┐
│   │   └── models.py             │
│   │                              │
│   ├── Processing Module (src/processing/)
│   │   ├── processor.py ◄────────┤
│   │   ├── worker_webhook.py ◄───┤
│   │   ├── docling_parser.py     │
│   │   ├── visual_processor.py   │
│   │   └── text_processor.py     │
│   │                              │
│   ├── Search Module (src/search/)
│   │   ├── search_engine.py ◄────┤
│   │   ├── query_processor.py    │
│   │   └── result_ranker.py      │
│   │                              │
│   ├── Embeddings Module (src/embeddings/)
│   │   ├── colpali_wrapper.py ◄──┼─────┐
│   │   ├── model_loader.py       │     │
│   │   ├── scoring.py            │     │
│   │   ├── types.py              │     │
│   │   └── exceptions.py         │     │
│   │                              │     │
│   ├── Storage Module (src/storage/)
│   │   ├── chroma_client.py ◄────┼─────┤
│   │   ├── collection_manager.py │     │
│   │   └── compression.py        │     │
│   │                              │     │
│   └── Config Module (src/config/)
│       ├── model_config.py ◄──────────┤
│       ├── processing_config.py       │
│       └── storage_config.py          │
│                                       │
└── ML/Data Layer                      │
    ├── ColNomic 7B Model (14GB) ◄─────┘
    ├── PyTorch MPS Runtime
    └── ChromaDB Collections
        ├── visual_collection (page embeddings)
        └── text_collection (chunk embeddings)
```

---

## Data Flow Diagrams

### Document Upload and Processing Flow

```
┌─────────────┐
│    User     │
│  (Browser)  │
└──────┬──────┘
       │ 1. Upload file
       ▼
┌─────────────────┐
│   Copyparty     │ Port 8000
│ (File Server)   │
└────────┬────────┘
         │ 2. Webhook trigger
         │    POST /process
         ▼
┌──────────────────────────┐
│  Processing Worker       │ Port 8002
│  (worker_webhook.py)     │
└────────┬─────────────────┘
         │ 3. Background processing
         ▼
┌────────────────────────────┐
│  DocumentProcessor         │
│  (processor.py)            │
└─┬────────┬────────┬───────┘
  │        │        │
  │ 4.     │ 5.     │ 6.
  │ Parse  │ Embed  │ Store
  ▼        ▼        ▼
┌──────┐ ┌──────┐ ┌──────────┐
│Docl- │ │ColPa-│ │ChromaDB  │
│ing   │ │li    │ │Client    │
└──────┘ └──────┘ └────┬─────┘
                       │ 7. Persist
                       ▼
                 ┌────────────┐
                 │ ChromaDB   │ Port 8001
                 │ (Docker)   │
                 └────────────┘

Timeline:
1. Upload: Instant
2. Webhook: <100ms
3. Queue: Instant
4. Parse: 1-5s (varies by doc size)
5. Embed: 2.3s/page + 0.24s/chunk
6. Store: <1s
7. Persist: <1s

Total: ~10-30s for typical document
```

---

### Search Query Flow

```
┌─────────────┐
│    User     │
│  (Browser)  │
└──────┬──────┘
       │ 1. Search query
       ▼
┌─────────────────┐
│   API Server    │ Port 8002
│  (server.py)    │
│  POST /search   │
└────────┬────────┘
         │ 2. Orchestrate search
         ▼
┌─────────────────────────┐
│  SearchEngine           │
│  (search_engine.py)     │
└────┬────────────────────┘
     │
     │ 3. Embed query
     ▼
┌─────────────────┐
│ ColPaliEngine   │
│ embed_query()   │
└────┬────────────┘
     │ Query: (22 tokens, 128 dim) + CLS
     │
     ├──────────────────────────────┐
     │                              │
     │ STAGE 1: Fast Retrieval      │ STAGE 2: Re-ranking
     ▼                              ▼
┌─────────────────┐           ┌─────────────────┐
│ ChromaClient    │           │ ColPaliEngine   │
│ search_visual() │           │ score_multi_    │
│ search_text()   │           │ _vector()       │
└────┬────────────┘           └────┬────────────┘
     │                             │
     │ 4. HNSW search              │ 6. MaxSim scoring
     │    (CLS tokens)             │    (full sequences)
     ▼                             ▼
┌─────────────────┐           ┌─────────────────┐
│ ChromaDB        │           │ ResultRanker    │
│ Top-100         │           │ rank_by_late_   │
│ candidates      │───5.──────►│ interaction()   │
└─────────────────┘  Decompress└────┬────────────┘
                     metadata       │
                                    │ 7. Merge & format
                                    ▼
                              ┌─────────────────┐
                              │ SearchResponse  │
                              │ Top-10 results  │
                              └────┬────────────┘
                                   │
                                   ▼
                              ┌─────────────┐
                              │    User     │
                              └─────────────┘

Timeline:
3. Embed query: 0.2s
4. Stage 1 (HNSW): 50-100ms
5. Decompress: 10-20ms
6. Stage 2 (MaxSim): <1ms per doc (100 docs = 100ms)
7. Merge/format: <10ms

Total: ~239ms average (target: <300ms)
```

---

## Module Dependency Graph

```
                    ┌────────────────┐
                    │   api.server   │
                    └────────┬───────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
    ┌──────────┐      ┌──────────┐      ┌──────────┐
    │ search   │      │processing│      │ API      │
    │ _engine  │      │.processor│      │ models   │
    └────┬─────┘      └────┬─────┘      └──────────┘
         │                 │
         │            ┌────┴────┐
         │            │         │
         │            ▼         ▼
         │      ┌──────────┬──────────┐
         │      │ visual   │  text    │
         │      │processor │processor │
         │      └──────────┴──────────┘
         │
    ┌────┴─────────────────┐
    │                      │
    ▼                      ▼
┌──────────┐          ┌──────────┐
│ query    │          │ result   │
│processor │          │ ranker   │
└────┬─────┘          └────┬─────┘
     │                     │
     └──────────┬──────────┘
                │
       ┌────────┴────────┐
       │                 │
       ▼                 ▼
┌────────────┐     ┌────────────┐
│ embeddings │     │  storage   │
│ .colpali   │     │  .chroma   │
└─────┬──────┘     └─────┬──────┘
      │                  │
      └─────────┬────────┘
                │
         ┌──────┴──────┐
         │             │
         ▼             ▼
    ┌────────┐   ┌────────┐
    │ model  │   │compress│
    │ _loader│   │ -ion   │
    └────┬───┘   └────────┘
         │
         ▼
    ┌────────┐
    │ config │
    │.model  │
    └────────┘

Legend:
  ──►  imports/depends on
  ═══► strong dependency (critical path)
```

---

## Integration Contract Map

```
┌─────────────────────────────────────────────────────────────┐
│                   Integration Contracts                      │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐
│ Embedding        │ Provider: ColPaliEngine
│ Interface        │ Consumers: DocumentProcessor, SearchEngine
└──────┬───────────┘
       │ Methods:
       ├─ embed_images(images) → BatchEmbeddingOutput
       ├─ embed_texts(texts) → BatchEmbeddingOutput
       ├─ embed_query(query) → EmbeddingOutput
       └─ score_multi_vector(query, docs) → ScoringOutput

       Status: ✅ VALIDATED (Wave 2)
       Performance: 2.3s/page (images), 0.24s/chunk (texts)

───────────────────────────────────────────────────────────────

┌──────────────────┐
│ Storage          │ Provider: ChromaClient
│ Interface        │ Consumers: DocumentProcessor, SearchEngine
└──────┬───────────┘
       │ Methods:
       ├─ add_visual_embedding(doc_id, page, embeddings, metadata)
       ├─ add_text_embedding(doc_id, chunk_id, embeddings, metadata)
       ├─ search_visual(query_embedding, n_results, filters)
       ├─ search_text(query_embedding, n_results, filters)
       └─ delete_document(doc_id)

       Status: ✅ VALIDATED (Wave 2)
       Features: 128-dim embeddings, 4x compression, <50KB metadata

───────────────────────────────────────────────────────────────

┌──────────────────┐
│ Processing       │ Provider: DocumentProcessor
│ Interface        │ Consumer: worker_webhook
└──────┬───────────┘
       │ Methods:
       ├─ process_document(file_path, status_callback)
       └─ Callback: ProcessingStatus with progress tracking

       Status: ✅ INTEGRATED (Wave 3)
       Pipeline: Parse → Embed → Store

───────────────────────────────────────────────────────────────

┌──────────────────┐
│ Search           │ Provider: SearchEngine
│ Interface        │ Consumer: api.server
└──────┬───────────┘
       │ Methods:
       └─ search(query, n_results, search_mode, filters)
          Modes: hybrid, visual_only, text_only

       Status: ✅ VALIDATED (Wave 3)
       Performance: 239ms avg, 100% accuracy

───────────────────────────────────────────────────────────────

┌──────────────────┐
│ Webhook          │ Provider: worker_webhook (FastAPI)
│ Interface        │ Consumer: Copyparty (Docker)
└──────┬───────────┘
       │ Endpoints:
       ├─ POST /process (Queue document)
       ├─ POST /delete (Remove from ChromaDB)
       ├─ GET /status (Worker health)
       └─ GET /health (Simple health check)

       Status: ✅ WORKING (Wave 3)
       Features: Async processing, status tracking
```

---

## Technology Stack Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
├─────────────────────────────────────────────────────────────┤
│  FastAPI Server │ DocumentProcessor │ SearchEngine          │
│  (REST API)     │ (Pipeline)        │ (2-Stage)             │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                   Core Components Layer                      │
├─────────────────────────────────────────────────────────────┤
│  ColPaliEngine  │  ChromaClient    │  DoclingParser        │
│  (Embeddings)   │  (Vector DB)     │  (Parsing)            │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    ML/AI Framework Layer                     │
├─────────────────────────────────────────────────────────────┤
│  PyTorch (MPS)  │  transformers    │  colpali-engine       │
│  (GPU Runtime)  │  (HF Models)     │  (ColPali)            │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                       │
├─────────────────────────────────────────────────────────────┤
│  Docker         │  Metal MPS       │  ChromaDB Server      │
│  (Containers)   │  (GPU Accel)     │  (Vector DB)          │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                      Hardware Layer                          │
├─────────────────────────────────────────────────────────────┤
│  M1/M2/M3 Mac   │  RAM (16GB+)     │  Storage (SSD)        │
│  (Apple Silicon)│  (Model + Data)  │  (DB + Models)        │
└─────────────────────────────────────────────────────────────┘
```

---

## Critical Path Analysis

### High-Impact Components (Failure = System Down)

```
Priority 1: CRITICAL
┌──────────────────┐
│  ChromaDB        │ - Single source of truth for embeddings
│  (Storage)       │ - No redundancy/replication
└──────────────────┘
   Mitigation: Volume persistence, health monitoring

┌──────────────────┐
│  ColPaliEngine   │ - Required for all embedding operations
│  (ML Model)      │ - 10-30s startup time, 14GB memory
└──────────────────┘
   Mitigation: Keep worker running, model caching

Priority 2: HIGH IMPACT
┌──────────────────┐
│  worker_webhook  │ - Async coupling for processing
│  (Processing)    │ - ThreadPoolExecutor (2 workers)
└──────────────────┘
   Mitigation: Status tracking, error handling, retry logic

┌──────────────────┐
│  Copyparty       │ - Upload entry point
│  (File Server)   │ - Webhook trigger
└──────────────────┘
   Mitigation: Docker auto-restart, volume persistence

Priority 3: RECOVERABLE
┌──────────────────┐
│  SearchEngine    │ - Read-only operations
│  (Search)        │ - Can retry on failure
└──────────────────┘
   Mitigation: Graceful error handling, fallback to Stage 1
```

---

## Performance Bottleneck Map

```
Processing Pipeline:
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│ Upload  │→ │ Parse   │→ │ Embed   │→ │ Store   │
│ <100ms  │  │ 1-5s    │  │ 2.5s/pg │  │ <1s     │
└─────────┘  └─────────┘  └─────────┘  └─────────┘
                   ↑             ↑
                   │             └─ Bottleneck 1: GPU-bound
                   │                (10-20x speedup with MPS)
                   │
                   └─ Bottleneck 2: I/O-bound
                      (DPI, page count)

Search Pipeline:
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│ Query   │→ │ Stage 1 │→ │ Stage 2 │→ │ Format  │
│ 0.2s    │  │ 50-100ms│  │ 100ms   │  │ <10ms   │
└─────────┘  └─────────┘  └─────────┘  └─────────┘
                   ↑             ↑
                   │             └─ Bottleneck 3: Scaling
                   │                (100ms for 100 docs)
                   │
                   └─ Bottleneck 4: ChromaDB
                      (HNSW index size)

Optimization Opportunities:
1. Batch size tuning (visual=4→8 on high-mem systems)
2. INT8 quantization (50% memory, 1.5-2x speed)
3. Parallel page processing (multi-GPU)
4. Result caching (frequent queries)
```

---

*This architecture graph provides a visual representation of the tkr-docusearch system's structure, dependencies, and data flows for knowledge graph analysis.*

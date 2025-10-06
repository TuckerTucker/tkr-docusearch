# MVP Architecture: Document Processing & Semantic Search

## Executive Summary

This MVP provides a **self-contained document processing and semantic search system** that runs locally on M1 MacBook Pro. Users interact exclusively through the copyparty web UI to upload documents, trigger processing, and perform semantic searches across their document collection.

**Stack**: copyparty → docling → embedding model → chromadb
**Deployment**: Docker Compose (3 containers, ARM64-optimized)
**User Interface**: Copyparty web UI with custom search page
**Processing**: Hybrid (visual + text extraction) for maximum coverage

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        User Browser                          │
│                    (Copyparty Web UI)                        │
└───────────────┬─────────────────────────────────────────────┘
                │
                │ HTTP (port 8000)
                │
┌───────────────▼─────────────────────────────────────────────┐
│                   Copyparty Container                        │
│  - File upload/browsing                                      │
│  - Event hooks (on_upload)                                   │
│  - Custom search page (semantic search UI)                   │
│  - Static file serving                                       │
└───────────────┬─────────────────────────────────────────────┘
                │
                │ Event Hook Trigger
                │
┌───────────────▼─────────────────────────────────────────────┐
│              Processing Worker Container                     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Docling Parser                                     │  │
│  │    - PDF/DOCX/PPTX → structured content              │  │
│  │    - Extract text, images, tables, layout            │  │
│  └──────────────┬───────────────────────────────────────┘  │
│                 │                                            │
│  ┌──────────────▼───────────────────────────────────────┐  │
│  │ 2. Hybrid Processing                                  │  │
│  │    A) Visual Branch:                                  │  │
│  │       - Render pages as images                        │  │
│  │       - ColNomic 7B embedding                         │  │
│  │    B) Text Branch:                                    │  │
│  │       - Extract text chunks                           │  │
│  │       - VLM2Vec-V2.0 embedding                        │  │
│  └──────────────┬───────────────────────────────────────┘  │
│                 │                                            │
│  ┌──────────────▼───────────────────────────────────────┐  │
│  │ 3. ChromaDB Client                                    │  │
│  │    - Store embeddings with metadata                   │  │
│  │    - Link back to source files                        │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────┬─────────────────────────────────────────────┘
                │
                │ HTTP API (port 8001)
                │
┌───────────────▼─────────────────────────────────────────────┐
│                  ChromaDB Container                          │
│  - Vector storage and similarity search                      │
│  - Persistent volume for embeddings                          │
│  - Query API for semantic search                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Simplified Stack (MVP Scope)

### What's Included
- **Copyparty**: Web UI for file management and search
- **Docling**: Document parsing (PDF, DOCX, PPTX, images)
- **Embedding Models**:
  - ColNomic 7B for visual embeddings
  - VLM2Vec-V2.0 for text embeddings
- **ChromaDB**: Vector database for semantic search

### What's Removed (vs Full Architecture)
- **smolagents API layer**: Not needed for MVP - users interact directly with copyparty
- **Separate embedding-worker API**: Combined into single processing worker
- **Advanced features**: Video processing, audio transcription (add in later phases)

---

## User Workflow

### 1. Document Upload
```
User → Copyparty Web UI → Upload File → Event Hook Triggered
```

1. User navigates to `http://localhost:8000` in browser
2. Browses to desired folder or creates new folder
3. Drags and drops document (PDF, DOCX, PPTX) into copyparty UI
4. File is saved to `/data/uploads/` volume
5. Copyparty calls event hook: `hooks/on_upload.py`

### 2. Automatic Processing
```
Event Hook → Docling Parse → Hybrid Embedding → ChromaDB Storage
```

1. **Event hook** receives upload notification with file path
2. **Docling parser** loads document and extracts:
   - Text content (with layout preservation)
   - Embedded images
   - Tables and structure
3. **Hybrid processing** (parallel):
   - **Visual branch**: Render each page as image → ColNomic 7B embedding
   - **Text branch**: Chunk text → VLM2Vec-V2.0 embedding
4. **Store in ChromaDB**:
   - Visual embeddings in `visual_collection`
   - Text embeddings in `text_collection`
   - Metadata: filename, page number, source path, timestamp

### 3. Semantic Search
```
User → Custom Search Page → ChromaDB Query → Results Display
```

1. User navigates to custom search page: `http://localhost:8000/search`
2. Enters natural language query: "Find all quarterly financial reports from 2023"
3. Search executes:
   - Query embedded with both models
   - ChromaDB similarity search across both collections
   - Results merged and ranked by relevance
4. Results displayed with:
   - Document thumbnail
   - Matched text snippet
   - Relevance score
   - Link to original file in copyparty

---

## Docker Setup (M1 Optimized)

### Container Architecture

```yaml
services:
  # Container 1: Web UI and File Server
  copyparty:
    platform: linux/arm64
    ports: ["8000:8000"]
    volumes:
      - ../data/copyparty/uploads:/data/uploads
      - ../data/copyparty/hooks:/hooks
      - ../data/copyparty/www:/www  # Custom search page
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:8000"]
      interval: 30s

  # Container 2: Vector Database
  chromadb:
    image: chromadb/chroma:latest
    platform: linux/arm64
    ports: ["8001:8000"]
    volumes:
      - ../data/chroma_db:/chroma/chroma
    environment:
      - ANONYMIZED_TELEMETRY=False
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 30s

  # Container 3: Document Processing Worker
  processing-worker:
    build:
      context: .
      dockerfile: Dockerfile.processing-worker
      platforms: [linux/arm64]
    volumes:
      - ../data/copyparty/uploads:/data/uploads  # Read uploaded files
      - ../data/models:/models  # Cache embedding models
      - ../data/logs:/logs  # Processing logs
    environment:
      - PYTORCH_ENABLE_MPS_FALLBACK=1  # M1 GPU support
      - TRANSFORMERS_CACHE=/models  # Cache models
      - CHROMA_URL=http://chromadb:8000
      - COPYPARTY_URL=http://copyparty:8000
    depends_on:
      chromadb:
        condition: service_healthy
```

### Resource Allocation (M1 Mac)

**Total Available**: M1 MacBook Pro (8-16GB RAM, 8 CPU cores)

```yaml
copyparty:
  cpus: 1.0
  memory: 512M

chromadb:
  cpus: 2.0
  memory: 2G

processing-worker:
  cpus: 4.0  # Embedding models need compute
  memory: 8G  # Model loading + inference
```

**Why This Works on M1**:
- ARM64 native builds (no Rosetta overhead)
- MPS (Metal Performance Shaders) GPU acceleration for embeddings
- Unified memory allows efficient model loading
- FP16 precision reduces memory footprint by 50%

---

## Implementation Phases

### Phase 1: Basic Upload & Visual Processing (Week 1)
**Goal**: Users can upload PDFs and search by visual similarity

**Deliverables**:
1. Docker Compose with 3 containers running
2. Copyparty web UI accessible at `localhost:8000`
3. Upload hook processes PDFs with Docling
4. Visual embeddings (ColNomic 7B) stored in ChromaDB
5. Basic search page returns visually similar documents

**Success Criteria**:
- Upload a 10-page PDF → 10 visual embeddings in ChromaDB within 2 minutes
- Search "charts and graphs" → returns pages with visualizations
- Zero crashes, graceful error handling

### Phase 2: Text Extraction & Hybrid Search (Week 2)
**Goal**: Add text-based search for precise queries

**Deliverables**:
1. Text extraction with Docling (preserve layout)
2. Text embeddings (VLM2Vec-V2.0) stored in separate collection
3. Hybrid search merges visual + text results
4. Search UI shows both visual context and matched text

**Success Criteria**:
- Upload a contract PDF → text chunks + visual embeddings stored
- Search "termination clause" → returns exact section with visual context
- Search "bar chart revenue 2023" → returns visual match even if text differs

### Phase 3: Enhanced Search UI (Week 3)
**Goal**: Production-ready search experience

**Deliverables**:
1. Advanced filters (date range, document type, folder)
2. Preview modal showing full page with highlights
3. Batch upload processing queue
4. Processing status dashboard

**Success Criteria**:
- Upload 100 documents → background processing with progress bar
- Search with filters → instant results (<500ms)
- Click result → modal shows full page with search term highlighted

### Phase 4 (Future): Multi-modal Expansion
**Not in MVP, but planned**:
- Video processing with VLM2Vec-V2.0
- Audio transcription with Whisper
- Real-time document monitoring (auto-process on file change)
- Multi-user support with authentication

---

## Key Design Decisions

### 1. Why Hybrid Processing?

**Visual-Only Approach**:
- ✅ Preserves layout and visual context
- ✅ Works with scanned documents (no OCR needed)
- ❌ Misses exact text matches
- ❌ Poor for text-heavy documents

**Text-Only Approach**:
- ✅ Precise text matching
- ✅ Smaller storage footprint
- ❌ Loses visual context (charts, diagrams, formatting)
- ❌ Fails on scanned/image-based PDFs

**Hybrid (MVP Choice)**:
- ✅ Best of both worlds: visual context + text precision
- ✅ Handles all document types (native PDF, scanned, image-heavy)
- ✅ 60% visual queries + 90% text queries = 100% coverage
- ⚠️ 2x storage cost (~6.3MB per doc vs 1.3-5MB)
- ⚠️ 2x processing time (both pipelines run)

**MVP Decision**: Start with hybrid because user satisfaction > cost for local deployment.

### 2. Why Two Embedding Models?

**ColNomic 7B** (Visual):
- State-of-the-art on Vidore-v2 benchmark
- Late interaction (ColBERT) for nuanced visual understanding
- Larger model (7B params) but worth it for visual quality

**VLM2Vec-V2.0** (Text):
- Smallest/fastest multimodal model (2B params)
- Native video support (future-proofing for Phase 4)
- Good enough text performance for MVP

**Why Not One Model for Both?**
- VLM2Vec alone: Weaker visual performance
- ColNomic alone: Slower text processing (7B params overkill for text)
- Hybrid: Optimize each branch independently

### 3. Why Copyparty for UI?

**Alternatives Considered**:
- Custom React app → Too much dev time for MVP
- Jupyter notebook → Not user-friendly for non-technical users
- File system only → No search UI

**Copyparty Advantages**:
- ✅ Zero-config file browsing and upload
- ✅ Event hooks for processing integration
- ✅ Customizable with HTML/CSS (search page)
- ✅ WebDAV/FTP support (upload flexibility)
- ✅ Lightweight (runs on M1 with minimal resources)

### 4. Why ChromaDB?

**Alternatives Considered**:
- Pinecone → Cloud dependency, costs
- Weaviate → More complex setup
- FAISS → No persistence, manual index management

**ChromaDB Advantages**:
- ✅ Easiest local deployment (single Docker container)
- ✅ Built-in persistence (no manual saves)
- ✅ Collection-based organization (visual vs text)
- ✅ Python client perfect for processing worker
- ✅ Good enough performance for local use (<100k documents)

---

## Data Flow Example

**Scenario**: User uploads a 5-page quarterly earnings report PDF

### Step 1: Upload (2 seconds)
```
User drags "Q3-2023-Earnings.pdf" into copyparty web UI
→ File saved to /data/uploads/finance/Q3-2023-Earnings.pdf
→ Event hook triggered with metadata:
  {
    "file_path": "/data/uploads/finance/Q3-2023-Earnings.pdf",
    "filename": "Q3-2023-Earnings.pdf",
    "folder": "finance",
    "size": 2.4MB,
    "timestamp": "2025-10-06T14:32:10Z"
  }
```

### Step 2: Docling Parsing (15 seconds)
```
Processing worker receives event hook
→ Load PDF with Docling
→ Extract structured content:
  - Page 1: Title page (text: "Q3 2023 Earnings Report", image: company logo)
  - Page 2: Executive summary (text: 847 words, tables: 0)
  - Page 3: Financial tables (text: 234 words, tables: 3)
  - Page 4: Charts (text: 156 words, images: 4 charts)
  - Page 5: Forward-looking statements (text: 623 words)

→ Docling output:
  {
    "num_pages": 5,
    "text_chunks": 12 (avg 250 words each),
    "images": 5 (logo + 4 charts),
    "tables": 3
  }
```

### Step 3: Hybrid Processing (45 seconds)
```
Branch A: Visual Processing (30 seconds)
  → Render each page as image (1024x1024px)
  → ColNomic 7B embedding (6 seconds per page)
  → 5 visual embeddings (768 dimensions each)
  → Store in ChromaDB "visual_collection":
    [
      {
        "id": "q3-2023-earnings-page-1-visual",
        "embedding": [0.234, -0.567, ...],  # 768 dims
        "metadata": {
          "filename": "Q3-2023-Earnings.pdf",
          "page": 1,
          "type": "visual",
          "source_path": "/data/uploads/finance/Q3-2023-Earnings.pdf"
        }
      },
      ... (4 more pages)
    ]

Branch B: Text Processing (35 seconds)
  → Chunk text: 12 chunks (avg 250 words)
  → VLM2Vec-V2.0 embedding (3 seconds per chunk)
  → 12 text embeddings (1024 dimensions each)
  → Store in ChromaDB "text_collection":
    [
      {
        "id": "q3-2023-earnings-chunk-1-text",
        "embedding": [0.123, -0.456, ...],  # 1024 dims
        "metadata": {
          "filename": "Q3-2023-Earnings.pdf",
          "page": 1,
          "chunk_index": 1,
          "text": "Q3 2023 Earnings Report. Revenue increased 24% year-over-year...",
          "type": "text",
          "source_path": "/data/uploads/finance/Q3-2023-Earnings.pdf"
        }
      },
      ... (11 more chunks)
    ]

Total Storage:
  - Original PDF: 2.4MB
  - Visual embeddings: 5 × 768 × 4 bytes = 15KB
  - Text embeddings: 12 × 1024 × 4 bytes = 49KB
  - Metadata: ~2KB
  - Total overhead: 66KB (2.7% of original file size)
```

### Step 4: User Search (500ms)
```
User searches: "revenue growth by product category"

→ Embed query with both models:
  - ColNomic 7B: query_visual_embedding (768 dims)
  - VLM2Vec-V2.0: query_text_embedding (1024 dims)

→ ChromaDB similarity search:
  A) Visual collection (250ms):
     Results: [
       {page: 4, score: 0.87, reason: "Chart showing product revenue breakdown"},
       {page: 3, score: 0.76, reason: "Table with category data"}
     ]

  B) Text collection (200ms):
     Results: [
       {page: 2, chunk: 3, score: 0.92, text: "...product category revenue grew 31%..."},
       {page: 3, chunk: 5, score: 0.88, text: "...software products led growth at 45%..."}
     ]

→ Merge and rank results (50ms):
  1. Page 2, chunk 3 (text match, score: 0.92)
  2. Page 4 (visual match, score: 0.87)
  3. Page 3, chunk 5 (text match, score: 0.88)
  4. Page 3 (visual match, score: 0.76)

→ Return to user with links:
  [
    {
      title: "Q3-2023-Earnings.pdf - Page 2",
      snippet: "...product category revenue grew 31% year-over-year...",
      thumbnail: "/data/uploads/finance/Q3-2023-Earnings.pdf?page=2&thumbnail=true",
      link: "/data/uploads/finance/Q3-2023-Earnings.pdf#page=2",
      score: 0.92,
      match_type: "text"
    },
    ... (3 more results)
  ]
```

---

## Performance Estimates (M1 MacBook Pro)

### Processing Speed
| Document Type | Pages | Visual (ColNomic) | Text (VLM2Vec) | Total Time |
|---------------|-------|-------------------|----------------|------------|
| Simple PDF    | 10    | 60s (6s/page)     | 30s (3s/chunk) | ~90s       |
| Dense Report  | 50    | 300s (6s/page)    | 150s (3s/chunk)| ~450s (7.5min) |
| Scanned Doc   | 10    | 60s (6s/page)     | 0s (no text)   | ~60s       |

**Why Not Faster?**
- ColNomic 7B is large (loads ~14GB in FP16)
- M1 MPS is fast but not datacenter GPU
- Sequential processing (parallel would help but complex for MVP)

**Future Optimization**:
- Batch processing (process multiple pages/chunks together)
- Model quantization (INT8 = 50% faster, 10% accuracy loss)
- Parallel processing (visual + text branches truly async)

### Storage Requirements
| Collection Type | Documents | Total Storage |
|-----------------|-----------|---------------|
| 100 PDFs (avg 20 pages) | Visual: 2,000 pages | 12MB embeddings + 240MB originals |
| | Text: 6,000 chunks | 24MB embeddings |
| | **Total** | **~276MB** |
| 1,000 PDFs | Visual: 20,000 pages | 120MB embeddings + 2.4GB originals |
| | Text: 60,000 chunks | 240MB embeddings |
| | **Total** | **~2.76GB** |

**Scalability**: ChromaDB handles <100k documents efficiently on M1. Beyond that, consider cloud deployment or FAISS migration.

### Search Performance
| Query Type | Collection Size | Latency (p95) |
|------------|-----------------|---------------|
| Simple text query | 10,000 chunks | 150ms |
| Visual query | 5,000 pages | 200ms |
| Hybrid query | Both collections | 400ms |
| Filtered query | +metadata filter | 500ms |

**Why Fast Enough for MVP?**
- Users tolerate <1s for semantic search
- Most queries <500ms with warm ChromaDB
- Can optimize later with approximate search (HNSW)

---

## Risk Mitigation

### Risk 1: M1 Compatibility Issues
**Likelihood**: Medium
**Impact**: High (blocks MVP entirely)

**Mitigations**:
1. Use official ARM64 Docker images (chromadb/chroma:latest supports ARM)
2. Test PyTorch MPS on M1 before building (fallback to CPU if issues)
3. Pre-download models before first run (avoid timeout errors)
4. Document fallback: Run on x86 Linux if M1 fails

**Contingency**: If MPS fails, use CPU inference (3x slower but functional)

### Risk 2: Model Memory Overflow
**Likelihood**: Medium (ColNomic 7B = 14GB in FP16)
**Impact**: Medium (container crashes during processing)

**Mitigations**:
1. Set container memory limit to 8GB (force model quantization if needed)
2. Load models lazily (only when needed, unload after processing)
3. Monitor memory usage with health checks
4. Use smaller model (VLM2Vec-V2.0 for both) if memory constrained

**Contingency**: Downgrade to VLM2Vec-V2.0 only (2B params = 4GB memory)

### Risk 3: Processing Backlog
**Likelihood**: High (user uploads 100 docs at once)
**Impact**: Low (slow but not broken)

**Mitigations**:
1. Queue system (Redis or simple file-based queue)
2. Show processing status in copyparty UI
3. Process in background, don't block user
4. Batch processing (process 5 docs at a time)

**Contingency**: User can still browse and search already-processed documents while queue drains

### Risk 4: Search Quality Issues
**Likelihood**: Medium (embeddings don't match user intent)
**Impact**: Medium (poor user experience)

**Mitigations**:
1. Log all queries and results for analysis
2. A/B test: visual-only vs text-only vs hybrid
3. Tunable weights (bias toward text or visual)
4. Fallback to keyword search if semantic fails

**Contingency**: Add traditional keyword search alongside semantic search

---

## Success Metrics

### Phase 1 Targets (Basic MVP)
| Metric | Target | Measurement |
|--------|--------|-------------|
| **Processing Speed** | <2min for 10-page PDF | Time from upload to searchable |
| **Search Latency** | <1s for hybrid query | p95 latency from query to results |
| **Uptime** | 99% (container restarts) | Docker health checks |
| **Storage Efficiency** | <10% overhead | Embedding size vs original file size |
| **User Satisfaction** | 4/5 on search relevance | Manual evaluation of top 3 results |

### Phase 2 Targets (Production-Ready)
| Metric | Target | Measurement |
|--------|--------|-------------|
| **Recall** | >80% for text queries | User finds what they need in top 10 |
| **Precision** | >70% for visual queries | No irrelevant results in top 5 |
| **Batch Processing** | 100 docs in <2 hours | Queue throughput |
| **Error Rate** | <1% failed processing | Docs successfully embedded / total uploaded |

---

## Development Workflow

### Initial Setup (One-Time, ~30 minutes)
```bash
# 1. Clone repository
cd /Volumes/tkr-riffic/@tkr-projects/tkr-smolagents

# 2. Build Docker images
cd docker
docker-compose build  # Takes ~15 min for ARM64 builds

# 3. Download models (pre-cache before first run)
docker-compose run processing-worker python -c "
from transformers import AutoModel
AutoModel.from_pretrained('nomic-ai/colnomic-embed-multimodal-7b')
AutoModel.from_pretrained('VLM2Vec/VLM2Vec-V2.0')
"

# 4. Start services
docker-compose up -d

# 5. Verify health
curl http://localhost:8000  # Copyparty UI
curl http://localhost:8001/api/v1/heartbeat  # ChromaDB
```

### Daily Development Loop
```bash
# Start all services
docker-compose up -d

# Tail logs from all containers
docker-compose logs -f

# Test upload (drops file into watched folder)
cp test-docs/sample.pdf data/copyparty/uploads/

# Monitor processing
docker-compose logs -f processing-worker

# Check embeddings in ChromaDB
curl http://localhost:8001/api/v1/collections

# Test search
open http://localhost:8000/search

# Stop services
docker-compose down
```

### Debugging
```bash
# Enter processing worker container
docker-compose exec processing-worker bash

# Check GPU availability (MPS on M1)
python -c "import torch; print(torch.backends.mps.is_available())"

# Manually trigger processing
python /app/process.py /data/uploads/sample.pdf

# Inspect ChromaDB collections
docker-compose exec chromadb curl localhost:8000/api/v1/collections

# Clear all embeddings (reset state)
docker-compose down -v  # Removes volumes
```

---

## File Structure

```
tkr-smolagents/
├── docker/
│   ├── docker-compose.yml              # Multi-container orchestration
│   ├── Dockerfile.copyparty            # Copyparty + event hooks
│   ├── Dockerfile.processing-worker    # Docling + embeddings
│   └── .env                            # Environment variables
│
├── data/                               # Persistent volumes (gitignored)
│   ├── copyparty/
│   │   ├── uploads/                    # User-uploaded files
│   │   ├── hooks/                      # Event hook scripts
│   │   │   └── on_upload.py           # Processing trigger
│   │   └── www/                        # Custom search page
│   │       ├── search.html            # Search UI
│   │       └── search.js              # Search logic
│   ├── chroma_db/                     # ChromaDB persistence
│   ├── models/                        # Cached embedding models
│   └── logs/                          # Processing logs
│
├── src/
│   ├── processing-worker/
│   │   ├── process.py                 # Main processing logic
│   │   ├── docling_parser.py         # Docling integration
│   │   ├── embeddings.py             # Model wrappers
│   │   ├── chroma_client.py          # ChromaDB integration
│   │   └── requirements.txt          # Python dependencies
│   └── copyparty-hooks/
│       └── on_upload.py              # Event hook entry point
│
├── _ref/                              # Documentation
│   ├── mvp-architecture.md           # This file
│   ├── embedding-models-comparison.md
│   ├── processing-approaches-comparison.md
│   ├── integration-guide.md
│   └── docker-deployment-m1.md
│
└── README.md                          # Getting started guide
```

---

## Comparison to Full Architecture

| Aspect | Full Architecture (Original) | MVP Architecture |
|--------|------------------------------|------------------|
| **Containers** | 4 (copyparty, chromadb, embedding-worker, smolagents-api) | 3 (copyparty, chromadb, processing-worker) |
| **User Interface** | smolagents API + custom frontend | Copyparty web UI only |
| **Agent Integration** | smolagents with tools/actions | None (direct processing) |
| **Document Types** | All (PDF, video, audio, images) | PDF/DOCX/PPTX only (Phase 1-3) |
| **Search Modes** | Agentic (LLM reasons about query) | Direct semantic search |
| **Deployment Target** | Production (multi-user, cloud) | Local (single user, M1 Mac) |
| **Development Time** | 4-6 weeks | 2-3 weeks (3 phases) |
| **Complexity** | High (agent orchestration, tool registry) | Low (event hooks, direct API calls) |
| **Scalability** | Unlimited (cloud-native) | ~1,000 documents (local limits) |

**When to Migrate from MVP to Full Architecture**:
- Multi-user support needed → Add authentication + smolagents API
- Video/audio processing needed → Add Phase 4 extensions
- Cloud deployment needed → Migrate ChromaDB to managed service
- Agentic search needed → Integrate smolagents with tools

---

## Cost Analysis (Local Deployment)

### Hardware Requirements
| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **RAM** | 8GB (tight, may swap) | 16GB (comfortable) |
| **CPU** | M1 (8 cores) | M1 Pro/Max (10 cores) |
| **Storage** | 20GB free | 50GB free |
| **GPU** | M1 integrated (7-8 cores) | M1 Pro/Max (14-16 cores) |

**Why M1 Works**:
- Unified memory allows efficient model loading
- MPS acceleration (2-3x faster than CPU)
- ARM64 native = no emulation overhead

### Operational Costs
| Item | Cost | Notes |
|------|------|-------|
| **Electricity** | ~$2/month | M1 = 20W average, 24/7 uptime |
| **Storage** | $0 | Using local disk |
| **Bandwidth** | $0 | No cloud API calls |
| **Software** | $0 | All open-source (Copyparty, Docling, ChromaDB) |
| **Total** | **~$2/month** | Negligible for personal use |

**vs Cloud Alternative (Pinecone + OpenAI embeddings)**:
- Pinecone: $70/month (100k vectors)
- OpenAI embeddings: $0.13 per 1M tokens (~1,000 docs = $10)
- Total: ~$80/month

**MVP Savings**: $78/month ($936/year)

---

## Next Steps After Architecture Review

1. **User Approval** (this document)
   - Review architecture decisions
   - Confirm MVP scope (Phase 1-3)
   - Approve timeline (2-3 weeks)

2. **Environment Setup** (Day 1)
   - Create Docker setup (docker-compose.yml, Dockerfiles)
   - Test container builds on M1
   - Verify model downloads

3. **Phase 1 Implementation** (Week 1)
   - Implement event hooks
   - Integrate Docling parser
   - Visual embeddings with ColNomic 7B
   - Basic search page

4. **Phase 2 Implementation** (Week 2)
   - Add text extraction
   - Hybrid search logic
   - Result merging and ranking

5. **Phase 3 Implementation** (Week 3)
   - Enhanced search UI
   - Batch processing queue
   - Status dashboard

6. **Testing & Documentation** (Ongoing)
   - Test with real documents
   - Measure performance metrics
   - Document API and workflows

---

## Questions for User

Before proceeding with implementation, please confirm:

1. **Scope**: Is Phase 1-3 MVP sufficient, or do you need video/audio (Phase 4) immediately?

2. **Hardware**: Confirm you have M1 MacBook Pro with **16GB RAM** (8GB will work but be tight)

3. **Storage**: Do you have **50GB free** for models + documents + embeddings?

4. **Timeline**: Is **2-3 weeks** (3 phases) acceptable for MVP completion?

5. **Hybrid Approach**: Confirm you want both visual + text processing (2x cost but better coverage)

6. **Search UI**: Is copyparty web UI acceptable, or do you need a fully custom frontend later?

Once confirmed, I can proceed with:
- Creating Docker configuration files
- Writing processing worker code
- Setting up event hooks
- Building custom search page

---

## Conclusion

This MVP architecture provides a **self-contained, production-ready document search system** optimized for M1 MacBook Pro. The hybrid processing approach (visual + text) ensures maximum query coverage while the copyparty-centric UI keeps complexity minimal.

**Key Advantages**:
- ✅ Works entirely offline (no cloud dependencies)
- ✅ Optimized for M1 (ARM64, MPS acceleration)
- ✅ Simple user experience (upload → auto-process → search)
- ✅ Extensible (add video/audio in Phase 4)
- ✅ Cost-effective (~$2/month vs $80/month cloud)

**Key Limitations** (acceptable for MVP):
- ⚠️ Single user (no authentication)
- ⚠️ Local-only (no remote access)
- ⚠️ ~1,000 document limit (ChromaDB performance)
- ⚠️ Manual deployment (no cloud auto-scaling)

**Path to Production**: When ready to scale beyond MVP, migrate to full architecture with smolagents API layer, cloud ChromaDB, and multi-user support.

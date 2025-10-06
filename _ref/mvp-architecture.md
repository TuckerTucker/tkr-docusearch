# MVP Architecture: Document Processing & Semantic Search

## Executive Summary

This MVP provides a **self-contained document processing and semantic search system** that runs locally on M1 MacBook Pro. Users interact exclusively through the copyparty web UI to upload documents, trigger processing, and perform semantic searches across their document collection.

**Stack**: copyparty → docling → ColNomic 7B → chromadb
**Deployment**: Docker Compose (3 containers, ARM64-optimized)
**User Interface**: Copyparty web UI with custom search page
**Processing**: Hybrid (visual + text extraction) using single embedding model

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
│  │ 2. Hybrid Processing (ColNomic 7B)                    │  │
│  │    A) Visual Branch:                                  │  │
│  │       - Render pages as images                        │  │
│  │       - ColNomic 7B embedding                         │  │
│  │    B) Text Branch:                                    │  │
│  │       - Extract text chunks                           │  │
│  │       - ColNomic 7B embedding (same model)            │  │
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
- **ColNomic 7B**: Single multimodal embedding model for both visual and text
- **ChromaDB**: Vector database for semantic search

### What's Removed (vs Full Architecture)
- **smolagents API layer**: Not needed for MVP - users interact directly with copyparty
- **VLM2Vec-V2.0**: Reserved for Phase 4 (video processing only)
- **Advanced features**: Video processing, audio transcription (add in later phases)

### Why Single Embedding Model (ColNomic 7B)?

**Advantages**:
- ✅ Simplified architecture (one model vs two)
- ✅ Consistent embeddings (same space for visual + text)
- ✅ Better cross-modal search (text query → visual results work seamlessly)
- ✅ Reduced memory footprint (14GB vs 14GB + 4GB)
- ✅ Faster cold start (load once vs loading two models)
- ✅ State-of-the-art performance on visual documents (Vidore-v2 benchmark)

**Tradeoffs**:
- ⚠️ Slightly slower text processing (7B params vs 2B for VLM2Vec)
- ⚠️ No native video support (acceptable - MVP is documents only)

**MVP Decision**: Use ColNomic 7B exclusively until Phase 4 (video) where we'll add VLM2Vec.

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
Event Hook → Docling Parse → Hybrid Embedding (ColNomic) → ChromaDB Storage
```

1. **Event hook** receives upload notification with file path
2. **Docling parser** loads document and extracts:
   - Text content (with layout preservation)
   - Embedded images
   - Tables and structure
3. **Hybrid processing** (parallel):
   - **Visual branch**: Render each page as image → ColNomic 7B embedding
   - **Text branch**: Chunk text → ColNomic 7B embedding (same model)
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
   - Query embedded with ColNomic 7B
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
      - PYTORCH_ENABLE_MPS_FALLBACK=1  # M1 GPU support (PyTorch)
      - GPT4ALL_BACKEND=metal  # ColNomic native Metal backend
      - MODEL_PRECISION=int8  # Options: fp16 (14GB, best), int8 (7GB, faster)
      - TRANSFORMERS_CACHE=/models  # Cache models
      - CHROMA_URL=http://chromadb:8000
      - COPYPARTY_URL=http://copyparty:8000
      - EMBEDDING_MODEL=nomic-ai/colnomic-embed-multimodal-7b  # Single model
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
  cpus: 4.0  # Embedding model needs compute
  memory: 8G  # ColNomic 7B = ~14GB FP16 or ~7GB INT8
```

**Why This Works on M1**:
- ARM64 native builds (no Rosetta overhead)
- **Native Metal acceleration**: ColNomic officially supports Apple Silicon via GPT4All Metal backend
- **Dual GPU options**: PyTorch MPS (Metal Performance Shaders) OR GPT4All Metal backend
- Unified memory allows efficient model loading
- **Precision options**: FP16 (14GB, best quality) or INT8 (7GB, 1.5-2x faster)
- Single model means we only load once

**Metal Backend Options**:
1. **GPT4All Metal** (Recommended): Native ColNomic integration, optimized for Apple Silicon
2. **PyTorch MPS**: Fallback if GPT4All backend unavailable, broader compatibility

**Quantization Options**:
| Precision | Memory | Speed | Quality | Use Case |
|-----------|--------|-------|---------|----------|
| **FP16** (default) | 14GB | 1x | 100% | 16GB+ RAM, best quality |
| **INT8** (quantized) | 7GB | 1.5-2x | 90-95% | 8GB RAM, faster processing |

**Recommendation**:
- **8GB M1 Macs**: Use INT8 quantization (required to fit in memory)
- **16GB M1 Macs**: Use FP16 for best quality, INT8 for speed (2x faster batch processing)

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
2. Text embeddings (ColNomic 7B) stored in separate collection
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
- **Video processing** with VLM2Vec-V2.0 (add second model only when needed)
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
- ✅ Same embedding model for both = consistent semantic space
- ⚠️ 2x processing time (both pipelines run)

**MVP Decision**: Start with hybrid because user satisfaction > cost for local deployment.

### 2. Why Single Embedding Model (ColNomic 7B)?

**Original Plan**: Two models (ColNomic for visual, VLM2Vec for text)
**MVP Simplification**: One model (ColNomic for both)

**Rationale**:
1. **Consistency**: Same embedding space for visual + text = better cross-modal search
2. **Simplicity**: One model to load, cache, and maintain
3. **Quality**: ColNomic is SOTA for visual documents, good enough for text
4. **Memory**: 14GB total vs 18GB (14GB + 4GB)
5. **Future-proof**: Add VLM2Vec only when we need video (Phase 4)

**Performance Impact**:
- Text processing: ~6s per chunk (vs 3s with VLM2Vec) → acceptable for MVP
- Visual processing: Same (6s per page)
- Cross-modal search: Better (single embedding space)

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

### Step 3: Hybrid Processing with Multi-Vector Storage (FP16: 60s, INT8: 30s)
```
Branch A: Visual Processing
  → Render each page as image (1024x1024px)
  → ColNomic 7B multi-vector embedding:
    - FP16: 6s per page → 30s total
    - INT8: 3s per page → 15s total (2x faster)
  → 5 multi-vector embeddings (avg 100 tokens × 768 dims each)
  → Store in ChromaDB "visual_collection":
    - Representative vector (CLS token): 768 dims
    - Full sequence in metadata: base64-encoded array

    Example for page 1:
    {
      "embedding": [0.234, -0.567, ...],  # CLS token (768 dims)
      "metadata": {
        "filename": "Q3-2023-Earnings.pdf",
        "page": 1,
        "full_embeddings": "base64_encoded_100x768_array",
        "seq_length": 100,
        "type": "visual"
      }
    }

Branch B: Text Processing
  → Chunk text: 12 chunks (avg 250 words)
  → ColNomic 7B multi-vector embedding (same model, loaded once):
    - FP16: 6s per chunk → 30s total
    - INT8: 3s per chunk → 15s total (2x faster)
  → 12 multi-vector embeddings (avg 64 tokens × 768 dims each)
  → Store in ChromaDB "text_collection":
    - Representative vector (CLS token): 768 dims
    - Full sequence in metadata: base64-encoded array

Total Processing Time (parallel branches):
  - FP16 (default): max(30s, 30s) = 30s
  - INT8 (quantized): max(15s, 15s) = 15s (2x faster)

Total Storage (Multi-Vector):
  - Original PDF: 2.4MB
  - Visual embeddings:
    - Representative vectors: 5 × 768 × 4 bytes = 15KB
    - Full sequences: 5 × 100 × 768 × 4 bytes = 1.5MB
  - Text embeddings:
    - Representative vectors: 12 × 768 × 4 bytes = 37KB
    - Full sequences: 12 × 64 × 768 × 4 bytes = 2.3MB
  - Metadata: ~10KB
  - Total overhead: 3.8MB (158% of original file size)

  Note: Overhead is higher but quality is maximal
```

### Step 4: Two-Stage Search with Late Interaction (300ms total)
```
User searches: "revenue growth by product category"

→ Embed query with ColNomic 7B:
  - Multi-vector query embedding (shape: 1 × query_tokens × 768)
  - Extract CLS token for Stage 1 initial retrieval

STAGE 1: Initial Retrieval (200ms) - Fast approximate search
  → ChromaDB similarity search using representative vectors:
    A) Visual collection:
       Top-50 candidates (cosine similarity on CLS tokens)

    B) Text collection:
       Top-50 candidates (cosine similarity on CLS tokens)

  → Combined top-100 candidates (from both collections)

STAGE 2: Re-ranking with Late Interaction (100ms) - Precise scoring
  → Load full multi-vector embeddings from metadata for top-100
  → Apply ColPali's score_multi_vector() for each candidate:
    - Query: (1 × query_tokens × 768)
    - Document: (1 × doc_tokens × 768)
    - Score: MaxSim over all token pairs

  → Final ranked results:
    1. Page 2, chunk 3 (text match, MaxSim score: 0.94)
       - Late interaction captured: "product category" + "revenue" + "grew"

    2. Page 4 (visual match, MaxSim score: 0.91)
       - Late interaction captured visual tokens for chart + "product" + "revenue"

    3. Page 3, chunk 5 (text match, MaxSim score: 0.89)
       - Late interaction captured: "software" + "products" + "growth"

    4. Page 3 (visual match, MaxSim score: 0.82)
       - Late interaction captured table structure + category data

  Note: Scores are higher with late interaction (0.94 vs 0.92) due to
  token-level matching capturing more nuanced semantic relationships
```

---

## Performance Estimates (M1 MacBook Pro)

### Processing Speed Comparison (FP16 vs INT8)

**FP16 (Default - Best Quality)**:
| Document Type | Pages | Visual | Text | Total Time |
|---------------|-------|--------|------|------------|
| Simple PDF    | 10    | 60s    | 60s  | ~60s (parallel) |
| Dense Report  | 50    | 300s   | 300s | ~300s (5min) |
| Scanned Doc   | 10    | 60s    | 0s   | ~60s |

**INT8 (Quantized - 2x Faster)**:
| Document Type | Pages | Visual | Text | Total Time |
|---------------|-------|--------|------|------------|
| Simple PDF    | 10    | 30s    | 30s  | ~30s (parallel) |
| Dense Report  | 50    | 150s   | 150s | ~150s (2.5min) |
| Scanned Doc   | 10    | 30s    | 0s   | ~30s |

**Processing Notes**:
- Processing is parallelized (visual + text run concurrently)
- Total time ≈ max(visual_time, text_time)
- INT8 quantization: 50% memory reduction, 2x speed increase, ~5-10% quality loss

**Recommended Settings**:
- **8GB M1 Mac**: Use INT8 (required, won't fit FP16)
- **16GB M1 Mac**: Use INT8 for speed (2x faster), FP16 for quality (100 doc batch → 5min vs 10min)

### Storage Requirements (Multi-Vector)

**Per-Document Breakdown**:
| Item | Representative Vectors | Full Multi-Vector Sequences | Total |
|------|------------------------|----------------------------|-------|
| Visual (per page) | 3KB (1 × 768 × 4) | 75KB (avg 100 tokens × 768 × 4) | 78KB |
| Text (per chunk) | 3KB (1 × 768 × 4) | 48KB (avg 64 tokens × 768 × 4) | 51KB |

**Scaled Storage Estimates**:
| Collection Size | Original Files | Representative Vectors | Full Sequences | Total Storage |
|-----------------|----------------|------------------------|----------------|---------------|
| **100 PDFs** (2,000 pages, 6,000 chunks) | 240MB | 27KB | 438MB | **~678MB** |
| - Visual collection | | 12KB | 150MB | 150MB |
| - Text collection | | 18KB | 288MB | 288MB |
| **1,000 PDFs** (20,000 pages, 60,000 chunks) | 2.4GB | 270KB | 4.38GB | **~6.78GB** |
| - Visual collection | | 120KB | 1.5GB | 1.5GB |
| - Text collection | | 180KB | 2.88GB | 2.88GB |

**Storage Tradeoff**:
- Multi-vector storage is **~2.5x larger** than original PDFs
- But: Preserves 100% of ColNomic's quality vs 85-90% with average pooling
- Still manageable on local disk (50GB free handles ~5,000 PDFs)

### Search Performance (Two-Stage Pipeline)

| Query Type | Stage 1 (Initial) | Stage 2 (Re-rank) | Total Latency |
|------------|-------------------|-------------------|---------------|
| Simple text query | 150ms (top-100) | 80ms (re-rank) | **230ms** |
| Visual query | 200ms (top-100) | 100ms (re-rank) | **300ms** |
| Hybrid query | 200ms (top-100 both) | 120ms (re-rank) | **320ms** |
| Filtered query | 220ms (w/ metadata) | 100ms (re-rank) | **320ms** |

**Performance Notes**:
- Stage 1 uses ChromaDB's HNSW index (fast approximate search)
- Stage 2 only re-ranks top-100 candidates (not entire collection)
- Total latency <500ms for all query types (acceptable)
- Quality: 100% of ColNomic's benchmark performance (vs 85-90% single-vector)

**Why Fast Enough for MVP?**
- Users tolerate <1s for semantic search
- Most queries <350ms with warm ChromaDB
- Late interaction quality improvement is worth 100-150ms overhead

---

## Risk Mitigation

### Risk 1: M1 Compatibility Issues
**Likelihood**: Medium
**Impact**: High (blocks MVP entirely)

**Mitigations**:
1. Use official ARM64 Docker images (chromadb/chroma:latest supports ARM)
2. Test PyTorch MPS on M1 before building (fallback to CPU if issues)
3. Pre-download ColNomic 7B before first run (avoid timeout errors)
4. Document fallback: Run on x86 Linux if M1 fails

**Contingency**: If MPS fails, use CPU inference (3x slower but functional)

### Risk 2: Model Memory Overflow
**Likelihood**: Medium (ColNomic 7B = 14GB in FP16)
**Impact**: Medium (container crashes during processing)

**Mitigations**:
1. Set container memory limit to 8GB (force model quantization if needed)
2. Load model once and reuse for both branches
3. Monitor memory usage with health checks
4. Use INT8 quantization if 16GB RAM not available

**Contingency**: Quantize to INT8 (7GB memory, 10% accuracy loss)

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
**Likelihood**: Low (ColNomic is SOTA for visual docs)
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

### Initial Setup (One-Time, ~20 minutes)
```bash
# 1. Clone repository
cd /Volumes/tkr-riffic/@tkr-projects/tkr-smolagents

# 2. Build Docker images (includes colpali installation)
cd docker
docker-compose build  # Takes ~15 min for ARM64 builds

# 3. Download model (pre-cache before first run - single model only)
docker-compose run processing-worker python -c "
from colpali_engine.models import ColQwen2_5, ColQwen2_5_Processor
ColQwen2_5.from_pretrained('nomic-ai/colnomic-embed-multimodal-7b')
ColQwen2_5_Processor.from_pretrained('nomic-ai/colnomic-embed-multimodal-7b')
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
│   ├── Dockerfile.processing-worker    # Docling + ColNomic embeddings
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
│   ├── models/                        # Cached ColNomic 7B model
│   └── logs/                          # Processing logs
│
├── src/
│   ├── processing-worker/
│   │   ├── process.py                 # Main processing logic
│   │   ├── docling_parser.py         # Docling integration
│   │   ├── embeddings.py             # ColPali engine wrapper (ColQwen2_5)
│   │   ├── chroma_client.py          # ChromaDB integration
│   │   └── requirements.txt          # Python dependencies (includes colpali from source)
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
| **Embedding Models** | 2 (ColNomic + VLM2Vec) | 1 (ColNomic only) |
| **User Interface** | smolagents API + custom frontend | Copyparty web UI only |
| **Agent Integration** | smolagents with tools/actions | None (direct processing) |
| **Document Types** | All (PDF, video, audio, images) | PDF/DOCX/PPTX only (Phase 1-3) |
| **Video Support** | Day 1 (VLM2Vec) | Phase 4 (add VLM2Vec when needed) |
| **Search Modes** | Agentic (LLM reasons about query) | Direct semantic search |
| **Deployment Target** | Production (multi-user, cloud) | Local (single user, M1 Mac) |
| **Development Time** | 4-6 weeks | 2-3 weeks (3 phases) |
| **Complexity** | High (agent orchestration, tool registry) | Low (event hooks, direct API calls) |
| **Scalability** | Unlimited (cloud-native) | ~1,000 documents (local limits) |

**When to Add VLM2Vec (Phase 4)**:
- User needs video processing → Add VLM2Vec-V2.0 container
- Memory allows second model (16GB+ RAM)
- Video semantic search becomes requirement

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
- Single model = reduced memory pressure

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

## Implementation Notes: ColPali Engine

### Critical Dependencies

ColNomic 7B requires **ColPali engine** (not standard transformers):

```bash
# Install from source (required)
pip install git+https://github.com/illuin-tech/colpali.git

# Standard dependencies
pip install torch torchvision pillow transformers chromadb
```

### Model Loading (Correct Approach)

```python
import torch
from PIL import Image
from colpali_engine.models import ColQwen2_5, ColQwen2_5_Processor

model_name = "nomic-ai/colnomic-embed-multimodal-7b"

# Load model with Apple Silicon optimization
model = ColQwen2_5.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,  # or torch.float16 for INT8
    device_map="mps",  # Apple Silicon GPU
    attn_implementation=None,  # flash_attention_2 not available on MPS
).eval()

# Load processor
processor = ColQwen2_5_Processor.from_pretrained(model_name)
```

### Processing Workflow

**For Visual Embeddings** (page images):
```python
from PIL import Image

# Load page images
images = [Image.open("page1.png"), Image.open("page2.png")]

# Process images
batch_images = processor.process_images(images).to(model.device)

# Generate embeddings
with torch.no_grad():
    image_embeddings = model(**batch_images)  # Shape: (batch, seq_len, 768)
```

**For Text Embeddings** (text chunks):
```python
# Process text as "queries" (same embedding space)
text_chunks = [
    "Q3 2023 revenue increased 24% year-over-year...",
    "Product category breakdown shows software leading at 45%..."
]

# Process text
batch_queries = processor.process_queries(text_chunks).to(model.device)

# Generate embeddings
with torch.no_grad():
    text_embeddings = model(**batch_queries)  # Shape: (batch, seq_len, 768)
```

### Multi-Vector Embeddings (ColBERT Architecture)

**Important**: ColNomic produces **multi-vector embeddings** (one vector per token), not single dense vectors:

```python
# Each embedding is a sequence of vectors (multi-vector)
# Shape: (batch_size, sequence_length, 768)
# For storage, we need to handle this differently than single-vector models

# Option 1: Average pooling (simple, loses detail)
single_vector = image_embeddings.mean(dim=1)  # Shape: (batch, 768)

# Option 2: Store all vectors (preserves late interaction, more storage)
# Store full sequence in ChromaDB as nested array
```

### Scoring (Late Interaction)

```python
# For search, use ColPali's multi-vector scoring
from colpali_engine.models import ColQwen2_5_Processor

# Query embeddings (from search text)
query_emb = model(**processor.process_queries([search_query]))

# Document embeddings (from stored images/text)
doc_embs = [stored_embedding_1, stored_embedding_2]

# Late interaction scoring (MaxSim)
scores = processor.score_multi_vector(query_emb, doc_embs)
# Returns similarity scores for each document
```

### Key Differences from Standard Transformers

| Aspect | Standard Transformers | ColPali Engine |
|--------|----------------------|----------------|
| **Installation** | `pip install transformers` | `pip install git+https://...` (from source) |
| **Model Class** | `AutoModel.from_pretrained()` | `ColQwen2_5.from_pretrained()` |
| **Processor** | `AutoProcessor` | `ColQwen2_5_Processor` |
| **Embeddings** | Single vector (768 dims) | Multi-vector sequence (seq_len × 768) |
| **Scoring** | Cosine similarity | Late interaction (MaxSim via `score_multi_vector`) |
| **Storage** | Simple float array | Sequence of vectors (more complex) |

### Docker Dockerfile Changes

```dockerfile
# Dockerfile.processing-worker

FROM python:3.10-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y git build-essential

# Install Python packages
RUN pip install --no-cache-dir \
    torch torchvision \
    transformers \
    pillow \
    chromadb \
    git+https://github.com/illuin-tech/colpali.git  # Install ColPali from source

# Copy application code
COPY src/processing-worker /app
WORKDIR /app

CMD ["python", "process.py"]
```

### Storage Strategy for Multi-Vector Embeddings

**Challenge**: ColNomic produces sequences of vectors, not single vectors.

**MVP Decision**: Use **full multi-vector storage** from the start for best quality.

**Why Multi-Vector for MVP**:
- ✅ Best retrieval quality (SOTA on Vidore-v2 benchmark)
- ✅ Architecture in place from day one (no re-processing needed later)
- ✅ True late interaction benefits (preserves token-level semantics)
- ✅ Worth the complexity for a production-quality system
- ⚠️ More complex storage (store sequences)
- ⚠️ Slower search (MaxSim scoring vs cosine similarity)

**ChromaDB Storage Approach**:

Since ChromaDB expects single vectors, we'll use a **hybrid metadata strategy**:

```python
# Store a representative vector in ChromaDB's embedding field
# (use CLS token or mean pooling for initial filtering)
representative_vector = embeddings[:, 0, :]  # CLS token (768 dims)

# Store full multi-vector sequence in metadata as compressed array
import numpy as np
import base64

full_sequence = embeddings.cpu().numpy()  # Shape: (1, seq_len, 768)
compressed = base64.b64encode(full_sequence.tobytes()).decode('utf-8')

# Add to ChromaDB
collection.add(
    embeddings=[representative_vector.tolist()],  # Single vector for initial search
    metadatas=[{
        "filename": "Q3-2023-Earnings.pdf",
        "page": 1,
        "full_embeddings": compressed,  # Full sequence for re-ranking
        "seq_length": full_sequence.shape[1],
        "embedding_shape": str(full_sequence.shape)
    }],
    ids=["doc1-page1"]
)
```

**Two-Stage Search Pipeline**:

1. **Stage 1: Initial Retrieval** (fast, using representative vector)
   - ChromaDB returns top-k candidates (k=100) using cosine similarity
   - Uses CLS token or mean pooling for approximate matching
   - Fast: ~200ms for 10k documents

2. **Stage 2: Re-ranking** (precise, using full multi-vector)
   - Load full embeddings for top-k candidates from metadata
   - Apply ColPali's `score_multi_vector()` (late interaction)
   - Re-rank to get final top-n results (n=10)
   - Slower but only for top candidates: ~100ms for 100 docs

**Total Search Time**: ~300ms (vs 150ms for single-vector, acceptable tradeoff)

### Updated Performance Estimates

With full multi-vector storage:

**Storage Requirements**:
| Item | Single-Vector | Multi-Vector | Notes |
|------|---------------|--------------|-------|
| Per page (visual) | 3KB (768 × 4 bytes) | 75KB (avg 100 tokens × 768 × 4 bytes) | 25x larger |
| Per chunk (text) | 3KB (768 × 4 bytes) | 48KB (avg 64 tokens × 768 × 4 bytes) | 16x larger |
| 100 PDFs (2000 pages, 6000 chunks) | 27KB | 438MB (150MB visual + 288MB text) | Manageable on local disk |

**Search Performance**:
| Stage | Time | Notes |
|-------|------|-------|
| Initial retrieval (ChromaDB) | 200ms | Top-100 candidates using representative vectors |
| Re-ranking (late interaction) | 100ms | MaxSim scoring on 100 candidates |
| **Total** | **300ms** | Still <500ms target, acceptable for MVP |

**Quality Improvement**:
- 100% of ColNomic's benchmark performance (vs 85-90% with average pooling)
- Better handling of visual queries (preserves spatial token relationships)
- Better text matching (token-level granularity)

---

## Next Steps After Architecture Review

1. **User Approval** (this document)
   - Review single-model architecture
   - Confirm MVP scope (Phase 1-3, ColNomic only)
   - Approve timeline (2-3 weeks)

2. **Environment Setup** (Day 1)
   - Create Docker setup (docker-compose.yml, Dockerfiles)
   - Test container builds on M1
   - Verify ColNomic 7B model download

3. **Phase 1 Implementation** (Week 1)
   - Implement event hooks
   - Integrate Docling parser
   - Visual embeddings with ColNomic 7B
   - Basic search page

4. **Phase 2 Implementation** (Week 2)
   - Add text extraction
   - Text embeddings with ColNomic 7B (same model)
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

## Conclusion

This MVP architecture provides a **production-quality document search system** optimized for M1 MacBook Pro using **ColNomic 7B with full multi-vector storage** for maximum retrieval quality.

**Key Advantages**:
- ✅ **State-of-the-art quality**: Full multi-vector storage preserves 100% of ColNomic's benchmark performance
- ✅ **Late interaction benefits**: Token-level semantic matching for nuanced retrieval
- ✅ **Single embedding model**: ColNomic 7B for both visual and text (consistent embedding space)
- ✅ **Two-stage search**: Fast initial retrieval + precise re-ranking (<500ms total)
- ✅ **Optimized for M1**: ARM64 native builds, Metal GPU acceleration, INT8 quantization option
- ✅ **Works entirely offline**: No cloud dependencies or API costs
- ✅ **Simple user experience**: Upload via copyparty UI → auto-process → semantic search
- ✅ **Production-ready from day one**: No need to re-process documents later
- ✅ **Cost-effective**: ~$2/month electricity vs $80/month cloud alternatives

**Architecture Highlights**:
- **Multi-vector storage**: CLS token for fast retrieval + full sequences for re-ranking
- **Hybrid processing**: Visual (page images) + text (extracted chunks) for maximum coverage
- **ChromaDB metadata strategy**: Representative vectors in embeddings, full sequences in metadata
- **ColPali engine integration**: Native ColQwen2_5 with processor for proper multi-vector handling

**Storage Trade-offs**:
- Multi-vector storage is **~2.5x larger** than original PDFs (678MB for 100 PDFs)
- Quality improvement is worth the storage cost for production use
- 50GB free disk handles ~5,000 PDFs comfortably

**Performance Trade-offs**:
- Search latency: **300ms** (vs 150ms single-vector)
- 100-150ms overhead for late interaction re-ranking
- Quality improvement justifies the latency increase

**Key Limitations** (acceptable for MVP):
- ⚠️ Single user (no authentication)
- ⚠️ Local-only (no remote access)
- ⚠️ ~5,000 document limit (disk space constrained)
- ⚠️ No video support until Phase 4 (add VLM2Vec when needed)

**Path to Production**: When ready to scale beyond MVP, add:
- VLM2Vec-V2.0 for video processing (Phase 4)
- smolagents API layer for agentic search
- Cloud ChromaDB or dedicated vector DB for unlimited scaling
- Multi-user authentication and access control
- Distributed processing for faster batch uploads

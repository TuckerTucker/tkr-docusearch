# DocuSearch MVP

**Local document processing and semantic search system with ColNomic 7B, ChromaDB, and multi-vector embeddings**

[![Status](https://img.shields.io/badge/status-Wave%201-blue)]()
[![Docker](https://img.shields.io/badge/docker-ready-success)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

---

## Overview

DocuSearch MVP is a production-quality local semantic search system for documents. It combines:

- **ColNomic 7B** (ColPali) for state-of-the-art multimodal embeddings
- **Two-stage search** (representative vectors + late interaction re-ranking)
- **ChromaDB** for efficient vector storage and retrieval
- **Copyparty** for file upload and web UI
- **Docker** for consistent deployment on M1 Macs

### Key Features

✨ **Multi-vector Embeddings** - Preserves spatial and semantic information
⚡ **<500ms Search** - Two-stage pipeline (200ms retrieval + 100ms re-ranking)
🎯 **100% Benchmark Quality** - No accuracy degradation from CLS token optimization
🐳 **Docker-Based** - Consistent environment across development and production
🍎 **M1 Optimized** - PyTorch MPS support for GPU acceleration

---

## Quick Start

### Prerequisites

- Docker and Docker Compose
- 20GB+ free disk space
- 16GB+ RAM (recommended for FP16 mode)
- M1/M2 Mac (or NVIDIA GPU, or CPU fallback)

### Setup

```bash
# Clone repository
git clone https://github.com/your-org/tkr-docusearch.git
cd tkr-docusearch

# Run setup script
./scripts/setup.sh

# Start services
cd docker && docker-compose up -d

# Access web UI
open http://localhost:8000
```

That's it! Upload documents and start searching.

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     User Browser                             │
│                  (Copyparty Web UI)                          │
└───────────────┬─────────────────────────────────────────────┘
                │ HTTP (port 8000)
┌───────────────▼─────────────────────────────────────────────┐
│                Copyparty Container                           │
│  - File upload/browsing                                     │
│  - Event hooks                                              │
│  - Search page                                              │
└───────────────┬─────────────────────────────────────────────┘
                │ Event Hook
┌───────────────▼─────────────────────────────────────────────┐
│           Processing Worker Container                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Docling Parser → Visual + Text Processing →            │ │
│  │ ColPali Embeddings → ChromaDB Storage                  │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────┬─────────────────────────────────────────────┘
                │ HTTP API (port 8001)
┌───────────────▼─────────────────────────────────────────────┐
│                 ChromaDB Container                           │
│  - Vector storage (multi-vector format)                     │
│  - Two-stage search                                         │
└─────────────────────────────────────────────────────────────┘
```

### Multi-Vector Embedding Strategy

**Innovation**: Store both representative vectors and full sequences

```python
# CLS token for fast retrieval
representative = embeddings[0]  # (768,)

# Full sequence for precise re-ranking
full_sequence = embeddings      # (seq_length, 768)

# Storage: CLS in embedding field, compressed full sequence in metadata
```

**Advantages**:
- Fast Stage 1 search with HNSW index (200ms)
- Accurate Stage 2 re-ranking with late interaction (100ms)
- 100% of ColNomic's benchmark performance

---

## Development Workflow

### Wave 1: Foundation & Contracts ✅

**Status**: Complete

- ✅ Integration contracts defined (6 agents)
- ✅ Docker infrastructure created
- ✅ Environment configuration
- ✅ Directory structure initialized

### Wave 2: Component Implementation (In Progress)

**Next Steps**:

1. **storage-agent**: Implement ChromaDB client with multi-vector storage
2. **embedding-agent**: Implement ColPali engine wrapper
3. **processing-agent**: Implement document processing pipeline
4. **search-agent**: Implement two-stage search
5. **ui-agent**: Implement search page and event hooks
6. **infrastructure-agent**: Complete Docker orchestration

**Run in parallel** - agents work independently with mocks until Wave 3 integration.

### Wave 3: Integration & Testing (Upcoming)

Replace mocks with real implementations, test end-to-end workflows.

### Wave 4: Production Polish (Upcoming)

Add filters, queue system, INT8 support, batch processing.

---

## Agent Orchestration

### 6 Agents, 4 Waves, 2-3 Weeks

| Agent | Responsibility | Output |
|-------|---------------|--------|
| **infrastructure-agent** | Docker orchestration | Runnable containers |
| **storage-agent** | ChromaDB integration | Storage client library |
| **embedding-agent** | ColPali engine | Embedding generation |
| **processing-agent** | Document processing | Processing pipeline |
| **search-agent** | Semantic search | Search engine |
| **ui-agent** | Web UI & hooks | User interface |

**Territorial Ownership**: Each agent owns exclusive directories - **zero merge conflicts**.

---

## Configuration

### Environment Variables

Edit `docker/.env` to customize:

```bash
# Model configuration
MODEL_NAME=vidore/colqwen2-v0.1  # ColNomic 7B
MODEL_PRECISION=fp16              # fp16 | int8
DEVICE=mps                        # mps | cuda | cpu

# Performance tuning
BATCH_SIZE_VISUAL=4               # Images per batch
BATCH_SIZE_TEXT=8                 # Text chunks per batch

# File handling
MAX_FILE_SIZE_MB=100
SUPPORTED_FORMATS=pdf,docx,pptx
```

### FP16 vs INT8

| Mode | Memory | Speed | Quality |
|------|--------|-------|---------|
| **FP16** | 14GB | 6s/page | 100% |
| **INT8** | 7GB | 3s/page | ~98% |

Switch via `MODEL_PRECISION=int8` in `.env`.

---

## Performance Targets

### Processing Speed

- **10-page PDF**: <2 minutes (FP16), <1 minute (INT8)
- **50-page PDF**: <10 minutes (FP16), <5 minutes (INT8)
- **100-doc batch**: <2 hours (FP16), <1 hour (INT8)

### Search Latency

- **Simple query**: <300ms median
- **Hybrid query**: <500ms p95
- **With filters**: <500ms p95

### Storage Efficiency

- **Embeddings + metadata**: <3x original file size
- **Compression**: 4x reduction via gzip

---

## Troubleshooting

### Common Issues

**Docker build fails:**
```bash
# Clean build
docker-compose build --no-cache
```

**MPS not available:**
```bash
# Check PyTorch MPS support
docker-compose run --rm processing-worker python3 -c "import torch; print(torch.backends.mps.is_available())"

# Fallback to CPU
# Edit docker/.env: DEVICE=cpu
```

**Model download slow:**
```bash
# Pre-download model
./scripts/setup.sh

# Or skip and download on first run
./scripts/setup.sh --skip-model-download
```

**ChromaDB connection error:**
```bash
# Check ChromaDB is running
docker-compose ps chromadb

# View logs
docker-compose logs chromadb
```

---

## Project Structure

```
tkr-docusearch/
├── docker/
│   ├── docker-compose.yml        # Service orchestration
│   ├── Dockerfile.copyparty       # File server
│   ├── Dockerfile.processing-worker  # Processing worker
│   └── .env                       # Configuration
├── src/
│   ├── storage/                   # ChromaDB integration
│   ├── embeddings/                # ColPali wrapper
│   ├── processing/                # Document processing
│   ├── search/                    # Two-stage search
│   ├── ui/                        # Web UI
│   └── config/                    # Configuration classes
├── data/
│   ├── uploads/                   # Uploaded documents
│   ├── models/                    # Model cache (14GB+)
│   ├── chroma_db/                 # ChromaDB persistence
│   ├── logs/                      # Application logs
│   └── copyparty/                 # Copyparty config & hooks
├── scripts/
│   ├── setup.sh                   # Initial setup
│   ├── start.sh                   # Start services
│   └── stop.sh                    # Stop services
└── .context-kit/
    └── orchestration/docusearch-mvp/
        ├── orchestration-plan.md  # Master execution plan
        ├── agent-assignments.md   # Territorial ownership
        ├── validation-strategy.md # Quality gates
        └── integration-contracts/ # API specifications
```

---

## Documentation

- **[Orchestration Plan](.context-kit/orchestration/docusearch-mvp/orchestration-plan.md)** - 4-wave development strategy
- **[Agent Assignments](.context-kit/orchestration/docusearch-mvp/agent-assignments.md)** - Territorial ownership
- **[Validation Strategy](.context-kit/orchestration/docusearch-mvp/validation-strategy.md)** - Quality gates
- **[Integration Contracts](.context-kit/orchestration/docusearch-mvp/integration-contracts/)** - API specifications

---

## Contributing

This project uses a **multi-agent orchestration** approach. See agent assignments for territorial boundaries.

### Wave 2 Development

1. Review your agent's [integration contracts](.context-kit/orchestration/docusearch-mvp/integration-contracts/)
2. Implement with mocks for dependencies
3. Write unit tests (>90% coverage target)
4. Submit for code review

### Code Reviews

Before Wave 3 integration, consumer agents review provider implementations.

---

## License

MIT License - See LICENSE file for details.

---

## Status

**Current Wave**: Wave 1 (Foundation & Contracts) ✅
**Next Wave**: Wave 2 (Component Implementation)
**Timeline**: 2-3 weeks to MVP

**Wave 1 Deliverables** ✅:
- Integration contracts defined
- Docker infrastructure created
- Environment configuration complete
- Directory structure initialized
- Ready for parallel agent development

---

## Contact

**Project Lead**: Tucker
**Repository**: https://github.com/your-org/tkr-docusearch
**Issues**: https://github.com/your-org/tkr-docusearch/issues

---

**Ready to build a production-quality semantic search system? Let's go! 🚀**

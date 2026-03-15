# DocuSearch

Local document processing and semantic search with multimodal embeddings, AI-powered research, and a React 19 interface.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  React 19 SPA (port 3333)                                   │
│  Vite 7 + React Router 7 + TanStack Query 5 + Zustand 5    │
└────────────┬────────────────────────────────────────────────┘
             │ HTTP (proxied by Vite)
             ├─→ /api/documents, /search, /images → Worker API
             ├─→ /api/research → Research API
             └─→ /ws → WebSocket (real-time processing updates)
┌────────────▼────────────────────────────────────────────────┐
│  Processing Worker (port 8002)                               │
│  FastAPI · Docling parser · Whisper ASR (MLX)                │
│  File uploads (POST /uploads/) · WebSocket status            │
└────────────┬────────────────────────────────────────────────┘
             │
     ┌───────┴───────┐
     ▼               ▼
┌──────────┐  ┌─────────────┐
│ Koji DB  │  │  Shikomi    │
│ (Lance)  │  │  gRPC:50051 │
│ file DB  │  │  embeddings │
└──────────┘  └─────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Research API (port 8004)                                    │
│  LiteLLM multi-provider · MLX local inference                │
│  Inline citations · Bidirectional highlighting                │
└─────────────────────────────────────────────────────────────┘
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3333 | React 19 SPA (Vite dev server) |
| Worker | 8002 | Document processing, search, file uploads, WebSocket |
| Research API | 8004 | LLM-powered Q&A with citations |
| Shikomi | 50051 | Multimodal embedding service (gRPC) |
| Koji DB | — | Lance-based file database (`data/koji.db`) |

## Prerequisites

- Python 3.10+
- Node.js 18+
- Shikomi binary at `bin/shikomi-worker` (see [build instructions](#building-shikomi))
- Apple Silicon Mac recommended (Metal/MPS GPU acceleration)

## Quick Start

```bash
# 1. Copy and configure environment
cp .env.example .env
# Edit .env with your API keys (OpenAI, Anthropic, or Google for research features)

# 2. Set up the worker environment
./scripts/run-worker-native.sh setup

# 3. Start all services
./scripts/start-all.sh

# 4. Open the app
open http://localhost:3333
```

### Management

```bash
./scripts/start-all.sh          # Start all services
./scripts/start-all.sh --no-vision  # Start without ngrok tunnel
./scripts/stop-all.sh           # Stop all services
./scripts/status.sh             # Check service status
```

## Environment Variables

Key variables (see `.env.example` for full list):

| Variable | Default | Description |
|----------|---------|-------------|
| `KOJI_DB_PATH` | `data/koji.db` | Koji database path |
| `SHIKOMI_GRPC_TARGET` | `localhost:50051` | Shikomi gRPC address |
| `SHIKOMI_USE_MOCK` | `true` | Use mock embeddings for testing |
| `DEVICE` | `mps` | Compute device (`mps`, `cuda`, `cpu`) |
| `LLM_PROVIDER` | `openai` | LLM provider for research |
| `LLM_MODEL` | `gpt-5-nano` | LLM model name |
| `OPENAI_API_KEY` | — | API key for OpenAI |
| `UPLOADS_DIR` | `data/uploads` | Upload storage directory |
| `ASR_ENABLED` | `true` | Enable audio transcription |
| `WORKER_PORT` | `8002` | Worker API port |
| `RESEARCH_API_PORT` | `8004` | Research API port |
| `VITE_FRONTEND_PORT` | `3333` | Frontend dev server port |

## Development

### Backend Tests

```bash
pytest                          # Run all backend tests
pytest tests/api/               # Run API tests only
pytest -x --tb=short            # Stop on first failure
```

### Frontend

```bash
cd frontend
npm install                     # Install dependencies
npm run dev                     # Dev server with HMR
npm test                        # Run Vitest tests
npm run test:e2e                # Run Playwright E2E tests
npm run build                   # Production build
```

## Project Structure

```
tkr-docusearch/
├── src/                        # Python backend
│   ├── api/                    # FastAPI routes and models
│   ├── embeddings/             # Shikomi embedding client
│   ├── processing/             # Docling parser, Whisper ASR, worker
│   ├── search/                 # Semantic search engine
│   ├── storage/                # Koji database client
│   ├── research/               # LLM research service
│   └── config/                 # Configuration
├── frontend/                   # React 19 SPA
│   ├── src/components/         # UI components
│   ├── src/features/           # Feature modules
│   ├── src/views/              # Page views
│   ├── src/hooks/              # Custom hooks
│   ├── src/services/           # API client
│   └── src/stores/             # Zustand stores
├── tests/                      # Backend pytest suite
├── scripts/                    # Start/stop/status scripts
├── data/                       # Runtime data (uploads, DB)
└── bin/                        # Shikomi binary
```

## Building Shikomi

The Shikomi embedding service is built from the `tkr-koji` repo:

```bash
cd /path/to/tkr-koji
cargo build --release --features server -p shikomi
cp target/release/shikomi-worker /path/to/tkr-docusearch/bin/
```

## License

Apache License 2.0

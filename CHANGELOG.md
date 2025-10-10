# Changelog

All notable changes to DocuSearch will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added - UI Replacement (2025-10-09)

#### New Production UI
- **React 19.2.0 + TypeScript 5.9.3** frontend with strict type checking
- **Tailwind CSS v3.4** with OKLCH color system for consistent theming
- **Vite 7.1.9** build system (production bundle: 127KB gzipped)
- **Component Library**:
  - `DocumentCard` - Document display with status, metadata, and actions
  - `DocumentLibrary` - Grid layout with filtering and sorting
  - `StatusBadge` - Visual status indicators (uploading/processing/completed/error)
  - `UploadZone` - Drag-and-drop file upload with progress tracking
  - `Toast` - Notification system for user feedback
  - `Keyboard Shortcuts` - Global shortcuts (Ctrl+U for upload, Delete for delete, etc.)

#### New RESTful API
- **Document Management** (`src/api/routes/documents.py`):
  - `GET /api/documents` - List documents with filtering, sorting, pagination
  - `GET /api/document/{doc_id}` - Get single document details
  - `DELETE /api/document/{doc_id}` - Delete document and embeddings
  - `POST /api/document/{doc_id}/reprocess` - Queue document for reprocessing
  - `GET /api/document/{doc_id}/download` - Download original file
  - `GET /api/document/{doc_id}/markdown` - Download as markdown (existing)

#### Type System
- **Frontend Types** (`src/ui/src/types/types.ts`):
  - `DocumentStatus`: 'uploading' | 'processing' | 'completed' | 'error'
  - `FileType`: PDF | DOCX | PPTX | MD | TXT | etc.
  - `DocumentCardProps`: Complete document metadata structure
  - `DocumentAPIResponse`: Backend API response format

- **Backend Models** (`src/api/routes/documents.py`):
  - `DocumentAPIResponse`: Pydantic model matching frontend expectations
  - `DocumentFilters`: Query parameter validation
  - Status transformation: `ProcessingStatusEnum` → `DocumentStatus`

#### Service Layer
- **Frontend Services** (`src/ui/src/services/`):
  - `documentService.ts` - Document CRUD operations
  - `uploadService.ts` - XHR file upload with progress tracking
  - `workerService.ts` - Worker health checks
  - All services use real backend APIs (no mocks)

### Removed - POC Cleanup (2025-10-09)

#### Removed POC Endpoints
Removed 6 proof-of-concept endpoints from `src/processing/worker_webhook.py`:
- `GET /status` - POC status endpoint (replaced by `/api/documents`)
- `GET /status/queue` - POC queue listing (replaced by `/api/documents?status=processing`)
- `GET /status/{doc_id}` - POC status detail (replaced by `/api/document/{doc_id}`)
- `POST /api/search/query` - POC search endpoint (not used by new UI)
- `GET /api/preview/{doc_id}/{page_num}` - POC preview endpoint (not used by new UI)
- `GET /config` - POC configuration endpoint (not needed)

#### Removed POC Dependencies
- `SearchRequest` and `SearchResponse` models
- `SearchEngine` integration in worker
- `PreviewGenerator` integration in worker
- POC-specific imports and configurations

#### Cleaned Architecture
- **Before**: 15 endpoints (webhooks + POC + new API)
- **After**: 9 endpoints (webhooks + new API only)
- Cleaner separation of concerns:
  - Webhook endpoints (`/process`, `/delete`) for Copyparty integration
  - RESTful API (`/api/*`) for frontend
  - Health check (`/health`) for monitoring

### Changed

#### Worker Backend (`src/processing/worker_webhook.py`)
- Complete rewrite to remove POC code (511 lines)
- Now focuses on:
  1. Document processing via webhooks
  2. RESTful API routing to `documents_router` and `markdown_router`
  3. Health monitoring
- Added `remove_status()` method to `StatusManager` for document deletion

#### Status Management
- `StatusManager.mark_completed()` now stores embedding counts in metadata:
  - `visual_embeddings`: Number of visual embeddings generated
  - `text_embeddings`: Number of text embeddings generated
  - `text_chunks`: Number of text chunks processed

#### UI Serving
- UI now served from `src/ui/dist` (production build)
- Added `NoCacheStaticFiles` class for development (prevents browser caching)
- UI available at `http://localhost:8002/ui/`

### Fixed

#### Type Safety Issues
- Fixed `QueueItem` vs `ProcessingStatus` type mismatch in document listing
- Changed from `list_as_queue_items()` to `list_all()` for proper metadata access

#### Validation Errors
- Fixed reprocess endpoint validation error with `completed_at` field
- Manually clear `completed_at` and `error` when resetting document to queued state

#### Path Issues
- Corrected UI directory path from `src/ui` to `src/ui/dist`

## Architecture Summary

### Current System (Post-Cleanup)

```
┌─────────────────────────────────────────────────────────┐
│             User Browser (New React UI)                 │
│               http://localhost:8002/ui/                  │
└───────────────┬─────────────────────────────────────────┘
                │ REST API
┌───────────────▼─────────────────────────────────────────┐
│          FastAPI Worker (Port 8002)                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Webhook Endpoints                                 │  │
│  │ • POST /process  - Queue document                │  │
│  │ • POST /delete   - Delete document               │  │
│  ├──────────────────────────────────────────────────┤  │
│  │ Document API (/api/documents)                    │  │
│  │ • GET  /api/documents         - List             │  │
│  │ • GET  /api/document/{id}     - Detail           │  │
│  │ • DEL  /api/document/{id}     - Delete           │  │
│  │ • POST /api/document/{id}/... - Actions          │  │
│  ├──────────────────────────────────────────────────┤  │
│  │ Static Files                                      │  │
│  │ • /ui/           - React app (127KB gzipped)     │  │
│  │ • /health        - Health check                  │  │
│  └──────────────────────────────────────────────────┘  │
└───────────────┬─────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────┐
│      Copyparty (Port 8000) + ChromaDB (Port 8001)       │
└─────────────────────────────────────────────────────────┘
```

### Endpoints (9 Total)

**Webhook Endpoints** (2):
- `POST /process` - Queue document for processing
- `POST /delete` - Delete document from ChromaDB

**Document API** (6):
- `GET /api/documents` - List documents with filters
- `GET /api/document/{doc_id}` - Get document details
- `DELETE /api/document/{doc_id}` - Delete document
- `POST /api/document/{doc_id}/reprocess` - Reprocess document
- `GET /api/document/{doc_id}/download` - Download original file
- `GET /api/document/{doc_id}/markdown` - Download as markdown

**Monitoring** (1):
- `GET /health` - Health check

### Testing Results

All functionality validated:
- ✅ Health check: Worker responsive
- ✅ Document upload: File processing queued successfully
- ✅ Document listing: All documents returned with correct metadata
- ✅ Document deletion: ChromaDB and status tracker cleaned
- ✅ Frontend integration: React UI connected to real APIs
- ✅ Real-time updates: Auto-refresh every 5 seconds

### Performance

- **Frontend Bundle**: 127KB gzipped (production build)
- **Initial Load**: <2s on localhost
- **API Response**: <50ms for document listing
- **Auto-refresh**: 5s interval for document updates
- **Upload Progress**: Real-time XHR progress tracking

## Migration Notes

### For Users

- **Old POC UI**: Removed (was proof of concept)
- **New Production UI**: Available at `http://localhost:8002/ui/`
- **File Upload**: Now via drag-and-drop or Copyparty (both work)
- **Document Management**: Full CRUD in new UI
- **Search**: Search UI planned for future release

### For Developers

- **POC Endpoints Removed**: If you have scripts calling old endpoints, update to new RESTful API
- **Status Format Changed**: Use `DocumentAPIResponse` instead of `ProcessingStatus` directly
- **Frontend Type Safety**: All API calls now strongly typed with TypeScript
- **Service Layer**: Use `src/ui/src/services/` for all backend interactions

## Next Steps

- [ ] Add search UI integration (search backend already implemented)
- [ ] Add thumbnail generation for visual documents
- [ ] Add batch upload support
- [ ] Add export to VTT/SRT formats
- [ ] Add user preferences and settings
- [ ] Add advanced filters (date range, file size, etc.)

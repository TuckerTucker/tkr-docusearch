"""DocuSearch API Server.

HTTP server for document upload, search, status, and retrieval.
Document processing is handled by a separate headless worker
(``src/processing/worker.py``).

This server:
- Accepts file uploads and creates processing jobs in Koji
- Serves document metadata, pages, and search results
- Broadcasts processing status via WebSocket
- Does NOT load GPU models or process documents directly
"""

import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import uvicorn
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..config.processing_config import ProcessingConfig
from .cover_art_utils import delete_document_cover_art
from ..embeddings.query_engine import QueryEngine

# Import documents API router
from .documents_api import router as documents_router
from .documents_api import set_storage_client as set_documents_storage
from shikomi.types import FileFormat

# Import cleanup utilities
from .image_utils import cleanup_temp_directories, delete_document_images
from .status_api import router as status_router
from .status_api import set_status_koji_client, set_status_manager

# Import status management components
from .status_manager import StatusManager, get_status_manager

# Import WebSocket broadcaster
from .websocket_broadcaster import get_broadcaster
from ..config.urls import get_service_urls
from ..storage.koji_client import KojiClient
from ..storage.markdown_utils import delete_document_markdown

# Configure logging
LOG_FILE = os.getenv("LOG_FILE", "./logs/worker-webhook.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Configure root logger to capture all logs
logging.basicConfig(
    level=logging.DEBUG,  # Capture all levels
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(LOG_FILE, mode="a")],  # Append mode
    force=True,  # Override any existing configuration
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Ensure this logger also captures DEBUG

# ============================================================================
# Configuration
# ============================================================================

UPLOADS_DIR = Path(os.getenv("UPLOAD_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "uploads")))
DEVICE = os.getenv("DEVICE", "mps")
PRECISION = os.getenv("MODEL_PRECISION", "fp16")
WORKER_PORT = int(os.getenv("WORKER_PORT", "8002"))

# Global components (initialized at startup)
koji_client: Optional[KojiClient] = None
query_engine: Optional[QueryEngine] = None
status_manager: Optional[StatusManager] = None
processing_config: Optional[ProcessingConfig] = None

# In-memory status dict for StatusManager (legacy compatibility)
processing_status: Dict[str, Dict[str, Any]] = {}

# Pre-registered uploads (doc_id -> registration info)
pending_uploads: Dict[str, Dict[str, Any]] = {}

# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="DocuSearch Processing Worker",
    description="Webhook-based document processing service",
    version="1.0.0",
)

# Add CORS middleware — scoped to known service origins
_cors_origins = [
    os.environ.get("FRONTEND_URL", "http://localhost:3333"),
    os.environ.get("WORKER_URL", "http://localhost:8002"),
    "http://localhost:8000",  # backend API
    "http://127.0.0.1:3333",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8002",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Mount status API router
app.include_router(status_router)

# Mount documents API router (Wave 3)
app.include_router(documents_router)
logger.info(
    "Mounted documents API: GET /documents, GET /documents/{doc_id}, GET /images/{doc_id}/{filename}"
)

# ============================================================================
# Static File Serving - REMOVED
# ============================================================================
# Legacy static file serving has been removed. The Worker API now serves only
# REST API endpoints. User interface is provided by the React frontend on port 3333.
#
# Removed mounts:
# - /static (monitor UI)
# - /ui (legacy UI)
# - /frontend (legacy library UI)
#
# All UI functionality migrated to React frontend (frontend/ directory).
# See .archive/ARCHIVE_NOTES.md for rollback instructions if needed.


# ============================================================================
# Request/Response Models
# ============================================================================


class ProcessRequest(BaseModel):
    """Request to process a document."""

    file_path: str
    filename: str
    project_id: str = "default"


class ProcessResponse(BaseModel):
    """Response from process request."""

    message: str
    doc_id: Optional[str] = None
    status: str


class DeleteRequest(BaseModel):
    """Request to delete a document from Koji."""

    file_path: str
    filename: str


class DeleteResponse(BaseModel):
    """Response from delete request."""

    message: str
    doc_id: Optional[str] = None
    visual_deleted: int
    text_deleted: int
    page_images_deleted: int = 0
    cover_art_deleted: int = 0
    markdown_deleted: bool = False
    temp_dirs_cleaned: int = 0
    status: str


class StatusResponse(BaseModel):
    """Worker status response."""

    status: str
    processing_count: int
    total_processed: int


# ============================================================================
# API Endpoints
# ============================================================================


@app.post("/uploads/")
@app.post("/uploads")
async def upload_file(
    f: UploadFile = File(...),
    project_id: str = "default",
):
    """Accept file upload, save to disk, and create a processing job.

    The file is saved to ``UPLOADS_DIR`` and a ``processing_jobs`` row
    is created in Koji with ``status='queued'``.  The headless processing
    worker picks up the job asynchronously.
    """
    raw_filename = f.filename or "untitled"
    filename = Path(raw_filename).name
    if not filename or filename.startswith("."):
        raise HTTPException(status_code=400, detail="Invalid filename")
    save_path = UPLOADS_DIR / filename

    # Avoid overwriting: append counter if file exists
    if save_path.exists():
        stem = save_path.stem
        suffix = save_path.suffix
        counter = 1
        while save_path.exists():
            save_path = UPLOADS_DIR / f"{stem}_{counter}{suffix}"
            counter += 1

    # Save uploaded file with size limit
    max_size_mb = int(os.environ.get("MAX_FILE_SIZE_MB", "500"))
    max_size_bytes = max_size_mb * 1024 * 1024
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        content = await f.read()
        if len(content) > max_size_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds maximum size of {max_size_mb}MB",
            )
        save_path.write_bytes(content)
        logger.info(f"Saved upload: {filename} -> {save_path} ({len(content)} bytes)")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save upload {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # Compute doc_id from file content hash
    doc_id = hashlib.sha256(content).hexdigest()

    # Create processing job in Koji
    try:
        koji_client.create_job(
            doc_id=doc_id,
            filename=filename,
            file_path=str(save_path),
            project_id=project_id,
        )
    except Exception:
        # Job may already exist (duplicate upload) — check existing status
        existing = koji_client.get_job(doc_id)
        if existing and existing["status"] in ("queued", "processing"):
            return ProcessResponse(
                message="Document already queued", doc_id=doc_id, status=existing["status"],
            )

    return ProcessResponse(
        message="Document queued for processing", doc_id=doc_id, status="queued",
    )


@app.post("/process", response_model=ProcessResponse)
async def process_document(request: ProcessRequest):
    """Create a processing job for a file already on disk."""
    logger.info(f"Received processing request for: {request.filename}")

    file_path = Path(request.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")

    # Compute doc_id from file content hash
    try:
        with open(file_path, "rb") as fh:
            doc_id = hashlib.sha256(fh.read()).hexdigest()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {e}")

    # Create processing job in Koji
    try:
        koji_client.create_job(
            doc_id=doc_id,
            filename=request.filename,
            file_path=str(file_path),
            project_id=request.project_id,
        )
    except Exception:
        existing = koji_client.get_job(doc_id)
        if existing and existing["status"] in ("queued", "processing"):
            return ProcessResponse(
                message="Document already queued", doc_id=doc_id, status=existing["status"],
            )

    return ProcessResponse(
        message="Document queued for processing", doc_id=doc_id, status="queued",
    )


@app.post("/delete", response_model=DeleteResponse)
async def delete_document(request: DeleteRequest):
    """
    Delete a document from Koji and filesystem.

    Performs comprehensive cleanup:
    1. Deletes document and related data from Koji (cascades to pages, chunks, relations)
    2. Deletes page images and thumbnails from filesystem
    3. Deletes cover art (for audio files)
    4. Deletes extracted markdown files
    5. Cleans up temporary directories

    Called by worker webhook when a file is deleted.
    """
    logger.info(f"Received deletion request for: {request.filename}")

    # Initialize counters for response
    visual_count = 0
    text_count = 0
    page_images_count = 0
    cover_art_count = 0
    markdown_deleted = False
    temp_dirs_count = 0
    doc_id = None

    try:
        # Initialize Koji client
        from src.storage.koji_client import KojiClient
        from src.config.koji_config import KojiConfig

        koji = KojiClient(KojiConfig.from_env())
        koji.open()

        try:
            # Find doc_id by filename
            docs = koji.list_documents(limit=10000)
            matching = [d for d in docs if d.get("filename") == request.filename]

            if not matching:
                koji.close()
                logger.warning(f"No document found for filename: {request.filename}")
                return DeleteResponse(
                    message=f"No document found for {request.filename}",
                    doc_id=None,
                    visual_deleted=0,
                    text_deleted=0,
                    page_images_deleted=0,
                    cover_art_deleted=0,
                    markdown_deleted=False,
                    temp_dirs_cleaned=0,
                    status="not_found",
                )

            doc_id = matching[0]["doc_id"]
            logger.info(f"Starting comprehensive cleanup for document: {doc_id}")

            # 1. Delete from Koji (cascades to pages, chunks, relations)
            try:
                koji.delete_document(doc_id)
                logger.info(f"Koji cleanup complete for {doc_id}")
            except Exception as e:
                logger.error(f"Koji deletion failed: {e}", exc_info=True)
                raise
        finally:
            koji.close()

        # 2. Delete page images and thumbnails
        try:
            page_images_count = delete_document_images(doc_id)
            if page_images_count > 0:
                logger.info(f"✓ Page images cleanup: {page_images_count} files deleted")
        except Exception as e:
            logger.error(f"✗ Page images deletion failed: {e}", exc_info=True)
            # Continue with other cleanup operations

        # 3. Delete cover art (for audio files)
        try:
            cover_art_count = delete_document_cover_art(doc_id)
            if cover_art_count > 0:
                logger.info(f"✓ Cover art cleanup: {cover_art_count} files deleted")
        except Exception as e:
            logger.error(f"✗ Cover art deletion failed: {e}", exc_info=True)
            # Continue with other cleanup operations

        # 4. Delete markdown file
        try:
            markdown_deleted = delete_document_markdown(doc_id)
            if markdown_deleted:
                logger.info(f"✓ Markdown cleanup: file deleted")
        except Exception as e:
            logger.error(f"✗ Markdown deletion failed: {e}", exc_info=True)
            # Continue with other cleanup operations

        # 5. Clean up temporary directories (PPTX processing artifacts)
        try:
            temp_dirs_count = cleanup_temp_directories(doc_id)
            if temp_dirs_count > 0:
                logger.info(f"✓ Temp directories cleanup: {temp_dirs_count} directories deleted")
        except Exception as e:
            logger.error(f"✗ Temp directory cleanup failed: {e}", exc_info=True)

        # 6. Delete uploaded source file
        upload_deleted = False
        try:
            upload_path = UPLOADS_DIR / request.filename
            if upload_path.exists():
                upload_path.unlink()
                upload_deleted = True
                logger.info(f"✓ Upload file cleanup: {upload_path}")
        except Exception as e:
            logger.error(f"✗ Upload file deletion failed: {e}", exc_info=True)

        # Summary
        total_filesystem_items = (
            page_images_count + cover_art_count + (1 if markdown_deleted else 0) + temp_dirs_count
        )
        logger.info(
            f"✓ Comprehensive cleanup completed for {doc_id}: "
            f"Koji={visual_count + text_count}, "
            f"filesystem={total_filesystem_items} items"
        )

        return DeleteResponse(
            message=f"Deleted {request.filename} completely (Koji + filesystem)",
            doc_id=doc_id,
            visual_deleted=visual_count,
            text_deleted=text_count,
            page_images_deleted=page_images_count,
            cover_art_deleted=cover_art_count,
            markdown_deleted=markdown_deleted,
            temp_dirs_cleaned=temp_dirs_count,
            status="success",
        )

    except Exception as e:
        logger.error(f"Failed to delete document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get worker status."""
    processing_count = sum(1 for s in processing_status.values() if s["status"] == "processing")
    total_processed = len(processing_status)

    return StatusResponse(
        status="healthy", processing_count=processing_count, total_processed=total_processed
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


async def handle_upload_registration(websocket: WebSocket, message: Dict[str, Any]):
    """
    Handle batch upload registration request.

    Client sends list of files to upload, server generates doc_ids and returns them.
    Files are matched to doc_ids when webhook receives upload notification.

    Also checks for duplicate filenames and returns existing document info.

    Args:
        websocket: WebSocket connection
        message: Registration message with 'files' list
    """
    files = message.get("files", [])
    force_upload = message.get("force_upload", False)  # Allow forcing duplicate uploads

    if not files:
        await get_broadcaster().send_to_client(
            websocket, {"type": "error", "message": "No files provided in registration"}
        )
        return

    logger.info(f"📋 Registering batch upload: {len(files)} files (force={force_upload})")

    # If force_upload=True, clean up any previous registrations for the same filenames
    # This ensures we don't have multiple pending registrations for the same file
    if force_upload:
        filenames_to_register = {f.get("filename") for f in files if f.get("filename")}
        stale_doc_ids = [
            doc_id
            for doc_id, info in list(pending_uploads.items())
            if info.get("base_filename") in filenames_to_register
        ]
        for doc_id in stale_doc_ids:
            logger.info(
                f"🧹 Removing stale registration: {pending_uploads[doc_id]['base_filename']} → {doc_id[:8]}..."
            )
            del pending_uploads[doc_id]

    registrations = []
    for file_info in files:
        filename = file_info.get("filename")
        size = file_info.get("size", 0)

        if not filename:
            logger.warning("File registration missing filename, skipping")
            continue

        # Check for existing document with same filename (unless forced)
        is_duplicate = False
        existing_doc = None

        if not force_upload:
            try:
                # Query Koji directly to check for existing files
                from src.storage.koji_client import KojiClient
                from src.config.koji_config import KojiConfig

                koji = KojiClient(KojiConfig.from_env())
                koji.open()

                try:
                    docs = koji.list_documents(limit=10000)
                    for doc in docs:
                        stored_filename = doc.get("filename", "")
                        if stored_filename == filename:
                            is_duplicate = True
                            existing_doc = {
                                "doc_id": doc.get("doc_id", ""),
                                "filename": stored_filename,
                                "date_added": doc.get("created_at", ""),
                                "file_type": doc.get("format", ""),
                            }
                            logger.info(f"  Duplicate detected (exact): {filename}")
                            break
                finally:
                    koji.close()

            except Exception as e:
                logger.warning(f"Could not check for duplicates: {e}")
                # Continue with registration even if duplicate check fails

        # Generate doc_id from filename + timestamp for uniqueness
        # This ensures each upload gets a unique doc_id even if filename is reused
        unique_string = f"{filename}_{datetime.now().isoformat()}_{size}"
        doc_id = hashlib.sha256(unique_string.encode()).hexdigest()

        # Store pending upload
        pending_uploads[doc_id] = {
            "filename": filename,
            "size": size,
            "registered_at": datetime.now().isoformat(),
            "base_filename": filename,  # Store base filename for matching against upload-modified names
        }

        logger.info(
            f"📝 Stored pending upload: base_filename='{filename}' → doc_id={doc_id[:8]}... (force={force_upload})"
        )

        registration = {
            "filename": filename,
            "doc_id": doc_id,
            "expected_size": size,
            "is_duplicate": is_duplicate,
        }

        # Include existing document info if duplicate
        if is_duplicate and existing_doc:
            registration["existing_doc"] = existing_doc

        registrations.append(registration)

        if is_duplicate:
            logger.info(f"  ⚠️  Registered (duplicate): {filename} → {doc_id[:8]}...")
        else:
            logger.info(f"  ✓ Registered: {filename} → {doc_id[:8]}...")

    # Send response with all doc_ids and duplicate info (to requesting client)
    await get_broadcaster().send_to_client(
        websocket,
        {
            "type": "upload_batch_registered",
            "registrations": registrations,
            "count": len(registrations),
        },
    )

    # PHASE 2: Broadcast to ALL clients for cross-browser sync
    # This enables Browser B to see uploads initiated in Browser A instantly
    for registration in registrations:
        # Skip broadcasting duplicates (they won't be processed)
        if registration.get("is_duplicate"):
            continue

        await get_broadcaster().broadcast(
            {
                "type": "upload_registered",
                "doc_id": registration["doc_id"],
                "filename": registration["filename"],
                "status": "pending",
                "progress": 0.0,
            }
        )
        logger.info(
            f"📢 Broadcast upload_registered: {registration['filename']} → {registration['doc_id'][:8]}..."
        )

    duplicate_count = sum(1 for r in registrations if r.get("is_duplicate"))
    logger.info(
        f"✅ Batch registration complete: {len(registrations)} files ({duplicate_count} duplicates detected)"
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time monitoring and upload registration.

    Clients can:
    - Receive live updates about document processing
    - Pre-register upload batches to get doc_ids before uploading
    """
    broadcaster = get_broadcaster()
    await broadcaster.connect(websocket)

    try:
        # Keep connection alive and listen for client messages
        while True:
            # Receive client messages
            data = await websocket.receive_text()
            logger.info(f"📨 WebSocket received: {data[:200]}...")  # Log first 200 chars

            try:
                message = json.loads(data)
                message_type = message.get("type")
                logger.info(f"📬 Message type: {message_type}")

                if message_type == "register_upload_batch":
                    # Handle batch upload registration
                    logger.info("🔄 Calling handle_upload_registration...")
                    await handle_upload_registration(websocket, message)
                else:
                    logger.debug(f"Received WebSocket message: {message_type}")

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await broadcaster.send_to_client(websocket, {"type": "error", "message": str(e)})

    except WebSocketDisconnect:
        await broadcaster.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await broadcaster.disconnect(websocket)


# ============================================================================
# Startup/Shutdown
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Initialize API server components.

    Opens Koji for document reads and job queue management.
    QueryEngine is lazy-loaded on first search request.
    No GPU models are loaded — processing is handled by the
    separate worker process.
    """
    global koji_client, query_engine, status_manager, processing_config

    logger.info("=" * 70)
    logger.info("DocuSearch API Server Starting...")
    logger.info("=" * 70)

    # Initialize StatusManager
    status_manager = get_status_manager(processing_status)
    set_status_manager(status_manager)
    logger.info("StatusManager initialized")

    # Initialize ProcessingConfig
    processing_config = ProcessingConfig()
    app.state.config = processing_config
    logger.info("ProcessingConfig initialized")

    logger.info(f"Configuration:")
    logger.info(f"  Uploads Directory: {UPLOADS_DIR}")
    logger.info(f"  Worker Port: {WORKER_PORT}")
    logger.info(f"  Supported Formats: {', '.join(processing_config.supported_formats)}")

    try:
        # Initialize Koji (for document reads + job queue)
        from ..config.koji_config import KojiConfig
        koji_config = KojiConfig.from_env()
        logger.info(f"Opening Koji database ({koji_config.db_path})...")
        koji_client = KojiClient(koji_config)
        koji_client.open()
        set_documents_storage(koji_client)
        set_status_koji_client(koji_client)
        logger.info("Koji database opened")

    except Exception as e:
        logger.error(f"Failed to initialize components: {e}", exc_info=True)
        raise

    logger.info("=" * 70)
    logger.info("API Server started successfully")
    logger.info(f"  Listening on port: {WORKER_PORT}")
    logger.info(f"  Processing worker: separate process")
    logger.info("=" * 70)

    # Start background tasks
    asyncio.create_task(cleanup_stale_registrations())
    asyncio.create_task(poll_and_broadcast_job_status())

    # Initialize graph enrichment service
    try:
        from ..config.graph_config import GraphEnrichmentConfig
        from ..processing.graph_enrichment import GraphEnrichmentService

        graph_config = GraphEnrichmentConfig.from_env()
        enrichment_service = GraphEnrichmentService(
            storage_client=koji_client,
            config=graph_config,
        )
        app.state.enrichment_service = enrichment_service
        logger.info("Graph enrichment service initialized")

        if graph_config.auto_enrich_on_startup:
            asyncio.create_task(_run_enrichment_once(enrichment_service))

        asyncio.create_task(
            _periodic_enrichment(enrichment_service, graph_config)
        )
    except Exception as exc:
        logger.warning(f"Graph enrichment init skipped: {exc}")


async def poll_and_broadcast_job_status():
    """Poll processing_jobs in Koji and broadcast status changes via WebSocket.

    Runs every 1.5 seconds.  Detects changes in job status, progress,
    or stage and broadcasts updates to all connected WebSocket clients.
    """
    last_seen: Dict[str, tuple] = {}
    broadcaster = get_broadcaster()

    while True:
        try:
            await asyncio.sleep(1.5)

            if koji_client is None:
                continue

            jobs = koji_client.list_jobs(limit=50)
            for job in jobs:
                doc_id = job["doc_id"]
                key = (job["status"], job.get("progress"), job.get("stage"))

                if last_seen.get(doc_id) != key:
                    await broadcaster.broadcast_status_update(
                        doc_id=doc_id,
                        status=job["status"],
                        progress=job.get("progress", 0.0),
                        filename=job.get("filename", ""),
                        stage=job.get("stage", ""),
                    )
                    last_seen[doc_id] = key

        except Exception as exc:
            logger.debug(f"Job status poll error: {exc}")


async def cleanup_stale_registrations():
    """
    Background task to cleanup stale upload registrations.

    Runs every 5 minutes and removes registrations older than 10 minutes.
    This handles cases where files were registered but never uploaded.
    """
    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes

            from datetime import timedelta

            cutoff_time = datetime.now() - timedelta(minutes=10)

            stale_doc_ids = []
            for doc_id, info in list(pending_uploads.items()):
                registered_at = datetime.fromisoformat(info["registered_at"])
                if registered_at < cutoff_time:
                    stale_doc_ids.append(doc_id)
                    del pending_uploads[doc_id]
                    logger.warning(
                        f"🧹 Cleaned stale registration: {info['filename']} (registered {registered_at.isoformat()})"
                    )

            if stale_doc_ids:
                logger.info(f"🧹 Cleanup: Removed {len(stale_doc_ids)} stale registrations")

        except Exception as e:
            logger.error(f"Error in cleanup task: {e}", exc_info=True)


async def _run_enrichment_once(service) -> None:
    """Run graph enrichment once (for startup or manual trigger)."""
    try:
        summary = service.run_full_enrichment()
        logger.info("graph_enrichment.completed", **summary)
    except Exception as exc:
        logger.error(f"graph_enrichment.failed: {exc}")


async def _periodic_enrichment(service, config) -> None:
    """Background task to periodically recompute graph enrichment."""
    while True:
        await asyncio.sleep(config.enrichment_interval_seconds)
        await _run_enrichment_once(service)


@app.post("/graph/enrich")
async def trigger_enrichment():
    """Manually trigger graph enrichment."""
    if not hasattr(app.state, "enrichment_service"):
        from fastapi import HTTPException
        raise HTTPException(503, "Enrichment service not initialized")
    from fastapi import BackgroundTasks
    bg = BackgroundTasks()
    bg.add_task(_run_enrichment_once, app.state.enrichment_service)
    return {"status": "enrichment_queued"}


@app.get("/graph/stats")
async def graph_stats():
    """Return graph statistics."""
    if not hasattr(app.state, "enrichment_service"):
        return {"error": "Enrichment service not initialized"}
    storage = app.state.enrichment_service._storage
    try:
        result = storage.query(
            "SELECT relation_type, COUNT(*) AS cnt "
            "FROM doc_relations GROUP BY relation_type"
        )
        d = result.to_pydict()
        edge_counts = {
            d["relation_type"][i]: d["cnt"][i]
            for i in range(result.num_rows)
        }
    except Exception:
        edge_counts = {}

    doc_count = 0
    try:
        r = storage.query("SELECT COUNT(*) AS n FROM documents")
        doc_count = r.column("n")[0].as_py()
    except Exception:
        pass

    return {
        "documents": doc_count,
        "edges_by_type": edge_counts,
        "total_edges": sum(edge_counts.values()),
    }


# ============================================================================
# Search Endpoint (used by Research API via HTTP)
# ============================================================================


class SearchRequest(BaseModel):
    """Search request model."""

    query: str = Field(..., min_length=1, max_length=1000)
    n_results: int = Field(default=10, ge=1, le=100)
    search_mode: str = Field(default="hybrid")


@app.post("/search")
async def search_documents(request: SearchRequest):
    """Semantic search across indexed documents.

    Lazy-loads the QueryEngine on first call (loads the embedding
    model for query encoding).
    """
    global query_engine

    # Lazy-load QueryEngine on first search request
    if query_engine is None:
        try:
            query_engine = QueryEngine(device=DEVICE, quantization=PRECISION)
            query_engine.connect()
            app.state.query_engine = query_engine
            logger.info("QueryEngine lazy-loaded for search")
        except Exception as exc:
            logger.error(f"Failed to load QueryEngine: {exc}")
            raise HTTPException(status_code=503, detail="Search engine not ready")

    from ..search.koji_search import KojiSearch

    # Map API mode names to KojiSearch mode names
    mode_map = {"visual": "visual_only", "text": "text_only", "hybrid": "hybrid"}
    search_mode = mode_map.get(request.search_mode, request.search_mode)

    # Get or create KojiSearch instance
    if not hasattr(app.state, "search_engine"):
        app.state.search_engine = KojiSearch(
            koji_client=koji_client, shikomi_client=query_engine
        )

    # Run in thread — KojiSearch.search() uses run_until_complete()
    # internally, which conflicts with uvicorn's running event loop
    import asyncio

    search_response = await asyncio.to_thread(
        app.state.search_engine.search,
        query=request.query,
        n_results=request.n_results,
        search_mode=search_mode,
    )

    # Normalize results for the HTTP client
    results = []
    for r in search_response.get("results", []):
        results.append({
            "doc_id": r.get("doc_id"),
            "chunk_id": r.get("chunk_id"),
            "page_num": r.get("page"),
            "score": r.get("score", 0.0),
            "text_preview": r.get("text", "")[:200] if r.get("text") else None,
            "metadata": r.get("metadata", {}),
            "type": r.get("metadata", {}).get("source"),
            "filename": r.get("metadata", {}).get("filename"),
        })

    return {
        "query": request.query,
        "results": results,
        "total_results": len(results),
        "search_time_ms": search_response.get("total_time_ms", 0),
        "search_mode": request.search_mode,
    }


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("API server shutting down...")
    if query_engine is not None:
        query_engine.close()
        logger.info("QueryEngine closed")
    if koji_client is not None:
        koji_client.close()
        logger.info("Koji closed")
    logger.info("API server stopped")


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    """Run the worker server.

    Uses the standard asyncio event loop instead of uvloop to avoid
    conflicts with Koji's internal Tokio runtime.  Both runtimes use
    kqueue for I/O and can interfere when running in the same process.
    """
    uvicorn.run(
        app, host="0.0.0.0", port=WORKER_PORT, log_level="info",
        loop="asyncio",
    )


if __name__ == "__main__":
    main()

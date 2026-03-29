"""
Document Processing Worker for DocuSearch MVP - Webhook Version.

HTTP server that processes documents when triggered by upload webhook.
Extracts text, generates embeddings, and stores in Koji.
"""

import asyncio
import hashlib
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import uvicorn
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..config.processing_config import EnhancedModeConfig, ProcessingConfig

# Import core components
from . import DocumentProcessor
from .cover_art_utils import delete_document_cover_art
from .docling_parser import DoclingParser

# Import documents API router (Wave 3)
from .documents_api import router as documents_router
from .file_validator import validate_file_type

# Import cleanup utilities
from .image_utils import cleanup_temp_directories, delete_document_images
from .status_api import router as status_router
from .status_api import set_status_manager

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

# Processing status tracking
processing_status: Dict[str, Dict[str, Any]] = {}

# Pre-registered uploads (doc_id -> registration info)
pending_uploads: Dict[str, Dict[str, Any]] = {}

# Global components (initialized at startup)
document_processor: Optional[DocumentProcessor] = None
parser: Optional[DoclingParser] = None
status_manager: Optional[StatusManager] = None
processing_config: Optional[ProcessingConfig] = None

# Thread pool for background processing
executor = ThreadPoolExecutor(max_workers=2)

# Event loop for async operations from sync context
_loop = None

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
# Processing Function
# ============================================================================


def process_document_sync(file_path: str, filename: str, doc_id: str = None) -> Dict[str, Any]:
    """
    Process a document (runs in thread pool).

    Args:
        file_path: Absolute path to document
        filename: Original filename
        doc_id: Optional pre-generated document ID (SHA-256 hash)

    Returns:
        Processing result dict
    """
    try:
        # Verify file exists
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Check extension using file_validator
        valid, error = validate_file_type(str(path))
        if not valid:
            return {"status": "skipped", "error": error}

        # Generate doc ID from file hash (SHA-256) if not provided
        if doc_id is None:
            with open(file_path, "rb") as f:
                content = f.read()
                doc_id = hashlib.sha256(content).hexdigest()

        # Update status - must include all ProcessingStatus required fields
        start_time = datetime.now()
        processing_status[doc_id] = {
            "doc_id": doc_id,
            "filename": filename,
            "status": "processing",
            "progress": 0.0,
            "stage": "started",
            "started_at": start_time.isoformat(),
            "updated_at": start_time.isoformat(),
            "elapsed_time": 0.0,
            "error": None,
        }

        logger.info(f"Processing document: {filename} (ID: {doc_id})")

        # Broadcast processing start
        broadcaster = get_broadcaster()
        _broadcast_from_sync(
            broadcaster.broadcast_status_update(
                doc_id=doc_id, status="processing", progress=0.0, filename=filename, stage="started"
            )
        )
        _broadcast_from_sync(
            broadcaster.broadcast_log_message(
                level="INFO", message=f"Started processing: {filename}", doc_id=doc_id
            )
        )

        # Process document
        result = document_processor.process_document(
            file_path=file_path,
            status_callback=lambda status: _update_processing_status(doc_id, status),
        )

        if not result or not result.doc_id:
            raise ValueError(f"Document processing failed: No result returned")

        logger.info(
            f"Processed {filename}: doc_id={result.doc_id}, visual_ids={len(result.visual_ids)}, text_ids={len(result.text_ids)}"
        )

        # Update status to completed
        completion_time = datetime.now()
        start_time = datetime.fromisoformat(processing_status[doc_id]["started_at"])
        elapsed = (completion_time - start_time).total_seconds()

        processing_status[doc_id]["status"] = "completed"
        processing_status[doc_id]["stage"] = "completed"
        processing_status[doc_id]["progress"] = 1.0
        processing_status[doc_id]["updated_at"] = completion_time.isoformat()
        processing_status[doc_id]["completed_at"] = completion_time.isoformat()
        processing_status[doc_id]["elapsed_time"] = elapsed
        processing_status[doc_id]["visual_embeddings"] = len(result.visual_ids)
        processing_status[doc_id]["text_embeddings"] = len(result.text_ids)

        logger.info(f"✓ Successfully processed {filename} (ID: {result.doc_id})")

        # Broadcast completion
        _broadcast_from_sync(
            broadcaster.broadcast_status_update(
                doc_id=doc_id,
                status="completed",
                progress=1.0,
                filename=filename,
                stage="completed",
                visual_embeddings=len(result.visual_ids),
                text_embeddings=len(result.text_ids),
            )
        )
        _broadcast_from_sync(
            broadcaster.broadcast_log_message(
                level="INFO",
                message=f"Completed processing: {filename} "
                f"(visual: {len(result.visual_ids)}, text: {len(result.text_ids)})",
                doc_id=doc_id,
            )
        )

        return {
            "status": "completed",
            "doc_id": result.doc_id,
            "visual_embeddings": len(result.visual_ids),
            "text_embeddings": len(result.text_ids),
        }

    except Exception as e:
        logger.error(f"Failed to process {filename}: {e}", exc_info=True)

        if doc_id:
            failure_time = datetime.now()
            start_time = datetime.fromisoformat(processing_status[doc_id]["started_at"])
            elapsed = (failure_time - start_time).total_seconds()

            processing_status[doc_id]["status"] = "failed"
            processing_status[doc_id]["stage"] = "failed"
            processing_status[doc_id]["error"] = str(e)
            processing_status[doc_id]["updated_at"] = failure_time.isoformat()
            processing_status[doc_id]["completed_at"] = failure_time.isoformat()
            processing_status[doc_id]["elapsed_time"] = elapsed

            # Broadcast failure
            broadcaster = get_broadcaster()
            _broadcast_from_sync(
                broadcaster.broadcast_status_update(
                    doc_id=doc_id,
                    status="failed",
                    progress=0.0,
                    filename=filename,
                    stage="failed",
                    error=str(e),
                )
            )
            _broadcast_from_sync(
                broadcaster.broadcast_log_message(
                    level="ERROR", message=f"Failed to process {filename}: {str(e)}", doc_id=doc_id
                )
            )

        return {"status": "failed", "error": str(e)}


def _update_processing_status(doc_id: str, status):
    """Update processing status from DocumentProcessor callback."""
    if doc_id in processing_status:
        update_time = datetime.now()
        start_time = datetime.fromisoformat(processing_status[doc_id]["started_at"])
        elapsed = (update_time - start_time).total_seconds()

        stage = status.stage if hasattr(status, "stage") else status.status
        progress = status.progress

        processing_status[doc_id]["status"] = status.status
        processing_status[doc_id]["stage"] = stage
        processing_status[doc_id]["progress"] = progress
        processing_status[doc_id]["updated_at"] = update_time.isoformat()
        processing_status[doc_id]["elapsed_time"] = elapsed

        logger.info(
            f"📊 Status update callback: {doc_id[:8]}... stage={stage}, progress={progress:.1%}"
        )

        # Broadcast progress update to WebSocket clients
        broadcaster = get_broadcaster()
        filename = processing_status[doc_id].get("filename", "unknown")

        logger.info(f"🔔 Broadcasting status update: {filename} - {stage} ({progress:.1%})")

        _broadcast_from_sync(
            broadcaster.broadcast_status_update(
                doc_id=doc_id,
                status=status.status,
                progress=progress,
                filename=filename,
                stage=stage,
            )
        )


def _broadcast_from_sync(coro):
    """
    Execute async broadcast from synchronous context.

    Args:
        coro: Coroutine to execute (e.g., broadcaster.broadcast_status_update(...))
    """
    if _loop is None:
        logger.warning("Event loop not available for broadcasting")
        return

    try:
        # Schedule coroutine in event loop from thread
        asyncio.run_coroutine_threadsafe(coro, _loop)
        # Don't wait for result - fire and forget
    except Exception as e:
        logger.error(f"Failed to broadcast from sync context: {e}")


# ============================================================================
# API Endpoints
# ============================================================================


@app.post("/uploads/")
@app.post("/uploads")
async def upload_file(
    background_tasks: BackgroundTasks,
    f: UploadFile = File(...),
):
    """Accept file upload, save to disk, and trigger processing."""
    # Sanitize filename: strip directory components to prevent path traversal
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
        logger.info(f"Saved upload: {filename} → {save_path} ({len(content)} bytes)")
    except Exception as e:
        logger.error(f"Failed to save upload {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # Trigger processing via the /process flow
    request = ProcessRequest(
        file_path=str(save_path),
        filename=filename,
    )
    return await process_document(request, background_tasks)


@app.post("/process", response_model=ProcessResponse)
async def process_document(request: ProcessRequest, background_tasks: BackgroundTasks):
    """
    Queue a document for processing.
    """
    logger.info(f"Received processing request for: {request.filename}")

    # Validate path
    file_path = Path(request.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")

    # Check if this file was pre-registered via WebSocket
    doc_id = None

    # Try to match filename with pending uploads
    # Upload filename may have a timestamp suffix, so strip it for matching
    base_filename = request.filename
    # Remove timestamp pattern: filename.ext-timestamp-random.ext
    # Pattern: original.ext-1234567890.123456-AbCdEf.ext
    # We want to extract: original.ext
    import re

    # Match pattern: (anything)-digits.digits-random_string.extension
    # Group 1: everything before the timestamp (the original filename with extension)
    # The random string can contain letters, numbers, dashes, and underscores
    match = re.match(r"(.+)-\d+\.\d+-[A-Za-z0-9_-]+\.[^.]+$", request.filename)
    if match:
        # The base filename is just group 1 (which already includes the original extension)
        base_filename = match.group(1)
        logger.info(
            f"Detected upload filename modification: {request.filename} → {base_filename}"
        )

    # Look for matching pre-registration
    for registered_doc_id, registration_info in list(pending_uploads.items()):
        if (
            registration_info["base_filename"] == base_filename
            or registration_info["filename"] == request.filename
        ):
            doc_id = registered_doc_id
            del pending_uploads[registered_doc_id]  # Consume registration
            logger.info(f"✅ Matched pre-registered upload: {request.filename} → {doc_id[:8]}...")
            break

    # Fallback: Generate doc_id from file content hash if not pre-registered
    if not doc_id:
        logger.info(
            f"No pre-registration found for {request.filename}, generating doc_id from file hash"
        )
        try:
            with open(file_path, "rb") as f:
                content = f.read()
                doc_id = hashlib.sha256(content).hexdigest()
        except Exception as e:
            logger.error(f"Failed to generate doc_id for {request.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

    # Create status entry via StatusManager
    try:
        metadata = {
            "format": file_path.suffix.lstrip(".").lower(),
            "file_size": file_path.stat().st_size,
        }
        status_manager.create_status(doc_id, request.filename, metadata)
    except ValueError:
        # Document already exists
        logger.warning(f"Document {doc_id} already in status tracker")

    # Queue for background processing (pass doc_id to ensure consistency)
    executor.submit(process_document_sync, request.file_path, request.filename, doc_id)

    # Return immediately with doc_id (processing continues in background)
    return ProcessResponse(
        message=f"Document queued for processing", doc_id=doc_id, status="queued"
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
            # Continue - temp cleanup is not critical

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
    """Initialize components on startup."""
    global document_processor, parser, status_manager, processing_config, _loop

    # Capture event loop for async broadcasts from sync context
    _loop = asyncio.get_event_loop()

    # Use print for guaranteed visibility in logs
    print("=" * 70)
    print("DocuSearch Processing Worker Starting (Webhook Mode)...")
    print("=" * 70)
    logger.info("=" * 70)
    logger.info("DocuSearch Processing Worker Starting (Webhook Mode)...")
    logger.info("=" * 70)

    # Initialize StatusManager with global processing_status dict
    status_manager = get_status_manager(processing_status)
    set_status_manager(status_manager)
    logger.info("StatusManager initialized")

    # Initialize ProcessingConfig
    processing_config = ProcessingConfig()
    app.state.config = processing_config
    logger.info("ProcessingConfig initialized")

    # Log configuration
    logger.info(f"Configuration:")
    logger.info(f"  Uploads Directory: {UPLOADS_DIR}")
    logger.info(f"  Device: {DEVICE}")
    logger.info(f"  Precision: {PRECISION}")
    logger.info(f"  Worker Port: {WORKER_PORT}")
    logger.info(f"  Supported Formats: {', '.join(processing_config.supported_formats)}")

    # Initialize components
    logger.info("Initializing components...")

    try:
        # Initialize embedding engine via factory
        from ..config.koji_config import ShikomiConfig
        shikomi_config = ShikomiConfig.from_env()
        from ..embeddings.factory import create_embedding_engine
        embedding_engine = create_embedding_engine(shikomi_config)
        logger.info(f"Embedding engine ready (mode={shikomi_config.mode})")

        # Initialize storage client
        from ..config.koji_config import KojiConfig
        koji_config = KojiConfig.from_env()
        logger.info(f"Opening Koji database ({koji_config.db_path})...")
        storage_client = KojiClient(koji_config)
        storage_client.open()
        logger.info("Koji database opened")

        # Load enhanced mode configuration
        print("Loading enhanced mode configuration...")
        logger.info("Loading enhanced mode configuration...")
        enhanced_config = EnhancedModeConfig.from_env()
        print(
            f"✓ Enhanced mode enabled: "
            f"table_structure={enhanced_config.enable_table_structure}, "
            f"picture_classification={enhanced_config.enable_picture_classification}, "
            f"chunking={enhanced_config.chunking_strategy.value}"
        )
        logger.info(
            f"✓ Enhanced mode enabled: "
            f"table_structure={enhanced_config.enable_table_structure}, "
            f"picture_classification={enhanced_config.enable_picture_classification}, "
            f"chunking={enhanced_config.chunking_strategy.value}"
        )

        # Initialize document processor with enhanced mode
        document_processor = DocumentProcessor(
            embedding_engine=embedding_engine,
            storage_client=storage_client,
            enhanced_mode_config=enhanced_config,
        )
        logger.info("✓ Document processor initialized (enhanced mode)")

        # Initialize document parser
        parser = DoclingParser()
        logger.info("✓ Document parser initialized")

    except Exception as e:
        logger.error(f"Failed to initialize components: {e}", exc_info=True)
        raise

    logger.info("=" * 70)
    logger.info("✓ Worker started successfully (Webhook Mode)")
    logger.info(f"  Listening on port: {WORKER_PORT}")
    logger.info(f"  Waiting for webhook requests...")
    logger.info("=" * 70)

    # Start background cleanup task for stale registrations
    asyncio.create_task(cleanup_stale_registrations())

    # Initialize graph enrichment service
    try:
        from ..config.graph_config import GraphEnrichmentConfig
        from ..processing.graph_enrichment import GraphEnrichmentService

        graph_config = GraphEnrichmentConfig.from_env()
        enrichment_service = GraphEnrichmentService(
            storage_client=storage_client,
            config=graph_config,
        )
        app.state.enrichment_service = enrichment_service
        logger.info("✓ Graph enrichment service initialized")

        if graph_config.auto_enrich_on_startup:
            asyncio.create_task(_run_enrichment_once(enrichment_service))

        asyncio.create_task(
            _periodic_enrichment(enrichment_service, graph_config)
        )
    except Exception as exc:
        logger.warning(f"Graph enrichment init skipped: {exc}")


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


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Worker shutting down...")
    executor.shutdown(wait=True)
    logger.info("Worker stopped")


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    """Run the worker server."""
    uvicorn.run(app, host="0.0.0.0", port=WORKER_PORT, log_level="info")


if __name__ == "__main__":
    main()

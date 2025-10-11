"""
Document Processing Worker for DocuSearch MVP - Webhook Version.

HTTP server that processes documents when triggered by copyparty webhook.
Extracts text, generates embeddings, and stores in ChromaDB.
"""

import logging
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# Import core components
from ..embeddings import ColPaliEngine
from ..storage import ChromaClient
from ..processing import DocumentProcessor
from ..processing.docling_parser import DoclingParser

# Import status management components
from .status_manager import StatusManager, get_status_manager
from .status_api import router as status_router, set_status_manager

# Import WebSocket broadcaster
from .websocket_broadcaster import get_broadcaster

# Import documents API router (Wave 3)
from .documents_api import router as documents_router

# Configure logging
LOG_FILE = os.getenv("LOG_FILE", "./logs/worker-webhook.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE)
    ]
)

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

UPLOADS_DIR = Path(os.getenv("UPLOAD_DIR", "/uploads"))
CHROMA_HOST = os.getenv("CHROMA_HOST", "chromadb")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
DEVICE = os.getenv("DEVICE", "mps")
PRECISION = os.getenv("MODEL_PRECISION", "fp16")
WORKER_PORT = int(os.getenv("WORKER_PORT", "8002"))

# Load supported formats from environment
_formats_str = os.getenv("SUPPORTED_FORMATS", "pdf,docx,pptx")
SUPPORTED_EXTENSIONS = {f".{fmt.strip().lower()}" for fmt in _formats_str.split(",")}

# Processing status tracking
processing_status: Dict[str, Dict[str, Any]] = {}

# Global components (initialized at startup)
document_processor: Optional[DocumentProcessor] = None
parser: Optional[DoclingParser] = None
status_manager: Optional[StatusManager] = None

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
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount status API router
app.include_router(status_router)

# Mount documents API router (Wave 3)
app.include_router(documents_router)
logger.info("Mounted documents API: GET /documents, GET /documents/{doc_id}, GET /images/{doc_id}/{filename}")

# Mount static files for monitor UI
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
    logger.info(f"Mounted monitor UI at /static (directory: {STATIC_DIR})")
else:
    logger.warning(f"Static directory not found: {STATIC_DIR}")

# Mount legacy UI if exists
UI_DIR = Path(__file__).parent.parent / "ui"
if UI_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(UI_DIR), html=True), name="ui")
    logger.info(f"Mounted UI at /ui (directory: {UI_DIR})")
else:
    logger.warning(f"UI directory not found: {UI_DIR}")


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
    """Request to delete a document from ChromaDB."""
    file_path: str
    filename: str


class DeleteResponse(BaseModel):
    """Response from delete request."""
    message: str
    doc_id: Optional[str] = None
    visual_deleted: int
    text_deleted: int
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

        # Check extension
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return {
                "status": "skipped",
                "error": f"Unsupported file type: {path.suffix}"
            }

        # Generate doc ID from file hash (SHA-256) if not provided
        if doc_id is None:
            with open(file_path, 'rb') as f:
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
            "error": None
        }

        logger.info(f"Processing document: {filename} (ID: {doc_id})")

        # Broadcast processing start
        broadcaster = get_broadcaster()
        _broadcast_from_sync(
            broadcaster.broadcast_status_update(
                doc_id=doc_id,
                status="processing",
                progress=0.0,
                filename=filename,
                stage="started"
            )
        )
        _broadcast_from_sync(
            broadcaster.broadcast_log_message(
                level="INFO",
                message=f"Started processing: {filename}",
                doc_id=doc_id
            )
        )

        # Process document
        result = document_processor.process_document(
            file_path=file_path,
            status_callback=lambda status: _update_processing_status(doc_id, status)
        )

        if not result or not result.doc_id:
            raise ValueError(f"Document processing failed: No result returned")

        logger.info(f"Processed {filename}: doc_id={result.doc_id}, visual_ids={len(result.visual_ids)}, text_ids={len(result.text_ids)}")

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
                text_embeddings=len(result.text_ids)
            )
        )
        _broadcast_from_sync(
            broadcaster.broadcast_log_message(
                level="INFO",
                message=f"Completed processing: {filename} "
                        f"(visual: {len(result.visual_ids)}, text: {len(result.text_ids)})",
                doc_id=doc_id
            )
        )

        return {
            "status": "completed",
            "doc_id": result.doc_id,
            "visual_embeddings": len(result.visual_ids),
            "text_embeddings": len(result.text_ids)
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
                    error=str(e)
                )
            )
            _broadcast_from_sync(
                broadcaster.broadcast_log_message(
                    level="ERROR",
                    message=f"Failed to process {filename}: {str(e)}",
                    doc_id=doc_id
                )
            )

        return {
            "status": "failed",
            "error": str(e)
        }


def _update_processing_status(doc_id: str, status):
    """Update processing status from DocumentProcessor callback."""
    if doc_id in processing_status:
        update_time = datetime.now()
        start_time = datetime.fromisoformat(processing_status[doc_id]["started_at"])
        elapsed = (update_time - start_time).total_seconds()

        processing_status[doc_id]["status"] = status.status
        processing_status[doc_id]["stage"] = status.stage if hasattr(status, 'stage') else status.status
        processing_status[doc_id]["progress"] = status.progress
        processing_status[doc_id]["updated_at"] = update_time.isoformat()
        processing_status[doc_id]["elapsed_time"] = elapsed


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
        future = asyncio.run_coroutine_threadsafe(coro, _loop)
        # Don't wait for result - fire and forget
    except Exception as e:
        logger.error(f"Failed to broadcast from sync context: {e}")


# ============================================================================
# API Endpoints
# ============================================================================

@app.post("/process", response_model=ProcessResponse)
async def process_document(request: ProcessRequest, background_tasks: BackgroundTasks):
    """
    Queue a document for processing.

    Called by copyparty webhook when a file is uploaded.
    """
    logger.info(f"Received processing request for: {request.filename}")

    # Validate path
    file_path = Path(request.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")

    # Generate doc_id from file content hash (SHA-256)
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
            doc_id = hashlib.sha256(content).hexdigest()
    except Exception as e:
        logger.error(f"Failed to generate doc_id for {request.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

    # Create status entry via StatusManager
    try:
        metadata = {
            "format": file_path.suffix.lstrip('.').lower(),
            "file_size": file_path.stat().st_size,
        }
        status_manager.create_status(doc_id, request.filename, metadata)
    except ValueError as e:
        # Document already exists
        logger.warning(f"Document {doc_id} already in status tracker")

    # Queue for background processing (pass doc_id to ensure consistency)
    future = executor.submit(process_document_sync, request.file_path, request.filename, doc_id)

    # Return immediately with doc_id (processing continues in background)
    return ProcessResponse(
        message=f"Document queued for processing",
        doc_id=doc_id,
        status="queued"
    )


@app.post("/delete", response_model=DeleteResponse)
async def delete_document(request: DeleteRequest):
    """
    Delete a document from ChromaDB.

    Called by copyparty webhook when a file is deleted.
    """
    logger.info(f"Received deletion request for: {request.filename}")

    try:
        # Initialize ChromaDB client
        storage_client = ChromaClient(host=CHROMA_HOST, port=CHROMA_PORT)

        # Find doc_id by filename in visual collection
        visual_results = storage_client._visual_collection.get(
            where={"filename": request.filename},
            limit=1,
            include=["metadatas"]
        )

        # Try text collection if not found in visual
        if not visual_results['ids']:
            text_results = storage_client._text_collection.get(
                where={"filename": request.filename},
                limit=1,
                include=["metadatas"]
            )
            if text_results['ids'] and text_results['metadatas']:
                doc_id = text_results['metadatas'][0].get('doc_id')
            else:
                logger.warning(f"No embeddings found for filename: {request.filename}")
                return DeleteResponse(
                    message=f"No embeddings found for {request.filename}",
                    doc_id=None,
                    visual_deleted=0,
                    text_deleted=0,
                    status="not_found"
                )
        else:
            doc_id = visual_results['metadatas'][0].get('doc_id')

        # Delete from ChromaDB using doc_id
        visual_count, text_count = storage_client.delete_document(doc_id)

        logger.info(
            f"Deleted document {doc_id}: {visual_count} visual, {text_count} text embeddings"
        )

        return DeleteResponse(
            message=f"Deleted {request.filename} from ChromaDB",
            doc_id=doc_id,
            visual_deleted=visual_count,
            text_deleted=text_count,
            status="success"
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
        status="healthy",
        processing_count=processing_count,
        total_processed=total_processed
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time monitoring.

    Clients can connect to receive live updates about document processing,
    including status changes, log messages, and statistics.
    """
    broadcaster = get_broadcaster()
    await broadcaster.connect(websocket)

    try:
        # Keep connection alive and listen for client messages
        while True:
            # Receive any client messages (keep-alive, commands, etc.)
            data = await websocket.receive_text()

            # Handle client commands if needed
            # For now, just acknowledge receipt
            logger.debug(f"Received WebSocket message: {data}")

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
    global document_processor, parser, status_manager, _loop

    # Capture event loop for async broadcasts from sync context
    _loop = asyncio.get_event_loop()

    logger.info("=" * 70)
    logger.info("DocuSearch Processing Worker Starting (Webhook Mode)...")
    logger.info("=" * 70)

    # Initialize StatusManager with global processing_status dict
    status_manager = get_status_manager(processing_status)
    set_status_manager(status_manager)
    logger.info("StatusManager initialized")

    # Log configuration
    logger.info(f"Configuration:")
    logger.info(f"  Uploads Directory: {UPLOADS_DIR}")
    logger.info(f"  ChromaDB: {CHROMA_HOST}:{CHROMA_PORT}")
    logger.info(f"  Device: {DEVICE}")
    logger.info(f"  Precision: {PRECISION}")
    logger.info(f"  Worker Port: {WORKER_PORT}")
    logger.info(f"  Supported Extensions: {SUPPORTED_EXTENSIONS}")

    # Initialize components
    logger.info("Initializing components...")

    try:
        # Initialize embedding engine
        logger.info(f"Loading ColPali model (device={DEVICE}, precision={PRECISION})...")
        embedding_engine = ColPaliEngine(
            device=DEVICE,
            precision=PRECISION
        )
        logger.info("✓ ColPali model loaded")

        # Initialize storage client
        logger.info(f"Connecting to ChromaDB ({CHROMA_HOST}:{CHROMA_PORT})...")
        storage_client = ChromaClient(
            host=CHROMA_HOST,
            port=CHROMA_PORT
        )
        logger.info("✓ ChromaDB connected")

        # Initialize document processor
        document_processor = DocumentProcessor(
            embedding_engine=embedding_engine,
            storage_client=storage_client
        )
        logger.info("✓ Document processor initialized")

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
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=WORKER_PORT,
        log_level="info"
    )


if __name__ == "__main__":
    main()

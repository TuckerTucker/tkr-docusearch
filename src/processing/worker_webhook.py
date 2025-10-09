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

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from pydantic import BaseModel
import uvicorn

# Import core components
from ..embeddings import ColPaliEngine
from ..storage import ChromaClient
from ..processing import DocumentProcessor
from ..processing.docling_parser import DoclingParser
from ..processing.preview_generator import PreviewGenerator  # Wave 3, Agent 6
from ..search import SearchEngine
from .path_utils import normalize_path, PathLike

# Import status management components
from .status_manager import StatusManager, get_status_manager
from .status_api import router as status_router, set_status_manager

# Import API models
from ..api.models import SearchRequest, SearchResponse, SearchResult

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
search_engine: Optional[SearchEngine] = None
embedding_engine: Optional[ColPaliEngine] = None
storage_client: Optional[ChromaClient] = None
preview_generator: Optional[PreviewGenerator] = None  # Wave 3, Agent 6

# Thread pool for background processing
executor = ThreadPoolExecutor(max_workers=2)

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

# Custom StaticFiles class with no-cache headers for development
class NoCacheStaticFiles(StaticFiles):
    """StaticFiles subclass that adds no-cache headers to prevent browser caching during development."""

    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        # Add no-cache headers to prevent browser caching
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

# Mount static files for UI
UI_DIR = Path(__file__).parent.parent / "ui"
if UI_DIR.exists():
    app.mount("/ui", NoCacheStaticFiles(directory=str(UI_DIR), html=True), name="ui")
    logger.info(f"Mounted UI at /ui (directory: {UI_DIR}) with no-cache headers")
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

def process_document_sync(file_path: PathLike, filename: str) -> Dict[str, Any]:
    """
    Process a document (runs in thread pool).

    Args:
        file_path: Path to document (str or Path object)
        filename: Original filename

    Returns:
        Processing result dict
    """
    doc_id = None
    try:
        print(f">>> PROCESS_DOCUMENT_SYNC STARTED: {filename}", flush=True)

        # Normalize path once (convert to absolute Path, validate existence)
        path = normalize_path(file_path)

        # Check extension
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            print(f">>> SKIPPING unsupported file type: {path.suffix}", flush=True)
            return {
                "status": "skipped",
                "error": f"Unsupported file type: {path.suffix}"
            }

        # Generate doc ID from file hash (SHA-256 to match /process endpoint)
        with open(file_path, 'rb') as f:
            content = f.read()
            doc_id = hashlib.sha256(content).hexdigest()

        print(f">>> PROCESSING DOCUMENT: {filename} (ID: {doc_id})", flush=True)
        logger.info(f"Processing document: {filename} (ID: {doc_id})")

        # Update status to parsing
        try:
            status_manager.update_status(doc_id, "parsing", 0.1, stage="Parsing document")
        except KeyError:
            # Status doesn't exist yet - this shouldn't happen but create it just in case
            logger.warning(f"Status for {doc_id} not found, creating...")
            metadata = {
                "format": path.suffix.lstrip('.').lower(),
                "file_size": path.stat().st_size,
            }
            status_manager.create_status(doc_id, filename, metadata)
            status_manager.update_status(doc_id, "parsing", 0.1, stage="Parsing document")

        # Process document
        result = document_processor.process_document(
            file_path=file_path,
            status_callback=lambda status: _update_processing_status(doc_id, status)
        )

        if not result or not result.doc_id:
            raise ValueError(f"Document processing failed: No result returned")

        logger.info(f"Processed {filename}: doc_id={result.doc_id}, visual_ids={len(result.visual_ids)}, text_ids={len(result.text_ids)}")

        # Mark as completed
        status_manager.mark_completed(
            doc_id,
            visual_embeddings=len(result.visual_ids),
            text_embeddings=len(result.text_ids)
        )

        logger.info(f"✓ Successfully processed {filename} (ID: {result.doc_id})")

        return {
            "status": "completed",
            "doc_id": result.doc_id,
            "visual_embeddings": len(result.visual_ids),
            "text_embeddings": len(result.text_ids)
        }

    except Exception as e:
        logger.error(f"Failed to process {filename}: {e}", exc_info=True)

        if doc_id:
            try:
                status_manager.mark_failed(doc_id, str(e))
            except KeyError:
                logger.warning(f"Could not mark {doc_id} as failed - not in status tracker")

        return {
            "status": "failed",
            "error": str(e)
        }


def _update_processing_status(doc_id: str, status):
    """Update processing status from DocumentProcessor callback."""
    try:
        # Map DocumentProcessor status to ProcessingStatusEnum values
        status_value = status.status  # e.g., "embedding_visual", "embedding_text", etc.
        progress = status.progress  # 0.0-1.0

        # Build kwargs for additional fields
        kwargs = {}
        if hasattr(status, 'stage'):
            kwargs['stage'] = status.stage
        if hasattr(status, 'page'):
            kwargs['page'] = status.page
        if hasattr(status, 'total_pages'):
            kwargs['total_pages'] = status.total_pages

        status_manager.update_status(doc_id, status_value, progress, **kwargs)
    except KeyError:
        logger.warning(f"Could not update status for {doc_id} - not in status tracker")
    except Exception as e:
        logger.error(f"Failed to update status for {doc_id}: {e}")


# ============================================================================
# API Endpoints
# ============================================================================

@app.post("/process", response_model=ProcessResponse)
async def process_document(request: ProcessRequest, background_tasks: BackgroundTasks):
    """
    Queue a document for processing.

    Called by copyparty webhook when a file is uploaded.
    """
    print(f">>> PROCESS ENDPOINT CALLED: {request.filename}", flush=True)
    logger.info(f"Received processing request for: {request.filename}")

    # Normalize and validate path once
    try:
        file_path = normalize_path(request.file_path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

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

    # Queue for background processing
    print(f">>> SUBMITTING TO THREADPOOL: {request.filename}", flush=True)
    future = executor.submit(process_document_sync, file_path, request.filename)

    # Add callback to log completion or errors
    def log_completion(fut):
        try:
            result = fut.result()
            print(f">>> BACKGROUND TASK COMPLETED: {result}", flush=True)
            logger.info(f"Background task completed: {result}")
        except Exception as e:
            print(f">>> BACKGROUND TASK FAILED: {e}", flush=True)
            logger.error(f"Background task failed: {e}", exc_info=True)

    future.add_done_callback(log_completion)

    # Return immediately with doc_id (processing continues in background)
    print(f">>> QUEUED FOR BACKGROUND: {request.filename} (doc_id: {doc_id})", flush=True)
    logger.info(f"Queued {request.filename} for background processing (doc_id: {doc_id})")
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


@app.post("/api/search/query", response_model=SearchResponse)
async def search_query(request: SearchRequest):
    """
    Execute semantic search across documents.

    Performs two-stage search:
    1. Fast retrieval with HNSW
    2. Late interaction re-ranking with MaxSim
    """
    if not search_engine:
        raise HTTPException(
            status_code=503,
            detail="Search engine not initialized"
        )

    try:
        start_time = time.time()

        # Map API search modes to SearchEngine modes
        search_mode_mapping = {
            "visual": "visual_only",
            "text": "text_only",
            "hybrid": "hybrid"
        }
        engine_search_mode = search_mode_mapping.get(request.search_mode, "hybrid")

        # Execute search
        response = search_engine.search(
            query=request.query,
            n_results=request.n_results,
            search_mode=engine_search_mode,
            enable_reranking=True
        )

        search_time_ms = (time.time() - start_time) * 1000

        # Convert to API response format
        results = []
        for result in response.get("results", []):
            results.append(SearchResult(
                doc_id=result.get("doc_id", ""),
                chunk_id=result.get("chunk_id"),
                page_num=result.get("page_num"),
                score=result.get("score", 0.0),
                text_preview=result.get("text", "")[:200] if result.get("text") else None,
                metadata=result.get("metadata", {})
            ))

        # Filter by minimum score if specified
        if request.min_score is not None:
            results = [r for r in results if r.score >= request.min_score]

        logger.info(
            f"Search completed: query='{request.query}', mode={request.search_mode}, "
            f"results={len(results)}, time={search_time_ms:.0f}ms"
        )

        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            search_time_ms=search_time_ms,
            search_mode=request.search_mode
        )

    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@app.get("/status")
async def get_status():
    """
    Get comprehensive worker status with dashboard statistics.

    Wave 2, Agent 5: Enhanced with dashboard stats for UI.
    """
    if not status_manager:
        # Fallback if status_manager not initialized
        return {
            "queue_size": 0,
            "processing_count": 0,
            "completed_today": 0,
            "failed_today": 0,
            "avg_processing_time_seconds": 0.0,
            "estimated_wait_time_seconds": 0.0,
            "current_processing": None,
            "recent_documents": []
        }

    # Get dashboard stats from StatusManager
    dashboard_stats = status_manager.get_dashboard_stats()
    return dashboard_stats


@app.get("/api/preview/{doc_id}/{page_num}")
async def get_preview(doc_id: str, page_num: int):
    """
    Get page preview with image and text.

    Wave 3, Agent 6: Preview endpoint for document preview modal.

    Args:
        doc_id: Document SHA-256 hash
        page_num: Page number (1-indexed)

    Returns:
        PreviewResponse with base64 image, text, and metadata
    """
    if not preview_generator:
        raise HTTPException(
            status_code=503,
            detail="Preview generator not initialized"
        )

    if page_num < 1:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid page_num={page_num}. Must be >= 1"
        )

    try:
        # Generate preview
        preview = preview_generator.get_page_preview(doc_id, page_num)

        if not preview:
            raise HTTPException(
                status_code=404,
                detail=f"Preview not found for doc_id={doc_id}, page={page_num}"
            )

        # Return preview as dictionary
        return preview.to_dict()

    except FileNotFoundError as e:
        logger.error(f"File not found for preview: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"Original file not found for document {doc_id}"
        )
    except ValueError as e:
        logger.error(f"Invalid page number: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Preview generation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate preview: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/config")
async def get_config():
    """Get worker configuration including supported formats."""
    return {
        "supported_formats": list(SUPPORTED_EXTENSIONS),
        "max_file_size_mb": int(os.getenv("MAX_FILE_SIZE_MB", "100")),
        "device": DEVICE,
        "model_precision": PRECISION
    }


# ============================================================================
# Startup/Shutdown
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    global document_processor, parser, status_manager, search_engine, embedding_engine, storage_client, preview_generator

    print("=" * 70, flush=True)
    print("DocuSearch Processing Worker Starting (Webhook Mode)...", flush=True)
    print("=" * 70, flush=True)
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

        # Initialize search engine
        search_engine = SearchEngine(
            storage_client=storage_client,
            embedding_engine=embedding_engine
        )
        logger.info("✓ Search engine initialized")

        # Initialize preview generator (Wave 3, Agent 6)
        preview_generator = PreviewGenerator(
            storage_client=storage_client,
            parser=parser
        )
        logger.info("✓ Preview generator initialized")

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

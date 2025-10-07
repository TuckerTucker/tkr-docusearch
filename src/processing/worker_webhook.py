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
from pydantic import BaseModel
import uvicorn

# Import core components
from ..embeddings import ColPaliEngine
from ..storage import ChromaClient
from ..processing import DocumentProcessor
from ..processing.docling_parser import DoclingParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/data/logs/worker.log')
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
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx"}
WORKER_PORT = int(os.getenv("WORKER_PORT", "8002"))

# Processing status tracking
processing_status: Dict[str, Dict[str, Any]] = {}

# Global components (initialized at startup)
document_processor: Optional[DocumentProcessor] = None
parser: Optional[DoclingParser] = None

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


class StatusResponse(BaseModel):
    """Worker status response."""
    status: str
    processing_count: int
    total_processed: int


# ============================================================================
# Processing Function
# ============================================================================

def process_document_sync(file_path: str, filename: str) -> Dict[str, Any]:
    """
    Process a document (runs in thread pool).

    Args:
        file_path: Absolute path to document
        filename: Original filename

    Returns:
        Processing result dict
    """
    doc_id = None
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

        # Generate doc ID from file hash
        with open(file_path, 'rb') as f:
            content = f.read()
            doc_id = hashlib.md5(content).hexdigest()[:12]

        # Update status
        processing_status[doc_id] = {
            "filename": filename,
            "status": "processing",
            "progress": 0.0,
            "started_at": datetime.now().isoformat(),
            "error": None
        }

        logger.info(f"Processing document: {filename} (ID: {doc_id})")

        # Process document
        result = document_processor.process_document(
            file_path=file_path,
            status_callback=lambda status: _update_processing_status(doc_id, status)
        )

        if not result or result.status.lower() != "completed":
            error_msg = result.error if result else "Unknown error"
            raise ValueError(f"Document processing failed: {error_msg}")

        logger.info(f"Processed {filename}: {result.pages_processed} pages, {result.text_chunks_processed} text chunks")

        # Update status to completed
        processing_status[doc_id]["status"] = "completed"
        processing_status[doc_id]["progress"] = 1.0
        processing_status[doc_id]["completed_at"] = datetime.now().isoformat()
        processing_status[doc_id]["pages"] = result.pages_processed
        processing_status[doc_id]["chunks"] = result.text_chunks_processed

        logger.info(f"✓ Successfully processed {filename} (ID: {doc_id})")

        return {
            "status": "completed",
            "doc_id": doc_id,
            "pages": result.pages_processed,
            "chunks": result.text_chunks_processed
        }

    except Exception as e:
        logger.error(f"Failed to process {filename}: {e}", exc_info=True)

        if doc_id:
            processing_status[doc_id]["status"] = "failed"
            processing_status[doc_id]["error"] = str(e)
            processing_status[doc_id]["completed_at"] = datetime.now().isoformat()

        return {
            "status": "failed",
            "error": str(e)
        }


def _update_processing_status(doc_id: str, status):
    """Update processing status from DocumentProcessor callback."""
    if doc_id in processing_status:
        processing_status[doc_id]["status"] = status.status
        processing_status[doc_id]["progress"] = status.progress


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

    # Queue for background processing
    future = executor.submit(process_document_sync, request.file_path, request.filename)

    # Return immediately (processing continues in background)
    return ProcessResponse(
        message=f"Processing queued for {request.filename}",
        status="queued"
    )


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


# ============================================================================
# Startup/Shutdown
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    global document_processor, parser

    logger.info("=" * 70)
    logger.info("DocuSearch Processing Worker Starting (Webhook Mode)...")
    logger.info("=" * 70)

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

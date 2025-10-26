"""
FastAPI server for DocuSearch MVP.

Provides REST API endpoints for document search, upload, and system monitoring.
"""

import logging
import os
import time
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

# Import core components
from ..embeddings import ColPaliEngine
from ..processing import DocumentProcessor
from ..search import SearchEngine
from ..storage import ChromaClient
from .models import (
    ComponentHealth,
    HealthResponse,
    ProcessingStatus,
    SearchRequest,
    SearchResponse,
    SearchResult,
    StatusResponse,
    SystemStats,
    UploadResponse,
)

logger = logging.getLogger(__name__)

# ============================================================================
# Application Configuration
# ============================================================================

API_VERSION = "1.0.0"
API_TITLE = "DocuSearch API"
API_DESCRIPTION = """
DocuSearch MVP - Semantic document search with ColPali embeddings.

## Features

* **Document Upload**: Upload PDF, DOCX, PPTX files for processing
* **Semantic Search**: Multi-vector late interaction search (visual + text)
* **System Status**: Real-time health monitoring and statistics
* **Processing Status**: Track document processing progress

## Search Modes

- **hybrid**: Search both visual (page images) and text chunks
- **visual**: Search only visual page embeddings
- **text**: Search only text chunk embeddings
"""

# Global component instances (initialized in create_app)
_app_state = {
    "embedding_engine": None,
    "storage_client": None,
    "search_engine": None,
    "document_processor": None,
    "start_time": None,
}


# ============================================================================
# Application Factory
# ============================================================================


def create_app(
    chroma_host: str = "localhost",
    chroma_port: int = 8001,
    device: str = "mps",
    precision: str = "fp16",
) -> FastAPI:
    """
    Create and configure FastAPI application.

    Args:
        chroma_host: ChromaDB host address
        chroma_port: ChromaDB port number
        device: Device for embedding model (mps, cuda, cpu)
        precision: Model precision (fp16, fp32)

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title=API_TITLE,
        description=API_DESCRIPTION,
        version=API_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS with environment-based whitelist
    allowed_origins = os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:8000,http://localhost:8001,http://localhost:8002"
    ).split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,  # Explicit whitelist from environment
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize components on startup
    @app.on_event("startup")
    async def startup_event():
        """Initialize system components on startup."""
        logger.info("Initializing DocuSearch API components...")
        _app_state["start_time"] = time.time()

        try:
            # Initialize embedding engine
            logger.info(f"Loading ColPali model (device={device}, precision={precision})...")
            _app_state["embedding_engine"] = ColPaliEngine(device=device, precision=precision)
            logger.info("✓ ColPali model loaded")

            # Initialize storage client
            logger.info(f"Connecting to ChromaDB ({chroma_host}:{chroma_port})...")
            _app_state["storage_client"] = ChromaClient(host=chroma_host, port=chroma_port)
            logger.info("✓ ChromaDB connected")

            # Initialize search engine
            _app_state["search_engine"] = SearchEngine(
                storage_client=_app_state["storage_client"],
                embedding_engine=_app_state["embedding_engine"],
            )
            logger.info("✓ Search engine initialized")

            # Initialize document processor
            _app_state["document_processor"] = DocumentProcessor(
                embedding_engine=_app_state["embedding_engine"],
                storage_client=_app_state["storage_client"],
            )
            logger.info("✓ Document processor initialized")

            logger.info("🎉 DocuSearch API ready!")

        except Exception as e:
            logger.error(f"Failed to initialize components: {e}", exc_info=True)
            raise

    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown."""
        logger.info("Shutting down DocuSearch API...")

    return app


# Create default app instance
app = create_app()


# ============================================================================
# Health Check Endpoints
# ============================================================================


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Simple health check endpoint",
)
async def health_check():
    """Basic health check."""
    return HealthResponse(status="ok", timestamp=datetime.now(), version=API_VERSION)


@app.get(
    "/status",
    response_model=StatusResponse,
    summary="System Status",
    description="Detailed system status including component health and statistics",
)
async def get_status():
    """Get detailed system status."""
    components = []

    # Check embedding engine
    if _app_state["embedding_engine"]:
        components.append(
            ComponentHealth(
                name="embedding_engine", status="healthy", message="ColPali model loaded and ready"
            )
        )
    else:
        components.append(
            ComponentHealth(
                name="embedding_engine",
                status="unhealthy",
                message="Embedding engine not initialized",
            )
        )

    # Check storage client
    storage_status = "unhealthy"
    storage_message = "ChromaDB not connected"
    storage_latency = None

    if _app_state["storage_client"]:
        try:
            start = time.time()
            # Test connection with heartbeat
            _app_state["storage_client"].client.heartbeat()
            storage_latency = (time.time() - start) * 1000
            storage_status = "healthy"
            storage_message = "Connected and responsive"
        except Exception as e:
            storage_message = f"Connection error: {str(e)}"

    components.append(
        ComponentHealth(
            name="chromadb",
            status=storage_status,
            message=storage_message,
            latency_ms=storage_latency,
        )
    )

    # Get statistics
    stats = SystemStats()
    if _app_state["storage_client"]:
        try:
            # Get collection counts
            visual_count = _app_state["storage_client"].visual_collection.count()
            text_count = _app_state["storage_client"].text_collection.count()

            stats.total_pages = visual_count
            stats.total_text_chunks = text_count
            # Estimate unique documents (rough approximation)
            stats.total_documents = max(1, visual_count // 5)  # Assume ~5 pages per doc
        except Exception as e:
            logger.warning(f"Failed to get statistics: {e}")

    # Determine overall status
    system_status = "healthy"
    if any(c.status == "unhealthy" for c in components):
        system_status = "unhealthy"
    elif any(c.status == "degraded" for c in components):
        system_status = "degraded"

    # Calculate uptime
    uptime = 0.0
    if _app_state["start_time"]:
        uptime = time.time() - _app_state["start_time"]

    return StatusResponse(
        system_status=system_status, components=components, stats=stats, uptime_seconds=uptime
    )


# ============================================================================
# Search Endpoints
# ============================================================================


@app.post(
    "/search",
    response_model=SearchResponse,
    summary="Search Documents",
    description="Semantic search across indexed documents using ColPali embeddings",
)
async def search_documents(request: SearchRequest):
    """
    Execute semantic search.

    Performs two-stage search:
    1. Fast retrieval with representative vectors (HNSW)
    2. Late interaction re-ranking with full multi-vectors (MaxSim)
    """
    if not _app_state["search_engine"]:
        raise HTTPException(status_code=503, detail="Search engine not initialized")

    try:
        start_time = time.time()

        # Execute search
        response = _app_state["search_engine"].search(
            query=request.query,
            n_results=request.n_results,
            search_mode=request.search_mode,
            enable_reranking=True,
        )

        search_time_ms = (time.time() - start_time) * 1000

        # Convert to API response format
        results = []
        for result in response.get("results", []):
            results.append(
                SearchResult(
                    doc_id=result.get("doc_id", ""),
                    chunk_id=result.get("chunk_id"),
                    page_num=result.get("page_num"),
                    score=result.get("score", 0.0),
                    text_preview=result.get("text", "")[:200] if result.get("text") else None,
                    metadata=result.get("metadata", {}),
                )
            )

        # Filter by minimum score if specified
        if request.min_score is not None:
            results = [r for r in results if r.score >= request.min_score]

        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            search_time_ms=search_time_ms,
            search_mode=request.search_mode,
        )

    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get(
    "/search",
    response_model=SearchResponse,
    summary="Search Documents (GET)",
    description="Semantic search with query parameters (alternative to POST)",
)
async def search_documents_get(
    q: str = Query(..., description="Search query", min_length=1, max_length=1000),
    n: int = Query(10, description="Number of results", ge=1, le=100),
    mode: str = Query("hybrid", description="Search mode: visual, text, or hybrid"),
):
    """Search via GET request for simple use cases."""
    request = SearchRequest(query=q, n_results=n, search_mode=mode)
    return await search_documents(request)


# ============================================================================
# Document Upload Endpoint
# ============================================================================


@app.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload Document",
    description="Upload a document file (PDF, DOCX, PPTX) for processing and indexing",
)
async def upload_document(file: UploadFile = File(..., description="Document file to upload")):
    """
    Upload and queue document for processing.

    Currently processes synchronously. In production, this should
    queue the document for background processing.
    """
    try:
        # Validate file type
        allowed_extensions = {".pdf", ".docx", ".pptx"}
        file_ext = Path(file.filename).suffix.lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_extensions}",
            )

        # Read file content
        content = await file.read()
        file_size = len(content)

        # Generate doc ID (using SHA-256 for security)
        import hashlib

        doc_id = hashlib.sha256(content).hexdigest()[:16]

        # Save to uploads directory
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / f"{doc_id}_{file.filename}"
        file_path.write_bytes(content)

        logger.info(f"Uploaded file: {file.filename} ({file_size} bytes) -> {file_path}")

        return UploadResponse(
            success=True,
            doc_id=doc_id,
            filename=file.filename,
            file_size_bytes=file_size,
            status="queued",
            message="Document uploaded and queued for processing",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# ============================================================================
# Processing Status Endpoint
# ============================================================================


@app.get(
    "/processing/{doc_id}",
    response_model=ProcessingStatus,
    summary="Get Processing Status",
    description="Get the processing status for a specific document",
)
async def get_processing_status(doc_id: str):
    """
    Get document processing status.

    Note: This is a stub. In production, this would query a job queue
    or database for actual processing status.
    """
    # TODO: Implement actual status tracking
    # For now, return a mock status
    return ProcessingStatus(
        doc_id=doc_id,
        status="completed",
        progress=1.0,
        pages_processed=None,
        total_pages=None,
        started_at=datetime.now(),
        completed_at=datetime.now(),
    )


# ============================================================================
# Statistics Endpoint
# ============================================================================


@app.get(
    "/stats/search", summary="Search Statistics", description="Get search performance statistics"
)
async def get_search_stats():
    """Get search engine statistics."""
    if not _app_state["search_engine"]:
        raise HTTPException(status_code=503, detail="Search engine not initialized")

    stats = _app_state["search_engine"].get_search_stats()
    return stats


# ============================================================================
# Main Entry Point
# ============================================================================


def main(host: str = "0.0.0.0", port: int = 8002, reload: bool = False):
    """
    Run the API server.

    Args:
        host: Host address to bind to
        port: Port number to listen on
        reload: Enable auto-reload on code changes (development)
    """
    uvicorn.run("src.api.server:app", host=host, port=port, reload=reload, log_level="info")


if __name__ == "__main__":
    main()

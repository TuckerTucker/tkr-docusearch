"""
Document API Routes - RESTful endpoints for UI frontend.

Provides CRUD operations for documents with DocumentAPIResponse format.
Replaces POC endpoints with clean RESTful API design.

Author: Claude Code
Date: 2025-10-09
"""

import logging
import hashlib
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ...processing.status_manager import StatusManager
from ...processing.status_models import ProcessingStatusEnum
from ...storage import ChromaClient

logger = logging.getLogger(__name__)

# Router for document endpoints
router = APIRouter(prefix="/api", tags=["documents"])

# Global dependencies (set at startup)
_status_manager: Optional[StatusManager] = None
_storage_client: Optional[ChromaClient] = None


def set_dependencies(status_manager: StatusManager, storage_client: ChromaClient) -> None:
    """
    Inject dependencies for document API router.

    Args:
        status_manager: StatusManager instance
        storage_client: ChromaClient instance
    """
    global _status_manager, _storage_client
    _status_manager = status_manager
    _storage_client = storage_client
    logger.info("Document API router initialized with dependencies")


# ============================================================================
# Response Models
# ============================================================================

class DocumentAPIResponse(BaseModel):
    """Frontend-compatible document response (matches types.ts)."""
    id: str
    title: str
    status: str  # 'uploading' | 'processing' | 'completed' | 'error'
    file_type: str
    thumbnail_url: Optional[str] = None
    metadata: Optional[dict] = None
    embeddings: Optional[dict] = None
    processing: Optional[dict] = None
    created_at: str
    processed_at: Optional[str] = None


class DocumentFilters(BaseModel):
    """Query filters for document list."""
    status: Optional[List[str]] = None
    file_type: Optional[List[str]] = None
    sort_by: Optional[str] = "date"
    sort_order: Optional[str] = "desc"
    limit: Optional[int] = 100
    offset: Optional[int] = 0


# ============================================================================
# Transformation Functions
# ============================================================================

def map_status_to_frontend(backend_status: ProcessingStatusEnum) -> str:
    """
    Map backend ProcessingStatusEnum to frontend DocumentStatus.

    Args:
        backend_status: Backend status enum value

    Returns:
        Frontend status string ('uploading' | 'processing' | 'completed' | 'error')
    """
    mapping = {
        ProcessingStatusEnum.QUEUED: "processing",
        ProcessingStatusEnum.PARSING: "processing",
        ProcessingStatusEnum.EMBEDDING_VISUAL: "processing",
        ProcessingStatusEnum.EMBEDDING_TEXT: "processing",
        ProcessingStatusEnum.STORING: "processing",
        ProcessingStatusEnum.COMPLETED: "completed",
        ProcessingStatusEnum.FAILED: "error",
    }
    return mapping.get(backend_status, "processing")


def transform_to_api_response(status) -> DocumentAPIResponse:
    """
    Transform backend ProcessingStatus to frontend DocumentAPIResponse.

    Args:
        status: ProcessingStatus object from StatusManager

    Returns:
        DocumentAPIResponse matching frontend types.ts
    """
    # Map status
    frontend_status = map_status_to_frontend(status.status)

    # Extract metadata
    metadata = status.metadata or {}
    file_format = metadata.get("format", "unknown").upper()
    file_size_bytes = metadata.get("file_size")

    # Build metadata dict
    api_metadata = {}
    if metadata.get("author"):
        api_metadata["author"] = metadata["author"]
    if metadata.get("published"):
        api_metadata["published"] = metadata["published"]
    if metadata.get("pages") or status.total_pages:
        api_metadata["pages"] = metadata.get("pages") or status.total_pages
    if file_size_bytes:
        api_metadata["size_bytes"] = file_size_bytes

    # Get embedding counts from metadata (set during completion)
    embeddings_data = None
    if frontend_status == "completed":
        visual_count = metadata.get("visual_embeddings", 0)
        text_count = metadata.get("text_embeddings", 0)
        chunk_count = metadata.get("text_chunks", 0)

        if visual_count or text_count or chunk_count:
            embeddings_data = {
                "visual_count": visual_count,
                "text_count": text_count,
                "chunk_count": chunk_count,
            }

    # Build processing dict
    processing_data = None
    if frontend_status == "processing":
        processing_data = {
            "progress": status.progress,
            "current_stage": status.stage,
        }
    elif frontend_status == "error":
        processing_data = {
            "progress": status.progress,
            "current_stage": status.stage,
            "error_message": status.error,
        }

    return DocumentAPIResponse(
        id=status.doc_id,
        title=status.filename,
        status=frontend_status,
        file_type=file_format,
        thumbnail_url=None,  # TODO: Add thumbnail support
        metadata=api_metadata if api_metadata else None,
        embeddings=embeddings_data,
        processing=processing_data,
        created_at=status.started_at.isoformat(),
        processed_at=status.completed_at.isoformat() if status.completed_at else None,
    )


# ============================================================================
# Document CRUD Endpoints
# ============================================================================

@router.get(
    "/documents",
    response_model=List[DocumentAPIResponse],
    summary="List all documents",
    description="Get list of all documents with optional filtering and sorting"
)
async def list_documents(
    status: Optional[str] = Query(None, description="Filter by status (comma-separated)"),
    file_type: Optional[str] = Query(None, description="Filter by file type (comma-separated)"),
    sort_by: str = Query("date", description="Sort by field (date, name, status)"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> List[DocumentAPIResponse]:
    """
    List all documents with optional filters.

    Query Parameters:
        status: Comma-separated status values (uploading, processing, completed, error)
        file_type: Comma-separated file types (PDF, DOCX, etc.)
        sort_by: Field to sort by (date, name, status)
        sort_order: Sort direction (asc, desc)
        limit: Maximum number of results (1-1000)
        offset: Number of results to skip

    Returns:
        List of DocumentAPIResponse objects
    """
    if not _status_manager:
        raise HTTPException(status_code=503, detail="Status manager not initialized")

    try:
        # Get all documents from status manager (use list_all for full ProcessingStatus objects)
        all_statuses = _status_manager.list_all(limit=limit + offset)

        # Transform to API response format
        documents = [transform_to_api_response(status) for status in all_statuses]

        # Apply status filter
        if status:
            status_filters = [s.strip().lower() for s in status.split(",")]
            documents = [doc for doc in documents if doc.status in status_filters]

        # Apply file type filter
        if file_type:
            type_filters = [t.strip().upper() for t in file_type.split(",")]
            documents = [doc for doc in documents if doc.file_type in type_filters]

        # Sort documents
        reverse = sort_order.lower() == "desc"
        if sort_by == "name":
            documents.sort(key=lambda d: d.title.lower(), reverse=reverse)
        elif sort_by == "status":
            documents.sort(key=lambda d: d.status, reverse=reverse)
        else:  # date (default)
            documents.sort(key=lambda d: d.created_at, reverse=reverse)

        # Apply pagination
        documents = documents[offset:offset + limit]

        logger.info(f"Listed {len(documents)} documents (filters: status={status}, type={file_type})")
        return documents

    except Exception as e:
        logger.error(f"Failed to list documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.get(
    "/document/{doc_id}",
    response_model=DocumentAPIResponse,
    summary="Get document by ID",
    description="Retrieve a single document by its unique identifier"
)
async def get_document(doc_id: str) -> DocumentAPIResponse:
    """
    Get a single document by ID.

    Args:
        doc_id: Document SHA-256 hash

    Returns:
        DocumentAPIResponse object

    Raises:
        HTTPException: 404 if document not found
    """
    if not _status_manager:
        raise HTTPException(status_code=503, detail="Status manager not initialized")

    try:
        status = _status_manager.get_status(doc_id)

        if status is None:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {doc_id}"
            )

        document = transform_to_api_response(status)
        logger.debug(f"Retrieved document {doc_id}: status={document.status}")
        return document

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document {doc_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@router.delete(
    "/document/{doc_id}",
    summary="Delete document",
    description="Delete a document and all its embeddings from ChromaDB"
)
async def delete_document(doc_id: str) -> dict:
    """
    Delete a document by ID.

    Removes all visual and text embeddings from ChromaDB and removes from status tracking.

    Args:
        doc_id: Document SHA-256 hash

    Returns:
        Success response with deletion counts

    Raises:
        HTTPException: 404 if document not found, 500 on error
    """
    if not _storage_client:
        raise HTTPException(status_code=503, detail="Storage client not initialized")

    if not _status_manager:
        raise HTTPException(status_code=503, detail="Status manager not initialized")

    try:
        # Check if document exists in status manager
        status = _status_manager.get_status(doc_id)
        if status is None:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {doc_id}"
            )

        filename = status.filename

        # Delete from ChromaDB
        visual_deleted, text_deleted = _storage_client.delete_document(doc_id)

        # Remove from status manager
        _status_manager.remove_status(doc_id)

        logger.info(
            f"Deleted document {doc_id} ({filename}): "
            f"{visual_deleted} visual, {text_deleted} text embeddings"
        )

        return {
            "success": True,
            "message": f"Document deleted: {filename}",
            "doc_id": doc_id,
            "visual_deleted": visual_deleted,
            "text_deleted": text_deleted,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document {doc_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@router.post(
    "/document/{doc_id}/reprocess",
    summary="Reprocess document",
    description="Queue a document for reprocessing"
)
async def reprocess_document(doc_id: str) -> dict:
    """
    Reprocess a document.

    Currently marks document status back to queued for reprocessing.
    In production, this would trigger a background job to re-extract and re-embed.

    Args:
        doc_id: Document SHA-256 hash

    Returns:
        Success response

    Raises:
        HTTPException: 404 if document not found, 500 on error
    """
    if not _status_manager:
        raise HTTPException(status_code=503, detail="Status manager not initialized")

    try:
        # Check if document exists
        status = _status_manager.get_status(doc_id)
        if status is None:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {doc_id}"
            )

        filename = status.filename

        # Reset status to queued for reprocessing
        # Need to manually update the dict to clear completed_at
        from datetime import datetime
        status_dict = _status_manager._status_dict[doc_id]
        status_dict["status"] = "queued"
        status_dict["progress"] = 0.0
        status_dict["stage"] = "Queued for reprocessing"
        status_dict["completed_at"] = None
        status_dict["error"] = None
        status_dict["updated_at"] = datetime.utcnow().isoformat()

        logger.info(f"Queued document {doc_id} ({filename}) for reprocessing")

        return {
            "success": True,
            "message": f"Document queued for reprocessing: {filename}",
            "doc_id": doc_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reprocess document {doc_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to reprocess document: {str(e)}")


@router.get(
    "/document/{doc_id}/download",
    summary="Download document",
    description="Download document in specified format (original, vtt, srt)"
)
async def download_document(
    doc_id: str,
    format: str = Query("original", description="Download format (original, vtt, srt)")
) -> FileResponse:
    """
    Download document in specified format.

    Args:
        doc_id: Document SHA-256 hash
        format: Download format (original, vtt, srt)

    Returns:
        FileResponse with document file

    Raises:
        HTTPException: 404 if document or file not found, 400 for invalid format
    """
    if not _status_manager:
        raise HTTPException(status_code=503, detail="Status manager not initialized")

    if not _storage_client:
        raise HTTPException(status_code=503, detail="Storage client not initialized")

    # Validate format
    valid_formats = ["original", "vtt", "srt"]
    if format not in valid_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format: {format}. Must be one of: {valid_formats}"
        )

    try:
        # Get document status to find original filename
        status = _status_manager.get_status(doc_id)
        if status is None:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {doc_id}"
            )

        filename = status.filename

        if format == "original":
            # Find original file in uploads directory
            upload_dir = Path("/uploads")
            # Files are stored as {doc_id}_{filename} or just filename
            possible_paths = [
                upload_dir / filename,
                upload_dir / f"{doc_id}_{filename}",
            ]

            file_path = None
            for path in possible_paths:
                if path.exists():
                    file_path = path
                    break

            if not file_path:
                raise HTTPException(
                    status_code=404,
                    detail=f"Original file not found for document {doc_id}"
                )

            return FileResponse(
                path=str(file_path),
                filename=filename,
                media_type="application/octet-stream"
            )

        else:
            # VTT/SRT format - not yet implemented
            # TODO: Implement VTT/SRT export from text chunks
            raise HTTPException(
                status_code=501,
                detail=f"Format '{format}' not yet implemented. Use /api/document/{doc_id}/markdown instead."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download document {doc_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to download document: {str(e)}")

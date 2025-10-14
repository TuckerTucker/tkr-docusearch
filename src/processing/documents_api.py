"""
Documents API for DocuSearch MVP.

Provides REST API endpoints for document listing and viewing.
Serves page images and thumbnails for the monitoring UI.

Provider: api-agent (Wave 3)
Consumers: ui-agent (Wave 4)
Contract: integration-contracts/03-documents-api.contract.md
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.config.image_config import PAGE_IMAGE_DIR
from src.storage import ChromaClient

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="", tags=["documents"])

# Validation patterns (security)
DOC_ID_PATTERN = re.compile(r'^[a-zA-Z0-9\-]{8,64}$')
FILENAME_PATTERN = re.compile(r'^(page\d{3}(_thumb\.jpg|\.png)|cover\.(jpg|jpeg|png))$')


# ============================================================================
# Request/Response Models
# ============================================================================

class DocumentListItem(BaseModel):
    """Document list item schema."""
    doc_id: str = Field(..., description="Document identifier (SHA-256 hash)")
    filename: str = Field(..., description="Original filename")
    page_count: int = Field(..., description="Number of pages")
    chunk_count: int = Field(..., description="Number of text chunks")
    date_added: str = Field(..., description="ISO 8601 timestamp")
    collections: List[str] = Field(..., description="Collections containing this document")
    has_images: bool = Field(..., description="True if page images exist")
    first_page_thumb: Optional[str] = Field(None, description="URL to first page thumbnail")


class DocumentListResponse(BaseModel):
    """Response model for GET /documents."""
    documents: List[DocumentListItem]
    total: int
    limit: int
    offset: int


class PageInfo(BaseModel):
    """Page information schema."""
    page_number: int = Field(..., description="Page number (1-indexed)")
    image_path: Optional[str] = Field(None, description="URL to full-resolution image")
    thumb_path: Optional[str] = Field(None, description="URL to thumbnail")
    embedding_id: str = Field(..., description="ChromaDB embedding ID")


class ChunkInfo(BaseModel):
    """Text chunk information schema."""
    chunk_id: str = Field(..., description="Chunk identifier")
    text_content: str = Field(..., description="Full text content")
    embedding_id: str = Field(..., description="ChromaDB embedding ID")
    start_time: Optional[float] = Field(None, description="Start time in seconds (audio only)")
    end_time: Optional[float] = Field(None, description="End time in seconds (audio only)")
    has_timestamps: bool = Field(False, description="True if chunk has timestamps")


class DocumentMetadata(BaseModel):
    """Document metadata schema."""
    page_count: int
    chunk_count: int
    has_images: bool
    collections: List[str]
    raw_metadata: Optional[Dict[str, Any]] = Field(None, description="Raw metadata from ChromaDB (includes audio metadata)")
    vtt_available: bool = Field(False, description="True if VTT file exists (audio only)")
    markdown_available: bool = Field(False, description="True if markdown file exists")
    has_timestamps: bool = Field(False, description="True if document has word-level timestamps (audio only)")


class DocumentDetail(BaseModel):
    """Document detail schema."""
    doc_id: str
    filename: str
    date_added: str
    pages: List[PageInfo]
    chunks: List[ChunkInfo]
    metadata: DocumentMetadata


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    error: str = Field(..., description="Human-readable error message")
    code: str = Field(..., description="Machine-readable error code")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional error details")


# ============================================================================
# Utility Functions
# ============================================================================

def validate_doc_id(doc_id: str) -> bool:
    """Validate doc_id to prevent path traversal.

    Args:
        doc_id: Document identifier to validate

    Returns:
        True if valid, False otherwise
    """
    return bool(DOC_ID_PATTERN.match(doc_id))


def validate_filename(filename: str) -> bool:
    """Validate filename to prevent path traversal.

    Args:
        filename: Filename to validate

    Returns:
        True if valid, False otherwise
    """
    return bool(FILENAME_PATTERN.match(filename))


def get_chroma_client() -> ChromaClient:
    """Get ChromaDB client instance.

    Returns:
        ChromaClient instance

    Raises:
        HTTPException: If client initialization fails
    """
    try:
        import os
        host = os.getenv("CHROMA_HOST", "localhost")
        port = int(os.getenv("CHROMA_PORT", "8001"))
        return ChromaClient(host=host, port=port)
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB client: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Database connection failed",
                "code": "DATABASE_ERROR",
                "details": {"message": str(e)}
            }
        )


def aggregate_documents(visual_metadata: List[Dict], text_metadata: List[Dict]) -> Dict[str, Dict]:
    """Aggregate document information from ChromaDB metadata.

    Args:
        visual_metadata: List of visual embedding metadata
        text_metadata: List of text embedding metadata

    Returns:
        Dictionary mapping doc_id to aggregated document info
    """
    documents = {}

    # Process visual embeddings
    for item in visual_metadata:
        doc_id = item.get("doc_id")
        if not doc_id:
            continue

        if doc_id not in documents:
            documents[doc_id] = {
                "doc_id": doc_id,
                "filename": item.get("filename", "unknown"),
                "date_added": item.get("timestamp", ""),
                "pages": [],
                "chunks": [],
                "collections": [],
                "has_images": False
            }

        # Add page info
        page_num = item.get("page")
        if page_num:
            documents[doc_id]["pages"].append({
                "page_number": page_num,
                "image_path": item.get("image_path"),
                "thumb_path": item.get("thumb_path"),
                "metadata": item
            })

        if item.get("image_path") or item.get("thumb_path"):
            documents[doc_id]["has_images"] = True

        if "visual" not in documents[doc_id]["collections"]:
            documents[doc_id]["collections"].append("visual")

    # Process text embeddings
    for item in text_metadata:
        doc_id = item.get("doc_id")
        if not doc_id:
            continue

        if doc_id not in documents:
            documents[doc_id] = {
                "doc_id": doc_id,
                "filename": item.get("filename", "unknown"),
                "date_added": item.get("timestamp", ""),
                "pages": [],
                "chunks": [],
                "collections": [],
                "has_images": False
            }

        # Add chunk info
        chunk_id = item.get("chunk_id")
        if chunk_id is not None:
            documents[doc_id]["chunks"].append({
                "chunk_id": f"chunk_{chunk_id}",
                "metadata": item
            })

        if "text" not in documents[doc_id]["collections"]:
            documents[doc_id]["collections"].append("text")

    # Sort pages by page number
    for doc_id in documents:
        documents[doc_id]["pages"].sort(key=lambda p: p["page_number"])

    return documents


# ============================================================================
# API Endpoints
# ============================================================================

@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="List all documents",
    description="Get a paginated list of all stored documents with metadata"
)
async def list_documents(
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    search: Optional[str] = Query(None, description="Filter by filename (case-insensitive)"),
    sort_by: str = Query("date_added", description="Sort field: date_added, filename, page_count")
):
    """List all stored documents with metadata.

    Args:
        limit: Number of results (1-100)
        offset: Pagination offset
        search: Optional filename filter
        sort_by: Sort field (date_added, filename, page_count)

    Returns:
        DocumentListResponse with paginated documents

    Raises:
        HTTPException: On database error
    """
    try:
        client = get_chroma_client()

        # Get all visual and text embeddings
        visual_data = client._visual_collection.get()
        text_data = client._text_collection.get()

        # Aggregate by document
        documents = aggregate_documents(
            visual_data.get("metadatas", []),
            text_data.get("metadatas", [])
        )

        # Convert to list
        doc_list = list(documents.values())

        # Apply search filter
        if search:
            search_lower = search.lower()
            doc_list = [
                doc for doc in doc_list
                if search_lower in doc["filename"].lower()
            ]

        # Apply sorting
        if sort_by == "filename":
            doc_list.sort(key=lambda d: d["filename"].lower())
        elif sort_by == "page_count":
            doc_list.sort(key=lambda d: len(d["pages"]), reverse=True)
        else:  # date_added (default)
            doc_list.sort(key=lambda d: d["date_added"], reverse=True)

        # Get total before pagination
        total = len(doc_list)

        # Apply pagination
        doc_list = doc_list[offset:offset + limit]

        # Convert to response format
        response_docs = []
        for doc in doc_list:
            first_page_thumb = None
            if doc["pages"] and doc["has_images"]:
                first_page = doc["pages"][0]
                if first_page.get("thumb_path"):
                    # Convert to URL format
                    thumb_path = first_page["thumb_path"]
                    # Extract doc_id and filename from path
                    if "/" in thumb_path:
                        parts = thumb_path.split("/")
                        if len(parts) >= 2:
                            doc_id_part = parts[-2]
                            filename_part = parts[-1]
                            first_page_thumb = f"/images/{doc_id_part}/{filename_part}"

            response_docs.append(DocumentListItem(
                doc_id=doc["doc_id"],
                filename=doc["filename"],
                page_count=len(doc["pages"]),
                chunk_count=len(doc["chunks"]),
                date_added=doc["date_added"],
                collections=doc["collections"],
                has_images=doc["has_images"],
                first_page_thumb=first_page_thumb
            ))

        return DocumentListResponse(
            documents=response_docs,
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to retrieve documents",
                "code": "DATABASE_ERROR",
                "details": {"message": str(e)}
            }
        )


@router.get(
    "/documents/{doc_id}",
    response_model=DocumentDetail,
    summary="Get document details",
    description="Get detailed metadata for a specific document including all pages and chunks"
)
async def get_document(doc_id: str):
    """Get detailed metadata for a specific document.

    Args:
        doc_id: Document identifier (SHA-256 hash)

    Returns:
        DocumentDetail with full document information

    Raises:
        HTTPException: 404 if document not found, 400 if invalid doc_id
    """
    # Validate doc_id
    if not validate_doc_id(doc_id):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid document ID format",
                "code": "INVALID_DOC_ID",
                "details": {"doc_id": doc_id}
            }
        )

    try:
        client = get_chroma_client()

        # Query visual collection
        visual_data = client._visual_collection.get(
            where={"doc_id": doc_id}
        )

        # Query text collection
        text_data = client._text_collection.get(
            where={"doc_id": doc_id}
        )

        # Check if document exists
        visual_ids = visual_data.get("ids", [])
        text_ids = text_data.get("ids", [])

        if not visual_ids and not text_ids:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Document not found",
                    "code": "DOCUMENT_NOT_FOUND",
                    "details": {"doc_id": doc_id}
                }
            )

        # Build pages list
        pages = []
        visual_metadatas = visual_data.get("metadatas", [])
        for idx, metadata in enumerate(visual_metadatas):
            page_num = metadata.get("page")
            image_path = metadata.get("image_path")
            thumb_path = metadata.get("thumb_path")

            # Convert paths to URLs
            if image_path and "/" in image_path:
                parts = image_path.split("/")
                if len(parts) >= 2:
                    image_path = f"/images/{parts[-2]}/{parts[-1]}"

            if thumb_path and "/" in thumb_path:
                parts = thumb_path.split("/")
                if len(parts) >= 2:
                    thumb_path = f"/images/{parts[-2]}/{parts[-1]}"

            pages.append(PageInfo(
                page_number=page_num,
                image_path=image_path,
                thumb_path=thumb_path,
                embedding_id=visual_ids[idx]
            ))

        # Sort pages by page number
        pages.sort(key=lambda p: p.page_number)

        # Build chunks list
        chunks = []
        text_metadatas = text_data.get("metadatas", [])
        for idx, metadata in enumerate(text_metadatas):
            chunk_id = metadata.get("chunk_id", idx)
            text_preview = metadata.get("text_preview", "")

            # Get timestamp fields (Wave 1)
            start_time = metadata.get("start_time")
            end_time = metadata.get("end_time")
            has_timestamps = metadata.get("has_timestamps", False)

            chunks.append(ChunkInfo(
                chunk_id=f"chunk_{chunk_id}",
                text_content=text_preview,
                embedding_id=text_ids[idx],
                start_time=start_time,
                end_time=end_time,
                has_timestamps=has_timestamps
            ))

        # Get document metadata
        filename = "unknown"
        date_added = ""

        if visual_metadatas:
            filename = visual_metadatas[0].get("filename", filename)
            date_added = visual_metadatas[0].get("timestamp", date_added)
        elif text_metadatas:
            filename = text_metadatas[0].get("filename", filename)
            date_added = text_metadatas[0].get("timestamp", date_added)

        has_images = any(p.image_path or p.thumb_path for p in pages)
        collections = []
        if visual_ids:
            collections.append("visual")
        if text_ids:
            collections.append("text")

        # Get raw metadata from first chunk (includes audio metadata)
        raw_metadata = None
        if text_metadatas:
            raw_metadata = text_metadatas[0]
        elif visual_metadatas:
            raw_metadata = visual_metadatas[0]

        # Check for VTT and markdown availability (Wave 2)
        vtt_available = raw_metadata.get("vtt_available", False) if raw_metadata else False
        markdown_available = raw_metadata.get("markdown_available", False) if raw_metadata else False
        has_word_timestamps = raw_metadata.get("has_word_timestamps", False) if raw_metadata else False

        return DocumentDetail(
            doc_id=doc_id,
            filename=filename,
            date_added=date_added,
            pages=pages,
            chunks=chunks,
            metadata=DocumentMetadata(
                page_count=len(pages),
                chunk_count=len(chunks),
                has_images=has_images,
                collections=collections,
                raw_metadata=raw_metadata,
                vtt_available=vtt_available,
                markdown_available=markdown_available,
                has_timestamps=has_word_timestamps
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {doc_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to retrieve document",
                "code": "DATABASE_ERROR",
                "details": {"message": str(e)}
            }
        )


@router.get(
    "/documents/{doc_id}/markdown",
    summary="Get document markdown",
    description="Download document as markdown with YAML frontmatter",
    responses={
        200: {"description": "Markdown file", "content": {"text/markdown": {}}},
        400: {"description": "Invalid document ID"},
        404: {"description": "Markdown file not found"}
    }
)
async def get_markdown(doc_id: str):
    """Get document as markdown with frontmatter.

    Args:
        doc_id: Document identifier (SHA-256 hash)

    Returns:
        FileResponse with markdown content

    Raises:
        HTTPException: 404 if markdown not found, 400 if invalid doc_id
    """
    # Validate doc_id
    if not validate_doc_id(doc_id):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid document ID format",
                "code": "INVALID_DOC_ID",
                "details": {"doc_id": doc_id}
            }
        )

    # Check if markdown file exists
    markdown_path = Path("data/markdown") / f"{doc_id}.md"

    if not markdown_path.exists():
        logger.info(f"Markdown file not found: {doc_id}")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Markdown file not found",
                "code": "MARKDOWN_NOT_FOUND",
                "details": {"doc_id": doc_id}
            }
        )

    # Get filename from ChromaDB for the download filename
    try:
        client = get_chroma_client()
        text_data = client._text_collection.get(
            where={"doc_id": doc_id},
            limit=1
        )

        filename = "unknown.md"
        if text_data.get("metadatas"):
            original_filename = text_data["metadatas"][0].get("filename", "unknown")
            # Remove extension and add .md
            filename = Path(original_filename).stem + ".md"
    except Exception as e:
        logger.warning(f"Failed to get filename from ChromaDB: {e}")
        filename = f"{doc_id}.md"

    # Return file with appropriate headers
    return FileResponse(
        path=markdown_path,
        media_type="text/markdown",
        filename=filename,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        }
    )


@router.get(
    "/documents/{doc_id}/vtt",
    summary="Get document VTT captions",
    description="Download VTT caption file for audio documents",
    responses={
        200: {"description": "VTT file", "content": {"text/vtt": {}}},
        400: {"description": "Invalid document ID"},
        404: {"description": "VTT file not found"}
    }
)
async def get_vtt(doc_id: str):
    """Get VTT caption file for audio documents.

    Args:
        doc_id: Document identifier (SHA-256 hash)

    Returns:
        FileResponse with VTT content

    Raises:
        HTTPException: 404 if VTT not found, 400 if invalid doc_id
    """
    # Validate doc_id
    if not validate_doc_id(doc_id):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid document ID format",
                "code": "INVALID_DOC_ID",
                "details": {"doc_id": doc_id}
            }
        )

    # Check if VTT file exists
    vtt_path = Path("data/vtt") / f"{doc_id}.vtt"

    if not vtt_path.exists():
        logger.info(f"VTT file not found: {doc_id}")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "VTT file not found",
                "code": "VTT_NOT_FOUND",
                "details": {"doc_id": doc_id, "message": "VTT captions only available for audio files with word-level timestamps"}
            }
        )

    # Get filename from ChromaDB for the download filename
    try:
        client = get_chroma_client()
        text_data = client._text_collection.get(
            where={"doc_id": doc_id},
            limit=1
        )

        filename = "unknown.vtt"
        if text_data.get("metadatas"):
            original_filename = text_data["metadatas"][0].get("filename", "unknown")
            # Remove extension and add .vtt
            filename = Path(original_filename).stem + ".vtt"
    except Exception as e:
        logger.warning(f"Failed to get filename from ChromaDB: {e}")
        filename = f"{doc_id}.vtt"

    # Return file with appropriate headers
    return FileResponse(
        path=vtt_path,
        media_type="text/vtt",
        filename=filename,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        }
    )


@router.get(
    "/images/{doc_id}/{filename}",
    summary="Serve page image",
    description="Serve page image or thumbnail file",
    responses={
        200: {"description": "Image file", "content": {"image/png": {}, "image/jpeg": {}}},
        403: {"description": "Invalid filename or path traversal attempt"},
        404: {"description": "Image file not found"}
    }
)
async def get_image(doc_id: str, filename: str):
    """Serve page image or thumbnail files.

    Args:
        doc_id: Document identifier
        filename: Image filename (e.g., page001.png, page001_thumb.jpg)

    Returns:
        FileResponse with image data

    Raises:
        HTTPException: 403 for invalid paths, 404 if file not found
    """
    # Validate doc_id
    if not validate_doc_id(doc_id):
        logger.warning(f"Invalid doc_id format: {doc_id}")
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Invalid document ID format",
                "code": "INVALID_DOC_ID",
                "details": {"doc_id": doc_id}
            }
        )

    # Validate filename
    if not validate_filename(filename):
        logger.warning(f"Invalid filename format: {filename}")
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Invalid filename format",
                "code": "INVALID_FILENAME",
                "details": {"filename": filename}
            }
        )

    # Try both image directories: page_images (for PDFs) and images (for album art)
    search_dirs = [
        Path(PAGE_IMAGE_DIR) / doc_id,  # data/page_images/{doc_id}/
        Path("data/images") / doc_id     # data/images/{doc_id}/
    ]

    image_path = None
    image_dir = None

    for search_dir in search_dirs:
        candidate_path = search_dir / filename

        # Security: Verify the resolved path is within the expected directory
        try:
            resolved_path = candidate_path.resolve()
            resolved_dir = search_dir.resolve()

            if not str(resolved_path).startswith(str(resolved_dir)):
                logger.error(f"Path traversal attempt: {resolved_path}")
                continue

            if resolved_path.exists():
                image_path = resolved_path
                image_dir = resolved_dir
                break
        except Exception as e:
            logger.debug(f"Path resolution failed for {search_dir}: {e}")
            continue

    # If still no valid path found, raise 404
    if not image_path or not image_dir:
        logger.info(f"Image not found in any directory: {filename} for doc_id {doc_id}")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Image file not found",
                "code": "IMAGE_NOT_FOUND",
                "details": {"doc_id": doc_id, "filename": filename}
            }
        )

    # Determine content type
    if filename.endswith('.png'):
        media_type = "image/png"
    elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
        media_type = "image/jpeg"
    else:
        media_type = "application/octet-stream"

    # Return file with caching headers
    return FileResponse(
        path=image_path,
        media_type=media_type,
        headers={
            "Cache-Control": "max-age=86400",  # 24 hours
        }
    )

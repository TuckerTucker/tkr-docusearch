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
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.config.filter_groups import resolve_filter_group
from src.config.image_config import PAGE_IMAGE_DIR
from src.processing.api import structure_router
from src.processing.file_validator import get_supported_extensions
from src.storage import ChromaClient

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="", tags=["documents"])

# Include structure endpoints router
router.include_router(structure_router)

# Validation patterns (security)
DOC_ID_PATTERN = re.compile(r"^[a-zA-Z0-9\-]{8,64}$")
FILENAME_PATTERN = re.compile(r"^(page\d{3}(_thumb\.jpg|\.png)|cover\.(jpg|jpeg|png|svg))$")


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
    raw_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Raw metadata from ChromaDB (includes audio metadata)"
    )
    vtt_available: bool = Field(False, description="True if VTT file exists (audio only)")
    markdown_available: bool = Field(False, description="True if markdown file exists")
    has_timestamps: bool = Field(
        False, description="True if document has word-level timestamps (audio only)"
    )
    has_album_art: bool = Field(False, description="True if album art is available (audio only)")
    album_art_url: Optional[str] = Field(
        None, description="URL to album art cover image (audio only)"
    )


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


class FormatGroup(BaseModel):
    """File format group schema."""

    id: str = Field(..., description="Group identifier")
    label: str = Field(..., description="Display label")
    extensions: List[str] = Field(..., description="File extensions in this group")


class SupportedFormatsResponse(BaseModel):
    """Response model for GET /config/supported-formats."""

    extensions: List[str] = Field(
        ..., description="All supported file extensions (with dot prefix)"
    )
    groups: List[FormatGroup] = Field(..., description="Format groups for filtering")


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
                "details": {"message": str(e)},
            },
        )


def _create_empty_document(doc_id: str, filename: str, timestamp: str) -> Dict[str, Any]:
    """Create empty document structure.

    Args:
        doc_id: Document identifier
        filename: Original filename
        timestamp: Document timestamp

    Returns:
        Empty document dictionary
    """
    return {
        "doc_id": doc_id,
        "filename": filename,
        "date_added": timestamp,
        "pages": [],
        "chunks": [],
        "collections": [],
        "has_images": False,
    }


def _process_visual_metadata(documents: Dict[str, Dict], visual_metadata: List[Dict]) -> None:
    """Process visual embeddings and update documents dict.

    Args:
        documents: Documents dictionary to update
        visual_metadata: List of visual embedding metadata
    """
    for item in visual_metadata:
        doc_id = item.get("doc_id")
        if not doc_id:
            continue

        # Initialize document if needed
        if doc_id not in documents:
            documents[doc_id] = _create_empty_document(
                doc_id, item.get("filename", "unknown"), item.get("timestamp", "")
            )

        # Add page info
        page_num = item.get("page")
        if page_num:
            documents[doc_id]["pages"].append(
                {
                    "page_number": page_num,
                    "image_path": item.get("image_path"),
                    "thumb_path": item.get("thumb_path"),
                    "metadata": item,
                }
            )

        # Track if document has images
        if item.get("image_path") or item.get("thumb_path"):
            documents[doc_id]["has_images"] = True

        # Add visual collection
        if "visual" not in documents[doc_id]["collections"]:
            documents[doc_id]["collections"].append("visual")


def _process_text_metadata(documents: Dict[str, Dict], text_metadata: List[Dict]) -> None:
    """Process text embeddings and update documents dict.

    Args:
        documents: Documents dictionary to update
        text_metadata: List of text embedding metadata
    """
    for item in text_metadata:
        doc_id = item.get("doc_id")
        if not doc_id:
            continue

        # Initialize document if needed
        if doc_id not in documents:
            documents[doc_id] = _create_empty_document(
                doc_id, item.get("filename", "unknown"), item.get("timestamp", "")
            )

        # Add chunk info
        chunk_id = item.get("chunk_id")
        if chunk_id is not None:
            documents[doc_id]["chunks"].append({"chunk_id": f"chunk_{chunk_id}", "metadata": item})

        # Add text collection
        if "text" not in documents[doc_id]["collections"]:
            documents[doc_id]["collections"].append("text")


def _sort_document_pages(documents: Dict[str, Dict]) -> None:
    """Sort pages by page number for all documents.

    Args:
        documents: Documents dictionary to update
    """
    for doc_id in documents:
        documents[doc_id]["pages"].sort(key=lambda p: p["page_number"])


def aggregate_documents(visual_metadata: List[Dict], text_metadata: List[Dict]) -> Dict[str, Dict]:
    """Aggregate document information from ChromaDB metadata.

    Args:
        visual_metadata: List of visual embedding metadata
        text_metadata: List of text embedding metadata

    Returns:
        Dictionary mapping doc_id to aggregated document info
    """
    documents: Dict[str, Dict] = {}

    # Process visual and text embeddings
    _process_visual_metadata(documents, visual_metadata)
    _process_text_metadata(documents, text_metadata)

    # Sort pages by page number
    _sort_document_pages(documents)

    return documents


# ============================================================================
# API Endpoints
# ============================================================================


@router.get(
    "/config/supported-formats",
    response_model=SupportedFormatsResponse,
    summary="Get supported file formats",
    description="Get list of supported file formats and format groups for filtering",
)
async def get_supported_formats():
    """Get supported file formats configuration.

    Returns:
        SupportedFormatsResponse with extensions and groups

    Note:
        This endpoint serves as the single source of truth for supported formats.
        Frontend should fetch this on initialization to stay in sync with backend.
    """
    # Get extensions from file_validator.py (respects SUPPORTED_FORMATS env var)
    extensions = sorted(get_supported_extensions())

    # Define format groups for filtering
    # Extensions without dots for matching against file extensions
    ext_set = {ext.lstrip(".") for ext in extensions}

    groups = []

    # PDF group
    pdf_exts = [f".{ext}" for ext in ["pdf"] if ext in ext_set]
    if pdf_exts:
        groups.append(FormatGroup(id="pdf", label="PDF", extensions=pdf_exts))

    # Audio group (only mp3 and wav - fully supported by Docling)
    audio_exts = [f".{ext}" for ext in ["mp3", "wav"] if ext in ext_set]
    if audio_exts:
        groups.append(FormatGroup(id="audio", label="Audio", extensions=audio_exts))

    # Office Documents group
    office_exts = [f".{ext}" for ext in ["docx", "doc", "xlsx", "xls"] if ext in ext_set]
    if office_exts:
        groups.append(FormatGroup(id="office", label="Office Documents", extensions=office_exts))

    # Text Documents group
    text_exts = [
        f".{ext}" for ext in ["md", "asciidoc", "vtt", "html", "xhtml", "csv"] if ext in ext_set
    ]
    if text_exts:
        groups.append(FormatGroup(id="text", label="Text Documents", extensions=text_exts))

    # Presentations group
    presentation_exts = [f".{ext}" for ext in ["pptx", "ppt"] if ext in ext_set]
    if presentation_exts:
        groups.append(
            FormatGroup(id="presentations", label="Presentations", extensions=presentation_exts)
        )

    # Images group
    image_exts = [
        f".{ext}" for ext in ["png", "jpg", "jpeg", "tiff", "bmp", "webp"] if ext in ext_set
    ]
    if image_exts:
        groups.append(FormatGroup(id="images", label="Images", extensions=image_exts))

    return SupportedFormatsResponse(extensions=extensions, groups=groups)


def _apply_search_filter(doc_list: List[Dict], search: Optional[str]) -> List[Dict]:
    """Filter documents by filename search.

    Args:
        doc_list: List of documents to filter
        search: Search string (case-insensitive)

    Returns:
        Filtered list of documents
    """
    if not search:
        return doc_list

    search_lower = search.lower()
    return [doc for doc in doc_list if search_lower in doc["filename"].lower()]


def _apply_file_type_filter(doc_list: List[Dict], file_type_group: str) -> List[Dict]:
    """Filter documents by file type group.

    Args:
        doc_list: List of documents to filter
        file_type_group: Filter group (all, pdf, audio, office, text, images)

    Returns:
        Filtered list of documents
    """
    # Get extensions for the group
    extensions = resolve_filter_group(file_type_group)

    # If None (all group) or invalid group, return all documents
    if extensions is None:
        return doc_list

    # Filter documents by extension
    filtered = []
    for doc in doc_list:
        filename = doc.get("filename", "")
        file_ext = Path(filename).suffix.lower()

        if file_ext in extensions:
            filtered.append(doc)

    return filtered


def _sort_documents(doc_list: List[Dict], sort_by: str) -> None:
    """Sort documents in-place by specified criteria.

    Args:
        doc_list: List of documents to sort
        sort_by: Sort order (newest_first, oldest_first, name_asc, name_desc)
    """
    if sort_by == "name_asc":
        doc_list.sort(key=lambda d: d["filename"].lower())
    elif sort_by == "name_desc":
        doc_list.sort(key=lambda d: d["filename"].lower(), reverse=True)
    elif sort_by == "oldest_first":
        doc_list.sort(key=lambda d: d["date_added"])
    else:  # newest_first (default)
        doc_list.sort(key=lambda d: d["date_added"], reverse=True)


def _resolve_document_thumbnail(doc: Dict) -> Optional[str]:
    """Resolve thumbnail URL for document.

    Args:
        doc: Document dictionary

    Returns:
        Thumbnail URL or None
    """
    # Check for page thumbnail (PDF, DOCX, PPTX)
    if doc["pages"] and doc["has_images"]:
        first_page = doc["pages"][0]
        if first_page.get("thumb_path"):
            thumb_path = first_page["thumb_path"]
            if "/" in thumb_path:
                parts = thumb_path.split("/")
                if len(parts) >= 2:
                    doc_id_part = parts[-2]
                    filename_part = parts[-1]
                    return f"/images/{doc_id_part}/{filename_part}"

    # Check for album art (audio files)
    images_dir = Path("data/images") / doc["doc_id"]
    if images_dir.exists():
        for ext in ["jpg", "jpeg", "png"]:
            cover_file = images_dir / f"cover.{ext}"
            if cover_file.exists():
                return f"/documents/{doc['doc_id']}/cover"

    return None


def _convert_to_response_items(doc_list: List[Dict]) -> List[DocumentListItem]:
    """Convert document dictionaries to response items.

    Args:
        doc_list: List of document dictionaries

    Returns:
        List of DocumentListItem objects
    """
    response_docs = []
    for doc in doc_list:
        first_page_thumb = _resolve_document_thumbnail(doc)

        response_docs.append(
            DocumentListItem(
                doc_id=doc["doc_id"],
                filename=doc["filename"],
                page_count=len(doc["pages"]),
                chunk_count=len(doc["chunks"]),
                date_added=doc["date_added"],
                collections=doc["collections"],
                has_images=doc["has_images"],
                first_page_thumb=first_page_thumb,
            )
        )

    return response_docs


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="List all documents",
    description="Get a paginated list of all stored documents with metadata",
)
async def list_documents(
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),  # noqa: B008
    offset: int = Query(0, ge=0, description="Pagination offset"),  # noqa: B008
    search: Optional[str] = Query(  # noqa: B008
        None, description="Filter by filename (case-insensitive)"
    ),
    sort_by: str = Query(  # noqa: B008
        "newest_first", description="Sort order: newest_first, oldest_first, name_asc, name_desc"
    ),
    file_type_group: str = Query(  # noqa: B008
        "all",
        description="Filter by file type group: all, pdf, audio, office, text, images",
    ),
):
    """List all stored documents with metadata.

    Args:
        limit: Number of results (1-100)
        offset: Pagination offset
        search: Optional filename filter
        sort_by: Sort order (newest_first, oldest_first, name_asc, name_desc)
        file_type_group: Filter by file type group (all, pdf, audio, office, text, images)

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
            visual_data.get("metadatas", []), text_data.get("metadatas", [])
        )

        # Convert to list and apply filters/sorting
        doc_list = list(documents.values())
        doc_list = _apply_search_filter(doc_list, search)
        doc_list = _apply_file_type_filter(doc_list, file_type_group)
        _sort_documents(doc_list, sort_by)

        # Get total before pagination
        total = len(doc_list)

        # Apply pagination
        doc_list = doc_list[offset : offset + limit]

        # Convert to response format
        response_docs = _convert_to_response_items(doc_list)

        return DocumentListResponse(
            documents=response_docs, total=total, limit=limit, offset=offset
        )

    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to retrieve documents",
                "code": "DATABASE_ERROR",
                "details": {"message": str(e)},
            },
        )


def _convert_path_to_url(path: Optional[str]) -> Optional[str]:
    """Convert file path to URL format.

    Args:
        path: File path with directory structure

    Returns:
        URL path or None
    """
    if not path or "/" not in path:
        return path

    parts = path.split("/")
    if len(parts) >= 2:
        return f"/images/{parts[-2]}/{parts[-1]}"

    return path


def _build_page_list(visual_data: Dict, visual_ids: List[str]) -> List[PageInfo]:
    """Build list of page information from visual data.

    Args:
        visual_data: Visual collection data from ChromaDB
        visual_ids: List of visual embedding IDs

    Returns:
        List of PageInfo objects sorted by page number
    """
    pages = []
    visual_metadatas = visual_data.get("metadatas", [])

    for idx, metadata in enumerate(visual_metadatas):
        page_num = metadata.get("page")
        image_path = _convert_path_to_url(metadata.get("image_path"))
        thumb_path = _convert_path_to_url(metadata.get("thumb_path"))

        pages.append(
            PageInfo(
                page_number=page_num,
                image_path=image_path,
                thumb_path=thumb_path,
                embedding_id=visual_ids[idx],
            )
        )

    pages.sort(key=lambda p: p.page_number)
    return pages


def _build_chunk_list(text_data: Dict, text_ids: List[str]) -> List[ChunkInfo]:
    """Build list of chunk information from text data.

    Args:
        text_data: Text collection data from ChromaDB
        text_ids: List of text embedding IDs

    Returns:
        List of ChunkInfo objects
    """
    chunks = []
    text_metadatas = text_data.get("metadatas", [])

    for idx, metadata in enumerate(text_metadatas):
        chunk_id = metadata.get("chunk_id", idx)
        text_content = metadata.get("full_text") or metadata.get("text_preview", "")
        start_time = metadata.get("start_time")
        end_time = metadata.get("end_time")
        has_timestamps = metadata.get("has_timestamps", False)

        chunks.append(
            ChunkInfo(
                chunk_id=f"chunk_{chunk_id}",
                text_content=text_content,
                embedding_id=text_ids[idx],
                start_time=start_time,
                end_time=end_time,
                has_timestamps=has_timestamps,
            )
        )

    return chunks


def _extract_document_metadata(
    visual_metadatas: List[Dict], text_metadatas: List[Dict]
) -> tuple[str, str, Optional[Dict]]:
    """Extract filename, date, and raw metadata.

    Args:
        visual_metadatas: Visual metadata list
        text_metadatas: Text metadata list

    Returns:
        Tuple of (filename, date_added, raw_metadata)
    """
    filename = "unknown"
    date_added = ""
    raw_metadata = None

    if visual_metadatas:
        filename = visual_metadatas[0].get("filename", filename)
        date_added = visual_metadatas[0].get("timestamp", date_added)
        raw_metadata = visual_metadatas[0]
    elif text_metadatas:
        filename = text_metadatas[0].get("filename", filename)
        date_added = text_metadatas[0].get("timestamp", date_added)
        raw_metadata = text_metadatas[0]

    return filename, date_added, raw_metadata


def _check_album_art_availability(doc_id: str) -> tuple[bool, Optional[str]]:
    """Check if album art exists for document.

    Args:
        doc_id: Document identifier

    Returns:
        Tuple of (has_album_art, album_art_url)
    """
    images_dir = Path("data/images") / doc_id
    if not images_dir.exists():
        return False, None

    for ext in ["jpg", "jpeg", "png"]:
        cover_file = images_dir / f"cover.{ext}"
        if cover_file.exists():
            return True, f"/documents/{doc_id}/cover"

    return False, None


@router.get(
    "/documents/{doc_id}",
    response_model=DocumentDetail,
    summary="Get document details",
    description="Get detailed metadata for a specific document including all pages and chunks",
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
                "details": {"doc_id": doc_id},
            },
        )

    try:
        client = get_chroma_client()

        # Query visual and text collections
        visual_data = client._visual_collection.get(where={"doc_id": doc_id})
        text_data = client._text_collection.get(where={"doc_id": doc_id})

        visual_ids = visual_data.get("ids", [])
        text_ids = text_data.get("ids", [])

        # Check if document exists
        if not visual_ids and not text_ids:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Document not found",
                    "code": "DOCUMENT_NOT_FOUND",
                    "details": {"doc_id": doc_id},
                },
            )

        # Build pages and chunks
        pages = _build_page_list(visual_data, visual_ids)
        chunks = _build_chunk_list(text_data, text_ids)

        # Extract document metadata
        visual_metadatas = visual_data.get("metadatas", [])
        text_metadatas = text_data.get("metadatas", [])
        filename, date_added, raw_metadata = _extract_document_metadata(
            visual_metadatas, text_metadatas
        )

        # Build collections list
        has_images = any(p.image_path or p.thumb_path for p in pages)
        collections = []
        if visual_ids:
            collections.append("visual")
        if text_ids:
            collections.append("text")

        # Check availability flags
        vtt_available = raw_metadata.get("vtt_available", False) if raw_metadata else False
        markdown_available = (
            raw_metadata.get("markdown_available", False) if raw_metadata else False
        )
        has_word_timestamps = (
            raw_metadata.get("has_word_timestamps", False) if raw_metadata else False
        )
        has_album_art, album_art_url = _check_album_art_availability(doc_id)

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
                has_timestamps=has_word_timestamps,
                has_album_art=has_album_art,
                album_art_url=album_art_url,
            ),
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
                "details": {"message": str(e)},
            },
        )


@router.get(
    "/documents/{doc_id}/markdown",
    summary="Get document markdown",
    description="Download document as markdown with YAML frontmatter and chunk markers",
    responses={
        200: {"description": "Markdown file with chunk markers", "content": {"text/markdown": {}}},
        400: {"description": "Invalid document ID"},
        404: {"description": "Markdown file not found"},
    },
)
async def get_markdown(doc_id: str, include_markers: bool = True):
    """Get document as markdown with frontmatter and chunk markers.

    Args:
        doc_id: Document identifier (SHA-256 hash)
        include_markers: If True, insert chunk markers for bidirectional highlighting

    Returns:
        FileResponse with markdown content

    Raises:
        HTTPException: 404 if markdown not found, 400 if invalid doc_id

    Note:
        Chunk markers are inserted as HTML comments and div wrappers to enable
        bidirectional highlighting between search results and document content.
        Format: <!-- chunk:ID page:N section:"PATH" --> <div>...</div>
    """
    # Validate doc_id
    if not validate_doc_id(doc_id):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid document ID format",
                "code": "INVALID_DOC_ID",
                "details": {"doc_id": doc_id},
            },
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
                "details": {"doc_id": doc_id},
            },
        )

    # Get filename from ChromaDB for the download filename
    try:
        client = get_chroma_client()
        text_data = client._text_collection.get(where={"doc_id": doc_id}, limit=1)

        filename = "unknown.md"
        if text_data.get("metadatas"):
            original_filename = text_data["metadatas"][0].get("filename", "unknown")
            # Remove extension and add .md
            filename = Path(original_filename).stem + ".md"
    except Exception as e:
        logger.warning(f"Failed to get filename from ChromaDB: {e}")
        filename = f"{doc_id}.md"

    # Insert chunk markers if requested
    if include_markers:
        try:
            from src.storage.markdown_chunking import get_chunks_for_document, insert_chunk_markers

            # Read original markdown
            with open(markdown_path, "r", encoding="utf-8") as f:
                original_markdown = f.read()

            # Get chunks from ChromaDB
            chunks = get_chunks_for_document(doc_id, client)

            # Insert markers
            if chunks:
                marked_markdown = insert_chunk_markers(original_markdown, chunks)

                # Write marked markdown to temporary file
                import tempfile

                with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", suffix=".md", delete=False
                ) as temp_file:
                    temp_file.write(marked_markdown)
                    temp_path = temp_file.name

                logger.info(f"Generated markdown with {len(chunks)} chunk markers for {doc_id}")

                # Return temporary file
                return FileResponse(
                    path=temp_path,
                    media_type="text/markdown",
                    filename=filename,
                    headers={
                        "Content-Disposition": f'attachment; filename="{filename}"',
                    },
                )
            else:
                logger.info(f"No chunks found for {doc_id}, returning original markdown")

        except Exception as e:
            logger.warning(f"Failed to insert chunk markers for {doc_id}: {e}", exc_info=True)
            # Fall through to return original markdown

    # Return file with appropriate headers
    return FileResponse(
        path=markdown_path,
        media_type="text/markdown",
        filename=filename,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get(
    "/documents/{doc_id}/vtt",
    summary="Get document VTT captions",
    description="Download VTT caption file for audio documents",
    responses={
        200: {"description": "VTT file", "content": {"text/vtt": {}}},
        400: {"description": "Invalid document ID"},
        404: {"description": "VTT file not found"},
    },
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
                "details": {"doc_id": doc_id},
            },
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
                "details": {
                    "doc_id": doc_id,
                    "message": "VTT captions only available for audio files with word-level timestamps",
                },
            },
        )

    # Get filename from ChromaDB for the download filename
    try:
        client = get_chroma_client()
        text_data = client._text_collection.get(where={"doc_id": doc_id}, limit=1)

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
        },
    )


@router.get(
    "/documents/{doc_id}/audio",
    summary="Get audio file",
    description="Stream audio file for playback",
    responses={
        200: {
            "description": "Audio file",
            "content": {"audio/mpeg": {}, "audio/wav": {}, "audio/mp4": {}},
        },
        400: {"description": "Invalid document ID"},
        404: {"description": "Audio file not found"},
    },
)
async def get_audio(doc_id: str):
    """Stream audio file for playback.

    Args:
        doc_id: Document identifier

    Returns:
        FileResponse with audio data

    Raises:
        HTTPException: 404 if audio not found, 400 if invalid doc_id
    """
    # Validate doc_id
    if not validate_doc_id(doc_id):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid document ID format",
                "code": "INVALID_DOC_ID",
                "details": {"doc_id": doc_id},
            },
        )

    # Get document metadata to find audio filename
    try:
        chroma_client = get_chroma_client()

        # Try text collection first (audio transcripts)
        text_results = chroma_client._text_collection.get(where={"doc_id": doc_id}, limit=1)

        if not text_results["ids"]:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Audio file not found",
                    "code": "AUDIO_NOT_FOUND",
                    "details": {
                        "doc_id": doc_id,
                        "message": "Document not found or is not an audio file",
                    },
                },
            )

        metadata = text_results["metadatas"][0]
        filename = metadata.get("filename") or metadata.get("original_filename")

        if not filename:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Audio filename not found in metadata",
                    "code": "FILENAME_NOT_FOUND",
                    "details": {"doc_id": doc_id},
                },
            )

        # Check for audio file in data/uploads/
        uploads_dir = Path("data/uploads")
        audio_path = uploads_dir / filename

        if not audio_path.exists():
            logger.warning(f"Audio file not found: {audio_path}")
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Audio file not found on disk",
                    "code": "AUDIO_FILE_NOT_FOUND",
                    "details": {"doc_id": doc_id, "filename": filename},
                },
            )

        # Determine MIME type based on extension
        ext = audio_path.suffix.lower()
        mime_types = {
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
        }
        media_type = mime_types.get(ext, "audio/mpeg")

        # Return file with proper headers for streaming
        return FileResponse(
            path=audio_path,
            media_type=media_type,
            headers={
                "Accept-Ranges": "bytes",  # Enable seeking
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving audio for {doc_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "code": "AUDIO_SERVE_ERROR",
                "details": {"doc_id": doc_id, "message": str(e)},
            },
        )


@router.get(
    "/documents/{doc_id}/cover",
    summary="Get album art cover image",
    description="Get album art cover image for audio documents",
    responses={
        200: {"description": "Cover image file", "content": {"image/jpeg": {}, "image/png": {}}},
        400: {"description": "Invalid document ID"},
        404: {"description": "Cover art not found"},
    },
)
async def get_cover(doc_id: str):
    """Get album art cover image for audio documents.

    Args:
        doc_id: Document identifier (SHA-256 hash)

    Returns:
        FileResponse with image data

    Raises:
        HTTPException: 404 if cover not found, 400 if invalid doc_id
    """
    # Validate doc_id
    if not validate_doc_id(doc_id):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid document ID format",
                "code": "INVALID_DOC_ID",
                "details": {"doc_id": doc_id},
            },
        )

    # Check for cover art in data/images/{doc_id}/
    images_dir = Path("data/images") / doc_id

    cover_path = None
    media_type = None

    if images_dir.exists():
        # Try different extensions (JPEG and PNG)
        for ext, mime in [("jpg", "image/jpeg"), ("jpeg", "image/jpeg"), ("png", "image/png")]:
            candidate = images_dir / f"cover.{ext}"
            if candidate.exists():
                cover_path = candidate
                media_type = mime
                break

    if not cover_path:
        logger.info(f"Cover art not found for document: {doc_id}")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Cover art not found",
                "code": "COVER_NOT_FOUND",
                "details": {
                    "doc_id": doc_id,
                    "message": "Album art only available for audio files with embedded cover images",
                },
            },
        )

    # Return file with caching headers (1 year for immutable images)
    return FileResponse(
        path=cover_path,
        media_type=media_type,
        headers={
            "Cache-Control": "max-age=31536000, immutable",  # 1 year
        },
    )


def _validate_image_request(doc_id: str, filename: str) -> None:
    """Validate document ID and filename for image requests.

    Args:
        doc_id: Document identifier to validate
        filename: Image filename to validate

    Raises:
        HTTPException: 403 if validation fails
    """
    if not validate_doc_id(doc_id):
        logger.warning(f"Invalid doc_id format: {doc_id}")
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Invalid document ID format",
                "code": "INVALID_DOC_ID",
                "details": {"doc_id": doc_id},
            },
        )

    if not validate_filename(filename):
        logger.warning(f"Invalid filename format: {filename}")
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Invalid filename format",
                "code": "INVALID_FILENAME",
                "details": {"filename": filename},
            },
        )


def _find_image_in_directories(doc_id: str, filename: str) -> Optional[Path]:
    """Search for image in multiple directories with security checks.

    Args:
        doc_id: Document identifier
        filename: Image filename to find

    Returns:
        Path to image file or None if not found
    """
    search_dirs = [
        Path(PAGE_IMAGE_DIR) / doc_id,  # data/page_images/{doc_id}/
        Path("data/images") / doc_id,  # data/images/{doc_id}/
    ]

    for search_dir in search_dirs:
        candidate_path = search_dir / filename

        try:
            resolved_path = candidate_path.resolve()
            resolved_dir = search_dir.resolve()

            # Security: Prevent path traversal
            if not str(resolved_path).startswith(str(resolved_dir)):
                logger.error(f"Path traversal attempt: {resolved_path}")
                continue

            if resolved_path.exists():
                return resolved_path

        except Exception as e:
            logger.debug(f"Path resolution failed for {search_dir}: {e}")
            continue

    return None


def _get_image_content_type(filename: str) -> str:
    """Determine content type from filename extension.

    Args:
        filename: Image filename

    Returns:
        MIME type string
    """
    if filename.endswith(".png"):
        return "image/png"
    elif filename.endswith(".jpg") or filename.endswith(".jpeg"):
        return "image/jpeg"
    elif filename.endswith(".svg"):
        return "image/svg+xml"
    else:
        return "application/octet-stream"


@router.get(
    "/images/{doc_id}/{filename}",
    summary="Serve page image",
    description="Serve page image, thumbnail, or cover art file (including SVG placeholders)",
    responses={
        200: {
            "description": "Image file",
            "content": {"image/png": {}, "image/jpeg": {}, "image/svg+xml": {}},
        },
        403: {"description": "Invalid filename or path traversal attempt"},
        404: {"description": "Image file not found"},
    },
)
async def get_image(doc_id: str, filename: str):
    """Serve page image, thumbnail, or cover art files.

    Args:
        doc_id: Document identifier
        filename: Image filename (e.g., page001.png, page001_thumb.jpg, cover.svg)

    Returns:
        FileResponse with image data

    Raises:
        HTTPException: 403 for invalid paths, 404 if file not found
    """
    # Validate request parameters
    _validate_image_request(doc_id, filename)

    # Find image in directories
    image_path = _find_image_in_directories(doc_id, filename)

    if not image_path:
        logger.info(f"Image not found in any directory: {filename} for doc_id {doc_id}")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Image file not found",
                "code": "IMAGE_NOT_FOUND",
                "details": {"doc_id": doc_id, "filename": filename},
            },
        )

    # Determine content type and return file
    media_type = _get_image_content_type(filename)

    return FileResponse(
        path=image_path,
        media_type=media_type,
        headers={
            "Cache-Control": "max-age=86400",  # 24 hours
        },
    )

"""
Structure and chunk metadata API endpoints.

Provides REST API endpoints for retrieving document structure metadata and
text chunk context information from ChromaDB storage.

Provider: api-agent (Wave 7: Structure API Builder)
Consumers: ui-agent
Contract: integration-contracts/docling-structure-spec.md
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from tkr_docusearch.storage import ChromaClient
from tkr_docusearch.storage.compression import decompress_structure_metadata
from tkr_docusearch.storage.metadata_schema import DocumentStructure

logger = logging.getLogger(__name__)

# Create API router with /api prefix for frontend compatibility
router = APIRouter(prefix="/api", tags=["structure"])

# Validation patterns (security)
DOC_ID_PATTERN = re.compile(r"^[a-zA-Z0-9\-]{8,64}$")
CHUNK_ID_PATTERN = re.compile(r"^[a-zA-Z0-9\-]{8,64}-chunk\d{4}$")


# ============================================================================
# Request/Response Models
# ============================================================================


class BoundingBox(BaseModel):
    """Bounding box coordinates.

    Format: [left, bottom, right, top] in PDF coordinate system
    Units: Points (1/72 inch)
    Origin: Bottom-left corner of page
    See: integration-contracts/docling-structure-spec.md
    """

    left: float = Field(..., description="Left edge (x1)")
    bottom: float = Field(..., description="Bottom edge (y1)")
    right: float = Field(..., description="Right edge (x2)")
    top: float = Field(..., description="Top edge (y2)")

    @classmethod
    def from_tuple(cls, bbox: tuple) -> "BoundingBox":
        """Create from tuple format [left, bottom, right, top]."""
        if bbox is None or len(bbox) != 4:
            raise ValueError("Invalid bbox format")
        return cls(left=bbox[0], bottom=bbox[1], right=bbox[2], top=bbox[3])


class HeadingInfo(BaseModel):
    """Document heading information."""

    text: str = Field(..., description="Heading text content")
    level: str = Field(..., description="Heading level (TITLE, SECTION_HEADER, etc.)")
    page: int = Field(..., description="Page number where heading appears")
    section_path: str = Field(..., description="Hierarchical section path")
    bbox: Optional[BoundingBox] = Field(None, description="Bounding box if available")


class TableInfo(BaseModel):
    """Document table information."""

    page: int = Field(..., description="Page number where table appears")
    caption: Optional[str] = Field(None, description="Table caption if available")
    rows: int = Field(..., description="Number of rows")
    cols: int = Field(..., description="Number of columns")
    has_header: bool = Field(..., description="Whether table has header row")
    table_id: str = Field(..., description="Unique table identifier")
    bbox: Optional[BoundingBox] = Field(None, description="Bounding box if available")


class PictureInfo(BaseModel):
    """Document picture information."""

    page: int = Field(..., description="Page number where picture appears")
    type: str = Field(..., description="Picture type (chart, diagram, photo, etc.)")
    caption: Optional[str] = Field(None, description="Picture caption if available")
    confidence: float = Field(..., description="Classification confidence (0-1)")
    picture_id: str = Field(..., description="Unique picture identifier")
    bbox: Optional[BoundingBox] = Field(None, description="Bounding box if available")


class CodeBlockInfo(BaseModel):
    """Code block information."""

    page: int = Field(..., description="Page number where code appears")
    language: Optional[str] = Field(None, description="Detected programming language")
    lines: int = Field(..., description="Number of lines")
    bbox: Optional[BoundingBox] = Field(None, description="Bounding box if available")


class FormulaInfo(BaseModel):
    """Formula information."""

    page: int = Field(..., description="Page number where formula appears")
    latex: Optional[str] = Field(None, description="LaTeX representation")
    bbox: Optional[BoundingBox] = Field(None, description="Bounding box if available")


class StructureSummary(BaseModel):
    """Document structure summary statistics."""

    total_sections: int = Field(..., description="Total number of sections")
    max_depth: int = Field(..., description="Maximum heading nesting depth")
    has_toc: bool = Field(..., description="Whether document has table of contents")


class CoordinateSystemInfo(BaseModel):
    """Coordinate system metadata for bounding boxes."""

    format: str = Field("[left, bottom, right, top]", description="Bounding box coordinate format")
    origin: str = Field("bottom-left", description="Coordinate system origin")
    units: str = Field("points", description="Coordinate units (1 point = 1/72 inch)")
    reference: str = Field(
        "integration-contracts/docling-structure-spec.md",
        description="Full specification reference",
    )


class PageStructureResponse(BaseModel):
    """Response model for GET /documents/{doc_id}/pages/{page}/structure."""

    doc_id: str = Field(..., description="Document identifier")
    page: int = Field(..., description="Page number (1-indexed)")
    has_structure: bool = Field(..., description="True if structure metadata exists")
    headings: List[HeadingInfo] = Field(default_factory=list, description="Headings on this page")
    tables: List[TableInfo] = Field(default_factory=list, description="Tables on this page")
    pictures: List[PictureInfo] = Field(default_factory=list, description="Pictures on this page")
    code_blocks: List[CodeBlockInfo] = Field(
        default_factory=list, description="Code blocks on this page"
    )
    formulas: List[FormulaInfo] = Field(default_factory=list, description="Formulas on this page")
    summary: Optional[StructureSummary] = Field(
        None, description="Summary statistics (if structure exists)"
    )
    coordinate_system: CoordinateSystemInfo = Field(
        default_factory=CoordinateSystemInfo, description="Coordinate system metadata"
    )


class ChunkContextResponse(BaseModel):
    """Response model for GET /documents/{doc_id}/chunks/{chunk_id}."""

    chunk_id: str = Field(..., description="Chunk identifier")
    doc_id: str = Field(..., description="Document identifier")
    text_content: str = Field(..., description="Full text content of chunk")
    parent_heading: Optional[str] = Field(None, description="Immediate parent heading text")
    parent_heading_level: Optional[int] = Field(
        None, description="Parent heading level (0=title, 1=section, etc.)"
    )
    section_path: str = Field(
        "", description="Breadcrumb of headings (e.g., 'Intro > Methods > Data')"
    )
    element_type: str = Field("text", description="Type of element (text, list_item, etc.)")
    related_tables: List[str] = Field(
        default_factory=list, description="IDs of tables mentioned in chunk"
    )
    related_pictures: List[str] = Field(
        default_factory=list, description="IDs of pictures mentioned in chunk"
    )
    page_nums: List[int] = Field(default_factory=list, description="Pages spanned by chunk")
    is_page_boundary: bool = Field(False, description="True if chunk crosses page boundary")
    bbox: Optional[BoundingBox] = Field(
        None, description="Bounding box if available (text chunks may not have bboxes)"
    )


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


def validate_chunk_id(chunk_id: str) -> bool:
    """Validate chunk_id format.

    Args:
        chunk_id: Chunk identifier to validate (format: {doc_id}-chunk{NNNN})

    Returns:
        True if valid, False otherwise
    """
    return bool(CHUNK_ID_PATTERN.match(chunk_id))


def parse_chunk_id(chunk_id: str) -> tuple[str, int]:
    """Parse chunk_id into doc_id and chunk number.

    Args:
        chunk_id: Chunk identifier (format: {doc_id}-chunk{NNNN})

    Returns:
        Tuple of (doc_id, chunk_number)

    Raises:
        ValueError: If chunk_id format is invalid
    """
    match = re.match(r"^([a-zA-Z0-9\-]{8,64})-chunk(\d{4})$", chunk_id)
    if not match:
        raise ValueError(f"Invalid chunk_id format: {chunk_id}")

    doc_id = match.group(1)
    chunk_num = int(match.group(2))

    return doc_id, chunk_num


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


def parse_json_field(field_value: Any) -> Any:
    """Parse JSON string field from ChromaDB metadata.

    ChromaDB stores lists/dicts as JSON strings. This helper parses them back.

    Args:
        field_value: Field value (may be JSON string or primitive)

    Returns:
        Parsed value (list/dict if JSON string, otherwise original value)
    """
    if isinstance(field_value, str) and field_value.startswith(("[", "{")):
        try:
            return json.loads(field_value)
        except json.JSONDecodeError:
            return field_value
    return field_value


# ============================================================================
# API Endpoints
# ============================================================================


@router.get(
    "/documents/{doc_id}/pages/{page}/structure",
    response_model=PageStructureResponse,
    summary="Get page structure metadata",
    description="Get document structure metadata for a specific page (headings, tables, pictures, etc.)",
)
async def get_page_structure(doc_id: str, page: int):
    """Get document structure metadata for a specific page.

    Args:
        doc_id: Document identifier (SHA-256 hash)
        page: Page number (1-indexed)

    Returns:
        PageStructureResponse with structure elements on this page

    Raises:
        HTTPException: 400 if invalid doc_id/page, 404 if document/page not found
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

    # Validate page number
    if page < 1:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid page number (must be >= 1)",
                "code": "INVALID_PAGE_NUMBER",
                "details": {"page": page},
            },
        )

    try:
        client = get_chroma_client()

        # Query visual collection for this doc_id and page using embedding ID
        # Format: {doc_id}-page{page:03d}
        embedding_id = f"{doc_id}-page{page:03d}"
        visual_data = client._visual_collection.get(ids=[embedding_id], include=["metadatas"])

        # Check if page exists
        if not visual_data["ids"]:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Page not found",
                    "code": "PAGE_NOT_FOUND",
                    "details": {"doc_id": doc_id, "page": page},
                },
            )

        metadata = visual_data["metadatas"][0]

        # Check if structure metadata exists
        has_structure = metadata.get("has_structure", False)

        if not has_structure:
            # Return empty structure
            return PageStructureResponse(
                doc_id=doc_id,
                page=page,
                has_structure=False,
                coordinate_system=CoordinateSystemInfo(),
            )

        # Decompress and parse structure metadata
        compressed_structure = metadata.get("structure")
        if not compressed_structure:
            # has_structure=True but no structure data (shouldn't happen)
            logger.warning(f"has_structure=True but no structure data for {doc_id} page {page}")
            return PageStructureResponse(
                doc_id=doc_id,
                page=page,
                has_structure=False,
                coordinate_system=CoordinateSystemInfo(),
            )

        # Decompress structure
        structure_dict = decompress_structure_metadata(compressed_structure)
        structure = DocumentStructure.from_dict(structure_dict)

        # Filter elements for this page
        page_headings = [h for h in structure.headings if h.page_num == page]
        page_tables = [t for t in structure.tables if t.page_num == page]
        page_pictures = [p for p in structure.pictures if p.page_num == page]
        page_code_blocks = [c for c in structure.code_blocks if c.page_num == page]
        page_formulas = [f for f in structure.formulas if f.page_num == page]

        # Convert to response models
        headings = [
            HeadingInfo(
                text=h.text,
                level=h.level.name,
                page=h.page_num,
                section_path=h.section_path,
                bbox=BoundingBox.from_tuple(h.bbox) if h.bbox else None,
            )
            for h in page_headings
        ]

        tables = [
            TableInfo(
                page=t.page_num,
                caption=t.caption,
                rows=t.num_rows,
                cols=t.num_cols,
                has_header=t.has_header,
                table_id=t.table_id,
                bbox=BoundingBox.from_tuple(t.bbox) if t.bbox else None,
            )
            for t in page_tables
        ]

        pictures = [
            PictureInfo(
                page=p.page_num,
                type=p.picture_type.value,
                caption=p.caption,
                confidence=p.confidence,
                picture_id=p.picture_id,
                bbox=BoundingBox.from_tuple(p.bbox) if p.bbox else None,
            )
            for p in page_pictures
        ]

        code_blocks = [
            CodeBlockInfo(
                page=c.page_num,
                language=c.language,
                lines=c.num_lines,
                bbox=BoundingBox.from_tuple(c.bbox) if c.bbox else None,
            )
            for c in page_code_blocks
        ]

        formulas = [
            FormulaInfo(
                page=f.page_num,
                latex=f.latex,
                bbox=BoundingBox.from_tuple(f.bbox) if f.bbox else None,
            )
            for f in page_formulas
        ]

        # Create summary
        summary = StructureSummary(
            total_sections=structure.total_sections,
            max_depth=structure.max_heading_depth,
            has_toc=structure.has_table_of_contents,
        )

        return PageStructureResponse(
            doc_id=doc_id,
            page=page,
            has_structure=True,
            headings=headings,
            tables=tables,
            pictures=pictures,
            code_blocks=code_blocks,
            formulas=formulas,
            summary=summary,
            coordinate_system=CoordinateSystemInfo(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting structure for {doc_id} page {page}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to retrieve page structure",
                "code": "DATABASE_ERROR",
                "details": {"message": str(e)},
            },
        )


@router.get(
    "/documents/{doc_id}/chunks/{chunk_id}",
    response_model=ChunkContextResponse,
    summary="Get chunk context metadata",
    description="Get contextual metadata for a specific text chunk (parent heading, section path, related elements)",
)
async def get_chunk_context(doc_id: str, chunk_id: str):
    """Get contextual metadata for a specific text chunk.

    Args:
        doc_id: Document identifier (SHA-256 hash)
        chunk_id: Chunk identifier (format: {doc_id}-chunk{NNNN})

    Returns:
        ChunkContextResponse with chunk context and related elements

    Raises:
        HTTPException: 400 if invalid IDs, 404 if chunk not found
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

    # Validate and parse chunk_id
    # Check if chunk_id is already in full format or just the chunk number
    if validate_chunk_id(chunk_id):
        # chunk_id is already in full format: {doc_id}-chunk{NNNN}
        full_chunk_id = chunk_id
    elif chunk_id.isdigit() and len(chunk_id) == 4:
        # chunk_id is just the number (e.g., "0001")
        full_chunk_id = f"{doc_id}-chunk{chunk_id}"
        if not validate_chunk_id(full_chunk_id):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid chunk ID format",
                    "code": "INVALID_CHUNK_ID",
                    "details": {"chunk_id": chunk_id, "expected_format": "{doc_id}-chunk{NNNN}"},
                },
            )
    else:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid chunk ID format",
                "code": "INVALID_CHUNK_ID",
                "details": {
                    "chunk_id": chunk_id,
                    "expected_format": "NNNN or {doc_id}-chunk{NNNN}",
                },
            },
        )

    try:
        # Parse chunk_id to extract doc_id and chunk number
        parsed_doc_id, chunk_num = parse_chunk_id(full_chunk_id)

        # Verify doc_id matches
        if parsed_doc_id != doc_id:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Chunk ID does not match document ID",
                    "code": "CHUNK_DOC_MISMATCH",
                    "details": {
                        "doc_id": doc_id,
                        "chunk_doc_id": parsed_doc_id,
                        "chunk_id": full_chunk_id,
                    },
                },
            )

        client = get_chroma_client()

        # Query text collection by chunk_id
        text_data = client._text_collection.get(ids=[full_chunk_id], include=["metadatas"])

        # Check if chunk exists
        if not text_data["ids"]:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Chunk not found",
                    "code": "CHUNK_NOT_FOUND",
                    "details": {"doc_id": doc_id, "chunk_id": full_chunk_id},
                },
            )

        metadata = text_data["metadatas"][0]

        # Extract basic fields
        text_content = metadata.get("full_text") or metadata.get("text_preview", "")
        parent_heading = metadata.get("parent_heading")
        parent_heading_level = metadata.get("parent_heading_level")
        section_path = metadata.get("section_path", "")
        element_type = metadata.get("element_type", "text")
        is_page_boundary = metadata.get("is_page_boundary", False)

        # Parse JSON array fields (ChromaDB stores lists as JSON strings)
        related_tables = parse_json_field(metadata.get("related_tables", []))
        if not isinstance(related_tables, list):
            related_tables = []

        related_pictures = parse_json_field(metadata.get("related_pictures", []))
        if not isinstance(related_pictures, list):
            related_pictures = []

        page_nums_raw = metadata.get("page_nums")
        if page_nums_raw:
            page_nums = parse_json_field(page_nums_raw)
            if not isinstance(page_nums, list):
                page_nums = []
        else:
            # Fallback to single page field
            page = metadata.get("page")
            page_nums = [page] if page is not None else []

        # Check for bbox (text chunks may not have bboxes)
        bbox = metadata.get("bbox")
        bbox_obj = None
        if bbox:
            if isinstance(bbox, str):
                bbox = parse_json_field(bbox)
            if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
                bbox_obj = BoundingBox.from_tuple(bbox)

        return ChunkContextResponse(
            chunk_id=full_chunk_id,
            doc_id=doc_id,
            text_content=text_content,
            parent_heading=parent_heading,
            parent_heading_level=parent_heading_level,
            section_path=section_path,
            element_type=element_type,
            related_tables=related_tables,
            related_pictures=related_pictures,
            page_nums=page_nums,
            is_page_boundary=is_page_boundary,
            bbox=bbox_obj,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chunk {chunk_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to retrieve chunk context",
                "code": "DATABASE_ERROR",
                "details": {"message": str(e)},
            },
        )

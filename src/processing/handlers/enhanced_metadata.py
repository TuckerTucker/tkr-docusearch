"""
Enhanced metadata preparation for document processing.

This module provides helper functions to prepare enhanced metadata for storage
in ChromaDB collections. It handles structure compression, validation, and
chunk context formatting according to the ChromaDB metadata schema v1.0.
"""

import json
import logging
from typing import Any, Dict, Optional

from tkr_docusearch.storage.compression import compress_structure_metadata, sanitize_metadata_for_chroma
from tkr_docusearch.storage.metadata_schema import (
    ChunkContext,
    DocumentStructure,
    validate_chunk_context,
    validate_document_structure,
    validate_metadata_size,
)

logger = logging.getLogger(__name__)


def prepare_enhanced_visual_metadata(
    base_metadata: Dict[str, Any],
    structure: Optional[DocumentStructure],
    image_width: Optional[int],
    image_height: Optional[int],
) -> Dict[str, Any]:
    """
    Prepare enhanced visual metadata for ChromaDB storage.

    Adds document structure information to base metadata according to
    ChromaDB metadata schema v1.0. Structure is compressed using gzip+base64
    for efficient storage.

    Args:
        base_metadata: Base metadata dictionary (filename, page, etc.)
        structure: DocumentStructure object from Docling parsing
        image_width: Original image width in pixels (for bbox coordinate system)
        image_height: Original image height in pixels (for bbox coordinate system)

    Returns:
        Enhanced metadata dictionary ready for ChromaDB storage

    Raises:
        ValueError: If structure is invalid or metadata exceeds size limits

    Example:
        >>> base_meta = {"filename": "report.pdf", "page": 1, "doc_id": "abc123"}
        >>> structure = DocumentStructure(headings=[...], tables=[...])
        >>> enhanced = prepare_enhanced_visual_metadata(base_meta, structure, 1700, 2200)
        >>> enhanced["has_structure"]
        True
    """
    # Start with base metadata
    enhanced = base_metadata.copy()

    # If no structure provided, set has_structure=False and return
    if structure is None:
        enhanced["has_structure"] = False
        return sanitize_metadata_for_chroma(enhanced)

    # Validate structure before compression
    try:
        validate_document_structure(structure)
    except AssertionError as e:
        logger.warning(f"Invalid document structure: {e}")
        enhanced["has_structure"] = False
        return sanitize_metadata_for_chroma(enhanced)

    # Add structure availability flag
    enhanced["has_structure"] = True

    # Add structure summary (for quick queries without decompression)
    enhanced["num_headings"] = len(structure.headings)
    enhanced["num_tables"] = len(structure.tables)
    enhanced["num_pictures"] = len(structure.pictures)
    enhanced["max_heading_depth"] = structure.max_heading_depth

    # Add coordinate system metadata
    if image_width is not None:
        enhanced["image_width"] = image_width
    if image_height is not None:
        enhanced["image_height"] = image_height

    # Compress and store full structure
    try:
        structure_dict = structure.to_dict()
        compressed_structure = compress_structure_metadata(structure_dict)
        enhanced["structure"] = compressed_structure

        logger.debug(
            f"Compressed structure: {len(compressed_structure)} bytes "
            f"(headings: {len(structure.headings)}, "
            f"tables: {len(structure.tables)}, "
            f"pictures: {len(structure.pictures)})"
        )
    except Exception as e:
        logger.error(f"Failed to compress structure: {e}")
        # Fall back to non-enhanced mode
        enhanced["has_structure"] = False
        return sanitize_metadata_for_chroma(enhanced)

    # Validate metadata size (should be <50KB)
    try:
        validate_metadata_size(enhanced, max_size_kb=50)
    except ValueError as e:
        logger.warning(f"Enhanced metadata too large: {e}")
        # Remove structure and fall back to summary only
        del enhanced["structure"]
        logger.info("Removed compressed structure, keeping summary fields only")

    # Sanitize for ChromaDB (convert lists/dicts to JSON strings)
    return sanitize_metadata_for_chroma(enhanced)


def prepare_enhanced_text_metadata(
    base_metadata: Dict[str, Any],
    chunk_context: Optional[ChunkContext],
) -> Dict[str, Any]:
    """
    Prepare enhanced text metadata for ChromaDB storage.

    Adds chunk context information to base metadata according to
    ChromaDB metadata schema v1.0. Context includes parent heading,
    section path, element type, and related elements.

    Args:
        base_metadata: Base metadata dictionary (chunk_id, text, page, etc.)
        chunk_context: ChunkContext object from smart chunking

    Returns:
        Enhanced metadata dictionary ready for ChromaDB storage

    Raises:
        ValueError: If chunk context is invalid

    Example:
        >>> base_meta = {"filename": "report.pdf", "chunk_id": "abc-chunk001", "page": 1}
        >>> context = ChunkContext(
        ...     parent_heading="Introduction",
        ...     section_path="Report > Introduction",
        ...     element_type="text",
        ...     page_nums=[1]
        ... )
        >>> enhanced = prepare_enhanced_text_metadata(base_meta, context)
        >>> enhanced["has_context"]
        True
    """
    # Start with base metadata
    enhanced = base_metadata.copy()

    # If no context provided, set has_context=False and return
    if chunk_context is None:
        enhanced["has_context"] = False
        return sanitize_metadata_for_chroma(enhanced)

    # Validate chunk context
    try:
        validate_chunk_context(chunk_context)
    except AssertionError as e:
        logger.warning(f"Invalid chunk context: {e}")
        enhanced["has_context"] = False
        return sanitize_metadata_for_chroma(enhanced)

    # Add context availability flag
    enhanced["has_context"] = True

    # Add structural context (flat fields for ChromaDB filtering)
    enhanced["parent_heading"] = chunk_context.parent_heading
    enhanced["parent_heading_level"] = chunk_context.parent_heading_level
    enhanced["section_path"] = chunk_context.section_path
    enhanced["element_type"] = chunk_context.element_type
    enhanced["is_page_boundary"] = chunk_context.is_page_boundary

    # Store full context as JSON string for visual necessity and multi-modal decisions
    enhanced["chunk_context_json"] = json.dumps(chunk_context.to_dict())

    # Add related elements (stored as JSON strings - ChromaDB limitation)
    enhanced["related_tables"] = json.dumps(chunk_context.related_tables)
    enhanced["related_pictures"] = json.dumps(chunk_context.related_pictures)

    # Add page range (stored as JSON string)
    enhanced["page_nums"] = json.dumps(chunk_context.page_nums)

    # Add bounding box if available (stored as JSON string)
    # Note: bbox not in current ChunkContext schema, but prepared for future
    # enhanced["bbox"] = json.dumps(chunk_context.bbox) if chunk_context.bbox else None

    logger.debug(
        f"Prepared enhanced text metadata: "
        f"section_path='{chunk_context.section_path}', "
        f"element_type={chunk_context.element_type}, "
        f"pages={chunk_context.page_nums}"
    )

    # Validate metadata size (should be <50KB)
    try:
        validate_metadata_size(enhanced, max_size_kb=50)
    except ValueError as e:
        logger.warning(f"Enhanced text metadata too large: {e}")
        # This should never happen for text chunks, but handle gracefully
        enhanced["has_context"] = False
        return sanitize_metadata_for_chroma(enhanced)

    # Sanitize for ChromaDB (convert any remaining lists/dicts to JSON strings)
    return sanitize_metadata_for_chroma(enhanced)


def build_chunk_context_from_chunking_results(
    chunk: Any,
    parent_heading: Optional[str] = None,
    parent_heading_level: Optional[int] = None,
    section_path: str = "",
) -> Optional[ChunkContext]:
    """
    Build ChunkContext from chunking results.

    Helper function to construct ChunkContext from chunking pipeline outputs.
    This is a convenience function for the text embedding handler.

    Args:
        chunk: TextChunk object with text content and context
        parent_heading: Optional parent heading text
        parent_heading_level: Optional parent heading level
        section_path: Optional section path breadcrumb

    Returns:
        ChunkContext object or None if context not available

    Example:
        >>> from src.processing.types import TextChunk
        >>> chunk = TextChunk(chunk_id="abc-001", text="Some text", page_num=1)
        >>> context = build_chunk_context_from_chunking_results(
        ...     chunk, parent_heading="Introduction", section_path="Report > Introduction"
        ... )
        >>> context.parent_heading
        'Introduction'
    """
    # If chunk has context attribute, use it
    if hasattr(chunk, "context") and chunk.context is not None:
        return chunk.context

    # Otherwise, build basic context from parameters
    if parent_heading or section_path:
        return ChunkContext(
            parent_heading=parent_heading,
            parent_heading_level=parent_heading_level,
            section_path=section_path,
            element_type="text",  # Default to text
            page_nums=[chunk.page_num] if hasattr(chunk, "page_num") else [],
            is_page_boundary=False,  # Default to False
        )

    # No context available
    return None

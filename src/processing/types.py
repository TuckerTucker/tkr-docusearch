"""
Shared type definitions for document processing.

This module contains dataclasses used across processing modules to avoid
circular imports.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from PIL import Image

from src.storage.metadata_schema import ChunkContext


@dataclass
class Page:
    """Represents a parsed document page.

    Attributes:
        page_num: Page number (1-indexed)
        image: Rendered page image
        width: Image width in pixels
        height: Image height in pixels
        text: Extracted page text
        image_path: Path to saved full-resolution page image (Wave 1)
        thumb_path: Path to saved thumbnail image (Wave 1)
    """

    page_num: int
    image: Image.Image
    width: int
    height: int
    text: str
    image_path: Optional[str] = None
    thumb_path: Optional[str] = None


@dataclass
class TextChunk:
    """Represents a text chunk from a document.

    Attributes:
        chunk_id: Unique chunk identifier
        page_num: Source page number
        text: Chunk text content
        start_offset: Character offset in page
        end_offset: Character offset in page
        word_count: Approximate word count
        context: Optional chunk context metadata (enhanced mode)
        start_time: Optional start time in seconds (audio only)
        end_time: Optional end time in seconds (audio only)
    """

    chunk_id: str
    page_num: int
    text: str
    start_offset: int
    end_offset: int
    word_count: int
    context: Optional[ChunkContext] = None
    start_time: Optional[float] = None  # Seconds from start (audio only)
    end_time: Optional[float] = None    # Seconds from start (audio only)


@dataclass
class ParsedDocument:
    """Represents a fully parsed document.

    Attributes:
        filename: Original filename
        doc_id: Unique identifier
        num_pages: Total page count
        pages: List of Page objects
        text_chunks: List of TextChunk objects
        metadata: Document-level metadata
    """

    filename: str
    doc_id: str
    num_pages: int
    pages: List[Page]
    text_chunks: List[TextChunk]
    metadata: Dict[str, Any]

"""
Document parsing using Docling.

This module provides basic document parsing functionality.
For Wave 2, this is a simplified implementation that can be enhanced
with full Docling integration in future waves.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
from PIL import Image
import uuid

logger = logging.getLogger(__name__)


@dataclass
class Page:
    """Represents a parsed document page.

    Attributes:
        page_num: Page number (1-indexed)
        image: Rendered page image
        width: Image width in pixels
        height: Image height in pixels
        text: Extracted page text
    """

    page_num: int
    image: Image.Image
    width: int
    height: int
    text: str


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
    """

    chunk_id: str
    page_num: int
    text: str
    start_offset: int
    end_offset: int
    word_count: int


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


class ParsingError(Exception):
    """Document parsing error."""

    pass


def docling_to_pages(result) -> List[Page]:
    """Convert Docling ConversionResult to Page objects.

    This adapter function bridges Docling's output format with our internal
    Page representation. It handles PDFs with full image rendering and provides
    text extraction for all formats.

    Args:
        result: Docling ConversionResult from DocumentConverter.convert()

    Returns:
        List of Page objects with images and text

    Notes:
        - For PDFs: Uses result.pages[i].get_image() for PIL images
        - For DOCX/PPTX: Falls back to text-only (images will be None)
        - Text is extracted from result.document for each page
    """
    from docling.datamodel.document import ConversionResult

    pages = []
    doc = result.document

    # Check if we have physical pages with images (PDFs)
    if result.pages and len(result.pages) > 0:
        logger.info(f"Processing {len(result.pages)} pages from Docling result")

        # PDF format - has result.pages with images
        for idx, page in enumerate(result.pages):
            try:
                # Get PIL image
                img = page.get_image()

                if img is None:
                    logger.warning(f"Page {idx+1} has no image, skipping")
                    continue

                # result.pages is 0-indexed, but we want 1-indexed page numbers
                page_num = idx + 1

                # Extract text for this specific page
                page_text = _extract_page_text(doc, page_num)

                pages.append(Page(
                    page_num=page_num,
                    image=img,
                    width=img.size[0],
                    height=img.size[1],
                    text=page_text
                ))

                logger.debug(f"Converted page {page_num}: {img.size[0]}x{img.size[1]}, {len(page_text)} chars")

            except Exception as e:
                logger.error(f"Failed to convert page {idx+1}: {e}")
                continue

    elif doc.pages and len(doc.pages) > 0:
        # PPTX format - has doc.pages but no images
        logger.info(f"Processing {len(doc.pages)} pages from document (no images)")

        for page_num in sorted(doc.pages.keys()):
            try:
                page_text = _extract_page_text(doc, page_num)

                # Create blank image as placeholder
                # Note: This will be replaced by proper rendering in future enhancement
                img = Image.new('RGB', (1024, 1024), color='white')

                pages.append(Page(
                    page_num=page_num,
                    image=img,
                    width=1024,
                    height=1024,
                    text=page_text
                ))

                logger.debug(f"Converted page {page_num} (text-only): {len(page_text)} chars")

            except Exception as e:
                logger.error(f"Failed to convert page {page_num}: {e}")
                continue

    else:
        # DOCX format - no page concept, treat as single page
        logger.info("Processing document without pages (DOCX)")

        # Get all text
        text = doc.export_to_text() if hasattr(doc, 'export_to_text') else ""

        # Create single page
        img = Image.new('RGB', (1024, 1024), color='white')

        pages.append(Page(
            page_num=1,
            image=img,
            width=1024,
            height=1024,
            text=text
        ))

        logger.debug(f"Converted document as single page: {len(text)} chars")

    logger.info(f"Converted {len(pages)} pages total")
    return pages


def _extract_page_text(doc, page_num: int) -> str:
    """Extract text from a specific page in DoclingDocument.

    Args:
        doc: DoclingDocument
        page_num: Page number (1-indexed)

    Returns:
        Concatenated text from all elements on the page
    """
    text_parts = []

    # Iterate through all text items
    if hasattr(doc, 'texts') and doc.texts:
        for text_item in doc.texts:
            # Check if this text belongs to the page
            if hasattr(text_item, 'prov') and text_item.prov:
                # prov is a list of ProvenanceItem objects
                for prov in text_item.prov:
                    if hasattr(prov, 'page_no') and prov.page_no == page_num:
                        # Add the text
                        if hasattr(text_item, 'text') and text_item.text:
                            text_parts.append(text_item.text)
                        break  # Found it on this page, no need to check other provs

    return "\n".join(text_parts)


class DoclingParser:
    """Basic document parser for Wave 2.

    This is a simplified implementation for MVP development.
    Future enhancements can integrate full Docling functionality.
    """

    def __init__(self, render_dpi: int = 150):
        """Initialize parser.

        Args:
            render_dpi: DPI for page rendering
        """
        self.render_dpi = render_dpi
        logger.info(f"Initialized DoclingParser (dpi={render_dpi})")

    def parse_document(
        self,
        file_path: str,
        chunk_size_words: int = 250,
        chunk_overlap_words: int = 50
    ) -> ParsedDocument:
        """Parse document and extract pages and text.

        Args:
            file_path: Path to document file
            chunk_size_words: Average words per chunk
            chunk_overlap_words: Word overlap between chunks

        Returns:
            ParsedDocument with pages and chunks

        Raises:
            ParsingError: If parsing fails
            FileNotFoundError: If file doesn't exist
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        filename = path.name
        doc_id = str(uuid.uuid4())
        ext = path.suffix.lower()

        logger.info(f"Parsing document: {filename} (id={doc_id})")

        try:
            # Parse with Docling (supports PDF, DOCX, PPTX)
            pages, metadata = self._parse_with_docling(file_path)

            # Generate text chunks
            text_chunks = self._chunk_text(
                pages,
                doc_id,
                chunk_size_words,
                chunk_overlap_words
            )

            parsed_doc = ParsedDocument(
                filename=filename,
                doc_id=doc_id,
                num_pages=len(pages),
                pages=pages,
                text_chunks=text_chunks,
                metadata=metadata
            )

            logger.info(
                f"Parsed {filename}: {len(pages)} pages, "
                f"{len(text_chunks)} chunks"
            )

            return parsed_doc

        except Exception as e:
            logger.error(f"Failed to parse {filename}: {e}")
            raise ParsingError(f"Parsing failed: {e}") from e

    def _parse_with_docling(self, file_path: str) -> tuple:
        """Parse document using Docling.

        Args:
            file_path: Path to document file (PDF, DOCX, or PPTX)

        Returns:
            Tuple of (pages, metadata)

        Raises:
            ParsingError: If Docling parsing fails
        """
        try:
            from docling.document_converter import DocumentConverter, PdfFormatOption
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions

            # Configure PDF rendering with images
            pipeline_options = PdfPipelineOptions()
            pipeline_options.generate_page_images = True
            pipeline_options.generate_picture_images = True

            converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )

            logger.info(f"Converting document with Docling: {file_path}")
            result = converter.convert(file_path)

            # Use adapter to convert to Page objects
            pages = docling_to_pages(result)

            # Extract metadata from DoclingDocument
            doc = result.document
            metadata = {
                "title": doc.name if hasattr(doc, 'name') else "",
                "author": "",  # Docling doesn't expose author in current version
                "created": "",
                "format": Path(file_path).suffix.lower()[1:],  # Remove leading dot
                "num_pages": len(pages)
            }

            # Try to extract origin metadata if available
            if hasattr(doc, 'origin') and doc.origin:
                origin = doc.origin
                if hasattr(origin, 'filename'):
                    metadata["original_filename"] = origin.filename
                if hasattr(origin, 'mimetype'):
                    metadata["mimetype"] = origin.mimetype

            logger.info(f"Docling conversion complete: {len(pages)} pages")
            return pages, metadata

        except ImportError as e:
            logger.error(f"Docling not installed: {e}")
            raise ParsingError(
                "Docling library not available. Install with: pip install docling"
            ) from e

        except Exception as e:
            logger.error(f"Docling parsing failed: {e}")
            raise ParsingError(f"Docling parsing failed: {e}") from e

    def _chunk_text(
        self,
        pages: List[Page],
        doc_id: str,
        chunk_size_words: int,
        chunk_overlap_words: int
    ) -> List[TextChunk]:
        """Chunk page text into overlapping chunks.

        Args:
            pages: List of Page objects
            doc_id: Document ID
            chunk_size_words: Target words per chunk
            chunk_overlap_words: Word overlap between chunks

        Returns:
            List of TextChunk objects
        """
        chunks = []
        chunk_counter = 0

        for page in pages:
            if not page.text.strip():
                continue

            # Split into words
            words = page.text.split()

            # Create overlapping chunks
            start_idx = 0
            while start_idx < len(words):
                end_idx = min(start_idx + chunk_size_words, len(words))

                # Get chunk words
                chunk_words = words[start_idx:end_idx]
                chunk_text = " ".join(chunk_words)

                # Calculate character offsets (approximate)
                char_start = sum(len(w) + 1 for w in words[:start_idx])
                char_end = char_start + len(chunk_text)

                chunk = TextChunk(
                    chunk_id=f"{doc_id}-chunk{chunk_counter:04d}",
                    page_num=page.page_num,
                    text=chunk_text,
                    start_offset=char_start,
                    end_offset=char_end,
                    word_count=len(chunk_words)
                )

                chunks.append(chunk)
                chunk_counter += 1

                # Move to next chunk with overlap
                if end_idx >= len(words):
                    break
                start_idx = end_idx - chunk_overlap_words

        logger.debug(f"Created {len(chunks)} chunks from {len(pages)} pages")
        return chunks

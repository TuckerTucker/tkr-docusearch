"""
Document parsing using Docling.

This module provides basic document parsing functionality.
For Wave 2, this is a simplified implementation that can be enhanced
with full Docling integration in future waves.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import uuid

from src.config.processing_config import EnhancedModeConfig, create_pipeline_options
from src.storage.metadata_schema import ChunkContext, DocumentStructure
from src.processing.structure_extractor import extract_document_structure
from src.processing.smart_chunker import create_chunker, SmartChunker

# Import shared types (re-exported for backward compatibility)
from src.processing.types import Page, TextChunk, ParsedDocument

logger = logging.getLogger(__name__)


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
        chunk_overlap_words: int = 50,
        config: Optional[EnhancedModeConfig] = None
    ) -> ParsedDocument:
        """Parse document and extract pages and text.

        Args:
            file_path: Path to document file
            chunk_size_words: Average words per chunk (legacy mode)
            chunk_overlap_words: Word overlap between chunks (legacy mode)
            config: Enhanced mode configuration (overrides legacy params)

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
            pages, metadata, doc = self._parse_with_docling(file_path, config)

            # Generate text chunks based on mode
            if config:
                # Enhanced mode with structure extraction
                text_chunks, structure = self._chunk_document_enhanced(
                    doc, pages, doc_id, config
                )
                # Add structure metadata to document metadata
                metadata["structure"] = {
                    "headings": len(structure.headings),
                    "tables": len(structure.tables),
                    "pictures": len(structure.pictures),
                    "code_blocks": len(structure.code_blocks),
                    "formulas": len(structure.formulas),
                    "max_heading_depth": structure.max_heading_depth,
                    "has_toc": structure.has_table_of_contents
                }
            else:
                # Legacy mode with word-based chunking
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

    def _parse_with_docling(
        self,
        file_path: str,
        config: Optional[EnhancedModeConfig] = None
    ) -> tuple:
        """Parse document using Docling.

        Args:
            file_path: Path to document file (PDF, DOCX, or PPTX)
            config: Enhanced mode configuration (optional)

        Returns:
            Tuple of (pages, metadata, docling_document)

        Raises:
            ParsingError: If Docling parsing fails
        """
        try:
            from docling.document_converter import DocumentConverter, PdfFormatOption
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions

            # Create pipeline options based on config
            if config:
                pipeline_options = create_pipeline_options(config)
                logger.debug(f"Using enhanced mode pipeline options")
            else:
                # Default pipeline options (legacy mode)
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
            return pages, metadata, doc

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

    def _chunk_document_enhanced(
        self,
        doc,
        pages: List[Page],
        doc_id: str,
        config: EnhancedModeConfig
    ) -> tuple:
        """Chunk document using enhanced mode with structure extraction.

        Args:
            doc: DoclingDocument from parsing
            pages: List of Page objects
            doc_id: Document identifier
            config: Enhanced mode configuration

        Returns:
            Tuple of (text_chunks, document_structure)
        """
        # Extract document structure
        structure = extract_document_structure(doc, config)
        logger.info(
            f"Extracted structure: {len(structure.headings)} headings, "
            f"{len(structure.tables)} tables, {len(structure.pictures)} pictures"
        )

        # Create appropriate chunker
        chunker = create_chunker(config)

        # Chunk based on strategy
        if isinstance(chunker, SmartChunker):
            # Use HybridChunker with structure awareness
            text_chunks = chunker.chunk_document(doc, doc_id, structure)
            logger.info(f"Created {len(text_chunks)} smart chunks with context")
        else:
            # Fall back to legacy chunking
            text_chunks = chunker.chunk_pages(pages, doc_id)
            logger.info(f"Created {len(text_chunks)} legacy chunks")

        return text_chunks, structure

"""
Document parsing using Docling.

This module provides document parsing functionality for 21+ formats.
Supports both visual formats (PDF, images) and text-only formats (MD, HTML, CSV).
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import uuid
from enum import Enum

from src.config.processing_config import EnhancedModeConfig, create_pipeline_options
from src.storage.metadata_schema import ChunkContext, DocumentStructure
from src.processing.structure_extractor import extract_document_structure
from src.processing.smart_chunker import create_chunker, SmartChunker

# Import shared types (re-exported for backward compatibility)
from src.processing.types import Page, TextChunk, ParsedDocument

# Import image utilities for page image persistence (Wave 1 integration)
from src.processing.image_utils import save_page_image, ImageStorageError

logger = logging.getLogger(__name__)


# ============================================================================
# Format Categories
# ============================================================================

class FormatType(Enum):
    """Document format processing type."""
    VISUAL = "visual"      # Full visual + text processing (PDF, images)
    TEXT_ONLY = "text"     # Text extraction only, skip visual embeddings
    AUDIO = "audio"        # Audio transcription processing


# Visual formats with page images
VISUAL_FORMATS: Set[str] = {
    '.pdf',     # Portable Document Format
}

# Image formats (treated as single-page visual documents)
IMAGE_FORMATS: Set[str] = {
    '.png',     # Portable Network Graphics
    '.jpg',     # JPEG Image
    '.jpeg',    # JPEG Image
    '.tiff',    # Tagged Image File Format
    '.bmp',     # Bitmap Image
    '.webp',    # WebP Image
}

# Office formats (visual for PPTX, text-only for others)
OFFICE_FORMATS: Set[str] = {
    '.docx',    # Microsoft Word
    '.xlsx',    # Microsoft Excel
    '.pptx',    # Microsoft PowerPoint
}

# Text-only formats (no visual embeddings)
TEXT_ONLY_FORMATS: Set[str] = {
    '.md',       # Markdown
    '.html',     # HTML
    '.htm',      # HTML (alternate extension)
    '.xhtml',    # XHTML
    '.asciidoc', # AsciiDoc
    '.csv',      # Comma-Separated Values
}

# Audio/transcript formats
AUDIO_FORMATS: Set[str] = {
    '.vtt',     # Web Video Text Tracks
    '.wav',     # Waveform Audio
    '.mp3',     # MPEG Audio
}

# Specialized formats
SPECIALIZED_FORMATS: Set[str] = {
    '.xml',     # XML (USPTO/JATS)
    '.json',    # JSON (Docling native)
}


def get_format_type(file_path: str) -> FormatType:
    """Determine processing type for a document.

    Args:
        file_path: Path to document file

    Returns:
        FormatType indicating how to process the document
    """
    ext = Path(file_path).suffix.lower()

    if ext in VISUAL_FORMATS or ext in IMAGE_FORMATS:
        return FormatType.VISUAL
    elif ext in AUDIO_FORMATS:
        return FormatType.AUDIO
    else:
        # All other formats are text-only (OFFICE, TEXT_ONLY, SPECIALIZED)
        return FormatType.TEXT_ONLY


# ============================================================================
# Parsing Functions
# ============================================================================

class ParsingError(Exception):
    """Document parsing error."""

    pass


def docling_to_pages(result, file_path: Optional[str] = None) -> List[Page]:
    """Convert Docling ConversionResult to Page objects.

    This adapter function bridges Docling's output format with our internal
    Page representation. Handles all supported formats:
    - Visual formats (PDF, images): Full image + text processing
    - Text-only formats (DOCX, MD, HTML, CSV): Text extraction only, no images
    - Audio formats (VTT, WAV, MP3): Transcript text, no images

    Args:
        result: Docling ConversionResult from DocumentConverter.convert()
        file_path: Optional path to determine format type

    Returns:
        List of Page objects with images (visual) or None images (text-only)

    Notes:
        - Visual formats: Real page images from Docling
        - Text-only formats: Pages with image=None (skips visual embeddings)
        - Images: Treated as single-page documents with the image itself
        - Audio: Transcript as single text-only page
    """
    from docling.datamodel.document import ConversionResult
    from PIL import Image

    pages = []
    doc = result.document

    # Determine format type if file_path provided
    format_type = get_format_type(file_path) if file_path else None
    ext = Path(file_path).suffix.lower() if file_path else None

    # Handle image formats specially (single image = single page)
    if ext and ext in IMAGE_FORMATS and result.pages and len(result.pages) > 0:
        logger.info(f"Processing image file as single-page document")
        try:
            img = result.pages[0].get_image()
            if img:
                # Extract text (OCR if available)
                text = doc.export_to_text() if hasattr(doc, 'export_to_text') else ""

                pages.append(Page(
                    page_num=1,
                    image=img,
                    width=img.size[0],
                    height=img.size[1],
                    text=text
                ))
                logger.debug(f"Converted image: {img.size[0]}x{img.size[1]}, {len(text)} chars")
        except Exception as e:
            logger.error(f"Failed to convert image: {e}")

        return pages

    # Handle audio formats (transcript only, no images)
    if ext and ext in AUDIO_FORMATS:
        logger.info(f"Processing audio file as text-only transcript")
        try:
            text = doc.export_to_text() if hasattr(doc, 'export_to_text') else ""

            pages.append(Page(
                page_num=1,
                image=None,  # No image for audio
                width=0,
                height=0,
                text=text
            ))
            logger.debug(f"Converted audio transcript: {len(text)} chars")
        except Exception as e:
            logger.error(f"Failed to convert audio: {e}")

        return pages

    # Handle text-only formats (MD, HTML, CSV, etc.)
    if format_type == FormatType.TEXT_ONLY:
        logger.info(f"Processing text-only format: {ext}")
        try:
            text = doc.export_to_text() if hasattr(doc, 'export_to_text') else ""

            pages.append(Page(
                page_num=1,
                image=None,  # No image for text-only
                width=0,
                height=0,
                text=text
            ))
            logger.debug(f"Converted text-only document: {len(text)} chars")
        except Exception as e:
            logger.error(f"Failed to convert text-only document: {e}")

        return pages

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

            # Save page images and thumbnails (Wave 1 integration)
            for page in pages:
                if page.image is not None:
                    try:
                        img_path, thumb_path = save_page_image(
                            image=page.image,
                            doc_id=doc_id,
                            page_num=page.page_num
                        )
                        # Store paths in Page object
                        page.image_path = img_path
                        page.thumb_path = thumb_path
                        logger.debug(
                            f"Saved page {page.page_num} images: "
                            f"full={img_path}, thumb={thumb_path}"
                        )
                    except ImageStorageError as e:
                        logger.warning(
                            f"Failed to save images for page {page.page_num}: {e}. "
                            f"Processing will continue without images."
                        )
                        # Continue processing even if image save fails

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
            from docling.document_converter import (
                DocumentConverter,
                PdfFormatOption,
                WordFormatOption,
                ImageFormatOption,
                AudioFormatOption,
            )
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import (
                PdfPipelineOptions,
                AsrPipelineOptions,
            )
            from docling.pipeline.asr_pipeline import AsrPipeline
            from src.config.processing_config import AsrConfig

            # Determine file format
            ext = Path(file_path).suffix.lower()
            format_type = get_format_type(file_path)

            # Create pipeline options based on config
            if config:
                pipeline_options = create_pipeline_options(config)
                logger.debug(f"Using enhanced mode pipeline options")
            else:
                # Default pipeline options (legacy mode)
                pipeline_options = PdfPipelineOptions()
                pipeline_options.generate_page_images = True
                pipeline_options.generate_picture_images = True

            # Build format-specific options
            format_options = {}

            if ext in VISUAL_FORMATS:
                # PDF with full pipeline
                format_options[InputFormat.PDF] = PdfFormatOption(
                    pipeline_options=pipeline_options
                )
            elif ext in IMAGE_FORMATS:
                # Images (PNG, JPG, etc.) - use image backend
                format_options[InputFormat.IMAGE] = ImageFormatOption(
                    pipeline_options=pipeline_options
                )
            elif ext in OFFICE_FORMATS:
                # Office formats (DOCX, PPTX, XLSX)
                if ext == '.docx':
                    format_options[InputFormat.DOCX] = WordFormatOption()
                elif ext == '.pptx':
                    # PPTX uses default options
                    pass  # DocumentConverter auto-handles PPTX
                elif ext == '.xlsx':
                    # Excel uses default options
                    pass  # DocumentConverter auto-handles XLSX
            elif ext in ['.mp3', '.wav']:
                # Audio formats with ASR transcription
                try:
                    # Load ASR configuration
                    asr_config = AsrConfig.from_env()

                    if asr_config.enabled:
                        logger.info(f"Configuring ASR pipeline for {ext} with model={asr_config.model}")

                        # Create Docling ASR options
                        asr_pipeline_options = AsrPipelineOptions()
                        asr_pipeline_options.asr_options = asr_config.to_docling_model_spec()

                        # Add to format options
                        format_options[InputFormat.AUDIO] = AudioFormatOption(
                            pipeline_cls=AsrPipeline,
                            pipeline_options=asr_pipeline_options
                        )

                        logger.debug(
                            f"ASR config: model={asr_config.model}, "
                            f"language={asr_config.language}, device={asr_config.device}"
                        )
                    else:
                        logger.warning(f"ASR disabled, audio file {file_path} will have minimal processing")

                except Exception as e:
                    logger.error(f"Failed to configure ASR: {e}")
                    # Continue without ASR (fallback to basic processing)
            # All other formats (MD, HTML, CSV, VTT, etc.) use default handling

            converter = DocumentConverter(format_options=format_options if format_options else None)

            # Get file size for logging
            import time
            file_size_bytes = Path(file_path).stat().st_size
            file_size_mb = file_size_bytes / (1024 * 1024)

            # Special logging for audio files (Whisper transcription)
            if ext in ['.mp3', '.wav']:
                logger.info(
                    f"Starting Whisper transcription: {file_path} "
                    f"({file_size_mb:.2f}MB, model={asr_config.model if 'asr_config' in locals() else 'unknown'})"
                )
            else:
                logger.info(
                    f"Starting Docling conversion: {file_path} "
                    f"({file_size_mb:.2f}MB, format: {ext})"
                )

            conversion_start = time.time()
            result = converter.convert(file_path)
            conversion_duration = time.time() - conversion_start

            # Use adapter to convert to Page objects (pass file_path for format detection)
            pages = docling_to_pages(result, file_path)

            # Log completion with throughput metrics
            if ext in ['.mp3', '.wav']:
                # For audio, estimate duration and show realtime factor
                logger.info(
                    f"Whisper transcription complete in {conversion_duration:.1f}s "
                    f"(file size: {file_size_mb:.2f}MB, "
                    f"{file_size_mb/conversion_duration:.2f} MB/sec)"
                )
            else:
                logger.info(
                    f"Docling conversion complete: {len(pages)} pages in {conversion_duration:.1f}s "
                    f"({len(pages)/conversion_duration:.2f} pages/sec, "
                    f"{file_size_mb/conversion_duration:.2f} MB/sec)"
                )

            # Extract metadata from DoclingDocument
            doc = result.document
            ext = Path(file_path).suffix.lower()
            format_type_enum = get_format_type(file_path)

            metadata = {
                "title": doc.name if hasattr(doc, 'name') else "",
                "author": "",  # Docling doesn't expose author in current version
                "created": "",
                "format": ext[1:],  # Remove leading dot
                "num_pages": len(pages),
                "format_type": format_type_enum.value,  # visual, text, or audio
                "has_images": any(p.image is not None for p in pages),
            }

            # Try to extract origin metadata if available
            if hasattr(doc, 'origin') and doc.origin:
                origin = doc.origin
                if hasattr(origin, 'filename'):
                    metadata["original_filename"] = origin.filename
                if hasattr(origin, 'mimetype'):
                    metadata["mimetype"] = origin.mimetype

            # Add audio-specific metadata for MP3/WAV files
            if ext in ['.mp3', '.wav'] and format_type_enum == FormatType.AUDIO:
                # ASR-specific metadata
                metadata["transcript_method"] = "whisper"
                metadata["asr_model_used"] = asr_config.model if 'asr_config' in locals() else "unknown"
                metadata["asr_language"] = asr_config.language if 'asr_config' in locals() else "unknown"
                metadata["audio_format"] = ext[1:]  # "mp3" or "wav"

                # Try to extract duration from Docling document
                if hasattr(doc, 'audio_duration'):
                    metadata["audio_duration_seconds"] = doc.audio_duration
                elif hasattr(doc.origin, 'duration'):
                    metadata["audio_duration_seconds"] = doc.origin.duration

                # Extract timestamp information if available
                if hasattr(doc, 'texts') and doc.texts:
                    # Check if timestamps are in provenance
                    has_timestamps = False
                    for text_item in doc.texts:
                        if hasattr(text_item, 'prov') and text_item.prov:
                            for prov in text_item.prov:
                                if hasattr(prov, 'start_time') and hasattr(prov, 'end_time'):
                                    has_timestamps = True
                                    break
                            if has_timestamps:
                                break

                    metadata["has_word_timestamps"] = has_timestamps

            # Extract full markdown from document (metadata only, not full content)
            # NOTE: We don't store the full markdown in ChromaDB metadata because:
            # 1. It can be hundreds of KB and exceed ChromaDB metadata limits
            # 2. We already have page-level text in the database
            # 3. Full markdown can be regenerated from pages if needed
            try:
                markdown = doc.export_to_markdown()
                metadata["markdown_length"] = len(markdown)
                metadata["markdown_extracted"] = True
                metadata["markdown_error"] = None
                logger.info(f"Extracted markdown: {len(markdown)} chars")
            except Exception as e:
                logger.warning(f"Markdown extraction failed: {e}")
                metadata["markdown_length"] = 0
                metadata["markdown_extracted"] = False
                # Truncate error message to avoid metadata size issues
                error_msg = str(e)
                metadata["markdown_error"] = error_msg[:500] if len(error_msg) > 500 else error_msg

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

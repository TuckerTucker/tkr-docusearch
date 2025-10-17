"""
Document parsing using Docling.

This module provides document parsing functionality for 21+ formats.
Supports both visual formats (PDF, images) and text-only formats (MD, HTML, CSV).
"""

import logging
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from src.config.processing_config import EnhancedModeConfig, create_pipeline_options

# Import image utilities for page image persistence (Wave 1 integration)
from src.processing.image_utils import ImageStorageError, save_page_image
from src.processing.smart_chunker import SmartChunker, create_chunker
from src.processing.structure_extractor import extract_document_structure

# Import timestamp extraction (Wave 3)
from src.processing.text_processor import extract_timestamps_from_text

# Import shared types (re-exported for backward compatibility)
from src.processing.types import Page, ParsedDocument, TextChunk

# Import path utilities for consistent path handling (fixes Whisper/FFmpeg path issues)
from src.utils.paths import ensure_absolute, log_path_info

# Import audio metadata extraction (ID3 tags, album art)


logger = logging.getLogger(__name__)


# ============================================================================
# Format Categories
# ============================================================================


class FormatType(Enum):
    """Document format processing type."""

    VISUAL = "visual"  # Full visual + text processing (PDF, images)
    TEXT_ONLY = "text"  # Text extraction only, skip visual embeddings
    AUDIO = "audio"  # Audio transcription processing


# Visual formats with page/slide images
VISUAL_FORMATS: Set[str] = {
    ".pdf",  # Portable Document Format
    ".pptx",  # Microsoft PowerPoint (slides rendered via slide-renderer service)
}

# Image formats (treated as single-page visual documents)
IMAGE_FORMATS: Set[str] = {
    ".png",  # Portable Network Graphics
    ".jpg",  # JPEG Image
    ".jpeg",  # JPEG Image
    ".tiff",  # Tagged Image File Format
    ".bmp",  # Bitmap Image
    ".webp",  # WebP Image
}

# Office formats (text-only)
OFFICE_FORMATS: Set[str] = {
    ".docx",  # Microsoft Word
    ".xlsx",  # Microsoft Excel
}

# Text-only formats (no visual embeddings)
TEXT_ONLY_FORMATS: Set[str] = {
    ".md",  # Markdown
    ".html",  # HTML
    ".htm",  # HTML (alternate extension)
    ".xhtml",  # XHTML
    ".asciidoc",  # AsciiDoc
    ".csv",  # Comma-Separated Values
}

# Audio/transcript formats
AUDIO_FORMATS: Set[str] = {
    ".vtt",  # Web Video Text Tracks
    ".wav",  # Waveform Audio
    ".mp3",  # MPEG Audio
}

# Specialized formats
SPECIALIZED_FORMATS: Set[str] = {
    ".xml",  # XML (USPTO/JATS)
    ".json",  # JSON (Docling native)
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


def docling_to_pages(
    result, file_path: Optional[str] = None, rendered_slide_images: Optional[List] = None
) -> List[Page]:
    """Convert Docling ConversionResult to Page objects.

    This adapter function bridges Docling's output format with our internal
    Page representation. Handles all supported formats:
    - Visual formats (PDF, PPTX, images): Full image + text processing
    - Text-only formats (DOCX, MD, HTML, CSV): Text extraction only, no images
    - Audio formats (VTT, WAV, MP3): Transcript text, no images

    Args:
        result: Docling ConversionResult from DocumentConverter.convert()
        file_path: Optional path to determine format type
        rendered_slide_images: Optional list of PIL Images for PPTX slides

    Returns:
        List of Page objects with images (visual) or None images (text-only)

    Notes:
        - Visual formats: Real page images from Docling or slide-renderer
        - Text-only formats: Pages with image=None (skips visual embeddings)
        - Images: Treated as single-page documents with the image itself
        - Audio: Transcript as single text-only page
        - PPTX: Slides rendered via slide-renderer service
    """
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
                text = doc.export_to_text() if hasattr(doc, "export_to_text") else ""

                pages.append(
                    Page(page_num=1, image=img, width=img.size[0], height=img.size[1], text=text)
                )
                logger.debug(f"Converted image: {img.size[0]}x{img.size[1]}, {len(text)} chars")
        except Exception as e:
            logger.error(f"Failed to convert image: {e}")

        return pages

    # Handle audio formats (transcript only, no images)
    if ext and ext in AUDIO_FORMATS:
        logger.info(f"Processing audio file as text-only transcript")
        try:
            text = doc.export_to_text() if hasattr(doc, "export_to_text") else ""

            pages.append(
                Page(page_num=1, image=None, width=0, height=0, text=text)  # No image for audio
            )
            logger.debug(f"Converted audio transcript: {len(text)} chars")
        except Exception as e:
            logger.error(f"Failed to convert audio: {e}")

        return pages

    # Handle text-only formats (MD, HTML, CSV, etc.)
    if format_type == FormatType.TEXT_ONLY:
        logger.info(f"Processing text-only format: {ext}")
        try:
            text = doc.export_to_text() if hasattr(doc, "export_to_text") else ""

            pages.append(
                Page(page_num=1, image=None, width=0, height=0, text=text)  # No image for text-only
            )
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

                pages.append(
                    Page(
                        page_num=page_num,
                        image=img,
                        width=img.size[0],
                        height=img.size[1],
                        text=page_text,
                    )
                )

                logger.debug(
                    f"Converted page {page_num}: {img.size[0]}x{img.size[1]}, {len(page_text)} chars"
                )

            except Exception as e:
                logger.error(f"Failed to convert page {idx+1}: {e}")
                continue

    elif doc.pages and len(doc.pages) > 0:
        # PPTX format - has doc.pages and potentially rendered slide images
        logger.info(f"Processing {len(doc.pages)} pages from document")

        for page_num in sorted(doc.pages.keys()):
            try:
                page_text = _extract_page_text(doc, page_num)

                # Use rendered slide image if available
                if rendered_slide_images and (page_num - 1) < len(rendered_slide_images):
                    img = rendered_slide_images[page_num - 1]  # 0-indexed list, 1-indexed page_num
                    logger.debug(f"Using rendered slide image for page {page_num}")
                else:
                    # Fallback: Create blank image as placeholder
                    img = Image.new("RGB", (1024, 1024), color="white")
                    logger.warning(f"No rendered image for page {page_num}, using placeholder")

                pages.append(
                    Page(
                        page_num=page_num,
                        image=img,
                        width=img.size[0],
                        height=img.size[1],
                        text=page_text,
                    )
                )

                logger.debug(
                    f"Converted page {page_num}: {img.size[0]}x{img.size[1]}, {len(page_text)} chars"
                )

            except Exception as e:
                logger.error(f"Failed to convert page {page_num}: {e}")
                continue

    else:
        # DOCX format - no page concept, treat as single page
        logger.info("Processing document without pages (DOCX)")

        # Get all text
        text = doc.export_to_text() if hasattr(doc, "export_to_text") else ""

        # Create single page
        img = Image.new("RGB", (1024, 1024), color="white")

        pages.append(Page(page_num=1, image=img, width=1024, height=1024, text=text))

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
    if hasattr(doc, "texts") and doc.texts:
        for text_item in doc.texts:
            # Check if this text belongs to the page
            if hasattr(text_item, "prov") and text_item.prov:
                # prov is a list of ProvenanceItem objects
                for prov in text_item.prov:
                    if hasattr(prov, "page_no") and prov.page_no == page_num:
                        # Add the text
                        if hasattr(text_item, "text") and text_item.text:
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
        config: Optional[EnhancedModeConfig] = None,
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
        path.suffix.lower()

        logger.info(f"Parsing document: {filename} (id={doc_id})")

        try:
            # Parse with Docling (supports PDF, DOCX, PPTX)
            pages, metadata, doc = self._parse_with_docling(file_path, config)

            # Save page images and thumbnails (Wave 1 integration)
            for page in pages:
                if page.image is not None:
                    try:
                        img_path, thumb_path = save_page_image(
                            image=page.image, doc_id=doc_id, page_num=page.page_num
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
                text_chunks, structure = self._chunk_document_enhanced(doc, pages, doc_id, config)
                # Add structure metadata to document metadata
                metadata["structure"] = {
                    "headings": len(structure.headings),
                    "tables": len(structure.tables),
                    "pictures": len(structure.pictures),
                    "code_blocks": len(structure.code_blocks),
                    "formulas": len(structure.formulas),
                    "max_heading_depth": structure.max_heading_depth,
                    "has_toc": structure.has_table_of_contents,
                }
            else:
                # Legacy mode with word-based chunking
                text_chunks = self._chunk_text(pages, doc_id, chunk_size_words, chunk_overlap_words)

            # Add timestamps to chunks if audio file
            # This extracts [time: X-Y] markers from text or docling provenance
            if metadata.get("format_type") == "audio":
                text_chunks = self._add_timestamps_to_chunks(text_chunks, doc, pages)

            parsed_doc = ParsedDocument(
                filename=filename,
                doc_id=doc_id,
                num_pages=len(pages),
                pages=pages,
                text_chunks=text_chunks,
                metadata=metadata,
            )

            logger.info(f"Parsed {filename}: {len(pages)} pages, " f"{len(text_chunks)} chunks")

            return parsed_doc

        except Exception as e:
            logger.error(f"Failed to parse {filename}: {e}")
            raise ParsingError(f"Parsing failed: {e}") from e

    def _parse_with_docling(
        self, file_path: str, config: Optional[EnhancedModeConfig] = None
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
            from docling.document_converter import DocumentConverter

            from src.processing.parsers import (
                AudioMetadataExtractor,
                FormatOptionsBuilder,
                SlideRenderer,
                SymlinkHelper,
            )

            # Ensure file path is absolute
            file_path = ensure_absolute(file_path, must_exist=True)
            log_path_info(file_path, context="Docling parsing")

            ext = Path(file_path).suffix.lower()

            # Build pipeline options
            pipeline_options = self._build_pipeline_options(config)

            # Build format-specific options
            format_options = FormatOptionsBuilder.build_format_options(
                file_path, pipeline_options, config
            )

            # Extract ID3 metadata for audio files
            audio_id3_metadata = None
            if ext in [".mp3", ".wav"]:
                audio_id3_metadata = AudioMetadataExtractor.extract_id3_metadata(file_path)

            # Create converter and log conversion start
            converter = DocumentConverter(format_options=format_options if format_options else None)
            self._log_conversion_start(file_path)

            # Convert document with symlink workaround for audio
            with SymlinkHelper.audio_file_symlink(file_path):
                result, conversion_duration = self._convert_document(converter, file_path)

            # Render PPTX slides if needed
            rendered_slide_images = None
            if ext == ".pptx":
                slide_renderer = SlideRenderer(render_dpi=self.render_dpi)
                rendered_slide_images = slide_renderer.render_pptx_slides(file_path)

            # Convert to pages
            pages = docling_to_pages(result, file_path, rendered_slide_images)

            # Log completion
            self._log_conversion_complete(file_path, pages, conversion_duration)

            # Build metadata
            metadata = self._build_metadata(result.document, file_path, pages, audio_id3_metadata)

            return pages, metadata, result.document

        except ImportError as e:
            logger.error(f"Docling not installed: {e}")
            raise ParsingError(
                "Docling library not available. Install with: pip install docling"
            ) from e

        except Exception as e:
            logger.error(f"Docling parsing failed: {e}")
            raise ParsingError(f"Docling parsing failed: {e}") from e

    def _build_pipeline_options(self, config: Optional[EnhancedModeConfig]):
        """Build pipeline options based on configuration."""
        from docling.datamodel.pipeline_options import PdfPipelineOptions

        if config:
            pipeline_options = create_pipeline_options(config)
            logger.debug(f"Using enhanced mode pipeline options")
        else:
            # Default pipeline options (legacy mode)
            pipeline_options = PdfPipelineOptions()
            pipeline_options.generate_page_images = True
            pipeline_options.generate_picture_images = True

        return pipeline_options

    def _log_conversion_start(self, file_path: str):
        """Log conversion start with file size."""

        ext = Path(file_path).suffix.lower()
        file_size_bytes = Path(file_path).stat().st_size
        file_size_mb = file_size_bytes / (1024 * 1024)

        if ext in [".mp3", ".wav"]:
            try:
                from src.config.processing_config import AsrConfig

                asr_config = AsrConfig.from_env()
                model = asr_config.model if asr_config.enabled else "unknown"
            except:
                model = "unknown"

            logger.info(
                f"Starting Whisper transcription: {file_path} "
                f"({file_size_mb:.2f}MB, model={model})"
            )
        else:
            logger.info(
                f"Starting Docling conversion: {file_path} "
                f"({file_size_mb:.2f}MB, format: {ext})"
            )

    def _convert_document(self, converter, file_path: str) -> tuple:
        """Convert document and return result with duration."""
        import time

        conversion_start = time.time()
        result = converter.convert(file_path)
        conversion_duration = time.time() - conversion_start

        return result, conversion_duration

    def _log_conversion_complete(self, file_path: str, pages, conversion_duration: float):
        """Log conversion completion with metrics."""
        ext = Path(file_path).suffix.lower()
        file_size_bytes = Path(file_path).stat().st_size
        file_size_mb = file_size_bytes / (1024 * 1024)

        if ext in [".mp3", ".wav"]:
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

    def _build_metadata(self, doc, file_path: str, pages, audio_id3_metadata) -> Dict[str, Any]:
        """Build document metadata."""
        from src.processing.parsers import AudioMetadataExtractor

        ext = Path(file_path).suffix.lower()
        format_type_enum = get_format_type(file_path)

        metadata = {
            "title": doc.name if hasattr(doc, "name") else "",
            "author": "",
            "created": "",
            "format": ext[1:],
            "num_pages": len(pages),
            "format_type": format_type_enum.value,
            "has_images": any(p.image is not None for p in pages),
        }

        # Extract origin metadata
        if hasattr(doc, "origin") and doc.origin:
            origin = doc.origin
            if hasattr(origin, "filename"):
                metadata["original_filename"] = origin.filename
            if hasattr(origin, "mimetype"):
                metadata["mimetype"] = origin.mimetype

        # Add audio-specific metadata
        if ext in [".mp3", ".wav"] and format_type_enum == FormatType.AUDIO:
            try:
                from src.config.processing_config import AsrConfig

                asr_config = AsrConfig.from_env()
            except:
                asr_config = None

            metadata["audio_format"] = ext[1:]
            AudioMetadataExtractor.merge_audio_metadata(
                metadata, doc, audio_id3_metadata, asr_config
            )

        # Extract markdown
        self._extract_markdown_metadata(doc, metadata)

        return metadata

    def _extract_markdown_metadata(self, doc, metadata: Dict[str, Any]):
        """Extract markdown metadata (not full content)."""
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
            error_msg = str(e)
            metadata["markdown_error"] = error_msg[:500] if len(error_msg) > 500 else error_msg

    def _chunk_text(
        self, pages: List[Page], doc_id: str, chunk_size_words: int, chunk_overlap_words: int
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

                # Extract timestamps from text (audio only)
                # Extracts [time: X-Y] markers and returns cleaned text
                start_time, end_time, cleaned_text = extract_timestamps_from_text(chunk_text)
                if start_time is not None:
                    logger.info(
                        f"[TIMESTAMP EXTRACTION] Extracted {start_time}-{end_time} from chunk"
                    )

                # Calculate character offsets (approximate)
                char_start = sum(len(w) + 1 for w in words[:start_idx])
                char_end = char_start + len(cleaned_text)

                chunk = TextChunk(
                    chunk_id=f"{doc_id}-chunk{chunk_counter:04d}",
                    page_num=page.page_num,
                    text=cleaned_text,  # Use cleaned text without [time: X-Y] markers
                    start_offset=char_start,
                    end_offset=char_end,
                    word_count=len(chunk_words),
                    start_time=start_time,  # Extracted timestamp or None
                    end_time=end_time,  # Extracted timestamp or None
                )

                chunks.append(chunk)
                chunk_counter += 1

                # Move to next chunk with overlap
                if end_idx >= len(words):
                    break
                start_idx = end_idx - chunk_overlap_words

        logger.debug(f"Created {len(chunks)} chunks from {len(pages)} pages")
        return chunks

    def _extract_chunk_timestamps(self, chunk: TextChunk, doc, page: Page) -> tuple:
        """Extract timestamps for a chunk from docling provenance data.

        Args:
            chunk: TextChunk to add timestamps to
            doc: DoclingDocument with provenance data
            page: Page containing this chunk

        Returns:
            Tuple of (start_time, end_time) in seconds, or (None, None) if no timestamps
        """
        if not hasattr(doc, "texts") or not doc.texts:
            return (None, None)

        # Collect all timestamps for words in this chunk
        chunk_words = set(chunk.text.lower().split())
        timestamps = []

        for text_item in doc.texts:
            if not hasattr(text_item, "prov") or not text_item.prov:
                continue

            for prov in text_item.prov:
                # Check if this provenance item has timestamps
                if not (hasattr(prov, "start_time") and hasattr(prov, "end_time")):
                    continue

                # Check if this word is in our chunk (simple matching)
                prov_text = text_item.text if hasattr(text_item, "text") else ""
                if any(word in prov_text.lower() for word in chunk_words):
                    timestamps.append((prov.start_time, prov.end_time))

        if not timestamps:
            return (None, None)

        # Aggregate: start = min, end = max
        start_time = min(t[0] for t in timestamps)
        end_time = max(t[1] for t in timestamps)

        # Round to 3 decimal places (millisecond precision)
        return (round(start_time, 3), round(end_time, 3))

    def _add_timestamps_to_chunks(
        self, chunks: List[TextChunk], doc, pages: List[Page]
    ) -> List[TextChunk]:
        """Add timestamps to chunks from docling provenance or text markers.

        Tries two methods:
        1. Extract from [time: X-Y] text markers (new - Wave 2)
        2. Extract from docling provenance data (existing)

        Args:
            chunks: List of TextChunk objects
            doc: DoclingDocument with provenance
            pages: List of Page objects

        Returns:
            Same chunks list with timestamps added (in-place modification)
        """
        # Import extraction function
        from .text_processor import extract_timestamps_from_text

        # Create page lookup
        page_lookup = {p.page_num: p for p in pages}

        for chunk in chunks:
            # Method 1: Try extracting from text markers first
            start_time, end_time, cleaned_text = extract_timestamps_from_text(chunk.text)

            if start_time is not None:
                # Successfully extracted from text marker
                chunk.start_time = start_time
                chunk.end_time = end_time
                chunk.text = cleaned_text  # Update text with marker removed
            else:
                # Method 2: Fall back to provenance extraction
                page = page_lookup.get(chunk.page_num)
                if page:
                    start_time, end_time = self._extract_chunk_timestamps(chunk, doc, page)
                    chunk.start_time = start_time
                    chunk.end_time = end_time

        # Log results
        chunks_with_timestamps = [c for c in chunks if c.start_time is not None]
        if chunks_with_timestamps:
            logger.info(f"Added timestamps to {len(chunks_with_timestamps)}/{len(chunks)} chunks")
        else:
            logger.debug("No timestamps found in provenance data or text markers")

        return chunks

    def _chunk_document_enhanced(
        self, doc, pages: List[Page], doc_id: str, config: EnhancedModeConfig
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

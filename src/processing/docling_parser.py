"""
Document parsing using Docling.

This module provides document parsing functionality for 21+ formats.
Supports both visual formats (PDF, images) and text-only formats (MD, HTML, CSV).
"""

import logging
import tempfile
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from tkr_docusearch.config.processing_config import EnhancedModeConfig, create_pipeline_options

# Import image utilities for page image persistence (Wave 1 integration)
from tkr_docusearch.processing.image_utils import ImageStorageError, save_page_image
from tkr_docusearch.processing.smart_chunker import SmartChunker, create_chunker
from tkr_docusearch.processing.structure_extractor import extract_document_structure

# Import shared types (re-exported for backward compatibility)
from tkr_docusearch.processing.types import Page, ParsedDocument, TextChunk

# Import path utilities for consistent path handling (fixes Whisper/FFmpeg path issues)
from tkr_docusearch.utils.paths import ensure_absolute, log_path_info

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
            # IMPORTANT: Use export_to_markdown() for audio to preserve [time: X-Y] markers
            # export_to_text() strips these markers, breaking timestamp extraction
            text = doc.export_to_markdown() if hasattr(doc, "export_to_markdown") else ""

            logger.info(f"[AUDIO] Using export_to_markdown() to preserve timestamps")

            # Check if timestamps are present in output
            import re

            timestamp_pattern = r"\[time:\s*([\d.]+)-([\d.]+)\]"
            timestamp_matches = re.findall(timestamp_pattern, text)
            if timestamp_matches:
                logger.info(
                    f"[AUDIO] ✓ Found {len(timestamp_matches)} timestamp markers in transcript"
                )
            else:
                logger.warning(
                    f"[AUDIO] ⚠ NO timestamp markers found in transcript - timestamps may not work"
                )

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
        self._temp_repair_files: List[str] = []

        # PDF repair metrics
        self._pdfs_processed = 0
        self._pdfs_repaired = 0
        self._repairs_failed = 0

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

            # Cleanup temp repair files after successful processing
            self._cleanup_temp_repairs()

            # Log repair metrics if any PDFs were processed
            if self._pdfs_processed > 0:
                metrics = self.get_repair_metrics()
                repair_pct = metrics["repair_rate"] * 100
                logger.info(
                    f"PDF repair metrics: {metrics['pdfs_processed']} processed, "
                    f"{metrics['pdfs_repaired']} repaired ({repair_pct:.1f}%), "
                    f"{metrics['repairs_failed']} failed"
                )

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
            doc_structure = None  # Will hold DocumentStructure object if enhanced mode
            if config:
                # Enhanced mode with structure extraction
                text_chunks, doc_structure = self._chunk_document_enhanced(
                    doc, pages, doc_id, config
                )
                # Add structure metadata to document metadata
                metadata["structure"] = {
                    "headings": len(doc_structure.headings),
                    "tables": len(doc_structure.tables),
                    "pictures": len(doc_structure.pictures),
                    "code_blocks": len(doc_structure.code_blocks),
                    "formulas": len(doc_structure.formulas),
                    "max_heading_depth": doc_structure.max_heading_depth,
                    "has_toc": doc_structure.has_table_of_contents,
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
                structure=doc_structure,
            )

            logger.info(f"Parsed {filename}: {len(pages)} pages, " f"{len(text_chunks)} chunks")

            return parsed_doc

        except Exception as e:
            logger.error(f"Failed to parse {filename}: {e}")
            raise ParsingError(f"Parsing failed: {e}") from e
        finally:
            # Ensure cleanup happens even on exceptions
            self._cleanup_temp_repairs()

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

            # Repair PDF dimensions if needed (before Docling processing)
            if ext == ".pdf":
                file_path = self._ensure_pdf_dimensions(file_path)

            # Convert .doc to .docx if needed
            original_filename = None
            conversion_time_ms = None
            if ext == ".doc":
                try:
                    original_filename = Path(file_path).name
                    docx_path, conversion_time_ms = self._convert_legacy_doc(file_path)
                    logger.info(f"Converted {original_filename} to .docx in {conversion_time_ms}ms")
                    file_path = docx_path
                    ext = ".docx"  # Update extension for downstream processing
                except Exception as e:
                    logger.error(f"Failed to convert {Path(file_path).name}: {e}")
                    raise ParsingError(f"Doc conversion failed: {e}") from e

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
            # If PDF dimension error occurs, force repair and retry
            try:
                with SymlinkHelper.audio_file_symlink(file_path):
                    result, conversion_duration = self._convert_document(converter, file_path)
            except Exception as e:
                # Check if this is a PDF dimension error
                if ext == ".pdf" and "page-dimensions" in str(e).lower():
                    logger.warning(f"Docling failed with dimension error, forcing PDF repair: {e}")
                    # Force repair by calling _repair_pdf_dimensions directly
                    repaired_path = self._repair_pdf_dimensions(file_path)
                    logger.info(f"Retrying with repaired PDF: {repaired_path}")
                    # Track the repair
                    self._pdfs_repaired += 1
                    # Retry with repaired PDF
                    converter = DocumentConverter(format_options=format_options if format_options else None)
                    with SymlinkHelper.audio_file_symlink(repaired_path):
                        result, conversion_duration = self._convert_document(converter, repaired_path)
                    # Update file_path to repaired version for downstream processing
                    file_path = repaired_path
                else:
                    # Re-raise if not a dimension error
                    raise

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

            # Add conversion metadata if .doc was converted
            if original_filename and conversion_time_ms is not None:
                metadata["original_filename"] = original_filename
                metadata["converted_from"] = ".doc"
                metadata["conversion_time_ms"] = conversion_time_ms

            return pages, metadata, result.document

        except ImportError as e:
            logger.error(f"Docling not installed: {e}")
            raise ParsingError(
                "Docling library not available. Install with: pip install docling"
            ) from e

        except Exception as e:
            logger.error(f"Docling parsing failed: {e}")
            raise ParsingError(f"Docling parsing failed: {e}") from e

    def _convert_legacy_doc(self, file_path: str) -> tuple:
        """Convert .doc to .docx via legacy-office service.

        Args:
            file_path: Path to .doc file

        Returns:
            Tuple of (path to converted .docx file, conversion_time_ms)

        Raises:
            ParsingError: If conversion fails
        """
        import time

        from src.processing.legacy_office_client import get_legacy_office_client

        logger.info(f"Starting .doc to .docx conversion: {file_path}")
        conversion_start = time.time()

        try:
            # Get client
            client = get_legacy_office_client()

            # Translate path to Docker format (/uploads/filename.doc)
            filename = Path(file_path).name
            docker_path = f"/uploads/{filename}"

            logger.debug(f"Path translation for conversion: {file_path} -> {docker_path}")

            # Call conversion
            docx_docker_path = client.convert_doc_to_docx(docker_path)

            # Translate returned path back to native format
            docx_filename = Path(docx_docker_path).name
            native_docx_path = str(Path(file_path).parent / docx_filename)

            # Calculate conversion time
            conversion_duration = time.time() - conversion_start
            conversion_time_ms = int(conversion_duration * 1000)

            logger.info(
                f"Conversion complete: {filename} -> {docx_filename} "
                f"({conversion_time_ms}ms, {conversion_duration:.2f}s)"
            )

            return native_docx_path, conversion_time_ms

        except Exception as e:
            logger.error(f"Doc conversion failed for {Path(file_path).name}: {e}")
            raise ParsingError(f"Doc conversion failed: {e}") from e

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
                from src.processing.text_processor import extract_timestamps_from_text

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
        # DEBUG: Log document structure on first chunk
        if not hasattr(self, "_logged_provenance_structure"):
            self._logged_provenance_structure = True
            logger.info(f"[TIMESTAMP DEBUG] Inspecting docling document structure")
            logger.info(f"  has 'texts': {hasattr(doc, 'texts')}")
            if hasattr(doc, "texts") and doc.texts:
                logger.info(f"  texts count: {len(doc.texts)}")
                logger.info(f"  first text type: {type(doc.texts[0])}")

                # Inspect first text item
                first_text = doc.texts[0]
                logger.info(
                    f"  first text attributes: {[a for a in dir(first_text) if not a.startswith('_')]}"
                )

                if hasattr(first_text, "prov") and first_text.prov:
                    logger.info(f"  first text has prov: True")
                    logger.info(f"  prov count: {len(first_text.prov)}")
                    if len(first_text.prov) > 0:
                        prov = first_text.prov[0]
                        logger.info(f"  first prov type: {type(prov)}")
                        prov_attrs = [a for a in dir(prov) if not a.startswith("_")]
                        logger.info(f"  first prov attributes: {prov_attrs}")

                        # Check for timestamp fields
                        for attr in ["start_time", "end_time", "time", "timestamp", "start", "end"]:
                            if hasattr(prov, attr):
                                value = getattr(prov, attr)
                                logger.info(f"  prov.{attr}: {value} (type: {type(value)})")
                else:
                    logger.info(f"  first text has prov: False")
            else:
                logger.warning(f"  Document has no 'texts' or texts is empty!")

        if not hasattr(doc, "texts") or not doc.texts:
            logger.debug(f"[TIMESTAMP] No texts in document for chunk {chunk.chunk_id}")
            return (None, None)

        # Collect all timestamps for text items
        timestamps = []
        matched_count = 0
        total_text_items = 0
        items_with_prov = 0

        for text_item in doc.texts:
            total_text_items += 1

            if not hasattr(text_item, "prov") or not text_item.prov:
                continue

            items_with_prov += 1

            for prov in text_item.prov:
                # Check if this provenance item has timestamps
                # Try multiple possible attribute names
                start_time = None
                end_time = None

                if hasattr(prov, "start_time") and hasattr(prov, "end_time"):
                    start_time = prov.start_time
                    end_time = prov.end_time
                elif hasattr(prov, "start") and hasattr(prov, "end"):
                    start_time = prov.start
                    end_time = prov.end
                elif hasattr(prov, "time"):
                    # Some formats might have a time object
                    time_obj = prov.time
                    if hasattr(time_obj, "start") and hasattr(time_obj, "end"):
                        start_time = time_obj.start
                        end_time = time_obj.end

                if start_time is None or end_time is None:
                    continue

                # For audio transcripts, we want ALL timestamps since chunks are sequential
                # Store timestamp with the text for better matching
                prov_text = text_item.text if hasattr(text_item, "text") else ""
                timestamps.append((start_time, end_time, prov_text))
                matched_count += 1

        logger.debug(
            f"[TIMESTAMP] Chunk {chunk.chunk_id}: "
            f"found {matched_count} timestamps from {items_with_prov}/{total_text_items} text items"
        )

        if not timestamps:
            logger.debug(f"[TIMESTAMP] No timestamps found for chunk {chunk.chunk_id}")
            return (None, None)

        # For audio files, chunks are sequential segments of the full transcript
        # We need to match this chunk's text to the corresponding section in the full transcript
        # Simple approach: use first and last timestamp from all available timestamps
        # (This assumes chunks are created in order from the transcript)

        # Better approach: Find timestamps that overlap with chunk text
        chunk_text_lower = chunk.text.lower()
        matching_timestamps = []

        for start, end, prov_text in timestamps:
            # Check if any words from prov_text are in chunk
            if prov_text and any(
                word in chunk_text_lower for word in prov_text.lower().split()[:5]
            ):
                matching_timestamps.append((start, end))

        if matching_timestamps:
            # Use matched timestamps
            start_time = min(t[0] for t in matching_timestamps)
            end_time = max(t[1] for t in matching_timestamps)
            logger.info(
                f"[TIMESTAMP] ✓ Extracted from provenance: "
                f"{start_time:.2f}s - {end_time:.2f}s for chunk {chunk.chunk_id} "
                f"(matched {len(matching_timestamps)} segments)"
            )
        else:
            # Fallback: Use all timestamps (assumes sequential chunks)
            start_time = min(t[0] for t in timestamps)
            end_time = max(t[1] for t in timestamps)
            logger.warning(
                f"[TIMESTAMP] Fallback: Using all available timestamps "
                f"{start_time:.2f}s - {end_time:.2f}s for chunk {chunk.chunk_id}"
            )

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

        # Track extraction methods
        from_text_markers = 0
        from_provenance = 0
        failed = 0

        for chunk in chunks:
            # Check if timestamps are already set (e.g., by smart_chunker)
            if chunk.start_time is not None and chunk.end_time is not None:
                # Timestamps already extracted - skip
                from_text_markers += 1
                logger.debug(
                    f"[TIMESTAMP] Method 0 (pre-extracted): "
                    f"{chunk.start_time:.2f}s - {chunk.end_time:.2f}s for {chunk.chunk_id}"
                )
                continue

            # Method 1: Try extracting from text markers first
            start_time, end_time, cleaned_text = extract_timestamps_from_text(chunk.text)

            if start_time is not None:
                # Successfully extracted from text marker
                chunk.start_time = start_time
                chunk.end_time = end_time
                chunk.text = cleaned_text  # Update text with marker removed
                from_text_markers += 1
                logger.debug(
                    f"[TIMESTAMP] Method 1 (text marker): "
                    f"{start_time:.2f}s - {end_time:.2f}s for {chunk.chunk_id}"
                )
            else:
                # Method 2: Fall back to provenance extraction
                page = page_lookup.get(chunk.page_num)
                if page:
                    start_time, end_time = self._extract_chunk_timestamps(chunk, doc, page)
                    chunk.start_time = start_time
                    chunk.end_time = end_time

                    if start_time is not None:
                        from_provenance += 1
                    else:
                        failed += 1
                else:
                    failed += 1
                    logger.warning(
                        f"[TIMESTAMP] No page found for chunk {chunk.chunk_id} (page {chunk.page_num})"
                    )

        # Log detailed results
        chunks_with_timestamps = [c for c in chunks if c.start_time is not None]
        if chunks_with_timestamps:
            logger.info(
                f"[TIMESTAMP] ✓ Added timestamps to {len(chunks_with_timestamps)}/{len(chunks)} chunks "
                f"(text markers: {from_text_markers}, provenance: {from_provenance}, failed: {failed})"
            )
        else:
            logger.warning(
                f"[TIMESTAMP] ✗ NO timestamps extracted for any chunks! "
                f"(total chunks: {len(chunks)}, failed: {failed})"
            )
            logger.warning(
                f"[TIMESTAMP] This means bidirectional audio navigation will NOT work. "
                f"Check that docling is extracting provenance data correctly."
            )

        return chunks

    def _pdf_has_explicit_dimensions(self, file_path: str) -> bool:
        """Check if PDF has explicit dimension boxes on first page.

        Uses pypdf to inspect the first page's object for explicit dimension boxes
        (/MediaBox, /CropBox, /BleedBox, /TrimBox). Returns False if dimensions
        are inherited from parent, True if explicitly defined.

        Args:
            file_path: Path to PDF file

        Returns:
            True if dimensions are explicit, False if inherited from parent
        """
        try:
            from pypdf import PdfReader

            logger.debug(f"Checking PDF dimensions: {file_path}")

            # Read PDF
            reader = PdfReader(file_path)
            if not reader.pages or len(reader.pages) == 0:
                logger.warning(f"PDF has no pages: {file_path}")
                return True  # Skip repair on error

            # Get first page object
            first_page = reader.pages[0]

            # Check for explicit dimension boxes in page object
            # These are the standard PDF page boundary boxes
            dimension_boxes = ["/MediaBox", "/CropBox", "/BleedBox", "/TrimBox"]

            has_explicit = False
            for box_name in dimension_boxes:
                if box_name in first_page:
                    has_explicit = True
                    logger.debug(f"Found explicit {box_name} on first page")
                    break

            if has_explicit:
                logger.debug(f"PDF has explicit dimensions: {file_path}")
            else:
                logger.debug(
                    f"PDF dimensions are inherited from parent (needs repair): {file_path}"
                )

            return has_explicit

        except Exception as e:
            logger.warning(f"Failed to check PDF dimensions: {e}. Skipping repair.")
            return True  # Skip repair on error

    def _repair_pdf_dimensions(self, file_path: str) -> str:
        """Repair PDF by making inherited dimensions explicit.

        Creates a repaired copy of the PDF where each page has explicit dimension
        boxes extracted from the parent. This fixes Docling compatibility issues
        with PDFs that have inherited dimensions.

        Args:
            file_path: Path to PDF file with inherited dimensions

        Returns:
            Path to repaired temporary PDF file
        """
        try:
            from pypdf import PdfReader, PdfWriter

            logger.info(f"Repairing PDF dimensions: {Path(file_path).name}")

            # Read original PDF
            reader = PdfReader(file_path)
            writer = PdfWriter()

            # Copy pages with explicit dimensions
            # Default to US Letter if no dimensions found anywhere
            DEFAULT_MEDIABOX = [0, 0, 612, 792]  # US Letter in points

            for page in reader.pages:
                # Get mediabox (auto-resolves from parent)
                mediabox = page.mediabox

                # Handle case where mediabox is None (no dimensions anywhere)
                if mediabox is None:
                    logger.warning(
                        f"Page has no dimensions in page tree, using default (US Letter)"
                    )
                    mediabox = DEFAULT_MEDIABOX

                # Explicitly set it on the page
                page.mediabox = mediabox

                # Add to writer
                writer.add_page(page)

            # Create temp file for repaired PDF
            fd, temp_path = tempfile.mkstemp(suffix=".pdf", prefix="repaired_docling_")

            try:
                # Write repaired PDF
                with open(temp_path, "wb") as f:
                    writer.write(f)

                logger.info(
                    f"PDF dimension repair complete: {Path(file_path).name} -> {Path(temp_path).name}"
                )

                # Track temp file for cleanup
                self._temp_repair_files.append(temp_path)

                return temp_path

            except Exception as e:
                # Clean up temp file if write fails
                import os

                os.close(fd)
                if Path(temp_path).exists():
                    Path(temp_path).unlink()
                raise

        except Exception as e:
            logger.error(f"Failed to repair PDF dimensions: {e}")
            raise ParsingError(f"PDF dimension repair failed: {e}") from e

    def _ensure_pdf_dimensions(self, file_path: str) -> str:
        """Ensure PDF has explicit dimensions, repairing if needed.

        Checks if PDF has explicit dimension boxes. If not, creates a repaired
        temporary copy with explicit dimensions for Docling compatibility.

        Args:
            file_path: Path to PDF file

        Returns:
            Path to PDF (original if already has dimensions, repaired temp if not)
        """
        # Increment processed counter
        self._pdfs_processed += 1

        if not self._pdf_has_explicit_dimensions(file_path):
            logger.info(
                f"PDF dimensions inherited from parent, repairing: {Path(file_path).name}"
            )
            try:
                repaired_path = self._repair_pdf_dimensions(file_path)
                # Increment repaired counter on success
                self._pdfs_repaired += 1
                return repaired_path
            except Exception:
                # Increment failed counter on exception
                self._repairs_failed += 1
                raise
        else:
            logger.debug(f"PDF has explicit dimensions, no repair needed: {Path(file_path).name}")
            return file_path

    def _cleanup_temp_repairs(self) -> None:
        """Clean up temporary repaired PDF files.

        Removes all tracked temporary files created during PDF dimension repair.
        Safe to call multiple times.
        """
        if not self._temp_repair_files:
            return

        logger.debug(f"Cleaning up {len(self._temp_repair_files)} temporary repair files")

        for temp_file in self._temp_repair_files:
            try:
                temp_path = Path(temp_file)
                if temp_path.exists():
                    temp_path.unlink()
                    logger.debug(f"Removed temp file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to remove temp file {temp_file}: {e}")

        # Clear the list
        self._temp_repair_files = []

    def get_repair_metrics(self) -> Dict[str, Any]:
        """Get PDF repair metrics.

        Returns:
            Dictionary containing repair metrics:
            - pdfs_processed: Total PDFs processed
            - pdfs_repaired: Number of PDFs successfully repaired
            - repairs_failed: Number of repair failures
            - repair_rate: Percentage of PDFs that required repair (0.0-1.0)
        """
        return {
            "pdfs_processed": self._pdfs_processed,
            "pdfs_repaired": self._pdfs_repaired,
            "repairs_failed": self._repairs_failed,
            "repair_rate": (
                self._pdfs_repaired / self._pdfs_processed if self._pdfs_processed > 0 else 0.0
            ),
        }

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

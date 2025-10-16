"""
Main document processing coordinator.

This module orchestrates the complete document processing pipeline:
1. Document parsing (Docling)
2. Visual processing (page embeddings)
3. Text processing (chunk embeddings)
4. Storage (ChromaDB)
"""

import os
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime

from .docling_parser import DoclingParser, ParsingError
from .visual_processor import VisualProcessor
from .text_processor import TextProcessor
from src.config.processing_config import EnhancedModeConfig
from src.storage.metadata_schema import DocumentStructure

logger = logging.getLogger(__name__)


@dataclass
class ProcessingStatus:
    """Processing status for monitoring.

    Matches the ProcessingStatus structure defined in processing-interface.md.
    """

    doc_id: str
    filename: str
    status: str  # queued, parsing, embedding_visual, embedding_text, storing, completed, failed
    progress: float  # 0.0 to 1.0
    stage: str  # Human-readable stage description
    current_page: Optional[int] = None
    total_pages: Optional[int] = None
    elapsed_seconds: int = 0
    estimated_remaining_seconds: Optional[int] = None
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


@dataclass
class StorageConfirmation:
    """Storage confirmation result.

    Matches the StorageConfirmation structure defined in processing-interface.md.
    """

    doc_id: str
    visual_ids: list
    text_ids: list
    total_size_bytes: int
    timestamp: str


class ProcessingError(Exception):
    """Base processing error."""

    pass


class EmbeddingError(ProcessingError):
    """Embedding generation error."""

    pass


class StorageError(ProcessingError):
    """Storage operation error."""

    pass


class DocumentProcessor:
    """Main document processing coordinator.

    Orchestrates the complete processing pipeline from file upload to storage.
    """

    def __init__(
        self,
        embedding_engine,
        storage_client,
        parser_config: Optional[Dict[str, Any]] = None,
        visual_batch_size: int = 4,
        text_batch_size: int = 8,
        enhanced_mode_config: Optional[EnhancedModeConfig] = None
    ):
        """Initialize document processor.

        Args:
            embedding_engine: Embedding engine instance (real or mock)
            storage_client: Storage client instance (real or mock)
            parser_config: Optional parser configuration
            visual_batch_size: Batch size for visual processing
            text_batch_size: Batch size for text processing
            enhanced_mode_config: Optional enhanced mode configuration
        """
        self.embedding_engine = embedding_engine
        self.storage_client = storage_client
        self.enhanced_mode_config = enhanced_mode_config

        # Initialize pipeline components
        parser_config = parser_config or {}
        self.parser = DoclingParser(
            render_dpi=parser_config.get('render_dpi', 150)
        )
        self.visual_processor = VisualProcessor(
            embedding_engine=embedding_engine,
            batch_size=visual_batch_size
        )
        self.text_processor = TextProcessor(
            embedding_engine=embedding_engine,
            batch_size=text_batch_size
        )

        mode = "enhanced" if enhanced_mode_config else "legacy"
        logger.info(
            f"Initialized DocumentProcessor ({mode} mode, "
            f"visual_batch={visual_batch_size}, text_batch={text_batch_size})"
        )

    def process_document(
        self,
        file_path: str,
        chunk_size_words: int = 250,
        chunk_overlap_words: int = 50,
        status_callback=None
    ) -> StorageConfirmation:
        """Process a document through the complete pipeline.

        Args:
            file_path: Path to document file
            chunk_size_words: Target words per chunk
            chunk_overlap_words: Word overlap between chunks
            status_callback: Optional callback(status: ProcessingStatus)

        Returns:
            StorageConfirmation with storage details

        Raises:
            ProcessingError: If processing fails at any stage
            ParsingError: If document parsing fails
            EmbeddingError: If embedding generation fails
            StorageError: If storage fails
        """
        start_time = time.time()
        path = Path(file_path)
        filename = path.name
        doc_id = None

        try:
            # Determine file type for user-friendly status messages
            file_ext = os.path.splitext(filename)[1].lower()

            # Create file-type-specific parsing messages
            parsing_messages = {
                '.pdf': "Extracting text and images from PDF",
                '.docx': "Processing Word document",
                '.pptx': "Processing PowerPoint presentation",
                '.xlsx': "Processing Excel spreadsheet",
                '.mp3': "Transcribing audio with Whisper (this may take several minutes)",
                '.wav': "Transcribing audio with Whisper (this may take several minutes)",
                '.md': "Parsing Markdown document",
                '.html': "Parsing HTML document",
                '.png': "Processing image",
                '.jpg': "Processing image",
                '.jpeg': "Processing image",
            }

            parsing_stage = parsing_messages.get(file_ext, f"Processing {file_ext} file")

            # Stage 1: Parsing
            status = ProcessingStatus(
                doc_id="pending",
                filename=filename,
                status="parsing",
                progress=0.1,
                stage=parsing_stage
            )
            self._update_status(status, status_callback)

            logger.info(f"Starting document processing: {filename}")

            parsed_doc = self.parser.parse_document(
                file_path=file_path,
                chunk_size_words=chunk_size_words,
                chunk_overlap_words=chunk_overlap_words,
                config=self.enhanced_mode_config
            )

            doc_id = parsed_doc.doc_id
            total_pages = parsed_doc.num_pages

            logger.info(
                f"Parsed {filename}: {total_pages} pages, "
                f"{len(parsed_doc.text_chunks)} chunks"
            )

            # Stage 2: Visual Embedding (skip for text-only formats)
            visual_results = []
            has_visual_content = any(page.image is not None for page in parsed_doc.pages)

            if has_visual_content:
                status = ProcessingStatus(
                    doc_id=doc_id,
                    filename=filename,
                    status="embedding_visual",
                    progress=0.3,
                    stage=f"Generating visual embeddings for {total_pages} pages",
                    total_pages=total_pages,
                    elapsed_seconds=int(time.time() - start_time)
                )
                self._update_status(status, status_callback)

                # Create progress callback for visual processing
                def visual_progress_callback(pages_completed, total):
                    # Progress ranges from 0.3 to 0.6 (30% of total)
                    granular_progress = 0.3 + (pages_completed / total * 0.3)
                    batch_num = (pages_completed - 1) // self.visual_processor.batch_size + 1
                    total_batches = (total + self.visual_processor.batch_size - 1) // self.visual_processor.batch_size

                    status = ProcessingStatus(
                        doc_id=doc_id,
                        filename=filename,
                        status="embedding_visual",
                        progress=granular_progress,
                        stage=f"Visual embeddings: {pages_completed}/{total} pages (batch {batch_num}/{total_batches})",
                        current_page=pages_completed,
                        total_pages=total,
                        elapsed_seconds=int(time.time() - start_time)
                    )
                    self._update_status(status, status_callback)

                visual_results = self.visual_processor.process_pages(
                    pages=parsed_doc.pages,
                    doc_id=doc_id,
                    progress_callback=visual_progress_callback
                )

                visual_stats = self.visual_processor.get_processing_stats(visual_results)
                logger.info(
                    f"Visual processing complete: "
                    f"{visual_stats['num_pages']} pages in "
                    f"{visual_stats['total_time_ms']:.0f}ms"
                )
            else:
                logger.info(
                    f"Skipping visual embeddings for {filename} - "
                    "text-only format (MD, HTML, CSV, audio transcript, etc.)"
                )

            # Stage 3: Text Embedding (skip if no text extracted)
            text_results = []
            if parsed_doc.text_chunks:
                total_chunks = len(parsed_doc.text_chunks)
                status = ProcessingStatus(
                    doc_id=doc_id,
                    filename=filename,
                    status="embedding_text",
                    progress=0.6,
                    stage=f"Generating text embeddings for {total_chunks} chunks",
                    total_pages=total_pages,
                    elapsed_seconds=int(time.time() - start_time)
                )
                self._update_status(status, status_callback)

                # Create progress callback for text processing
                def text_progress_callback(chunks_completed, total):
                    # Progress ranges from 0.6 to 0.9 (30% of total)
                    granular_progress = 0.6 + (chunks_completed / total * 0.3)
                    batch_num = (chunks_completed - 1) // self.text_processor.batch_size + 1
                    total_batches = (total + self.text_processor.batch_size - 1) // self.text_processor.batch_size

                    status = ProcessingStatus(
                        doc_id=doc_id,
                        filename=filename,
                        status="embedding_text",
                        progress=granular_progress,
                        stage=f"Text embeddings: {chunks_completed}/{total} chunks (batch {batch_num}/{total_batches})",
                        total_pages=total_pages,
                        elapsed_seconds=int(time.time() - start_time)
                    )
                    self._update_status(status, status_callback)

                text_results = self.text_processor.process_chunks(
                    chunks=parsed_doc.text_chunks,
                    doc_id=doc_id,
                    progress_callback=text_progress_callback
                )

                text_stats = self.text_processor.get_processing_stats(text_results)
                logger.info(
                    f"Text processing complete: "
                    f"{text_stats['num_chunks']} chunks in "
                    f"{text_stats['total_time_ms']:.0f}ms"
                )
            else:
                logger.info(
                    f"No text extracted from {filename} - "
                    "document appears to be image-only (e.g., scanned PDF)"
                )

            # Stage 3.4: Check for timestamps and set metadata flags
            if parsed_doc.text_chunks:
                has_timestamps = any(
                    chunk.start_time is not None and chunk.end_time is not None
                    for chunk in parsed_doc.text_chunks
                )
                parsed_doc.metadata["has_timestamps"] = has_timestamps

                # For audio files with timestamps, set VTT trigger flag
                if parsed_doc.metadata.get("format_type") == "audio" and has_timestamps:
                    parsed_doc.metadata["has_word_timestamps"] = True

                timestamp_count = sum(
                    1 for c in parsed_doc.text_chunks
                    if c.start_time is not None
                )
                logger.info(
                    f"Document has timestamps: {has_timestamps} "
                    f"({timestamp_count}/{len(parsed_doc.text_chunks)} chunks)"
                )
            else:
                parsed_doc.metadata["has_timestamps"] = False

            # Stage 3.5: VTT Generation (audio with timestamps only)
            if parsed_doc.metadata.get("has_word_timestamps") and parsed_doc.text_chunks:
                # Check if any chunks have timestamps
                has_timestamps = any(
                    chunk.start_time is not None
                    for chunk in parsed_doc.text_chunks
                )

                if has_timestamps:
                    try:
                        from .vtt_generator import generate_vtt, save_vtt

                        logger.info(f"Generating VTT for audio file: {filename}")

                        vtt_content = generate_vtt(parsed_doc.text_chunks, filename)
                        vtt_path = save_vtt(doc_id, vtt_content)

                        # Store VTT path in metadata
                        parsed_doc.metadata["vtt_path"] = str(vtt_path)
                        parsed_doc.metadata["vtt_available"] = True

                        logger.info(f"Generated VTT: {vtt_path}")
                    except Exception as e:
                        logger.warning(f"VTT generation failed: {e}")
                        parsed_doc.metadata["vtt_available"] = False
                else:
                    logger.info(
                        f"No chunks with timestamps in {filename}, skipping VTT generation"
                    )
                    parsed_doc.metadata["vtt_available"] = False

            # Stage 3.6: Markdown Generation (all documents with text)
            if parsed_doc.text_chunks:
                try:
                    from .markdown_utils import generate_markdown_with_frontmatter, save_markdown

                    logger.info(f"Generating markdown for document: {filename}")

                    # Prepare chunks for markdown generation
                    chunks_for_markdown = [
                        {"text_content": chunk.text}
                        for chunk in parsed_doc.text_chunks
                    ]

                    markdown_content = generate_markdown_with_frontmatter(
                        chunks=chunks_for_markdown,
                        doc_metadata=parsed_doc.metadata,
                        filename=filename,
                        doc_id=doc_id
                    )

                    markdown_path = save_markdown(doc_id, markdown_content)

                    # Store markdown path in metadata
                    parsed_doc.metadata["markdown_path"] = str(markdown_path)
                    parsed_doc.metadata["markdown_available"] = True

                    logger.info(f"Generated markdown: {markdown_path}")
                except Exception as e:
                    logger.warning(f"Markdown generation failed: {e}")
                    parsed_doc.metadata["markdown_available"] = False

            # Stage 4: Storage
            status = ProcessingStatus(
                doc_id=doc_id,
                filename=filename,
                status="storing",
                progress=0.9,
                stage="Storing embeddings in ChromaDB",
                total_pages=total_pages,
                elapsed_seconds=int(time.time() - start_time)
            )
            self._update_status(status, status_callback)

            confirmation = self._store_embeddings(
                doc_id=doc_id,
                visual_results=visual_results,
                text_results=text_results,
                text_chunks=parsed_doc.text_chunks,
                doc_metadata=parsed_doc.metadata,
                filename=filename,
                file_path=file_path,
                pages=parsed_doc.pages  # Wave 1: Pass pages for image paths
            )

            # Stage 5: Completed
            elapsed = int(time.time() - start_time)
            status = ProcessingStatus(
                doc_id=doc_id,
                filename=filename,
                status="completed",
                progress=1.0,
                stage="Processing complete",
                total_pages=total_pages,
                elapsed_seconds=elapsed
            )
            self._update_status(status, status_callback)

            logger.info(
                f"Document processing complete: {filename} "
                f"({elapsed}s, {total_pages} pages, "
                f"{len(visual_results)} visual + {len(text_results)} text embeddings)"
            )

            return confirmation

        except ParsingError as e:
            logger.error(f"Parsing failed for {filename}: {e}")
            self._update_failure_status(
                doc_id or "unknown",
                filename,
                f"Parsing failed: {e}",
                status_callback,
                int(time.time() - start_time)
            )
            raise

        except EmbeddingError as e:
            logger.error(f"Embedding failed for {filename}: {e}")
            self._update_failure_status(
                doc_id or "unknown",
                filename,
                f"Embedding generation failed: {e}",
                status_callback,
                int(time.time() - start_time)
            )
            raise

        except StorageError as e:
            logger.error(f"Storage failed for {filename}: {e}")
            self._update_failure_status(
                doc_id or "unknown",
                filename,
                f"Storage failed: {e}",
                status_callback,
                int(time.time() - start_time)
            )
            raise

        except Exception as e:
            logger.error(f"Unexpected error processing {filename}: {e}", exc_info=True)
            self._update_failure_status(
                doc_id or "unknown",
                filename,
                f"Unexpected error: {e}",
                status_callback,
                int(time.time() - start_time)
            )
            raise ProcessingError(f"Processing failed: {e}") from e

    def _store_embeddings(
        self,
        doc_id: str,
        visual_results,
        text_results,
        text_chunks,
        doc_metadata: Dict[str, Any],
        filename: str,
        file_path: str,
        pages: List = None  # Wave 1: Optional pages for image paths
    ) -> StorageConfirmation:
        """Store embeddings in ChromaDB with enhanced metadata.

        Args:
            doc_id: Document ID (for album art storage)
            visual_results: List of VisualEmbeddingResult
            text_results: List of TextEmbeddingResult
            text_chunks: List of TextChunk (with context)
            doc_metadata: Document metadata
            filename: Original filename
            file_path: Source file path
            pages: Optional list of Page objects (for image paths - Wave 1)

        Returns:
            StorageConfirmation

        Raises:
            StorageError: If storage fails
        """
        try:
            visual_ids = []
            text_ids = []
            total_size_bytes = 0

            # Extract structure from metadata if available (enhanced mode)
            structure = None
            if "structure" in doc_metadata and self.enhanced_mode_config:
                # Structure metadata is already in doc_metadata from parser
                logger.debug("Enhanced mode: Document structure available")

            # Save album art for audio files (use placeholder if no embedded art)
            album_art_saved_path = None
            if "audio_duration_seconds" in doc_metadata:  # This is an audio file
                try:
                    from src.processing.audio_metadata import save_album_art, AudioMetadata

                    # Check if album art exists
                    has_album_art = "_album_art_data" in doc_metadata and "_album_art_mime" in doc_metadata

                    # Create temporary AudioMetadata
                    temp_metadata = AudioMetadata(
                        has_album_art=has_album_art,
                        album_art_data=doc_metadata.get("_album_art_data"),
                        album_art_mime=doc_metadata.get("_album_art_mime"),
                        album_art_description=doc_metadata.get("album_art_description")
                    )

                    # Always save (will use placeholder if no album art)
                    album_art_saved_path = save_album_art(
                        doc_id,
                        temp_metadata,
                        use_placeholder=True  # Use placeholder for audio files without album art
                    )

                    if album_art_saved_path:
                        logger.info(f"Saved album art to: {album_art_saved_path}")
                        # Add path to metadata
                        doc_metadata["album_art_path"] = album_art_saved_path
                except Exception as e:
                    logger.error(f"Failed to save album art for {doc_id}: {e}")

            # Filter doc_metadata to remove large/problematic fields before spreading
            # ChromaDB metadata values must be simple types and not too large
            filtered_keys = []
            safe_doc_metadata = {}
            for k, v in doc_metadata.items():
                # Always exclude these known large/problematic fields
                # markdown_error can contain large error messages even after truncation
                # _album_art_data is temporary and should not be stored in ChromaDB (binary data)
                if k in ['full_markdown', 'structure', 'full_markdown_compressed', 'markdown_error', '_album_art_data', '_album_art_mime']:
                    filtered_keys.append(f"{k} (excluded field)")
                    continue
                # Skip very large string values or binary data
                if isinstance(v, (str, bytes)) and len(v) > 1000:
                    filtered_keys.append(f"{k} ({len(v)} chars/bytes, too large)")
                    continue
                safe_doc_metadata[k] = v

            if filtered_keys:
                logger.info(f"Filtered metadata fields: {', '.join(filtered_keys)}")

            # Create page lookup for image paths (Wave 1 integration)
            page_lookup = {}
            if pages:
                page_lookup = {page.page_num: page for page in pages}

            # Store visual embeddings
            for result in visual_results:
                base_metadata = {
                    "filename": filename,
                    "page": result.page_num,
                    "source_path": file_path,
                    **safe_doc_metadata
                }

                # Prepare enhanced metadata if available
                if hasattr(self.storage_client, '_prepare_enhanced_visual_metadata') and structure:
                    metadata = self.storage_client._prepare_enhanced_visual_metadata(
                        base_metadata, structure
                    )
                else:
                    metadata = base_metadata

                # Get image paths from page if available (Wave 1 integration)
                image_path = None
                thumb_path = None
                if result.page_num in page_lookup:
                    page = page_lookup[result.page_num]
                    image_path = page.image_path
                    thumb_path = page.thumb_path

                embedding_id = self.storage_client.add_visual_embedding(
                    doc_id=result.doc_id,
                    page=result.page_num,
                    full_embeddings=result.embedding,
                    metadata=metadata,
                    image_path=image_path,  # Wave 1: Pass image path
                    thumb_path=thumb_path   # Wave 1: Pass thumbnail path
                )
                visual_ids.append(embedding_id)

                # Estimate size (rough approximation)
                total_size_bytes += result.embedding.nbytes

            logger.debug(f"Stored {len(visual_ids)} visual embeddings")

            # Create chunk lookup by chunk_id for context
            chunk_lookup = {chunk.chunk_id: chunk for chunk in text_chunks}

            # Store text embeddings
            for result in text_results:
                # Get chunk for context and timestamps
                chunk = chunk_lookup.get(result.chunk_id)

                base_metadata = {
                    "filename": filename,
                    "chunk_id": result.chunk_id,
                    "page": result.page_num,
                    "text_preview": result.text[:200],
                    "word_count": len(result.text.split()),
                    "source_path": file_path,
                    **safe_doc_metadata  # Use filtered metadata (already defined above)
                }

                # Add timestamp fields if chunk has timestamps (Wave 1)
                # Only add if not None - ChromaDB doesn't accept None values
                if chunk:
                    if chunk.start_time is not None:
                        base_metadata["start_time"] = chunk.start_time
                    if chunk.end_time is not None:
                        base_metadata["end_time"] = chunk.end_time
                    base_metadata["has_timestamps"] = chunk.start_time is not None

                # Get chunk context if available
                chunk_context = None
                if chunk and chunk.context:
                    chunk_context = chunk.context

                # Prepare enhanced metadata if available
                if hasattr(self.storage_client, '_prepare_enhanced_text_metadata') and chunk_context:
                    metadata = self.storage_client._prepare_enhanced_text_metadata(
                        base_metadata, chunk_context
                    )
                else:
                    metadata = base_metadata

                embedding_id = self.storage_client.add_text_embedding(
                    doc_id=result.doc_id,
                    chunk_id=int(result.chunk_id.split('-chunk')[-1]),
                    full_embeddings=result.embedding,
                    metadata=metadata
                )
                text_ids.append(embedding_id)

                # Estimate size
                total_size_bytes += result.embedding.nbytes

            logger.debug(f"Stored {len(text_ids)} text embeddings")

            confirmation = StorageConfirmation(
                doc_id=visual_results[0].doc_id if visual_results else text_results[0].doc_id,
                visual_ids=visual_ids,
                text_ids=text_ids,
                total_size_bytes=total_size_bytes,
                timestamp=datetime.utcnow().isoformat() + "Z"
            )

            return confirmation

        except Exception as e:
            logger.error(f"Storage failed: {e}")
            raise StorageError(f"Failed to store embeddings: {e}") from e

    def _update_status(self, status: ProcessingStatus, callback):
        """Update processing status.

        Args:
            status: ProcessingStatus object
            callback: Optional callback function
        """
        if callback:
            try:
                callback(status)
            except Exception as e:
                logger.warning(f"Status callback failed: {e}")

    def _update_failure_status(
        self,
        doc_id: str,
        filename: str,
        error_message: str,
        callback,
        elapsed_seconds: int
    ):
        """Update status with failure.

        Args:
            doc_id: Document ID
            filename: Filename
            error_message: Error message
            callback: Optional callback function
            elapsed_seconds: Elapsed time
        """
        status = ProcessingStatus(
            doc_id=doc_id,
            filename=filename,
            status="failed",
            progress=0.0,
            stage="Processing failed",
            error_message=error_message,
            elapsed_seconds=elapsed_seconds
        )
        self._update_status(status, callback)

    def get_model_info(self) -> Dict[str, Any]:
        """Get embedding model information.

        Returns:
            Model info dictionary
        """
        return self.embedding_engine.get_model_info()

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics.

        Returns:
            Storage stats dictionary
        """
        return self.storage_client.get_collection_stats()

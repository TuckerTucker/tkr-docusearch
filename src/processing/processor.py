"""
Main document processing coordinator.

This module orchestrates the complete document processing pipeline:
1. Document parsing (Docling)
2. Visual processing (page embeddings)
3. Text processing (chunk embeddings)
4. Storage (Koji)
"""

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from tkr_docusearch.config.processing_config import EnhancedModeConfig

from .docling_parser import DoclingParser, ParsingError
from .text_processor import TextProcessor
from .visual_processor import VisualProcessor

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


class EmbeddingError(ProcessingError):
    """Embedding generation error."""


class StorageError(ProcessingError):
    """Storage operation error."""


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
        enhanced_mode_config: Optional[EnhancedModeConfig] = None,
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
        self.parser = DoclingParser(render_dpi=parser_config.get("render_dpi", 150))
        self.visual_processor = VisualProcessor(
            embedding_engine=embedding_engine, batch_size=visual_batch_size
        )
        self.text_processor = TextProcessor(
            embedding_engine=embedding_engine, batch_size=text_batch_size
        )

        mode = "enhanced" if enhanced_mode_config else "legacy"
        logger.info(
            f"Initialized DocumentProcessor ({mode} mode, "
            f"visual_batch={visual_batch_size}, text_batch={text_batch_size})"
        )

    def process_document(  # noqa: C901
        self,
        file_path: str,
        chunk_size_words: int = 250,
        chunk_overlap_words: int = 50,
        status_callback=None,
        project_id: str = "default",
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
                ".pdf": "Extracting text and images from PDF",
                ".docx": "Processing Word document",
                ".pptx": "Processing PowerPoint presentation",
                ".xlsx": "Processing Excel spreadsheet",
                ".mp3": "Transcribing audio with Whisper (this may take several minutes)",
                ".wav": "Transcribing audio with Whisper (this may take several minutes)",
                ".md": "Parsing Markdown document",
                ".html": "Parsing HTML document",
                ".png": "Processing image",
                ".jpg": "Processing image",
                ".jpeg": "Processing image",
            }

            parsing_stage = parsing_messages.get(file_ext, f"Processing {file_ext} file")

            # Stage 1: Parsing
            status = ProcessingStatus(
                doc_id="pending",
                filename=filename,
                status="parsing",
                progress=0.1,
                stage=parsing_stage,
            )
            self._update_status(status, status_callback)

            logger.info(f"Starting document processing: {filename}")
            print(f"DEBUG: DocumentProcessor.enhanced_mode_config = {self.enhanced_mode_config}")
            print(f"DEBUG: Calling parser.parse_document with config={self.enhanced_mode_config}")
            logger.info(f"DEBUG: enhanced_mode_config = {self.enhanced_mode_config}")

            parsed_doc = self.parser.parse_document(
                file_path=file_path,
                chunk_size_words=chunk_size_words,
                chunk_overlap_words=chunk_overlap_words,
                config=self.enhanced_mode_config,
            )

            doc_id = parsed_doc.doc_id
            total_pages = parsed_doc.num_pages

            logger.info(
                f"Parsed {filename}: {total_pages} pages, " f"{len(parsed_doc.text_chunks)} chunks"
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
                    elapsed_seconds=int(time.time() - start_time),
                )
                self._update_status(status, status_callback)

                # Create progress callback for visual processing
                def visual_progress_callback(pages_completed, total):
                    # Progress ranges from 0.3 to 0.6 (30% of total)
                    granular_progress = 0.3 + (pages_completed / total * 0.3)
                    batch_num = (pages_completed - 1) // self.visual_processor.batch_size + 1
                    total_batches = (
                        total + self.visual_processor.batch_size - 1
                    ) // self.visual_processor.batch_size

                    status = ProcessingStatus(
                        doc_id=doc_id,
                        filename=filename,
                        status="embedding_visual",
                        progress=granular_progress,
                        stage=f"Visual embeddings: {pages_completed}/{total} pages (batch {batch_num}/{total_batches})",
                        current_page=pages_completed,
                        total_pages=total,
                        elapsed_seconds=int(time.time() - start_time),
                    )
                    self._update_status(status, status_callback)

                visual_results = self.visual_processor.process_pages(
                    pages=parsed_doc.pages,
                    doc_id=doc_id,
                    progress_callback=visual_progress_callback,
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
                    elapsed_seconds=int(time.time() - start_time),
                )
                self._update_status(status, status_callback)

                # Create progress callback for text processing
                def text_progress_callback(chunks_completed, total):
                    # Progress ranges from 0.6 to 0.9 (30% of total)
                    granular_progress = 0.6 + (chunks_completed / total * 0.3)
                    batch_num = (chunks_completed - 1) // self.text_processor.batch_size + 1
                    total_batches = (
                        total + self.text_processor.batch_size - 1
                    ) // self.text_processor.batch_size

                    status = ProcessingStatus(
                        doc_id=doc_id,
                        filename=filename,
                        status="embedding_text",
                        progress=granular_progress,
                        stage=f"Text embeddings: {chunks_completed}/{total} chunks (batch {batch_num}/{total_batches})",
                        total_pages=total_pages,
                        elapsed_seconds=int(time.time() - start_time),
                    )
                    self._update_status(status, status_callback)

                text_results = self.text_processor.process_chunks(
                    chunks=parsed_doc.text_chunks,
                    doc_id=doc_id,
                    progress_callback=text_progress_callback,
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

                timestamp_count = sum(1 for c in parsed_doc.text_chunks if c.start_time is not None)
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
                    chunk.start_time is not None for chunk in parsed_doc.text_chunks
                )

                if has_timestamps:
                    try:
                        from src.config.processing_config import AsrConfig

                        from .vtt_generator import generate_vtt, save_vtt

                        logger.info(f"Generating VTT for audio file: {filename}")

                        # Load ASR config for caption splitting parameters
                        asr_config = AsrConfig.from_env()

                        # Pass pages to enable fine-grained caption extraction
                        # Pass asr_config to enable intelligent caption splitting
                        vtt_content = generate_vtt(
                            parsed_doc.text_chunks,
                            filename,
                            pages=parsed_doc.pages,
                            asr_config=asr_config,
                        )
                        vtt_path = save_vtt(doc_id, vtt_content)

                        # Store VTT path in metadata
                        parsed_doc.metadata["vtt_path"] = str(vtt_path)
                        parsed_doc.metadata["vtt_available"] = True

                        logger.info(f"Generated VTT: {vtt_path}")
                    except Exception as e:
                        logger.warning(f"VTT generation failed: {e}")
                        parsed_doc.metadata["vtt_available"] = False
                else:
                    logger.info(f"No chunks with timestamps in {filename}, skipping VTT generation")
                    parsed_doc.metadata["vtt_available"] = False

            # Stage 3.6: Markdown Generation (all documents with text)
            if parsed_doc.text_chunks:
                try:
                    from .markdown_utils import generate_markdown_with_frontmatter, save_markdown

                    logger.info(f"Generating markdown for document: {filename}")

                    # Prepare chunks for markdown generation
                    chunks_for_markdown = [
                        {"text_content": chunk.text} for chunk in parsed_doc.text_chunks
                    ]

                    markdown_content = generate_markdown_with_frontmatter(
                        chunks=chunks_for_markdown,
                        doc_metadata=parsed_doc.metadata,
                        filename=filename,
                        doc_id=doc_id,
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
                stage="Storing embeddings",
                total_pages=total_pages,
                elapsed_seconds=int(time.time() - start_time),
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
                pages=parsed_doc.pages,  # Wave 1: Pass pages for image paths
                structure=parsed_doc.structure,  # Pass structure object
                project_id=project_id,
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
                elapsed_seconds=elapsed,
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
                int(time.time() - start_time),
            )
            raise

        except EmbeddingError as e:
            logger.error(f"Embedding failed for {filename}: {e}")
            self._update_failure_status(
                doc_id or "unknown",
                filename,
                f"Embedding generation failed: {e}",
                status_callback,
                int(time.time() - start_time),
            )
            raise

        except StorageError as e:
            logger.error(f"Storage failed for {filename}: {e}")
            self._update_failure_status(
                doc_id or "unknown",
                filename,
                f"Storage failed: {e}",
                status_callback,
                int(time.time() - start_time),
            )
            raise

        except Exception as e:
            logger.error(f"Unexpected error processing {filename}: {e}", exc_info=True)
            self._update_failure_status(
                doc_id or "unknown",
                filename,
                f"Unexpected error: {e}",
                status_callback,
                int(time.time() - start_time),
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
        pages: Optional[List] = None,
        structure: Optional[Any] = None,
        project_id: str = "default",
    ) -> StorageConfirmation:
        """Store embeddings via the injected KojiClient.

        Args:
            doc_id: Document identifier.
            visual_results: List of VisualEmbeddingResult.
            text_results: List of TextEmbeddingResult.
            text_chunks: List of TextChunk objects.
            doc_metadata: Document metadata dict.
            filename: Original filename.
            file_path: Source file path.
            pages: Optional page objects (for image data).
            structure: Optional DocumentStructure.
            project_id: Project to assign the document to.

        Returns:
            StorageConfirmation with storage details.

        Raises:
            StorageError: If storage fails.
        """
        try:
            return self._store_koji(
                doc_id, visual_results, text_results, text_chunks,
                doc_metadata, filename, file_path, pages, structure,
                project_id=project_id,
            )
        except Exception as e:
            logger.error(f"Storage failed: {e}")
            raise StorageError(f"Failed to store embeddings: {e}") from e

    def _store_koji(
        self,
        doc_id: str,
        visual_results,
        text_results,
        text_chunks,
        doc_metadata: Dict[str, Any],
        filename: str,
        file_path: str,
        pages: Optional[List] = None,
        structure: Optional[Any] = None,
        project_id: str = "default",
    ) -> StorageConfirmation:
        """Store embeddings in Koji database.

        Creates a document record, then inserts page and chunk records
        with their embeddings as binary blobs.
        """
        import json

        file_ext = os.path.splitext(filename)[1].lstrip(".").lower()

        # Save album art for audio files (side effect, not storage-dependent)
        try:
            from src.processing.handlers import AlbumArtHandler
            AlbumArtHandler.save_album_art_if_present(doc_id, doc_metadata)
        except ImportError:
            pass

        # Create document record
        num_pages = len(visual_results) if visual_results else None
        markdown_content = doc_metadata.get("markdown")
        self.storage_client.create_document(
            doc_id=doc_id,
            filename=filename,
            format=file_ext,
            num_pages=num_pages,
            markdown=markdown_content,
            metadata=doc_metadata,
            project_id=project_id,
        )

        # Insert pages from visual results
        visual_ids = []
        visual_size = 0
        if visual_results:
            page_records = []
            for vr in visual_results:
                page_id = f"{doc_id}-page{vr.page_num:03d}"
                visual_ids.append(page_id)

                # Get embedding as bytes (ShikomiClient returns bytes,
                # ColPali returns np.ndarray — convert if needed)
                embedding_blob = self._to_embedding_blob(vr.embedding)

                # Get page image bytes if available
                image_bytes = None
                if pages and vr.page_num - 1 < len(pages):
                    page_obj = pages[vr.page_num - 1]
                    if hasattr(page_obj, "image") and page_obj.image is not None:
                        import io
                        buf = io.BytesIO()
                        page_obj.image.save(buf, format="PNG")
                        image_bytes = buf.getvalue()

                # Get structure for this page
                structure_dict = None
                if structure and hasattr(structure, "get_page_structure"):
                    structure_dict = structure.get_page_structure(vr.page_num)

                record = {
                    "id": page_id,
                    "doc_id": doc_id,
                    "page_num": vr.page_num,
                    "embedding": embedding_blob,
                    "image": image_bytes,
                    "structure": structure_dict,
                }
                if image_bytes:
                    visual_size += len(image_bytes)
                if embedding_blob:
                    visual_size += len(embedding_blob)
                page_records.append(record)

            self.storage_client.insert_pages(page_records)

        # Insert chunks from text results
        text_ids = []
        text_size = 0
        chunk_records: list = []
        if text_results:
            for tr in text_results:
                chunk_id = tr.chunk_id
                text_ids.append(chunk_id)

                embedding_blob = self._to_embedding_blob(tr.embedding)

                # Build context from text chunk metadata
                context_dict = None
                matching_chunks = [
                    c for c in (text_chunks or [])
                    if hasattr(c, "text") and c.text == tr.text
                ]
                if matching_chunks:
                    tc = matching_chunks[0]
                    context_dict = {}
                    if hasattr(tc, "parent_heading") and tc.parent_heading:
                        context_dict["parent_heading"] = tc.parent_heading
                    if hasattr(tc, "section_path") and tc.section_path:
                        context_dict["section_path"] = tc.section_path
                    if hasattr(tc, "element_type") and tc.element_type:
                        context_dict["element_type"] = tc.element_type

                record = {
                    "id": chunk_id,
                    "doc_id": doc_id,
                    "page_num": tr.page_num,
                    "text": tr.text,
                    "embedding": embedding_blob,
                    "context": context_dict if context_dict else None,
                    "word_count": len(tr.text.split()) if tr.text else 0,
                }

                # Audio timestamps
                if matching_chunks:
                    tc = matching_chunks[0]
                    if hasattr(tc, "start_time") and tc.start_time is not None:
                        record["start_time"] = tc.start_time
                    if hasattr(tc, "end_time") and tc.end_time is not None:
                        record["end_time"] = tc.end_time

                if embedding_blob:
                    text_size += len(embedding_blob)
                text_size += len(tr.text.encode()) if tr.text else 0
                chunk_records.append(record)

            self.storage_client.insert_chunks(chunk_records)

        # Detect and create document relations (non-blocking)
        try:
            from src.processing.relation_builder import RelationBuilder

            builder = RelationBuilder(storage_client=self.storage_client)
            created_relations = builder.build_relations(
                doc_id=doc_id,
                filename=filename,
                chunks=chunk_records,
                doc_metadata=doc_metadata,
                project_id=project_id,
            )
            if created_relations:
                logger.info(
                    f"relations_created: doc_id={doc_id} "
                    f"count={len(created_relations)} "
                    f"types={[r['relation_type'] for r in created_relations]}"
                )
        except Exception as exc:
            logger.warning(
                f"relation_building_failed: doc_id={doc_id} error={exc}"
            )

        return StorageConfirmation(
            doc_id=doc_id,
            visual_ids=visual_ids,
            text_ids=text_ids,
            total_size_bytes=visual_size + text_size,
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

    @staticmethod
    def _to_embedding_blob(embedding) -> Optional[bytes]:
        """Convert an embedding to bytes for Koji storage.

        Handles both numpy arrays (ColPali) and raw bytes (Shikomi).

        Args:
            embedding: numpy ndarray, bytes, or None.

        Returns:
            Packed binary blob or None.
        """
        if embedding is None:
            return None
        if isinstance(embedding, bytes):
            return embedding
        # numpy ndarray → pack as multi-vector blob
        try:
            import struct
            import numpy as np
            if isinstance(embedding, np.ndarray):
                if embedding.ndim == 2:
                    num_tokens, dim = embedding.shape
                    header = struct.pack("<II", num_tokens, dim)
                    data = embedding.astype(np.float32).tobytes()
                    return header + data
                elif embedding.ndim == 1:
                    # Single vector — wrap as 1-token multi-vector
                    dim = embedding.shape[0]
                    header = struct.pack("<II", 1, dim)
                    data = embedding.astype(np.float32).tobytes()
                    return header + data
        except ImportError:
            pass
        return None

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
        self, doc_id: str, filename: str, error_message: str, callback, elapsed_seconds: int
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
            elapsed_seconds=elapsed_seconds,
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

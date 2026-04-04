"""Main document processing coordinator.

Orchestrates the complete document processing pipeline by delegating
to ``shikomi.Ingester`` for parsing, chunking, text embedding, page
rendering, visual embedding, VTT, markdown, and relation detection.
This module handles artifact persistence and Koji storage.

Pipeline stages:
    1. Ingest via shikomi (parse -> chunk -> embed text/visual -> VTT -> markdown)
    2. Save artifacts to disk (page images, VTT, markdown, album art)
    3. Store results in Koji
"""

from __future__ import annotations

import io
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import structlog

from .result_mapper import map_chunk_records, map_document_record, map_page_records
from .shikomi_ingester import ShikomiIngester, StatusBridge

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Status and confirmation dataclasses (backward-compatible public API)
# ---------------------------------------------------------------------------


@dataclass
class ProcessingStatus:
    """Processing status for monitoring.

    Matches the ProcessingStatus structure used by the WebSocket
    broadcaster and status API.
    """

    doc_id: str
    filename: str
    status: str  # queued, parsing, chunking, embedding_text, embedding_visual, storing, completed, failed
    progress: float  # 0.0 to 1.0
    stage: str  # Human-readable stage description
    current_page: Optional[int] = None
    total_pages: Optional[int] = None
    elapsed_seconds: int = 0
    estimated_remaining_seconds: Optional[int] = None
    error_message: Optional[str] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )


@dataclass
class StorageConfirmation:
    """Storage confirmation result."""

    doc_id: str
    visual_ids: list
    text_ids: list
    total_size_bytes: int
    timestamp: str


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------


class ProcessingError(Exception):
    """Base processing error."""


class EmbeddingError(ProcessingError):
    """Embedding generation error."""


class StorageError(ProcessingError):
    """Storage operation error."""


# ---------------------------------------------------------------------------
# DocumentProcessor
# ---------------------------------------------------------------------------


class DocumentProcessor:
    """Main document processing coordinator.

    Delegates the text pipeline (parse, chunk, embed, VTT, markdown,
    relations) to ``ShikomiIngester`` and handles page rendering, visual
    embedding, and Koji storage directly.

    Args:
        ingester: Connected ``ShikomiIngester`` instance.
        storage_client: ``KojiClient`` instance for database storage.
    """

    def __init__(
        self,
        ingester: ShikomiIngester,
        storage_client: Any,
    ) -> None:
        self.ingester = ingester
        self.storage_client = storage_client

        logger.info("processor.initialized")

    # -- public API ----------------------------------------------------------

    def process_document(
        self,
        file_path: str,
        status_callback: Optional[Callable] = None,
        project_id: str = "default",
    ) -> StorageConfirmation:
        """Process a document through the complete pipeline.

        Args:
            file_path: Path to document file.
            status_callback: Optional callback receiving
                ``ProcessingStatus`` objects.
            project_id: Project to assign the document to.

        Returns:
            StorageConfirmation with storage details.

        Raises:
            ProcessingError: If processing fails at any stage.
        """
        start_time = time.time()
        path = Path(file_path)
        filename = path.name
        file_ext = path.suffix.lower()
        doc_id: Optional[str] = None

        try:
            # ---- Stage 1: Ingest via shikomi --------------------------------
            # Shikomi handles: parse -> chunk -> text embed -> render pages
            #   -> visual embed -> VTT -> markdown -> album art -> relations
            self._emit_status(
                "pending", filename, "processing", 0.02,
                "Preparing document",
                status_callback, start_time,
            )

            bridge = (
                StatusBridge(filename, status_callback, start_time)
                if status_callback is not None
                else None
            )
            result = self.ingester.process(file_path, status_bridge=bridge)
            doc_id = result.content_hash

            logger.info(
                "processor.ingest_complete",
                filename=filename,
                doc_id=doc_id,
                chunks=result.chunk_count,
                source_type=result.source_type,
                time_ms=result.processing_time_ms,
                pages=len(result.page_images) if result.page_images else 0,
            )

            # ---- Stage 2: Save page images to disk --------------------------
            page_image_bytes = result.page_images or []
            if page_image_bytes:
                self._save_page_images_from_bytes(doc_id, page_image_bytes)

            # ---- Stage 3: Save VTT / markdown / album art to disk -----------
            self._save_artifacts(doc_id, result, filename)

            # ---- Stage 4: Store in Koji -------------------------------------
            self._emit_status(
                doc_id, filename, "storing", 0.9,
                "Storing embeddings",
                status_callback, start_time,
            )

            confirmation = self._store_results(
                doc_id=doc_id,
                result=result,
                filename=filename,
                project_id=project_id,
                visual_embeddings=result.visual_embeddings,
                page_image_bytes=page_image_bytes,
            )

            # ---- Done -------------------------------------------------------
            elapsed = int(time.time() - start_time)
            self._emit_status(
                doc_id, filename, "completed", 1.0,
                "Processing complete",
                status_callback, start_time,
            )

            logger.info(
                "processor.complete",
                filename=filename,
                doc_id=doc_id,
                elapsed_s=elapsed,
                chunks=result.chunk_count,
                pages=len(page_image_bytes),
            )

            return confirmation

        except Exception as exc:
            logger.error(
                "processor.failed",
                filename=filename,
                error=str(exc),
                exc_info=True,
            )
            self._emit_status(
                doc_id or "unknown", filename, "failed", 0.0,
                "Processing failed",
                status_callback, start_time,
                error_message=str(exc),
            )
            if isinstance(exc, ProcessingError):
                raise
            raise ProcessingError(f"Processing failed: {exc}") from exc

    # -- artifact persistence ------------------------------------------------

    @staticmethod
    def _save_page_images_from_bytes(
        doc_id: str,
        page_image_bytes: List[bytes],
    ) -> None:
        """Save rendered page images and thumbnails to disk.

        Converts image bytes (from shikomi's ``IngestResult.page_images``)
        to PIL Images for thumbnail generation, then saves both the
        full-size image and thumbnail.

        Args:
            doc_id: Document identifier.
            page_image_bytes: List of PNG/JPEG bytes, one per page.
        """
        try:
            from PIL import Image

            from .image_utils import save_page_image

            for idx, img_bytes in enumerate(page_image_bytes):
                page_num = idx + 1
                try:
                    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                    save_page_image(image=img, doc_id=doc_id, page_num=page_num)
                except Exception as exc:
                    logger.warning(
                        "processor.page_image_save_failed",
                        doc_id=doc_id,
                        page_num=page_num,
                        error=str(exc),
                    )
        except ImportError:
            logger.warning("processor.image_utils_unavailable")

    @staticmethod
    def _save_artifacts(
        doc_id: str,
        result: Any,
        filename: str,
    ) -> None:
        """Save VTT, markdown, and album art to disk.

        Args:
            doc_id: Document identifier.
            result: ``IngestResult`` from shikomi.
            filename: Original filename.
        """
        # VTT (audio files)
        if result.vtt_content:
            try:
                vtt_dir = Path("data/vtt")
                vtt_dir.mkdir(parents=True, exist_ok=True)
                vtt_path = vtt_dir / f"{doc_id}.vtt"
                vtt_path.write_text(result.vtt_content, encoding="utf-8")
                result.metadata["vtt_path"] = str(vtt_path)
                result.metadata["vtt_available"] = True
                logger.info("processor.vtt_saved", path=str(vtt_path))
            except Exception as exc:
                logger.warning("processor.vtt_save_failed", error=str(exc))

        # Markdown
        if result.markdown_content:
            try:
                md_dir = Path("data/markdown")
                md_dir.mkdir(parents=True, exist_ok=True)
                md_path = md_dir / f"{doc_id}.md"
                md_path.write_text(result.markdown_content, encoding="utf-8")
                result.metadata["markdown_path"] = str(md_path)
                result.metadata["markdown_available"] = True
                logger.info("processor.markdown_saved", path=str(md_path))
            except Exception as exc:
                logger.warning("processor.markdown_save_failed", error=str(exc))

        # Album art (from shikomi's IngestResult)
        if result.album_art is not None:
            try:
                art_bytes, mime_type = result.album_art
                ext = "jpg" if "jpeg" in mime_type else mime_type.split("/")[-1]
                art_dir = Path("data/images") / doc_id
                art_dir.mkdir(parents=True, exist_ok=True)
                art_path = art_dir / f"cover.{ext}"
                art_path.write_bytes(art_bytes)
                result.metadata["album_art_path"] = str(art_path)
                logger.info(
                    "processor.album_art_saved",
                    path=str(art_path),
                    size_kb=len(art_bytes) // 1024,
                )
            except Exception as exc:
                logger.warning("processor.album_art_failed", error=str(exc))

    # -- Koji storage --------------------------------------------------------

    def _store_results(
        self,
        doc_id: str,
        result: Any,
        filename: str,
        project_id: str,
        visual_embeddings: Optional[list] = None,
        page_image_bytes: Optional[List[bytes]] = None,
    ) -> StorageConfirmation:
        """Map IngestResult to Koji records and store.

        Args:
            doc_id: Document identifier (content hash).
            result: ``IngestResult`` from shikomi.
            filename: Original filename.
            project_id: Project identifier.
            visual_embeddings: Optional list of ``MultiVectorEmbedding``.
            page_image_bytes: Optional PNG bytes per page.

        Returns:
            StorageConfirmation with storage details.

        Raises:
            StorageError: If storage fails.
        """
        try:
            num_pages = (
                len(visual_embeddings) if visual_embeddings
                else len(page_image_bytes) if page_image_bytes
                else None
            )

            # Document record
            doc_record = map_document_record(
                result, filename, project_id, num_pages=num_pages,
            )
            self.storage_client.create_document(**doc_record)

            # Page records (visual formats only)
            visual_ids: list = []
            visual_size = 0
            if visual_embeddings:
                page_records = map_page_records(
                    doc_id=doc_id,
                    visual_embeddings=visual_embeddings,
                    page_images=page_image_bytes,
                )
                self.storage_client.insert_pages(page_records)
                visual_ids = [r["id"] for r in page_records]
                visual_size = sum(
                    len(r.get("embedding", b"")) + len(r.get("image", b""))
                    for r in page_records
                )

            # Chunk records
            text_ids: list = []
            text_size = 0
            if result.chunks:
                chunk_records = map_chunk_records(doc_id, result)
                self.storage_client.insert_chunks(chunk_records)
                text_ids = [r["id"] for r in chunk_records]
                text_size = sum(
                    len(r.get("embedding", b"")) + len(r.get("text", "").encode())
                    for r in chunk_records
                )

            # Relations (already detected by shikomi ingester)
            if result.relations:
                for rel in result.relations:
                    try:
                        self.storage_client.create_relation(
                            src_doc_id=rel.get("src_doc_id", doc_id),
                            dst_doc_id=rel["dst_doc_id"],
                            relation_type=rel["relation_type"],
                            metadata=rel.get("metadata"),
                        )
                    except Exception as exc:
                        logger.warning(
                            "processor.relation_store_failed",
                            relation=rel,
                            error=str(exc),
                        )

                logger.info(
                    "processor.relations_stored",
                    doc_id=doc_id,
                    count=len(result.relations),
                )

            return StorageConfirmation(
                doc_id=doc_id,
                visual_ids=visual_ids,
                text_ids=text_ids,
                total_size_bytes=visual_size + text_size,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        except Exception as exc:
            raise StorageError(f"Failed to store results: {exc}") from exc

    # -- status helpers ------------------------------------------------------

    @staticmethod
    def _emit_status(
        doc_id: str,
        filename: str,
        status: str,
        progress: float,
        stage: str,
        callback: Optional[Callable],
        start_time: float,
        error_message: Optional[str] = None,
    ) -> None:
        """Emit a ProcessingStatus to the callback if provided."""
        if callback is None:
            return
        try:
            callback(ProcessingStatus(
                doc_id=doc_id,
                filename=filename,
                status=status,
                progress=progress,
                stage=stage,
                elapsed_seconds=int(time.time() - start_time),
                error_message=error_message,
            ))
        except Exception as exc:
            logger.warning("processor.status_callback_failed", error=str(exc))

    @staticmethod
    def _parsing_message(file_ext: str) -> str:
        """Return a user-friendly parsing stage message."""
        messages = {
            ".pdf": "Extracting text and images from PDF",
            ".docx": "Processing Word document",
            ".pptx": "Processing PowerPoint presentation",
            ".xlsx": "Processing Excel spreadsheet",
            ".mp3": "Transcribing audio (this may take several minutes)",
            ".wav": "Transcribing audio (this may take several minutes)",
            ".m4a": "Transcribing audio (this may take several minutes)",
            ".md": "Parsing Markdown document",
            ".html": "Parsing HTML document",
            ".png": "Processing image",
            ".jpg": "Processing image",
            ".jpeg": "Processing image",
        }
        return messages.get(file_ext, f"Processing {file_ext} file")

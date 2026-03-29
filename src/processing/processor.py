"""Main document processing coordinator.

Orchestrates the complete document processing pipeline by delegating
to ``shikomi.Ingester`` for parsing, chunking, text embedding, VTT,
markdown, and relation detection.  Page rendering and visual embedding
are handled directly since shikomi's page rendering is not yet
implemented.

Pipeline stages:
    1. Ingest via shikomi (parse -> chunk -> text embed -> VTT -> markdown)
    2. Render page images (PDF/image formats only)
    3. Visual embedding via ``ColNomicEngine.encode_images``
    4. Store results in Koji
"""

from __future__ import annotations

import io
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import structlog

from .result_mapper import map_chunk_records, map_document_record, map_page_records
from .shikomi_ingester import ShikomiIngester

logger = structlog.get_logger(__name__)

# Visual formats that have renderable pages
_VISUAL_FORMATS = {".pdf"}

# Image formats treated as single-page visual documents
_IMAGE_FORMATS = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}


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
            self._emit_status(
                "pending", filename, "parsing", 0.05,
                self._parsing_message(file_ext),
                status_callback, start_time,
            )

            result = self.ingester.process(file_path)
            doc_id = result.content_hash

            logger.info(
                "processor.ingest_complete",
                filename=filename,
                doc_id=doc_id,
                chunks=result.chunk_count,
                source_type=result.source_type,
                time_ms=result.processing_time_ms,
            )

            # ---- Stage 2: Render page images (visual formats only) ----------
            page_images: List[Any] = []  # PIL Image objects
            page_image_bytes: List[bytes] = []

            if file_ext in _VISUAL_FORMATS or file_ext in _IMAGE_FORMATS:
                self._emit_status(
                    doc_id, filename, "embedding_visual", 0.5,
                    "Rendering page images",
                    status_callback, start_time,
                )
                page_images = self._render_pages(file_path, file_ext)

                # Convert to PNG bytes for Koji storage
                for img in page_images:
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    page_image_bytes.append(buf.getvalue())

            # ---- Stage 3: Visual embeddings (if pages rendered) -------------
            visual_embeddings = None
            if page_images:
                self._emit_status(
                    doc_id, filename, "embedding_visual", 0.6,
                    f"Generating visual embeddings for {len(page_images)} pages",
                    status_callback, start_time,
                )
                try:
                    visual_embeddings = self.ingester._run_async(
                        self.ingester.engine.encode_images(page_images),
                    )
                except Exception as exc:
                    logger.warning(
                        "processor.visual_embedding_failed", error=str(exc),
                    )

            # ---- Stage 4: Save page images to disk --------------------------
            if page_images:
                self._save_page_images(doc_id, page_images)

            # ---- Stage 5: Save VTT / markdown / album art to disk -----------
            self._save_artifacts(doc_id, result, filename)

            # ---- Stage 6: Store in Koji -------------------------------------
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
                visual_embeddings=visual_embeddings,
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
                pages=len(page_images),
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

    # -- page rendering ------------------------------------------------------

    @staticmethod
    def _render_pages(
        file_path: str,
        file_ext: str,
    ) -> list:
        """Render file pages to PIL Images.

        Uses pypdfium2 for PDFs and PIL for image files.  Returns an
        empty list for formats without visual pages.

        Args:
            file_path: Path to the source file.
            file_ext: Lowercase file extension (e.g. ``".pdf"``).

        Returns:
            List of PIL Image objects, one per page.
        """
        from PIL import Image

        if file_ext in _IMAGE_FORMATS:
            try:
                img = Image.open(file_path).convert("RGB")
                return [img]
            except Exception as exc:
                logger.warning("processor.image_open_failed", error=str(exc))
                return []

        if file_ext == ".pdf":
            try:
                import pypdfium2 as pdfium

                pdf = pdfium.PdfDocument(file_path)
                images = []
                for page_idx in range(len(pdf)):
                    page = pdf[page_idx]
                    bitmap = page.render(scale=150 / 72)  # 150 DPI
                    img = bitmap.to_pil().convert("RGB")
                    images.append(img)
                pdf.close()
                return images
            except Exception as exc:
                logger.warning("processor.pdf_render_failed", error=str(exc))
                return []

        return []

    # -- artifact persistence ------------------------------------------------

    @staticmethod
    def _save_page_images(doc_id: str, page_images: list) -> None:
        """Save rendered page images and thumbnails to disk.

        Args:
            doc_id: Document identifier.
            page_images: List of PIL Image objects.
        """
        try:
            from .image_utils import save_page_image

            for idx, img in enumerate(page_images):
                page_num = idx + 1
                try:
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

        # Album art (audio files)
        try:
            from .handlers import AlbumArtHandler

            AlbumArtHandler.save_album_art_if_present(doc_id, result.metadata)
        except ImportError:
            pass

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
            num_pages = len(visual_embeddings) if visual_embeddings else None

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

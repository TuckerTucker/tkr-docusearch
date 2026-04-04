"""Synchronous wrapper around shikomi.Ingester.

Bridges the async ``shikomi.Ingester.process()`` method to a synchronous
``process()`` call using a private event loop.

Shikomi handles the complete ingest pipeline: parsing, chunking, text
embedding, page rendering, visual embedding, VTT/markdown generation,
album art extraction, and relation detection.  The ``renderer`` parameter
controls page rendering for visual formats (PDF, DOCX, PPTX, images).

Example:
    >>> from shikomi.parser.renderer import LibreOfficeRenderer
    >>> from processing.shikomi_ingester import ShikomiIngester
    >>> ingester = ShikomiIngester(
    ...     device="mps", quantization="4bit",
    ...     renderer=LibreOfficeRenderer(),
    ... )
    >>> ingester.connect()
    >>> result = ingester.process("document.pdf")
    >>> print(f"Produced {result.chunk_count} chunks")
    >>> ingester.close()
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any, Callable, Optional

import structlog

from shikomi import Ingester, IngestResult
from shikomi.config import ChunkConfig, RelationConfig, ValidationConfig
from shikomi.status import StatusManager as ShikomiStatusManager
from shikomi.status import calculate_progress, get_stage_description

if TYPE_CHECKING:
    from shikomi.embedding import ColNomicEngine
    from shikomi.parser.renderer import PageRenderer

    from .processor import ProcessingStatus

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# StatusBridge — forwards Shikomi's internal stage transitions to DocuSearch
# ---------------------------------------------------------------------------


class StatusBridge(ShikomiStatusManager):
    """Bridges Shikomi's internal status updates to a DocuSearch status callback.

    Subclasses Shikomi's ``StatusManager`` so it can be injected into
    ``Ingester._status_manager``.  Only the stages that Shikomi handles
    exclusively (parsing, chunking, text embedding) are forwarded; later
    stages (visual embedding, storing, completed, failed) are suppressed
    because ``DocumentProcessor`` emits its own updates for those.

    Args:
        filename: Original filename for display.
        status_callback: DocuSearch callback receiving ``ProcessingStatus``.
        start_time: ``time.time()`` epoch when processing started.
    """

    # Stages to forward — storing/completed/failed handled by DocumentProcessor
    _FORWARDED = frozenset({"parsing", "chunking", "embedding_text", "embedding_visual"})

    def __init__(
        self,
        filename: str,
        status_callback: Callable,
        start_time: float,
    ) -> None:
        super().__init__()
        self._filename = filename
        self._callback = status_callback
        self._start_time = start_time

    def create_status(
        self,
        doc_id: str,
        filename: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Any:
        """No-op — DocuSearch manages entry creation in the worker."""

    def update_status(
        self,
        doc_id: str,
        status: Any,
        progress: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        """Forward supported stage transitions to the DocuSearch callback."""
        status_value = status.value if hasattr(status, "value") else str(status)
        if status_value not in self._FORWARDED:
            return

        computed_progress = progress if progress is not None else calculate_progress(status, **kwargs)
        stage_desc = get_stage_description(status)

        total_chunks = kwargs.get("total_chunks")
        if total_chunks and status_value == "embedding_text":
            stage_desc = f"Generating text embeddings ({total_chunks} chunks)"

        from .processor import ProcessingStatus

        self._callback(
            ProcessingStatus(
                doc_id=doc_id,
                filename=self._filename,
                status=status_value,
                progress=computed_progress,
                stage=stage_desc,
                elapsed_seconds=int(time.time() - self._start_time),
            )
        )

    def mark_completed(self, doc_id: str, **kwargs: Any) -> None:
        """No-op — DocuSearch handles completion."""

    def mark_failed(self, doc_id: str, error: str) -> None:
        """No-op — DocuSearch handles failure."""


class ShikomiIngester:
    """Synchronous wrapper around shikomi's async Ingester.

    Creates a ``shikomi.Ingester`` with the provided configuration and
    exposes a sync ``process()`` method that bridges to the async pipeline
    via a dedicated event loop. The loop is private to this instance,
    making it safe to call from ``ThreadPoolExecutor`` workers.

    The ``engine`` property exposes the underlying ``ColNomicEngine`` so
    that ``DocumentProcessor`` and ``QueryEngine`` can share the loaded
    model for visual embedding and query embedding.

    Args:
        device: Compute device (``mps``, ``cuda``, ``cpu``).
        quantization: Model quantization (``4bit``, ``8bit``, ``fp16``).
        chunk_config: Chunking configuration.
        validation_config: File validation configuration.
        relation_config: Relation detection configuration.
        db: Storage backend for relation building (KojiClient).
        generate_vtt: Whether to generate WebVTT for audio files.
        generate_markdown: Whether to generate markdown export.
        enable_visual_embeddings: Whether to generate visual embeddings.
        renderer: Page renderer for visual embedding of documents/images.
        engine: Optional pre-loaded ColNomicEngine for DI/testing.
    """

    def __init__(
        self,
        device: str = "mps",
        quantization: str = "4bit",
        chunk_config: Optional[ChunkConfig] = None,
        validation_config: Optional[ValidationConfig] = None,
        relation_config: Optional[RelationConfig] = None,
        db: Optional[Any] = None,
        generate_vtt: bool = True,
        generate_markdown: bool = True,
        enable_visual_embeddings: bool = True,
        *,
        renderer: Optional[PageRenderer] = None,
        engine: Optional[ColNomicEngine] = None,
    ) -> None:
        self._device = device
        self._quantization = quantization
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        self._ingester = Ingester(
            device=device,
            quantization=quantization,
            chunk_config=chunk_config,
            enable_visual_embeddings=enable_visual_embeddings,
            validation_config=validation_config,
            relation_config=relation_config,
            db=db,
            generate_vtt=generate_vtt,
            generate_markdown=generate_markdown,
            renderer=renderer,
            engine=engine,
        )

    # -- lifecycle -------------------------------------------------------------

    def connect(self) -> None:
        """Initialize the private event loop.

        Idempotent -- safe to call multiple times. The ``shikomi.Ingester``
        is created eagerly in ``__init__``; engine loading is lazy and
        handled internally by shikomi on first use.
        """
        if self._loop is not None:
            return

        self._loop = asyncio.new_event_loop()

        logger.info(
            "shikomi_ingester.connected",
            device=self._device,
            quantization=self._quantization,
        )

    def close(self) -> None:
        """Release the event loop and clean up resources."""
        if self._loop is not None:
            self._loop.close()
            self._loop = None
        logger.info("shikomi_ingester.closed")

    def health_check(self) -> dict[str, Any]:
        """Return ingester health status.

        Returns:
            Dictionary containing connection status, device, and
            quantization settings.
        """
        return {
            "connected": self._loop is not None,
            "device": self._device,
            "quantization": self._quantization,
            "mode": "shikomi_ingester",
        }

    # -- public API ------------------------------------------------------------

    @property
    def engine(self) -> ColNomicEngine:
        """Expose the underlying ColNomicEngine.

        Allows ``DocumentProcessor`` and ``QueryEngine`` to share the
        loaded model for visual embedding and query embedding without
        loading a second copy.

        Returns:
            The ``ColNomicEngine`` instance from the wrapped Ingester.
        """
        return self._ingester.engine

    def process(
        self,
        file_path: str,
        status_bridge: Optional[StatusBridge] = None,
    ) -> IngestResult:
        """Process a file through the full ingestion pipeline synchronously.

        Delegates to ``shikomi.Ingester.process()`` (async) and bridges
        the result back via the private event loop.

        Args:
            file_path: Path to the file to ingest.
            status_bridge: Optional ``StatusBridge`` for forwarding
                Shikomi's internal stage transitions to the UI.

        Returns:
            ``IngestResult`` containing chunks, embeddings, metadata,
            and processing statistics.

        Raises:
            RuntimeError: If ``connect()`` has not been called.
            FileNotFoundError: If the file does not exist.
            ValueError: If the file format is unsupported or validation fails.
        """
        self._require_connected()

        if status_bridge is not None:
            self._ingester._status_manager = status_bridge

        try:
            logger.info("shikomi_ingester.process_start", file_path=file_path)
            result = self._run_async(self._ingester.process(file_path))
            logger.info(
                "shikomi_ingester.process_complete",
                file_path=file_path,
                chunk_count=result.chunk_count,
                processing_time_ms=result.processing_time_ms,
            )
            return result
        finally:
            self._ingester._status_manager = None

    # -- internal helpers ------------------------------------------------------

    def _require_connected(self) -> None:
        """Raise if the event loop has not been initialized."""
        if self._loop is None:
            raise RuntimeError(
                "ShikomiIngester is not connected. Call connect() first."
            )

    def _run_async(self, coro: Any) -> Any:
        """Run an async coroutine on the private event loop.

        Safe to call from ``ThreadPoolExecutor`` workers because the loop
        is private to this instance and not shared with FastAPI.

        If the loop is in a broken state (e.g. after a prior timeout or
        cancellation), it is replaced with a fresh loop so that
        subsequent calls can proceed.

        Args:
            coro: Awaitable coroutine to execute.

        Returns:
            The coroutine's return value.
        """
        try:
            return self._loop.run_until_complete(coro)
        except RuntimeError as exc:
            if "already running" in str(exc) or self._loop.is_closed():
                logger.warning(
                    "shikomi_ingester.loop_reset",
                    reason=str(exc),
                )
                self._loop = asyncio.new_event_loop()
                return self._loop.run_until_complete(coro)
            raise

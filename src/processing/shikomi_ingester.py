"""Synchronous wrapper around shikomi.Ingester.

Bridges the async ``shikomi.Ingester.process()`` method to a synchronous
``process()`` call using a private event loop. Follows the same pattern
as ``InProcessEmbeddingEngine`` in ``src/embeddings/in_process_engine.py``.

This allows ``DocumentProcessor`` and other sync callers to drive the
full ingestion pipeline (parse -> chunk -> embed) without needing to
manage async contexts themselves.

Example:
    >>> from processing.shikomi_ingester import ShikomiIngester
    >>> ingester = ShikomiIngester(device="mps", quantization="4bit")
    >>> ingester.connect()
    >>> result = ingester.process("document.pdf")
    >>> print(f"Produced {result.chunk_count} chunks")
    >>> ingester.close()
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Optional

import structlog

from shikomi import Ingester, IngestResult
from shikomi.config import ChunkConfig, RelationConfig, ValidationConfig

if TYPE_CHECKING:
    from shikomi.embedding import ColNomicEngine

logger = structlog.get_logger(__name__)


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
        *,
        engine: Optional[ColNomicEngine] = None,
    ) -> None:
        self._device = device
        self._quantization = quantization
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        self._ingester = Ingester(
            device=device,
            quantization=quantization,
            chunk_config=chunk_config,
            validation_config=validation_config,
            relation_config=relation_config,
            db=db,
            generate_vtt=generate_vtt,
            generate_markdown=generate_markdown,
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

    def process(self, file_path: str) -> IngestResult:
        """Process a file through the full ingestion pipeline synchronously.

        Delegates to ``shikomi.Ingester.process()`` (async) and bridges
        the result back via the private event loop.

        Args:
            file_path: Path to the file to ingest.

        Returns:
            ``IngestResult`` containing chunks, embeddings, metadata,
            and processing statistics.

        Raises:
            RuntimeError: If ``connect()`` has not been called.
            FileNotFoundError: If the file does not exist.
            ValueError: If the file format is unsupported or validation fails.
        """
        self._require_connected()

        logger.info("shikomi_ingester.process_start", file_path=file_path)
        result = self._run_async(self._ingester.process(file_path))
        logger.info(
            "shikomi_ingester.process_complete",
            file_path=file_path,
            chunk_count=result.chunk_count,
            processing_time_ms=result.processing_time_ms,
        )

        return result

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

        Args:
            coro: Awaitable coroutine to execute.

        Returns:
            The coroutine's return value.
        """
        return self._loop.run_until_complete(coro)

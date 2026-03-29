"""In-process embedding engine using shikomi-ingest ColNomicEngine.

Drop-in replacement for ShikomiClient that runs embeddings locally
instead of calling a remote gRPC service. Provides the same 3-method
interface: ``embed_images``, ``embed_texts``, ``embed_query``.
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

import structlog
from PIL import Image

logger = structlog.get_logger(__name__)


class InProcessEmbeddingEngine:
    """In-process embedding engine using ColNomicEngine.

    Wraps shikomi-ingest's ``ColNomicEngine`` to provide the same interface
    as ``ShikomiClient``, allowing drop-in replacement throughout DocuSearch.

    ColNomicEngine methods are async; this wrapper bridges them to sync
    using a dedicated event loop that is safe to call from
    ``ThreadPoolExecutor`` workers.

    Args:
        device: Compute device (``mps``, ``cuda``, ``cpu``).
        quantization: Model quantization (``4bit``, ``8bit``, ``fp16``).
        engine: Optional pre-configured ColNomicEngine for DI/testing.
    """

    def __init__(
        self,
        device: str = "mps",
        quantization: str = "4bit",
        *,
        engine: Optional[Any] = None,
    ) -> None:
        self._device = device
        self._quantization = quantization
        self._engine = engine
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    # -- lifecycle (matches ShikomiClient contract) --------------------------

    def connect(self) -> None:
        """Initialize the engine and create a private event loop.

        Idempotent — safe to call multiple times.
        """
        if self._loop is not None:
            return

        self._loop = asyncio.new_event_loop()

        if self._engine is None:
            from shikomi_ingest import ColNomicEngine

            self._engine = ColNomicEngine(
                device=self._device,
                quantization=self._quantization,
            )

        logger.info(
            "in_process_engine.connected",
            device=self._device,
            quantization=self._quantization,
        )

    def close(self) -> None:
        """Release resources."""
        if self._loop is not None:
            self._loop.close()
            self._loop = None
        self._engine = None
        logger.info("in_process_engine.closed")

    def health_check(self) -> dict[str, Any]:
        """Return engine health status."""
        return {
            "connected": self._engine is not None,
            "model": "colnomic-embed-multimodal-7b",
            "device": self._device,
            "quantization": self._quantization,
            "model_loaded": self._engine is not None,
            "mode": "in_process",
        }

    # -- embedding methods (match ShikomiClient signatures) ------------------

    def embed_images(
        self,
        images: list[Image.Image],
        batch_size: int = 1,
    ) -> list[bytes]:
        """Embed page images, returning packed binary blobs.

        Args:
            images: List of PIL Image objects.
            batch_size: Ignored (ColNomicEngine batches internally).

        Returns:
            List of packed binary blobs in Koji format.
        """
        if not images:
            return []
        self._require_connected()

        embeddings = self._run_async(self._engine.encode_images(images))
        blobs = [emb.to_blob() for emb in embeddings]

        logger.debug("in_process_engine.images_embedded", count=len(images))
        return blobs

    def embed_texts(
        self,
        texts: list[str],
        batch_size: int = 8,
    ) -> list[bytes]:
        """Embed text chunks, returning packed binary blobs.

        Args:
            texts: List of text strings.
            batch_size: Ignored (ColNomicEngine batches internally).

        Returns:
            List of packed binary blobs in Koji format.
        """
        if not texts:
            return []
        self._require_connected()

        embeddings = self._run_async(self._engine.encode_documents(texts))
        blobs = [emb.to_blob() for emb in embeddings]

        logger.debug("in_process_engine.texts_embedded", count=len(texts))
        return blobs

    def embed_query(self, query: str) -> list[list[float]]:
        """Embed a search query, returning nested float lists.

        Returns ``list[list[float]]`` for direct use with Koji's
        ``<~>`` MaxSim operator.

        Args:
            query: Search query string.

        Returns:
            Multi-vector embedding as nested list of floats.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        self._require_connected()

        embeddings = self._run_async(self._engine.encode_queries([query]))
        result: list[list[float]] = embeddings[0].data.tolist()

        logger.debug(
            "in_process_engine.query_embedded",
            query_len=len(query),
            num_tokens=len(result),
        )
        return result

    # -- internal helpers ----------------------------------------------------

    def _require_connected(self) -> None:
        """Raise if the engine is not connected."""
        if self._engine is None or self._loop is None:
            raise RuntimeError(
                "InProcessEmbeddingEngine is not connected. "
                "Call connect() first."
            )

    def _run_async(self, coro: Any) -> Any:
        """Run an async coroutine on the private event loop.

        Safe to call from ThreadPoolExecutor workers because the loop
        is private to this instance and not shared with FastAPI.
        """
        return self._loop.run_until_complete(coro)

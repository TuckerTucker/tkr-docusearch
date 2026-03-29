"""Query embedding engine for search.

Drop-in replacement for ``InProcessEmbeddingEngine`` and ``ShikomiClient``
that provides the ``embed_query()`` method needed by ``KojiSearch``.  Wraps
``shikomi.ColNomicEngine`` with the same async-to-sync bridging pattern used
throughout the embeddings package.

Supports engine injection so a single ``ColNomicEngine`` instance can be
shared with ``ShikomiIngester`` -- avoiding loading the model twice.

Example:
    >>> from processing.shikomi_ingester import ShikomiIngester
    >>> ingester = ShikomiIngester(device="mps")
    >>> ingester.connect()
    >>> qe = QueryEngine(engine=ingester.engine)
    >>> qe.connect()
    >>> vectors = qe.embed_query("what is the revenue for Q3?")
    >>> qe.close()
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Optional

import structlog

if TYPE_CHECKING:
    from shikomi.embedding import ColNomicEngine

logger = structlog.get_logger(__name__)


class QueryEngine:
    """Sync query embedding engine using ColNomicEngine.

    Wraps ``shikomi.ColNomicEngine.encode_queries`` to provide the same
    ``embed_query`` interface that ``KojiSearch`` expects.  Bridges async
    calls to sync using a dedicated event loop that is safe to call from
    ``ThreadPoolExecutor`` workers.

    Args:
        engine: Optional pre-loaded ``ColNomicEngine`` for sharing with
            ``ShikomiIngester``.  When provided, ``close()`` will not
            release the engine -- the caller retains ownership.
        device: Compute device (``mps``, ``cuda``, ``cpu``).
            Only used when *engine* is ``None``.
        quantization: Model quantization (``4bit``, ``8bit``, ``fp16``).
            Only used when *engine* is ``None``.
    """

    def __init__(
        self,
        engine: Optional[ColNomicEngine] = None,
        device: str = "mps",
        quantization: str = "4bit",
    ) -> None:
        self._device = device
        self._quantization = quantization
        self._engine: Optional[ColNomicEngine] = engine
        self._engine_injected: bool = engine is not None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    # -- lifecycle -------------------------------------------------------------

    def connect(self) -> None:
        """Initialize the engine and create a private event loop.

        Creates a ``ColNomicEngine`` if one was not injected at
        construction time.  Idempotent -- safe to call multiple times.
        """
        if self._loop is not None:
            return

        self._loop = asyncio.new_event_loop()

        if self._engine is None:
            from shikomi.embedding import ColNomicEngine

            self._engine = ColNomicEngine(
                device=self._device,
                quantization=self._quantization,
            )

        logger.info(
            "query_engine.connected",
            device=self._device,
            quantization=self._quantization,
            engine_injected=self._engine_injected,
        )

    def close(self) -> None:
        """Release resources.

        Closes the private event loop.  If the engine was injected at
        construction time the caller retains ownership and the engine
        reference is preserved.  If the engine was created internally it
        is released.
        """
        if self._loop is not None:
            self._loop.close()
            self._loop = None

        if not self._engine_injected:
            self._engine = None

        logger.info("query_engine.closed")

    def health_check(self) -> dict[str, Any]:
        """Return engine health status.

        Returns:
            Dictionary with ``connected``, ``model``, ``device``,
            ``quantization``, and ``mode`` fields.
        """
        return {
            "connected": self._engine is not None and self._loop is not None,
            "model": "colnomic-embed-multimodal-7b",
            "device": self._device,
            "quantization": self._quantization,
            "mode": "query_engine",
        }

    # -- embedding method ------------------------------------------------------

    def embed_query(self, query: str) -> list[list[float]]:
        """Embed a search query, returning nested float lists.

        Returns ``list[list[float]]`` for direct use with Koji's
        ``<~>`` MaxSim operator.

        Args:
            query: Search query string.

        Returns:
            Multi-vector embedding as nested list of floats.

        Raises:
            ValueError: If *query* is empty or whitespace-only.
            RuntimeError: If the engine is not connected.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        self._require_connected()

        embeddings = self._run_async(self._engine.encode_queries([query]))
        result: list[list[float]] = embeddings[0].data.tolist()

        logger.debug(
            "query_engine.query_embedded",
            query_len=len(query),
            num_tokens=len(result),
        )
        return result

    # -- internal helpers ------------------------------------------------------

    def _require_connected(self) -> None:
        """Raise if the engine is not connected."""
        if self._engine is None or self._loop is None:
            raise RuntimeError(
                "QueryEngine is not connected. Call connect() first."
            )

    def _run_async(self, coro: Any) -> Any:
        """Run an async coroutine on the private event loop.

        Safe to call from ``ThreadPoolExecutor`` workers because the
        loop is private to this instance and not shared with FastAPI.
        """
        return self._loop.run_until_complete(coro)

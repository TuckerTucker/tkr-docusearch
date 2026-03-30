"""
HTTP search client that proxies search requests to the worker API.

Provides the same ``search()`` interface that ``ContextBuilder`` expects,
but delegates to the worker API on port 8002 instead of loading the
embedding model in-process.
"""

from typing import Any, Dict, Optional

import httpx
import structlog

logger = structlog.get_logger(__name__)

# Map ContextBuilder search modes to worker API search modes
_MODE_MAP = {
    "hybrid": "hybrid",
    "visual_only": "visual",
    "text_only": "text",
    # Also accept the API-form values directly
    "visual": "visual",
    "text": "text",
}


class HttpSearchClient:
    """Search client that calls the worker API over HTTP.

    Drop-in replacement for ``KojiSearch`` as far as ``ContextBuilder``
    is concerned — implements the same ``search()`` method signature
    and return format.

    Args:
        worker_url: Base URL of the worker API (default ``http://localhost:8002``).
        timeout: HTTP request timeout in seconds.
    """

    def __init__(
        self,
        worker_url: str = "http://localhost:8002",
        timeout: float = 30.0,
    ) -> None:
        self._worker_url = worker_url.rstrip("/")
        self._timeout = timeout

    def search(
        self,
        query: str,
        n_results: Optional[int] = None,
        search_mode: str = "hybrid",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute search via the worker API.

        Args:
            query: Search query string.
            n_results: Maximum number of results to return.
            search_mode: One of ``hybrid``, ``visual_only``, ``text_only``,
                ``visual``, or ``text``.

        Returns:
            Dict with ``results`` list and ``total_time_ms``, matching
            the format that ``ContextBuilder`` expects.
        """
        api_mode = _MODE_MAP.get(search_mode, "hybrid")

        payload: Dict[str, Any] = {
            "query": query,
            "search_mode": api_mode,
        }
        if n_results is not None:
            payload["n_results"] = n_results

        logger.info(
            "http_search_client.search",
            query_length=len(query),
            n_results=n_results,
            search_mode=api_mode,
            worker_url=self._worker_url,
        )

        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(
                f"{self._worker_url}/search",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        # Normalize: worker returns "page_num", ContextBuilder expects "page"
        results = []
        for result in data.get("results", []):
            result["page"] = result.get("page_num", result.get("page"))
            results.append(result)

        logger.info(
            "http_search_client.search.done",
            num_results=len(results),
            search_time_ms=data.get("search_time_ms", 0),
        )

        return {
            "results": results,
            "total_time_ms": data.get("search_time_ms", 0),
        }

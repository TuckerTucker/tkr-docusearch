"""
Koji SQL search engine for DocuSearch.

This module replaces the two-stage custom Python search pipeline with
direct Koji SQL queries using the ``<~>`` MaxSim operator for multi-vector
similarity. It eliminates ~500 lines of custom retrieval, re-ranking,
and merging code.

The result format matches the existing ``SearchEngine.search()`` contract
for drop-in replacement.
"""

from __future__ import annotations

import time
from typing import Any, Literal, Optional

import structlog

logger = structlog.get_logger(__name__)


class KojiSearch:
    """Semantic search via Koji SQL with MaxSim operator.

    Args:
        koji_client: KojiClient instance for database queries.
        shikomi_client: ShikomiClient instance for query embedding.
    """

    def __init__(self, koji_client, shikomi_client) -> None:
        self._koji = koji_client
        self._shikomi = shikomi_client

        self._stats: dict[str, Any] = {
            "total_queries": 0,
            "total_times": [],
        }

        logger.info("koji_search.initialized")

    # -- public API ----------------------------------------------------------

    def search(
        self,
        query: str,
        n_results: int | None = None,
        search_mode: Literal["hybrid", "visual_only", "text_only"] = "hybrid",
        filters: dict[str, Any] | None = None,
        enable_reranking: bool = True,
        rerank_candidates: int | None = None,
    ) -> dict[str, Any]:
        """Execute semantic search.

        Signature matches the existing ``SearchEngine.search()`` for
        drop-in replacement. ``enable_reranking`` and ``rerank_candidates``
        are accepted but ignored — Koji handles scoring in a single pass.

        Args:
            query: Natural language search query.
            n_results: Number of results to return (default 10).
            search_mode: ``"hybrid"``, ``"visual_only"``, or ``"text_only"``.
            filters: Metadata filters (reserved for future use).
            enable_reranking: Ignored — no two-stage pipeline.
            rerank_candidates: Ignored — no two-stage pipeline.

        Returns:
            Search response dict matching the existing contract.

        Raises:
            ValueError: If query is empty or search_mode is invalid.
        """
        if not query or not query.strip():
            raise ValueError("Query must not be empty")

        if search_mode not in ("hybrid", "visual_only", "text_only"):
            raise ValueError(
                f"search_mode must be 'hybrid', 'visual_only', or 'text_only', "
                f"got '{search_mode}'"
            )

        n_results = n_results or 10

        dispatch = {
            "hybrid": self.hybrid_search,
            "visual_only": self.visual_search,
            "text_only": self.text_search,
        }
        return dispatch[search_mode](query, n_results)

    def text_search(self, query: str, n_results: int = 10) -> dict[str, Any]:
        """Search text chunks by semantic similarity.

        Args:
            query: Search query.
            n_results: Maximum results.

        Returns:
            Search response dict.
        """
        start = time.perf_counter()

        query_emb = self._shikomi.embed_query(query)

        result = self._koji.query(
            """SELECT c.id, c.doc_id, c.page_num, c.text, c.context,
                      d.filename, d.format, _distance
               FROM chunks c
               JOIN documents d ON c.doc_id = d.doc_id
               WHERE c.embedding <~> $1
               LIMIT $2""",
            [query_emb, n_results],
        )

        elapsed_ms = (time.perf_counter() - start) * 1000
        results = self._format_chunk_results(result)
        self._record_query(elapsed_ms)

        return self._build_response(results, query, "text_only", elapsed_ms)

    def visual_search(self, query: str, n_results: int = 10) -> dict[str, Any]:
        """Search page images by visual similarity.

        Args:
            query: Search query.
            n_results: Maximum results.

        Returns:
            Search response dict.
        """
        start = time.perf_counter()

        query_emb = self._shikomi.embed_query(query)

        result = self._koji.query(
            """SELECT p.id, p.doc_id, p.page_num, p.structure,
                      d.filename, d.format, _distance
               FROM pages p
               JOIN documents d ON p.doc_id = d.doc_id
               WHERE p.embedding <~> $1
               LIMIT $2""",
            [query_emb, n_results],
        )

        elapsed_ms = (time.perf_counter() - start) * 1000
        results = self._format_page_results(result)
        self._record_query(elapsed_ms)

        return self._build_response(results, query, "visual_only", elapsed_ms)

    def hybrid_search(self, query: str, n_results: int = 10) -> dict[str, Any]:
        """Search across both pages and chunks, merging results.

        Runs two separate vector searches (Koji ``<~>`` doesn't support CTEs)
        and merges results in Python, keeping the best score per
        ``(doc_id, page_num)`` pair.

        Args:
            query: Search query.
            n_results: Maximum results.

        Returns:
            Search response dict.
        """
        start = time.perf_counter()

        query_emb = self._shikomi.embed_query(query)
        candidates = n_results * 5

        page_hits = self._koji.query(
            """SELECT doc_id, page_num, _distance
               FROM pages WHERE embedding <~> $1 LIMIT $2""",
            [query_emb, candidates],
        )

        chunk_hits = self._koji.query(
            """SELECT doc_id, page_num, _distance
               FROM chunks WHERE embedding <~> $1 LIMIT $2""",
            [query_emb, candidates],
        )

        # Merge in Python: best score per (doc_id, page_num), track source
        merged: dict[tuple[str, int], tuple[float, str]] = {}

        for rows, source in [(page_hits, "visual"), (chunk_hits, "text")]:
            d = rows.to_pydict()
            for i in range(rows.num_rows):
                key = (d["doc_id"][i], d["page_num"][i])
                dist = d["_distance"][i]
                if key not in merged or dist < merged[key][0]:
                    merged[key] = (dist, source)

        # Sort by distance, take top n_results
        ranked = sorted(merged.items(), key=lambda item: item[1][0])[:n_results]

        # Fetch document metadata for the result doc_ids
        result_doc_ids = list({doc_id for (doc_id, _), _ in ranked})
        doc_meta: dict[str, dict[str, str]] = {}
        if result_doc_ids:
            placeholders = ", ".join(f"${i+1}" for i in range(len(result_doc_ids)))
            docs = self._koji.query(
                f"SELECT doc_id, filename, format FROM documents "
                f"WHERE doc_id IN ({placeholders})",
                result_doc_ids,
            )
            d = docs.to_pydict()
            for i in range(docs.num_rows):
                doc_meta[d["doc_id"][i]] = {
                    "filename": d["filename"][i],
                    "format": d["format"][i],
                }

        # Build result dicts
        results = []
        for (doc_id, page_num), (dist, source) in ranked:
            meta = doc_meta.get(doc_id, {})
            results.append({
                "doc_id": doc_id,
                "chunk_id": None,
                "page_num": page_num,
                "score": self._distance_to_score(dist),
                "text": "",
                "metadata": {
                    "filename": meta.get("filename", ""),
                    "format": meta.get("format", ""),
                    "source": source,
                },
            })

        elapsed_ms = (time.perf_counter() - start) * 1000
        self._record_query(elapsed_ms)

        return self._build_response(results, query, "hybrid", elapsed_ms)

    def get_search_stats(self) -> dict[str, Any]:
        """Get search performance statistics.

        Returns:
            Stats dict matching the existing ``SearchEngine.get_search_stats()`` contract.
        """
        if self._stats["total_queries"] == 0:
            return {
                "total_queries": 0,
                "avg_stage1_ms": 0.0,
                "avg_stage2_ms": 0.0,
                "avg_total_ms": 0.0,
                "p95_total_ms": 0.0,
            }

        times = self._stats["total_times"]
        sorted_times = sorted(times)
        p95_idx = min(int(len(sorted_times) * 0.95), len(sorted_times) - 1)

        return {
            "total_queries": self._stats["total_queries"],
            "avg_stage1_ms": sum(times) / len(times),  # single stage
            "avg_stage2_ms": 0.0,  # no re-ranking stage
            "avg_total_ms": sum(times) / len(times),
            "p95_total_ms": sorted_times[p95_idx],
        }

    # -- result formatting ---------------------------------------------------

    @staticmethod
    def _distance_to_score(distance: float) -> float:
        """Convert Koji distance to a 0-1 similarity score.

        Lower distance means more similar. We use ``1 / (1 + distance)``
        which maps [0, inf) → (0, 1].

        Args:
            distance: Koji ``_distance`` value.

        Returns:
            Normalized similarity score.
        """
        return 1.0 / (1.0 + distance) if distance is not None else 0.0

    def _format_chunk_results(self, result) -> list[dict[str, Any]]:
        """Convert PyArrow chunk results to result dicts."""
        import json

        rows = result.to_pydict()
        out = []
        for i in range(result.num_rows):
            context = rows.get("context", [None] * result.num_rows)[i]
            if context and isinstance(context, str):
                try:
                    context = json.loads(context)
                except (json.JSONDecodeError, TypeError):
                    pass

            out.append({
                "doc_id": rows["doc_id"][i],
                "chunk_id": rows["id"][i],
                "page_num": rows["page_num"][i],
                "score": self._distance_to_score(rows["_distance"][i]),
                "text": rows["text"][i],
                "metadata": {
                    "filename": rows["filename"][i],
                    "format": rows["format"][i],
                    "context": context,
                    "source": "text",
                },
            })
        return out

    def _format_page_results(self, result) -> list[dict[str, Any]]:
        """Convert PyArrow page results to result dicts."""
        import json

        rows = result.to_pydict()
        out = []
        for i in range(result.num_rows):
            structure = rows.get("structure", [None] * result.num_rows)[i]
            if structure and isinstance(structure, str):
                try:
                    structure = json.loads(structure)
                except (json.JSONDecodeError, TypeError):
                    pass

            out.append({
                "doc_id": rows["doc_id"][i],
                "chunk_id": None,
                "page_num": rows["page_num"][i],
                "score": self._distance_to_score(rows["_distance"][i]),
                "text": "",
                "metadata": {
                    "filename": rows["filename"][i],
                    "format": rows["format"][i],
                    "structure": structure,
                    "source": "visual",
                },
            })
        return out

    def _format_hybrid_results(self, result) -> list[dict[str, Any]]:
        """Convert PyArrow hybrid results to result dicts."""
        rows = result.to_pydict()
        out = []
        for i in range(result.num_rows):
            out.append({
                "doc_id": rows["doc_id"][i],
                "chunk_id": None,
                "page_num": rows["page_num"][i],
                "score": self._distance_to_score(rows["dist"][i]),
                "text": "",
                "metadata": {
                    "filename": rows["filename"][i],
                    "format": rows["format"][i],
                    "source": rows["source"][i],
                },
            })
        return out

    def _build_response(
        self,
        results: list[dict[str, Any]],
        query: str,
        search_mode: str,
        total_time_ms: float,
    ) -> dict[str, Any]:
        """Build the standardized search response dict."""
        return {
            "results": results,
            "total_results": len(results),
            "query": query,
            "search_mode": search_mode,
            "stage1_time_ms": total_time_ms,
            "stage2_time_ms": 0.0,
            "total_time_ms": total_time_ms,
            "candidates_retrieved": len(results),
            "reranked_count": 0,
        }

    def _record_query(self, elapsed_ms: float) -> None:
        """Record query timing for stats."""
        self._stats["total_queries"] += 1
        self._stats["total_times"].append(elapsed_ms)
        if len(self._stats["total_times"]) > 1000:
            self._stats["total_times"] = self._stats["total_times"][-1000:]


class SearchError(Exception):
    """Base exception for search operations."""


class RetrievalError(SearchError):
    """Retrieval failed."""

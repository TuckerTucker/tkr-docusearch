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

# Per-edge-type boost weights for graph-aware re-ranking.
_EDGE_BOOST_WEIGHTS: dict[str, float] = {
    "similar_to": 0.04,
    "same_topic": 0.03,
    "overlaps_topic": 0.02,
    "series_member": 0.03,
    "same_author": 0.02,
    "same_genre": 0.01,
    "references": 0.05,
    "version_of": 0.05,
}


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
        project_id: str | None = None,
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
            project_id: Optional project scope. ``None`` searches all projects.

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
        return dispatch[search_mode](query, n_results, project_id=project_id)

    def text_search(
        self,
        query: str,
        n_results: int = 10,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """Search text chunks by semantic similarity.

        Args:
            query: Search query.
            n_results: Maximum results.
            project_id: Optional project scope. ``None`` searches all projects.

        Returns:
            Search response dict.
        """
        start = time.perf_counter()

        query_emb = self._shikomi.embed_query(query)

        if project_id is not None:
            result = self._koji.query(
                """SELECT c.id, c.doc_id, c.page_num, c.text, c.context,
                          d.filename, d.format, _distance
                   FROM chunks c
                   JOIN documents d ON c.doc_id = d.doc_id
                   WHERE c.embedding <~> $1 AND d.project_id = $2
                   LIMIT $3""",
                [query_emb, project_id, n_results],
            )
        else:
            result = self._koji.query(
                """SELECT c.id, c.doc_id, c.page_num, c.text, c.context,
                          d.filename, d.format, _distance
                   FROM chunks c
                   JOIN documents d ON c.doc_id = d.doc_id
                   WHERE c.embedding <~> $1
                   LIMIT $2""",
                [query_emb, n_results],
            )

        results = self._format_chunk_results(result)
        results = self._boost_related_results(results)
        relationships = self._collect_result_relationships(results)
        elapsed_ms = (time.perf_counter() - start) * 1000
        self._record_query(elapsed_ms)

        return self._build_response(
            results, query, "text_only", elapsed_ms, relationships=relationships,
        )

    def visual_search(
        self,
        query: str,
        n_results: int = 10,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """Search page images by visual similarity.

        Args:
            query: Search query.
            n_results: Maximum results.
            project_id: Optional project scope. ``None`` searches all projects.

        Returns:
            Search response dict.
        """
        start = time.perf_counter()

        query_emb = self._shikomi.embed_query(query)

        if project_id is not None:
            result = self._koji.query(
                """SELECT p.id, p.doc_id, p.page_num, p.structure,
                          d.filename, d.format, _distance
                   FROM pages p
                   JOIN documents d ON p.doc_id = d.doc_id
                   WHERE p.embedding <~> $1 AND d.project_id = $2
                   LIMIT $3""",
                [query_emb, project_id, n_results],
            )
        else:
            result = self._koji.query(
                """SELECT p.id, p.doc_id, p.page_num, p.structure,
                          d.filename, d.format, _distance
                   FROM pages p
                   JOIN documents d ON p.doc_id = d.doc_id
                   WHERE p.embedding <~> $1
                   LIMIT $2""",
                [query_emb, n_results],
            )

        results = self._format_page_results(result)
        results = self._boost_related_results(results)
        relationships = self._collect_result_relationships(results)
        elapsed_ms = (time.perf_counter() - start) * 1000
        self._record_query(elapsed_ms)

        return self._build_response(
            results, query, "visual_only", elapsed_ms, relationships=relationships,
        )

    def hybrid_search(
        self,
        query: str,
        n_results: int = 10,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """Search across both pages and chunks, merging results.

        Runs two separate vector searches (Koji ``<~>`` doesn't support CTEs)
        and merges results in Python, keeping the best score per
        ``(doc_id, page_num)`` pair.

        Args:
            query: Search query.
            n_results: Maximum results.
            project_id: Optional project scope. ``None`` searches all projects.

        Returns:
            Search response dict.
        """
        start = time.perf_counter()

        query_emb = self._shikomi.embed_query(query)
        candidates = n_results * 5

        if project_id is not None:
            page_hits = self._koji.query(
                """SELECT p.doc_id, p.page_num, _distance
                   FROM pages p
                   JOIN documents d ON p.doc_id = d.doc_id
                   WHERE p.embedding <~> $1 AND d.project_id = $2
                   LIMIT $3""",
                [query_emb, project_id, candidates],
            )
            chunk_hits = self._koji.query(
                """SELECT c.doc_id, c.page_num, _distance
                   FROM chunks c
                   JOIN documents d ON c.doc_id = d.doc_id
                   WHERE c.embedding <~> $1 AND d.project_id = $2
                   LIMIT $3""",
                [query_emb, project_id, candidates],
            )
        else:
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

        results = self._boost_related_results(results)
        relationships = self._collect_result_relationships(results)
        elapsed_ms = (time.perf_counter() - start) * 1000
        self._record_query(elapsed_ms)

        return self._build_response(
            results, query, "hybrid", elapsed_ms, relationships=relationships,
        )

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
        relationships: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Build the standardized search response dict.

        Args:
            results: Formatted search result dicts.
            query: Original search query.
            search_mode: The search mode used.
            total_time_ms: Total elapsed time in milliseconds.
            relationships: Optional list of relationship edges between
                result documents. Omitted from response when ``None``.

        Returns:
            Standardized response dict.
        """
        response: dict[str, Any] = {
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
        if relationships is not None:
            response["relationships"] = relationships
        return response

    def _boost_related_results(
        self,
        results: list[dict[str, Any]],
        boost_factor: float = 0.05,
    ) -> list[dict[str, Any]]:
        """Boost scores for documents related to other results in the set.

        For each result, fetches 1-hop relations. If any neighbor is also
        in the result set, adds a type-weighted score boost based on
        ``_EDGE_BOOST_WEIGHTS``. Re-sorts by boosted score.

        Args:
            results: Search result dicts (must have ``doc_id`` and ``score``).
            boost_factor: Default score increment for unknown edge types.

        Returns:
            Results re-sorted by boosted score.
        """
        if not results:
            return results

        result_doc_ids: set[str] = {r["doc_id"] for r in results}

        # Build a map of doc_id -> accumulated type-weighted boost
        boost_totals: dict[str, float] = {}
        for doc_id in result_doc_ids:
            try:
                relations = self._koji.get_relations(doc_id, direction="both")
            except Exception:
                logger.debug(
                    "koji_search.boost_relations_failed",
                    doc_id=doc_id,
                )
                relations = []

            accumulated = 0.0
            for rel in relations:
                if rel["src_doc_id"] == doc_id:
                    other = rel["dst_doc_id"]
                else:
                    other = rel["src_doc_id"]

                if other in result_doc_ids:
                    weight = _EDGE_BOOST_WEIGHTS.get(
                        rel["relation_type"], boost_factor,
                    )
                    accumulated += weight

            boost_totals[doc_id] = accumulated

        # Apply boost
        for result in results:
            boost = boost_totals.get(result["doc_id"], 0.0)
            result["score"] = min(1.0, result["score"] + boost)
            result.setdefault("metadata", {})["graph_boost"] = boost

        # Re-sort by score descending
        results.sort(key=lambda r: r["score"], reverse=True)

        boosted_count = sum(1 for b in boost_totals.values() if b > 0)
        if boosted_count:
            logger.info(
                "koji_search.graph_boost_applied",
                boosted_results=boosted_count,
                total_results=len(results),
                boost_factor=boost_factor,
            )

        # Apply cached PageRank boost if available
        try:
            pagerank_scores = self._get_cached_pagerank(result_doc_ids)
            if pagerank_scores:
                results = self._apply_pagerank_boost(results, pagerank_scores)
        except Exception:
            pass  # No enrichment data available

        return results

    def _collect_result_relationships(
        self,
        results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Collect relationship edges between documents in the result set.

        Only includes edges where both endpoints appear in *results*.

        Args:
            results: Search result dicts (must have ``doc_id``).

        Returns:
            List of edge dicts with ``src_doc_id``, ``dst_doc_id``, and
            ``relation_type``.
        """
        if not results:
            return []

        result_doc_ids: set[str] = {r["doc_id"] for r in results}
        seen_edges: set[tuple[str, str, str]] = set()
        edges: list[dict[str, Any]] = []

        for doc_id in result_doc_ids:
            try:
                relations = self._koji.get_relations(doc_id, direction="both")
            except Exception:
                continue

            for rel in relations:
                src = rel["src_doc_id"]
                dst = rel["dst_doc_id"]
                rtype = rel["relation_type"]

                if src in result_doc_ids and dst in result_doc_ids:
                    edge_key = (src, dst, rtype)
                    if edge_key not in seen_edges:
                        seen_edges.add(edge_key)
                        edges.append({
                            "src_doc_id": src,
                            "dst_doc_id": dst,
                            "relation_type": rtype,
                        })

        return edges

    def _get_cached_pagerank(self, doc_ids: set[str]) -> dict[str, float]:
        """Read pre-computed PageRank from document metadata.

        Returns empty dict if no enrichment has run.
        """
        scores: dict[str, float] = {}
        for doc_id in doc_ids:
            try:
                doc = self._koji.get_document(doc_id)
                if doc:
                    meta = doc.get("metadata") or {}
                    graph = meta.get("graph") or {}
                    pr = graph.get("pagerank_score")
                    if pr is not None:
                        scores[doc_id] = float(pr)
            except Exception:
                continue
        return scores

    def _apply_pagerank_boost(
        self,
        results: list[dict[str, Any]],
        pagerank_scores: dict[str, float],
        weight: float = 0.1,
    ) -> list[dict[str, Any]]:
        """Blend PageRank importance into search scores.

        Normalizes PageRank scores to [0, 1] and blends with the original
        search score using a weighted average.

        Args:
            results: Search result dicts (must have ``doc_id`` and ``score``).
            pagerank_scores: Dict mapping doc_id to PageRank score.
            weight: Blending weight for PageRank (0-1). Higher values
                give more influence to global document importance.

        Returns:
            Results with blended scores, re-sorted descending.
        """
        if not results or not pagerank_scores:
            return results

        max_pr = max(pagerank_scores.values()) if pagerank_scores else 1.0
        if max_pr <= 0:
            return results

        for result in results:
            pr = pagerank_scores.get(result["doc_id"], 0.0)
            normalized_pr = pr / max_pr
            original_score = result["score"]
            result["score"] = (1 - weight) * original_score + weight * normalized_pr
            result.setdefault("metadata", {})["pagerank"] = pr

        results.sort(key=lambda r: r["score"], reverse=True)
        return results

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

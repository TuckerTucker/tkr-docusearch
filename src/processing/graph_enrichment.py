"""Batch graph enrichment service.

Computes derived graph edges and node properties for the document
library. Designed to run periodically or on-demand. All operations
are idempotent — safe to re-run at any time.
"""

from __future__ import annotations

import itertools
import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

import structlog

from ..config.graph_config import GraphEnrichmentConfig
from ..storage.koji_client import KojiClient, KojiDuplicateError, KojiQueryError

logger = structlog.get_logger(__name__)


class GraphEnrichmentService:
    """Batch graph enrichment for the document library.

    Computes derived relationship edges (``similar_to``, ``same_topic``,
    ``overlaps_topic``) and stores graph analytics (PageRank, community,
    hub score) as document metadata.  Every public method is idempotent:
    it deletes stale computed edges before recreating them.

    Args:
        storage_client: An open :class:`KojiClient` instance.
        config: Enrichment thresholds and limits.
    """

    def __init__(
        self,
        storage_client: KojiClient,
        config: GraphEnrichmentConfig,
    ) -> None:
        self._storage = storage_client
        self._config = config

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def run_full_enrichment(self) -> dict[str, Any]:
        """Run all enrichment steps, collecting per-step results.

        Each step is executed independently — a failure in one step does
        not prevent the others from running.

        Returns:
            Summary dict with keys ``similar_to``, ``same_topic``,
            ``overlaps_topic``, ``node_properties`` (each an int count),
            plus ``total_ms`` (float) and any ``errors`` (dict of step
            name to error message).
        """
        t0 = time.perf_counter()
        results: dict[str, Any] = {
            "similar_to": 0,
            "same_topic": 0,
            "overlaps_topic": 0,
            "node_properties": 0,
            "errors": {},
        }

        steps: list[tuple[str, Any]] = [
            ("similar_to", self.compute_similar_to),
            ("same_topic", self.compute_same_topic),
            ("overlaps_topic", self.compute_overlaps_topic),
            ("node_properties", self.compute_node_properties),
        ]

        for name, fn in steps:
            try:
                results[name] = fn()
                logger.info(
                    "graph_enrichment.step_complete",
                    step=name,
                    count=results[name],
                )
            except Exception as exc:
                results["errors"][name] = str(exc)
                logger.error(
                    "graph_enrichment.step_failed",
                    step=name,
                    error=str(exc),
                )

        elapsed_ms = (time.perf_counter() - t0) * 1000
        results["total_ms"] = round(elapsed_ms, 2)

        logger.info(
            "graph_enrichment.complete",
            total_ms=results["total_ms"],
            similar_to=results["similar_to"],
            same_topic=results["same_topic"],
            overlaps_topic=results["overlaps_topic"],
            node_properties=results["node_properties"],
            errors=results["errors"] or None,
        )
        return results

    # ------------------------------------------------------------------
    # Step 1 — similar_to (embedding similarity)
    # ------------------------------------------------------------------

    def compute_similar_to(self) -> int:
        """Compute ``similar_to`` edges via MaxSim embedding search.

        For every document, selects the longest chunk as a representative,
        then performs a vector search against all chunks.  Results are
        grouped by target ``doc_id`` and the best (lowest) distance per
        document is converted to a similarity score.  Bidirectional edges
        are created for pairs exceeding the configured threshold.

        Returns:
            Number of edges created.
        """
        doc_ids = self._fetch_all_doc_ids()
        if not doc_ids:
            return 0

        self._storage.delete_relations_by_type("similar_to")

        created = 0
        # Track pairs already connected so we don't duplicate
        connected: set[tuple[str, str]] = set()

        for doc_id in doc_ids:
            embedding = self._get_representative_embedding(doc_id)
            if embedding is None:
                logger.debug(
                    "graph_enrichment.similar_to.no_embedding",
                    doc_id=doc_id,
                )
                continue

            neighbors = self._maxsim_search(
                embedding,
                self._config.similarity_top_k + 1,
            )

            # Re-rank with exact MaxSim scoring when available.
            # After re-ranking, scores are normalized 0-1 similarity
            # (higher is better) rather than distances (lower is better).
            reranked = self._rerank_with_maxsim(embedding, neighbors)
            is_reranked = reranked is not neighbors

            for target_id, value in reranked:
                if target_id == doc_id:
                    continue

                pair = tuple(sorted((doc_id, target_id)))
                if pair in connected:
                    continue

                if is_reranked:
                    score = value
                else:
                    score = 1.0 / (1.0 + value)

                if score < self._config.similarity_threshold:
                    continue

                method = "maxsim_reranked" if is_reranked else "maxsim"
                metadata = {"score": round(score, 4), "method": method}

                # Bidirectional edges
                rel_fwd = self._safe_create_relation(
                    doc_id, target_id, "similar_to", metadata=metadata,
                )
                rel_rev = self._safe_create_relation(
                    target_id, doc_id, "similar_to", metadata=metadata,
                )
                if rel_fwd or rel_rev:
                    connected.add(pair)
                if rel_fwd:
                    created += 1
                if rel_rev:
                    created += 1

        return created

    # ------------------------------------------------------------------
    # Step 2 — same_topic (heading Jaccard similarity)
    # ------------------------------------------------------------------

    def compute_same_topic(self) -> int:
        """Compute ``same_topic`` edges from shared section headings.

        Extracts ``parent_heading`` and ``section_path`` from chunk
        context metadata, builds a heading set per document, then
        creates bidirectional edges for document pairs whose Jaccard
        similarity exceeds the configured threshold.

        Returns:
            Number of edges created.
        """
        doc_headings = self._build_doc_heading_sets()
        if len(doc_headings) < 2:
            return 0

        self._storage.delete_relations_by_type("same_topic")

        created = 0
        sorted_ids = sorted(doc_headings.keys())

        for id_a, id_b in itertools.combinations(sorted_ids, 2):
            set_a = doc_headings[id_a]
            set_b = doc_headings[id_b]
            if not set_a or not set_b:
                continue

            intersection = set_a & set_b
            union = set_a | set_b
            jaccard = len(intersection) / len(union)

            if jaccard < self._config.same_topic_jaccard_threshold:
                continue

            shared = sorted(intersection)
            metadata = {"jaccard": round(jaccard, 4), "shared_headings": shared}

            rel_fwd = self._safe_create_relation(
                id_a, id_b, "same_topic", metadata=metadata,
            )
            rel_rev = self._safe_create_relation(
                id_b, id_a, "same_topic", metadata=metadata,
            )
            if rel_fwd:
                created += 1
            if rel_rev:
                created += 1

        return created

    # ------------------------------------------------------------------
    # Step 3 — overlaps_topic (community detection)
    # ------------------------------------------------------------------

    def compute_overlaps_topic(self) -> int:
        """Compute ``overlaps_topic`` edges from label propagation communities.

        Runs label propagation on the existing graph, groups documents
        by community, and connects all pairs within communities that
        are small enough (at or below ``max_community_full_connect``).

        Returns:
            Number of edges created.
        """
        try:
            communities = self._storage.graph_label_propagation()
        except Exception as exc:
            logger.warning(
                "graph_enrichment.overlaps_topic.label_propagation_failed",
                error=str(exc),
            )
            return 0

        if not communities:
            return 0

        self._storage.delete_relations_by_type("overlaps_topic")

        # Group doc_ids by community label
        groups: dict[int, list[str]] = defaultdict(list)
        for doc_id, label in communities.items():
            groups[label].append(doc_id)

        created = 0
        max_size = self._config.max_community_full_connect

        for community_id, members in groups.items():
            if len(members) > max_size:
                logger.debug(
                    "graph_enrichment.overlaps_topic.community_too_large",
                    community_id=community_id,
                    size=len(members),
                    max_size=max_size,
                )
                continue

            sorted_members = sorted(members)
            metadata = {"community_id": community_id}

            for id_a, id_b in itertools.combinations(sorted_members, 2):
                rel_fwd = self._safe_create_relation(
                    id_a, id_b, "overlaps_topic", metadata=metadata,
                )
                rel_rev = self._safe_create_relation(
                    id_b, id_a, "overlaps_topic", metadata=metadata,
                )
                if rel_fwd:
                    created += 1
                if rel_rev:
                    created += 1

        return created

    # ------------------------------------------------------------------
    # Step 4 — node properties (PageRank, community, hub score)
    # ------------------------------------------------------------------

    def compute_node_properties(self) -> int:
        """Compute and store graph analytics as document metadata.

        Runs PageRank and label propagation, counts hub scores
        (total incoming + outgoing edges), and writes results into
        each document's ``metadata["graph"]`` key.

        Returns:
            Number of documents updated.
        """
        # PageRank
        try:
            pagerank_scores = self._storage.graph_pagerank()
        except Exception as exc:
            logger.warning(
                "graph_enrichment.node_properties.pagerank_failed",
                error=str(exc),
            )
            pagerank_scores = {}

        # Community labels
        try:
            community_labels = self._storage.graph_label_propagation()
        except Exception as exc:
            logger.warning(
                "graph_enrichment.node_properties.label_propagation_failed",
                error=str(exc),
            )
            community_labels = {}

        # Hub scores
        hub_scores = self._compute_hub_scores()

        # Collect all doc_ids that have at least one property
        all_doc_ids = (
            set(pagerank_scores.keys())
            | set(community_labels.keys())
            | set(hub_scores.keys())
        )

        if not all_doc_ids:
            return 0

        updated = 0
        enriched_at = datetime.now(timezone.utc).isoformat()

        for doc_id in all_doc_ids:
            try:
                doc = self._storage.get_document(doc_id)
                if doc is None:
                    continue

                metadata = doc.get("metadata")
                if metadata is None:
                    metadata = {}
                elif isinstance(metadata, str):
                    metadata = json.loads(metadata)

                metadata["graph"] = {
                    "pagerank_score": round(
                        pagerank_scores.get(doc_id, 0.0), 6
                    ),
                    "community_id": community_labels.get(doc_id),
                    "hub_score": hub_scores.get(doc_id, 0),
                    "enriched_at": enriched_at,
                }

                self._storage.update_document(doc_id, metadata=metadata)
                updated += 1
            except Exception as exc:
                logger.warning(
                    "graph_enrichment.node_properties.update_failed",
                    doc_id=doc_id,
                    error=str(exc),
                )

        return updated

    # ------------------------------------------------------------------
    # private helpers
    # ------------------------------------------------------------------

    def _fetch_all_doc_ids(self) -> list[str]:
        """Fetch all document IDs from the documents table.

        Returns:
            Sorted list of doc_id strings.
        """
        try:
            result = self._storage.query("SELECT doc_id FROM documents")
            d = result.to_pydict()
            return sorted(d.get("doc_id", []))
        except KojiQueryError:
            return []

    def _get_representative_embedding(self, doc_id: str) -> bytes | None:
        """Select the embedding from the longest chunk of a document.

        Args:
            doc_id: Document identifier.

        Returns:
            Raw embedding bytes, or ``None`` if no embedded chunks exist.
        """
        try:
            result = self._storage.query(
                "SELECT embedding FROM chunks "
                "WHERE doc_id = ? ORDER BY word_count DESC LIMIT 1",
                [doc_id],
            )
            if result.num_rows == 0:
                return None
            embedding = result.to_pydict()["embedding"][0]
            if embedding is None:
                return None
            return embedding
        except KojiQueryError:
            return None

    def _rerank_with_maxsim(
        self,
        query_blob: bytes,
        candidates: list[tuple[str, float]],
    ) -> list[tuple[str, float]]:
        """Re-rank candidates using exact MaxSim scoring.

        Deserializes multi-vector embeddings for both the query and each
        candidate document, then computes a normalized MaxSim similarity
        score.  Scores are in ``[0, 1]`` range and can be compared
        directly against the similarity threshold.

        Falls back to returning *candidates* unchanged when the required
        ``shikomi_ingest`` scoring modules are not installed.

        Args:
            query_blob: Packed multi-vector embedding bytes for the query
                document.
            candidates: List of ``(doc_id, approx_distance)`` pairs from
                the approximate search.

        Returns:
            List of ``(doc_id, score)`` pairs sorted by score descending.
            If re-ranking is unavailable, returns *candidates* unchanged.
        """
        try:
            from shikomi_ingest.types import MultiVectorEmbedding
            from shikomi_ingest.embedding.scoring import maxsim
        except ImportError:
            logger.debug(
                "graph_enrichment.rerank_with_maxsim.import_unavailable",
                reason="shikomi_ingest scoring modules not installed",
            )
            return candidates

        query_emb = MultiVectorEmbedding.from_blob(query_blob)
        reranked: list[tuple[str, float]] = []

        for doc_id, _approx_distance in candidates:
            doc_blob = self._get_representative_embedding(doc_id)
            if doc_blob is None:
                logger.debug(
                    "graph_enrichment.rerank_with_maxsim.no_embedding",
                    doc_id=doc_id,
                )
                continue

            doc_emb = MultiVectorEmbedding.from_blob(doc_blob)
            raw_score = maxsim(query_emb, doc_emb)
            score = raw_score / query_emb.num_tokens
            reranked.append((doc_id, score))

        reranked.sort(key=lambda x: x[1], reverse=True)

        logger.debug(
            "graph_enrichment.rerank_with_maxsim.complete",
            input_count=len(candidates),
            output_count=len(reranked),
        )
        return reranked

    def _maxsim_search(
        self,
        embedding: bytes,
        top_k: int,
    ) -> list[tuple[str, float]]:
        """Run MaxSim vector search and return per-document best distances.

        Queries a larger candidate set and groups by ``doc_id`` in Python,
        keeping the minimum distance per document.

        Args:
            embedding: Packed multi-vector binary blob.
            top_k: Number of target documents to return.

        Returns:
            List of ``(doc_id, best_distance)`` pairs, sorted by distance
            ascending, limited to *top_k* entries.
        """
        candidate_limit = top_k * 10

        try:
            result = self._storage.query(
                "SELECT doc_id, _distance "
                "FROM chunks WHERE embedding <~> $1 LIMIT $2",
                [embedding, candidate_limit],
            )
        except KojiQueryError as exc:
            logger.warning(
                "graph_enrichment.maxsim_search_failed",
                error=str(exc),
            )
            return []

        d = result.to_pydict()
        doc_ids = d.get("doc_id", [])
        distances = d.get("_distance", [])

        # Group by doc_id, keep best (minimum) distance
        best: dict[str, float] = {}
        for i in range(len(doc_ids)):
            did = doc_ids[i]
            dist = float(distances[i])
            if did not in best or dist < best[did]:
                best[did] = dist

        # Sort by distance ascending, take top_k
        ranked = sorted(best.items(), key=lambda x: x[1])
        return ranked[:top_k]

    def _build_doc_heading_sets(self) -> dict[str, set[str]]:
        """Extract heading sets from chunk context for all documents.

        Parses ``parent_heading`` and ``section_path`` from each chunk's
        ``context`` JSON and aggregates unique headings per document.

        Returns:
            Dict mapping ``doc_id`` to a set of heading strings.
        """
        try:
            result = self._storage.query(
                "SELECT doc_id, context FROM chunks WHERE context IS NOT NULL"
            )
        except KojiQueryError:
            return {}

        d = result.to_pydict()
        doc_ids = d.get("doc_id", [])
        contexts = d.get("context", [])

        headings: dict[str, set[str]] = defaultdict(set)

        for i in range(len(doc_ids)):
            ctx_raw = contexts[i]
            if not ctx_raw:
                continue

            try:
                ctx = json.loads(ctx_raw) if isinstance(ctx_raw, str) else ctx_raw
            except (json.JSONDecodeError, TypeError):
                continue

            if not isinstance(ctx, dict):
                continue

            doc_id = doc_ids[i]

            parent_heading = ctx.get("parent_heading")
            if parent_heading and isinstance(parent_heading, str):
                headings[doc_id].add(parent_heading.strip().lower())

            section_path = ctx.get("section_path")
            if isinstance(section_path, list):
                for entry in section_path:
                    if isinstance(entry, str) and entry.strip():
                        headings[doc_id].add(entry.strip().lower())
            elif isinstance(section_path, str) and section_path.strip():
                headings[doc_id].add(section_path.strip().lower())

        return dict(headings)

    def _compute_hub_scores(self) -> dict[str, int]:
        """Count total edges (src + dst) per document.

        Returns:
            Dict mapping ``doc_id`` to total edge count.
        """
        hub: dict[str, int] = {}

        try:
            src_result = self._storage.query(
                "SELECT src_doc_id, COUNT(*) AS cnt "
                "FROM doc_relations GROUP BY src_doc_id"
            )
            d = src_result.to_pydict()
            for i in range(len(d.get("src_doc_id", []))):
                doc_id = d["src_doc_id"][i]
                hub[doc_id] = hub.get(doc_id, 0) + int(d["cnt"][i])
        except KojiQueryError as exc:
            logger.warning(
                "graph_enrichment.hub_scores.src_query_failed",
                error=str(exc),
            )

        try:
            dst_result = self._storage.query(
                "SELECT dst_doc_id, COUNT(*) AS cnt "
                "FROM doc_relations GROUP BY dst_doc_id"
            )
            d = dst_result.to_pydict()
            for i in range(len(d.get("dst_doc_id", []))):
                doc_id = d["dst_doc_id"][i]
                hub[doc_id] = hub.get(doc_id, 0) + int(d["cnt"][i])
        except KojiQueryError as exc:
            logger.warning(
                "graph_enrichment.hub_scores.dst_query_failed",
                error=str(exc),
            )

        return hub

    def _safe_create_relation(
        self,
        src_doc_id: str,
        dst_doc_id: str,
        relation_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Create a relation, swallowing duplicates and other errors.

        Args:
            src_doc_id: Source document identifier.
            dst_doc_id: Destination document identifier.
            relation_type: Relationship type string.
            metadata: Optional metadata dict.

        Returns:
            ``True`` if the relation was created, ``False`` otherwise.
        """
        try:
            self._storage.create_relation(
                src_doc_id=src_doc_id,
                dst_doc_id=dst_doc_id,
                relation_type=relation_type,
                metadata=metadata,
            )
            logger.debug(
                "graph_enrichment.relation_created",
                src=src_doc_id,
                dst=dst_doc_id,
                type=relation_type,
            )
            return True
        except (KojiDuplicateError, KojiQueryError, ValueError) as exc:
            logger.debug(
                "graph_enrichment.relation_skipped",
                src=src_doc_id,
                dst=dst_doc_id,
                type=relation_type,
                reason=str(exc),
            )
            return False
        except Exception as exc:
            logger.warning(
                "graph_enrichment.relation_failed",
                src=src_doc_id,
                dst=dst_doc_id,
                type=relation_type,
                error=str(exc),
            )
            return False

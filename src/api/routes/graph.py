"""Graph API endpoints for document relationship visualization.

Provides query endpoints for the document graph — nodes, edges,
neighborhoods, paths, communities, and importance rankings.
The graph data is pre-computed by the enrichment service; these
endpoints serve shaped projections for different view use cases.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/graph", tags=["graph"])

# Injected at startup by server.py
_storage_client = None


def set_storage_client(storage_client: Any) -> None:
    """Set the storage client for graph endpoints."""
    global _storage_client
    _storage_client = storage_client


def _require_storage():
    """Raise 503 if storage not initialized."""
    if _storage_client is None:
        raise HTTPException(503, "Storage service not available")
    return _storage_client


# ---------------------------------------------------------------------------
# GET /api/graph/overview — full graph summary for library view
# ---------------------------------------------------------------------------


@router.get("/overview")
async def graph_overview():
    """Full graph summary: nodes with properties, edge counts by type.

    Returns the data needed to render a library-level graph view with
    community clusters and importance sizing.
    """
    storage = _require_storage()

    try:
        # Fetch all documents with graph properties
        docs_result = storage.query(
            "SELECT doc_id, filename, format, num_pages, metadata "
            "FROM documents ORDER BY doc_id"
        )
        d = docs_result.to_pydict()

        nodes = []
        for i in range(docs_result.num_rows):
            meta = _parse_metadata(d["metadata"][i])
            graph = meta.get("graph", {})
            nodes.append({
                "doc_id": d["doc_id"][i],
                "filename": d["filename"][i],
                "format": d["format"][i],
                "num_pages": d["num_pages"][i],
                "pagerank_score": graph.get("pagerank_score", 0.0),
                "community_id": graph.get("community_id"),
                "hub_score": graph.get("hub_score", 0),
            })

        # Edge counts by type
        edge_result = storage.query(
            "SELECT relation_type, COUNT(*) AS cnt "
            "FROM doc_relations GROUP BY relation_type"
        )
        ed = edge_result.to_pydict()
        edge_counts = {
            ed["relation_type"][i]: ed["cnt"][i]
            for i in range(edge_result.num_rows)
        }

        # Community summary
        communities: dict[int, int] = {}
        for node in nodes:
            cid = node["community_id"]
            if cid is not None:
                communities[cid] = communities.get(cid, 0) + 1

    except Exception as exc:
        logger.error(f"graph_overview failed: {exc}", exc_info=True)
        raise HTTPException(500, f"Failed to load graph: {exc}")

    return {
        "nodes": nodes,
        "node_count": len(nodes),
        "edge_counts": edge_counts,
        "total_edges": sum(edge_counts.values()),
        "communities": communities,
        "community_count": len(communities),
    }


# ---------------------------------------------------------------------------
# GET /api/graph/neighborhood/{doc_id} — expand around a document
# ---------------------------------------------------------------------------


@router.get("/neighborhood/{doc_id}")
async def graph_neighborhood(
    doc_id: str,
    depth: int = Query(1, ge=1, le=3),
    edge_types: Optional[str] = Query(
        None, description="Comma-separated edge types to include"
    ),
):
    """Expand the neighborhood around a document up to N hops.

    Returns the subgraph reachable from the given document, including
    nodes (with properties) and edges (with metadata).

    Args:
        doc_id: Center document identifier.
        depth: Maximum traversal depth (1-3).
        edge_types: Optional filter — comma-separated relation types.
    """
    storage = _require_storage()

    # Verify document exists
    doc = storage.get_document(doc_id)
    if doc is None:
        raise HTTPException(404, f"Document '{doc_id}' not found")

    try:
        # Get related documents via BFS
        related = storage.get_related_documents(doc_id, max_depth=depth)

        # Get all edges for the center + related documents
        all_doc_ids = {doc_id} | {r["doc_id"] for r in related}
        edges = _collect_edges(storage, all_doc_ids, edge_types)

        # Build node list (center + related)
        nodes = [_doc_to_node(doc, depth=0)]
        for r in related:
            nodes.append(_doc_to_node(r, depth=r.get("depth", 1)))

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"graph_neighborhood failed: {exc}", exc_info=True)
        raise HTTPException(500, f"Failed to load neighborhood: {exc}")

    return {
        "center": doc_id,
        "nodes": nodes,
        "edges": edges,
        "depth": depth,
    }


# ---------------------------------------------------------------------------
# GET /api/graph/path — shortest path between two documents
# ---------------------------------------------------------------------------


@router.get("/path")
async def graph_path(
    source: str = Query(..., description="Source document ID"),
    target: str = Query(..., description="Target document ID"),
):
    """Find the shortest path between two documents.

    Returns the chain of documents and relationships connecting them.
    Empty path means the documents are not connected.
    """
    storage = _require_storage()

    # Verify both documents exist
    for did, label in [(source, "Source"), (target, "Target")]:
        if storage.get_document(did) is None:
            raise HTTPException(404, f"{label} document '{did}' not found")

    try:
        distances = storage.graph_shortest_paths(source)
    except Exception as exc:
        logger.error(f"graph_path failed: {exc}", exc_info=True)
        raise HTTPException(500, f"Shortest path computation failed: {exc}")

    if target not in distances:
        return {
            "source": source,
            "target": target,
            "connected": False,
            "path": [],
            "distance": None,
        }

    # Reconstruct path via BFS
    path = _reconstruct_path(storage, source, target)

    return {
        "source": source,
        "target": target,
        "connected": True,
        "path": path,
        "distance": distances[target],
    }


# ---------------------------------------------------------------------------
# GET /api/graph/communities — topic clusters
# ---------------------------------------------------------------------------


@router.get("/communities")
async def graph_communities():
    """List all topic communities with their members.

    Returns community clusters from label propagation, each with
    member documents and aggregate stats.
    """
    storage = _require_storage()

    try:
        labels = storage.graph_label_propagation()
    except Exception as exc:
        logger.error(f"graph_communities failed: {exc}", exc_info=True)
        raise HTTPException(500, f"Community detection failed: {exc}")

    if not labels:
        return {"communities": [], "total": 0}

    # Group by community
    groups: dict[int, list[str]] = {}
    for doc_id, label in labels.items():
        groups.setdefault(label, []).append(doc_id)

    # Build community entries with document details
    communities = []
    for label, doc_ids in sorted(groups.items(), key=lambda x: -len(x[1])):
        members = []
        for did in sorted(doc_ids):
            doc = storage.get_document(did)
            if doc:
                members.append({
                    "doc_id": did,
                    "filename": doc.get("filename"),
                    "format": doc.get("format"),
                })
        communities.append({
            "community_id": label,
            "size": len(members),
            "members": members,
        })

    return {
        "communities": communities,
        "total": len(communities),
    }


# ---------------------------------------------------------------------------
# GET /api/graph/importance — documents ranked by PageRank
# ---------------------------------------------------------------------------


@router.get("/importance")
async def graph_importance(
    limit: int = Query(20, ge=1, le=100),
):
    """Documents ranked by PageRank importance.

    Returns the most influential documents in the library graph,
    useful for identifying foundational or highly-cited content.
    """
    storage = _require_storage()

    try:
        scores = storage.graph_pagerank()
    except Exception as exc:
        logger.error(f"graph_importance failed: {exc}", exc_info=True)
        raise HTTPException(500, f"PageRank computation failed: {exc}")

    if not scores:
        return {"documents": [], "total": 0}

    # Sort by score descending, take top N
    ranked = sorted(scores.items(), key=lambda x: -x[1])[:limit]

    documents = []
    for doc_id, score in ranked:
        doc = storage.get_document(doc_id)
        if doc:
            meta = _parse_metadata(doc.get("metadata"))
            graph = meta.get("graph", {})
            documents.append({
                "doc_id": doc_id,
                "filename": doc.get("filename"),
                "format": doc.get("format"),
                "pagerank_score": score,
                "hub_score": graph.get("hub_score", 0),
                "community_id": graph.get("community_id"),
            })

    return {
        "documents": documents,
        "total": len(documents),
    }


# ---------------------------------------------------------------------------
# GET /api/graph/similar/{doc_id} — similarity neighbors
# ---------------------------------------------------------------------------


@router.get("/similar/{doc_id}")
async def graph_similar(
    doc_id: str,
    limit: int = Query(10, ge=1, le=50),
):
    """Documents most similar to a given document.

    Returns pre-computed similarity neighbors ranked by score,
    from the ``similar_to`` edge type.
    """
    storage = _require_storage()

    doc = storage.get_document(doc_id)
    if doc is None:
        raise HTTPException(404, f"Document '{doc_id}' not found")

    try:
        relations = storage.get_relations(
            doc_id, relation_type="similar_to", direction="both"
        )
    except Exception as exc:
        logger.error(f"graph_similar failed: {exc}", exc_info=True)
        raise HTTPException(500, f"Failed to load similarity data: {exc}")

    # Extract neighbor doc_ids with scores from metadata
    neighbors = []
    for rel in relations:
        other_id = (
            rel["dst_doc_id"] if rel["src_doc_id"] == doc_id
            else rel["src_doc_id"]
        )
        meta = rel.get("metadata") or {}
        score = meta.get("score", 0.0)
        neighbors.append((other_id, score))

    # Deduplicate (bidirectional edges) and sort by score descending
    seen = set()
    unique = []
    for other_id, score in sorted(neighbors, key=lambda x: -x[1]):
        if other_id not in seen:
            seen.add(other_id)
            unique.append((other_id, score))

    results = []
    for other_id, score in unique[:limit]:
        other_doc = storage.get_document(other_id)
        if other_doc:
            results.append({
                "doc_id": other_id,
                "filename": other_doc.get("filename"),
                "format": other_doc.get("format"),
                "similarity_score": score,
            })

    return {
        "doc_id": doc_id,
        "filename": doc.get("filename"),
        "similar": results,
        "total": len(results),
    }


# ---------------------------------------------------------------------------
# GET /api/graph/edges — query edges with optional filters
# ---------------------------------------------------------------------------


@router.get("/edges")
async def graph_edges(
    doc_id: Optional[str] = Query(None, description="Filter by document"),
    edge_type: Optional[str] = Query(None, description="Filter by type"),
    limit: int = Query(100, ge=1, le=1000),
):
    """Query graph edges with optional filters.

    Returns raw edge data for visualization or analysis.
    """
    storage = _require_storage()

    try:
        if doc_id:
            relations = storage.get_relations(
                doc_id,
                relation_type=edge_type,
                direction="both",
            )
        else:
            # All edges (with optional type filter)
            sql = "SELECT src_doc_id, dst_doc_id, relation_type, metadata FROM doc_relations"
            params = []
            if edge_type:
                sql += " WHERE relation_type = ?"
                params = [edge_type]
            sql += f" LIMIT {limit}"
            result = storage.query(sql, params or None)
            d = result.to_pydict()
            relations = []
            for i in range(result.num_rows):
                meta = d["metadata"][i]
                if isinstance(meta, str):
                    try:
                        meta = json.loads(meta)
                    except (json.JSONDecodeError, TypeError):
                        meta = None
                relations.append({
                    "src_doc_id": d["src_doc_id"][i],
                    "dst_doc_id": d["dst_doc_id"][i],
                    "relation_type": d["relation_type"][i],
                    "metadata": meta,
                })
    except Exception as exc:
        logger.error(f"graph_edges failed: {exc}", exc_info=True)
        raise HTTPException(500, f"Failed to load edges: {exc}")

    return {
        "edges": relations[:limit],
        "total": len(relations[:limit]),
    }


# ---------------------------------------------------------------------------
# GET /api/graph/reading-order — topological ordering for a community
# ---------------------------------------------------------------------------


@router.get("/reading-order")
async def graph_reading_order(
    community_id: Optional[int] = Query(
        None, description="Community ID to order (all docs if omitted)"
    ),
):
    """Suggested reading order based on graph topology.

    Uses topological sort on directional edges within a community.
    Falls back to PageRank ordering if cycles exist.
    """
    storage = _require_storage()

    try:
        # Try topological sort first
        has_cycle = storage.graph_has_cycle()

        if not has_cycle:
            ordered_ids = storage.graph_topological_sort()
        else:
            # Fall back to PageRank ordering
            scores = storage.graph_pagerank()
            ordered_ids = [
                doc_id for doc_id, _ in
                sorted(scores.items(), key=lambda x: -x[1])
            ]

        # Filter to community if specified
        if community_id is not None:
            labels = storage.graph_label_propagation()
            community_members = {
                did for did, label in labels.items()
                if label == community_id
            }
            ordered_ids = [did for did in ordered_ids if did in community_members]

        # Fetch document details
        documents = []
        for i, doc_id in enumerate(ordered_ids):
            doc = storage.get_document(doc_id)
            if doc:
                documents.append({
                    "position": i + 1,
                    "doc_id": doc_id,
                    "filename": doc.get("filename"),
                    "format": doc.get("format"),
                })

    except Exception as exc:
        logger.error(f"graph_reading_order failed: {exc}", exc_info=True)
        raise HTTPException(500, f"Reading order computation failed: {exc}")

    return {
        "order": documents,
        "method": "pagerank" if has_cycle else "topological",
        "community_id": community_id,
        "total": len(documents),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_metadata(raw: Any) -> dict:
    """Parse metadata from Koji (may be JSON string, dict, or None)."""
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


def _doc_to_node(doc: dict, depth: int = 0) -> dict:
    """Convert a document dict to a graph node payload."""
    meta = _parse_metadata(doc.get("metadata"))
    graph = meta.get("graph", {})
    return {
        "doc_id": doc.get("doc_id"),
        "filename": doc.get("filename"),
        "format": doc.get("format"),
        "num_pages": doc.get("num_pages"),
        "depth": depth,
        "pagerank_score": graph.get("pagerank_score", 0.0),
        "community_id": graph.get("community_id"),
        "hub_score": graph.get("hub_score", 0),
    }


def _collect_edges(
    storage: Any,
    doc_ids: set[str],
    edge_types: Optional[str] = None,
) -> list[dict]:
    """Collect all edges between a set of documents."""
    type_filter = set(edge_types.split(",")) if edge_types else None
    seen: set[tuple[str, str, str]] = set()
    edges: list[dict] = []

    for doc_id in doc_ids:
        try:
            relations = storage.get_relations(doc_id, direction="both")
        except Exception:
            continue

        for rel in relations:
            src = rel["src_doc_id"]
            dst = rel["dst_doc_id"]
            rtype = rel["relation_type"]

            if src not in doc_ids or dst not in doc_ids:
                continue
            if type_filter and rtype not in type_filter:
                continue

            key = (src, dst, rtype)
            if key not in seen:
                seen.add(key)
                edges.append({
                    "src_doc_id": src,
                    "dst_doc_id": dst,
                    "relation_type": rtype,
                    "metadata": rel.get("metadata"),
                })

    return edges


def _reconstruct_path(
    storage: Any,
    source: str,
    target: str,
    max_depth: int = 10,
) -> list[dict]:
    """BFS to reconstruct the shortest path between two documents."""
    from collections import deque

    visited = {source}
    queue: deque[tuple[str, list[dict]]] = deque([(source, [])])

    while queue:
        current, path = queue.popleft()
        if len(path) >= max_depth:
            continue

        try:
            relations = storage.get_relations(current, direction="outgoing")
        except Exception:
            continue

        for rel in relations:
            neighbor = rel["dst_doc_id"]
            if neighbor in visited:
                continue
            visited.add(neighbor)

            step = {
                "from": current,
                "to": neighbor,
                "relation_type": rel["relation_type"],
            }
            new_path = path + [step]

            if neighbor == target:
                return new_path

            queue.append((neighbor, new_path))

    return []

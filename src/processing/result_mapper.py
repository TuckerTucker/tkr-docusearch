"""Pure mapping functions from Shikomi IngestResult to Koji record dicts.

This module bridges the type gap between Shikomi's ingest output and the
record formats expected by :class:`~src.storage.koji_client.KojiClient`.
All functions are pure -- no I/O, no side effects, no database access.

Key field translations:

- ``TextChunk.content`` -> ``"text"`` (Koji chunks table)
- ``TextChunk.page`` -> ``"page_num"`` (Koji chunks table, defaults to 1)
- ``MultiVectorEmbedding.to_blob()`` -> ``"embedding"`` (binary column)

VLM enrichment (Gemma 4 E4B via shikomi):

- ``IngestResult.enrichment_result`` is a serialized ``EnrichmentResult``
  dict with keys ``figures``, ``code_blocks``, ``formulas``,
  ``document_summary``, ``semantic_metadata``. When present, this module
  extracts per-document/page/chunk enrichment dicts into the
  ``"enrichment"`` field of each record type and can build synthetic
  text-only ``SyntheticEnrichmentChunk`` records for the caller to embed
  so that captions and summaries flow into the searchable text stream.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from shikomi import IngestResult
    from shikomi.types import MultiVectorEmbedding, TextChunk

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Synthetic enrichment chunks
# ---------------------------------------------------------------------------


@dataclass
class SyntheticEnrichmentChunk:
    """Text-only chunk synthesized from VLM enrichment output.

    These chunks do not come from the parser. They capture VLM-generated
    text (document summaries, figure descriptions, formula
    interpretations) so the caller can embed and store them alongside
    organic chunks, making enrichment retrievable via text search.

    Attributes:
        chunk_id: Unique chunk identifier (includes source prefix).
        text: Embed-ready text content.
        page_num: Page number to associate the chunk with (``1`` when
            unknown — doc-level summary and unlocated figures).
        enrichment: Dict describing where this chunk came from. Always
            includes a ``"source"`` key with values like
            ``"document_summary"``, ``"figure_caption"``, ``"code_block"``,
            or ``"formula"``.
    """

    chunk_id: str
    text: str
    page_num: int
    enrichment: dict[str, Any]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _coerce_enrichment_result(
    enrichment_result: Any,
) -> dict[str, Any]:
    """Return the enrichment dict or an empty dict for missing/malformed input.

    ``IngestResult.enrichment_result`` is typed ``Optional[Dict[str, Any]]``
    but may be ``None``, a dataclass (if shikomi ever stops pre-serializing),
    or something else. Normalize to a dict and return an empty dict on
    any unexpected shape.
    """
    if not enrichment_result:
        return {}
    if isinstance(enrichment_result, dict):
        return enrichment_result
    # Fallback for dataclass-like objects.
    to_dict = getattr(enrichment_result, "to_dict", None)
    if callable(to_dict):
        try:
            return to_dict()
        except Exception:
            return {}
    return {}


def _build_document_enrichment(
    enrichment_data: dict[str, Any],
) -> dict[str, Any] | None:
    """Flatten the document-level slice of enrichment_result into one dict.

    Merges ``document_summary`` (summary, key_points, document_type) and
    ``semantic_metadata`` (topics, entities, key_terms) into a single
    record for the ``documents.enrichment`` column.

    Returns ``None`` when both sources are absent.
    """
    doc_summary = enrichment_data.get("document_summary") or {}
    semantic = enrichment_data.get("semantic_metadata") or {}
    if not doc_summary and not semantic:
        return None

    record: dict[str, Any] = {}
    if doc_summary:
        record["summary"] = doc_summary.get("summary") or None
        key_points = doc_summary.get("key_points") or []
        if key_points:
            record["key_points"] = list(key_points)
        doc_type = doc_summary.get("document_type")
        if doc_type:
            record["document_type"] = doc_type
    if semantic:
        topics = semantic.get("topics") or []
        if topics:
            record["topics"] = list(topics)
        entities = semantic.get("entities") or []
        if entities:
            record["entities"] = [dict(e) for e in entities]
        key_terms = semantic.get("key_terms") or []
        if key_terms:
            record["key_terms"] = list(key_terms)
    return record or None


def _index_figures_by_id(
    enrichment_data: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Return ``{figure_id: FigureEnrichment_dict}`` for fast chunk lookup."""
    figures = enrichment_data.get("figures") or []
    indexed: dict[str, dict[str, Any]] = {}
    for fig in figures:
        fig_id = fig.get("figure_id")
        if fig_id:
            indexed[fig_id] = fig
    return indexed


def _build_chunk_enrichment(
    chunk: TextChunk,
    figures_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    """Compose the chunk-level enrichment dict from related figures.

    Uses ``chunk.context.related_figures`` to find any figures this
    chunk references and attaches their VLM descriptions/classifications.
    Returns ``None`` when no relevant enrichment is available.
    """
    context = getattr(chunk, "context", None)
    related_ids: list[str] = []
    if context is not None:
        related_ids = list(getattr(context, "related_figures", []) or [])

    attached: list[dict[str, Any]] = []
    for fig_id in related_ids:
        fig_data = figures_by_id.get(fig_id)
        if fig_data is None:
            continue
        desc = fig_data.get("description")
        if not desc:
            continue
        attached.append({
            "figure_id": fig_id,
            "description": desc,
            "classification": fig_data.get("classification"),
            "confidence": fig_data.get("confidence"),
        })

    if not attached:
        return None
    return {"figures": attached}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def map_document_record(
    result: IngestResult,
    filename: str,
    project_id: str,
    num_pages: int | None = None,
) -> dict[str, Any]:
    """Build a document record dict from an IngestResult.

    The returned dict can be unpacked directly into
    :meth:`KojiClient.create_document`.

    Args:
        result: Completed ingest result from Shikomi.
        filename: Original uploaded filename.
        project_id: Project identifier for logical partitioning.
        num_pages: Explicit page count override. When ``None``, the count
            is inferred from ``result.visual_embeddings`` length if present.

    Returns:
        Dict with keys matching ``KojiClient.create_document`` parameters:
        ``doc_id``, ``filename``, ``format``, ``num_pages``, ``markdown``,
        ``metadata``, ``project_id``, ``enrichment``.
    """
    _, ext = os.path.splitext(filename)
    file_format = ext.lstrip(".").lower() if ext else ""

    resolved_pages = num_pages
    if resolved_pages is None and result.visual_embeddings:
        resolved_pages = len(result.visual_embeddings)

    enrichment_data = _coerce_enrichment_result(
        getattr(result, "enrichment_result", None)
    )
    doc_enrichment = _build_document_enrichment(enrichment_data)

    record: dict[str, Any] = {
        "doc_id": result.content_hash,
        "filename": filename,
        "format": file_format,
        "num_pages": resolved_pages,
        "markdown": result.markdown_content,
        "metadata": result.metadata,
        "project_id": project_id,
        "enrichment": doc_enrichment,
    }

    logger.debug(
        "result_mapper.map_document_record",
        doc_id=result.content_hash,
        filename=filename,
        format=file_format,
        num_pages=resolved_pages,
        project_id=project_id,
        has_enrichment=doc_enrichment is not None,
    )

    return record


def map_page_records(
    doc_id: str,
    visual_embeddings: list[MultiVectorEmbedding],
    page_images: list[bytes] | None = None,
    page_structures: list[dict[str, Any]] | None = None,
    result: IngestResult | None = None,
    chunks: list[TextChunk] | None = None,
) -> list[dict[str, Any]]:
    """Build page record dicts from visual embeddings and optional images.

    Page numbering is 1-indexed. The page ID follows the convention
    ``"{doc_id}-page{num:03d}"``.

    When ``result`` (or its ``chunks`` equivalent) is provided and
    carries VLM enrichment, each page's ``enrichment`` column is
    populated with the figure descriptions referenced by any chunk on
    that page. This is a best-effort correlation: ``IngestResult`` does
    not expose per-figure page numbers directly, so we rely on the
    chunker's ``related_figures`` cross-reference to locate them.

    Args:
        doc_id: Parent document identifier.
        visual_embeddings: One embedding per page, ordered by page number.
        page_images: Optional PNG bytes per page, parallel to embeddings.
        page_structures: Optional structure dict per page, parallel to
            embeddings.
        result: Optional full ``IngestResult`` for enrichment extraction.
        chunks: Optional explicit chunk list for enrichment correlation.
            Falls back to ``result.chunks`` when not provided.

    Returns:
        List of dicts with keys matching ``KojiClient.insert_pages``
        format: ``id``, ``doc_id``, ``page_num``, ``embedding``,
        ``image`` (optional), ``structure`` (optional),
        ``enrichment`` (optional).
    """
    records: list[dict[str, Any]] = []

    # Pre-compute per-page enrichment from chunks (if available).
    enrichment_data: dict[str, Any] = {}
    if result is not None:
        enrichment_data = _coerce_enrichment_result(
            getattr(result, "enrichment_result", None)
        )

    figures_by_id = _index_figures_by_id(enrichment_data)

    source_chunks: list[TextChunk] | None = chunks
    if source_chunks is None and result is not None:
        source_chunks = list(getattr(result, "chunks", []) or [])

    page_figures: dict[int, list[dict[str, Any]]] = {}
    seen_per_page: dict[int, set[str]] = {}
    if figures_by_id and source_chunks:
        for chunk in source_chunks:
            context = getattr(chunk, "context", None)
            related = (
                list(getattr(context, "related_figures", []) or [])
                if context is not None
                else []
            )
            if not related:
                continue
            chunk_page = getattr(chunk, "page", None) or 1
            bucket = page_figures.setdefault(chunk_page, [])
            seen = seen_per_page.setdefault(chunk_page, set())
            for fig_id in related:
                if fig_id in seen:
                    continue
                fig_data = figures_by_id.get(fig_id)
                if not fig_data or not fig_data.get("description"):
                    continue
                bucket.append({
                    "figure_id": fig_id,
                    "description": fig_data.get("description"),
                    "classification": fig_data.get("classification"),
                })
                seen.add(fig_id)

    for idx, emb in enumerate(visual_embeddings):
        page_num = idx + 1
        page_id = f"{doc_id}-page{page_num:03d}"

        record: dict[str, Any] = {
            "id": page_id,
            "doc_id": doc_id,
            "page_num": page_num,
            "embedding": emb.to_blob(),
        }

        if page_images is not None and idx < len(page_images):
            record["image"] = page_images[idx]

        if page_structures is not None and idx < len(page_structures):
            record["structure"] = page_structures[idx]

        figures_on_page = page_figures.get(page_num)
        if figures_on_page:
            record["enrichment"] = {"figures": figures_on_page}

        records.append(record)

    logger.debug(
        "result_mapper.map_page_records",
        doc_id=doc_id,
        page_count=len(records),
        pages_with_enrichment=sum(1 for r in records if "enrichment" in r),
    )

    return records


def map_chunk_records(
    doc_id: str,
    result: IngestResult,
) -> list[dict[str, Any]]:
    """Build chunk record dicts from an IngestResult's chunks and embeddings.

    Maps Shikomi's ``TextChunk`` fields to the dict format expected by
    :meth:`KojiClient.insert_chunks`:

    - ``chunk.content`` -> ``"text"``
    - ``chunk.page`` -> ``"page_num"`` (defaults to ``1`` when ``None``)
    - ``chunk.context.to_dict()`` -> ``"context"`` (omitted when absent)
    - ``chunk.start_time`` / ``chunk.end_time`` -> included only when not
      ``None`` (audio sources)

    When VLM enrichment is available, each chunk's ``enrichment`` field
    is populated with the figure descriptions it references (via
    ``context.related_figures``).

    When the number of text embeddings does not match the chunk count, a
    warning is logged and embedding assignment falls back to index-safe
    access.

    Args:
        doc_id: Parent document identifier.
        result: Completed ingest result containing ``chunks`` and
            ``text_embeddings``.

    Returns:
        List of dicts with keys matching ``KojiClient.insert_chunks``
        format.
    """
    chunks: list[TextChunk] = result.chunks
    embeddings: list[MultiVectorEmbedding] = result.text_embeddings

    if len(chunks) != len(embeddings):
        logger.warning(
            "result_mapper.map_chunk_records.length_mismatch",
            doc_id=doc_id,
            chunk_count=len(chunks),
            embedding_count=len(embeddings),
        )

    enrichment_data = _coerce_enrichment_result(
        getattr(result, "enrichment_result", None)
    )
    figures_by_id = _index_figures_by_id(enrichment_data)

    records: list[dict[str, Any]] = []

    for idx, chunk in enumerate(chunks):
        record: dict[str, Any] = {
            "id": chunk.id,
            "doc_id": doc_id,
            "page_num": chunk.page if chunk.page is not None else 1,
            "text": chunk.content,
            "word_count": chunk.word_count,
        }

        if idx < len(embeddings):
            record["embedding"] = embeddings[idx].to_blob()

        if chunk.context is not None:
            record["context"] = chunk.context.to_dict()

        if chunk.start_time is not None:
            record["start_time"] = chunk.start_time

        if chunk.end_time is not None:
            record["end_time"] = chunk.end_time

        chunk_enrichment = _build_chunk_enrichment(chunk, figures_by_id)
        if chunk_enrichment is not None:
            record["enrichment"] = chunk_enrichment

        records.append(record)

    logger.debug(
        "result_mapper.map_chunk_records",
        doc_id=doc_id,
        chunk_count=len(records),
        chunks_with_enrichment=sum(1 for r in records if "enrichment" in r),
    )

    return records


def build_synthetic_enrichment_chunks(
    doc_id: str,
    result: IngestResult,
) -> list[SyntheticEnrichmentChunk]:
    """Generate synthetic chunks from VLM enrichment output.

    These carry only ``text`` and metadata. The caller (typically
    ``DocumentProcessor``) must embed each chunk's text via the shared
    ``ColNomicEngine`` and then convert them to regular chunk records
    for insertion into Koji.

    The synthetic chunks produced:

    1. **Document summary** — one chunk on page 1 with the Gemma doc
       summary, key points, and topics joined into a paragraph. ID:
       ``{doc_id}:enrichment-summary``.
    2. **Figure captions** — one chunk per figure with a non-empty
       ``description``. Page is inferred from any organic chunk that
       references the figure, else defaults to 1. ID:
       ``{doc_id}:enrichment-figure-{figure_id}``.
    3. **Code block analysis** — one chunk per code block with a
       non-empty ``summary``. Page is 1 when unknown. ID:
       ``{doc_id}:enrichment-code-{index}``.
    4. **Formula interpretation** — one chunk per formula with a
       non-empty ``interpretation``. ID:
       ``{doc_id}:enrichment-formula-{index}``.

    Args:
        doc_id: Parent document identifier.
        result: Completed ingest result.

    Returns:
        List of synthetic chunks ready for embedding (possibly empty).
    """
    enrichment_data = _coerce_enrichment_result(
        getattr(result, "enrichment_result", None)
    )
    if not enrichment_data:
        return []

    synthetic: list[SyntheticEnrichmentChunk] = []

    # -- Correlate figures to pages via organic chunks -------------------
    source_chunks = list(getattr(result, "chunks", []) or [])
    figure_page: dict[str, int] = {}
    for chunk in source_chunks:
        context = getattr(chunk, "context", None)
        related = (
            list(getattr(context, "related_figures", []) or [])
            if context is not None
            else []
        )
        if not related:
            continue
        page = getattr(chunk, "page", None) or 1
        for fig_id in related:
            figure_page.setdefault(fig_id, page)

    # -- 1. Document summary ----------------------------------------------
    doc_summary = enrichment_data.get("document_summary") or {}
    semantic = enrichment_data.get("semantic_metadata") or {}
    summary_text_parts: list[str] = []
    summary = doc_summary.get("summary")
    if summary:
        summary_text_parts.append(summary)
    key_points = doc_summary.get("key_points") or []
    if key_points:
        summary_text_parts.append(
            "Key points: " + "; ".join(str(kp) for kp in key_points)
        )
    topics = semantic.get("topics") or []
    if topics:
        summary_text_parts.append(
            "Topics: " + ", ".join(str(t) for t in topics)
        )
    if summary_text_parts:
        synthetic.append(SyntheticEnrichmentChunk(
            chunk_id=f"{doc_id}:enrichment-summary",
            text="\n\n".join(summary_text_parts),
            page_num=1,
            enrichment={
                "source": "document_summary",
                "document_type": doc_summary.get("document_type"),
            },
        ))

    # -- 2. Figure captions ----------------------------------------------
    for fig in enrichment_data.get("figures") or []:
        fig_id = fig.get("figure_id")
        desc = fig.get("description")
        if not fig_id or not desc:
            continue
        classification = fig.get("classification") or "figure"
        page = figure_page.get(fig_id, 1)
        synthetic.append(SyntheticEnrichmentChunk(
            chunk_id=f"{doc_id}:enrichment-figure-{fig_id}",
            text=f"{classification.capitalize()}: {desc}",
            page_num=page,
            enrichment={
                "source": "figure_caption",
                "figure_id": fig_id,
                "classification": fig.get("classification"),
                "confidence": fig.get("confidence"),
            },
        ))

    # -- 3. Code block analysis ------------------------------------------
    for code in enrichment_data.get("code_blocks") or []:
        summary_text = code.get("summary")
        if not summary_text:
            continue
        idx = code.get("block_index", 0)
        language = code.get("language") or ""
        purpose = code.get("purpose") or ""
        parts = []
        if purpose:
            parts.append(f"Purpose: {purpose}")
        parts.append(f"Summary: {summary_text}")
        prefix = f"{language} code block" if language else "Code block"
        text = f"{prefix}. " + " ".join(parts)
        synthetic.append(SyntheticEnrichmentChunk(
            chunk_id=f"{doc_id}:enrichment-code-{idx}",
            text=text,
            page_num=1,
            enrichment={
                "source": "code_block",
                "block_index": idx,
                "language": language or None,
            },
        ))

    # -- 4. Formula interpretation ---------------------------------------
    for formula in enrichment_data.get("formulas") or []:
        interp = formula.get("interpretation")
        if not interp:
            continue
        idx = formula.get("formula_index", 0)
        plain = formula.get("plain_text") or ""
        text = f"Formula: {plain}. Interpretation: {interp}" if plain else f"Formula interpretation: {interp}"
        synthetic.append(SyntheticEnrichmentChunk(
            chunk_id=f"{doc_id}:enrichment-formula-{idx}",
            text=text,
            page_num=1,
            enrichment={
                "source": "formula",
                "formula_index": idx,
            },
        ))

    logger.debug(
        "result_mapper.build_synthetic_enrichment_chunks",
        doc_id=doc_id,
        count=len(synthetic),
    )
    return synthetic


def synthetic_to_chunk_records(
    doc_id: str,
    synthetic: list[SyntheticEnrichmentChunk],
    embeddings: list[MultiVectorEmbedding],
) -> list[dict[str, Any]]:
    """Pair synthetic enrichment chunks with their fresh embeddings.

    The caller produced embeddings via
    :meth:`ShikomiIngester.embed_texts` (preserving order). This helper
    zips them into dicts ready for :meth:`KojiClient.insert_chunks`.

    Args:
        doc_id: Parent document identifier.
        synthetic: Output from :func:`build_synthetic_enrichment_chunks`.
        embeddings: Multi-vector embeddings in the same order.

    Returns:
        List of chunk dicts, one per synthetic chunk that has an
        embedding. Mismatched lengths are logged and truncated.
    """
    if len(synthetic) != len(embeddings):
        logger.warning(
            "result_mapper.synthetic_to_chunk_records.length_mismatch",
            doc_id=doc_id,
            synthetic_count=len(synthetic),
            embedding_count=len(embeddings),
        )

    records: list[dict[str, Any]] = []
    for item, emb in zip(synthetic, embeddings):
        records.append({
            "id": item.chunk_id,
            "doc_id": doc_id,
            "page_num": item.page_num,
            "text": item.text,
            "embedding": emb.to_blob(),
            "word_count": len(item.text.split()),
            "enrichment": item.enrichment,
        })
    return records

"""Pure mapping functions from Shikomi IngestResult to Koji record dicts.

This module bridges the type gap between Shikomi's ingest output and the
record formats expected by :class:`~src.storage.koji_client.KojiClient`.
All functions are pure -- no I/O, no side effects, no database access.

Key field translations:

- ``TextChunk.content`` -> ``"text"`` (Koji chunks table)
- ``TextChunk.page`` -> ``"page_num"`` (Koji chunks table, defaults to 1)
- ``MultiVectorEmbedding.to_blob()`` -> ``"embedding"`` (binary column)
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from shikomi import IngestResult
    from shikomi.types import MultiVectorEmbedding, TextChunk

logger = structlog.get_logger(__name__)


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
        ``metadata``, ``project_id``.
    """
    _, ext = os.path.splitext(filename)
    file_format = ext.lstrip(".").lower() if ext else ""

    resolved_pages = num_pages
    if resolved_pages is None and result.visual_embeddings:
        resolved_pages = len(result.visual_embeddings)

    record: dict[str, Any] = {
        "doc_id": result.content_hash,
        "filename": filename,
        "format": file_format,
        "num_pages": resolved_pages,
        "markdown": result.markdown_content,
        "metadata": result.metadata,
        "project_id": project_id,
    }

    logger.debug(
        "result_mapper.map_document_record",
        doc_id=result.content_hash,
        filename=filename,
        format=file_format,
        num_pages=resolved_pages,
        project_id=project_id,
    )

    return record


def map_page_records(
    doc_id: str,
    visual_embeddings: list[MultiVectorEmbedding],
    page_images: list[bytes] | None = None,
    page_structures: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Build page record dicts from visual embeddings and optional images.

    Page numbering is 1-indexed. The page ID follows the convention
    ``"{doc_id}-page{num:03d}"``.

    Args:
        doc_id: Parent document identifier.
        visual_embeddings: One embedding per page, ordered by page number.
        page_images: Optional PNG bytes per page, parallel to embeddings.
        page_structures: Optional structure dict per page, parallel to
            embeddings.

    Returns:
        List of dicts with keys matching ``KojiClient.insert_pages``
        format: ``id``, ``doc_id``, ``page_num``, ``embedding``,
        ``image`` (optional), ``structure`` (optional).
    """
    records: list[dict[str, Any]] = []

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

        records.append(record)

    logger.debug(
        "result_mapper.map_page_records",
        doc_id=doc_id,
        page_count=len(records),
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

        records.append(record)

    logger.debug(
        "result_mapper.map_chunk_records",
        doc_id=doc_id,
        chunk_count=len(records),
    )

    return records

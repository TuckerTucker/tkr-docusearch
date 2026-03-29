"""Tests for result_mapper -- IngestResult to Koji record mapping."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from shikomi import IngestResult
from shikomi.types import ChunkContext, MultiVectorEmbedding, TextChunk

from src.processing.result_mapper import (
    map_chunk_records,
    map_document_record,
    map_page_records,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_embedding(num_tokens: int = 10, dim: int = 128) -> MultiVectorEmbedding:
    """Create a deterministic MultiVectorEmbedding for testing."""
    data = np.random.randn(num_tokens, dim).astype(np.float32)
    return MultiVectorEmbedding(num_tokens=num_tokens, dim=dim, data=data)


def _make_chunk(
    chunk_id: str = "chunk-001",
    content: str = "The quick brown fox jumps over the lazy dog.",
    page: int | None = 1,
    start_time: float | None = None,
    end_time: float | None = None,
    context: ChunkContext | None = None,
) -> TextChunk:
    """Create a TextChunk with sensible defaults."""
    return TextChunk(
        id=chunk_id,
        content=content,
        source_path="/tmp/test.pdf",
        start_char=0,
        end_char=len(content),
        start_time=start_time,
        end_time=end_time,
        context=context,
        page=page,
    )


def _make_ingest_result(
    chunks: list[TextChunk] | None = None,
    text_embeddings: list[MultiVectorEmbedding] | None = None,
    visual_embeddings: list[MultiVectorEmbedding] | None = None,
    content_hash: str = "abc123hash",
    markdown_content: str | None = "# Test Document\n\nSome content.",
    metadata: dict[str, Any] | None = None,
    vtt_content: str | None = None,
) -> IngestResult:
    """Create an IngestResult with sensible defaults."""
    if chunks is None:
        chunks = [_make_chunk()]
    if text_embeddings is None:
        text_embeddings = [_make_embedding() for _ in chunks]

    return IngestResult(
        chunks=chunks,
        text_embeddings=text_embeddings,
        visual_embeddings=visual_embeddings,
        content_hash=content_hash,
        markdown_content=markdown_content,
        metadata=metadata if metadata is not None else {"source": "test"},
        source_path="/tmp/test.pdf",
        source_type="pdf",
        chunk_count=len(chunks),
        vtt_content=vtt_content,
    )


# ---------------------------------------------------------------------------
# map_document_record tests
# ---------------------------------------------------------------------------


class TestMapDocumentRecord:
    """Tests for map_document_record."""

    def test_basic(self) -> None:
        """Create an IngestResult with known fields and verify mapping."""
        result = _make_ingest_result(content_hash="deadbeef42")
        record = map_document_record(
            result, filename="report.pdf", project_id="proj-1",
        )

        assert record["doc_id"] == "deadbeef42"
        assert record["filename"] == "report.pdf"
        assert record["format"] == "pdf"
        assert record["project_id"] == "proj-1"
        assert record["markdown"] == "# Test Document\n\nSome content."

    def test_infers_pages_from_visual_embeddings(self) -> None:
        """When num_pages is None, infer from visual_embeddings length."""
        vis = [_make_embedding() for _ in range(3)]
        result = _make_ingest_result(visual_embeddings=vis)

        record = map_document_record(
            result, filename="slides.pdf", project_id="default",
        )

        assert record["num_pages"] == 3

    def test_explicit_num_pages_overrides_inference(self) -> None:
        """Explicit num_pages wins over visual_embeddings length."""
        vis = [_make_embedding() for _ in range(5)]
        result = _make_ingest_result(visual_embeddings=vis)

        record = map_document_record(
            result, filename="doc.pdf", project_id="default", num_pages=10,
        )

        assert record["num_pages"] == 10

    def test_format_extracted_from_extension(self) -> None:
        """File extension is lowercased and stripped of the leading dot."""
        result = _make_ingest_result()

        record = map_document_record(
            result, filename="README.MD", project_id="default",
        )

        assert record["format"] == "md"

    def test_no_extension_yields_empty_format(self) -> None:
        """A filename without an extension produces an empty format string."""
        result = _make_ingest_result()

        record = map_document_record(
            result, filename="Makefile", project_id="default",
        )

        assert record["format"] == ""

    def test_no_pages_without_visual_embeddings(self) -> None:
        """Without visual embeddings or explicit count, num_pages is None."""
        result = _make_ingest_result(visual_embeddings=None)

        record = map_document_record(
            result, filename="notes.txt", project_id="default",
        )

        assert record["num_pages"] is None


# ---------------------------------------------------------------------------
# map_page_records tests
# ---------------------------------------------------------------------------


class TestMapPageRecords:
    """Tests for map_page_records."""

    def test_basic(self) -> None:
        """Two visual embeddings produce two page records."""
        embs = [_make_embedding(), _make_embedding()]
        records = map_page_records(doc_id="doc-abc", visual_embeddings=embs)

        assert len(records) == 2

        # Page numbering is 1-indexed
        assert records[0]["page_num"] == 1
        assert records[1]["page_num"] == 2

        # ID format is "{doc_id}-page{num:03d}"
        assert records[0]["id"] == "doc-abc-page001"
        assert records[1]["id"] == "doc-abc-page002"

        # Embedding is bytes
        assert isinstance(records[0]["embedding"], bytes)
        assert len(records[0]["embedding"]) > 0

    def test_with_images(self) -> None:
        """Page images are included when provided."""
        embs = [_make_embedding(), _make_embedding()]
        img_bytes = [b"\x89PNG-page1", b"\x89PNG-page2"]

        records = map_page_records(
            doc_id="doc-img",
            visual_embeddings=embs,
            page_images=img_bytes,
        )

        assert records[0]["image"] == b"\x89PNG-page1"
        assert records[1]["image"] == b"\x89PNG-page2"

    def test_without_images(self) -> None:
        """When page_images is None, records have no 'image' key."""
        embs = [_make_embedding()]
        records = map_page_records(
            doc_id="doc-no-img", visual_embeddings=embs,
        )

        assert "image" not in records[0]

    def test_doc_id_propagated(self) -> None:
        """Each page record has the parent doc_id."""
        embs = [_make_embedding()]
        records = map_page_records(doc_id="parent-doc", visual_embeddings=embs)

        assert records[0]["doc_id"] == "parent-doc"


# ---------------------------------------------------------------------------
# map_chunk_records tests
# ---------------------------------------------------------------------------


class TestMapChunkRecords:
    """Tests for map_chunk_records."""

    def test_field_mapping(self) -> None:
        """Verify Shikomi field names are translated to Koji field names."""
        ctx = ChunkContext(parent_heading="Introduction", element_type="text")
        chunk = _make_chunk(
            chunk_id="c-001",
            content="Hello world this is a test sentence.",
            page=3,
            start_time=1.5,
            end_time=4.2,
            context=ctx,
        )
        result = _make_ingest_result(chunks=[chunk])

        records = map_chunk_records(doc_id="doc-x", result=result)
        assert len(records) == 1

        rec = records[0]

        # content -> text
        assert rec["text"] == "Hello world this is a test sentence."
        # page -> page_num
        assert rec["page_num"] == 3
        # word_count from property
        assert rec["word_count"] == 7
        # audio timestamps
        assert rec["start_time"] == 1.5
        assert rec["end_time"] == 4.2
        # context serialized to dict
        assert isinstance(rec["context"], dict)
        assert rec["context"]["parent_heading"] == "Introduction"

    def test_none_page_defaults_to_1(self) -> None:
        """Chunk with page=None defaults page_num to 1."""
        chunk = _make_chunk(chunk_id="c-002", page=None)
        result = _make_ingest_result(chunks=[chunk])

        records = map_chunk_records(doc_id="doc-y", result=result)

        assert records[0]["page_num"] == 1

    def test_optional_fields_omitted(self) -> None:
        """Chunks without start_time, end_time, context omit those keys."""
        chunk = _make_chunk(
            chunk_id="c-003",
            start_time=None,
            end_time=None,
            context=None,
        )
        result = _make_ingest_result(chunks=[chunk])

        records = map_chunk_records(doc_id="doc-z", result=result)
        rec = records[0]

        assert "start_time" not in rec
        assert "end_time" not in rec
        assert "context" not in rec

    def test_embedding_assigned(self) -> None:
        """Each chunk record gets the corresponding embedding as bytes."""
        chunk = _make_chunk(chunk_id="c-004")
        emb = _make_embedding(num_tokens=5, dim=64)
        result = _make_ingest_result(chunks=[chunk], text_embeddings=[emb])

        records = map_chunk_records(doc_id="doc-e", result=result)

        assert "embedding" in records[0]
        assert isinstance(records[0]["embedding"], bytes)
        assert len(records[0]["embedding"]) > 0

    def test_chunk_id_preserved(self) -> None:
        """The chunk's original id is carried through to the record."""
        chunk = _make_chunk(chunk_id="custom-id-999")
        result = _make_ingest_result(chunks=[chunk])

        records = map_chunk_records(doc_id="doc-id", result=result)

        assert records[0]["id"] == "custom-id-999"
        assert records[0]["doc_id"] == "doc-id"

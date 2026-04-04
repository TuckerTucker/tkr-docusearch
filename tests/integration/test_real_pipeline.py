"""Real integration tests for the document processing pipeline.

Exercises the actual shikomi ingestion pipeline and DocuSearch storage
layer with real fixture files. Uses a mock embedding engine (no GPU)
but real parsing, rendering, chunking, and Koji storage.

The integration boundary is ``ShikomiIngester.process()`` — we treat
shikomi as a black box and validate its outputs, then verify those
outputs are correctly stored in Koji via ``DocumentProcessor``.

Requirements:
    - shikomi (``pip install shikomi``)
    - pdf2image + poppler (``pip install pdf2image && brew install poppler``)
    - LibreOffice for DOCX/PPTX (``brew install --cask libreoffice``)

Tests skip gracefully when optional dependencies are unavailable.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest

from shikomi.config import RenderConfig
from shikomi.types import MultiVectorEmbedding

# ---------------------------------------------------------------------------
# Skip conditions
# ---------------------------------------------------------------------------

_pdf2image_available = False
try:
    import pdf2image  # noqa: F401

    _pdf2image_available = True
except ImportError:
    pass

_soffice_available = False
try:
    from shikomi.parser.renderer import discover_soffice

    _soffice_available = discover_soffice() is not None
except ImportError:
    pass

requires_pdf2image = pytest.mark.skipif(
    not _pdf2image_available,
    reason="pdf2image not installed (pip install pdf2image)",
)
requires_soffice = pytest.mark.skipif(
    not _soffice_available,
    reason="LibreOffice not installed (brew install --cask libreoffice)",
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _make_mock_engine(dim: int = 128) -> MagicMock:
    """Build a mock ColNomicEngine that returns proper-shape embeddings."""
    engine = MagicMock()

    def _fake_encode(items: list) -> list:
        return [
            MultiVectorEmbedding(
                num_tokens=32,
                dim=dim,
                data=np.random.randn(32, dim).astype(np.float32),
            )
            for _ in items
        ]

    engine.encode_documents = AsyncMock(side_effect=_fake_encode)
    engine.encode_images = AsyncMock(side_effect=_fake_encode)
    engine.encode_queries = AsyncMock(side_effect=_fake_encode)
    engine.close = MagicMock()
    return engine


@pytest.fixture
def mock_engine() -> MagicMock:
    """Mock ColNomicEngine -- valid-shape embeddings, no GPU required."""
    return _make_mock_engine()


@pytest.fixture
def koji_storage(tmp_path):
    """Real KojiClient backed by a temporary file database."""
    from src.config.koji_config import KojiConfig
    from src.storage.koji_client import KojiClient

    config = KojiConfig(db_path=str(tmp_path / "real_test.db"))
    client = KojiClient(config)
    client.open()
    yield client
    client.close()


@pytest.fixture
def make_real_processor(mock_engine, koji_storage):
    """Factory: DocumentProcessor with real shikomi ingestion + real Koji.

    Uses a real ``ShikomiIngester`` wrapping a real ``shikomi.Ingester``
    (real Docling parsing, real LibreOffice rendering) with a mock
    embedding engine (no GPU).
    """
    from shikomi.parser.renderer import LibreOfficeRenderer

    from src.processing.processor import DocumentProcessor
    from src.processing.shikomi_ingester import ShikomiIngester

    renderer = LibreOfficeRenderer(RenderConfig(dpi=150))

    ingester = ShikomiIngester(
        engine=mock_engine,
        renderer=renderer,
        generate_vtt=False,
        generate_markdown=False,
    )
    ingester.connect()

    processor = DocumentProcessor(
        ingester=ingester,
        storage_client=koji_storage,
    )

    yield processor
    ingester.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _assert_valid_image(data: bytes) -> None:
    """Assert that data is a valid image (PNG or JPEG)."""
    from PIL import Image

    img = Image.open(BytesIO(data))
    assert img.format in ("PNG", "JPEG"), f"Expected PNG/JPEG, got {img.format}"
    assert img.width > 0
    assert img.height > 0


# ===========================================================================
# ShikomiIngester.process() — validate IngestResult
# ===========================================================================


@requires_pdf2image
class TestShikomiIngestsPDF:
    """Shikomi processes a real PDF and returns a valid IngestResult."""

    def test_produces_text_chunks(self, make_real_processor) -> None:
        """PDF ingestion extracts real text into chunks."""
        result = make_real_processor.ingester.process(
            str(FIXTURES / "sample.pdf"),
        )

        assert result.source_type == "document"
        assert result.chunk_count >= 1
        assert len(result.chunks) == result.chunk_count

        # Chunks contain actual document content, not canned data
        all_text = " ".join(c.content for c in result.chunks)
        assert "Test Document" in all_text

    def test_produces_text_embeddings(self, make_real_processor) -> None:
        """Each chunk has a corresponding embedding."""
        result = make_real_processor.ingester.process(
            str(FIXTURES / "sample.pdf"),
        )

        assert len(result.text_embeddings) == result.chunk_count
        for emb in result.text_embeddings:
            assert emb.num_tokens > 0
            assert emb.dim == 128

    def test_content_hash_is_deterministic(self, make_real_processor) -> None:
        """Processing the same file twice produces the same content hash."""
        r1 = make_real_processor.ingester.process(str(FIXTURES / "sample.pdf"))
        r2 = make_real_processor.ingester.process(str(FIXTURES / "sample.pdf"))

        assert r1.content_hash == r2.content_hash
        assert len(r1.content_hash) > 16


@requires_pdf2image
class TestShikomiIngestsImage:
    """Shikomi processes a real image with visual embedding."""

    def test_image_produces_visual_embeddings(
        self, make_real_processor,
    ) -> None:
        """Image ingestion produces visual embeddings and page images."""
        result = make_real_processor.ingester.process(
            str(FIXTURES / "sample.png"),
        )

        assert result.source_type == "image"
        assert result.visual_embeddings is not None
        assert len(result.visual_embeddings) == 1
        assert result.visual_embeddings[0].dim == 128

    def test_image_produces_page_image_bytes(
        self, make_real_processor,
    ) -> None:
        """Image ingestion returns renderable page image bytes."""
        result = make_real_processor.ingester.process(
            str(FIXTURES / "sample.png"),
        )

        assert result.page_images is not None
        assert len(result.page_images) == 1
        _assert_valid_image(result.page_images[0])


@requires_pdf2image
@requires_soffice
class TestShikomiIngestsDOCX:
    """Shikomi processes a real DOCX via LibreOffice rendering."""

    def test_docx_produces_text_chunks(self, make_real_processor) -> None:
        """DOCX ingestion extracts real text."""
        result = make_real_processor.ingester.process(
            str(FIXTURES / "sample.docx"),
        )

        assert result.source_type == "document"
        assert result.chunk_count >= 1

        all_text = " ".join(c.content for c in result.chunks)
        assert len(all_text) > 50

    def test_docx_has_embeddings(self, make_real_processor) -> None:
        """DOCX text chunks have corresponding embeddings."""
        result = make_real_processor.ingester.process(
            str(FIXTURES / "sample.docx"),
        )

        assert len(result.text_embeddings) == result.chunk_count


# ===========================================================================
# DocumentProcessor → Koji — validate storage round-trip
# ===========================================================================


@requires_pdf2image
class TestProcessorStoresInKoji:
    """DocumentProcessor stores real ingestion results into real Koji."""

    def test_pdf_document_record(
        self, make_real_processor, koji_storage,
    ) -> None:
        """PDF produces a document record with correct metadata."""
        confirmation = make_real_processor.process_document(
            str(FIXTURES / "sample.pdf"),
        )

        doc = koji_storage.get_document(confirmation.doc_id)
        assert doc is not None
        assert doc["filename"] == "sample.pdf"
        assert doc["format"] == "pdf"

    def test_pdf_chunk_records(
        self, make_real_processor, koji_storage,
    ) -> None:
        """PDF chunks stored in Koji contain real extracted text."""
        confirmation = make_real_processor.process_document(
            str(FIXTURES / "sample.pdf"),
        )

        chunks = koji_storage.get_chunks_for_document(confirmation.doc_id)
        assert len(chunks) >= 1

        for chunk in chunks:
            assert chunk["text"] is not None
            assert len(chunk["text"].strip()) > 0
            assert chunk["embedding"] is not None

        # Verify actual content, not canned mock data
        all_text = " ".join(c["text"] for c in chunks)
        assert "Test Document" in all_text

    def test_image_page_record(
        self, make_real_processor, koji_storage,
    ) -> None:
        """PNG produces a page record with visual embedding in Koji."""
        confirmation = make_real_processor.process_document(
            str(FIXTURES / "sample.png"),
        )

        pages = koji_storage.get_pages_for_document(confirmation.doc_id)
        assert len(pages) == 1

        page = pages[0]
        assert page["page_num"] == 1
        assert page["embedding"] is not None
        assert len(page["embedding"]) > 0

    def test_status_callbacks(
        self, make_real_processor, koji_storage,
    ) -> None:
        """Status callbacks fire with real processing stages."""
        from src.processing.processor import ProcessingStatus

        statuses: list[ProcessingStatus] = []
        make_real_processor.process_document(
            str(FIXTURES / "sample.pdf"),
            status_callback=statuses.append,
        )

        status_names = [s.status for s in statuses]

        # DocuSearch-owned stages
        assert "processing" in status_names
        assert "completed" in status_names

        # Shikomi stages forwarded via StatusBridge
        forwarded = {"parsing", "chunking", "embedding_text"}
        assert forwarded.intersection(status_names), (
            f"Expected shikomi stages in {status_names}"
        )

    def test_two_documents_isolated(
        self, make_real_processor, koji_storage,
    ) -> None:
        """Processing two files produces distinct, non-overlapping records."""
        c1 = make_real_processor.process_document(str(FIXTURES / "sample.pdf"))
        c2 = make_real_processor.process_document(str(FIXTURES / "sample.png"))

        assert c1.doc_id != c2.doc_id

        chunks_1 = koji_storage.get_chunks_for_document(c1.doc_id)
        chunks_2 = koji_storage.get_chunks_for_document(c2.doc_id)

        ids_1 = {c["id"] for c in chunks_1}
        ids_2 = {c["id"] for c in chunks_2}
        assert ids_1.isdisjoint(ids_2)

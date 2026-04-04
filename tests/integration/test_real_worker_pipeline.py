"""Real pipeline tests through the processing worker.

Exercises the actual shikomi ingestion pipeline (real Docling parsing,
real LibreOffice rendering) via the worker's ``process_job()`` function.
Only the embedding engine is mocked (no GPU required).

Requirements:
    - pdf2image + poppler (``pip install pdf2image && brew install poppler``)
    - LibreOffice for DOCX (``brew install --cask libreoffice``)
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest

from shikomi.config import RenderConfig
from shikomi.types import MultiVectorEmbedding

from src.config.koji_config import KojiConfig
from src.processing.processor import DocumentProcessor
from src.processing.shikomi_ingester import ShikomiIngester
from src.processing.worker import process_job
from src.storage.koji_client import KojiClient

# ---------------------------------------------------------------------------
# Skip conditions
# ---------------------------------------------------------------------------

_pdf2image_available = False
try:
    import pdf2image  # noqa: F401

    _pdf2image_available = True
except ImportError:
    pass

requires_pdf2image = pytest.mark.skipif(
    not _pdf2image_available,
    reason="pdf2image not installed",
)

FIXTURES = Path(__file__).parent.parent / "fixtures"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_mock_engine(dim: int = 128) -> MagicMock:
    """Mock ColNomicEngine with proper-shape embeddings."""
    engine = MagicMock()

    def _fake_encode(items: list) -> list:
        return [
            MultiVectorEmbedding(
                num_tokens=32, dim=dim,
                data=np.random.randn(32, dim).astype(np.float32),
            )
            for _ in items
        ]

    engine.encode_documents = AsyncMock(side_effect=_fake_encode)
    engine.encode_images = AsyncMock(side_effect=_fake_encode)
    engine.close = MagicMock()
    return engine


@pytest.fixture
def koji(tmp_path):
    """Real KojiClient with fresh database."""
    config = KojiConfig(db_path=str(tmp_path / "real_worker.db"))
    client = KojiClient(config)
    client.open()
    yield client
    client.close()


@pytest.fixture
def real_processor(koji):
    """DocumentProcessor with real shikomi parsing + mock embeddings."""
    from shikomi.parser.renderer import LibreOfficeRenderer

    mock_engine = _make_mock_engine()
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
        storage_client=koji,
    )
    yield processor
    ingester.close()


# ===========================================================================
# Real Pipeline Through Worker
# ===========================================================================


@requires_pdf2image
class TestRealWorkerPipeline:
    """Worker processes real files via shikomi + stores in Koji."""

    def test_pdf_through_worker(self, koji, real_processor) -> None:
        """Worker processes a real PDF: parse, chunk, embed, store."""
        koji.create_job("pdf1", "sample.pdf", str(FIXTURES / "sample.pdf"))
        job = koji.claim_next_job()

        process_job(job, real_processor, koji)

        # Job completed
        assert koji.get_job("pdf1")["status"] == "completed"

        # Document stored with real extracted text
        docs = koji.list_documents()
        assert len(docs) >= 1

        doc_id = docs[0]["doc_id"]
        chunks = koji.get_chunks_for_document(doc_id)
        assert len(chunks) >= 1

        all_text = " ".join(c["text"] for c in chunks)
        assert "Test Document" in all_text

    def test_image_through_worker(self, koji, real_processor) -> None:
        """Worker processes a real PNG with visual embedding."""
        koji.create_job("png1", "sample.png", str(FIXTURES / "sample.png"))
        job = koji.claim_next_job()

        process_job(job, real_processor, koji)

        assert koji.get_job("png1")["status"] == "completed"

        docs = koji.list_documents()
        doc_id = docs[0]["doc_id"]
        pages = koji.get_pages_for_document(doc_id)
        assert len(pages) == 1
        assert pages[0]["embedding"] is not None

    def test_two_files_in_sequence(self, koji, real_processor) -> None:
        """Worker handles two jobs sequentially."""
        koji.create_job("seq1", "sample.pdf", str(FIXTURES / "sample.pdf"))
        koji.create_job("seq2", "sample.png", str(FIXTURES / "sample.png"))

        for _ in range(2):
            job = koji.claim_next_job()
            process_job(job, real_processor, koji)

        assert koji.get_job("seq1")["status"] == "completed"
        assert koji.get_job("seq2")["status"] == "completed"

        docs = koji.list_documents()
        assert len(docs) >= 2

    def test_status_callbacks_written_to_koji(
        self, koji, real_processor,
    ) -> None:
        """Processing status callbacks update the job in Koji."""
        koji.create_job("cb1", "sample.pdf", str(FIXTURES / "sample.pdf"))
        job = koji.claim_next_job()

        process_job(job, real_processor, koji)

        # After completion the job should be marked completed
        result = koji.get_job("cb1")
        assert result["status"] == "completed"
        assert result["completed_at"] is not None

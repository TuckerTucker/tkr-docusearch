"""Shared fixtures for processing pipeline tests.

Provides mock engines, real Koji clients, processor factories, and
status callback collectors used across all test_pipeline_*, test_error_*,
test_status_*, and test_multi_document_* test files.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.config.koji_config import KojiConfig
from src.core.testing.mocks import MockKojiClient, MockShikomiIngester
from src.processing.processor import DocumentProcessor, ProcessingStatus
from src.storage.koji_client import KojiClient


# ---------------------------------------------------------------------------
# Fixture file paths
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to tests/fixtures/ containing sample documents."""
    return FIXTURES_DIR


@pytest.fixture
def sample_pdf() -> Path:
    """Path to sample.pdf fixture."""
    return FIXTURES_DIR / "sample.pdf"


@pytest.fixture
def sample_docx() -> Path:
    """Path to sample.docx fixture."""
    return FIXTURES_DIR / "sample.docx"


@pytest.fixture
def sample_md() -> Path:
    """Path to sample.md fixture."""
    return FIXTURES_DIR / "sample.md"


@pytest.fixture
def sample_html() -> Path:
    """Path to sample.html fixture."""
    return FIXTURES_DIR / "sample.html"


@pytest.fixture
def sample_csv() -> Path:
    """Path to sample.csv fixture."""
    return FIXTURES_DIR / "sample.csv"


@pytest.fixture
def sample_pptx() -> Path:
    """Path to sample.pptx fixture."""
    return FIXTURES_DIR / "sample.pptx"


@pytest.fixture
def sample_png() -> Path:
    """Path to sample.png fixture."""
    return FIXTURES_DIR / "sample.png"


# ---------------------------------------------------------------------------
# Mock components
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_engine() -> MockShikomiIngester:
    """Mock ingester with no model loading."""
    ingester = MockShikomiIngester()
    ingester.connect()
    return ingester


@pytest.fixture
def mock_storage() -> MockKojiClient:
    """Opened MockKojiClient (in-memory)."""
    client = MockKojiClient()
    client.open()
    return client


# ---------------------------------------------------------------------------
# Real Koji client
# ---------------------------------------------------------------------------


@pytest.fixture
def koji_storage(tmp_path) -> KojiClient:
    """Real KojiClient backed by a temporary file database."""
    config = KojiConfig(db_path=str(tmp_path / "pipeline_test.db"))
    client = KojiClient(config)
    client.open()
    yield client
    client.close()


# ---------------------------------------------------------------------------
# Processor factory
# ---------------------------------------------------------------------------


@pytest.fixture
def make_processor():
    """Factory fixture for building DocumentProcessor with configurable deps.

    Usage::

        processor = make_processor()                    # all mocks
        processor = make_processor(storage=koji_client) # real Koji
    """

    def _make(ingester=None, storage=None):
        if ingester is None:
            ingester = MockShikomiIngester()
            ingester.connect()
        if storage is None:
            storage = MockKojiClient()
            storage.open()
        return DocumentProcessor(ingester=ingester, storage_client=storage)

    return _make


# ---------------------------------------------------------------------------
# Status callback collector
# ---------------------------------------------------------------------------


@pytest.fixture
def status_collector():
    """Collector for ProcessingStatus callbacks.

    Returns a ``(callback, statuses)`` tuple. Pass ``callback`` as the
    ``status_callback`` argument to ``process_document()``, then inspect
    ``statuses`` after processing completes.

    Usage::

        callback, statuses = status_collector()
        processor.process_document(path, status_callback=callback)
        assert statuses[-1].status == "completed"
    """
    captured: list[ProcessingStatus] = []

    def _callback(status: ProcessingStatus) -> None:
        captured.append(status)

    return _callback, captured

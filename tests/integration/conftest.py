"""Shared fixtures for integration flow tests.

Provides real KojiClient instances, DocumentProcessor with mock
embeddings, and a TestClient for the API server that creates jobs
in the Koji queue.

For full upload-process-verify flows, tests use the worker's
``process_job()`` function directly after creating a job via the API.
"""

from __future__ import annotations

from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import src.processing.worker_webhook as ww
from src.config.koji_config import KojiConfig
from src.core.testing.mocks import MockShikomiIngester
from src.processing.processor import DocumentProcessor
from src.processing.worker import process_job
from src.storage.koji_client import KojiClient

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


# ---------------------------------------------------------------------------
# Real Koji client
# ---------------------------------------------------------------------------


@pytest.fixture
def flow_koji_client(tmp_path: Path) -> Generator[KojiClient, None, None]:
    """Real KojiClient backed by a temporary file database."""
    config = KojiConfig(db_path=str(tmp_path / "flow_test.db"))
    client = KojiClient(config)
    client.open()
    yield client
    client.close()


# ---------------------------------------------------------------------------
# Real processor with mock embeddings
# ---------------------------------------------------------------------------


@pytest.fixture
def flow_processor(flow_koji_client: KojiClient) -> DocumentProcessor:
    """DocumentProcessor with MockShikomiIngester + real Koji.

    No GPU required — uses mock embeddings for text/visual encoding.
    """
    ingester = MockShikomiIngester()
    ingester.connect()
    return DocumentProcessor(ingester=ingester, storage_client=flow_koji_client)


# ---------------------------------------------------------------------------
# API TestClient with real Koji job queue
# ---------------------------------------------------------------------------


@pytest.fixture
def sync_worker_client(
    tmp_path: Path,
) -> Generator[tuple[TestClient, KojiClient], None, None]:
    """TestClient for the API server with real Koji job queue.

    Patches ``koji_client`` and ``UPLOADS_DIR`` on the worker_webhook
    module so that upload endpoints create jobs in a temporary database.

    After uploading, tests should call ``process_uploaded_job()`` to
    run the processing worker inline (synchronous, no GPU).

    Yields ``(client, koji_client)`` so tests can verify storage state.
    """
    uploads = tmp_path / "uploads"
    uploads.mkdir()

    # Real Koji
    config = KojiConfig(db_path=str(tmp_path / "worker_flow.db"))
    koji = KojiClient(config)
    koji.open()

    # Save originals
    originals = {
        "koji_client": ww.koji_client,
        "query_engine": ww.query_engine,
        "status_manager": ww.status_manager,
        "UPLOADS_DIR": ww.UPLOADS_DIR,
        "processing_status": ww.processing_status,
        "pending_uploads": ww.pending_uploads,
    }

    # Patch globals — API server only needs Koji + uploads dir
    ww.koji_client = koji
    ww.query_engine = MagicMock()
    ww.status_manager = MagicMock()
    ww.status_manager.create_status.return_value = None
    ww.UPLOADS_DIR = uploads
    ww.processing_status = {}
    ww.pending_uploads = {}

    client = TestClient(ww.app, raise_server_exceptions=False)
    yield client, koji

    # Restore originals
    for attr, value in originals.items():
        setattr(ww, attr, value)
    koji.close()


# ---------------------------------------------------------------------------
# Helper: run processing inline after API upload
# ---------------------------------------------------------------------------


def process_uploaded_job(koji: KojiClient) -> None:
    """Claim and process the next queued job using mock ingester.

    Call this after ``POST /uploads/`` to simulate what the headless
    worker would do.  Uses MockShikomiIngester (no GPU).
    """
    job = koji.claim_next_job()
    if job is None:
        return

    ingester = MockShikomiIngester()
    ingester.connect()
    processor = DocumentProcessor(ingester=ingester, storage_client=koji)
    process_job(job, processor, koji)

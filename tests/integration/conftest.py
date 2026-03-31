"""Shared fixtures for integration flow tests.

Provides real KojiClient instances, DocumentProcessor with mock
embeddings, and a synchronous worker TestClient for deterministic
upload-process-verify flows.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import src.processing.worker_webhook as ww
from src.config.koji_config import KojiConfig
from src.core.testing.mocks import MockShikomiIngester
from src.processing.processor import DocumentProcessor
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
# Synchronous worker TestClient
# ---------------------------------------------------------------------------


class _SyncExecutor:
    """Runs submitted functions synchronously instead of in a thread pool.

    Replaces ``ThreadPoolExecutor`` so that ``POST /uploads/`` processing
    completes before the test continues.
    """

    def submit(self, fn, *args, **kwargs):
        """Execute *fn* inline and return a mock future."""
        result = fn(*args, **kwargs)
        future = MagicMock()
        future.result.return_value = result
        return future


@pytest.fixture
def sync_worker_client(
    tmp_path: Path,
) -> Generator[tuple[TestClient, KojiClient], None, None]:
    """TestClient for the worker app with synchronous processing.

    Patches module-level globals on ``worker_webhook`` so that:
    - ``UPLOADS_DIR`` points to a temp directory
    - ``document_processor`` uses MockShikomiIngester + real Koji
    - ``executor`` runs processing synchronously (not threaded)
    - All other globals are safely stubbed

    Yields ``(client, koji_client)`` so tests can verify storage state.
    """
    uploads = tmp_path / "uploads"
    uploads.mkdir()

    # Real Koji
    config = KojiConfig(db_path=str(tmp_path / "worker_flow.db"))
    koji_client = KojiClient(config)
    koji_client.open()

    # Mock ingester (no GPU)
    mock_ingester = MockShikomiIngester()
    mock_ingester.connect()

    # Real processor with mock ingester + real Koji
    processor = DocumentProcessor(
        ingester=mock_ingester, storage_client=koji_client,
    )

    # Save originals
    originals = {
        "document_processor": ww.document_processor,
        "ingester": ww.ingester,
        "query_engine": ww.query_engine,
        "status_manager": ww.status_manager,
        "UPLOADS_DIR": ww.UPLOADS_DIR,
        "_loop": ww._loop,
        "executor": ww.executor,
        "processing_status": ww.processing_status,
        "pending_uploads": ww.pending_uploads,
    }

    # Patch globals
    ww.document_processor = processor
    ww.ingester = mock_ingester
    ww.query_engine = MagicMock()
    ww.status_manager = MagicMock()
    ww.status_manager.create_status.return_value = None
    ww.UPLOADS_DIR = uploads
    ww._loop = asyncio.new_event_loop()
    ww.executor = _SyncExecutor()
    ww.processing_status = {}
    ww.pending_uploads = {}

    client = TestClient(ww.app, raise_server_exceptions=False)
    yield client, koji_client

    # Restore originals
    for attr, value in originals.items():
        setattr(ww, attr, value)
    koji_client.close()

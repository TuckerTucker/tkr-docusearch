"""
Integration tests for the worker webhook POST /search endpoint.

Tests the search HTTP contract on the worker FastAPI app:
- Response shape and field mapping
- Search mode translation (visual -> visual_only, text -> text_only)
- Default search mode (hybrid)
- n_results pass-through
- 503 when the search engine is not ready
- Request validation (empty query, out-of-range n_results)

These tests use FastAPI TestClient against the worker app with patched
module-level globals to avoid starting real services or loading embeddings.
"""

import asyncio
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import src.processing.worker_webhook as ww


def _make_search_result(
    doc_id: str = "doc-1",
    chunk_id: str = "chunk-1",
    page: int = 1,
    score: float = 0.85,
    text: str = "Sample text content",
    filename: str = "test.pdf",
    source: str = "text",
) -> dict[str, Any]:
    """Build a single search result dict matching KojiSearch.search() output."""
    return {
        "doc_id": doc_id,
        "chunk_id": chunk_id,
        "page": page,
        "score": score,
        "text": text,
        "metadata": {"filename": filename, "source": source},
    }


def _make_search_response(
    results: list[dict[str, Any]] | None = None,
    total_time_ms: float = 50.0,
) -> dict[str, Any]:
    """Build a canned KojiSearch.search() response."""
    return {
        "results": results if results is not None else [],
        "total_time_ms": total_time_ms,
    }


@pytest.fixture
def test_client(tmp_path):
    """TestClient with patched worker globals.

    Patches module-level globals on the worker_webhook module so the
    FastAPI app can be exercised without real infrastructure.

    Yields:
        Tuple of (TestClient, mock_search_engine) so tests can configure
        the mock's return_value before making requests.
    """
    # Save originals
    orig_query_engine = ww.query_engine
    orig_processor = ww.document_processor
    orig_ingester = ww.ingester
    orig_status_manager = ww.status_manager
    orig_uploads_dir = ww.UPLOADS_DIR
    orig_loop = ww._loop
    orig_executor = ww.executor
    orig_processing_status = ww.processing_status
    orig_pending_uploads = ww.pending_uploads

    # Patch globals
    ww.query_engine = MagicMock()
    ww.document_processor = MagicMock()
    ww.ingester = MagicMock()
    ww.status_manager = MagicMock()
    ww.UPLOADS_DIR = tmp_path / "uploads"
    ww.UPLOADS_DIR.mkdir()
    ww._loop = asyncio.new_event_loop()
    ww.executor = MagicMock()
    ww.processing_status = {}
    ww.pending_uploads = {}

    # Pre-set mock search engine on app.state so the endpoint
    # doesn't try to construct a real KojiSearch.
    mock_search = MagicMock()
    mock_search.search.return_value = _make_search_response()
    ww.app.state.search_engine = mock_search

    client = TestClient(ww.app, raise_server_exceptions=False)
    yield client, mock_search

    # Restore originals
    ww.query_engine = orig_query_engine
    ww.document_processor = orig_processor
    ww.ingester = orig_ingester
    ww.status_manager = orig_status_manager
    ww.UPLOADS_DIR = orig_uploads_dir
    ww._loop = orig_loop
    ww.executor = orig_executor
    ww.processing_status = orig_processing_status
    ww.pending_uploads = orig_pending_uploads

    if hasattr(ww.app.state, "search_engine"):
        del ww.app.state.search_engine


# ============================================================================
# Search Endpoint Tests
# ============================================================================


class TestWorkerSearch:
    """POST /search endpoint behaviour."""

    def test_search_returns_results(self, test_client):
        """Verify response shape when the search engine returns results."""
        client, mock_search = test_client

        mock_search.search.return_value = _make_search_response(
            results=[
                _make_search_result(doc_id="doc-1", chunk_id="c-1", page=1, score=0.95),
                _make_search_result(doc_id="doc-2", chunk_id="c-2", page=3, score=0.72),
            ],
            total_time_ms=42.5,
        )

        response = client.post("/search", json={"query": "test query"})

        assert response.status_code == 200
        data = response.json()

        assert data["query"] == "test query"
        assert data["total_results"] == 2
        assert data["search_time_ms"] == 42.5

        first = data["results"][0]
        assert first["doc_id"] == "doc-1"
        assert first["chunk_id"] == "c-1"
        assert first["page_num"] == 1
        assert first["score"] == 0.95
        assert first["text_preview"] is not None
        assert first["filename"] == "test.pdf"
        assert first["type"] == "text"

    def test_search_empty_results(self, test_client):
        """Verify response when no results are found."""
        client, mock_search = test_client

        mock_search.search.return_value = _make_search_response(results=[])

        response = client.post("/search", json={"query": "obscure query"})

        assert response.status_code == 200
        data = response.json()
        assert data["total_results"] == 0
        assert data["results"] == []
        assert data["query"] == "obscure query"

    def test_search_mode_text_only(self, test_client):
        """Sending search_mode='text' maps to 'text_only' for KojiSearch."""
        client, mock_search = test_client

        mock_search.search.return_value = _make_search_response()

        response = client.post(
            "/search", json={"query": "find text", "search_mode": "text"}
        )

        assert response.status_code == 200
        mock_search.search.assert_called_once_with(
            query="find text", n_results=10, search_mode="text_only"
        )

    def test_search_mode_visual_only(self, test_client):
        """Sending search_mode='visual' maps to 'visual_only' for KojiSearch."""
        client, mock_search = test_client

        mock_search.search.return_value = _make_search_response()

        response = client.post(
            "/search", json={"query": "find image", "search_mode": "visual"}
        )

        assert response.status_code == 200
        mock_search.search.assert_called_once_with(
            query="find image", n_results=10, search_mode="visual_only"
        )

    def test_search_mode_hybrid_default(self, test_client):
        """Omitting search_mode defaults to 'hybrid'."""
        client, mock_search = test_client

        mock_search.search.return_value = _make_search_response()

        response = client.post("/search", json={"query": "default mode"})

        assert response.status_code == 200
        mock_search.search.assert_called_once_with(
            query="default mode", n_results=10, search_mode="hybrid"
        )

    def test_search_n_results_passed(self, test_client):
        """Custom n_results is forwarded to the search engine."""
        client, mock_search = test_client

        mock_search.search.return_value = _make_search_response()

        response = client.post(
            "/search", json={"query": "limited", "n_results": 5}
        )

        assert response.status_code == 200
        mock_search.search.assert_called_once_with(
            query="limited", n_results=5, search_mode="hybrid"
        )

    def test_search_engine_not_ready_returns_503(self, test_client):
        """When query_engine is None the endpoint returns 503."""
        client, _mock_search = test_client

        # Simulate search engine not initialized
        orig = ww.query_engine
        ww.query_engine = None
        try:
            response = client.post("/search", json={"query": "anything"})
        finally:
            ww.query_engine = orig

        assert response.status_code == 503
        assert "not ready" in response.json()["detail"].lower()


# ============================================================================
# Request Validation Tests
# ============================================================================


class TestSearchRequestValidation:
    """Pydantic validation on SearchRequest."""

    def test_empty_query_rejected(self, test_client):
        """An empty query string is rejected by min_length=1."""
        client, _mock_search = test_client

        response = client.post("/search", json={"query": ""})

        assert response.status_code == 422

    def test_n_results_below_minimum_rejected(self, test_client):
        """n_results=0 is rejected by ge=1."""
        client, _mock_search = test_client

        response = client.post("/search", json={"query": "q", "n_results": 0})

        assert response.status_code == 422

    def test_n_results_above_maximum_rejected(self, test_client):
        """n_results=101 is rejected by le=100."""
        client, _mock_search = test_client

        response = client.post("/search", json={"query": "q", "n_results": 101})

        assert response.status_code == 422

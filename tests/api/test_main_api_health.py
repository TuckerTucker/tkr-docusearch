"""Integration tests for the main API health and status endpoints.

Tests ``/health``, ``/status``, and ``/stats/search`` on the main
FastAPI server app.  Uses real KojiClient with patched ``_app_state``.
"""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

import tkr_docusearch.api.server as srv
from tkr_docusearch.config.koji_config import KojiConfig
from tkr_docusearch.storage.koji_client import KojiClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def test_client(tmp_path):
    """TestClient against the main API app with patched state.

    Injects a real KojiClient (tmp_path) and sets start_time so
    uptime is computable.
    """
    config = KojiConfig(db_path=str(tmp_path / "health_test.db"))
    koji_client = KojiClient(config)
    koji_client.open()

    original_state = dict(srv._app_state)

    srv._app_state["storage_client"] = koji_client
    srv._app_state["start_time"] = time.time()
    srv._app_state["search_engine"] = None
    srv._app_state["embedding_engine"] = None

    client = TestClient(srv.app, raise_server_exceptions=False)
    yield client

    srv._app_state.update(original_state)
    koji_client.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestHealthEndpoints:
    """GET /health and GET /status"""

    def test_health_returns_ok(self, test_client):
        resp = test_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
        assert "version" in data

    def test_status_returns_components(self, test_client):
        resp = test_client.get("/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "components" in data
        assert "stats" in data
        names = {c["name"] for c in data["components"]}
        assert "koji" in names

    def test_status_koji_healthy(self, test_client):
        resp = test_client.get("/status")
        data = resp.json()
        koji = next(c for c in data["components"] if c["name"] == "koji")
        assert koji["status"] == "healthy"

    def test_status_includes_uptime(self, test_client):
        resp = test_client.get("/status")
        data = resp.json()
        assert data["uptime_seconds"] >= 0

    def test_search_stats_not_initialized_returns_503(self, test_client):
        resp = test_client.get("/stats/search")
        assert resp.status_code == 503

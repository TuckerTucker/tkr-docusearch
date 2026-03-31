"""Integration tests for the worker documents API.

Tests the /documents/* endpoints served by the worker app via FastAPI
TestClient with a real Koji database (file-backed via tmp_path).

Covers:
    - GET  /documents         (list with pagination, search, project filter)
    - GET  /documents/{doc_id} (detail with page/chunk counts)
    - DELETE /documents/{doc_id} (removal and 404 handling)

The documents router creates a new KojiClient via ``get_storage_client()``
on every request, so we patch that function to inject the test client.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tkr_docusearch.config.koji_config import KojiConfig
from tkr_docusearch.processing.documents_api import router as documents_router
from tkr_docusearch.storage.koji_client import KojiClient

# Fully-qualified target for the patch — must match where the function is
# looked up at call time, not where it is defined.
_PATCH_TARGET = "tkr_docusearch.processing.documents_api.get_storage_client"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def koji_client(tmp_path: Path) -> KojiClient:
    """Create and open a KojiClient with a temporary file-based database."""
    config = KojiConfig(db_path=str(tmp_path / "worker_docs_test.db"))
    client = KojiClient(config)
    client.open()
    yield client
    client.close()


@pytest.fixture
def test_client(koji_client: KojiClient) -> TestClient:
    """FastAPI TestClient wired to the documents router.

    Patches ``get_storage_client`` so every request handler receives the
    test KojiClient instead of creating one from environment variables.
    """
    app = FastAPI()
    app.include_router(documents_router)
    with patch(_PATCH_TARGET, return_value=koji_client):
        yield TestClient(app)


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------


def _seed_documents(client: KojiClient) -> None:
    """Populate 3 documents with pages and chunks.

    Documents:
        doc-alpha  (sample.pdf,  2 pages, 3 chunks)
        doc-beta   (report.docx, 1 page,  2 chunks)
        doc-gamma  (notes.md,    1 page,  1 chunk)
    """
    for doc_id, filename, fmt, num_pages in [
        ("doc-alpha", "sample.pdf", "pdf", 2),
        ("doc-beta", "report.docx", "docx", 1),
        ("doc-gamma", "notes.md", "md", 1),
    ]:
        client.create_document(
            doc_id=doc_id,
            filename=filename,
            format=fmt,
            num_pages=num_pages,
        )
        page_records: list[dict[str, Any]] = [
            {"id": f"{doc_id}-page-{i}", "doc_id": doc_id, "page_num": i}
            for i in range(1, num_pages + 1)
        ]
        client.insert_pages(page_records)

    # Chunks for doc-alpha
    client.insert_chunks([
        {"id": "doc-alpha-chunk-1", "doc_id": "doc-alpha", "page_num": 1,
         "text": "Introduction to machine learning concepts.", "word_count": 5},
        {"id": "doc-alpha-chunk-2", "doc_id": "doc-alpha", "page_num": 1,
         "text": "Supervised learning uses labeled training data.", "word_count": 6},
        {"id": "doc-alpha-chunk-3", "doc_id": "doc-alpha", "page_num": 2,
         "text": "Neural networks are composed of layers.", "word_count": 6},
    ])

    # Chunks for doc-beta
    client.insert_chunks([
        {"id": "doc-beta-chunk-1", "doc_id": "doc-beta", "page_num": 1,
         "text": "Quarterly revenue report summary.", "word_count": 4},
        {"id": "doc-beta-chunk-2", "doc_id": "doc-beta", "page_num": 1,
         "text": "Growth exceeded expectations in Q3.", "word_count": 5},
    ])

    # Chunks for doc-gamma
    client.insert_chunks([
        {"id": "doc-gamma-chunk-1", "doc_id": "doc-gamma", "page_num": 1,
         "text": "Meeting notes from the design review.", "word_count": 6},
    ])


def _seed_documents_with_projects(client: KojiClient) -> None:
    """Populate documents across two projects for project-filter tests.

    Project "project-a": doc-p1, doc-p2
    Project "project-b": doc-p3
    """
    for doc_id, filename, fmt, project_id in [
        ("doc-proj1a", "alpha.pdf", "pdf", "project-a"),
        ("doc-proj2a", "bravo.pdf", "pdf", "project-a"),
        ("doc-proj3b", "charlie.md", "md", "project-b"),
    ]:
        client.create_document(
            doc_id=doc_id,
            filename=filename,
            format=fmt,
            num_pages=1,
            project_id=project_id,
        )
        client.insert_pages([
            {"id": f"{doc_id}-page-1", "doc_id": doc_id, "page_num": 1},
        ])


# ---------------------------------------------------------------------------
# GET /documents — list
# ---------------------------------------------------------------------------


class TestDocumentList:
    """Tests for the document listing endpoint."""

    def test_list_documents_empty(
        self, test_client: TestClient
    ) -> None:
        """Empty database returns an empty document list."""
        resp = test_client.get("/documents")
        assert resp.status_code == 200

        data = resp.json()
        assert data["documents"] == []
        assert data["total"] == 0

    def test_list_documents_with_data(
        self, koji_client: KojiClient, test_client: TestClient
    ) -> None:
        """Seeded database returns all documents with expected fields."""
        _seed_documents(koji_client)

        resp = test_client.get("/documents")
        assert resp.status_code == 200

        data = resp.json()
        assert data["total"] == 3

        returned_ids = {doc["doc_id"] for doc in data["documents"]}
        assert returned_ids == {"doc-alpha", "doc-beta", "doc-gamma"}

        # Verify each document carries required fields
        for doc in data["documents"]:
            assert "doc_id" in doc
            assert "filename" in doc
            assert "page_count" in doc
            assert "chunk_count" in doc
            assert "date_added" in doc
            assert "has_images" in doc

    def test_list_documents_pagination(
        self, koji_client: KojiClient, test_client: TestClient
    ) -> None:
        """Limit and offset parameters control pagination."""
        _seed_documents(koji_client)

        # Request first page of size 2
        resp = test_client.get("/documents?limit=2&offset=0")
        assert resp.status_code == 200

        data = resp.json()
        assert len(data["documents"]) == 2
        assert data["total"] == 3  # total is unaffected by pagination
        assert data["limit"] == 2
        assert data["offset"] == 0

        # Request second page
        resp2 = test_client.get("/documents?limit=2&offset=2")
        assert resp2.status_code == 200

        data2 = resp2.json()
        assert len(data2["documents"]) == 1
        assert data2["total"] == 3

    def test_list_documents_project_filter(
        self, koji_client: KojiClient, test_client: TestClient
    ) -> None:
        """Filtering by project_id returns only documents in that project."""
        _seed_documents_with_projects(koji_client)

        resp_a = test_client.get("/documents?project_id=project-a")
        assert resp_a.status_code == 200
        data_a = resp_a.json()
        assert data_a["total"] == 2
        ids_a = {doc["doc_id"] for doc in data_a["documents"]}
        assert ids_a == {"doc-proj1a", "doc-proj2a"}

        resp_b = test_client.get("/documents?project_id=project-b")
        assert resp_b.status_code == 200
        data_b = resp_b.json()
        assert data_b["total"] == 1
        assert data_b["documents"][0]["doc_id"] == "doc-proj3b"


# ---------------------------------------------------------------------------
# GET /documents/{doc_id} — detail
# ---------------------------------------------------------------------------


class TestDocumentDetail:
    """Tests for the document detail endpoint."""

    def test_get_document_detail(
        self, koji_client: KojiClient, test_client: TestClient
    ) -> None:
        """Retrieving a known document returns its full detail."""
        _seed_documents(koji_client)

        resp = test_client.get("/documents/doc-alpha")
        assert resp.status_code == 200

        data = resp.json()
        assert data["doc_id"] == "doc-alpha"
        assert data["filename"] == "sample.pdf"
        assert "date_added" in data
        assert "pages" in data
        assert "chunks" in data
        assert "metadata" in data

    def test_get_document_includes_page_count(
        self, koji_client: KojiClient, test_client: TestClient
    ) -> None:
        """Detail response includes correct page and chunk counts."""
        _seed_documents(koji_client)

        resp = test_client.get("/documents/doc-alpha")
        assert resp.status_code == 200

        data = resp.json()
        assert data["metadata"]["page_count"] == 2
        assert data["metadata"]["chunk_count"] == 3
        assert len(data["pages"]) == 2
        assert len(data["chunks"]) == 3

        # Verify single-page doc as well
        resp_beta = test_client.get("/documents/doc-beta")
        assert resp_beta.status_code == 200

        data_beta = resp_beta.json()
        assert data_beta["metadata"]["page_count"] == 1
        assert data_beta["metadata"]["chunk_count"] == 2

    def test_get_nonexistent_returns_404(
        self, test_client: TestClient
    ) -> None:
        """Requesting a non-existent document returns 404."""
        resp = test_client.get("/documents/abcdef1234567890abcdef1234567890")
        assert resp.status_code == 404

        data = resp.json()
        assert data["detail"]["code"] == "DOCUMENT_NOT_FOUND"


# ---------------------------------------------------------------------------
# DELETE /documents/{doc_id}
# ---------------------------------------------------------------------------


class TestDocumentDelete:
    """Tests for the document deletion endpoint."""

    def test_delete_document(
        self, koji_client: KojiClient, test_client: TestClient
    ) -> None:
        """Deleting an existing document returns success."""
        _seed_documents(koji_client)

        resp = test_client.delete("/documents/doc-alpha")
        assert resp.status_code == 200

        data = resp.json()
        assert data["success"] is True
        assert data["doc_id"] == "doc-alpha"
        assert data["filename"] == "sample.pdf"
        assert "koji" in data["deleted"]

    def test_delete_removes_from_list(
        self, koji_client: KojiClient, test_client: TestClient
    ) -> None:
        """After deletion the document no longer appears in the list."""
        _seed_documents(koji_client)

        # Confirm doc-beta is present
        resp_before = test_client.get("/documents")
        ids_before = {d["doc_id"] for d in resp_before.json()["documents"]}
        assert "doc-beta" in ids_before

        # Delete
        del_resp = test_client.delete("/documents/doc-beta")
        assert del_resp.status_code == 200

        # Confirm gone
        resp_after = test_client.get("/documents")
        ids_after = {d["doc_id"] for d in resp_after.json()["documents"]}
        assert "doc-beta" not in ids_after
        assert resp_after.json()["total"] == 2

    def test_delete_nonexistent_returns_404(
        self, test_client: TestClient
    ) -> None:
        """Deleting a non-existent document returns 404."""
        resp = test_client.delete(
            "/documents/abcdef1234567890abcdef1234567890"
        )
        assert resp.status_code == 404

        data = resp.json()
        assert data["detail"]["code"] == "DOCUMENT_NOT_FOUND"

"""Integration tests for project-document scoping.

Verifies that documents are correctly scoped to projects via
``project_id`` and that project operations (list, get, delete)
cascade and reflect accurate document counts.

Tests use a real KojiClient with a temporary file-based database
and the projects HTTP API via FastAPI TestClient.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tkr_docusearch.config.koji_config import KojiConfig
from tkr_docusearch.storage.koji_client import KojiClient
from tkr_docusearch.api.routes.projects import router, set_storage_client


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def koji_client(tmp_path):
    """Real KojiClient backed by a temporary file database."""
    config = KojiConfig(db_path=str(tmp_path / "scoping_test.db"))
    client = KojiClient(config)
    client.open()
    yield client
    client.close()


@pytest.fixture
def test_client(koji_client):
    """FastAPI TestClient wired to the projects router with real Koji.

    Injects the KojiClient via ``set_storage_client`` and cleans up
    the module-level global after the test.
    """
    app = FastAPI()
    app.include_router(router)
    set_storage_client(koji_client)
    yield TestClient(app)
    set_storage_client(None)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_project_via_api(
    client: TestClient,
    name: str,
    project_id: str | None = None,
) -> dict:
    """Create a project through the HTTP API and return the response body.

    Args:
        client: FastAPI TestClient.
        name: Human-readable project name.
        project_id: Explicit slug; auto-generated from *name* if omitted.

    Returns:
        Parsed JSON response body.
    """
    payload: dict = {"name": name}
    if project_id is not None:
        payload["project_id"] = project_id
    resp = client.post("/api/projects", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestProjectDocumentScoping:
    """Verify that documents are correctly scoped to projects."""

    def test_create_project_and_add_document(
        self, koji_client, test_client
    ):
        """Create a project via API, add a document via Koji, verify count.

        The GET /api/projects/{id} endpoint should report
        ``document_count=1`` after a single document is inserted into
        the project.
        """
        _create_project_via_api(test_client, "Alpha", project_id="alpha")

        koji_client.create_document(
            doc_id="alpha-doc-1",
            filename="report.pdf",
            format="pdf",
            project_id="alpha",
        )

        resp = test_client.get("/api/projects/alpha")
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == "alpha"
        assert data["document_count"] == 1

    def test_documents_isolated_between_projects(
        self, koji_client, test_client
    ):
        """Documents in one project must not appear in another.

        Creates two projects, adds 2 docs to project-a and 1 to
        project-b, then verifies ``list_documents`` scopes correctly.
        """
        _create_project_via_api(test_client, "Project A", project_id="proj-a")
        _create_project_via_api(test_client, "Project B", project_id="proj-b")

        koji_client.create_document(
            doc_id="a-doc-1",
            filename="a1.pdf",
            format="pdf",
            project_id="proj-a",
        )
        koji_client.create_document(
            doc_id="a-doc-2",
            filename="a2.pdf",
            format="pdf",
            project_id="proj-a",
        )
        koji_client.create_document(
            doc_id="b-doc-1",
            filename="b1.md",
            format="md",
            project_id="proj-b",
        )

        docs_a = koji_client.list_documents(project_id="proj-a")
        docs_b = koji_client.list_documents(project_id="proj-b")

        assert len(docs_a) == 2
        assert {d["doc_id"] for d in docs_a} == {"a-doc-1", "a-doc-2"}

        assert len(docs_b) == 1
        assert docs_b[0]["doc_id"] == "b-doc-1"

    def test_delete_project_cascades_documents(
        self, koji_client, test_client
    ):
        """Deleting a project removes all its documents from Koji.

        After DELETE /api/projects/{id}, neither the project nor its
        documents should be retrievable.
        """
        _create_project_via_api(test_client, "Doomed", project_id="doomed")

        for i in range(3):
            koji_client.create_document(
                doc_id=f"doomed-doc-{i}",
                filename=f"file{i}.pdf",
                format="pdf",
                project_id="doomed",
            )

        # Pre-condition: 3 documents exist
        assert koji_client.count_documents_in_project("doomed") == 3

        resp = test_client.delete("/api/projects/doomed")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["documents_deleted"] == 3

        # Project gone
        assert koji_client.get_project("doomed") is None

        # Documents gone
        for i in range(3):
            assert koji_client.get_document(f"doomed-doc-{i}") is None

    def test_default_project_assignment(self, koji_client):
        """Documents created without an explicit project_id default to 'default'.

        The ``create_document`` method should assign ``project_id='default'``
        when the caller omits it.
        """
        koji_client.create_document(
            doc_id="orphan-doc",
            filename="notes.md",
            format="md",
        )

        doc = koji_client.get_document("orphan-doc")
        assert doc is not None
        assert doc["project_id"] == "default"

        # Also verifiable through the count helper
        assert koji_client.count_documents_in_project("default") >= 1

    def test_list_projects_with_document_counts(
        self, koji_client, test_client
    ):
        """GET /api/projects returns accurate document_count for each project.

        Creates 3 projects with 3, 1, and 0 documents respectively and
        checks that the listing reflects these counts.
        """
        _create_project_via_api(test_client, "Many", project_id="many")
        _create_project_via_api(test_client, "One", project_id="one")
        _create_project_via_api(test_client, "Empty", project_id="empty")

        for i in range(3):
            koji_client.create_document(
                doc_id=f"many-doc-{i}",
                filename=f"m{i}.pdf",
                format="pdf",
                project_id="many",
            )
        koji_client.create_document(
            doc_id="one-doc-0",
            filename="o0.pdf",
            format="pdf",
            project_id="one",
        )

        resp = test_client.get("/api/projects")
        assert resp.status_code == 200

        projects = {p["project_id"]: p for p in resp.json()}
        assert projects["many"]["document_count"] == 3
        assert projects["one"]["document_count"] == 1
        assert projects["empty"]["document_count"] == 0

    def test_project_count_decreases_on_document_delete(
        self, koji_client, test_client
    ):
        """Deleting a document decreases the project's document_count.

        Adds a document, verifies count=1, deletes the document via
        Koji, and verifies count returns to 0 through the HTTP API.
        """
        _create_project_via_api(
            test_client, "Shrinking", project_id="shrinking"
        )

        koji_client.create_document(
            doc_id="shrink-doc",
            filename="temp.pdf",
            format="pdf",
            project_id="shrinking",
        )

        # Count = 1 via API
        resp = test_client.get("/api/projects/shrinking")
        assert resp.status_code == 200
        assert resp.json()["document_count"] == 1

        # Delete the document directly via Koji
        koji_client.delete_document("shrink-doc")

        # Count = 0 via API
        resp = test_client.get("/api/projects/shrinking")
        assert resp.status_code == 200
        assert resp.json()["document_count"] == 0

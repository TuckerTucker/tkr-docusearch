"""Integration tests for the Projects CRUD API.

Tests ``/api/projects`` endpoints using FastAPI TestClient with a real
Koji database (file-backed via tmp_path).  Validates HTTP contracts,
request/response shapes, status codes, and error handling.
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
    """Real KojiClient with temporary database."""
    config = KojiConfig(db_path=str(tmp_path / "projects_test.db"))
    client = KojiClient(config)
    client.open()
    yield client
    client.close()


@pytest.fixture
def test_client(koji_client):
    """TestClient wired to the projects router with real Koji."""
    app = FastAPI()
    app.include_router(router)
    set_storage_client(koji_client)
    yield TestClient(app)
    set_storage_client(None)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


class TestProjectCreate:
    """POST /api/projects"""

    def test_create_project_returns_201(self, test_client):
        resp = test_client.post(
            "/api/projects",
            json={"name": "Test Project"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test Project"
        assert data["project_id"] == "test-project"
        assert data["document_count"] == 0
        assert "created_at" in data

    def test_create_project_auto_generates_slug(self, test_client):
        resp = test_client.post(
            "/api/projects",
            json={"name": "My Fancy  Research!!  Project"},
        )
        assert resp.status_code == 201
        pid = resp.json()["project_id"]
        # Slug should be lowercased, special chars replaced with hyphens
        assert pid == "my-fancy-research-project"

    def test_create_project_with_explicit_id(self, test_client):
        resp = test_client.post(
            "/api/projects",
            json={"name": "Custom", "project_id": "custom-id-123"},
        )
        assert resp.status_code == 201
        assert resp.json()["project_id"] == "custom-id-123"

    def test_create_duplicate_returns_409(self, test_client):
        test_client.post("/api/projects", json={"name": "Dup"})
        resp = test_client.post("/api/projects", json={"name": "Dup"})
        assert resp.status_code == 409

    def test_create_with_metadata(self, test_client):
        resp = test_client.post(
            "/api/projects",
            json={
                "name": "Rich",
                "description": "A described project",
                "metadata": {"team": "research", "priority": 1},
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["description"] == "A described project"
        assert data["metadata"]["team"] == "research"


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


class TestProjectList:
    """GET /api/projects"""

    def test_list_projects_includes_default(self, test_client):
        resp = test_client.get("/api/projects")
        assert resp.status_code == 200
        # Koji auto-creates a "default" project on schema sync
        names = {p["project_id"] for p in resp.json()}
        assert "default" in names

    def test_list_projects_returns_created_items(self, test_client):
        test_client.post("/api/projects", json={"name": "One"})
        test_client.post("/api/projects", json={"name": "Two"})

        resp = test_client.get("/api/projects")
        assert resp.status_code == 200
        names = {p["name"] for p in resp.json()}
        assert "One" in names
        assert "Two" in names

    def test_list_projects_returns_document_counts(self, test_client, koji_client):
        test_client.post("/api/projects", json={"name": "Counted"})
        # Add a document to the project
        koji_client.create_document(
            doc_id="doc-in-project",
            filename="test.pdf",
            format="pdf",
            project_id="counted",
        )

        resp = test_client.get("/api/projects")
        project = next(p for p in resp.json() if p["project_id"] == "counted")
        assert project["document_count"] == 1

    def test_list_projects_pagination(self, test_client):
        for i in range(5):
            test_client.post(
                "/api/projects",
                json={"name": f"Project {i}", "project_id": f"proj-{i}"},
            )

        resp = test_client.get("/api/projects", params={"limit": 2, "offset": 0})
        assert len(resp.json()) == 2

        resp = test_client.get("/api/projects", params={"limit": 2, "offset": 3})
        assert len(resp.json()) == 2


# ---------------------------------------------------------------------------
# Get
# ---------------------------------------------------------------------------


class TestProjectGet:
    """GET /api/projects/{project_id}"""

    def test_get_project_by_id(self, test_client):
        test_client.post(
            "/api/projects",
            json={"name": "Findable", "project_id": "findable"},
        )
        resp = test_client.get("/api/projects/findable")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Findable"

    def test_get_nonexistent_returns_404(self, test_client):
        resp = test_client.get("/api/projects/does-not-exist")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


class TestProjectUpdate:
    """PUT /api/projects/{project_id}"""

    def test_update_project_name(self, test_client):
        test_client.post(
            "/api/projects",
            json={"name": "Old Name", "project_id": "updatable"},
        )
        resp = test_client.put(
            "/api/projects/updatable",
            json={"name": "New Name"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    def test_update_no_fields_returns_400(self, test_client):
        test_client.post(
            "/api/projects",
            json={"name": "Static", "project_id": "static"},
        )
        resp = test_client.put("/api/projects/static", json={})
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


class TestProjectDelete:
    """DELETE /api/projects/{project_id}"""

    def test_delete_project(self, test_client):
        test_client.post(
            "/api/projects",
            json={"name": "Removable", "project_id": "removable"},
        )
        resp = test_client.delete("/api/projects/removable")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # Verify it's gone
        resp = test_client.get("/api/projects/removable")
        assert resp.status_code == 404

    def test_delete_nonexistent_returns_404(self, test_client):
        resp = test_client.delete("/api/projects/ghost")
        assert resp.status_code == 404

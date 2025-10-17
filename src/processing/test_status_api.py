"""
Unit tests for Status API endpoints.

Tests HTTP endpoints for document status and queue retrieval.

Contract: status-api.contract.md
"""

import pytest
from fastapi.testclient import TestClient

from processing.status_api import set_status_manager
from processing.status_manager import StatusManager
from processing.worker_webhook import app


@pytest.fixture
def status_dict():
    """Create a fresh status dictionary for each test."""
    return {}


@pytest.fixture
def status_manager(status_dict):
    """Create and configure StatusManager for tests."""
    manager = StatusManager(status_dict)
    set_status_manager(manager)
    return manager


@pytest.fixture
def client(status_manager):
    """Create FastAPI test client with configured StatusManager."""
    return TestClient(app)


class TestGetDocumentStatus:
    """Test GET /status/{doc_id} endpoint."""

    def test_get_existing_document(self, client, status_manager):
        """Test retrieving status for existing document."""
        doc_id = "a" * 64
        status_manager.create_status(doc_id, "test.pdf", {"format": "pdf"})

        response = client.get(f"/status/{doc_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["doc_id"] == doc_id
        assert data["filename"] == "test.pdf"
        assert "progress" in data
        assert 0.0 <= data["progress"] <= 1.0

    def test_get_nonexistent_document(self, client, status_manager):
        """Test retrieving status for nonexistent document returns 404."""
        doc_id = "nonexistent" + "0" * 54

        response = client.get(f"/status/{doc_id}")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]
        assert data["detail"]["code"] == "DOCUMENT_NOT_FOUND"

    def test_get_document_with_progress(self, client, status_manager):
        """Test retrieving document with progress information."""
        doc_id = "a" * 64
        status_manager.create_status(doc_id, "test.pdf", {})
        status_manager.update_status(
            doc_id,
            status="embedding_visual",
            progress=0.65,
            page=13,
            total_pages=20,
        )

        response = client.get(f"/status/{doc_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "embedding_visual"
        assert data["progress"] == 0.65
        assert data["page"] == 13
        assert data["total_pages"] == 20

    def test_response_format(self, client, status_manager):
        """Test response format matches ProcessingStatus schema."""
        doc_id = "a" * 64
        status_manager.create_status(doc_id, "test.pdf", {"format": "pdf"})

        response = client.get(f"/status/{doc_id}")

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        required_fields = [
            "doc_id",
            "filename",
            "status",
            "progress",
            "stage",
            "started_at",
            "updated_at",
            "elapsed_time",
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"


class TestGetProcessingQueue:
    """Test GET /status/queue endpoint."""

    def test_get_empty_queue(self, client, status_manager):
        """Test retrieving empty queue."""
        response = client.get("/status/queue")

        assert response.status_code == 200
        data = response.json()
        assert data["queue"] == []
        assert data["total"] == 0
        assert data["active"] == 0
        assert data["completed"] == 0
        assert data["failed"] == 0

    def test_get_queue_with_documents(self, client, status_manager):
        """Test retrieving queue with multiple documents."""
        # Create multiple documents
        doc1 = "a" * 64
        doc2 = "b" * 64
        doc3 = "c" * 64

        status_manager.create_status(doc1, "file1.pdf", {})
        status_manager.create_status(doc2, "file2.pdf", {})
        status_manager.create_status(doc3, "file3.pdf", {})

        status_manager.mark_completed(doc1)
        status_manager.update_status(doc2, status="parsing", progress=0.1)
        # doc3 remains queued

        response = client.get("/status/queue")

        assert response.status_code == 200
        data = response.json()
        assert len(data["queue"]) == 3
        assert data["total"] == 3
        assert data["active"] == 2
        assert data["completed"] == 1
        assert data["failed"] == 0

    def test_queue_filter_by_status(self, client, status_manager):
        """Test filtering queue by status."""
        doc1 = "a" * 64
        doc2 = "b" * 64

        status_manager.create_status(doc1, "file1.pdf", {})
        status_manager.create_status(doc2, "file2.pdf", {})

        status_manager.mark_completed(doc1)
        # doc2 remains queued

        response = client.get("/status/queue?status=completed")

        assert response.status_code == 200
        data = response.json()
        assert len(data["queue"]) == 1
        assert data["queue"][0]["status"] == "completed"

    def test_queue_limit(self, client, status_manager):
        """Test queue limit parameter."""
        # Create 5 documents
        for i in range(5):
            doc_id = str(i).zfill(64)
            status_manager.create_status(doc_id, f"file{i}.pdf", {})

        response = client.get("/status/queue?limit=3")

        assert response.status_code == 200
        data = response.json()
        assert len(data["queue"]) == 3

    def test_queue_item_format(self, client, status_manager):
        """Test queue item format matches QueueItem schema."""
        doc_id = "a" * 64
        status_manager.create_status(doc_id, "test.pdf", {})

        response = client.get("/status/queue")

        assert response.status_code == 200
        data = response.json()

        item = data["queue"][0]
        required_fields = [
            "doc_id",
            "filename",
            "status",
            "progress",
            "elapsed_time",
            "timestamp",
        ]
        for field in required_fields:
            assert field in item, f"Missing required field: {field}"


class TestHealthCheck:
    """Test GET /status/health endpoint."""

    def test_health_check(self, client, status_manager):
        """Test health check returns healthy status."""
        response = client.get("/status/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "queue_stats" in data

    def test_health_check_with_queue(self, client, status_manager):
        """Test health check includes queue statistics."""
        doc_id = "a" * 64
        status_manager.create_status(doc_id, "test.pdf", {})

        response = client.get("/status/health")

        assert response.status_code == 200
        data = response.json()
        assert data["queue_stats"]["total"] == 1


class TestCORSHeaders:
    """Test CORS headers are present."""

    def test_cors_headers_on_get_status(self, client, status_manager):
        """Test CORS headers are present on GET /status/{doc_id}."""
        doc_id = "a" * 64
        status_manager.create_status(doc_id, "test.pdf", {})

        response = client.get(f"/status/{doc_id}")

        # CORS middleware should add these headers
        assert "access-control-allow-origin" in response.headers

    def test_cors_headers_on_queue(self, client, status_manager):
        """Test CORS headers are present on GET /status/queue."""
        response = client.get("/status/queue")

        # CORS middleware should add these headers
        assert "access-control-allow-origin" in response.headers


class TestErrorHandling:
    """Test error responses."""

    def test_invalid_doc_id_format(self, client, status_manager):
        """Test that invalid doc_id format returns 404 (not found)."""
        # Note: FastAPI doesn't validate doc_id format in path,
        # so this will just return 404 not found
        response = client.get("/status/invalid-id")

        assert response.status_code == 404

    def test_queue_invalid_limit(self, client, status_manager):
        """Test queue with invalid limit returns validation error."""
        response = client.get("/status/queue?limit=0")

        assert response.status_code == 422  # Validation error

        response = client.get("/status/queue?limit=10000")

        assert response.status_code == 422  # Exceeds maximum


class TestIntegrationScenarios:
    """Integration tests for common usage scenarios."""

    def test_document_lifecycle_tracking(self, client, status_manager):
        """Test tracking document through complete lifecycle."""
        doc_id = "a" * 64

        # Create document
        status_manager.create_status(doc_id, "report.pdf", {"format": "pdf"})

        # Check initial status
        response = client.get(f"/status/{doc_id}")
        assert response.json()["status"] == "queued"

        # Update to parsing
        status_manager.update_status(doc_id, status="parsing", progress=0.1)
        response = client.get(f"/status/{doc_id}")
        assert response.json()["status"] == "parsing"

        # Update to visual embedding
        status_manager.update_status(doc_id, status="embedding_visual", progress=0.5)
        response = client.get(f"/status/{doc_id}")
        assert response.json()["status"] == "embedding_visual"

        # Complete
        status_manager.mark_completed(doc_id)
        response = client.get(f"/status/{doc_id}")
        assert response.json()["status"] == "completed"
        assert response.json()["progress"] == 1.0

    def test_multi_document_queue(self, client, status_manager):
        """Test queue with multiple documents in different states."""
        docs = {
            "a" * 64: ("file1.pdf", "completed"),
            "b" * 64: ("file2.pdf", "parsing"),
            "c" * 64: ("file3.pdf", "embedding_visual"),
            "d" * 64: ("file4.pdf", "failed"),
        }

        for doc_id, (filename, target_status) in docs.items():
            status_manager.create_status(doc_id, filename, {})

            if target_status == "completed":
                status_manager.mark_completed(doc_id)
            elif target_status == "failed":
                status_manager.mark_failed(doc_id, "Test error")
            elif target_status != "queued":
                status_manager.update_status(doc_id, status=target_status, progress=0.5)

        # Check queue
        response = client.get("/status/queue")
        data = response.json()

        assert data["total"] == 4
        assert data["active"] == 2  # parsing + embedding_visual
        assert data["completed"] == 1
        assert data["failed"] == 1

    def test_queue_ordering(self, client, status_manager):
        """Test that queue returns most recent documents first."""
        import time

        # Create documents with slight delay
        for i in range(3):
            doc_id = str(i).zfill(64)
            status_manager.create_status(doc_id, f"file{i}.pdf", {})
            time.sleep(0.01)  # Small delay to ensure different timestamps

        response = client.get("/status/queue")
        data = response.json()

        # Should be in reverse order (most recent first)
        assert data["queue"][0]["filename"] == "file2.pdf"
        assert data["queue"][1]["filename"] == "file1.pdf"
        assert data["queue"][2]["filename"] == "file0.pdf"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

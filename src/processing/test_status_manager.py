"""
Unit tests for StatusManager class.

Tests thread-safe status management, model validation, and lifecycle operations.

Contract: status-manager.contract.md
"""

import pytest
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any

from .status_manager import StatusManager
from .status_models import (
    ProcessingStatus,
    ProcessingStatusEnum,
    QueueItem,
)


@pytest.fixture
def status_dict():
    """Create a fresh status dictionary for each test."""
    return {}


@pytest.fixture
def status_manager(status_dict):
    """Create a StatusManager instance for each test."""
    return StatusManager(status_dict)


class TestStatusManagerBasics:
    """Test basic status management operations."""

    def test_create_status(self, status_manager):
        """Test creating a new status entry."""
        doc_id = "a" * 64  # Valid SHA-256 hash
        filename = "test.pdf"
        metadata = {"format": "pdf", "file_size": 1024}

        status = status_manager.create_status(doc_id, filename, metadata)

        assert status.doc_id == doc_id
        assert status.filename == filename
        assert status.status == ProcessingStatusEnum.QUEUED
        assert status.progress == 0.0
        assert status.metadata == metadata
        assert status.error is None

    def test_create_duplicate_raises_error(self, status_manager):
        """Test that creating duplicate doc_id raises ValueError."""
        doc_id = "a" * 64
        filename = "test.pdf"
        metadata = {}

        status_manager.create_status(doc_id, filename, metadata)

        with pytest.raises(ValueError, match="already exists"):
            status_manager.create_status(doc_id, filename, metadata)

    def test_get_status(self, status_manager):
        """Test retrieving status for a document."""
        doc_id = "a" * 64
        status_manager.create_status(doc_id, "test.pdf", {})

        status = status_manager.get_status(doc_id)

        assert status is not None
        assert status.doc_id == doc_id

    def test_get_nonexistent_status(self, status_manager):
        """Test retrieving status for nonexistent document returns None."""
        status = status_manager.get_status("nonexistent" + "0" * 54)
        assert status is None

    def test_update_status(self, status_manager):
        """Test updating status fields."""
        doc_id = "a" * 64
        status_manager.create_status(doc_id, "test.pdf", {})

        status_manager.update_status(
            doc_id,
            status="parsing",
            progress=0.1,
            stage="Parsing document",
        )

        status = status_manager.get_status(doc_id)
        assert status.status == ProcessingStatusEnum.PARSING
        assert status.progress == 0.1
        assert status.stage == "Parsing document"

    def test_update_nonexistent_raises_error(self, status_manager):
        """Test updating nonexistent document raises KeyError."""
        with pytest.raises(KeyError, match="not found"):
            status_manager.update_status(
                "nonexistent" + "0" * 54, status="parsing", progress=0.1
            )

    def test_update_invalid_progress_raises_error(self, status_manager):
        """Test updating with invalid progress raises ValueError."""
        doc_id = "a" * 64
        status_manager.create_status(doc_id, "test.pdf", {})

        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            status_manager.update_status(doc_id, status="parsing", progress=1.5)

        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            status_manager.update_status(doc_id, status="parsing", progress=-0.1)


class TestStatusManagerLists:
    """Test listing and filtering status entries."""

    def test_list_active(self, status_manager):
        """Test listing only active documents."""
        # Create multiple documents with different statuses
        doc1 = "a" * 64
        doc2 = "b" * 64
        doc3 = "c" * 64

        status_manager.create_status(doc1, "file1.pdf", {})
        status_manager.create_status(doc2, "file2.pdf", {})
        status_manager.create_status(doc3, "file3.pdf", {})

        status_manager.mark_completed(doc1)
        status_manager.update_status(doc2, status="parsing", progress=0.1)
        # doc3 remains queued

        active = status_manager.list_active()

        assert len(active) == 2
        assert all(
            s.status
            not in [ProcessingStatusEnum.COMPLETED, ProcessingStatusEnum.FAILED]
            for s in active
        )

    def test_list_all(self, status_manager):
        """Test listing all documents with limit."""
        # Create multiple documents
        for i in range(5):
            doc_id = str(i).zfill(64)
            status_manager.create_status(doc_id, f"file{i}.pdf", {})

        all_statuses = status_manager.list_all(limit=3)

        assert len(all_statuses) == 3

    def test_list_as_queue_items(self, status_manager):
        """Test getting simplified queue items."""
        doc_id = "a" * 64
        status_manager.create_status(doc_id, "test.pdf", {})

        queue_items = status_manager.list_as_queue_items()

        assert len(queue_items) == 1
        assert isinstance(queue_items[0], QueueItem)
        assert queue_items[0].doc_id == doc_id

    def test_count_by_status(self, status_manager):
        """Test counting documents by status."""
        doc1 = "a" * 64
        doc2 = "b" * 64
        doc3 = "c" * 64
        doc4 = "d" * 64

        status_manager.create_status(doc1, "file1.pdf", {})
        status_manager.create_status(doc2, "file2.pdf", {})
        status_manager.create_status(doc3, "file3.pdf", {})
        status_manager.create_status(doc4, "file4.pdf", {})

        status_manager.mark_completed(doc1)
        status_manager.mark_completed(doc2)
        status_manager.mark_failed(doc3, "Test error")
        # doc4 remains queued

        counts = status_manager.count_by_status()

        assert counts["total"] == 4
        assert counts["completed"] == 2
        assert counts["failed"] == 1
        assert counts["active"] == 1


class TestStatusManagerCompletion:
    """Test marking documents as completed or failed."""

    def test_mark_completed(self, status_manager):
        """Test marking document as completed."""
        doc_id = "a" * 64
        status_manager.create_status(doc_id, "test.pdf", {})

        status_manager.mark_completed(doc_id, num_chunks=42)

        status = status_manager.get_status(doc_id)
        assert status.status == ProcessingStatusEnum.COMPLETED
        assert status.progress == 1.0
        assert status.completed_at is not None
        assert status.metadata["num_chunks"] == 42

    def test_mark_failed(self, status_manager):
        """Test marking document as failed."""
        doc_id = "a" * 64
        status_manager.create_status(doc_id, "test.pdf", {})

        error_msg = "Test error message"
        status_manager.mark_failed(doc_id, error_msg)

        status = status_manager.get_status(doc_id)
        assert status.status == ProcessingStatusEnum.FAILED
        assert status.error == error_msg
        assert status.completed_at is not None

    def test_mark_completed_nonexistent_raises_error(self, status_manager):
        """Test marking nonexistent document raises KeyError."""
        with pytest.raises(KeyError, match="not found"):
            status_manager.mark_completed("nonexistent" + "0" * 54)

    def test_mark_failed_nonexistent_raises_error(self, status_manager):
        """Test marking nonexistent document raises KeyError."""
        with pytest.raises(KeyError, match="not found"):
            status_manager.mark_failed("nonexistent" + "0" * 54, "error")


class TestStatusManagerCleanup:
    """Test cleanup of old status entries."""

    def test_cleanup_old_entries(self, status_manager):
        """Test cleanup removes old completed/failed entries."""
        doc1 = "a" * 64
        doc2 = "b" * 64
        doc3 = "c" * 64

        # Create and complete documents
        status_manager.create_status(doc1, "file1.pdf", {})
        status_manager.create_status(doc2, "file2.pdf", {})
        status_manager.create_status(doc3, "file3.pdf", {})

        status_manager.mark_completed(doc1)
        status_manager.mark_failed(doc2, "error")
        # doc3 remains active

        # Manually set old timestamps (simulate old entries)
        old_time = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        status_manager._status_dict[doc1]["updated_at"] = old_time
        status_manager._status_dict[doc2]["updated_at"] = old_time

        # Cleanup entries older than 1 hour
        removed = status_manager.cleanup_old_entries(max_age_seconds=3600)

        assert removed == 2
        assert status_manager.get_status(doc1) is None
        assert status_manager.get_status(doc2) is None
        assert status_manager.get_status(doc3) is not None

    def test_cleanup_preserves_active_entries(self, status_manager):
        """Test cleanup preserves active entries regardless of age."""
        doc_id = "a" * 64

        status_manager.create_status(doc_id, "file.pdf", {})

        # Manually set old timestamp
        old_time = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        status_manager._status_dict[doc_id]["updated_at"] = old_time

        # Cleanup should not remove active entry
        removed = status_manager.cleanup_old_entries(max_age_seconds=3600)

        assert removed == 0
        assert status_manager.get_status(doc_id) is not None


class TestStatusManagerThreadSafety:
    """Test thread-safe concurrent access."""

    def test_concurrent_updates(self, status_manager):
        """Test concurrent status updates are thread-safe."""
        doc_id = "a" * 64
        status_manager.create_status(doc_id, "test.pdf", {})

        def update_worker():
            for i in range(100):
                status_manager.update_status(
                    doc_id, status="parsing", progress=0.1
                )

        # Create multiple threads
        threads = [threading.Thread(target=update_worker) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify status is still valid
        status = status_manager.get_status(doc_id)
        assert status is not None
        assert status.progress == 0.1

    def test_concurrent_create_and_read(self, status_manager):
        """Test concurrent create and read operations."""
        created_docs = []

        def create_worker(worker_id):
            doc_id = str(worker_id).zfill(64)
            status_manager.create_status(doc_id, f"file{worker_id}.pdf", {})
            created_docs.append(doc_id)

        def read_worker():
            for _ in range(100):
                all_statuses = status_manager.list_all()
                # Just verify no exceptions

        # Create threads
        create_threads = [
            threading.Thread(target=create_worker, args=(i,)) for i in range(5)
        ]
        read_threads = [threading.Thread(target=read_worker) for _ in range(3)]

        all_threads = create_threads + read_threads

        for t in all_threads:
            t.start()
        for t in all_threads:
            t.join()

        # Verify all documents were created
        assert len(created_docs) == 5


class TestStatusManagerIntegration:
    """Integration tests with ProcessingStatus model."""

    def test_status_model_validation(self, status_manager):
        """Test that retrieved status passes Pydantic validation."""
        doc_id = "a" * 64
        metadata = {"format": "pdf", "format_type": "visual", "file_size": 2048}

        status_manager.create_status(doc_id, "test.pdf", metadata)
        status_manager.update_status(
            doc_id,
            status="embedding_visual",
            progress=0.65,
            page=13,
            total_pages=20,
        )

        status = status_manager.get_status(doc_id)

        # Pydantic validation happens automatically
        assert isinstance(status, ProcessingStatus)
        assert status.page == 13
        assert status.total_pages == 20

    def test_elapsed_time_calculation(self, status_manager):
        """Test that elapsed time is calculated correctly."""
        doc_id = "a" * 64
        status_manager.create_status(doc_id, "test.pdf", {})

        # Wait a bit
        time.sleep(0.1)

        status_manager.update_status(doc_id, status="parsing", progress=0.1)

        status = status_manager.get_status(doc_id)
        assert status.elapsed_time >= 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

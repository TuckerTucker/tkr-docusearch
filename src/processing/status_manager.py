"""
Thread-safe status manager for document processing.

This module provides the StatusManager class which wraps the global processing_status
dictionary with thread-safe access patterns and automatic cleanup.

Provider: status-persistence-agent
Consumers: api-endpoints-agent, processing-agent
Contract: status-manager.contract.md
"""

import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .status_models import ProcessingStatus, ProcessingStatusEnum, QueueItem, get_stage_description

logger = logging.getLogger(__name__)


class StatusManager:
    """
    Thread-safe manager for document processing status.

    Wraps the global processing_status dictionary to provide:
    - Thread-safe access via locking
    - Structured status updates
    - Automatic cleanup of old entries
    - Pydantic model validation
    """

    def __init__(self, status_dict: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Initialize StatusManager with existing processing_status dict.

        Args:
            status_dict: Existing status dictionary to wrap (optional, creates new if None)
        """
        self._lock = threading.Lock()
        self._status_dict = status_dict if status_dict is not None else {}
        logger.info("StatusManager initialized")

    def create_status(
        self, doc_id: str, filename: str, metadata: Dict[str, Any]
    ) -> ProcessingStatus:
        """
        Create a new processing status entry.

        Args:
            doc_id: Unique document identifier (SHA-256 hash)
            filename: Original filename
            metadata: Document metadata (format, size, etc.)

        Returns:
            ProcessingStatus object

        Raises:
            ValueError: If doc_id already exists
        """
        with self._lock:
            if doc_id in self._status_dict:
                raise ValueError(f"Document {doc_id} already exists in status tracker")

            now = datetime.utcnow()
            status = ProcessingStatus(
                doc_id=doc_id,
                filename=filename,
                status=ProcessingStatusEnum.QUEUED,
                progress=0.0,
                stage=get_stage_description(ProcessingStatusEnum.QUEUED),
                page=None,
                total_pages=None,
                started_at=now,
                updated_at=now,
                completed_at=None,
                elapsed_time=0.0,
                estimated_remaining=None,
                metadata=metadata,
                error=None,
            )

            # Store as dict in global status tracker
            self._status_dict[doc_id] = status.model_dump()

            logger.info(f"Created status for document {doc_id} (filename: {filename})")
            return status

    def get_status(self, doc_id: str) -> Optional[ProcessingStatus]:
        """
        Retrieve status for a specific document.

        Args:
            doc_id: Document identifier

        Returns:
            ProcessingStatus object or None if not found
        """
        with self._lock:
            status_dict = self._status_dict.get(doc_id)
            if status_dict is None:
                return None

            # Convert dict to Pydantic model
            return ProcessingStatus(**status_dict)

    def update_status(self, doc_id: str, status: str, progress: float, **kwargs) -> None:
        """
        Update processing status for a document.

        Args:
            doc_id: Document identifier
            status: New status value
            progress: Progress value (0.0-1.0)
            **kwargs: Additional fields (stage, page, total_pages, etc.)

        Raises:
            KeyError: If doc_id doesn't exist
            ValueError: If progress out of range or invalid status
        """
        with self._lock:
            if doc_id not in self._status_dict:
                raise KeyError(f"Document {doc_id} not found in status tracker")

            if not 0.0 <= progress <= 1.0:
                raise ValueError(f"Progress must be between 0.0 and 1.0, got {progress}")

            # Get existing status
            status_dict = self._status_dict[doc_id]
            status_enum = ProcessingStatusEnum(status)

            # Update fields
            status_dict["status"] = status_enum.value
            status_dict["progress"] = progress
            status_dict["updated_at"] = datetime.utcnow().isoformat()

            # Calculate elapsed time
            started_at = datetime.fromisoformat(status_dict["started_at"].replace("Z", "+00:00"))
            elapsed = (datetime.utcnow() - started_at).total_seconds()
            status_dict["elapsed_time"] = elapsed

            # Update stage if not provided
            if "stage" not in kwargs:
                kwargs["stage"] = get_stage_description(status_enum)

            # Update additional fields
            for key, value in kwargs.items():
                if key in ["page", "total_pages", "stage", "estimated_remaining"]:
                    status_dict[key] = value

            logger.debug(f"Updated status for {doc_id}: {status} ({progress:.0%})")

    def list_active(self) -> List[ProcessingStatus]:
        """
        Get all documents currently being processed.

        Returns:
            List of ProcessingStatus objects with status != completed/failed
        """
        with self._lock:
            active_statuses = []
            for doc_id, status_dict in self._status_dict.items():
                status = status_dict.get("status")
                if status not in [
                    ProcessingStatusEnum.COMPLETED.value,
                    ProcessingStatusEnum.FAILED.value,
                ]:
                    active_statuses.append(ProcessingStatus(**status_dict))

            # Sort by started_at (most recent first)
            active_statuses.sort(key=lambda s: s.started_at, reverse=True)
            return active_statuses

    def list_all(self, limit: int = 100) -> List[ProcessingStatus]:
        """
        Get all documents in status tracker.

        Args:
            limit: Maximum number of results (default: 100)

        Returns:
            List of ProcessingStatus objects (most recent first)
        """
        with self._lock:
            all_statuses = [
                ProcessingStatus(**status_dict) for status_dict in self._status_dict.values()
            ]

            # Sort by updated_at (most recent first)
            all_statuses.sort(key=lambda s: s.updated_at, reverse=True)

            # Apply limit
            return all_statuses[:limit]

    def list_as_queue_items(self, limit: int = 100) -> List[QueueItem]:
        """
        Get all documents as simplified queue items.

        Args:
            limit: Maximum number of results (default: 100)

        Returns:
            List of QueueItem objects (most recent first)
        """
        statuses = self.list_all(limit=limit)

        queue_items = []
        for status in statuses:
            queue_items.append(
                QueueItem(
                    doc_id=status.doc_id,
                    filename=status.filename,
                    status=status.status,
                    progress=status.progress,
                    elapsed_time=status.elapsed_time,
                    timestamp=status.updated_at,
                )
            )

        return queue_items

    def count_by_status(self) -> Dict[str, int]:
        """
        Get count of documents by status.

        Returns:
            Dictionary with counts: {active, completed, failed, total}
        """
        with self._lock:
            counts = {"active": 0, "completed": 0, "failed": 0, "total": 0}

            for status_dict in self._status_dict.values():
                status = status_dict.get("status")
                counts["total"] += 1

                if status == ProcessingStatusEnum.COMPLETED.value:
                    counts["completed"] += 1
                elif status == ProcessingStatusEnum.FAILED.value:
                    counts["failed"] += 1
                else:
                    counts["active"] += 1

            return counts

    def cleanup_old_entries(self, max_age_seconds: int = 3600) -> int:
        """
        Remove completed/failed entries older than max_age.

        Args:
            max_age_seconds: Max age in seconds (default: 1 hour)

        Returns:
            Number of entries removed
        """
        with self._lock:
            now = datetime.utcnow()
            cutoff_time = now - timedelta(seconds=max_age_seconds)

            doc_ids_to_remove = []

            for doc_id, status_dict in self._status_dict.items():
                status = status_dict.get("status")
                updated_at_str = status_dict.get("updated_at")

                # Only clean up completed/failed entries
                if status not in [
                    ProcessingStatusEnum.COMPLETED.value,
                    ProcessingStatusEnum.FAILED.value,
                ]:
                    continue

                # Parse updated_at timestamp
                try:
                    updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
                    if updated_at < cutoff_time:
                        doc_ids_to_remove.append(doc_id)
                except (ValueError, AttributeError):
                    # Invalid timestamp, skip
                    continue

            # Remove old entries
            for doc_id in doc_ids_to_remove:
                del self._status_dict[doc_id]

            if doc_ids_to_remove:
                logger.info(
                    f"Cleaned up {len(doc_ids_to_remove)} old status entries "
                    f"(older than {max_age_seconds}s)"
                )

            return len(doc_ids_to_remove)

    def mark_completed(self, doc_id: str, **kwargs) -> None:
        """
        Mark document as completed.

        Args:
            doc_id: Document identifier
            **kwargs: Additional metadata (num_chunks, storage_ids, etc.)

        Raises:
            KeyError: If doc_id doesn't exist
        """
        now = datetime.utcnow()

        with self._lock:
            if doc_id not in self._status_dict:
                raise KeyError(f"Document {doc_id} not found in status tracker")

            status_dict = self._status_dict[doc_id]

            # Update status
            status_dict["status"] = ProcessingStatusEnum.COMPLETED.value
            status_dict["progress"] = 1.0
            status_dict["stage"] = get_stage_description(ProcessingStatusEnum.COMPLETED)
            status_dict["updated_at"] = now.isoformat()
            status_dict["completed_at"] = now.isoformat()
            status_dict["estimated_remaining"] = None

            # Calculate final elapsed time
            started_at = datetime.fromisoformat(status_dict["started_at"].replace("Z", "+00:00"))
            elapsed = (now - started_at).total_seconds()
            status_dict["elapsed_time"] = elapsed

            # Add additional metadata
            for key, value in kwargs.items():
                if key in ["num_chunks", "storage_ids"]:
                    status_dict["metadata"][key] = value

            logger.info(f"Marked document {doc_id} as completed " f"(elapsed: {elapsed:.1f}s)")

    def mark_failed(self, doc_id: str, error: str) -> None:
        """
        Mark document as failed.

        Args:
            doc_id: Document identifier
            error: Error message

        Raises:
            KeyError: If doc_id doesn't exist
        """
        now = datetime.utcnow()

        with self._lock:
            if doc_id not in self._status_dict:
                raise KeyError(f"Document {doc_id} not found in status tracker")

            status_dict = self._status_dict[doc_id]

            # Update status
            status_dict["status"] = ProcessingStatusEnum.FAILED.value
            status_dict["stage"] = get_stage_description(ProcessingStatusEnum.FAILED)
            status_dict["updated_at"] = now.isoformat()
            status_dict["completed_at"] = now.isoformat()
            status_dict["error"] = error
            status_dict["estimated_remaining"] = None

            # Calculate final elapsed time
            started_at = datetime.fromisoformat(status_dict["started_at"].replace("Z", "+00:00"))
            elapsed = (now - started_at).total_seconds()
            status_dict["elapsed_time"] = elapsed

            logger.error(
                f"Marked document {doc_id} as failed: {error} " f"(elapsed: {elapsed:.1f}s)"
            )


# Singleton instance (will be initialized with worker's global processing_status dict)
_status_manager_instance: Optional[StatusManager] = None


def get_status_manager(status_dict: Optional[Dict[str, Dict[str, Any]]] = None) -> StatusManager:
    """
    Get or create the global StatusManager instance.

    Args:
        status_dict: Status dictionary to wrap (only used on first call)

    Returns:
        StatusManager singleton instance
    """
    global _status_manager_instance

    if _status_manager_instance is None:
        _status_manager_instance = StatusManager(status_dict)

    return _status_manager_instance

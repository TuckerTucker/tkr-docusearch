"""
Thread-safe status manager for document processing.

This module provides the StatusManager class which wraps the global processing_status
dictionary with thread-safe access patterns and automatic cleanup.

Provider: status-persistence-agent
Consumers: api-endpoints-agent, processing-agent
Contract: status-manager.contract.md
"""

import threading
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import ValidationError

from .status_models import (
    ProcessingStatus,
    ProcessingStatusEnum,
    QueueItem,
    get_stage_description,
    calculate_progress,
)

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

            # Store as dict in global status tracker (serialize datetimes to strings)
            self._status_dict[doc_id] = status.model_dump(mode='json')

            logger.info(
                f"Created status for document {doc_id} (filename: {filename})"
            )
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

    def update_status(
        self, doc_id: str, status: str, progress: float, **kwargs
    ) -> None:
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
            started_at = status_dict["started_at"]
            # Handle both datetime objects and ISO strings
            if isinstance(started_at, str):
                started_at = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
            elapsed = (datetime.utcnow() - started_at).total_seconds()
            status_dict["elapsed_time"] = elapsed

            # Update stage if not provided
            if "stage" not in kwargs:
                kwargs["stage"] = get_stage_description(status_enum)

            # Update additional fields
            for key, value in kwargs.items():
                if key in ["page", "total_pages", "stage", "estimated_remaining"]:
                    status_dict[key] = value

            logger.debug(
                f"Updated status for {doc_id}: {status} ({progress:.0%})"
            )

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
            all_statuses = []

            for doc_id, status_dict in self._status_dict.items():
                try:
                    status = ProcessingStatus(**status_dict)
                    all_statuses.append(status)
                except ValidationError as e:
                    # Skip invalid entries (likely stale data from previous runs)
                    logger.warning(
                        f"Skipping invalid status entry for {doc_id}: {e.error_count()} validation error(s)"
                    )
                    continue

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
                    error=status.error,
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
                    updated_at = datetime.fromisoformat(
                        updated_at_str.replace("Z", "+00:00")
                    )
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

    # ====================================================================
    # Wave 2, Agent 5: Dashboard Enhancement Methods
    # ====================================================================

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive dashboard statistics.

        Returns:
            Dictionary with dashboard stats including:
            - queue_size: Documents queued
            - processing_count: Documents currently processing
            - completed_today: Completed since midnight
            - failed_today: Failed since midnight
            - avg_processing_time_seconds: Average time for completed docs
            - estimated_wait_time_seconds: Estimated wait time
            - current_processing: Currently processing document details
            - recent_documents: Last 5 documents
        """
        with self._lock:
            # Get today's start (midnight local time)
            today_start = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            queue_size = 0
            processing_count = 0
            completed_today = 0
            failed_today = 0
            processing_times = []
            current_processing = None
            recent_documents = []

            # Collect all documents sorted by updated_at (newest first)
            all_docs = []
            for doc_id, status_dict in self._status_dict.items():
                all_docs.append((doc_id, status_dict))

            # Sort by updated_at descending
            all_docs.sort(
                key=lambda x: x[1].get("updated_at", ""),
                reverse=True
            )

            # Process documents
            for doc_id, status_dict in all_docs:
                status = status_dict.get("status")

                # Count queued/processing
                if status == ProcessingStatusEnum.QUEUED.value:
                    queue_size += 1
                elif status in [
                    ProcessingStatusEnum.PARSING.value,
                    ProcessingStatusEnum.EMBEDDING_VISUAL.value,
                    ProcessingStatusEnum.EMBEDDING_TEXT.value,
                    ProcessingStatusEnum.STORING.value,
                ]:
                    processing_count += 1
                    # Get first processing document details
                    if current_processing is None:
                        current_processing = self._build_current_processing(
                            doc_id, status_dict
                        )

                # Count completed/failed today
                completed_at_str = status_dict.get("completed_at")
                if completed_at_str:
                    try:
                        completed_at = datetime.fromisoformat(
                            completed_at_str.replace("Z", "+00:00")
                        )
                        if completed_at >= today_start:
                            if status == ProcessingStatusEnum.COMPLETED.value:
                                completed_today += 1
                            elif status == ProcessingStatusEnum.FAILED.value:
                                failed_today += 1
                    except (ValueError, AttributeError):
                        pass

                # Collect processing times for completed docs
                if status == ProcessingStatusEnum.COMPLETED.value:
                    elapsed = status_dict.get("elapsed_time")
                    if elapsed:
                        processing_times.append(elapsed)

                # Build recent documents list (max 5)
                if len(recent_documents) < 5:
                    recent_doc = self._build_recent_document(doc_id, status_dict)
                    if recent_doc:
                        recent_documents.append(recent_doc)

            # Calculate average processing time
            avg_processing_time = (
                sum(processing_times) / len(processing_times)
                if processing_times
                else 0.0
            )

            # Estimate wait time
            estimated_wait = queue_size * avg_processing_time if avg_processing_time > 0 else 0.0

            return {
                "queue_size": queue_size,
                "processing_count": processing_count,
                "completed_today": completed_today,
                "failed_today": failed_today,
                "avg_processing_time_seconds": round(avg_processing_time, 1),
                "estimated_wait_time_seconds": round(estimated_wait, 1),
                "current_processing": current_processing,
                "recent_documents": recent_documents,
            }

    def _build_current_processing(
        self, doc_id: str, status_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build current processing details from status dict."""
        started_at_str = status_dict.get("started_at")
        elapsed = 0
        eta = 0

        if started_at_str:
            try:
                started_at = datetime.fromisoformat(
                    started_at_str.replace("Z", "+00:00")
                )
                elapsed = int((datetime.utcnow() - started_at).total_seconds())
            except (ValueError, AttributeError):
                pass

        # Estimate ETA based on progress
        progress = status_dict.get("progress", 0.0)
        if progress > 0.1:  # Avoid division by zero
            total_estimated = elapsed / progress
            eta = int(total_estimated - elapsed)

        return {
            "doc_id": doc_id,
            "filename": status_dict.get("filename", "unknown"),
            "status": status_dict.get("status", "unknown"),
            "progress": status_dict.get("progress", 0.0),
            "stage": status_dict.get("stage", ""),
            "page": status_dict.get("page"),
            "total_pages": status_dict.get("total_pages"),
            "elapsed_seconds": elapsed,
            "eta_seconds": max(0, eta),
        }

    def _build_recent_document(
        self, doc_id: str, status_dict: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Build recent document entry from status dict."""
        status = status_dict.get("status")
        if not status:
            return None

        doc = {
            "doc_id": doc_id,
            "filename": status_dict.get("filename", "unknown"),
            "status": status.replace("_", " "),  # Human-readable
            "created_at": status_dict.get("started_at", ""),
        }

        # Add completion info
        if status in [
            ProcessingStatusEnum.COMPLETED.value,
            ProcessingStatusEnum.FAILED.value,
        ]:
            doc["completed_at"] = status_dict.get("completed_at", "")
            doc["processing_time_seconds"] = status_dict.get("elapsed_time")

        # Add error if failed
        if status == ProcessingStatusEnum.FAILED.value:
            doc["error_message"] = status_dict.get("error", "Unknown error")

        return doc

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
            started_at = datetime.fromisoformat(
                status_dict["started_at"].replace("Z", "+00:00")
            )
            elapsed = (now - started_at).total_seconds()
            status_dict["elapsed_time"] = elapsed

            # Add additional metadata
            for key, value in kwargs.items():
                if key in ["num_chunks", "storage_ids", "visual_embeddings", "text_embeddings", "text_chunks"]:
                    status_dict["metadata"][key] = value

            logger.info(
                f"Marked document {doc_id} as completed "
                f"(elapsed: {elapsed:.1f}s)"
            )

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
            started_at = datetime.fromisoformat(
                status_dict["started_at"].replace("Z", "+00:00")
            )
            elapsed = (now - started_at).total_seconds()
            status_dict["elapsed_time"] = elapsed

            logger.error(
                f"Marked document {doc_id} as failed: {error} "
                f"(elapsed: {elapsed:.1f}s)"
            )

    def remove_status(self, doc_id: str) -> bool:
        """
        Remove document status from tracker.

        Used when deleting documents from the system.

        Args:
            doc_id: Document identifier

        Returns:
            True if document was removed, False if not found
        """
        with self._lock:
            if doc_id in self._status_dict:
                del self._status_dict[doc_id]
                logger.info(f"Removed document {doc_id} from status tracker")
                return True
            else:
                logger.warning(f"Document {doc_id} not found in status tracker")
                return False


# Singleton instance (will be initialized with worker's global processing_status dict)
_status_manager_instance: Optional[StatusManager] = None


def get_status_manager(
    status_dict: Optional[Dict[str, Dict[str, Any]]] = None
) -> StatusManager:
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

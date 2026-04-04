"""Status API endpoints for document processing.

Reads processing job status from the ``processing_jobs`` table in Koji.
Falls back to the in-memory ``StatusManager`` for backward compatibility
with tests that don't use the job queue.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query

from .status_manager import StatusManager
from .status_models import (
    ErrorResponse,
    ProcessingStatus,
    ProcessingStatusEnum,
    QueueItem,
    QueueResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/status", tags=["status"])

_status_manager: Optional[StatusManager] = None
_koji_client: Optional[Any] = None


def set_status_manager(manager: StatusManager) -> None:
    """Set the StatusManager instance (legacy in-memory fallback)."""
    global _status_manager
    _status_manager = manager
    logger.info("Status API router initialized with StatusManager")


def set_status_koji_client(client: Any) -> None:
    """Set the KojiClient for reading processing_jobs."""
    global _koji_client
    _koji_client = client


def _job_to_queue_item(job: dict) -> QueueItem:
    """Convert a Koji processing_jobs row to a QueueItem."""
    status_str = job.get("status", "queued")
    try:
        status_enum = ProcessingStatusEnum(status_str)
    except ValueError:
        status_enum = ProcessingStatusEnum.QUEUED

    queued_at = job.get("queued_at") or datetime.now(timezone.utc).isoformat()
    try:
        ts = datetime.fromisoformat(queued_at.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        ts = datetime.now(timezone.utc)

    started = job.get("started_at")
    elapsed = 0.0
    if started:
        try:
            start_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
            elapsed = (datetime.now(timezone.utc) - start_dt).total_seconds()
        except (ValueError, AttributeError):
            pass

    return QueueItem(
        doc_id=job["doc_id"],
        filename=job.get("filename", "unknown"),
        status=status_enum,
        progress=job.get("progress", 0.0) or 0.0,
        elapsed_time=elapsed,
        timestamp=ts,
        error=job.get("error"),
    )


# ============================================================================
# Endpoints
# ============================================================================


@router.get(
    "/queue",
    response_model=QueueResponse,
    summary="Get processing queue",
)
async def get_processing_queue(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000),
) -> QueueResponse:
    """Get all documents in the processing queue."""
    if _koji_client is not None:
        jobs = _koji_client.list_jobs(status=status, limit=limit)
        queue_items = [_job_to_queue_item(j) for j in jobs]

        all_jobs = _koji_client.list_jobs(limit=1000)
        active = sum(1 for j in all_jobs if j["status"] in ("queued", "processing"))
        completed = sum(1 for j in all_jobs if j["status"] == "completed")
        failed = sum(1 for j in all_jobs if j["status"] == "failed")

        return QueueResponse(
            queue=queue_items,
            total=len(all_jobs),
            active=active,
            completed=completed,
            failed=failed,
        )

    # Fallback: in-memory StatusManager
    if _status_manager is None:
        return QueueResponse(queue=[], total=0, active=0, completed=0, failed=0)

    queue_items = _status_manager.list_as_queue_items(limit=limit)
    if status is not None:
        queue_items = [i for i in queue_items if i.status.value == status]
    counts = _status_manager.count_by_status()

    return QueueResponse(
        queue=queue_items,
        total=counts["total"],
        active=counts["active"],
        completed=counts["completed"],
        failed=counts["failed"],
    )


@router.get(
    "/health",
    summary="Health check",
)
async def health_check():
    """Check if the status API is operational."""
    if _koji_client is not None:
        jobs = _koji_client.list_jobs(limit=1000)
        active = sum(1 for j in jobs if j["status"] in ("queued", "processing"))
        completed = sum(1 for j in jobs if j["status"] == "completed")
        failed = sum(1 for j in jobs if j["status"] == "failed")
        return {
            "status": "healthy",
            "service": "status-api",
            "queue_stats": {
                "total": len(jobs),
                "active": active,
                "completed": completed,
                "failed": failed,
            },
        }

    if _status_manager is not None:
        counts = _status_manager.count_by_status()
        return {
            "status": "healthy",
            "service": "status-api",
            "queue_stats": counts,
        }

    return {"status": "healthy", "service": "status-api", "queue_stats": {}}


@router.get(
    "/",
    response_model=QueueResponse,
    include_in_schema=False,
)
async def get_processing_queue_root(
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
) -> QueueResponse:
    """Alias for /status/queue."""
    return await get_processing_queue(status=status, limit=limit)


# ============================================================================
# Document Status (catch-all — must be LAST)
# ============================================================================


@router.get(
    "/{doc_id}",
    responses={
        200: {"description": "Document status retrieved"},
        404: {"description": "Document not found", "model": ErrorResponse},
    },
    summary="Get document status",
)
async def get_document_status(doc_id: str):
    """Get processing status for a specific document."""
    # Try Koji job queue first
    if _koji_client is not None:
        job = _koji_client.get_job(doc_id)
        if job is not None:
            item = _job_to_queue_item(job)
            return {
                "doc_id": item.doc_id,
                "filename": item.filename,
                "status": item.status.value,
                "progress": item.progress,
                "stage": job.get("stage", ""),
                "elapsed_time": item.elapsed_time,
                "error": item.error,
            }

    # Fallback: in-memory StatusManager
    if _status_manager is not None:
        status = _status_manager.get_status(doc_id)
        if status is not None:
            return status

    raise HTTPException(
        status_code=404,
        detail={
            "error": "Document not found",
            "code": "DOCUMENT_NOT_FOUND",
            "details": {"doc_id": doc_id},
        },
    )

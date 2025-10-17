"""
Status API endpoints for document processing.

Provides HTTP endpoints for querying document processing status and queue information.

Provider: api-endpoints-agent
Consumers: monitoring-logic-agent (Wave 3), upload-logic-agent (Wave 3)
Contract: status-api.contract.md
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from .status_manager import StatusManager
from .status_models import ErrorResponse, ProcessingStatus, QueueResponse

logger = logging.getLogger(__name__)

# Router for status endpoints
router = APIRouter(prefix="/status", tags=["status"])

# StatusManager instance (will be injected at startup)
_status_manager: Optional[StatusManager] = None


def set_status_manager(manager: StatusManager) -> None:
    """
    Set the StatusManager instance for this API router.

    Args:
        manager: StatusManager instance to use
    """
    global _status_manager
    _status_manager = manager
    logger.info("Status API router initialized with StatusManager")


def get_status_manager() -> StatusManager:
    """
    Get the StatusManager instance.

    Returns:
        StatusManager instance

    Raises:
        RuntimeError: If StatusManager not initialized
    """
    if _status_manager is None:
        raise RuntimeError("StatusManager not initialized. Call set_status_manager() first.")
    return _status_manager


# ============================================================================
# Endpoints
# ============================================================================
# NOTE: Specific routes (/queue, /health) must come before path parameter routes (/{doc_id})


@router.get(
    "/queue",
    response_model=QueueResponse,
    responses={
        200: {"description": "Queue retrieved successfully"},
    },
    summary="Get processing queue",
    description="Retrieve all documents currently being processed or queued",
)
async def get_processing_queue(
    status: Optional[str] = Query(
        None,
        description="Filter by status (queued, parsing, embedding_visual, etc.)",
    ),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results to return"),
) -> QueueResponse:
    """
    Get all documents in processing queue.

    Args:
        status: Optional status filter
        limit: Maximum number of results (1-1000)

    Returns:
        QueueResponse with queue items and statistics
    """
    manager = get_status_manager()

    # Get all queue items
    queue_items = manager.list_as_queue_items(limit=limit)

    # Apply status filter if provided
    if status is not None:
        queue_items = [item for item in queue_items if item.status.value == status]

    # Get counts
    counts = manager.count_by_status()

    response = QueueResponse(
        queue=queue_items,
        total=counts["total"],
        active=counts["active"],
        completed=counts["completed"],
        failed=counts["failed"],
    )

    logger.debug(
        f"Retrieved queue: {len(queue_items)} items "
        f"(active: {counts['active']}, completed: {counts['completed']}, "
        f"failed: {counts['failed']})"
    )

    return response


@router.get(
    "/{doc_id}",
    response_model=ProcessingStatus,
    responses={
        200: {"description": "Document status retrieved successfully"},
        404: {
            "description": "Document not found",
            "model": ErrorResponse,
        },
    },
    summary="Get document status",
    description="Retrieve the current processing status for a specific document by doc_id",
)
async def get_document_status(doc_id: str) -> ProcessingStatus:
    """
    Get status for a specific document.

    Args:
        doc_id: SHA-256 document hash

    Returns:
        ProcessingStatus object

    Raises:
        HTTPException: 404 if document not found
    """
    manager = get_status_manager()

    status = manager.get_status(doc_id)

    if status is None:
        logger.warning(f"Document not found: {doc_id}")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Document not found",
                "code": "DOCUMENT_NOT_FOUND",
                "details": {"doc_id": doc_id},
            },
        )

    logger.debug(f"Retrieved status for document {doc_id}: {status.status.value}")
    return status


@router.get(
    "/",
    response_model=QueueResponse,
    responses={
        200: {"description": "Queue retrieved successfully"},
    },
    summary="Get processing queue (root)",
    description="Alias for /status/queue endpoint",
    include_in_schema=False,  # Hide from docs (prefer /queue)
)
async def get_processing_queue_root(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results to return"),
) -> QueueResponse:
    """
    Get all documents in processing queue (root endpoint).

    This is an alias for GET /status/queue for convenience.
    """
    return await get_processing_queue(status=status, limit=limit)


# ============================================================================
# Health/Info Endpoints
# ============================================================================


@router.get(
    "/health",
    responses={200: {"description": "Status API is healthy"}},
    summary="Health check",
    description="Check if the status API is operational",
    include_in_schema=True,
)
async def health_check():
    """
    Health check endpoint.

    Returns:
        Health status information
    """
    manager = get_status_manager()
    counts = manager.count_by_status()

    return {
        "status": "healthy",
        "service": "status-api",
        "queue_stats": counts,
    }


# ============================================================================
# CORS Middleware Configuration
# ============================================================================

# CORS headers are configured at the FastAPI app level
# See worker_webhook.py for CORS middleware setup

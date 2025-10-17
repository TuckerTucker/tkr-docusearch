"""
Pydantic models for document processing status.

This module defines the data structures used for tracking document processing status
across the DocuSearch pipeline. Models include validation, serialization, and
examples for API documentation.

Provider: status-persistence-agent
Consumers: api-endpoints-agent, processing-agent
Contract: status-manager.contract.md
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator


class ProcessingStatusEnum(str, Enum):
    """Valid processing status values."""

    QUEUED = "queued"
    PARSING = "parsing"
    EMBEDDING_VISUAL = "embedding_visual"
    EMBEDDING_TEXT = "embedding_text"
    STORING = "storing"
    COMPLETED = "completed"
    FAILED = "failed"


class FormatType(str, Enum):
    """Document format categories."""

    VISUAL = "visual"
    TEXT = "text"
    AUDIO = "audio"


class ProcessingStatus(BaseModel):
    """
    Status model for document processing.

    This model tracks the complete lifecycle of a document through the
    processing pipeline, including progress, timing, and error information.
    """

    # Document identification
    doc_id: str = Field(
        ...,
        description="SHA-256 document hash",
        min_length=64,
        max_length=64,
        pattern=r"^[a-f0-9]{64}$",
    )
    filename: str = Field(..., description="Original filename", min_length=1, max_length=255)

    # Status tracking
    status: ProcessingStatusEnum = Field(..., description="Current processing status")
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress value between 0.0 and 1.0")
    stage: str = Field(..., description="Human-readable current stage")

    # Progress details
    page: Optional[int] = Field(
        None, description="Current page being processed (null if not applicable)", ge=1
    )
    total_pages: Optional[int] = Field(
        None, description="Total pages in document (null if not applicable)", ge=1
    )

    # Timing
    started_at: datetime = Field(..., description="Processing start time (UTC)")
    updated_at: datetime = Field(..., description="Last update time (UTC)")
    completed_at: Optional[datetime] = Field(
        None, description="Completion time (UTC), null if not completed"
    )
    elapsed_time: float = Field(..., ge=0.0, description="Seconds elapsed since processing started")
    estimated_remaining: Optional[float] = Field(
        None, ge=0.0, description="Estimated seconds remaining (null if unavailable)"
    )

    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Document metadata (format, size, etc.)"
    )

    # Error tracking
    error: Optional[str] = Field(
        None, description="Error message if status is 'failed', null otherwise"
    )

    @field_validator("page", "total_pages")
    @classmethod
    def validate_page_numbers(cls, v: Optional[int], info) -> Optional[int]:
        """Ensure page numbers are positive if provided."""
        if v is not None and v < 1:
            raise ValueError("Page numbers must be >= 1")
        return v

    @field_validator("completed_at")
    @classmethod
    def validate_completed_at(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Ensure completed_at is only set for completed/failed status."""
        values = info.data
        status = values.get("status")
        if v is not None and status not in [
            ProcessingStatusEnum.COMPLETED,
            ProcessingStatusEnum.FAILED,
        ]:
            raise ValueError("completed_at should only be set for completed/failed status")
        return v

    @field_validator("error")
    @classmethod
    def validate_error(cls, v: Optional[str], info) -> Optional[str]:
        """Ensure error is only set for failed status."""
        values = info.data
        status = values.get("status")
        if v is not None and status != ProcessingStatusEnum.FAILED:
            raise ValueError("error should only be set for failed status")
        if v is None and status == ProcessingStatusEnum.FAILED:
            raise ValueError("error is required for failed status")
        return v

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "examples": [
                {
                    "doc_id": "abc123def456789abcdef0123456789abcdef0123456789abcdef0123456789ab",
                    "filename": "report.pdf",
                    "status": "embedding_visual",
                    "progress": 0.65,
                    "stage": "Generating visual embeddings",
                    "page": 13,
                    "total_pages": 20,
                    "started_at": "2025-10-07T19:00:00Z",
                    "updated_at": "2025-10-07T19:01:30Z",
                    "completed_at": None,
                    "elapsed_time": 90.0,
                    "estimated_remaining": 48.5,
                    "metadata": {
                        "format": "pdf",
                        "format_type": "visual",
                        "file_size": 2458624,
                    },
                    "error": None,
                }
            ]
        }


class QueueItem(BaseModel):
    """
    Simplified status model for queue display.

    Used by GET /status/queue endpoint to return lightweight status information.
    """

    doc_id: str = Field(..., description="SHA-256 document hash", pattern=r"^[a-f0-9]{64}$")
    filename: str = Field(..., description="Original filename", min_length=1, max_length=255)
    status: ProcessingStatusEnum = Field(..., description="Current processing status")
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress value between 0.0 and 1.0")
    elapsed_time: float = Field(..., ge=0.0, description="Seconds elapsed since processing started")
    timestamp: datetime = Field(..., description="Last update time in ISO 8601 format (UTC)")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "examples": [
                {
                    "doc_id": "abc123def456789abcdef0123456789abcdef0123456789abcdef0123456789ab",
                    "filename": "report.pdf",
                    "status": "embedding_visual",
                    "progress": 0.65,
                    "elapsed_time": 45.2,
                    "timestamp": "2025-10-07T19:30:00Z",
                }
            ]
        }


class QueueResponse(BaseModel):
    """
    Response model for GET /status/queue endpoint.

    Includes array of queue items plus summary statistics.
    """

    queue: list[QueueItem] = Field(..., description="Array of status objects (simplified)")
    total: int = Field(..., ge=0, description="Total documents in response")
    active: int = Field(..., ge=0, description="Count of documents with status != completed/failed")
    completed: int = Field(..., ge=0, description="Count of completed documents")
    failed: int = Field(..., ge=0, description="Count of failed documents")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "examples": [
                {
                    "queue": [
                        {
                            "doc_id": "abc123def456789abcdef0123456789abcdef0123456789abcdef0123456789ab",
                            "filename": "report.pdf",
                            "status": "embedding_visual",
                            "progress": 0.65,
                            "elapsed_time": 45.2,
                            "timestamp": "2025-10-07T19:30:00Z",
                        }
                    ],
                    "total": 1,
                    "active": 1,
                    "completed": 0,
                    "failed": 0,
                }
            ]
        }


class WebhookResponse(BaseModel):
    """
    Response model for POST /webhook endpoint.

    Returns document ID for accepted uploads or error for rejected uploads.
    """

    status: str = Field(..., description="Response status", pattern=r"^(accepted|rejected)$")
    doc_id: Optional[str] = Field(
        None,
        description="SHA-256 document hash (required when status is 'accepted')",
        pattern=r"^[a-f0-9]{64}$",
    )
    filename: Optional[str] = Field(
        None, description="Original filename", min_length=1, max_length=255
    )
    message: Optional[str] = Field(None, description="Human-readable message")
    error: Optional[str] = Field(
        None, description="Error message (required when status is 'rejected')"
    )

    @field_validator("doc_id")
    @classmethod
    def validate_doc_id_for_accepted(cls, v: Optional[str], info) -> Optional[str]:
        """Ensure doc_id is present for accepted status."""
        values = info.data
        status = values.get("status")
        if status == "accepted" and v is None:
            raise ValueError("doc_id is required when status is 'accepted'")
        return v

    @field_validator("error")
    @classmethod
    def validate_error_for_rejected(cls, v: Optional[str], info) -> Optional[str]:
        """Ensure error is present for rejected status."""
        values = info.data
        status = values.get("status")
        if status == "rejected" and v is None:
            raise ValueError("error is required when status is 'rejected'")
        return v

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "examples": [
                {
                    "status": "accepted",
                    "doc_id": "abc123def456789abcdef0123456789abcdef0123456789abcdef0123456789ab",
                    "filename": "report.pdf",
                    "message": "Document queued for processing",
                }
            ]
        }


class ErrorResponse(BaseModel):
    """
    Standard error response format for all API endpoints.

    Provides consistent error structure with human-readable message,
    machine-readable code, and optional details.
    """

    error: str = Field(..., description="Human-readable error message", min_length=1)
    code: Optional[str] = Field(None, description="Machine-readable error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "examples": [
                {
                    "error": "Document not found",
                    "code": "DOCUMENT_NOT_FOUND",
                    "details": {
                        "doc_id": "abc123def456789abcdef0123456789abcdef0123456789abcdef0123456789ab"
                    },
                }
            ]
        }


# Helper functions for status stage descriptions
def get_stage_description(status: ProcessingStatusEnum) -> str:
    """
    Get human-readable stage description for a status.

    Args:
        status: Processing status enum value

    Returns:
        Human-readable stage description
    """
    stage_map = {
        ProcessingStatusEnum.QUEUED: "Queued for processing",
        ProcessingStatusEnum.PARSING: "Parsing document",
        ProcessingStatusEnum.EMBEDDING_VISUAL: "Generating visual embeddings",
        ProcessingStatusEnum.EMBEDDING_TEXT: "Generating text embeddings",
        ProcessingStatusEnum.STORING: "Storing in database",
        ProcessingStatusEnum.COMPLETED: "Completed successfully",
        ProcessingStatusEnum.FAILED: "Processing failed",
    }
    return stage_map.get(status, "Unknown status")


def calculate_progress(
    status: ProcessingStatusEnum,
    page: Optional[int] = None,
    total_pages: Optional[int] = None,
    chunk: Optional[int] = None,
    total_chunks: Optional[int] = None,
) -> float:
    """
    Calculate progress value based on current stage and details.

    Progress breakdown:
    - queued: 0.0
    - parsing: 0.1
    - embedding_visual: 0.1 - 0.6 (based on page progress)
    - embedding_text: 0.6 - 0.9 (based on chunk progress)
    - storing: 0.95
    - completed: 1.0
    - failed: varies (last known progress)

    Args:
        status: Current processing status
        page: Current page number (for visual processing)
        total_pages: Total pages (for visual processing)
        chunk: Current chunk number (for text processing)
        total_chunks: Total chunks (for text processing)

    Returns:
        Progress value between 0.0 and 1.0
    """
    if status == ProcessingStatusEnum.QUEUED:
        return 0.0
    elif status == ProcessingStatusEnum.PARSING:
        return 0.1
    elif status == ProcessingStatusEnum.EMBEDDING_VISUAL:
        if page is not None and total_pages is not None and total_pages > 0:
            page_progress = page / total_pages
            return 0.1 + (page_progress * 0.5)
        return 0.35  # Default to midpoint if no page info
    elif status == ProcessingStatusEnum.EMBEDDING_TEXT:
        if chunk is not None and total_chunks is not None and total_chunks > 0:
            chunk_progress = chunk / total_chunks
            return 0.6 + (chunk_progress * 0.3)
        return 0.75  # Default to midpoint if no chunk info
    elif status == ProcessingStatusEnum.STORING:
        return 0.95
    elif status == ProcessingStatusEnum.COMPLETED:
        return 1.0
    else:  # FAILED or unknown
        return 0.0

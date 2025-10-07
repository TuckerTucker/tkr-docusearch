"""
API request/response models for DocuSearch.

Defines Pydantic models for type-safe API communication.
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


# ============================================================================
# Search Models
# ============================================================================

class SearchRequest(BaseModel):
    """Request model for document search."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Search query text"
    )
    n_results: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of results to return"
    )
    search_mode: Literal["visual", "text", "hybrid"] = Field(
        default="hybrid",
        description="Search mode: visual (images only), text (text only), or hybrid (both)"
    )
    min_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score threshold"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "revenue growth Q3 2024",
                "n_results": 10,
                "search_mode": "hybrid",
                "min_score": 0.5
            }
        }


class SearchResult(BaseModel):
    """Single search result."""

    doc_id: str = Field(..., description="Document ID")
    chunk_id: Optional[str] = Field(None, description="Chunk ID for text results")
    page_num: Optional[int] = Field(None, description="Page number for visual results")
    score: float = Field(..., description="Similarity score (0-1)")
    text_preview: Optional[str] = Field(None, description="Text preview snippet")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "doc_id": "financial-report-2024",
                "chunk_id": "chunk_12",
                "page_num": 5,
                "score": 0.87,
                "text_preview": "Revenue grew by 23% in Q3...",
                "metadata": {"filename": "report.pdf", "upload_date": "2024-01-15"}
            }
        }


class SearchResponse(BaseModel):
    """Response model for search results."""

    query: str = Field(..., description="Original search query")
    results: List[SearchResult] = Field(..., description="List of search results")
    total_results: int = Field(..., description="Total number of results")
    search_time_ms: float = Field(..., description="Search execution time in milliseconds")
    search_mode: str = Field(..., description="Search mode used")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "revenue growth Q3 2024",
                "results": [],
                "total_results": 15,
                "search_time_ms": 239.5,
                "search_mode": "hybrid"
            }
        }


# ============================================================================
# Upload Models
# ============================================================================

class UploadResponse(BaseModel):
    """Response model for document upload."""

    success: bool = Field(..., description="Upload success status")
    doc_id: str = Field(..., description="Assigned document ID")
    filename: str = Field(..., description="Original filename")
    file_size_bytes: int = Field(..., description="File size in bytes")
    status: str = Field(..., description="Processing status: queued, processing, completed, failed")
    message: Optional[str] = Field(None, description="Status message or error details")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "doc_id": "doc_abc123",
                "filename": "financial-report.pdf",
                "file_size_bytes": 2048576,
                "status": "queued",
                "message": "Document queued for processing"
            }
        }


class ProcessingStatus(BaseModel):
    """Processing status for a document."""

    doc_id: str = Field(..., description="Document ID")
    status: Literal["queued", "processing", "completed", "failed"] = Field(
        ...,
        description="Processing status"
    )
    progress: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Processing progress (0-1)"
    )
    pages_processed: Optional[int] = Field(None, description="Number of pages processed")
    total_pages: Optional[int] = Field(None, description="Total pages in document")
    error: Optional[str] = Field(None, description="Error message if failed")
    started_at: Optional[datetime] = Field(None, description="Processing start time")
    completed_at: Optional[datetime] = Field(None, description="Processing completion time")

    class Config:
        json_schema_extra = {
            "example": {
                "doc_id": "doc_abc123",
                "status": "processing",
                "progress": 0.6,
                "pages_processed": 6,
                "total_pages": 10,
                "error": None,
                "started_at": "2024-01-15T10:30:00Z",
                "completed_at": None
            }
        }


# ============================================================================
# Status Models
# ============================================================================

class ComponentHealth(BaseModel):
    """Health status for a system component."""

    name: str = Field(..., description="Component name")
    status: Literal["healthy", "unhealthy", "degraded"] = Field(
        ...,
        description="Health status"
    )
    message: Optional[str] = Field(None, description="Status message")
    latency_ms: Optional[float] = Field(None, description="Response latency in milliseconds")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "chromadb",
                "status": "healthy",
                "message": "Connected and responsive",
                "latency_ms": 5.2
            }
        }


class SystemStats(BaseModel):
    """System statistics."""

    total_documents: int = Field(default=0, description="Total indexed documents")
    total_pages: int = Field(default=0, description="Total indexed pages")
    total_text_chunks: int = Field(default=0, description="Total indexed text chunks")
    index_size_mb: float = Field(default=0.0, description="Index size in megabytes")

    class Config:
        json_schema_extra = {
            "example": {
                "total_documents": 42,
                "total_pages": 523,
                "total_text_chunks": 1847,
                "index_size_mb": 128.5
            }
        }


class StatusResponse(BaseModel):
    """Response model for system status."""

    system_status: Literal["healthy", "degraded", "unhealthy"] = Field(
        ...,
        description="Overall system status"
    )
    components: List[ComponentHealth] = Field(..., description="Component health status")
    stats: SystemStats = Field(..., description="System statistics")
    uptime_seconds: float = Field(..., description="System uptime in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "system_status": "healthy",
                "components": [],
                "stats": {},
                "uptime_seconds": 3600.5
            }
        }


class HealthResponse(BaseModel):
    """Simple health check response."""

    status: Literal["ok", "error"] = Field(..., description="Health status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="API version")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "timestamp": "2024-01-15T10:30:00Z",
                "version": "1.0.0"
            }
        }


# ============================================================================
# Error Models
# ============================================================================

class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid search query",
                "detail": "Query must be at least 1 character long"
            }
        }

"""
DocuSearch API - REST API for document search and management.

This module provides FastAPI endpoints for:
- Document upload and processing
- Semantic search
- System status and health checks
"""

from .models import HealthResponse, SearchRequest, SearchResponse, StatusResponse, UploadResponse
from .server import app, create_app

__all__ = [
    "app",
    "create_app",
    "SearchRequest",
    "SearchResponse",
    "UploadResponse",
    "StatusResponse",
    "HealthResponse",
]

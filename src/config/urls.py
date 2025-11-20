"""
Centralized URL configuration for DocuSearch backend services.

This module provides a single source of truth for all service URLs and endpoints
across the DocuSearch application. It supports environment variable configuration
and provides convenient properties and methods for building service-specific URLs.

Environment Variables:
    WORKER_URL: Processing worker base URL (default: http://localhost:8002)
    CHROMADB_URL: ChromaDB server URL (default: http://localhost:8001)
    RESEARCH_API_URL: Research API base URL (default: http://localhost:8004)
    COPYPARTY_URL: Copyparty file server URL (default: http://localhost:8000)
    FRONTEND_URL: Frontend application URL (default: http://localhost:42007)

Usage:
    >>> from src.config.urls import get_service_urls
    >>> urls = get_service_urls()
    >>> search_url = urls.worker_search
    >>> image_url = urls.document_image_url("abc123", "page-5.png")

Thread Safety:
    This module uses a singleton pattern with thread-local storage to ensure
    thread-safe access to URL configuration.
"""

import logging
import os
from typing import Optional
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class ServiceURLs:
    """
    Centralized configuration for all service URLs and endpoints.

    This class provides properties for common endpoints and methods for building
    dynamic URLs with document-specific paths.

    Attributes:
        worker: Processing worker base URL
        chromadb: ChromaDB server base URL
        research_api: Research API base URL
        copyparty: Copyparty file server base URL
        frontend: Frontend application base URL
    """

    def __init__(self) -> None:
        """Initialize service URLs from environment variables."""
        # Service base URLs
        self.worker = os.getenv("WORKER_URL", "http://localhost:8002")
        self.chromadb = os.getenv("CHROMADB_URL", "http://localhost:8001")
        self.research_api = os.getenv("RESEARCH_API_URL", "http://localhost:8004")
        self.copyparty = os.getenv("COPYPARTY_URL", "http://localhost:8000")
        self.frontend = os.getenv("FRONTEND_URL", "http://localhost:42007")

        # Log configuration on initialization
        logger.debug(
            f"Initialized ServiceURLs: worker={self.worker}, "
            f"chromadb={self.chromadb}, research_api={self.research_api}, "
            f"copyparty={self.copyparty}, frontend={self.frontend}"
        )

    # =========================================================================
    # Worker Service Endpoints
    # =========================================================================

    @property
    def worker_search(self) -> str:
        """Worker search endpoint URL."""
        return urljoin(self.worker, "/search")

    @property
    def worker_status(self) -> str:
        """Worker status endpoint URL."""
        return urljoin(self.worker, "/status")

    @property
    def worker_health(self) -> str:
        """Worker health check endpoint URL."""
        return urljoin(self.worker, "/health")

    @property
    def worker_documents(self) -> str:
        """Worker documents endpoint URL."""
        return urljoin(self.worker, "/documents")

    @property
    def worker_document_structure(self) -> str:
        """Worker document structure endpoint URL."""
        return urljoin(self.worker, "/document-structure")

    # =========================================================================
    # ChromaDB Endpoints
    # =========================================================================

    @property
    def chromadb_heartbeat(self) -> str:
        """ChromaDB heartbeat endpoint URL."""
        return urljoin(self.chromadb, "/api/v1/heartbeat")

    @property
    def chromadb_collections(self) -> str:
        """ChromaDB collections endpoint URL."""
        return urljoin(self.chromadb, "/api/v1/collections")

    # =========================================================================
    # Research API Endpoints
    # =========================================================================

    @property
    def research_ask(self) -> str:
        """Research API ask endpoint URL."""
        return urljoin(self.research_api, "/api/research/ask")

    @property
    def research_health(self) -> str:
        """Research API health check endpoint URL."""
        return urljoin(self.research_api, "/api/health")

    @property
    def research_status(self) -> str:
        """Research API status endpoint URL."""
        return urljoin(self.research_api, "/api/status")

    # =========================================================================
    # Copyparty File Server Methods
    # =========================================================================

    def document_image_url(self, doc_id: str, image_filename: str, absolute: bool = True) -> str:
        """
        Build URL for a document image (page/chunk image).

        Args:
            doc_id: Document ID (SHA-256 hash)
            image_filename: Image filename (e.g., "page-5.png", "chunk-42.png")
            absolute: If True, return absolute URL; if False, return relative path

        Returns:
            URL to document image on Copyparty file server

        Example:
            >>> urls = ServiceURLs()
            >>> urls.document_image_url("abc123", "page-5.png")
            'http://localhost:8000/uploads/abc123/images/page-5.png'
        """
        path = f"/uploads/{doc_id}/images/{image_filename}"
        if absolute:
            return urljoin(self.copyparty, path)
        return path

    def document_thumbnail_url(self, doc_id: str, absolute: bool = True) -> str:
        """
        Build URL for a document thumbnail (cover/first page).

        Args:
            doc_id: Document ID (SHA-256 hash)
            absolute: If True, return absolute URL; if False, return relative path

        Returns:
            URL to document thumbnail on Copyparty file server

        Example:
            >>> urls = ServiceURLs()
            >>> urls.document_thumbnail_url("abc123")
            'http://localhost:8000/uploads/abc123/thumbnail.png'
        """
        path = f"/uploads/{doc_id}/thumbnail.png"
        if absolute:
            return urljoin(self.copyparty, path)
        return path

    def cover_art_url(self, doc_id: str, absolute: bool = True) -> str:
        """
        Build URL for audio cover art.

        Args:
            doc_id: Document ID (SHA-256 hash)
            absolute: If True, return absolute URL; if False, return relative path

        Returns:
            URL to cover art on Copyparty file server

        Example:
            >>> urls = ServiceURLs()
            >>> urls.cover_art_url("abc123")
            'http://localhost:8000/uploads/abc123/cover-art.png'
        """
        path = f"/uploads/{doc_id}/cover-art.png"
        if absolute:
            return urljoin(self.copyparty, path)
        return path

    def original_file_url(self, doc_id: str, filename: str, absolute: bool = True) -> str:
        """
        Build URL for original uploaded file.

        Args:
            doc_id: Document ID (SHA-256 hash)
            filename: Original filename
            absolute: If True, return absolute URL; if False, return relative path

        Returns:
            URL to original file on Copyparty file server

        Example:
            >>> urls = ServiceURLs()
            >>> urls.original_file_url("abc123", "document.pdf")
            'http://localhost:8000/uploads/abc123/document.pdf'
        """
        path = f"/uploads/{doc_id}/{filename}"
        if absolute:
            return urljoin(self.copyparty, path)
        return path

    # =========================================================================
    # Frontend URLs
    # =========================================================================

    def frontend_details_url(
        self, doc_id: str, page: Optional[int] = None, chunk_id: Optional[str] = None
    ) -> str:
        """
        Build frontend document details URL with optional navigation parameters.

        Note: For more advanced URL building with relative/absolute control,
        use src.utils.url_builder.build_details_url() directly.

        Args:
            doc_id: Document ID (SHA-256 hash)
            page: Optional page number (1-indexed, for visual documents)
            chunk_id: Optional chunk ID for navigation

        Returns:
            Absolute URL to document details page in frontend

        Example:
            >>> urls = ServiceURLs()
            >>> urls.frontend_details_url("abc123", page=5)
            'http://localhost:3000/details/abc123?page=5'
        """
        from src.utils.url_builder import build_details_url

        return build_details_url(doc_id=doc_id, page=page, chunk_id=chunk_id, absolute=True)


# =============================================================================
# Singleton Pattern with Thread-Local Storage
# =============================================================================

import threading

_thread_local = threading.local()


def get_service_urls() -> ServiceURLs:
    """
    Get the singleton ServiceURLs instance for the current thread.

    This function implements a thread-safe singleton pattern, ensuring that
    each thread gets its own ServiceURLs instance while avoiding race conditions
    in multi-threaded environments.

    Returns:
        ServiceURLs instance for the current thread

    Example:
        >>> from src.config.urls import get_service_urls
        >>> urls = get_service_urls()
        >>> search_url = urls.worker_search
    """
    if not hasattr(_thread_local, "service_urls"):
        _thread_local.service_urls = ServiceURLs()
        logger.debug("Created new ServiceURLs instance for thread")
    # Type assertion for mypy - we just created it above if it didn't exist
    result: ServiceURLs = _thread_local.service_urls
    return result


def reset_service_urls() -> None:
    """
    Reset the ServiceURLs singleton for the current thread.

    Useful for testing or when environment variables change at runtime.

    Example:
        >>> import os
        >>> os.environ["WORKER_URL"] = "http://newworker:8002"
        >>> reset_service_urls()
        >>> urls = get_service_urls()  # Will use new WORKER_URL
    """
    if hasattr(_thread_local, "service_urls"):
        delattr(_thread_local, "service_urls")
        logger.debug("Reset ServiceURLs instance for thread")

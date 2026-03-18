"""
Centralized URL configuration for DocuSearch backend services.

This module provides a single source of truth for all service URLs and endpoints
across the DocuSearch application. It supports environment variable configuration
and provides convenient properties and methods for building service-specific URLs.

Environment Variables:
    WORKER_URL: Processing worker base URL (default: http://localhost:8002)
    RESEARCH_API_URL: Research API base URL (default: http://localhost:8004)
    FRONTEND_URL: Frontend application URL (default: http://localhost:3333)

Usage:
    >>> from src.config.urls import get_service_urls
    >>> urls = get_service_urls()
    >>> search_url = urls.worker_search

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
        research_api: Research API base URL
        frontend: Frontend application base URL
    """

    def __init__(self) -> None:
        """Initialize service URLs from environment variables."""
        # Service base URLs
        self.worker = os.getenv("WORKER_URL", "http://localhost:8002")
        self.research_api = os.getenv("RESEARCH_API_URL", "http://localhost:8004")
        self.frontend = os.getenv("FRONTEND_URL", "http://localhost:3333")

        # Log configuration on initialization
        logger.debug(
            f"Initialized ServiceURLs: worker={self.worker}, "
            f"research_api={self.research_api}, frontend={self.frontend}"
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
            'http://localhost:3333/details/abc123?page=5'
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

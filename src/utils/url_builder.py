"""
Centralized URL builder for DocuSearch application.

Provides single source of truth for building frontend URLs from backend services.
Used by: Research API, MCP Server, and future integrations.

All URL building logic for document detail pages should use this module to ensure
consistency across MCP integrations, API responses, webhooks, and other services.
"""

import logging
import os
from typing import Optional
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

# Configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


def build_details_url(
    doc_id: str,
    page: Optional[int] = None,
    chunk_id: Optional[str] = None,
    absolute: bool = True,
) -> str:
    """
    Build document details URL with optional navigation parameters.

    This is the single source of truth for constructing document detail URLs
    across all backend services (Research API, MCP Server, webhooks, etc.).

    Args:
        doc_id: Document identifier (SHA-256 hash format)
        page: Optional page number (1-indexed, for visual documents)
        chunk_id: Optional chunk ID for text navigation (format: "{doc_id}-chunk{NNNN}")
        absolute: If True, return absolute URL; if False, return relative path

    Returns:
        URL to document detail view with optional navigation params

    Examples:
        >>> # Absolute URL for external tools (MCP, emails, webhooks)
        >>> build_details_url("abc123", absolute=True)
        'http://localhost:3000/details/abc123'

        >>> # With page navigation (visual documents)
        >>> build_details_url("abc123", page=5, absolute=True)
        'http://localhost:3000/details/abc123?page=5'

        >>> # With chunk navigation (text documents)
        >>> build_details_url("abc123", chunk_id="abc123-chunk0042", absolute=True)
        'http://localhost:3000/details/abc123?chunk=abc123-chunk0042'

        >>> # With both page and chunk (visual documents with chunk highlighting)
        >>> build_details_url("abc123", page=5, chunk_id="abc123-page5", absolute=True)
        'http://localhost:3000/details/abc123?page=5&chunk=abc123-page5'

        >>> # Relative URL for API responses (frontend resolves to current origin)
        >>> build_details_url("abc123", page=5, absolute=False)
        '/details/abc123?page=5'

    Note:
        - MCP Server should use absolute=True (external tools need full URLs)
        - Research API should use absolute=False (web frontend handles relative URLs)
        - Frontend URL is configurable via FRONTEND_URL environment variable
        - Empty or whitespace-only chunk_id values are ignored
    """
    if not doc_id:
        raise ValueError("doc_id is required")

    # Build base path
    path = f"/details/{doc_id}"

    # Build query parameters
    params = {}
    if page is not None:
        if not isinstance(page, int) or page < 1:
            logger.warning(f"Invalid page number: {page}. Must be positive integer.")
        else:
            params["page"] = str(page)

    if chunk_id is not None and isinstance(chunk_id, str) and chunk_id.strip():
        params["chunk"] = chunk_id.strip()

    # Construct URL with query string
    if params:
        query_string = urlencode(params)
        path = f"{path}?{query_string}"

    # Return absolute or relative
    if absolute:
        return f"{FRONTEND_URL}{path}"
    else:
        return path


def add_details_url_to_source(source_dict: dict, absolute: bool = True) -> dict:
    """
    Add details_url field to source dictionary.

    Convenience function for adding URLs to source objects in API responses.

    Args:
        source_dict: Source dictionary with doc_id, page, chunk_id fields
        absolute: Whether to use absolute URLs (default: True)

    Returns:
        Source dictionary with added details_url field (mutates original dict)

    Example:
        >>> source = {"doc_id": "abc123", "page": 5, "chunk_id": "abc123-chunk0042"}
        >>> add_details_url_to_source(source)
        {
            "doc_id": "abc123",
            "page": 5,
            "chunk_id": "abc123-chunk0042",
            "details_url": "http://localhost:3000/details/abc123?page=5&chunk=abc123-chunk0042"
        }

    Note:
        This function modifies the input dictionary in place.
    """
    source_dict["details_url"] = build_details_url(
        doc_id=source_dict["doc_id"],
        page=source_dict.get("page"),
        chunk_id=source_dict.get("chunk_id"),
        absolute=absolute,
    )
    return source_dict

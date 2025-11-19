"""
Utility functions for DocuSearch MCP Server.

Provides image fetching, link building, and error handling utilities.
"""

import base64
import logging
from typing import Dict, List, Optional

import httpx

from tkr_docusearch.utils.url_builder import build_details_url

logger = logging.getLogger(__name__)


async def fetch_image_as_base64(image_url: str, timeout: float = 10.0) -> Optional[str]:
    """
    Fetch image from URL and convert to base64.

    Args:
        image_url: HTTPS URL to image (via ngrok)
        timeout: Request timeout in seconds

    Returns:
        Base64-encoded image data, or None if fetch fails

    Note:
        Images must be accessible via HTTPS for Claude Desktop.
        Uses ngrok URLs like: https://abc123.ngrok-free.dev/images/doc_id/page.jpg
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(image_url)
            response.raise_for_status()

            # Convert to base64
            image_data = base64.b64encode(response.content).decode("utf-8")

            logger.debug(
                f"Image fetched successfully: {image_url} "
                f"({len(response.content)} bytes, {len(image_data)} base64)"
            )

            return image_data

    except httpx.TimeoutException:
        logger.warning(f"Image fetch timeout ({timeout}s): {image_url}")
        return None
    except httpx.HTTPStatusError as e:
        logger.warning(f"Image fetch HTTP error {e.response.status_code}: {image_url}")
        return None
    except Exception as e:
        logger.error(f"Image fetch failed for {image_url}: {e}")
        return None


def get_mime_type(image_url: str) -> str:
    """
    Determine MIME type from image URL.

    Args:
        image_url: URL to image file

    Returns:
        MIME type string (e.g., "image/png", "image/jpeg")

    Note:
        Defaults to "image/png" if extension cannot be determined.
    """
    ext = image_url.lower().split(".")[-1]

    mime_types = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "webp": "image/webp",
    }

    return mime_types.get(ext, "image/png")


def build_document_link(doc_id: str, chunk_id: Optional[str] = None) -> str:
    """
    Build frontend URL for document detail view.

    DEPRECATED: This function now delegates to centralized URL builder.
    Use src.utils.url_builder.build_details_url() directly for new code.

    Args:
        doc_id: Document ID (SHA-256 hash)
        chunk_id: Optional chunk ID for text sources (format: "{doc_id}-chunk{NNNN}")

    Returns:
        URL to document detail view with optional chunk navigation

    Examples:
        >>> build_document_link("abc123")
        'http://localhost:3000/details/abc123'

        >>> build_document_link("abc123", "abc123-chunk0012")
        'http://localhost:3000/details/abc123?chunk=abc123-chunk0012'
    """
    # Delegate to centralized URL builder
    return build_details_url(
        doc_id=doc_id,
        chunk_id=chunk_id,
        absolute=True,  # MCP server needs absolute URLs for external tools
    )


def format_source_links(sources: List[Dict]) -> str:
    """
    Format source list as text with clickable links.

    Args:
        sources: List of source dictionaries from context-only endpoint

    Returns:
        Formatted text with source links

    Example output:
        SOURCE LINKS:

        [1] [Visual Match] Q3-Report.pdf (Page 8)
            http://localhost:3000/details/abc123
            Relevance: 92%

        [2] Sales-Analysis.pdf (Page 2)
            http://localhost:3000/details/def456?chunk=def456-chunk0008
            Relevance: 78%
    """
    lines = ["", "", "---", "", "SOURCE LINKS:", ""]

    for source in sources:
        # Visual match indicator
        visual_tag = "[Visual Match] " if source.get("is_visual") else ""

        # Build link
        link = build_document_link(source["doc_id"], source.get("chunk_id"))

        # Format entry
        lines.append(f"[{source['id']}] {visual_tag}{source['filename']} (Page {source['page']})")
        lines.append(f"    {link}")
        lines.append(f"    Relevance: {source['relevance_score']:.0%}")
        lines.append("")

    return "\n".join(lines)


def format_error_message(error_type: str, detail: str) -> str:
    """
    Format user-friendly error message.

    Args:
        error_type: Type of error (e.g., "connection", "not_found", "server_error")
        detail: Detailed error message

    Returns:
        Formatted error message for user

    Examples:
        >>> format_error_message("connection", "Failed to connect to localhost:8004")
        "DocuSearch API is unavailable. Please ensure DocuSearch is running:\\n  ./scripts/start-all.sh\\n\\nError: Failed to connect to localhost:8004"
    """
    error_messages = {
        "connection": (
            "DocuSearch API is unavailable. Please ensure DocuSearch is running:\n"
            "  ./scripts/start-all.sh\n\n"
            f"Error: {detail}"
        ),
        "not_found": (
            "No relevant documents found for your query.\n\n"
            "Try:\n"
            "- Rephrasing your question\n"
            "- Uploading more documents\n"
            "- Using different search keywords"
        ),
        "server_error": (
            "DocuSearch encountered an internal error.\n\n"
            "Please check the logs:\n"
            "  tail logs/research-api.log\n\n"
            f"Error: {detail}"
        ),
        "invalid_query": (
            "Invalid query. Please provide a meaningful search question (3+ characters)."
        ),
    }

    return error_messages.get(error_type, f"Error: {detail}")

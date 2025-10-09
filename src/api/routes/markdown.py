"""
Markdown download API endpoint.

Provides endpoint for downloading processed documents as markdown files.
"""

import logging
import re
from pathlib import Path
from typing import Optional

import numpy as np
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)

# Router instance
router = APIRouter(prefix="/api/document", tags=["markdown"])

# doc_id validation patterns
# SHA-256 format (64-char lowercase hex) - per contract specification
SHA256_PATTERN = re.compile(r'^[a-f0-9]{64}$')
# UUID format (for backward compatibility with existing documents)
UUID_PATTERN = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')

# Global storage client (set by server.py during startup)
_storage_client = None


def set_storage_client(storage_client):
    """Set the storage client for the router (called from server.py)."""
    global _storage_client
    _storage_client = storage_client


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe download.

    Args:
        filename: Original filename (may include path, extension)

    Returns:
        Sanitized filename (base name only)
    """
    # Get base name (remove path, extension)
    base_name = Path(filename).stem

    # Remove control characters and reserved chars
    sanitized = re.sub(r'[\x00-\x1F<>:"|?*\\/]', '', base_name)

    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip('. ')

    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:200]

    # Fallback if empty
    if not sanitized:
        sanitized = "document"

    return sanitized


@router.get("/{doc_id}/markdown")
async def download_markdown(doc_id: str):
    """
    Download document as markdown file.

    Args:
        doc_id: Document SHA-256 hash (64 hex characters)

    Returns:
        FileResponse: Markdown file with download headers

    Raises:
        HTTPException(400): Invalid doc_id format
        HTTPException(404): Document not found
        HTTPException(404): Markdown not available
        HTTPException(404): Markdown file missing
        HTTPException(500): Internal server error
    """
    # Step 1: Validate doc_id format (support both SHA-256 and UUID for compatibility)
    if not (SHA256_PATTERN.match(doc_id) or UUID_PATTERN.match(doc_id)):
        logger.warning(f"Invalid doc_id format: {doc_id}")
        raise HTTPException(
            status_code=400,
            detail="Invalid doc_id format"
        )

    # Check storage client is initialized
    if _storage_client is None:
        logger.error("Storage client not initialized")
        raise HTTPException(
            status_code=503,
            detail="Storage service not available"
        )

    try:
        # Step 2: Query ChromaDB visual collection for metadata (page 1)
        logger.info(f"Querying markdown metadata for doc_id: {doc_id}")

        visual_results = _storage_client.search_visual(
            query_embedding=np.zeros(128),  # Dummy embedding for metadata query
            n_results=1,
            filters={"doc_id": doc_id, "page": 1}
        )

        # Step 3: Check if document found
        if not visual_results:
            logger.warning(f"Document not found: {doc_id}")
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

        # Get metadata
        metadata = visual_results[0]["metadata"]

        # Step 4: Check has_markdown flag and markdown_path
        has_markdown = metadata.get("has_markdown", False)
        markdown_path = metadata.get("markdown_path")

        if not has_markdown or not markdown_path:
            logger.warning(f"Markdown not available for doc_id: {doc_id}")
            raise HTTPException(
                status_code=404,
                detail="Markdown not available for this document"
            )

        # Step 5: Verify file exists on disk
        path = Path(markdown_path)
        if not path.exists():
            logger.error(f"Markdown file missing: {markdown_path} for doc_id: {doc_id}")
            raise HTTPException(
                status_code=404,
                detail="Markdown file missing"
            )

        # Step 6: Get and sanitize filename
        original_filename = metadata.get("filename", "document")
        base_name = sanitize_filename(original_filename)
        download_filename = f"{base_name}.md"

        # Step 7: Return FileResponse
        logger.info(f"Downloaded markdown: {doc_id} -> {download_filename}")

        return FileResponse(
            path=str(path),
            media_type="text/markdown",
            filename=download_filename,
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"'
            }
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log and return 500 for unexpected errors
        logger.error(f"Download failed for doc_id: {doc_id}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

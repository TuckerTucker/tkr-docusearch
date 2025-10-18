"""
Chunk ID extraction utilities for research context.

Handles extraction and transformation of chunk_id from ChromaDB metadata
for bidirectional highlighting in the research interface.
"""

import re
from typing import Any, Dict, Optional

import structlog

logger = structlog.get_logger(__name__)


def extract_chunk_id(metadata: Dict[str, Any], doc_id: str) -> Optional[str]:
    """
    Extract and transform chunk_id from search result metadata.

    Args:
        metadata: ChromaDB metadata from search result
        doc_id: Document identifier

    Returns:
        Transformed chunk_id in format "{doc_id}-chunk{NNNN}", or None

    Behavior:
        - Text results: metadata["chunk_id"] exists (int like 0, 45, etc.)
          Transform to: "{doc_id}-chunk{chunk_id:04d}"
          Example: chunk_id=45 → "abc123-chunk0045"

        - Visual results: no chunk_id field
          Return: None

    Note:
        ChromaDB stores chunk_id as integer. We transform to string format
        matching the embedding ID format used in storage layer.
    """
    # Check if chunk_id exists in metadata
    if "chunk_id" not in metadata:
        # Visual result - no chunk_id
        logger.debug("No chunk_id in metadata (visual result)", doc_id=doc_id)
        return None

    try:
        # Get chunk_id value
        chunk_id_value = metadata["chunk_id"]

        # Handle both int and string representations
        if isinstance(chunk_id_value, int):
            chunk_num = chunk_id_value
        elif isinstance(chunk_id_value, str):
            # Try to parse as integer
            chunk_num = int(chunk_id_value)
        else:
            logger.warning(
                "Unexpected chunk_id type",
                doc_id=doc_id,
                chunk_id_type=type(chunk_id_value).__name__,
            )
            return None

        # Format as "{doc_id}-chunk{NNNN}"
        formatted_chunk_id = f"{doc_id}-chunk{chunk_num:04d}"

        logger.debug(
            "Extracted chunk_id",
            doc_id=doc_id,
            chunk_num=chunk_num,
            formatted=formatted_chunk_id,
        )

        return formatted_chunk_id

    except (ValueError, TypeError) as e:
        logger.warning(
            "Failed to parse chunk_id",
            doc_id=doc_id,
            chunk_id_value=metadata.get("chunk_id"),
            error=str(e),
        )
        return None


def parse_chunk_id(chunk_id_str: str) -> Optional[Dict[str, Any]]:
    """
    Parse chunk_id string into components.

    Args:
        chunk_id_str: Chunk ID string like "abc123-chunk0045"

    Returns:
        Dict with "doc_id" and "chunk_num" keys, or None if invalid

    Example:
        >>> parse_chunk_id("abc123-chunk0045")
        {"doc_id": "abc123", "chunk_num": 45}
    """
    if not chunk_id_str:
        return None

    # Match pattern: {doc_id}-chunk{NNNN}
    pattern = r"^(.+)-chunk(\d{4})$"
    match = re.match(pattern, chunk_id_str)

    if not match:
        logger.warning("Invalid chunk_id format", chunk_id=chunk_id_str)
        return None

    doc_id = match.group(1)
    chunk_num = int(match.group(2))

    return {"doc_id": doc_id, "chunk_num": chunk_num}

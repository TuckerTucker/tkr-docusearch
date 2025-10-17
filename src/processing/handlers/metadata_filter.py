"""
Metadata filter for ChromaDB storage.

This module filters document metadata to remove large/problematic fields,
extracted from DocumentProcessor for reduced complexity.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class MetadataFilter:
    """Filter for preparing metadata for ChromaDB storage."""

    # Fields to exclude from ChromaDB metadata
    EXCLUDED_FIELDS = {
        "full_markdown",  # Too large (hundreds of KB)
        "structure",  # Complex nested structure
        "full_markdown_compressed",  # Binary data
        "markdown_error",  # Can be large
        "_album_art_data",  # Binary data (temporary)
        "_album_art_mime",  # Associated with binary data
    }

    # Maximum size for string/bytes values
    MAX_VALUE_SIZE = 1000

    @staticmethod
    def filter_metadata(doc_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter metadata to remove large/problematic fields.

        ChromaDB metadata values must be simple types and not too large.

        Args:
            doc_metadata: Original document metadata

        Returns:
            Filtered metadata safe for ChromaDB storage
        """
        filtered_keys = []
        safe_doc_metadata = {}

        for k, v in doc_metadata.items():
            # Always exclude known large/problematic fields
            if k in MetadataFilter.EXCLUDED_FIELDS:
                filtered_keys.append(f"{k} (excluded field)")
                continue

            # Skip very large string values or binary data
            if isinstance(v, (str, bytes)) and len(v) > MetadataFilter.MAX_VALUE_SIZE:
                filtered_keys.append(f"{k} ({len(v)} chars/bytes, too large)")
                continue

            safe_doc_metadata[k] = v

        if filtered_keys:
            logger.info(f"Filtered metadata fields: {', '.join(filtered_keys)}")

        return safe_doc_metadata

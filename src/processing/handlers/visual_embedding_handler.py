"""
Visual embedding handler for storing page embeddings.

This module handles visual embedding storage operations,
extracted from DocumentProcessor for reduced complexity.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class VisualEmbeddingHandler:
    """Handler for storing visual embeddings."""

    def __init__(self, storage_client, enhanced_mode_config=None):
        """
        Initialize handler.

        Args:
            storage_client: Storage client for ChromaDB
            enhanced_mode_config: Optional enhanced mode configuration
        """
        self.storage_client = storage_client
        self.enhanced_mode_config = enhanced_mode_config

    def store_visual_embeddings(
        self,
        visual_results: List,
        filename: str,
        file_path: str,
        safe_doc_metadata: Dict[str, Any],
        structure: Optional[Any] = None,
        pages: Optional[List] = None,
    ) -> tuple:
        """
        Store visual embeddings in ChromaDB.

        Args:
            visual_results: List of VisualEmbeddingResult
            filename: Original filename
            file_path: Source file path
            safe_doc_metadata: Filtered document metadata
            structure: Optional document structure (enhanced mode)
            pages: Optional list of Page objects (for image paths)

        Returns:
            Tuple of (visual_ids, total_size_bytes)
        """
        visual_ids = []
        total_size_bytes = 0

        # Create page lookup for image paths
        page_lookup = {}
        if pages:
            page_lookup = {page.page_num: page for page in pages}

        # Store each visual embedding
        for result in visual_results:
            base_metadata = {
                "filename": filename,
                "page": result.page_num,
                "source_path": file_path,
                **safe_doc_metadata,
            }

            # Prepare enhanced metadata if available
            metadata = self._prepare_metadata(base_metadata, structure)

            # Get image paths from page if available
            image_path, thumb_path = self._get_image_paths(result.page_num, page_lookup)

            # Store embedding
            embedding_id = self.storage_client.add_visual_embedding(
                doc_id=result.doc_id,
                page=result.page_num,
                full_embeddings=result.embedding,
                metadata=metadata,
                image_path=image_path,
                thumb_path=thumb_path,
            )
            visual_ids.append(embedding_id)

            # Estimate size
            total_size_bytes += result.embedding.nbytes

        logger.debug(f"Stored {len(visual_ids)} visual embeddings")
        return visual_ids, total_size_bytes

    def _prepare_metadata(
        self, base_metadata: Dict[str, Any], structure: Optional[Any]
    ) -> Dict[str, Any]:
        """Prepare enhanced metadata if available."""
        if hasattr(self.storage_client, "_prepare_enhanced_visual_metadata") and structure:
            return self.storage_client._prepare_enhanced_visual_metadata(base_metadata, structure)
        return base_metadata

    def _get_image_paths(self, page_num: int, page_lookup: Dict) -> tuple:
        """Get image paths from page lookup."""
        image_path = None
        thumb_path = None

        if page_num in page_lookup:
            page = page_lookup[page_num]
            image_path = page.image_path
            thumb_path = page.thumb_path

        return image_path, thumb_path

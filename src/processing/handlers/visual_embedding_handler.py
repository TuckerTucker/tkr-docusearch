"""
Visual embedding handler for storing page embeddings.

This module handles visual embedding storage operations,
extracted from DocumentProcessor for reduced complexity.
"""

import logging
from typing import Any, Dict, List, Optional

from .enhanced_metadata import prepare_enhanced_visual_metadata

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

            # Get image dimensions from page if available
            image_width, image_height = self._get_image_dimensions(result.page_num, page_lookup)

            # Prepare enhanced metadata if available
            metadata = self._prepare_metadata(base_metadata, structure, image_width, image_height)

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
        self,
        base_metadata: Dict[str, Any],
        structure: Optional[Any],
        image_width: Optional[int] = None,
        image_height: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Prepare enhanced metadata if available.

        Args:
            base_metadata: Base metadata dictionary
            structure: Optional DocumentStructure from Docling
            image_width: Original image width in pixels
            image_height: Original image height in pixels

        Returns:
            Enhanced metadata if structure provided, else base metadata
        """
        # If enhanced mode is enabled and structure is available, use enhanced metadata
        if self.enhanced_mode_config and structure:
            try:
                return prepare_enhanced_visual_metadata(
                    base_metadata, structure, image_width, image_height
                )
            except Exception as e:
                logger.warning(f"Failed to prepare enhanced metadata: {e}, falling back to base")
                return base_metadata

        # Otherwise, return base metadata
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

    def _get_image_dimensions(self, page_num: int, page_lookup: Dict) -> tuple:
        """
        Get image dimensions from page lookup.

        Args:
            page_num: Page number to look up
            page_lookup: Dictionary mapping page numbers to Page objects

        Returns:
            Tuple of (width, height) or (None, None) if not available
        """
        if page_num in page_lookup:
            page = page_lookup[page_num]
            # Try to get dimensions from page object
            if hasattr(page, "width") and hasattr(page, "height"):
                return page.width, page.height
            # Try image_width/image_height attributes
            if hasattr(page, "image_width") and hasattr(page, "image_height"):
                return page.image_width, page.image_height

        return None, None

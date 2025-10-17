"""
Text embedding handler for storing chunk embeddings.

This module handles text embedding storage operations,
extracted from DocumentProcessor for reduced complexity.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TextEmbeddingHandler:
    """Handler for storing text embeddings."""

    def __init__(self, storage_client, enhanced_mode_config=None):
        """
        Initialize handler.

        Args:
            storage_client: Storage client for ChromaDB
            enhanced_mode_config: Optional enhanced mode configuration
        """
        self.storage_client = storage_client
        self.enhanced_mode_config = enhanced_mode_config

    def store_text_embeddings(
        self,
        text_results: List,
        text_chunks: List,
        filename: str,
        file_path: str,
        safe_doc_metadata: Dict[str, Any],
    ) -> tuple:
        """
        Store text embeddings in ChromaDB.

        Args:
            text_results: List of TextEmbeddingResult
            text_chunks: List of TextChunk (with context and timestamps)
            filename: Original filename
            file_path: Source file path
            safe_doc_metadata: Filtered document metadata

        Returns:
            Tuple of (text_ids, total_size_bytes)
        """
        text_ids = []
        total_size_bytes = 0

        # Create chunk lookup by chunk_id for context
        chunk_lookup = {chunk.chunk_id: chunk for chunk in text_chunks}

        # Store each text embedding
        for result in text_results:
            # Get chunk for context and timestamps
            chunk = chunk_lookup.get(result.chunk_id)

            # Build base metadata
            base_metadata = self._build_base_metadata(
                result, filename, file_path, safe_doc_metadata, chunk
            )

            # Get chunk context if available
            chunk_context = self._get_chunk_context(chunk)

            # Prepare enhanced metadata if available
            metadata = self._prepare_metadata(base_metadata, chunk_context)

            # Store embedding
            embedding_id = self.storage_client.add_text_embedding(
                doc_id=result.doc_id,
                chunk_id=int(result.chunk_id.split("-chunk")[-1]),
                full_embeddings=result.embedding,
                metadata=metadata,
            )
            text_ids.append(embedding_id)

            # Estimate size
            total_size_bytes += result.embedding.nbytes

        logger.debug(f"Stored {len(text_ids)} text embeddings")
        return text_ids, total_size_bytes

    def _build_base_metadata(
        self,
        result,
        filename: str,
        file_path: str,
        safe_doc_metadata: Dict[str, Any],
        chunk: Optional[Any],
    ) -> Dict[str, Any]:
        """Build base metadata for text embedding."""
        base_metadata = {
            "filename": filename,
            "chunk_id": result.chunk_id,
            "page": result.page_num,
            "text_preview": result.text[:200],
            "full_text": result.text,  # Store complete chunk text
            "word_count": len(result.text.split()),
            "source_path": file_path,
            **safe_doc_metadata,
        }

        # Add timestamp fields if chunk has timestamps
        # Only add if not None - ChromaDB doesn't accept None values
        if chunk:
            if chunk.start_time is not None:
                base_metadata["start_time"] = chunk.start_time
            if chunk.end_time is not None:
                base_metadata["end_time"] = chunk.end_time
            base_metadata["has_timestamps"] = chunk.start_time is not None

        return base_metadata

    def _get_chunk_context(self, chunk: Optional[Any]) -> Optional[Any]:
        """Get chunk context if available."""
        if chunk and chunk.context:
            return chunk.context
        return None

    def _prepare_metadata(
        self, base_metadata: Dict[str, Any], chunk_context: Optional[Any]
    ) -> Dict[str, Any]:
        """Prepare enhanced metadata if available."""
        if hasattr(self.storage_client, "_prepare_enhanced_text_metadata") and chunk_context:
            return self.storage_client._prepare_enhanced_text_metadata(base_metadata, chunk_context)
        return base_metadata

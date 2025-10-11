"""
ChromaDB client with multi-vector storage support.

This module provides a ChromaDB client wrapper that implements the storage
interface contract for DocuSearch MVP. It supports multi-vector embeddings
with CLS token-based indexing and compressed full sequence storage.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

import numpy as np
import chromadb
from chromadb.config import Settings
from chromadb.api.models.Collection import Collection

from .compression import (
    compress_embeddings,
    decompress_embeddings,
    compress_structure_metadata,
    compress_markdown,
    decompress_markdown,
    CorruptedDataError,
)
from .metadata_schema import DocumentStructure, ChunkContext

# Configure logging
logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Base exception for storage operations."""
    pass


class ChromaDBConnectionError(StorageError):
    """Cannot connect to ChromaDB server."""
    pass


class EmbeddingValidationError(StorageError):
    """Invalid embedding shape or dtype."""
    pass


class MetadataCompressionError(StorageError):
    """Failed to compress or decompress embeddings."""
    pass


class DocumentNotFoundError(StorageError):
    """Document ID not found in collections."""
    pass


class ChromaClient:
    """ChromaDB client wrapper with multi-vector storage support.

    This client manages two collections:
    - visual_collection: Page-level visual embeddings
    - text_collection: Chunk-level text embeddings

    Each embedding is stored with:
    - Representative vector (CLS token) in embedding field for fast search
    - Full multi-vector sequence (compressed) in metadata for re-ranking
    """

    def __init__(
        self,
        host: str = "chromadb",
        port: int = 8000,
        visual_collection: str = "visual_collection",
        text_collection: str = "text_collection"
    ):
        """Initialize ChromaDB client and create collections if needed.

        Args:
            host: ChromaDB server host
            port: ChromaDB server port
            visual_collection: Name of visual embeddings collection
            text_collection: Name of text embeddings collection

        Raises:
            ChromaDBConnectionError: If connection to ChromaDB fails
        """
        self.host = host
        self.port = port
        self.visual_collection_name = visual_collection
        self.text_collection_name = text_collection

        # Initialize ChromaDB client
        try:
            self.client = chromadb.HttpClient(
                host=host,
                port=port,
                settings=Settings(
                    allow_reset=False,
                    anonymized_telemetry=False
                )
            )

            # Test connection
            self.client.heartbeat()
            logger.info(f"Connected to ChromaDB at {host}:{port}")

        except Exception as e:
            error_msg = f"Failed to connect to ChromaDB at {host}:{port}: {str(e)}"
            logger.error(error_msg)
            raise ChromaDBConnectionError(error_msg) from e

        # Initialize collections
        self._visual_collection: Collection = self._get_or_create_collection(
            visual_collection,
            metadata={"type": "visual", "description": "Page-level visual embeddings"}
        )
        self._text_collection: Collection = self._get_or_create_collection(
            text_collection,
            metadata={"type": "text", "description": "Chunk-level text embeddings"}
        )

        logger.info(
            f"Collections initialized: {visual_collection}, {text_collection}"
        )

    @property
    def visual_collection(self) -> Collection:
        """Public accessor for visual collection."""
        return self._visual_collection

    @property
    def text_collection(self) -> Collection:
        """Public accessor for text collection."""
        return self._text_collection

    def _get_or_create_collection(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Collection:
        """Get existing collection or create new one.

        Args:
            name: Collection name
            metadata: Optional collection metadata

        Returns:
            ChromaDB Collection object
        """
        try:
            collection = self.client.get_collection(name=name)
            logger.info(f"Retrieved existing collection: {name}")
            return collection
        except Exception:
            # Collection doesn't exist, create it
            logger.info(f"Creating new collection: {name}")
            return self.client.create_collection(
                name=name,
                metadata=metadata or {}
            )

    def _validate_embedding_shape(
        self,
        embeddings: np.ndarray,
        expected_dim: int = 768
    ) -> None:
        """Validate embedding shape and dtype.

        Args:
            embeddings: Embedding array to validate
            expected_dim: Expected embedding dimension (default: 768)

        Raises:
            EmbeddingValidationError: If shape or dtype is invalid
        """
        if not isinstance(embeddings, np.ndarray):
            raise EmbeddingValidationError(
                f"Embeddings must be numpy array, got {type(embeddings)}"
            )

        if len(embeddings.shape) != 2:
            raise EmbeddingValidationError(
                f"Embeddings must be 2D array, got shape {embeddings.shape}"
            )

        seq_length, dim = embeddings.shape

        if seq_length <= 0:
            raise EmbeddingValidationError(
                f"Sequence length must be > 0, got {seq_length}"
            )

        # Support both real ColPali (128) and mock (768) dimensions
        if dim not in [128, 768]:
            raise EmbeddingValidationError(
                f"Embedding dimension must be 128 or 768, got {dim}"
            )

        # Ensure float32 dtype
        if embeddings.dtype not in [np.float32, np.float16, np.float64]:
            raise EmbeddingValidationError(
                f"Embeddings must be float type, got {embeddings.dtype}"
            )

    def _extract_cls_token(self, embeddings: np.ndarray) -> List[float]:
        """Extract CLS token (first token) as representative vector.

        Args:
            embeddings: Full multi-vector sequence, shape (seq_length, 768)

        Returns:
            CLS token as list of floats, shape (768,)
        """
        cls_token = embeddings[0].astype(np.float32)
        return cls_token.tolist()

    def _compress_and_validate(
        self,
        embeddings: np.ndarray,
        max_size_mb: float = 2.0
    ) -> str:
        """Compress embeddings and validate size limits.

        Args:
            embeddings: Embedding array to compress
            max_size_mb: Maximum compressed size in MB (default: 2.0)

        Returns:
            Compressed base64 string

        Raises:
            MetadataCompressionError: If compression fails or exceeds size limit
        """
        try:
            compressed = compress_embeddings(embeddings)

            # Check size limit
            size_bytes = len(compressed.encode('utf-8'))
            size_mb = size_bytes / (1024 * 1024)

            if size_mb > max_size_mb:
                raise MetadataCompressionError(
                    f"Compressed embeddings ({size_mb:.2f}MB) exceed "
                    f"limit of {max_size_mb}MB"
                )

            logger.debug(
                f"Compressed embeddings: {embeddings.shape} -> {size_mb:.2f}MB"
            )

            return compressed

        except Exception as e:
            if isinstance(e, MetadataCompressionError):
                raise
            error_msg = f"Failed to compress embeddings: {str(e)}"
            logger.error(error_msg)
            raise MetadataCompressionError(error_msg) from e

    def add_visual_embedding(
        self,
        doc_id: str,
        page: int,
        full_embeddings: np.ndarray,
        metadata: Dict[str, Any]
    ) -> str:
        """Store visual embedding for a document page.

        Args:
            doc_id: Unique document identifier
            page: Page number (1-indexed)
            full_embeddings: Multi-vector sequence, shape (seq_length, 768)
            metadata: Additional metadata (filename, source_path, etc.)

        Returns:
            Embedding ID: "{doc_id}-page{page:03d}"

        Raises:
            ValueError: If embedding shape is invalid
            ChromaDBError: If storage fails
        """
        # Validate embeddings
        self._validate_embedding_shape(full_embeddings)

        # Generate ID
        embedding_id = f"{doc_id}-page{page:03d}"

        # Extract CLS token for indexing
        cls_token = self._extract_cls_token(full_embeddings)

        # Compress full embeddings for metadata
        compressed_embeddings = self._compress_and_validate(full_embeddings)

        # Compress markdown if present and large
        if "full_markdown" in metadata and metadata.get("markdown_extracted"):
            markdown = metadata["full_markdown"]

            if len(markdown) > 1024:  # 1KB threshold
                try:
                    # Compress and replace
                    compressed = compress_markdown(markdown)
                    metadata["full_markdown_compressed"] = compressed
                    metadata["markdown_compression"] = "gzip+base64"
                    del metadata["full_markdown"]  # Remove uncompressed
                    logger.debug(f"Compressed markdown: {len(markdown)} → {len(compressed)} chars")
                except Exception as e:
                    # Compression failed, log warning and store uncompressed
                    logger.warning(f"Markdown compression failed: {e}, storing uncompressed")
                    metadata["markdown_compression"] = "none"
            else:
                # Small markdown, store uncompressed
                metadata["markdown_compression"] = "none"

        # Build complete metadata
        seq_length, embedding_dim = full_embeddings.shape
        complete_metadata = {
            "doc_id": doc_id,
            "page": page,
            "type": "visual",
            "full_embeddings": compressed_embeddings,
            "seq_length": seq_length,
            "embedding_shape": f"({seq_length}, {embedding_dim})",
            "timestamp": datetime.utcnow().isoformat(),
            **metadata  # Add user-provided metadata
        }

        # Validate required fields
        required_fields = ["filename", "source_path"]
        missing_fields = [f for f in required_fields if f not in complete_metadata]
        if missing_fields:
            raise ValueError(
                f"Missing required metadata fields: {missing_fields}"
            )

        # Store in ChromaDB
        try:
            self._visual_collection.add(
                ids=[embedding_id],
                embeddings=[cls_token],
                metadatas=[complete_metadata]
            )

            logger.info(
                f"Stored visual embedding: {embedding_id} "
                f"(seq_length={seq_length})"
            )

            return embedding_id

        except Exception as e:
            error_msg = f"Failed to store visual embedding {embedding_id}: {str(e)}"
            logger.error(error_msg)
            raise StorageError(error_msg) from e

    def add_text_embedding(
        self,
        doc_id: str,
        chunk_id: int,
        full_embeddings: np.ndarray,
        metadata: Dict[str, Any]
    ) -> str:
        """Store text embedding for a document chunk.

        Args:
            doc_id: Unique document identifier (same as visual)
            chunk_id: Chunk number (0-indexed)
            full_embeddings: Multi-vector sequence, shape (seq_length, 768)
            metadata: Additional metadata (text_preview, word_count, etc.)

        Returns:
            Embedding ID: "{doc_id}-chunk{chunk_id:04d}"

        Raises:
            ValueError: If embedding shape is invalid
            ChromaDBError: If storage fails
        """
        # Validate embeddings
        self._validate_embedding_shape(full_embeddings)

        # Generate ID
        embedding_id = f"{doc_id}-chunk{chunk_id:04d}"

        # Extract CLS token for indexing
        cls_token = self._extract_cls_token(full_embeddings)

        # Compress full embeddings for metadata
        compressed_embeddings = self._compress_and_validate(full_embeddings)

        # Compress markdown if present and large
        if "full_markdown" in metadata and metadata.get("markdown_extracted"):
            markdown = metadata["full_markdown"]

            if len(markdown) > 1024:  # 1KB threshold
                try:
                    # Compress and replace
                    compressed = compress_markdown(markdown)
                    metadata["full_markdown_compressed"] = compressed
                    metadata["markdown_compression"] = "gzip+base64"
                    del metadata["full_markdown"]  # Remove uncompressed
                    logger.debug(f"Compressed markdown: {len(markdown)} → {len(compressed)} chars")
                except Exception as e:
                    # Compression failed, log warning and store uncompressed
                    logger.warning(f"Markdown compression failed: {e}, storing uncompressed")
                    metadata["markdown_compression"] = "none"
            else:
                # Small markdown, store uncompressed
                metadata["markdown_compression"] = "none"

        # Build complete metadata
        seq_length, embedding_dim = full_embeddings.shape
        complete_metadata = {
            "doc_id": doc_id,
            "chunk_id": chunk_id,
            "type": "text",
            "full_embeddings": compressed_embeddings,
            "seq_length": seq_length,
            "embedding_shape": f"({seq_length}, {embedding_dim})",
            "timestamp": datetime.utcnow().isoformat(),
            **metadata  # Add user-provided metadata
        }

        # Validate required fields
        required_fields = ["filename", "page", "source_path"]
        missing_fields = [f for f in required_fields if f not in complete_metadata]
        if missing_fields:
            raise ValueError(
                f"Missing required metadata fields: {missing_fields}"
            )

        # Store in ChromaDB
        try:
            self._text_collection.add(
                ids=[embedding_id],
                embeddings=[cls_token],
                metadatas=[complete_metadata]
            )

            logger.info(
                f"Stored text embedding: {embedding_id} "
                f"(seq_length={seq_length})"
            )

            return embedding_id

        except Exception as e:
            error_msg = f"Failed to store text embedding {embedding_id}: {str(e)}"
            logger.error(error_msg)
            raise StorageError(error_msg) from e

    def get_document_markdown(self, doc_id: str) -> Optional[str]:
        """Retrieve full markdown for a document.

        Args:
            doc_id: Document identifier

        Returns:
            Full markdown text, or None if not available

        Raises:
            DocumentNotFoundError: If doc_id doesn't exist
            CorruptedDataError: If markdown data corrupted
        """
        # Query any embedding for this doc_id (visual first)
        results = self._visual_collection.get(
            where={"doc_id": doc_id},
            limit=1,
            include=["metadatas"]
        )

        if not results['ids']:
            # Try text collection
            results = self._text_collection.get(
                where={"doc_id": doc_id},
                limit=1,
                include=["metadatas"]
            )

        if not results['ids']:
            raise DocumentNotFoundError(f"Document {doc_id} not found")

        metadata = results['metadatas'][0]

        # Check if markdown extraction succeeded
        if not metadata.get("markdown_extracted"):
            logger.info(f"Markdown not available for {doc_id}")
            return None

        # Handle compressed markdown
        if "full_markdown_compressed" in metadata:
            try:
                compressed = metadata["full_markdown_compressed"]
                return decompress_markdown(compressed)
            except CorruptedDataError:
                logger.error(f"Corrupted markdown data for {doc_id}")
                raise
            except Exception as e:
                logger.error(f"Failed to decompress markdown for {doc_id}: {e}")
                return None

        # Handle uncompressed markdown
        if "full_markdown" in metadata:
            return metadata["full_markdown"]

        return None

    def _prepare_enhanced_visual_metadata(
        self,
        base_metadata: Dict[str, Any],
        structure: Optional[DocumentStructure] = None
    ) -> Dict[str, Any]:
        """Prepare visual embedding metadata with optional structure.

        Args:
            base_metadata: Base metadata (filename, source_path, etc.)
            structure: Optional document structure metadata

        Returns:
            Enhanced metadata dictionary ready for storage
        """
        metadata = base_metadata.copy()

        # Add structure metadata if provided (compressed)
        if structure:
            compressed_structure = compress_structure_metadata(structure.to_dict())
            metadata["structure"] = compressed_structure
            metadata["has_structure"] = True

            # Add summary statistics for quick filtering
            metadata["num_headings"] = len(structure.headings)
            metadata["num_tables"] = len(structure.tables)
            metadata["num_pictures"] = len(structure.pictures)
            metadata["max_heading_depth"] = structure.max_heading_depth
        else:
            metadata["has_structure"] = False

        return metadata

    def _prepare_enhanced_text_metadata(
        self,
        base_metadata: Dict[str, Any],
        chunk_context: Optional[ChunkContext] = None
    ) -> Dict[str, Any]:
        """Prepare text embedding metadata with optional chunk context.

        Args:
            base_metadata: Base metadata (filename, page, source_path, etc.)
            chunk_context: Optional chunk context metadata

        Returns:
            Enhanced metadata dictionary ready for storage
        """
        metadata = base_metadata.copy()

        # Add chunk context if provided
        if chunk_context:
            context_dict = chunk_context.to_dict()

            # Store context inline (not compressed - it's small)
            metadata["chunk_context"] = context_dict
            metadata["has_context"] = True

            # Add key fields for filtering
            if chunk_context.parent_heading:
                metadata["parent_heading"] = chunk_context.parent_heading
            if chunk_context.section_path:
                metadata["section_path"] = chunk_context.section_path
            metadata["element_type"] = chunk_context.element_type
            metadata["is_page_boundary"] = chunk_context.is_page_boundary
        else:
            metadata["has_context"] = False

        return metadata

    def search_visual(
        self,
        query_embedding: np.ndarray,
        n_results: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Stage 1 search: Fast retrieval using representative vectors.

        Args:
            query_embedding: Query embedding CLS token, shape (768,)
            n_results: Number of candidates to retrieve
            filters: Optional metadata filters (e.g., {"filename": "report.pdf"})

        Returns:
            List of candidates with:
            {
                "id": str,
                "score": float,              # Cosine similarity (0-1)
                "metadata": Dict[str, Any],  # Includes full_embeddings
                "representative_vector": List[float]
            }

        Raises:
            ChromaDBError: If query fails
        """
        # Ensure query is 1D array
        if len(query_embedding.shape) == 2:
            query_embedding = query_embedding[0]

        # Convert to list for ChromaDB
        query_vector = query_embedding.astype(np.float32).tolist()

        try:
            results = self._visual_collection.query(
                query_embeddings=[query_vector],
                n_results=n_results,
                where=filters
            )

            # Format results
            candidates = []
            for i in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][i]

                # Decompress full embeddings from metadata
                full_embeddings = None
                if 'full_embeddings' in metadata and 'seq_length' in metadata:
                    # Parse embedding shape from metadata string "(seq_len, dim)"
                    shape_str = metadata.get('embedding_shape', '')
                    if shape_str:
                        # Extract dimensions from string like "(1031, 128)"
                        seq_len, dim = eval(shape_str)
                        shape = (seq_len, dim)
                        full_embeddings = decompress_embeddings(
                            metadata['full_embeddings'],
                            shape
                        )

                candidates.append({
                    "id": results['ids'][0][i],
                    "score": 1.0 - results['distances'][0][i],  # Convert distance to similarity
                    "metadata": metadata,
                    "full_embeddings": full_embeddings,  # Include decompressed embeddings
                    "representative_vector": results['embeddings'][0][i] if results.get('embeddings') else None
                })

            logger.info(
                f"Visual search returned {len(candidates)} candidates "
                f"(requested: {n_results})"
            )

            return candidates

        except Exception as e:
            error_msg = f"Visual search failed: {str(e)}"
            logger.error(error_msg)
            raise StorageError(error_msg) from e

    def search_text(
        self,
        query_embedding: np.ndarray,
        n_results: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Stage 1 search: Fast retrieval using representative vectors.

        Same interface as search_visual but queries text_collection.

        Args:
            query_embedding: Query embedding CLS token, shape (768,)
            n_results: Number of candidates to retrieve
            filters: Optional metadata filters

        Returns:
            List of candidates (same format as search_visual)

        Raises:
            ChromaDBError: If query fails
        """
        # Ensure query is 1D array
        if len(query_embedding.shape) == 2:
            query_embedding = query_embedding[0]

        # Convert to list for ChromaDB
        query_vector = query_embedding.astype(np.float32).tolist()

        try:
            results = self._text_collection.query(
                query_embeddings=[query_vector],
                n_results=n_results,
                where=filters
            )

            # Format results
            candidates = []
            for i in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][i]

                # Decompress full embeddings from metadata
                full_embeddings = None
                if 'full_embeddings' in metadata and 'seq_length' in metadata:
                    # Parse embedding shape from metadata string "(seq_len, dim)"
                    shape_str = metadata.get('embedding_shape', '')
                    if shape_str:
                        # Extract dimensions from string like "(1031, 128)"
                        seq_len, dim = eval(shape_str)
                        shape = (seq_len, dim)
                        full_embeddings = decompress_embeddings(
                            metadata['full_embeddings'],
                            shape
                        )

                candidates.append({
                    "id": results['ids'][0][i],
                    "score": 1.0 - results['distances'][0][i],  # Convert distance to similarity
                    "metadata": metadata,
                    "full_embeddings": full_embeddings,  # Include decompressed embeddings
                    "representative_vector": results['embeddings'][0][i] if results.get('embeddings') else None
                })

            logger.info(
                f"Text search returned {len(candidates)} candidates "
                f"(requested: {n_results})"
            )

            return candidates

        except Exception as e:
            error_msg = f"Text search failed: {str(e)}"
            logger.error(error_msg)
            raise StorageError(error_msg) from e

    def get_full_embeddings(
        self,
        embedding_id: str,
        collection: str = "visual"
    ) -> np.ndarray:
        """Retrieve full multi-vector sequence for re-ranking.

        Args:
            embedding_id: ID returned from search
            collection: "visual" or "text"

        Returns:
            Decompressed numpy array, shape (seq_length, 768)

        Raises:
            ValueError: If embedding_id not found
            DecompressionError: If metadata corrupted
        """
        # Select collection
        col = self._visual_collection if collection == "visual" else self._text_collection

        try:
            # Get metadata
            result = col.get(ids=[embedding_id], include=["metadatas"])

            if not result['ids']:
                raise DocumentNotFoundError(
                    f"Embedding {embedding_id} not found in {collection} collection"
                )

            metadata = result['metadatas'][0]

            # Extract compressed embeddings and shape
            compressed = metadata.get('full_embeddings')
            shape_str = metadata.get('embedding_shape')

            if not compressed or not shape_str:
                raise MetadataCompressionError(
                    f"Missing embedding data for {embedding_id}"
                )

            # Parse shape string "(seq_length, 768)" -> tuple
            shape = tuple(map(int, shape_str.strip('()').split(',')))

            # Decompress
            embeddings = decompress_embeddings(compressed, shape)

            logger.debug(
                f"Retrieved full embeddings for {embedding_id}: shape {embeddings.shape}"
            )

            return embeddings

        except DocumentNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Failed to retrieve embeddings for {embedding_id}: {str(e)}"
            logger.error(error_msg)
            raise MetadataCompressionError(error_msg) from e

    def delete_document(
        self,
        doc_id: str
    ) -> Tuple[int, int]:
        """Delete all embeddings for a document.

        Args:
            doc_id: Document identifier

        Returns:
            Tuple of (visual_count, text_count) deleted
        """
        visual_count = 0
        text_count = 0

        try:
            # Delete from visual collection
            visual_results = self._visual_collection.get(
                where={"doc_id": doc_id},
                include=[]
            )
            if visual_results['ids']:
                self._visual_collection.delete(ids=visual_results['ids'])
                visual_count = len(visual_results['ids'])

            # Delete from text collection
            text_results = self._text_collection.get(
                where={"doc_id": doc_id},
                include=[]
            )
            if text_results['ids']:
                self._text_collection.delete(ids=text_results['ids'])
                text_count = len(text_results['ids'])

            logger.info(
                f"Deleted document {doc_id}: "
                f"{visual_count} visual, {text_count} text embeddings"
            )

            return (visual_count, text_count)

        except Exception as e:
            error_msg = f"Failed to delete document {doc_id}: {str(e)}"
            logger.error(error_msg)
            raise StorageError(error_msg) from e

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics.

        Returns:
            {
                "visual_count": int,
                "text_count": int,
                "total_documents": int,  # Unique doc_ids
                "storage_size_mb": float
            }
        """
        try:
            # Get counts
            visual_count = self._visual_collection.count()
            text_count = self._text_collection.count()

            # Get unique doc_ids (this is approximate, requires querying)
            # For performance, we'll estimate from visual collection
            visual_docs = self._visual_collection.get(include=["metadatas"])
            unique_docs = set()
            if visual_docs['metadatas']:
                unique_docs = {
                    meta.get('doc_id')
                    for meta in visual_docs['metadatas']
                    if meta.get('doc_id')
                }

            # Estimate storage size (simplified - actual DB size may vary)
            # This is a rough estimate based on embedding counts
            estimated_size_mb = (visual_count + text_count) * 0.1  # ~100KB per embedding

            stats = {
                "visual_count": visual_count,
                "text_count": text_count,
                "total_documents": len(unique_docs),
                "storage_size_mb": round(estimated_size_mb, 2)
            }

            logger.info(f"Collection stats: {stats}")

            return stats

        except Exception as e:
            error_msg = f"Failed to get collection stats: {str(e)}"
            logger.error(error_msg)
            raise StorageError(error_msg) from e

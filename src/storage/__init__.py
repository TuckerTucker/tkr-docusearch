"""
Storage module for DocuSearch MVP.

This module provides ChromaDB storage capabilities with multi-vector
embedding support for visual and text embeddings.

Components:
- ChromaClient: Main client for ChromaDB operations
- CollectionManager: Collection lifecycle management
- Compression utilities: Embedding compression/decompression
- Custom exceptions: Storage-specific error types
"""

from .chroma_client import (
    ChromaClient,
    StorageError,
    ChromaDBConnectionError,
    EmbeddingValidationError,
    MetadataCompressionError,
    DocumentNotFoundError,
)
from .collection_manager import CollectionManager
from .compression import (
    compress_embeddings,
    decompress_embeddings,
    estimate_compressed_size,
    compression_ratio,
)

__all__ = [
    # Main client
    'ChromaClient',
    # Collection management
    'CollectionManager',
    # Exceptions
    'StorageError',
    'ChromaDBConnectionError',
    'EmbeddingValidationError',
    'MetadataCompressionError',
    'DocumentNotFoundError',
    # Compression utilities
    'compress_embeddings',
    'decompress_embeddings',
    'estimate_compressed_size',
    'compression_ratio',
]

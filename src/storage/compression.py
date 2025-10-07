"""
Compression utilities for multi-vector embeddings.

This module provides compression and decompression for storing large
multi-vector embeddings in ChromaDB metadata fields (max 2MB per entry).
"""

import gzip
import base64
import json
import numpy as np
from typing import Tuple, Dict, Any


def compress_embeddings(embeddings: np.ndarray) -> str:
    """Compress embeddings using gzip + base64 encoding.

    Reduces storage size by ~4x for multi-vector embeddings.

    Args:
        embeddings: NumPy array of shape (seq_length, embedding_dim)

    Returns:
        Base64-encoded compressed string

    Example:
        >>> emb = np.random.randn(100, 768)
        >>> compressed = compress_embeddings(emb)
        >>> isinstance(compressed, str)
        True
    """
    # Convert to bytes
    embeddings_bytes = embeddings.tobytes()

    # Compress with gzip
    compressed_bytes = gzip.compress(embeddings_bytes, compresslevel=6)

    # Encode as base64 string
    encoded = base64.b64encode(compressed_bytes).decode('utf-8')

    return encoded


def decompress_embeddings(
    compressed_str: str,
    shape: Tuple[int, int],
    dtype: np.dtype = np.float32
) -> np.ndarray:
    """Decompress embeddings from base64 + gzip format.

    Args:
        compressed_str: Base64-encoded compressed string
        shape: Original embedding shape (seq_length, embedding_dim)
        dtype: NumPy dtype of embeddings (default: float32)

    Returns:
        Decompressed NumPy array

    Example:
        >>> emb = np.random.randn(100, 768).astype(np.float32)
        >>> compressed = compress_embeddings(emb)
        >>> decompressed = decompress_embeddings(compressed, emb.shape)
        >>> np.allclose(emb, decompressed)
        True
    """
    # Decode from base64
    compressed_bytes = base64.b64decode(compressed_str.encode('utf-8'))

    # Decompress with gzip
    embeddings_bytes = gzip.decompress(compressed_bytes)

    # Convert back to NumPy array
    embeddings = np.frombuffer(embeddings_bytes, dtype=dtype)

    # Reshape to original shape
    embeddings = embeddings.reshape(shape)

    return embeddings


def estimate_compressed_size(embeddings: np.ndarray) -> int:
    """Estimate compressed size of embeddings in bytes.

    Args:
        embeddings: NumPy array to compress

    Returns:
        Estimated compressed size in bytes
    """
    compressed = compress_embeddings(embeddings)
    return len(compressed.encode('utf-8'))


def compression_ratio(embeddings: np.ndarray) -> float:
    """Calculate compression ratio for embeddings.

    Args:
        embeddings: NumPy array to compress

    Returns:
        Compression ratio (original_size / compressed_size)

    Example:
        >>> emb = np.random.randn(100, 768).astype(np.float32)
        >>> ratio = compression_ratio(emb)
        >>> ratio > 1.0  # Should achieve some compression
        True
    """
    original_size = embeddings.nbytes
    compressed_size = estimate_compressed_size(embeddings)

    if compressed_size == 0:
        return 0.0

    return original_size / compressed_size


def compress_structure_metadata(metadata_dict: Dict[str, Any]) -> str:
    """Compress structure metadata using gzip + base64 encoding.

    For storing DocumentStructure and ChunkContext in ChromaDB metadata.
    Target: <50KB compressed per document.

    Args:
        metadata_dict: Dictionary representation of metadata (from .to_dict())

    Returns:
        Base64-encoded compressed JSON string

    Example:
        >>> from src.storage.metadata_schema import DocumentStructure
        >>> structure = DocumentStructure()
        >>> compressed = compress_structure_metadata(structure.to_dict())
        >>> isinstance(compressed, str)
        True
    """
    # Convert dict to JSON string
    json_str = json.dumps(metadata_dict, separators=(',', ':'))  # Compact JSON
    json_bytes = json_str.encode('utf-8')

    # Compress with gzip
    compressed_bytes = gzip.compress(json_bytes, compresslevel=6)

    # Encode as base64
    encoded = base64.b64encode(compressed_bytes).decode('utf-8')

    return encoded


def decompress_structure_metadata(compressed_str: str) -> Dict[str, Any]:
    """Decompress structure metadata from base64 + gzip format.

    Args:
        compressed_str: Base64-encoded compressed JSON string

    Returns:
        Dictionary representation of metadata

    Example:
        >>> from src.storage.metadata_schema import DocumentStructure
        >>> structure = DocumentStructure()
        >>> compressed = compress_structure_metadata(structure.to_dict())
        >>> decompressed = decompress_structure_metadata(compressed)
        >>> isinstance(decompressed, dict)
        True
    """
    # Decode from base64
    compressed_bytes = base64.b64decode(compressed_str.encode('utf-8'))

    # Decompress with gzip
    json_bytes = gzip.decompress(compressed_bytes)

    # Parse JSON
    json_str = json_bytes.decode('utf-8')
    metadata_dict = json.loads(json_str)

    return metadata_dict

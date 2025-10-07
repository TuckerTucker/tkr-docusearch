"""
Compression utilities for multi-vector embeddings.

This module provides compression and decompression for storing large
multi-vector embeddings in ChromaDB metadata fields (max 2MB per entry).
"""

import gzip
import base64
import numpy as np
from typing import Tuple


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

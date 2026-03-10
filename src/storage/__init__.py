"""
Storage module for DocuSearch.

This module provides Koji hybrid database (SQL + vector + graph) storage
for documents, pages, chunks, and document relationships.

Components:
- KojiClient: Main client for Koji database operations
- Custom exceptions: Storage-specific error types
- Multi-vector utilities: Binary packing/unpacking for embeddings
"""

from .koji_client import (
    KojiClient,
    KojiClientError,
    KojiConnectionError,
    KojiDuplicateError,
    KojiQueryError,
    pack_multivec,
    unpack_multivec,
)

__all__ = [
    # Main client
    "KojiClient",
    # Exceptions
    "KojiClientError",
    "KojiConnectionError",
    "KojiQueryError",
    "KojiDuplicateError",
    # Multi-vector utilities
    "pack_multivec",
    "unpack_multivec",
]

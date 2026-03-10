"""
Embeddings module for DocuSearch.

This module provides the Shikomi gRPC client for ColNomic multi-vector
embeddings via the external Shikomi embedding service.

Components:
- ShikomiClient: gRPC client for embedding generation
"""

from .shikomi_client import ShikomiClient

__all__ = [
    "ShikomiClient",
]
